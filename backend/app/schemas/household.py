from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, EmailStr, AliasPath

from app.enums.household import HouseholdRole

class HouseholdCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)

class HouseholdResponse(BaseModel):
    id: int
    name: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class HouseholdMemberResponse(BaseModel):
    user_id: int
    username: str = Field(validation_alias=AliasPath("user", "username"))
    email: EmailStr = Field(validation_alias=AliasPath("user", "email"))
    role: HouseholdRole
    joined_at: datetime

    model_config = ConfigDict(from_attributes=True)

class HouseholdMemberAdd(BaseModel):
    user_id: int

class HouseholdRoleUpdate(BaseModel):
    role: HouseholdRole