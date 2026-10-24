
package com.smartpantry.app.data.model

import kotlinx.serialization.SerialName
import kotlinx.serialization.Serializable
//@Serializable сообщает библиотеке, что объект можно преобразовать из JSON и обратно

@Serializable
data class RegisterRequest(
    val email: String,
    val username: String,
    val password: String
)

@Serializable
data class LoginRequest(
    val email: String,
    val password: String
)

@Serializable
data class RefreshRequest(
    val refresh_token: String
)

@Serializable
data class LogoutRequest(
    val refresh_token: String
)

@Serializable
data class TokenResponse(
    val access_token: String,
    val refresh_token: String,
    val token_type: String
)

@Serializable
data class UserResponse(
    val id: Int,
    val email: String,
    val username: String
)
