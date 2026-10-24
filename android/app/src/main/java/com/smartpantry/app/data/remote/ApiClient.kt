package com.smartpantry.app.data.remote

import kotlinx.serialization.json.Json
import okhttp3.MediaType.Companion.toMediaType
import retrofit2.Retrofit
import com.jakewharton.retrofit2.converter.kotlinx.serialization.asConverterFactory

object ApiClient {

    private const val BASE_URL = "http://10.0.2.2:8000/"
// адрес FastAPI. Адрес 10.0.2.2 нужен именно Android-эмулятору,
// чтобы обратиться к компьютеру, на котором запущен сервер
// Адрес localhost внутри эмулятора указывал бы на сам эмулятор.
    private val json = Json {
        ignoreUnknownKeys = true
    }//позволяет игнорировать дополнительные поля ответа,
    // которых нет в нашей Kotlin-модели

    private val retrofit: Retrofit = Retrofit.Builder()
        .baseUrl(BASE_URL)
        .addConverterFactory(//подключает преобразование JSON в Kotlin-объекты
            json.asConverterFactory(
                "application/json".toMediaType()
            )
        )
        .build()

    val authApi: AuthApi = retrofit.create(AuthApi::class.java)
    //создаёт реализацию интерфейса AuthApi, которая действительно отправляет HTTP-запросы
    val householdApi: HouseholdApi =
        retrofit.create(HouseholdApi::class.java)
}
