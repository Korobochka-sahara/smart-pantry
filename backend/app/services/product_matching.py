'''Поиск и ранжирование похожих товаров в каталоге Product.'''

import re
from decimal import Decimal

from rapidfuzz import fuzz
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.product import Product


def normalize_name(value: str | None) -> str:
    """Приводит название к форме, удобной для сравнения."""

    if not value:
        return ""

    value = value.lower().replace("ё", "е")
    value = re.sub(r"[^a-zа-я0-9]+", " ", value)
    return " ".join(value.split())


def enum_value(value) -> str | None:
    """Возвращает значение Enum, не меняя типы в модели."""

    if value is None:
        return None

    return str(getattr(value, "value", value))


def normalized_brand(value: str | None) -> str:
    return normalize_name(value)


def to_base_quantity(
    quantity: Decimal | float | int | None,
    unit: str | None,
) -> tuple[float, str] | None:
    """Переводит массу в граммы, объём в миллилитры."""

    if quantity is None or unit is None:
        return None

    unit = unit.lower()

    factors = {
        "g": ("mass", 1.0),
        "kg": ("mass", 1000.0),
        "ml": ("volume", 1.0),
        "l": ("volume", 1000.0),
    }

    if unit not in factors:
        return None

    dimension, factor = factors[unit]
    return float(quantity) * factor, dimension


def package_score(receipt_item: dict, product: Product) -> float | None:
    """Оценивает совпадение размера упаковки от 0 до 100."""

    receipt = to_base_quantity(
        receipt_item.get("package_quantity"),
        receipt_item.get("package_unit"),
    )
    product_size = to_base_quantity(
        product.package_quantity,
        enum_value(product.package_unit),
    )

    # Если размер упаковки неизвестен хотя бы с одной стороны,
    # не используем его для оценки.
    if receipt is None or product_size is None:
        return None

    receipt_quantity, receipt_dimension = receipt
    product_quantity, product_dimension = product_size

    # Массу нельзя сопоставлять с объёмом.
    if receipt_dimension != product_dimension:
        return 0.0

    if receipt_quantity == product_quantity:
        return 100.0

    difference = abs(receipt_quantity - product_quantity)
    relative_difference = difference / max(
        receipt_quantity,
        product_quantity,
    )

    return max(0.0, 100.0 * (1.0 - relative_difference))


def score_product(receipt_item: dict, product: Product) -> float:
    """Рассчитывает итоговый рейтинг кандидата."""

    receipt_name = normalize_name(receipt_item.get("name"))
    product_name = normalize_name(product.name)

    if not receipt_name or not product_name:
        return 0.0

    # WRatio устойчивее к небольшим различиям в строках.
    name_score = float(fuzz.WRatio(receipt_name, product_name))

    receipt_brand = normalized_brand(receipt_item.get("brand"))
    product_brand = normalized_brand(product.brand)

    # Учитываем бренд только тогда, когда он есть с обеих сторон.
    if receipt_brand and product_brand:
        brand_score = float(fuzz.WRatio(receipt_brand, product_brand))
        name_score = 0.85 * name_score + 0.15 * brand_score

    size_score = package_score(receipt_item, product)

    if size_score is not None:
        name_score = 0.8 * name_score + 0.2 * size_score

    # Не даём совпадению названия скрыть несовместимость единиц.
    receipt_unit = enum_value(receipt_item.get("unit"))
    product_unit = enum_value(product.unit)

    if receipt_unit and product_unit:
        if receipt_unit.lower() != product_unit.lower():
            name_score *= 0.5

    return round(name_score, 2)


def find_product_candidates(
    db: Session,
    receipt_item: dict,
    limit: int = 3,
    min_score: float = 45.0,
) -> list[dict]:
    """Возвращает лучшие совпадения из каталога Product."""

    products = db.scalars(select(Product)).all()
    ranked = []

    for product in products:
        score = score_product(receipt_item, product)

        if score < min_score:
            continue

        ranked.append((score, product))

    ranked.sort(key=lambda item: item[0], reverse=True)

    candidates = []

    for score, product in ranked[:limit]:
        candidates.append({
            "product_id": product.id,
            "name": product.name,
            "brand": product.brand,
            "category": enum_value(product.category) or "",
            "unit": enum_value(product.unit) or "",
            "package_quantity": float(product.package_quantity),
            "package_unit": enum_value(product.package_unit),
            "score": score,
        })

    return candidates

def search_catalog_products(
    db: Session,
    query: str,
    limit: int = 20,
    offset: int = 0,
) -> list[Product]:
    """Ищет товары по названию, бренду или штрихкоду."""

    normalized_query = normalize_name(query)

    if not normalized_query:
        return []

    products = db.scalars(select(Product)).all()
    ranked = []

    for product in products:
        name = normalize_name(product.name)
        brand = normalized_brand(product.brand)
        barcode = (product.barcode or "").strip().lower()

        # Точное совпадение штрихкода — самый надёжный вариант.
        if barcode and barcode == query.strip().lower():
            score = 100.0
        else:
            # Сравниваем запрос с названием и брендом.
            name_score = fuzz.WRatio(normalized_query, name)
            brand_score = (
                fuzz.WRatio(normalized_query, brand)
                if brand
                else 0.0
            )

            score = max(name_score, brand_score)

            # Бонус за вхождение запроса в название или бренд.
            if normalized_query in name or normalized_query in brand:
                score = min(100.0, score + 5.0)

        # Для ручного поиска допускаем более свободное совпадение.
        if score >= 30.0:
            ranked.append((float(score), product))

    ranked.sort(key=lambda item: item[0], reverse=True)

    return [
        product
        for _, product in ranked[offset:offset + limit]
    ]