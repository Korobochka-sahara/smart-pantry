'''Форматы запросов и ответов OCR и сопоставления товаров.'''
from pydantic import BaseModel, Field

class ProductCandidate(BaseModel):
    """Товар из каталога, предложенный как возможное совпадение."""

    product_id: int
    name: str
    brand: str | None = None
    category: str
    unit: str
    package_quantity: float
    package_unit: str | None = None

    # Оценка похожести от 0 до 100, не вероятность совпадения.
    score: float

class OCRItem(BaseModel):
    """Товар, извлечённый Qwen из чека."""

    raw_name: str
    item_code: str | None = None
    name: str
    brand: str | None = None
    quantity: float | None = None
    unit: str | None = None
    package_quantity: float | None = None
    package_unit: str | None = None

    # Может быть пустым, если похожих продуктов в каталоге нет.
    candidates: list[ProductCandidate] = Field(default_factory=list)

class OCRResponse(BaseModel):
    status: str
    tier: str
    markdown: str

    # Заполним после реализации парсера.
    items: list[OCRItem] = Field(default_factory=list)