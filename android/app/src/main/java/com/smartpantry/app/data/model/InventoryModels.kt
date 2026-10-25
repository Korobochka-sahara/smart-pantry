package com.smartpantry.app.data.model

import kotlinx.serialization.Serializable

@Serializable
data class InventoryItemResponse(
    val household_id: Int,
    val product_id: Int,
    val quantity: Double,
    val created_at: String,
    val updated_at: String
)

@Serializable
data class InventoryItemCreateRequest(
    val product_id: Int,
    val quantity: Double
)

@Serializable
data class InventoryItemUpdateRequest(
    val quantity: Double
)

@Serializable
data class ProductResponse(
    val id: Int,
    val barcode: String? = null,
    val name: String,
    val brand: String? = null,
    val category: String,
    val unit: String,
    val package_quantity: Double,
    val package_unit: String? = null
)
