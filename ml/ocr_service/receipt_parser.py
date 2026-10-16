import re
from html.parser import HTMLParser
from typing import Any


class ReceiptTableParser(HTMLParser):
    """Извлекает строки и ячейки из HTML-таблиц MinerU."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.rows: list[list[str]] = []
        self.current_row: list[str] | None = None
        self.current_cell: list[str] | None = None

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        tag = tag.lower()

        if tag == "tr":
            self.current_row = []
        elif tag in ("td", "th") and self.current_row is not None:
            self.current_cell = []

    def handle_data(self, data: str) -> None:
        if self.current_cell is not None:
            self.current_cell.append(data)

    def handle_endtag(self, tag: str) -> None:
        tag = tag.lower()

        if tag in ("td", "th") and self.current_cell is not None:
            cell_text = normalize_text("".join(self.current_cell))

            if self.current_row is not None:
                self.current_row.append(cell_text)

            self.current_cell = None

        elif tag == "tr" and self.current_row is not None:
            if self.current_cell is not None:
                cell_text = normalize_text("".join(self.current_cell))
                self.current_row.append(cell_text)
                self.current_cell = None

            if self.current_row:
                self.rows.append(self.current_row)

            self.current_row = None


# Поддерживаемые обозначения фасовки.
PACKAGE_PATTERN = re.compile(
    r"(?i)(\d+(?:[.,]\d+)?)\s*"
    r"(килограмм(?:а|ов)?|кг|грамм(?:а|ов)?|гр|г|мл|"
    r"литр(?:а|ов)?|л|шт\.?)"
    r"(?=$|[\s.,;)\]])"
)

# Слова, по которым можно отличить итоговые строки чека от товаров.
EXCLUDED_MARKERS = (
    "ндс",
    "итог",
    "подытог",
    "скидка",
    "округление",
    "наличными",
    "безналичными",
    "сдача",
    "сумма ндс",
    "инн:",
    "касса:",
    "автомат:",
    "фп:",
    "фн:",
    "зн ккт:",
    "фд:",
    "поступ",
)


def normalize_text(text: str) -> str:
    """Убирает лишние пробелы и переносы строк."""
    return " ".join(text.split()).strip()


def normalize_package_unit(unit: str) -> str:
    """Приводит единицы фасовки к единому внутреннему формату."""
    unit = unit.lower().strip().rstrip(".")

    if unit in {"г", "гр", "грамм", "грамма", "граммов"}:
        return "g"

    if unit in {"кг", "килограмм", "килограмма", "килограммов"}:
        return "kg"

    if unit == "мл":
        return "ml"

    if unit in {"л", "литр", "литра", "литров"}:
        return "l"

    if unit == "шт":
        return "pcs"

    return unit


def extract_package(name: str) -> tuple[float | None, str | None]:
    """Извлекает размер упаковки из названия товара."""
    match = PACKAGE_PATTERN.search(name)

    if not match:
        return None, None

    amount = float(match.group(1).replace(",", "."))
    unit = normalize_package_unit(match.group(2))

    return amount, unit


def is_product_row(row: list[str]) -> bool:
    """Проверяет, похожа ли строка на строку с названием товара."""
    text = normalize_text(" ".join(row))

    if not text:
        return False

    lowered = text.lower()

    if any(marker in lowered for marker in EXCLUDED_MARKERS):
        return False

    # В текущей версии ищем фасовку, явно указанную в строке.
    return PACKAGE_PATTERN.search(text) is not None


def extract_product_name(row: list[str]) -> str:
    """Находит название с фасовкой и удаляет код товара в начале."""
    candidates = [
        cell
        for cell in row
        if cell and PACKAGE_PATTERN.search(cell)
    ]

    if not candidates:
        return ""

    # В Standard название обычно находится в отдельной ячейке.
    name = max(candidates, key=len)
    name = normalize_text(name)

    # Например: "8047BRUTO Чипсы ...120Г" -> "Чипсы ...120Г".
    name = re.sub(
        r"^\s*\d{4,}[A-ZА-ЯЁ0-9-]*\s+",
        "",
        name,
    )

    return normalize_text(name)


def extract_quantity(rows: list[list[str]]) -> float | None:
    """
    Извлекает количество только из явной записи вида '149.99*1'.

    Если количество не указано явно, не пытаемся угадать его
    по словам 'ШТ' или по расположению цены.
    """
    text = " ".join(
        cell
        for row in rows
        for cell in row
    )

    match = re.search(
        r"\*\s*(\d+(?:[.,]\d+)?)",
        text,
    )

    if not match:
        return None

    return float(match.group(1).replace(",", "."))


def parse_receipt(markdown: str) -> list[dict[str, Any]]:
    """
    Разбирает HTML-таблицы из поля markdown ответа MinerU Standard.

    Возвращает список товарных позиций. Markdown-таблицы Basic
    пока намеренно не поддерживаются.
    """
    if not isinstance(markdown, str) or not markdown.strip():
        raise ValueError("В ответе OCR отсутствует непустой markdown")

    table_parser = ReceiptTableParser()
    table_parser.feed(markdown)
    table_parser.close()

    rows = table_parser.rows
    items: list[dict[str, Any]] = []

    for index, row in enumerate(rows):
        if not is_product_row(row):
            continue

        name = extract_product_name(row)

        if not name:
            continue

        # Собираем следующие строки, пока не встретится следующий товар.
        detail_rows: list[list[str]] = []

        for next_row in rows[index + 1:]:
            if is_product_row(next_row):
                break

            detail_rows.append(next_row)

        package_quantity, package_unit = extract_package(name)
        quantity = extract_quantity(detail_rows)

        items.append({
            "name": name,
            "brand": None,
            "quantity": quantity,
            "package_quantity": package_quantity,
            "package_unit": package_unit,
        })

    return items


def parse_receipt_response(response: dict[str, Any]) -> list[dict[str, Any]]:
    """
    Принимает полный JSON-ответ MinerU, извлекает markdown
    и передаёт его парсеру.

    Поддерживается только tier='standard'.
    """
    if not isinstance(response, dict):
        raise ValueError("Ответ MinerU должен быть JSON-объектом")

    tier = response.get("tier")

    if tier != "standard":
        raise ValueError(
            f"Поддерживается только MinerU Standard; получен tier={tier!r}"
        )

    markdown = response.get("markdown")

    if not isinstance(markdown, str) or not markdown.strip():
        raise ValueError("В ответе MinerU отсутствует непустое поле 'markdown'")

    return parse_receipt(markdown)