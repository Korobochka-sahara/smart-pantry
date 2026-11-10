from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, field_validator
from app.enums.category import ProductCategory
from app.enums.unit import Unit


class ProductFields(BaseModel):
    @field_validator("name", mode="before", check_fields=False)
    @classmethod
    def normalize_name(cls, value):
        if isinstance(value, str):
            return " ".join(value.split())
        return value

    @field_validator("brand", "barcode", mode="before", check_fields=False)
    @classmethod
    def normalize_optional_text(cls, value):
        if isinstance(value, str):
            return " ".join(value.split()) or None
        return value


class ProductCreate(ProductFields):
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

    unit: Unit

    package_quantity: Decimal = Field(
        default=Decimal("1"),
        gt=0,
        max_digits=10,
        decimal_places=3,
    )

    package_unit: Unit | None = None


class ProductUpdate(ProductFields):
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

    unit: Unit | None = None

    package_quantity: Decimal | None = Field(
        default=None,
        gt=0,
        max_digits=10,
        decimal_places=3,
    )

    package_unit: Unit | None = None


class ProductResponse(BaseModel):
    id: int
    barcode: str | None
    name: str
    brand: str | None
    category: ProductCategory
    unit: Unit
    package_quantity: Decimal
    package_unit: Unit | None

    model_config = ConfigDict(from_attributes=True)