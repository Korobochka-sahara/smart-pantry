from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field
from app.enums.category import ProductCategory


class ProductCreate(BaseModel):
    barcode: str | None = Field(
        default=None,
        max_length=50,
    )

    name: str = Field(
        min_length=1,
        max_length=255,
    )

    brand: str | None = Field(
        default=None,
        max_length=100,
    )

    category: ProductCategory

    unit: str = Field(
        min_length=1,
        max_length=50,
    )

    package_quantity: Decimal = Field(
        default=Decimal("1"),
        gt=0,
    )

    package_unit: str | None = Field(
        default=None,
        max_length=50,
    )


class ProductUpdate(BaseModel):
    barcode: str | None = Field(
        default=None,
        max_length=50,
    )

    name: str | None = Field(
        default=None,
        min_length=1,
        max_length=255,
    )

    brand: str | None = Field(
        default=None,
        max_length=100,
    )

    category: ProductCategory | None = None

    unit: str | None = Field(
        default=None,
        min_length=1,
        max_length=50,
    )

    package_quantity: Decimal | None = Field(
        default=None,
        gt=0,
    )

    package_unit: str | None = Field(
        default=None,
        max_length=50,
    )


class ProductResponse(BaseModel):
    id: int
    barcode: str | None
    name: str
    brand: str | None
    category: ProductCategory
    unit: str
    package_quantity: Decimal
    package_unit: str | None

    model_config = ConfigDict(from_attributes=True)