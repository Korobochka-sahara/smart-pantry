package com.smartpantry.app.data.remote

import android.content.Context
import com.smartpantry.app.data.local.TokenStorage
import com.smartpantry.app.data.model.TokenResponse
import kotlinx.serialization.json.Json
import kotlinx.serialization.builtins.serializer
import kotlinx.serialization.decodeFromString
import okhttp3.Authenticator
import okhttp3.MediaType.Companion.toMediaType
import okhttp3.OkHttpClient
import okhttp3.Request
import okhttp3.RequestBody.Companion.toRequestBody
import okhttp3.Response as OkHttpResponse
import okhttp3.Route
import okhttp3.Interceptor
import retrofit2.Retrofit
import com.jakewharton.retrofit2.converter.kotlinx.serialization.asConverterFactory
import java.io.IOException
import com.smartpantry.app.data.remote.OCRApi

object ApiClient {
    private const val BASE_URL = "http://10.0.2.2:8000/"
    private const val REFRESH_PATH = "auth/refresh"
    private val json = Json { ignoreUnknownKeys = true }
    @Volatile private var appContext: Context? = null
    private val refreshLock = Any()

    /** Call once from MainActivity before any API request. */
    fun initialize(context: Context) {
        appContext = context.applicationContext
    }

    private val tokenInterceptor = Interceptor { chain ->
        val original = chain.request()
        val context = appContext
        val token = context?.let { TokenStorage.getAccessToken(it) }
        val request = if (token != null) {
            original.newBuilder().header("Authorization", "Bearer $token").build()
        } else original
        chain.proceed(request)
    }

    private val tokenAuthenticator = object : Authenticator {
        override fun authenticate(route: Route?, response: OkHttpResponse): Request? {
            // Avoid loops for authentication endpoints and allow only one retry.
            val path = response.request.url.encodedPath.trimStart('/')
            if (path == "auth/login" || path == "auth/register" ||
                path == REFRESH_PATH || path == "auth/logout" ||
                responseCount(response) >= 2) return null

            val context = appContext ?: return null
            synchronized(refreshLock) {
                val currentAccess = TokenStorage.getAccessToken(context)
                val requestToken = response.request.header("Authorization")
                    ?.removePrefix("Bearer ")
                // Another request may already have refreshed the token.
                if (currentAccess != null && currentAccess != requestToken) {
                    return response.request.newBuilder()
                        .header("Authorization", "Bearer $currentAccess")
                        .build()
                }

                val refreshToken = TokenStorage.getRefreshToken(context) ?: return null
                val body = """{"refresh_token":${json.encodeToString(String.serializer(), refreshToken)}}"""
                    .toRequestBody("application/json".toMediaType())
                val refreshRequest = Request.Builder()
                    .url(BASE_URL + REFRESH_PATH)
                    .post(body)
                    .build()

                return try {
                    // A separate bare client prevents recursive authenticator calls.
                    OkHttpClient().newCall(refreshRequest).execute().use { refreshResponse ->
                        if (!refreshResponse.isSuccessful) {
                            if (refreshResponse.code == 401 || refreshResponse.code == 403) {
                                TokenStorage.clear(context)
                            }
                            return null
                        }
                        val responseBody = refreshResponse.body?.string() ?: return null
                        val tokens = json.decodeFromString<TokenResponse>(responseBody)
                        TokenStorage.save(context, tokens.access_token, tokens.refresh_token)
                        response.request.newBuilder()
                            .header("Authorization", "Bearer ${tokens.access_token}")
                            .build()
                    }
                } catch (_: IOException) {
                    // Keep tokens on network failure; the user may retry later.
                    null
                } catch (_: Exception) {
                    null
                }
            }
        }

        private fun responseCount(response: OkHttpResponse): Int {
            var result = 1
            var prior = response.priorResponse
            while (prior != null) {
                result++
                prior = prior.priorResponse
            }
            return result
        }
    }

    private val client = OkHttpClient.Builder()
        .addInterceptor(tokenInterceptor)
        .authenticator(tokenAuthenticator)
        .connectTimeout(30, java.util.concurrent.TimeUnit.SECONDS)
        .writeTimeout(120, java.util.concurrent.TimeUnit.SECONDS)
        .readTimeout(900, java.util.concurrent.TimeUnit.SECONDS)
        .callTimeout(960, java.util.concurrent.TimeUnit.SECONDS)
        .build()

    private val retrofit: Retrofit = Retrofit.Builder()
        .baseUrl(BASE_URL)
        .client(client)
        .addConverterFactory(json.asConverterFactory("application/json".toMediaType()))
        .build()

    val authApi: AuthApi = retrofit.create(AuthApi::class.java)
    val householdApi: HouseholdApi = retrofit.create(HouseholdApi::class.java)
    val inventoryApi: InventoryApi = retrofit.create(InventoryApi::class.java)

    val ocrApi: OCRApi = retrofit.create(OCRApi::class.java)
}
