'''Формат запросов и ответов'''
from pydantic import BaseModel, Field

class OCRItem (BaseModel):
    name: str
    brand: str | None = None

    # Количество купленных упаковок/единиц.
    quantity: float | None = None
    
    # Масса или объём одной упаковки, если удалось распознать.
    package_quantity: float | None = None
    package_unit: str | None = None

class OCRResponse(BaseModel):
    status: str
    tier: str
    markdown: str

    # Заполним после реализации парсера.
    items: list[OCRItem] = Field(default_factory=list)