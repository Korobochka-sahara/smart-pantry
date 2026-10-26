
package com.smartpantry.app.ui.screens.home

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.material3.AlertDialog
import androidx.compose.material3.Button
import androidx.compose.material3.Card
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.material3.TopAppBar
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.input.KeyboardType
import androidx.compose.ui.unit.dp
import androidx.compose.ui.graphics.Color
import com.smartpantry.app.data.model.HouseholdMemberResponse
import com.smartpantry.app.data.model.HouseholdResponse

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun HouseholdSettingsScreen(
    household: HouseholdResponse,
    members: List<HouseholdMemberResponse>,
    currentUserId: Int,
    currentUserRole: String,
    isLoading: Boolean,
    isWorking: Boolean,
    error: String?,
    onBack: () -> Unit,
    onRetry: () -> Unit,
    onAddMember: (Int) -> Unit,
    onChangeRole: (Int, String) -> Unit,
    onRemoveMember: (Int) -> Unit,
    onLeave: () -> Unit
) {
    var showAddDialog by remember { mutableStateOf(false) }
    var memberForRemoval by remember {
        mutableStateOf<HouseholdMemberResponse?>(null)
    }
    var memberForRoleChange by remember {
        mutableStateOf<HouseholdMemberResponse?>(null)
    }
    var showLeaveDialog by remember { mutableStateOf(false) }

    val role = currentUserRole.uppercase()
    val isOwner = role == "OWNER"
    val canManageMembers = isOwner || role == "ADMIN"

    Scaffold(
        topBar = {
            TopAppBar(
                title = { Text("Настройки дома") },
                navigationIcon = {
                    TextButton(onClick = onBack) {
                        Text("Назад")
                    }
                }
            )
        }
    ) { padding ->
        Column(
            modifier = Modifier
                .fillMaxSize()
                .padding(padding)
                .padding(16.dp),
            verticalArrangement = Arrangement.spacedBy(12.dp)
        ) {
            Text(
                household.name,
                style = MaterialTheme.typography.headlineSmall
            )
            Text("Участники и права доступа")

            Text(
                "Твоя роль: ${roleLabel(role)}",
                style = MaterialTheme.typography.titleMedium
            )

            if (isLoading) {
                CircularProgressIndicator()
            } else if (members.isEmpty()) {
                Text("Список участников пуст.")
            } else {
                val orderedMembers = members.sortedWith(
                    compareBy<HouseholdMemberResponse> {
                        when {
                            it.user_id == currentUserId -> 0
                            it.role.uppercase() == "OWNER" -> 1
                            it.role.uppercase() == "ADMIN" -> 2
                            else -> 3
                        }
                    }.thenBy { it.username.lowercase() }
                )
                LazyColumn(
                    modifier = Modifier.weight(1f),
                    verticalArrangement = Arrangement.spacedBy(8.dp)
                ) {
                    items(orderedMembers, key = { it.user_id }) { member ->
                        val memberRole = member.role.uppercase()
                        val isSelf = member.user_id == currentUserId

                        // Нельзя управлять владельцем.
                        val canEditMember = canManageMembers &&
                                !isSelf &&
                                memberRole != "OWNER" &&
                                (isOwner || memberRole == "MEMBER")

                        val cardColor = when (memberRole) {
                            "OWNER" -> Color(0xFFFFE3E3)
                            "ADMIN" -> Color(0xFFEDE3FF)
                            else -> MaterialTheme.colorScheme.surface
                        }
                        Card(
                            modifier = Modifier.fillMaxWidth(),
                            colors = androidx.compose.material3.CardDefaults.cardColors(
                                containerColor = cardColor
                            )
                        ) {
                            Column(
                                modifier = Modifier.padding(12.dp),
                                verticalArrangement = Arrangement.spacedBy(6.dp)
                            ) {
                                Text(
                                    text = buildString {
                                        append(member.username)
                                        if (isSelf) append(" · ты")
                                    },
                                    style = MaterialTheme.typography.titleMedium
                                )
                                Text("Роль: ${roleLabel(memberRole)}")
                                Text(
                                    "Дата вступления: ${formatJoinedDate(member.joined_at)}",
                                    style = MaterialTheme.typography.bodySmall
                                )

                                if (canEditMember) {
                                    Row(
                                        modifier = Modifier.fillMaxWidth(),
                                        horizontalArrangement = Arrangement.spacedBy(8.dp)
                                    ) {
                                        if (memberRole == "MEMBER") {
                                            OutlinedButton(
                                                enabled = !isWorking,
                                                onClick = {
                                                    memberForRoleChange = member
                                                }
                                            ) {
                                                Text("Дать права администратора")
                                            }
                                        } else if (memberRole == "ADMIN" && isOwner) {
                                            OutlinedButton(
                                                enabled = !isWorking,
                                                onClick = {
                                                    memberForRoleChange = member
                                                }
                                            ) {
                                                Text("Отнять права администратора")
                                            }
                                        }

                                        TextButton(
                                            enabled = !isWorking,
                                            onClick = {
                                                memberForRemoval = member
                                            }
                                        ) {
                                            Text("Удалить")
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }

            if (error != null) {
                Text(
                    text = error,
                    color = MaterialTheme.colorScheme.error
                )
                OutlinedButton(
                    enabled = !isWorking,
                    onClick = onRetry
                ) {
                    Text("Обновить")
                }
            }

            Text("Участники: ${members.size}/20", style = MaterialTheme.typography.bodySmall)
            if (members.size >= 18 && members.size < 20) {
                Text(
                    "Внимание: в домохозяйстве может быть не больше 20 участников.",
                    color = MaterialTheme.colorScheme.error,
                    style = MaterialTheme.typography.bodySmall
                )
            }
            if (members.size >= 20) {
                Text(
                    "Достигнут лимит: в домохозяйстве уже 20 участников. Добавить новых нельзя.",
                    color = MaterialTheme.colorScheme.error
                )
            }
            if (canManageMembers) {
                Button(
                    modifier = Modifier.fillMaxWidth(),
                    enabled = !isWorking && members.size < 20,
                    onClick = { showAddDialog = true }
                ) {
                    Text("Добавить участника по ID")
                }
            }

            OutlinedButton(
                modifier = Modifier.fillMaxWidth(),
                enabled = !isWorking,
                onClick = { showLeaveDialog = true }
            ) {
                Text("Покинуть дом")
            }
        }
    }

    if (showAddDialog) {
        AddMemberDialog(
            onDismiss = { showAddDialog = false },
            onAdd = { userId ->
                showAddDialog = false
                onAddMember(userId)
            }
        )
    }

    memberForRoleChange?.let { member ->
        val memberRole = member.role.uppercase()
        val newRole = if (memberRole == "MEMBER") "ADMIN" else "MEMBER"

        AlertDialog(
            onDismissRequest = { memberForRoleChange = null },
            title = {
                Text(
                    if (newRole == "ADMIN") {
                        "Выдать права администратора?"
                    } else {
                        "Отнять права администратора?"
                    }
                )
            },
            text = {
                Text(
                    if (newRole == "ADMIN") {
                        "Пользователь ${member.username} получит возможность удалять и добавлять участников."
                    }
                    else{
                        "Пользователь ${member.username} потеряет возможность удалять и добавлять участников."
                    }
                )
            },
            confirmButton = {
                TextButton(
                    enabled = !isWorking,
                    onClick = {
                        memberForRoleChange = null
                        onChangeRole(member.user_id, newRole)
                    }
                ) {
                    Text("Подтвердить")
                }
            },
            dismissButton = {
                TextButton(onClick = { memberForRoleChange = null }) {
                    Text("Отмена")
                }
            }
        )
    }

    memberForRemoval?.let { member ->
        AlertDialog(
            onDismissRequest = { memberForRemoval = null },
            title = { Text("Удалить участника?") },
            text = {
                Text(
                    "Пользователь #${member.user_id} потеряет доступ к дому."
                )
            },
            confirmButton = {
                TextButton(
                    enabled = !isWorking,
                    onClick = {
                        memberForRemoval = null
                        onRemoveMember(member.user_id)
                    }
                ) {
                    Text("Удалить")
                }
            },
            dismissButton = {
                TextButton(onClick = { memberForRemoval = null }) {
                    Text("Отмена")
                }
            }
        )
    }

    if (showLeaveDialog) {
        AlertDialog(
            onDismissRequest = { showLeaveDialog = false },
            title = { Text("Покинуть дом?") },
            text = {
                Text(
                    if (isOwner) {
                        "Ты владелец дома. Если ты покинешь дом - владение передастся кому-то ещё"
                    } else {
                        "Ты потеряешь доступ к продуктам и участникам этого дома."
                    }
                )
            },
            confirmButton = {
                TextButton(
                    enabled = !isWorking,
                    onClick = {
                        showLeaveDialog = false
                        onLeave()
                    }
                ) {
                    Text("Покинуть")
                }
            },
            dismissButton = {
                TextButton(onClick = { showLeaveDialog = false }) {
                    Text("Отмена")
                }
            }
        )
    }
}

@Composable
private fun AddMemberDialog(
    onDismiss: () -> Unit,
    onAdd: (Int) -> Unit
) {
    var userIdText by remember { mutableStateOf("") }
    val userId = userIdText.toIntOrNull()

    AlertDialog(
        onDismissRequest = onDismiss,
        title = { Text("Добавить участника") },
        text = {
            Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
                Text("Введи ID существующего пользователя.")
                OutlinedTextField(
                    value = userIdText,
                    onValueChange = { input ->
                        userIdText = input.filter { it.isDigit() }
                    },
                    label = { Text("ID пользователя") },
                    keyboardOptions = KeyboardOptions(
                        keyboardType = KeyboardType.Number
                    ),
                    singleLine = true
                )
            }
        },
        confirmButton = {
            TextButton(
                enabled = userId != null && userId > 0,
                onClick = { userId?.let(onAdd) }
            ) {
                Text("Добавить")
            }
        },
        dismissButton = {
            TextButton(onClick = onDismiss) {
                Text("Отмена")
            }
        }
    )
}

private fun roleLabel(role: String): String = when (role.uppercase()) {
    "OWNER" -> "Владелец"
    "ADMIN" -> "Администратор"
    "MEMBER" -> "Участник"
    else -> role
}

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun TrackedProductsScreen(
    household: HouseholdResponse,
    onBack: () -> Unit
) {
    Scaffold(
        topBar = {
            TopAppBar(
                title = { Text("Отслеживаемые продукты") },
                navigationIcon = {
                    TextButton(onClick = onBack) {
                        Text("Назад")
                    }
                }
            )
        }
    ) { padding ->
        Column(
            modifier = Modifier
                .fillMaxSize()
                .padding(padding)
                .padding(20.dp),
            verticalArrangement = Arrangement.spacedBy(12.dp)
        ) {
            Text(household.name, style = MaterialTheme.typography.titleMedium)
            Text("ID дома: ${household.id}")
            Text(
                "Здесь будут продукты, для которых установлен минимальный запас."
            )
            Text(
                "Подключим этот экран к API TrackedProduct после реализации " +
                        "списка запасов."
            )
        }
    }
}

private fun formatJoinedDate(value: String): String {
    // FastAPI serializes datetime as ISO-8601: yyyy-MM-ddTHH:mm:ss.
    val date = value.substringBefore('T').substringBefore(' ')
    val parts = date.split('-')
    return if (parts.size == 3) "${parts[2]}.${parts[1]}.${parts[0]}" else value
}
