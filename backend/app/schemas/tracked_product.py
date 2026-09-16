from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class TrackedProductCreate(BaseModel):
    product_id: int = Field(gt=0)
    minimum_quantity: int = Field(default=1, gt=0)


class TrackedProductUpdate(BaseModel):
    minimum_quantity: int = Field(gt=0)


class TrackedProductResponse(BaseModel):
    household_id: int
    product_id: int
    minimum_quantity: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class LowStockItemResponse(BaseModel):
    household_id: int
    product_id: int
    minimum_quantity: int
    current_quantity: float