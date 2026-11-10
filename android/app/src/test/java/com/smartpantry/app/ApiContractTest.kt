package com.smartpantry.app

import com.smartpantry.app.data.model.*
import kotlinx.serialization.SerializationException
import kotlinx.serialization.decodeFromString
import kotlinx.serialization.encodeToString
import kotlinx.serialization.json.Json
import org.junit.Assert.assertEquals
import org.junit.Assert.assertTrue
import org.junit.Test

class ApiContractTest {
    private val json = Json { ignoreUnknownKeys = true }

    @Test
    fun productEnumsAndDecimalStringsMatchBackendResponse() {
        val product = json.decodeFromString<ProductResponse>("""
            {"id":1,"name":"Milk","category":"dairy","unit":"pcs",
             "package_quantity":"0.500","package_unit":"l"}
        """.trimIndent())
        assertEquals(ProductUnit.PCS, product.unit)
        assertEquals(ProductUnit.L, product.package_unit)
        assertEquals(ProductCategory.DAIRY, product.category)
        assertEquals(0.5, product.package_quantity, 0.0)
        assertTrue(json.encodeToString(product).contains("\"unit\":\"pcs\""))
    }

    @Test
    fun fractionalThresholdReadsDecimalStrings() {
        val item = json.decodeFromString<LowStockItemResponse>("""
            {"household_id":1,"product_id":2,"minimum_quantity":"0.500","current_quantity":"0.125"}
        """.trimIndent())
        assertEquals(0.5, item.minimum_quantity, 0.0)
        assertEquals(0.125, item.current_quantity, 0.0)
    }

    @Test
    fun inventoryReadsBothDecimalStringsAndNumbers() {
        for (quantity in listOf("\"0.125\"", "0.125")) {
            val item = json.decodeFromString<InventoryItemResponse>("""
                {"household_id":1,"product_id":2,"quantity":$quantity,
                 "created_at":"2026-11-11","updated_at":"2026-11-11"}
            """.trimIndent())
            assertEquals(0.125, item.quantity, 0.0)
        }
    }

    @Test(expected = SerializationException::class)
    fun unsupportedProductUnitIsRejected() {
        json.decodeFromString<ProductResponse>("""
            {"id":1,"name":"Milk","category":"dairy","unit":"bucket","package_quantity":"1.000"}
        """.trimIndent())
    }

    @Test
    fun manualEditIncludesExpectedQuantity() {
        val body = json.encodeToString(InventoryItemUpdateRequest(2.5, 1.25))
        assertTrue(body.contains("\"expected_quantity\":1.25"))
    }
}
