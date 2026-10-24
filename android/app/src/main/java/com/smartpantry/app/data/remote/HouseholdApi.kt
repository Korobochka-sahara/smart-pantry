package com.smartpantry.app.data.remote

import com.smartpantry.app.data.model.AddHouseholdMemberRequest
import com.smartpantry.app.data.model.CreateHouseholdRequest
import com.smartpantry.app.data.model.HouseholdMemberResponse
import com.smartpantry.app.data.model.HouseholdResponse
import com.smartpantry.app.data.model.UpdateHouseholdMemberRoleRequest
import retrofit2.Response
import retrofit2.http.Body
import retrofit2.http.DELETE
import retrofit2.http.GET
import retrofit2.http.Header
import retrofit2.http.PATCH
import retrofit2.http.POST
import retrofit2.http.Path

interface HouseholdApi {

    @GET("households")
    suspend fun getMyHouseholds(
        @Header("Authorization") authorization: String
    ): List<HouseholdResponse>

    @POST("households")
    suspend fun createHousehold(
        @Header("Authorization") authorization: String,
        @Body request: CreateHouseholdRequest
    ): HouseholdResponse

    @GET("households/{household_id}")
    suspend fun getHousehold(
        @Header("Authorization") authorization: String,
        @Path("household_id") householdId: Int
    ): HouseholdResponse

    @GET("households/{household_id}/members")
    suspend fun getMembers(
        @Header("Authorization") authorization: String,
        @Path("household_id") householdId: Int
    ): List<HouseholdMemberResponse>

    @POST("households/{household_id}/members")
    suspend fun addMember(
        @Header("Authorization") authorization: String,
        @Path("household_id") householdId: Int,
        @Body request: AddHouseholdMemberRequest
    ): HouseholdMemberResponse

    @PATCH("households/{household_id}/members/{target_user_id}/role")
    suspend fun updateMemberRole(
        @Header("Authorization") authorization: String,
        @Path("household_id") householdId: Int,
        @Path("target_user_id") targetUserId: Int,
        @Body request: UpdateHouseholdMemberRoleRequest
    ): HouseholdMemberResponse

    @DELETE("households/{household_id}/members/{target_user_id}")
    suspend fun removeMember(
        @Header("Authorization") authorization: String,
        @Path("household_id") householdId: Int,
        @Path("target_user_id") targetUserId: Int
    ): Response<Unit>

    @POST("households/{household_id}/leave")
    suspend fun leaveHousehold(
        @Header("Authorization") authorization: String,
        @Path("household_id") householdId: Int
    ): Response<Unit>
}