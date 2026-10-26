package com.smartpantry.app.data.model

import kotlinx.serialization.Serializable

@Serializable
data class OCRCandidate(
    val product_id: Int,
    val name: String,
    val brand: String? = null,
    val category: String,
    val unit: String,
    val package_quantity: Double,
    val package_unit: String? = null,
    val score: Double
)

@Serializable
data class OCRItem(
    val raw_name: String,
    val item_code: String? = null,
    val name: String,
    val brand: String? = null,
    val quantity: Double? = null,
    val unit: String? = null,
    val package_quantity: Double? = null,
    val package_unit: String? = null,
    val candidates: List<OCRCandidate> = emptyList()
)

@Serializable
data class OCRResponse(
    val status: String,
    val tier: String,
    val markdown: String,
    val items: List<OCRItem> = emptyList()
)