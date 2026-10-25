package com.smartpantry.app.ui.screens.home

import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.AlertDialog
import androidx.compose.material3.Button
import androidx.compose.material3.Card
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.NavigationBar
import androidx.compose.material3.NavigationBarItem
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.material3.TopAppBar
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableIntStateOf
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.rememberCoroutineScope
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.input.KeyboardCapitalization
import androidx.compose.ui.unit.dp
import com.smartpantry.app.data.local.TokenStorage
import com.smartpantry.app.data.model.CreateHouseholdRequest
import com.smartpantry.app.data.model.HouseholdMemberResponse
import com.smartpantry.app.data.model.HouseholdResponse
import com.smartpantry.app.data.model.UserResponse
import com.smartpantry.app.data.remote.ApiClient
import kotlinx.coroutines.CancellationException
import kotlinx.coroutines.launch
import retrofit2.HttpException
import java.io.IOException
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.ui.text.input.KeyboardType

private enum class MainTab(val title: String) {
    HOUSEHOLDS("Домохозяйства"),
    PROFILE("Профиль")
}

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun HomeScreen(
    user: UserResponse,
    onLogout: () -> Unit
) {
    val context = LocalContext.current
    val scope = rememberCoroutineScope()

    var selectedTab by remember { mutableStateOf(MainTab.HOUSEHOLDS) }
    var households by remember { mutableStateOf<List<HouseholdResponse>>(emptyList()) }
    var isLoading by remember { mutableStateOf(true) }
    var error by remember { mutableStateOf<String?>(null) }
    var refreshKey by remember { mutableIntStateOf(0) }
    var selectedHousehold by remember { mutableStateOf<HouseholdResponse?>(null) }
    var showCreateDialog by remember { mutableStateOf(false) }

    fun loadHouseholds() {
        scope.launch {
            isLoading = true
            error = null

            try {
                val token = TokenStorage.getAccessToken(context)
                if (token == null) {
                    error = "Сессия не найдена. Войди в аккаунт заново."
                    return@launch
                }

                households = ApiClient.householdApi.getMyHouseholds(
                    authorization = "Bearer $token"
                )
            } catch (e: CancellationException) {
                throw e
            } catch (e: HttpException) {
                error = when (e.code()) {
                    401, 403 -> "Нет доступа. Попробуй восстановить сессию."
                    else -> "Сервер вернул ошибку: ${e.code()}"
                }
            } catch (e: IOException) {
                error = "Не удалось подключиться к серверу."
            } catch (e: Exception) {
                error = "Не удалось загрузить домохозяйства."
            } finally {
                isLoading = false
            }
        }
    }

    LaunchedEffect(refreshKey) {
        loadHouseholds()
    }

    if (selectedHousehold != null) {
        HouseholdDetailScreen(
            household = selectedHousehold!!,
            user = user,
            onBack = { selectedHousehold = null },
            onLeave = {
                selectedHousehold = null
                refreshKey++
            }
        )
        return
    }

    if (showCreateDialog) {
        CreateHouseholdDialog(
            onDismiss = { showCreateDialog = false },
            onCreate = { name ->
                scope.launch {
                    try {
                        val token = TokenStorage.getAccessToken(context)
                            ?: throw IllegalStateException("Сессия не найдена")

                        val created = ApiClient.householdApi.createHousehold(
                            authorization = "Bearer $token",
                            request = CreateHouseholdRequest(name = name)
                        )

                        showCreateDialog = false
                        refreshKey++
                        selectedHousehold = created
                    } catch (e: CancellationException) {
                        throw e
                    } catch (e: HttpException) {
                        // Закрываем диалог, чтобы сообщение об ограничении было видно на главном экране.
                        showCreateDialog = false
                        error = when (e.code()) {
                            409 -> "Нельзя создать домохозяйство: достигнут лимит в 5 домов, где ты владелец."
                            401 -> "Сессия истекла. Войди в приложение снова."
                            422 -> "Проверь название домохозяйства."
                            else -> "Не удалось создать домохозяйство: ${e.code()}"
                        }
                    } catch (e: IOException) {
                        error = "Нет соединения с сервером."
                    } catch (e: Exception) {
                        error = "Не удалось создать домохозяйство. ${e.message ?: "Попробуй ещё раз."}"
                    }
                }
            }
        )
    }

    Scaffold(
        topBar = {
            TopAppBar(
                title = { Text("Smart Pantry") }
            )
        },
        bottomBar = {
            NavigationBar {
                MainTab.entries.forEach { tab ->
                    NavigationBarItem(
                        selected = selectedTab == tab,
                        onClick = { selectedTab = tab },
                        icon = {
                            Text(
                                if (tab == MainTab.HOUSEHOLDS) "⌂" else "●"
                            )
                        },
                        label = { Text(tab.title) }
                    )
                }
            }
        }
    ) { padding ->
        when (selectedTab) {
            MainTab.HOUSEHOLDS -> {
                Column(
                    modifier = Modifier
                        .fillMaxSize()
                        .padding(padding)
                        .padding(16.dp),
                    verticalArrangement = Arrangement.spacedBy(12.dp)
                ) {
                    Text(
                        text = "Мои домохозяйства",
                        style = MaterialTheme.typography.headlineMedium
                    )

                    Button(
                        onClick = { showCreateDialog = true },
                        modifier = Modifier.fillMaxWidth()
                    ) {
                        Text("Создать домохозяйство")
                    }
                    Text(
                        "Можно создать не более 5 домохозяйств.",
                        style = MaterialTheme.typography.bodySmall
                    )

                    error?.let {
                        Text(
                            text = it,
                            color = MaterialTheme.colorScheme.error
                        )
                        OutlinedButton(onClick = { refreshKey++ }) {
                            Text("Повторить загрузку")
                        }
                    }

                    if (isLoading) {
                        CircularProgressIndicator()
                    } else if (error == null && households.isEmpty()) {
                        Text(
                            "Пока нет домохозяйств. Создай дом для себя " +
                                    "или своей семьи."
                        )
                    } else if (error == null) {
                        LazyColumn(
                            verticalArrangement = Arrangement.spacedBy(8.dp)
                        ) {
                            items(
                                items = households,
                                key = { it.id }
                            ) { household ->
                                Card(
                                    modifier = Modifier
                                        .fillMaxWidth()
                                        .clickable {
                                            selectedHousehold = household
                                        }
                                ) {
                                    Row(
                                        modifier = Modifier
                                            .fillMaxWidth()
                                            .padding(16.dp),
                                        verticalAlignment = Alignment.CenterVertically,
                                        horizontalArrangement = Arrangement.SpaceBetween
                                    ) {
                                        Column(
                                            modifier = Modifier.weight(1f),
                                            verticalArrangement = Arrangement.spacedBy(4.dp)
                                        ) {
                                            Text(
                                                household.name,
                                                style = MaterialTheme.typography.titleMedium
                                            )
                                            Text(
                                                "ID: ${household.id}",
                                                style = MaterialTheme.typography.bodySmall
                                            )
                                        }
                                        Text("›")
                                    }
                                }
                            }
                        }
                    }
                }
            }

            MainTab.PROFILE -> {
                ProfileScreen(
                    user = user,
                    onLogout = onLogout,
                    modifier = Modifier
                        .fillMaxSize()
                        .padding(padding)
                )
            }
        }
    }
}

