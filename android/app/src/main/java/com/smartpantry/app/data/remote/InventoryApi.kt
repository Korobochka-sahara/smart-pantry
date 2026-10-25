package com.smartpantry.app.data.remote

import com.smartpantry.app.data.model.InventoryItemCreateRequest
import com.smartpantry.app.data.model.InventoryItemResponse
import com.smartpantry.app.data.model.InventoryItemUpdateRequest
import com.smartpantry.app.data.model.ProductResponse
import retrofit2.Response
import retrofit2.http.Body
import retrofit2.http.DELETE
import retrofit2.http.GET
import retrofit2.http.Header
import retrofit2.http.PATCH
import retrofit2.http.POST
import retrofit2.http.Path
import retrofit2.http.Query

interface InventoryApi {
    @GET("households/{household_id}/inventory")
    suspend fun getInventory(
        @Header("Authorization") authorization: String,
        @Path("household_id") householdId: Int
    ): List<InventoryItemResponse>

    @POST("households/{household_id}/inventory")
    suspend fun addInventoryItem(
        @Header("Authorization") authorization: String,
        @Path("household_id") householdId: Int,
        @Body request: InventoryItemCreateRequest
    ): InventoryItemResponse

    @PATCH("households/{household_id}/inventory/{product_id}")
    suspend fun updateInventoryItem(
        @Header("Authorization") authorization: String,
        @Path("household_id") householdId: Int,
        @Path("product_id") productId: Int,
        @Body request: InventoryItemUpdateRequest
    ): InventoryItemResponse

    @DELETE("households/{household_id}/inventory/{product_id}")
    suspend fun deleteInventoryItem(
        @Header("Authorization") authorization: String,
        @Path("household_id") householdId: Int,
        @Path("product_id") productId: Int
    ): Response<Unit>

    @GET("products/search")
    suspend fun searchProducts(
        @Query("q") query: String,
        @Query("limit") limit: Int = 20
    ): List<ProductResponse>

    @GET("products/{product_id}")
    suspend fun getProduct(
        @Path("product_id") productId: Int
    ): ProductResponse
}
