package com.smartpantry.app.data.model

import kotlinx.serialization.SerialName
import kotlinx.serialization.Serializable

@Serializable
enum class ProductUnit(val value: String) {
    @SerialName("pcs") PCS("pcs"),
    @SerialName("g") G("g"),
    @SerialName("kg") KG("kg"),
    @SerialName("ml") ML("ml"),
    @SerialName("l") L("l");
    override fun toString() = value
}

@Serializable
enum class ProductCategory(val value: String) {
    @SerialName("dairy") DAIRY("dairy"),
    @SerialName("meat") MEAT("meat"),
    @SerialName("fish") FISH("fish"),
    @SerialName("vegetables") VEGETABLES("vegetables"),
    @SerialName("fruits") FRUITS("fruits"),
    @SerialName("groceries") GROCERIES("groceries"),
    @SerialName("drinks") DRINKS("drinks"),
    @SerialName("frozen") FROZEN("frozen"),
    @SerialName("sweets") SWEETS("sweets"),
    @SerialName("other") OTHER("other");
    override fun toString() = value
}
