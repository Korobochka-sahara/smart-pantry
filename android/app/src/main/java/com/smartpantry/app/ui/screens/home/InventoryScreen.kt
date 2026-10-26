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
import android.net.Uri
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.result.contract.ActivityResultContracts
import okhttp3.MediaType.Companion.toMediaType
import okhttp3.MultipartBody
import okhttp3.RequestBody.Companion.toRequestBody
import com.smartpantry.app.data.model.OCRResponse
import com.smartpantry.app.data.model.OCRCandidate
import java.net.SocketTimeoutException

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
    var editedQuantities by remember {
        mutableStateOf<Map<Int, String>>(emptyMap())
    }
    var isRecognizing by remember {
        mutableStateOf(false)
    }

    var receiptResult by remember {
        mutableStateOf<OCRResponse?>(null)
    }

    var receiptError by remember {
        mutableStateOf<String?>(null)
    }

    val imagePicker = rememberLauncherForActivityResult(
        contract = ActivityResultContracts.GetContent()
    ) { uri: Uri? ->
        if (uri != null) {
            android.util.Log.d("ReceiptOCR", "Выбрана фотография: $uri")
            scope.launch {
                isRecognizing = true
                receiptError = null
                receiptResult = null

                try {
                    val bytes = context.contentResolver
                        .openInputStream(uri)
                        ?.use { it.readBytes() }
                        ?: throw IOException(
                            "Не удалось прочитать изображение"
                        )

                    val body = bytes.toRequestBody(
                        "image/jpeg".toMediaType()
                    )

                    val part = MultipartBody.Part.createFormData(
                        "file",
                        "receipt.jpg",
                        body
                    )
                    android.util.Log.d(
                        "ReceiptOCR",
                        "Отправка OCR: ${bytes.size} bytes"
                    )
                    receiptResult =
                        ApiClient.ocrApi.recognizeReceipt(part)

                    if (receiptResult?.items.isNullOrEmpty()) {
                        receiptError =
                            "Не удалось найти товары в чеке."
                    }
                } catch (e: HttpException) {
                    android.util.Log.e(
                        "ReceiptOCR",
                        "HTTP ${e.code()}: ${e.response()?.errorBody()?.string()}",
                        e
                    )
                    receiptError = "Ошибка сервера: ${e.code()}"
                } catch (e: java.net.SocketTimeoutException) {
                    android.util.Log.e("ReceiptOCR", "Таймаут OCR", e)
                    receiptError =
                        "Распознавание занимает слишком много времени. Попробуй ещё раз."
                } catch (e: IOException) {
                    android.util.Log.e("ReceiptOCR", "Ошибка чтения файла или сети", e)
                    receiptError = "Ошибка соединения: ${e.message}"
                } catch (e: Exception) {
                    android.util.Log.e("ReceiptOCR", "Неожиданная ошибка", e)
                    receiptError =
                        "${e.javaClass.simpleName}: ${e.message ?: "Неизвестная ошибка"}"
                } finally {
                    isRecognizing = false
                }
            }
        }
    }
    var selectedOCRCandidates by remember {
        mutableStateOf<Map<Int, OCRCandidate>>(emptyMap())
    }

    var ocrQuantities by remember {
        mutableStateOf<Map<Int, String>>(emptyMap())
    }

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
            OutlinedButton(
                enabled = !isRecognizing && !isWorking,
                onClick = {
                    imagePicker.launch("image/*")
                }
            ) {
                Text("Добавить продукты по чеку")
            }

            if (isRecognizing) {
                CircularProgressIndicator()
            }

            receiptError?.let {
                Text(
                    text = it,
                    color = MaterialTheme.colorScheme.error
                )
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
            receiptResult?.let { result ->
                Text(
                    "Проверь распознанные товары",
                    style = MaterialTheme.typography.titleMedium
                )

                result.items.forEachIndexed { index, item ->
                    Card(
                        modifier = Modifier.fillMaxWidth()
                    ) {
                        Column(
                            modifier = Modifier.padding(12.dp),
                            verticalArrangement = Arrangement.spacedBy(8.dp)
                        ) {
                            Text(item.raw_name)

                            OutlinedTextField(
                                value = ocrQuantities[index]
                                    ?: (item.quantity ?: 1.0).toString(),
                                onValueChange = {
                                    ocrQuantities =
                                        ocrQuantities + (index to it)
                                },
                                label = { Text("Количество") },
                                keyboardOptions = KeyboardOptions(
                                    keyboardType = KeyboardType.Decimal
                                ),
                                singleLine = true
                            )

                            if (item.candidates.isEmpty()) {
                                Text(
                                    "Совпадений в каталоге не найдено.",
                                    color = MaterialTheme.colorScheme.error
                                )
                            } else {
                                item.candidates.forEach { candidate ->
                                    val selected =
                                        selectedOCRCandidates[index]?.product_id ==
                                                candidate.product_id

                                    OutlinedButton(
                                        onClick = {
                                            selectedOCRCandidates =
                                                selectedOCRCandidates +
                                                        (index to candidate)
                                        }
                                    ) {
                                        Text(
                                            (if (selected) "✓ " else "") +
                                                    candidate.name +
                                                    (candidate.brand?.let { " · $it" } ?: "") +
                                                    " · ${candidate.score.toInt()}%"
                                        )
                                    }
                                }
                            }
                        }
                    }
                }

                Button(
                    enabled = !isWorking &&
                            result.items.indices.any {
                                selectedOCRCandidates.containsKey(it)
                            },
                    onClick = {
                        val selectedItems = result.items.indices.mapNotNull { index ->
                            val candidate = selectedOCRCandidates[index]
                                ?: return@mapNotNull null

                            val quantity = (
                                    ocrQuantities[index]
                                        ?: (result.items[index].quantity ?: 1.0).toString()
                                    ).replace(',', '.').toDoubleOrNull()

                            if (quantity == null || quantity <= 0.0) {
                                null
                            } else {
                                candidate to quantity
                            }
                        }

                        if (selectedItems.isEmpty()) {
                            receiptError =
                                "Выбери продукты и укажи корректное количество."
                            return@Button
                        }

                        performInventoryAction { token ->
                            selectedItems.forEach { (candidate, quantity) ->
                                ApiClient.inventoryApi.addInventoryItem(
                                    "Bearer $token",
                                    household.id,
                                    InventoryItemCreateRequest(
                                        product_id = candidate.product_id,
                                        quantity = quantity
                                    )
                                )
                            }
                        }

                        receiptResult = null
                        selectedOCRCandidates = emptyMap()
                        ocrQuantities = emptyMap()
                    }
                ) {
                    Text("Добавить выбранные продукты")
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
                            val quantityText = editedQuantities[item.product_id]
                                ?: item.quantity.toString()

                            OutlinedTextField(
                                value = quantityText,
                                onValueChange = { value ->
                                    editedQuantities = editedQuantities +
                                            (item.product_id to value)
                                },
                                label = { Text("Количество (${product?.unit.orEmpty()})") },
                                keyboardOptions = KeyboardOptions(
                                    keyboardType = KeyboardType.Decimal
                                ),
                                singleLine = true,
                                modifier = Modifier.fillMaxWidth()
                            )

                            Row(
                                horizontalArrangement = Arrangement.spacedBy(8.dp),
                                verticalAlignment = Alignment.CenterVertically
                            ) {
                                Button(
                                    enabled = !isWorking &&
                                            quantityText.replace(',', '.')
                                                .toDoubleOrNull()?.let { it >= 0.0 } == true,
                                    onClick = {
                                        val newQuantity = quantityText
                                            .replace(',', '.')
                                            .toDoubleOrNull() ?: return@Button

                                        performInventoryAction { token ->
                                            if (newQuantity == 0.0) {
                                                val response =
                                                    ApiClient.inventoryApi.deleteInventoryItem(
                                                        "Bearer $token",
                                                        household.id,
                                                        item.product_id
                                                    )

                                                if (!response.isSuccessful) {
                                                    throw IllegalStateException(
                                                        "Не удалось удалить продукт"
                                                    )
                                                }
                                            } else {
                                                ApiClient.inventoryApi.updateInventoryItem(
                                                    "Bearer $token",
                                                    household.id,
                                                    item.product_id,
                                                    InventoryItemUpdateRequest(newQuantity)
                                                )
                                            }
                                        }

                                        editedQuantities =
                                            editedQuantities - item.product_id
                                    }
                                ) {
                                    Text("Сохранить")
                                }

                                TextButton(
                                    onClick = {
                                        editedQuantities =
                                            editedQuantities - item.product_id
                                    }
                                ) {
                                    Text("Отмена")
                                }
                            }
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