@Composable
private fun CreateHouseholdDialog(
    onDismiss: () -> Unit,
    onCreate: (String) -> Unit
) {
    var name by remember { mutableStateOf("") }

    AlertDialog(
        onDismissRequest = onDismiss,
        title = { Text("Новое домохозяйство") },
        text = {
            OutlinedTextField(
                value = name,
                onValueChange = { name = it },
                label = { Text("Название") },
                placeholder = { Text("Например, Дом родителей") },
                singleLine = true,
                keyboardOptions = KeyboardOptions(
                    capitalization = KeyboardCapitalization.Sentences,
                    keyboardType = KeyboardType.Text
                )
            )
        },
        confirmButton = {
            TextButton(
                onClick = { onCreate(name.trim()) },
                enabled = name.isNotBlank()
            ) {
                Text("Создать")
            }
        },
        dismissButton = {
            TextButton(onClick = onDismiss) {
                Text("Отмена")
            }
        }
    )
}

@Composable
private fun ProfileScreen(
    user: UserResponse,
    onLogout: () -> Unit,
    modifier: Modifier = Modifier
) {
    Column(
        modifier = modifier
            .padding(20.dp)
            .verticalScroll(rememberScrollState()),
        verticalArrangement = Arrangement.spacedBy(12.dp)
    ) {
        Text(
            "Профиль",
            style = MaterialTheme.typography.headlineMedium
        )
        Text("Имя пользователя: ${user.username}")
        Text("Email: ${user.email}")
        Text("ID пользователя: ${user.id}")

        Spacer(Modifier.size(8.dp))

        Button(onClick = onLogout) {
            Text("Выйти из аккаунта")
        }
    }
}