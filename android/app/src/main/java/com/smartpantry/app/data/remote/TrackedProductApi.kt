package com.smartpantry.app.data.remote

import com.smartpantry.app.data.model.LowStockItemResponse
import com.smartpantry.app.data.model.TrackedProductCreateRequest
import com.smartpantry.app.data.model.TrackedProductResponse
import com.smartpantry.app.data.model.TrackedProductUpdateRequest
import retrofit2.Response
import retrofit2.http.Body
import retrofit2.http.DELETE
import retrofit2.http.GET
import retrofit2.http.Header
import retrofit2.http.PATCH
import retrofit2.http.POST
import retrofit2.http.Path

interface TrackedProductApi {
    @GET("households/{household_id}/tracked-products")
    suspend fun getTrackedProducts(
        @Header("Authorization") authorization: String,
        @Path("household_id") householdId: Int
    ): List<TrackedProductResponse>

    @POST("households/{household_id}/tracked-products")
    suspend fun addTrackedProduct(
        @Header("Authorization") authorization: String,
        @Path("household_id") householdId: Int,
        @Body request: TrackedProductCreateRequest
    ): TrackedProductResponse

    @PATCH("households/{household_id}/tracked-products/{product_id}")
    suspend fun updateTrackedProduct(
        @Header("Authorization") authorization: String,
        @Path("household_id") householdId: Int,
        @Path("product_id") productId: Int,
        @Body request: TrackedProductUpdateRequest
    ): TrackedProductResponse

    @DELETE("households/{household_id}/tracked-products/{product_id}")
    suspend fun deleteTrackedProduct(
        @Header("Authorization") authorization: String,
        @Path("household_id") householdId: Int,
        @Path("product_id") productId: Int
    ): Response<Unit>

    @GET("households/{household_id}/tracked-products/low-stock")
    suspend fun getLowStock(
        @Header("Authorization") authorization: String,
        @Path("household_id") householdId: Int
    ): List<LowStockItemResponse>
}
