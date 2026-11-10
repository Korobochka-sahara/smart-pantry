package com.smartpantry.app.data.model

import kotlinx.serialization.KSerializer
import kotlinx.serialization.SerializationException
import kotlinx.serialization.descriptors.PrimitiveKind
import kotlinx.serialization.descriptors.PrimitiveSerialDescriptor
import kotlinx.serialization.encoding.Decoder
import kotlinx.serialization.encoding.Encoder
import kotlinx.serialization.json.JsonDecoder
import kotlinx.serialization.json.double
import kotlinx.serialization.json.jsonPrimitive

/** Pydantic Decimal responses are JSON strings; OCR responses may be numbers. */
object DecimalQuantitySerializer : KSerializer<Double> {
    override val descriptor = PrimitiveSerialDescriptor("DecimalQuantity", PrimitiveKind.DOUBLE)
    override fun deserialize(decoder: Decoder): Double {
        val value = if (decoder is JsonDecoder) decoder.decodeJsonElement().jsonPrimitive.double
                    else decoder.decodeDouble()
        if (!value.isFinite()) throw SerializationException("Quantity must be finite")
        return value
    }
    override fun serialize(encoder: Encoder, value: Double) {
        if (!value.isFinite()) throw SerializationException("Quantity must be finite")
        encoder.encodeDouble(value)
    }
}
