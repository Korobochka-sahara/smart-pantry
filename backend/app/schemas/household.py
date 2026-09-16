from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.enums.household import HouseholdRole

class HouseholdCreate(BaseModel):
    name: str

class HouseholdResponse(BaseModel):
    id: int
    name: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class HouseholdMemberResponse(BaseModel):
    user_id: int
    role: HouseholdRole
    joined_at: datetime

    model_config = ConfigDict(from_attributes=True)

class HouseholdMemberAdd(BaseModel):
    user_id: int

class HouseholdRoleUpdate(BaseModel):
    role: HouseholdRole