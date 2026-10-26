package com.smartpantry.app.data.remote

import com.smartpantry.app.data.model.OCRResponse
import okhttp3.MultipartBody
import retrofit2.http.Multipart
import retrofit2.http.POST
import retrofit2.http.Part

interface OCRApi {

    @Multipart
    @POST("ocr/receipts")
    suspend fun recognizeReceipt(
        @Part file: MultipartBody.Part
    ): OCRResponse
}