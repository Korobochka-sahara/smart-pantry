package com.smartpantry.app.ui.screens.home

import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.Card
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.material3.TopAppBar
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableIntStateOf
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.rememberCoroutineScope
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.unit.dp
import com.smartpantry.app.data.local.TokenStorage
import com.smartpantry.app.data.model.AddHouseholdMemberRequest
import com.smartpantry.app.data.model.HouseholdMemberResponse
import com.smartpantry.app.data.model.HouseholdResponse
import com.smartpantry.app.data.model.UpdateHouseholdMemberRoleRequest
import com.smartpantry.app.data.model.UserResponse
import com.smartpantry.app.data.remote.ApiClient
import kotlinx.coroutines.CancellationException
import kotlinx.coroutines.launch
import retrofit2.HttpException
import java.io.IOException

private enum class HouseholdSection {
    INVENTORY,
    TRACKED_PRODUCTS,
    SETTINGS
}

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun HouseholdDetailScreen(
    household: HouseholdResponse,
    user: UserResponse,
    onBack: () -> Unit,
    onLeave: () -> Unit
) {
    val context = LocalContext.current
    val scope = rememberCoroutineScope()

    var members by remember {
        mutableStateOf<List<HouseholdMemberResponse>>(emptyList())
    }
    var isLoading by remember {
        mutableStateOf(true)
    }
    var error by remember {
        mutableStateOf<String?>(null)
    }
    var refreshKey by remember {
        mutableIntStateOf(0)
    }
    var selectedSection by remember {
        mutableStateOf<HouseholdSection?>(null)
    }
    var isWorking by remember {
        mutableStateOf(false)
    }

    LaunchedEffect(household.id, refreshKey) {
        isLoading = true
        error = null

        try {
            val token = TokenStorage.getAccessToken(context)
                ?: throw IllegalStateException("Сессия не найдена")

            members = ApiClient.householdApi.getMembers(
                authorization = "Bearer $token",
                householdId = household.id
            )
        } catch (e: CancellationException) {
            throw e
        } catch (e: HttpException) {
            error = when (e.code()) {
                401 -> "Сессия истекла. Войди в приложение снова."
                403 -> "У тебя нет доступа к участникам этого дома."
                else -> "Не удалось загрузить участников: ${e.code()}"
            }
        } catch (e: IOException) {
            error = "Нет соединения с сервером."
        } catch (e: Exception) {
            error = e.message ?: "Не удалось загрузить участников."
        } finally {
            isLoading = false
        }
    }

    val currentRole = members
        .firstOrNull { it.user_id == user.id }
        ?.role
        ?.uppercase()
        ?: "MEMBER"

    fun runHouseholdAction(
        action: suspend (String) -> Unit,
        onSuccess: (() -> Unit)? = null
    ) {
        scope.launch {
            isWorking = true
            error = null

            try {
                val token = TokenStorage.getAccessToken(context)
                    ?: throw IllegalStateException("Сессия не найдена")

                action(token)

                // Выполняем действие после успешного ответа сервера.
                onSuccess?.invoke()

                // Обновляем список участников после изменения.
                refreshKey++
            } catch (e: CancellationException) {
                throw e
            } catch (e: HttpException) {
                error = when (e.code()) {
                    401 -> "Сессия истекла. Войди в приложение снова."
                    403 -> "Сервер запретил действие: недостаточно прав."
                    404 -> "Дом или пользователь не найден."
                    409 -> "Действие невозможно: проверь состав дома и роли."
                    422 -> "Сервер отклонил данные. Проверь введённый ID и роль."
                    else -> "Ошибка сервера: ${e.code()}"
                }
            } catch (e: IOException) {
                error = "Нет соединения с сервером."
            } catch (e: Exception) {
                error = e.message ?: "Не удалось выполнить действие."
            } finally {
                isWorking = false
            }
        }
    }

    if (selectedSection == HouseholdSection.SETTINGS) {
        HouseholdSettingsScreen(
            household = household,
            members = members,
            currentUserId = user.id,
            currentUserRole = currentRole,
            isLoading = isLoading,
            isWorking = isWorking,
            error = error,
            onBack = {
                selectedSection = null
            },
            onRetry = {
                refreshKey++
            },
            onAddMember = { targetUserId ->
                runHouseholdAction(
                    action = { token ->
                        ApiClient.householdApi.addMember(
                            authorization = "Bearer $token",
                            householdId = household.id,
                            request = AddHouseholdMemberRequest(
                                user_id = targetUserId
                            )
                        )
                    }
                )
            },
            onChangeRole = { targetUserId, newRole ->
                runHouseholdAction(
                    action = { token ->
                        ApiClient.householdApi.updateMemberRole(
                            authorization = "Bearer $token",
                            householdId = household.id,
                            targetUserId = targetUserId,
                            request = UpdateHouseholdMemberRoleRequest(
                                role = newRole
                            )
                        )
                    }
                )
            },
            onRemoveMember = { targetUserId ->
                runHouseholdAction(
                    action = { token ->
                        val response = ApiClient.householdApi.removeMember(
                            authorization = "Bearer $token",
                            householdId = household.id,
                            targetUserId = targetUserId
                        )

                        if (!response.isSuccessful) {
                            throw IllegalStateException(
                                "Не удалось удалить участника: ${response.code()}"
                            )
                        }
                    }
                )
            },
            onLeave = {
                runHouseholdAction(
                    action = { token ->
                        val response = ApiClient.householdApi.leaveHousehold(
                            authorization = "Bearer $token",
                            householdId = household.id
                        )

                        if (!response.isSuccessful) {
                            throw IllegalStateException(
                                "Не удалось покинуть дом: ${response.code()}"
                            )
                        }
                    },
                    onSuccess = onLeave
                )
            }
        )

        return
    }

    if (selectedSection == HouseholdSection.INVENTORY) {
        InventoryScreen(
            household = household,
            onBack = {
                selectedSection = null
            }
        )
        return
    }

    if (selectedSection == HouseholdSection.TRACKED_PRODUCTS) {
        TrackedProductsScreen(
            household = household,
            onBack = {
                selectedSection = null
            }
        )
        return
    }

    Scaffold(
        topBar = {
            TopAppBar(
                title = {
                    Text(household.name)
                },
                navigationIcon = {
                    TextButton(onClick = onBack) {
                        Text("Назад")
                    }
                },
                actions = {
                    TextButton(
                        onClick = {
                            selectedSection = HouseholdSection.SETTINGS
                        }
                    ) {
                        Text("Настройки")
                    }
                }
            )
        }
    ) { padding ->
        Column(
            modifier = Modifier
                .fillMaxSize()
                .padding(padding)
                .verticalScroll(rememberScrollState())
                .padding(16.dp),
            verticalArrangement = Arrangement.spacedBy(12.dp)
        ) {
            Text(
                text = household.name,
                style = MaterialTheme.typography.headlineMedium
            )

            HouseholdSectionCard(
                title = "Продукты",
                description = "Посмотреть запасы продуктов в этом доме.",
                onClick = {
                    selectedSection = HouseholdSection.INVENTORY
                }
            )

            HouseholdSectionCard(
                title = "Отслеживаемые продукты",
                description = "Посмотреть продукты с минимальным порогом запасов.",
                onClick = {
                    selectedSection = HouseholdSection.TRACKED_PRODUCTS
                }
            )

            if (error != null) {
                Text(
                    text = error!!,
                    color = MaterialTheme.colorScheme.error
                )

                OutlinedButton(
                    onClick = {
                        refreshKey++
                    }
                ) {
                    Text("Повторить загрузку")
                }
            }
        }
    }
}

@Composable
private fun HouseholdSectionCard(
    title: String,
    description: String,
    onClick: () -> Unit
) {
    Card(
        modifier = Modifier
            .fillMaxWidth()
            .clickable(onClick = onClick)
    ) {
        Column(
            modifier = Modifier.padding(16.dp),
            verticalArrangement = Arrangement.spacedBy(8.dp)
        ) {
            Text(
                text = title,
                style = MaterialTheme.typography.titleLarge
            )

            Text(description)

            Text(
                text = "Открыть раздел →",
                color = MaterialTheme.colorScheme.primary
            )
        }
    }
}
