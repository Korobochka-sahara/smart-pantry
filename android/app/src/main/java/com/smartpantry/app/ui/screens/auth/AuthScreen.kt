
package com.smartpantry.app.ui.screens.auth

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.material3.Button
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.input.KeyboardType
import androidx.compose.ui.text.input.PasswordVisualTransformation
import androidx.compose.ui.unit.dp
import androidx.compose.runtime.rememberCoroutineScope
import com.smartpantry.app.data.model.LoginRequest
import com.smartpantry.app.data.model.RegisterRequest
import com.smartpantry.app.data.remote.ApiClient
import kotlinx.coroutines.launch
import retrofit2.HttpException
import java.io.IOException
import org.json.JSONArray
import org.json.JSONObject
import androidx.compose.ui.platform.LocalContext
import com.smartpantry.app.data.local.TokenStorage


@Composable
fun AuthScreen(
    onLoginSuccess: () -> Unit = {}
) {
    var isRegister by rememberSaveable { mutableStateOf(false) }

    var email by rememberSaveable { mutableStateOf("") }
    var username by rememberSaveable { mutableStateOf("") }
    var password by rememberSaveable { mutableStateOf("") }
    var confirmPassword by rememberSaveable { mutableStateOf("") }

    var message by rememberSaveable { mutableStateOf("") }
    var isLoading by rememberSaveable { mutableStateOf(false) }

    val scope = rememberCoroutineScope()
    val context = LocalContext.current

    Column(
        modifier = Modifier
            .fillMaxSize()
            .padding(24.dp),
        verticalArrangement = Arrangement.Center,
        horizontalAlignment = Alignment.CenterHorizontally
    ) {
        Text(
            text = "Smart Pantry",
            style = MaterialTheme.typography.headlineLarge
        )

        Spacer(modifier = Modifier.height(8.dp))

        Text(
            text = if (isRegister) {
                "Создание аккаунта"
            } else {
                "Твои продукты — под контролем"
            },
            style = MaterialTheme.typography.bodyLarge
        )

        Spacer(modifier = Modifier.height(32.dp))

        OutlinedTextField(
            value = email,
            onValueChange = {
                email = it
                message = ""
            },
            modifier = Modifier.fillMaxWidth(),
            label = { Text("Электронная почта") },
            singleLine = true,
            enabled = !isLoading,
            keyboardOptions = KeyboardOptions(
                keyboardType = KeyboardType.Email
            )
        )

        if (isRegister) {
            Spacer(modifier = Modifier.height(12.dp))

            OutlinedTextField(
                value = username,
                onValueChange = {
                    username = it
                    message = ""
                },
                modifier = Modifier.fillMaxWidth(),
                label = { Text("Имя пользователя") },
                singleLine = true,
                enabled = !isLoading
            )
        }

        Spacer(modifier = Modifier.height(12.dp))

        OutlinedTextField(
            value = password,
            onValueChange = {
                password = it
                message = ""
            },
            modifier = Modifier.fillMaxWidth(),
            label = { Text("Пароль") },
            singleLine = true,
            enabled = !isLoading,
            visualTransformation = PasswordVisualTransformation(),
            keyboardOptions = KeyboardOptions(
                keyboardType = KeyboardType.Password
            )
        )
        if (isRegister) {
            Text(
                text = "Минимум 8 символов",
                style = MaterialTheme.typography.bodySmall,
                color = MaterialTheme.colorScheme.onSurfaceVariant
            )
        }

        if (isRegister) {
            Spacer(modifier = Modifier.height(12.dp))

            OutlinedTextField(
                value = confirmPassword,
                onValueChange = {
                    confirmPassword = it
                    message = ""
                },
                modifier = Modifier.fillMaxWidth(),
                label = { Text("Повтори пароль") },
                singleLine = true,
                enabled = !isLoading,
                visualTransformation = PasswordVisualTransformation(),
                keyboardOptions = KeyboardOptions(
                    keyboardType = KeyboardType.Password
                )
            )
        }

        Spacer(modifier = Modifier.height(20.dp))

        Button(
            onClick = {
                message = ""

                when {
                    email.isBlank() || password.isBlank() -> {
                        message = "Заполни почту и пароль"
                    }

                    isRegister && username.isBlank() -> {
                        message = "Введи имя пользователя"
                    }

                    isRegister && password != confirmPassword -> {
                        message = "Пароли не совпадают"
                    }

                    else -> {
                        scope.launch {
                            isLoading = true

                            try {
                                if (isRegister) {
                                    if (password.length < 8) {
                                        message = "Пароль должен содержать не менее 8 символов"
                                        return@launch
                                    }

                                    val user = ApiClient.authApi.register(
                                        RegisterRequest(
                                            email = email.trim(),
                                            username = username.trim(),
                                            password = password
                                        )
                                    )

                                    message =
                                        "Аккаунт ${user.username} создан. Теперь войди."

                                    isRegister = false
                                    password = ""
                                    confirmPassword = ""
                                } else {
                                    val response = ApiClient.authApi.login(
                                        LoginRequest(
                                            email = email.trim(),
                                            password = password
                                        )
                                    )

                                    TokenStorage.save(
                                        context = context,
                                        accessToken = response.access_token,
                                        refreshToken = response.refresh_token
                                    )
                                    onLoginSuccess()
                                }
                            } catch (e: HttpException) {
                                message = readableApiError(e)
                            } catch (e: IOException) {
                                message =
                                    "Не удалось подключиться к серверу. Проверь соединение и FastAPI."
                            } catch (e: Exception) {
                                message =
                                    "Не удалось выполнить запрос. Проверь настройки приложения."
                            } finally {
                                isLoading = false
                            }
                        }
                    }
                }
            },
            modifier = Modifier.fillMaxWidth(),
            enabled = !isLoading
        ) {
            if (isLoading) {
                CircularProgressIndicator()
            } else {
                Text(
                    if (isRegister) {
                        "Зарегистрироваться"
                    } else {
                        "Войти"
                    }
                )
            }
        }

        Spacer(modifier = Modifier.height(8.dp))

        TextButton(
            onClick = {
                isRegister = !isRegister
                message = ""
                confirmPassword = ""
            },
            enabled = !isLoading
        ) {
            Text(
                if (isRegister) {
                    "Уже есть аккаунт? Войти"
                } else {
                    "Нет аккаунта? Зарегистрироваться"
                }
            )
        }

        if (message.isNotBlank()) {
            Spacer(modifier = Modifier.height(12.dp))

            Text(
                text = message,
                color = MaterialTheme.colorScheme.primary,
                style = MaterialTheme.typography.bodyMedium
            )
        }
    }
}

