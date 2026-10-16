import json
import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[3]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from ml.ocr_service.receipt_parser import (
    extract_package,
    parse_receipt,
    parse_receipt_response,
)


FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures"


def load_response(filename: str) -> dict:
    """Загружает сохранённый JSON-ответ MinerU."""
    file_path = FIXTURES_DIR / filename

    assert file_path.is_file(), f"Не найден файл: {file_path}"

    with file_path.open("r", encoding="utf-8") as file:
        return json.load(file)


def test_standard_receipt_returns_products() -> None:
    """Проверяем разбор реального ответа MinerU Standard."""
    response = load_response("receipt_01_standard_response.json")

    items = parse_receipt_response(response)

    assert len(items) == 2

    assert items[0]["name"] == "Чипсы карт.с мор.сол.120Г"
    assert items[0]["package_quantity"] == 120.0
    assert items[0]["package_unit"] == "g"

    assert items[1]["name"] == "С.ЧИП.КАР.ВК.ЛИС.По-МИЛ.80Г"
    assert items[1]["package_quantity"] == 80.0
    assert items[1]["package_unit"] == "g"


def test_quantity_is_extracted_only_when_explicit() -> None:
    """Не угадываем количество по обозначению ШТ."""
    response = load_response("receipt_01_standard_response.json")

    items = parse_receipt_response(response)

    # В первой позиции нет явной записи вида цена*количество.
    assert items[0]["quantity"] is None

    # Во второй позиции есть запись 149.99*1.
    assert items[1]["quantity"] == 1.0


def test_basic_response_is_rejected() -> None:
    """Проверяем, что Basic не обрабатывается как Standard."""
    response = load_response("receipt_01_basic_response.json")

    with pytest.raises(ValueError, match="только MinerU Standard"):
        parse_receipt_response(response)


@pytest.mark.parametrize(
    ("text", "expected_quantity", "expected_unit"),
    [
        ("Чипсы 120Г", 120.0, "g"),
        ("Молоко 1,5л", 1.5, "l"),
        ("Вода 500мл", 500.0, "ml"),
        ("Мука 2 кг", 2.0, "kg"),
        ("Яйца 10шт", 10.0, "pcs"),
        ("Товар без фасовки", None, None),
    ],
)
def test_extract_package(
    text: str,
    expected_quantity: float | None,
    expected_unit: str | None,
) -> None:
    assert extract_package(text) == (expected_quantity, expected_unit)


def test_parser_normalizes_spaces_and_removes_product_code() -> None:
    """Проверяем простую очистку названия товара."""
    markdown = """
    <table>
      <tr>
        <td>Код</td>
        <td>Название</td>
      </tr>
      <tr>
        <td>8047BRUTO</td>
        <td>  Чипсы   карт.с мор.сол.120Г  </td>
      </tr>
      <tr>
        <td>НДС 22%</td>
        <td>149.99*1</td>
      </tr>
    </table>
    """

    items = parse_receipt(markdown)

    assert len(items) == 1
    assert items[0]["name"] == "Чипсы карт.с мор.сол.120Г"
    assert items[0]["quantity"] == 1.0
    assert items[0]["package_quantity"] == 120.0
    assert items[0]["package_unit"] == "g"


def test_empty_markdown_is_rejected() -> None:
    with pytest.raises(ValueError, match="markdown"):
        parse_receipt_response({
            "tier": "standard",
            "markdown": "",
        })


def test_missing_markdown_is_rejected() -> None:
    with pytest.raises(ValueError, match="markdown"):
        parse_receipt_response({
            "tier": "standard",
        })