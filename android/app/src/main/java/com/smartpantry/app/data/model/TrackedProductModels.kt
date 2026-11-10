package com.smartpantry.app.data.model

import kotlinx.serialization.Serializable

@Serializable
data class TrackedProductResponse(
    val household_id: Int,
    val product_id: Int,
    @Serializable(with = DecimalQuantitySerializer::class)
    val minimum_quantity: Double,
    val created_at: String,
    val updated_at: String
)

@Serializable
data class TrackedProductCreateRequest(
    val product_id: Int,
    @Serializable(with = DecimalQuantitySerializer::class)
    val minimum_quantity: Double = 1.0
)

@Serializable
data class TrackedProductUpdateRequest(
    @Serializable(with = DecimalQuantitySerializer::class)
    val minimum_quantity: Double
)

@Serializable
data class LowStockItemResponse(
    val household_id: Int,
    val product_id: Int,
    @Serializable(with = DecimalQuantitySerializer::class)
    val minimum_quantity: Double,
    @Serializable(with = DecimalQuantitySerializer::class)
    val current_quantity: Double
)
