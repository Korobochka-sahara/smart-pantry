package com.smartpantry.app.data.model

import kotlinx.serialization.Serializable

@Serializable
data class TrackedProductResponse(
    val household_id: Int,
    val product_id: Int,
    val minimum_quantity: Int,
    val created_at: String,
    val updated_at: String
)

@Serializable
data class TrackedProductCreateRequest(
    val product_id: Int,
    val minimum_quantity: Int = 1
)

@Serializable
data class TrackedProductUpdateRequest(
    val minimum_quantity: Int
)

@Serializable
data class LowStockItemResponse(
    val household_id: Int,
    val product_id: Int,
    val minimum_quantity: Int,
    val current_quantity: Double
)
