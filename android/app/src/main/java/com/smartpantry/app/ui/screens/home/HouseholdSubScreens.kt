
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
import kotlinx.coroutines.launch
import retrofit2.HttpException
import java.io.IOException
import com.smartpantry.app.data.remote.ApiClient
import com.smartpantry.app.data.model.ProductResponse
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.material3.TopAppBar
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
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
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.foundation.layout.heightIn
import com.smartpantry.app.data.local.TokenStorage
import com.smartpantry.app.data.model.TrackedProductCreateRequest

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
                                        } else if (memberRole == "ADMIN") {
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
    val context = androidx.compose.ui.platform.LocalContext.current
    val scope = androidx.compose.runtime.rememberCoroutineScope()
    var tracked by remember { mutableStateOf<List<com.smartpantry.app.data.model.TrackedProductResponse>>(emptyList()) }
    var productNames by remember { mutableStateOf<Map<Int, ProductResponse>>(emptyMap()) }
    var search by remember { mutableStateOf("") }
    var searchResults by remember { mutableStateOf<List<ProductResponse>>(emptyList()) }
    var minimums by remember { mutableStateOf<Map<Int, String>>(emptyMap()) }
    var loading by remember { mutableStateOf(true) }
    var working by remember { mutableStateOf(false) }
    var error by remember { mutableStateOf<String?>(null) }
    var refreshKey by remember { androidx.compose.runtime.mutableIntStateOf(0) }
    var currentQuantities by remember {
        mutableStateOf<Map<Int, Double>>(emptyMap())
    }
    var showGeneratedList by remember {
        mutableStateOf(false)
    }

    fun tokenOrThrow(): String =
        TokenStorage.getAccessToken(context)?: throw IllegalStateException(
            "Сессия не найдена. Войди в приложение снова."
        )

    fun load() {
        scope.launch {
            loading = true
            error = null
            try {
                val token = "Bearer ${tokenOrThrow()}"
                tracked = ApiClient.trackedProductApi.getTrackedProducts(token, household.id)
                val inventoryItems = ApiClient.inventoryApi.getInventory(
                    token,
                    household.id
                )
                currentQuantities = inventoryItems.associate {
                    it.product_id to it.quantity
                }

                val loaded = mutableMapOf<Int, ProductResponse>()
                tracked.forEach { item ->
                    try { loaded[item.product_id] = ApiClient.inventoryApi.getProduct(item.product_id) }
                    catch (_: Exception) { }
                }
                productNames = loaded
                minimums = tracked.associate { it.product_id to it.minimum_quantity.toString() }
            } catch (e: HttpException) {
                error = when (e.code()) {
                    401 -> "Сессия истекла. Войди в приложение снова."
                    403 -> "Нет доступа к этому дому."
                    else -> "Ошибка сервера: ${e.code()}"
                }
            } catch (e: IOException) { error = "Нет соединения с сервером." }
            catch (e: Exception) { error = e.message ?: "Не удалось загрузить список." }
            finally { loading = false }
        }
    }

    LaunchedEffect(household.id, refreshKey) { load() }

    Scaffold(topBar = {
        TopAppBar(title = { Text("Отслеживаемые продукты") }, navigationIcon = {
            TextButton(onClick = onBack) { Text("Назад") }
        })
    }) { padding ->
        Column(
            modifier = Modifier.fillMaxSize().padding(padding).padding(16.dp),
            verticalArrangement = Arrangement.spacedBy(10.dp)
        ) {
            Text(household.name, style = MaterialTheme.typography.titleMedium)
            Text("Добавь продукты и укажи минимальный запас для всей семьи.")
            OutlinedTextField(
                value = search,
                onValueChange = { search = it },
                label = { Text("Найти продукт в каталоге") },
                singleLine = true,
                modifier = Modifier.fillMaxWidth()
            )
            Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                Button(enabled = search.isNotBlank() && !working, onClick = {
                    scope.launch {
                        try {
                            searchResults = ApiClient.inventoryApi.searchProducts(search.trim(), 10)
                            if (searchResults.isEmpty()) error = "В каталоге ничего не найдено."
                        } catch (e: Exception) { error = "Не удалось выполнить поиск: ${e.message}" }
                    }
                }) { Text("Найти") }
                TextButton(onClick = { search = ""; searchResults = emptyList() }) { Text("Очистить") }
            }
            searchResults.forEach { product ->
                Card(Modifier.fillMaxWidth()) {
                    Row(
                        modifier = Modifier.fillMaxWidth().padding(10.dp),
                        verticalAlignment = Alignment.CenterVertically,
                        horizontalArrangement = Arrangement.SpaceBetween
                    ) {
                        Column(Modifier.weight(1f)) {
                            Text(product.name, style = MaterialTheme.typography.titleSmall)
                            Text(listOfNotNull(product.brand, product.category).joinToString(" · "))
                        }
                        TextButton(enabled = !working && tracked.none { it.product_id == product.id }, onClick = {
                            scope.launch {
                                working = true
                                error = null
                                try {
                                    ApiClient.trackedProductApi.addTrackedProduct(
                                        "Bearer ${tokenOrThrow()}", household.id,
                                        TrackedProductCreateRequest(product.id, 1)
                                    )
                                    searchResults = emptyList()
                                    search = ""
                                    refreshKey++
                                } catch (e: HttpException) {
                                    error = when (e.code()) {
                                        409 -> "Этот продукт уже отслеживается."
                                        404 -> "Продукт не найден в каталоге."
                                        else -> "Ошибка сервера: ${e.code()}"
                                    }
                                } catch (e: Exception) { error = e.message ?: "Не удалось добавить продукт." }
                                finally { working = false }
                            }
                        }) { Text(if (tracked.any { it.product_id == product.id }) "Уже добавлен" else "Добавить") }
                    }
                }
            }
            error?.let { Text(it, color = MaterialTheme.colorScheme.error) }
            Text("Список семьи", style = MaterialTheme.typography.titleMedium)
            Button(
                modifier = Modifier.fillMaxWidth(),
                enabled = !loading,
                onClick = { showGeneratedList = true }
            ) {
                Text("Сгенерировать список")
            }
            if (loading) CircularProgressIndicator()
            else if (tracked.isEmpty()) Text("Пока нет отслеживаемых продуктов. Найди продукт выше и добавь его.")
            else LazyColumn(
                modifier = Modifier.weight(1f),
                verticalArrangement = Arrangement.spacedBy(8.dp)
            ) {
                items(tracked, key = { it.product_id }) { item ->
                    val product = productNames[item.product_id]
                    val minimumText = minimums[item.product_id] ?: item.minimum_quantity.toString()
                    val current = currentQuantities[item.product_id] ?: 0.0
                    val minimum = item.minimum_quantity.toDouble()
                    val missing = (minimum - current).coerceAtLeast(0.0)
                    Card(Modifier.fillMaxWidth()) {
                        Column(Modifier.fillMaxWidth().padding(12.dp), verticalArrangement = Arrangement.spacedBy(6.dp)) {
                            Text(product?.name ?: "Продукт #${item.product_id}", style = MaterialTheme.typography.titleMedium)
                            product?.brand?.let { Text(it) }
                            Text("Минимальный запас: ${item.minimum_quantity} ${product?.unit.orEmpty()}")
                            when {
                                current == 0.0 -> {
                                    Text(
                                        "Нет в запасах · нужно добавить " +
                                                "${missing.toInt()} ${product?.unit.orEmpty()}",
                                        color = MaterialTheme.colorScheme.error
                                    )
                                }

                                current < minimum -> {
                                    Text(
                                        "Сейчас: $current ${product?.unit.orEmpty()} · " +
                                                "не хватает $missing ${product?.unit.orEmpty()}",
                                        color = MaterialTheme.colorScheme.error
                                    )
                                }

                                else -> {
                                    Text(
                                        "Сейчас: $current ${product?.unit.orEmpty()} · Запаса достаточно",
                                        color = MaterialTheme.colorScheme.primary
                                    )
                                }
                            }
                            OutlinedTextField(
                                value = minimumText,
                                onValueChange = { minimums = minimums + (item.product_id to it) },
                                label = { Text("Новый минимальный запас") },
                                keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Number),
                                singleLine = true,
                                modifier = Modifier.fillMaxWidth()
                            )
                            Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                                Button(enabled = !working && minimumText.toIntOrNull()?.let { it > 0 } == true,
                                    onClick = {
                                        scope.launch {
                                            working = true
                                            error = null
                                            try {
                                                ApiClient.trackedProductApi.updateTrackedProduct(
                                                    "Bearer ${tokenOrThrow()}", household.id, item.product_id,
                                                    com.smartpantry.app.data.model.TrackedProductUpdateRequest(minimumText.toInt())
                                                )
                                                refreshKey++
                                            } catch (e: Exception) { error = "Не удалось сохранить порог: ${e.message}" }
                                            finally { working = false }
                                        }
                                    }) { Text("Сохранить") }
                                TextButton(enabled = !working, onClick = {
                                    scope.launch {
                                        working = true
                                        error = null
                                        try {
                                            val response = ApiClient.trackedProductApi.deleteTrackedProduct(
                                                "Bearer ${tokenOrThrow()}", household.id, item.product_id
                                            )
                                            if (!response.isSuccessful) throw IllegalStateException("HTTP ${response.code()}")
                                            refreshKey++
                                        } catch (e: Exception) { error = "Не удалось удалить продукт: ${e.message}" }
                                        finally { working = false }
                                    }
                                }) { Text("Удалить") }
                            }
                        }
                    }
                }
            }
        }
        if (showGeneratedList) {
            val missingProducts = tracked.mapNotNull { item ->
                val current = currentQuantities[item.product_id] ?: 0.0
                val minimum = item.minimum_quantity.toDouble()

                if (current < minimum) {
                    val missing = minimum - current
                    val product = productNames[item.product_id]

                    "${product?.name ?: "Продукт #${item.product_id}"} — " +
                            "${missing.toString().removeSuffix(".0")} ${product?.unit.orEmpty()}"
                } else {
                    null
                }
            }

            AlertDialog(
                onDismissRequest = { showGeneratedList = false },
                title = { Text("Список покупок") },
                text = {
                    if (missingProducts.isEmpty()) {
                        Text("Все отслеживаемые продукты есть в достаточном количестве.")
                    } else {
                        Column(
                            modifier = Modifier
                                .fillMaxWidth()
                                .heightIn(max = 350.dp)
                                .verticalScroll(rememberScrollState()),
                            verticalArrangement = Arrangement.spacedBy(8.dp)
                        ) {
                            missingProducts.forEach { product ->
                                Text("• $product")
                            }
                        }
                    }
                },
                confirmButton = {
                    TextButton(onClick = { showGeneratedList = false }) {
                        Text("Закрыть")
                    }
                }
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
