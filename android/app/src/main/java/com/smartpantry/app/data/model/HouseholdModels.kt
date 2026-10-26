package com.smartpantry.app.data.model

import kotlinx.serialization.Serializable

@Serializable
data class HouseholdResponse(
    val id: Int,
    val name: String,
    val created_at: String,
    val updated_at: String
)

@Serializable
data class CreateHouseholdRequest(
    val name: String
)

@Serializable
data class HouseholdMemberResponse(
    val user_id: Int,
    val username: String,
    val email: String,
    val role: String,
    val joined_at: String
)

@Serializable
data class AddHouseholdMemberRequest(
    val user_id: Int
)

@Serializable
data class UpdateHouseholdMemberRoleRequest(
    val role: String
)