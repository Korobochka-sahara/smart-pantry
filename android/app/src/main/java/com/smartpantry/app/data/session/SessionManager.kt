
package com.smartpantry.app.data.session

import android.content.Context
import com.smartpantry.app.data.local.TokenStorage
import com.smartpantry.app.data.model.RefreshRequest
import com.smartpantry.app.data.model.UserResponse
import com.smartpantry.app.data.remote.ApiClient
import kotlinx.coroutines.CancellationException
import retrofit2.HttpException
import java.io.IOException

sealed interface SessionState {
    data object Unauthenticated : SessionState

    data class Authenticated(
        val user: UserResponse
    ) : SessionState

    data object Unavailable : SessionState
}

object SessionManager {

    suspend fun restore(context: Context): SessionState {
        val appContext = context.applicationContext

        val accessToken = TokenStorage.getAccessToken(appContext)
        val refreshToken = TokenStorage.getRefreshToken(appContext)

        // Нет ни одного токена — пользователь не входил
        // или ранее вышел из аккаунта.
        if (accessToken == null && refreshToken == null) {
            return SessionState.Unauthenticated
        }

        // Проверяем access token, если он есть.
        if (accessToken != null) {
            when (val result = getCurrentUser(accessToken)) {
                is UserCheck.Success -> {
                    return SessionState.Authenticated(result.user)
                }

                UserCheck.Unauthorized -> {
                    // Access token недействителен или истёк.
                    // Попробуем обновить его ниже.
                }

                UserCheck.Unavailable -> {
                    // Не удаляем токены из-за проблем с сетью
                    // или временной ошибки сервера.
                    return SessionState.Unavailable
                }
            }
        }

        // Без refresh token обновить сессию невозможно.
        if (refreshToken == null) {
            TokenStorage.clear(appContext)
            return SessionState.Unauthenticated
        }

        val newTokens = try {
            ApiClient.authApi.refresh(
                RefreshRequest(refresh_token = refreshToken)
            )
        } catch (e: CancellationException) {
            throw e
        } catch (e: HttpException) {
            return when (e.code()) {
                401, 403 -> {
                    // Сервер явно отклонил refresh token.
                    TokenStorage.clear(appContext)
                    SessionState.Unauthenticated
                }

                else -> {
                    // Например, 5xx или другой неожиданный
                    // HTTP-ответ. Сохраняем текущие токены.
                    SessionState.Unavailable
                }
            }
        } catch (e: IOException) {
            // Нет соединения, тайм-аут, ошибка DNS и т. п.
            // Токены оставляем для следующей попытки.
            return SessionState.Unavailable
        } catch (e: Exception) {
            // Неожиданная ошибка: не разлогиниваем пользователя
            // автоматически, поскольку причина неизвестна.
            return SessionState.Unavailable
        }

        // Бэкенд ротирует refresh token, поэтому сохраняем
        // новую пару сразу после успешного ответа.
        TokenStorage.save(
            context = appContext,
            accessToken = newTokens.access_token,
            refreshToken = newTokens.refresh_token
        )

        // Проверяем, что новая пара действительно работает.
        return when (
            val result = getCurrentUser(newTokens.access_token)
        ) {
            is UserCheck.Success -> {
                SessionState.Authenticated(result.user)
            }

            UserCheck.Unauthorized -> {
                TokenStorage.clear(appContext)
                SessionState.Unauthenticated
            }

            UserCheck.Unavailable -> {
                // Новые токены уже сохранены. Повторим проверку
                // при следующем запуске или по кнопке повтора.
                SessionState.Unavailable
            }
        }
    }

    private suspend fun getCurrentUser(
        accessToken: String
    ): UserCheck {
        return try {
            val user = ApiClient.authApi.getMe(
                authorization = "Bearer $accessToken"
            )
            UserCheck.Success(user)
        } catch (e: CancellationException) {
            throw e
        } catch (e: HttpException) {
            when (e.code()) {
                401, 403 -> UserCheck.Unauthorized
                else -> UserCheck.Unavailable
            }
        } catch (e: IOException) {
            UserCheck.Unavailable
        } catch (e: Exception) {
            UserCheck.Unavailable
        }
    }

    private sealed interface UserCheck {
        data class Success(val user: UserResponse) : UserCheck
        data object Unauthorized : UserCheck
        data object Unavailable : UserCheck
    }
}
