from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class TrackedProductCreate(BaseModel):
    product_id: int = Field(gt=0)
    minimum_quantity: Decimal = Field(default=Decimal("1"), gt=0, max_digits=10, decimal_places=3)


class TrackedProductUpdate(BaseModel):
    minimum_quantity: Decimal = Field(gt=0, max_digits=10, decimal_places=3)


class TrackedProductResponse(BaseModel):
    household_id: int
    product_id: int
    minimum_quantity: Decimal
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class LowStockItemResponse(BaseModel):
    household_id: int
    product_id: int
    minimum_quantity: Decimal
    current_quantity: Decimal