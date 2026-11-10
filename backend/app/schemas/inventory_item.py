from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, field_validator


class InventoryItemCreate(BaseModel):
    product_id: int = Field(gt=0)
    quantity: Decimal = Field(
        gt=0,
        max_digits=10,
        decimal_places=3,
    )


class InventoryItemUpdate(BaseModel):
    # Optional for compatibility; Android always supplies its displayed snapshot.
    expected_quantity: Decimal | None = Field(default=None, ge=0, max_digits=10, decimal_places=3)

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

class InventoryQuantityChange(BaseModel):
    delta: Decimal = Field(max_digits=10, decimal_places=3)

    @field_validator("delta")
    @classmethod
    def nonzero_delta(cls, value):
        if value == 0:
            raise ValueError("delta must not be zero")
        return value
