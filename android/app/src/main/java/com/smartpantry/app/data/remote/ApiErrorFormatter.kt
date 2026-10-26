package com.smartpantry.app.data.remote

import kotlinx.serialization.json.Json
import kotlinx.serialization.json.jsonObject
import kotlinx.serialization.json.jsonPrimitive
import retrofit2.HttpException

object ApiErrorFormatter {
    fun detail(error: HttpException): String? {
        return try {
            val raw = error.response()?.errorBody()?.string() ?: return null
            val root = Json.parseToJsonElement(raw).jsonObject
            root["detail"]?.let { value ->
                if (value is kotlinx.serialization.json.JsonPrimitive) value.content
                else value.toString()
            }
        } catch (_: Exception) {
            null
        }
    }
}
