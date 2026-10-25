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
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.rememberCoroutineScope
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.input.KeyboardType
import androidx.compose.ui.unit.dp
import com.smartpantry.app.data.local.TokenStorage
import com.smartpantry.app.data.model.HouseholdResponse
import com.smartpantry.app.data.model.InventoryItemCreateRequest
import com.smartpantry.app.data.model.InventoryItemResponse
import com.smartpantry.app.data.model.InventoryItemUpdateRequest
import com.smartpantry.app.data.model.ProductResponse
import com.smartpantry.app.data.remote.ApiClient
import kotlinx.coroutines.CancellationException
import kotlinx.coroutines.launch
import retrofit2.HttpException
import java.io.IOException

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun InventoryScreen(household: HouseholdResponse, onBack: () -> Unit) {
    val context = LocalContext.current
    val scope = rememberCoroutineScope()
    var inventory by remember { mutableStateOf<List<InventoryItemResponse>>(emptyList()) }
    var products by remember { mutableStateOf<Map<Int, ProductResponse>>(emptyMap()) }
    var searchText by remember { mutableStateOf("") }
    var searchResults by remember { mutableStateOf<List<ProductResponse>>(emptyList()) }
    var quantityText by remember { mutableStateOf("1") }
    var selectedProduct by remember { mutableStateOf<ProductResponse?>(null) }
    var isLoading by remember { mutableStateOf(true) }
    var isWorking by remember { mutableStateOf(false) }
    var error by remember { mutableStateOf<String?>(null) }
    var refreshKey by remember { mutableStateOf(0) }

    fun tokenOrThrow(): String = TokenStorage.getAccessToken(context)
        ?: throw IllegalStateException("Сессия не найдена. Войди в приложение снова.")

    fun loadInventory() {
        scope.launch {
            isLoading = true
            error = null
            try {
                val token = tokenOrThrow()
                inventory = ApiClient.inventoryApi.getInventory("Bearer $token", household.id)
                val loadedProducts = mutableMapOf<Int, ProductResponse>()
                inventory.forEach { item ->
                    try {
                        loadedProducts[item.product_id] = ApiClient.inventoryApi.getProduct(item.product_id)
                    } catch (_: HttpException) {
                        // Не скрываем весь список запасов, если каталоговый объект недоступен.
                    }
                }
                products = loadedProducts
            } catch (e: CancellationException) { throw e }
            catch (e: HttpException) {
                error = when (e.code()) {
                    401 -> "Сессия истекла. Войди в приложение снова."
                    403 -> "У тебя нет доступа к запасам этого дома."
                    else -> "Не удалось загрузить запасы: ${e.code()}"
                }
            } catch (e: IOException) { error = "Нет соединения с сервером." }
            catch (e: Exception) { error = e.message ?: "Не удалось загрузить запасы." }
            finally { isLoading = false }
        }
    }

    LaunchedEffect(household.id, refreshKey) { loadInventory() }

    fun performInventoryAction(action: suspend (String) -> Unit) {
        scope.launch {
            isWorking = true
            error = null
            try {
                action(tokenOrThrow())
                refreshKey++
                selectedProduct = null
                searchResults = emptyList()
            } catch (e: CancellationException) { throw e }
            catch (e: HttpException) {
                error = when (e.code()) {
                    401 -> "Сессия истекла. Войди в приложение снова."
                    403 -> "Недостаточно прав для изменения запасов."
                    404 -> "Такого продукта нет в каталоге или запасах."
                    422 -> "Сервер отклонил количество. Укажи число больше нуля, не более 3 знаков после запятой."
                    else -> "Ошибка сервера: ${e.code()}"
                }
            } catch (e: IOException) { error = "Нет соединения с сервером." }
            catch (e: Exception) { error = e.message ?: "Не удалось изменить запасы." }
            finally { isWorking = false }
        }
    }

    Scaffold(topBar = {
        TopAppBar(title = { Text("Запасы продуктов") }, navigationIcon = {
            TextButton(onClick = onBack) { Text("Назад") }
        })
    }) { padding ->
        Column(
            modifier = Modifier.fillMaxSize().padding(padding).padding(16.dp),
            verticalArrangement = Arrangement.spacedBy(10.dp)
        ) {
            Text(household.name, style = MaterialTheme.typography.titleMedium)
            Text("Добавить продукт из каталога", style = MaterialTheme.typography.titleSmall)
            Row(verticalAlignment = Alignment.CenterVertically, horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                OutlinedTextField(
                    value = searchText, onValueChange = { searchText = it },
                    label = { Text("Название продукта") }, modifier = Modifier.weight(1f),
                    singleLine = true
                )
                Button(enabled = !isWorking && searchText.isNotBlank(), onClick = {
                    scope.launch {
                        error = null
                        try {
                            searchResults = ApiClient.inventoryApi.searchProducts(searchText.trim())
                            if (searchResults.isEmpty()) error = "Продукт не найден в каталоге. Сейчас добавить можно только существующие продукты."
                        } catch (e: HttpException) { error = "Поиск не удался: ${e.code()}" }
                        catch (e: IOException) { error = "Нет соединения с сервером." }
                    }
                }) { Text("Найти") }
            }
            if (searchResults.isNotEmpty()) {
                Text("Выбери продукт из результатов:", style = MaterialTheme.typography.bodyMedium)
                LazyColumn(modifier = Modifier.weight(0.8f, fill = false), verticalArrangement = Arrangement.spacedBy(6.dp)) {
                    items(searchResults, key = { it.id }) { product ->
                        Card(modifier = Modifier.fillMaxWidth()) {
                            Row(modifier = Modifier.fillMaxWidth().padding(10.dp), verticalAlignment = Alignment.CenterVertically) {
                                Column(modifier = Modifier.weight(1f)) {
                                    Text(product.name, style = MaterialTheme.typography.titleSmall)
                                    Text(listOfNotNull(product.brand, "Ед. изм.: ${product.unit}").joinToString(" · "))
                                }
                                TextButton(onClick = { selectedProduct = product; quantityText = "1" }) { Text("Добавить") }
                            }
                        }
                    }
                }
            }
            Text("Текущие запасы", style = MaterialTheme.typography.titleMedium)
            error?.let { Text(it, color = MaterialTheme.colorScheme.error) }
            if (isLoading) CircularProgressIndicator()
            else if (inventory.isEmpty()) Text("В этом доме пока нет продуктов.")
            else LazyColumn(modifier = Modifier.weight(1f), verticalArrangement = Arrangement.spacedBy(8.dp)) {
                items(inventory, key = { it.product_id }) { item ->
                    val product = products[item.product_id]
                    Card(modifier = Modifier.fillMaxWidth()) {
                        Column(modifier = Modifier.fillMaxWidth().padding(12.dp), verticalArrangement = Arrangement.spacedBy(6.dp)) {
                            Text(product?.name ?: "Продукт #${item.product_id}", style = MaterialTheme.typography.titleMedium)
                            product?.brand?.let { Text(it) }
                            Text("Количество: ${item.quantity} ${product?.unit.orEmpty()}".trim())
                            Row(horizontalArrangement = Arrangement.spacedBy(8.dp), verticalAlignment = Alignment.CenterVertically) {
                                OutlinedButton(enabled = !isWorking && item.quantity > 0, onClick = {
                                    val newQuantity = (item.quantity - 1.0).coerceAtLeast(0.0)
                                    performInventoryAction {
                                        if (newQuantity == 0.0) {
                                            val response = ApiClient.inventoryApi.deleteInventoryItem("Bearer $it", household.id, item.product_id)
                                            if (!response.isSuccessful) throw IllegalStateException("Не удалось удалить продукт: ${response.code()}")
                                        } else ApiClient.inventoryApi.updateInventoryItem("Bearer $it", household.id, item.product_id, InventoryItemUpdateRequest(newQuantity))
                                    }
                                }) { Text("−1") }
                                OutlinedButton(enabled = !isWorking, onClick = {
                                    performInventoryAction {
                                        ApiClient.inventoryApi.updateInventoryItem("Bearer $it", household.id, item.product_id, InventoryItemUpdateRequest(item.quantity + 1.0))
                                    }
                                }) { Text("+1") }
                                TextButton(enabled = !isWorking, onClick = {
                                    performInventoryAction {
                                        val response = ApiClient.inventoryApi.deleteInventoryItem("Bearer $it", household.id, item.product_id)
                                        if (!response.isSuccessful) throw IllegalStateException("Не удалось удалить продукт: ${response.code()}")
                                    }
                                }) { Text("Удалить") }
                            }
                        }
                    }
                }
            }
        }
    }

    if (selectedProduct != null) {
        AlertDialog(
            onDismissRequest = { if (!isWorking) selectedProduct = null },
            title = { Text("Добавить продукт") },
            text = {
                Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
                    Text(selectedProduct!!.name)
                    Text("Если продукт уже есть в запасах, сервер прибавит указанное количество к текущему.")
                    OutlinedTextField(
                        value = quantityText, onValueChange = { quantityText = it },
                        label = { Text("Количество (${selectedProduct!!.unit})") },
                        keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Decimal),
                        singleLine = true
                    )
                }
            },
            confirmButton = {
                TextButton(enabled = !isWorking && (quantityText.toDoubleOrNull() ?: 0.0) > 0.0, onClick = {
                    val product = selectedProduct!!
                    val quantity = quantityText.toDoubleOrNull() ?: return@TextButton
                    performInventoryAction {
                        ApiClient.inventoryApi.addInventoryItem("Bearer $it", household.id, InventoryItemCreateRequest(product.id, quantity))
                    }
                }) { Text("Добавить") }
            },
            dismissButton = { TextButton(onClick = { selectedProduct = null }) { Text("Отмена") } }
        )
    }
}