private fun readableApiError(e: HttpException): String {
    val body = try {
        e.response()?.errorBody()?.string().orEmpty()
    } catch (_: Exception) {
        ""
    }

    val detail = try {
        JSONObject(body).opt("detail")
    } catch (_: Exception) {
        null
    }

    // Ошибки, которые бэкенд возвращает обычной строкой.
    if (detail is String) {
        return when (detail) {
            "Email already registered" ->
                "Этот email уже зарегистрирован"

            "Username already taken" ->
                "Это имя пользователя уже занято"

            "Invalid email or password" ->
                "Неверный email или пароль"

            "Password must be at least 8 characters long" ->
                "Пароль должен содержать не менее 8 символов"

            else -> when (e.code()) {
                401 -> "Неверный email или пароль"
                409 -> "Не удалось зарегистрировать пользователя: проверьте email и имя"
                422 -> "Проверьте правильность введённых данных"
                else -> "Не удалось выполнить запрос. Попробуйте позже"
            }
        }
    }

    // Ошибки валидации Pydantic обычно приходят массивом.
    if (detail is JSONArray) {
        for (i in 0 until detail.length()) {
            val item = detail.optJSONObject(i) ?: continue
            val location = item.optJSONArray("loc")
            val field = location
                ?.optString(location.length() - 1)
                .orEmpty()
            val error = item.optString("msg").lowercase()

            when {
                field == "email" ->
                    return "Проверьте правильность введённого email"

                field == "password" &&
                        ("8 characters" in error || "at least 8" in error) ->
                    return "Пароль должен содержать не менее 8 символов"

                field == "password" ->
                    return "Проверьте правильность введённого пароля"

                field == "username" ->
                    return "Проверьте правильность введённого имени пользователя"
            }
        }
    }

    return when (e.code()) {
        401 -> "Неверный email или пароль"
        409 -> "Эти данные уже используются"
        422 -> "Проверьте правильность введённых данных"
        else -> "Не удалось выполнить запрос. Попробуйте позже"
    }
}