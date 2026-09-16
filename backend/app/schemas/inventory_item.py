from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class InventoryItemCreate(BaseModel):
    product_id: int = Field(gt=0)
    quantity: Decimal = Field(
        gt=0,
        max_digits=10,
        decimal_places=3,
    )


class InventoryItemUpdate(BaseModel):
    quantity: Decimal | None = Field(
        default=None,
        ge=0,
        max_digits=10,
        decimal_places=3,
    )


class InventoryItemResponse(BaseModel):
    household_id: int
    product_id: int
    quantity: Decimal
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)