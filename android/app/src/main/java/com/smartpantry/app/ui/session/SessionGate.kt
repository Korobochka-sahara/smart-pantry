package com.smartpantry.app.ui.session

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableIntStateOf
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.unit.dp
import androidx.compose.foundation.layout.padding
import androidx.compose.material3.Button
import com.smartpantry.app.data.local.TokenStorage
import com.smartpantry.app.data.session.SessionManager
import com.smartpantry.app.data.session.SessionState
import com.smartpantry.app.ui.screens.auth.AuthScreen
import com.smartpantry.app.ui.screens.home.HomeScreen

@Composable
fun SessionGate() {
    val context = LocalContext.current

    var retryTrigger by remember { mutableIntStateOf(0) }
    var sessionState by remember { mutableStateOf<SessionState?>(null) }

    LaunchedEffect(retryTrigger) { //запускает SessionManager.restore() при
        // открытии экрана и после нажатия «Повторить»
        sessionState = SessionManager.restore(context)
    }

    when (val state = sessionState) {
        null -> LoadingScreen() //sessionState == null означает, что проверка ещё выполняется

        SessionState.Unauthenticated -> { //Unauthenticated открывает экран регистрации
            // и входа
            AuthScreen(
                onLoginSuccess = {
                    sessionState = null
                    retryTrigger++
                }
            )
        }

        is SessionState.Authenticated -> { //Authenticated открывает главное приложение
            HomeScreen(
                user = state.user,
                onLogout = {
                    TokenStorage.clear(context)
                    sessionState = SessionState.Unauthenticated
                }
            )
        }

        SessionState.Unavailable -> { //Unavailable показывает ошибку
            // подключения, не очищая токены
            ConnectionErrorScreen(
                onRetry = {
                    sessionState = null
                    retryTrigger++
                }
            )
        }
    }
}

@Composable
private fun LoadingScreen() {
    Box(
        modifier = Modifier.fillMaxSize(),
        contentAlignment = Alignment.Center
    ) {
        Column(
            horizontalAlignment = Alignment.CenterHorizontally,
            verticalArrangement = Arrangement.spacedBy(12.dp)
        ) {
            CircularProgressIndicator()
            Text("Проверяем сессию...")
        }
    }
}

@Composable
private fun ConnectionErrorScreen(
    onRetry: () -> Unit
) {
    Box(
        modifier = Modifier
            .fillMaxSize()
            .padding(24.dp),
        contentAlignment = Alignment.Center
    ) {
        Column(
            horizontalAlignment = Alignment.CenterHorizontally,
            verticalArrangement = Arrangement.spacedBy(12.dp)
        ) {
            Text(
                text = "Не удалось проверить сессию",
                style = MaterialTheme.typography.titleLarge
            )

            Text(
                text = "Проверь подключение к интернету и попробуй ещё раз"
            )

            Button(onClick = onRetry) {
                Text("Повторить")
            }
        }
    }
}