package com.smartpantry.app.data.remote

import com.smartpantry.app.data.model.LoginRequest
import com.smartpantry.app.data.model.RegisterRequest
import com.smartpantry.app.data.model.RefreshRequest
import com.smartpantry.app.data.model.TokenResponse
import com.smartpantry.app.data.model.UserResponse
import retrofit2.http.Body
import retrofit2.http.GET
import retrofit2.http.Header
import retrofit2.http.POST

interface AuthApi { //описание операций, которые предоставляет сервер

    @POST("auth/register") //HTTP-метод POST и путь к регистрации
    // Полный адрес Retrofit составит из базового URL и этого пути
    suspend fun register(// suspend позволяет вызывать эти методы из корутины
        @Body request: RegisterRequest //передать объект в теле запроса
    ): UserResponse //ожидаемый тип ответа

    @POST("auth/login")
    suspend fun login(
        @Body request: LoginRequest
    ): TokenResponse

    @GET("auth/me")
    suspend fun getMe(
        @Header("Authorization") authorization: String
    ): UserResponse

    @POST("auth/refresh")
    suspend fun refresh(
        @Body request: RefreshRequest
    ): TokenResponse
}
