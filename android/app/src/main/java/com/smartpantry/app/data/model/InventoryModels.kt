package com.smartpantry.app.data.model

import kotlinx.serialization.Serializable

@Serializable
data class InventoryItemResponse(
    val household_id: Int,
    val product_id: Int,
    @Serializable(with = DecimalQuantitySerializer::class)
    val quantity: Double,
    val created_at: String,
    val updated_at: String
)

@Serializable
data class InventoryItemCreateRequest(
    val product_id: Int,
    @Serializable(with = DecimalQuantitySerializer::class)
    val quantity: Double
)

@Serializable
data class InventoryItemUpdateRequest(
    @Serializable(with = DecimalQuantitySerializer::class)
    val quantity: Double,
    @Serializable(with = DecimalQuantitySerializer::class)
    val expected_quantity: Double? = null
)

@Serializable
data class ProductResponse(
    val id: Int,
    val barcode: String? = null,
    val name: String,
    val brand: String? = null,
    val category: ProductCategory,
    val unit: ProductUnit,
    @Serializable(with = DecimalQuantitySerializer::class)
    val package_quantity: Double,
    val package_unit: ProductUnit? = null
)

@Serializable
data class InventoryQuantityChangeRequest(val delta: Double)
