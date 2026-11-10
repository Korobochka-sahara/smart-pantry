'''Форматы запросов и ответов OCR и сопоставления товаров.'''
from pydantic import BaseModel, Field, field_validator
from app.enums.unit import Unit
from app.enums.category import ProductCategory

class ProductCandidate(BaseModel):
    """Товар из каталога, предложенный как возможное совпадение."""

    product_id: int
    name: str
    brand: str | None = None
    category: ProductCategory
    unit: Unit
    package_quantity: float
    package_unit: Unit | None = None

    # Оценка похожести от 0 до 100, не вероятность совпадения.
    score: float

class OCRItem(BaseModel):
    """Товар, извлечённый Qwen из чека."""

    raw_name: str
    item_code: str | None = None
    name: str
    brand: str | None = None
    quantity: float | None = None
    unit: Unit | None = None
    package_quantity: float | None = None
    package_unit: Unit | None = None

    # Может быть пустым, если похожих продуктов в каталоге нет.
    candidates: list[ProductCandidate] = Field(default_factory=list)

    @field_validator("unit", "package_unit", mode="before")
    @classmethod
    def known_unit_or_none(cls, value):
        # OCR is untrusted recognition output, not a user product-creation request.
        if isinstance(value, str):
            value = value.lower().strip()
        return value if value in Unit._value2member_map_ else None

class OCRResponse(BaseModel):
    status: str
    tier: str
    markdown: str

    # Заполним после реализации парсера.
    items: list[OCRItem] = Field(default_factory=list)