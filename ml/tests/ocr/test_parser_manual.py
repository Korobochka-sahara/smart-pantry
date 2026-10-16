import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[3]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from ml.ocr_service.receipt_parser import parse_receipt_response


def main() -> None:
    if len(sys.argv) < 2:
        print("Использование:")
        print('python ml/ocr_service/test_parser_manual.py "путь_к_json"')
        return

    file_path = Path(sys.argv[1])

    if not file_path.is_file():
        print(f"Файл не найден: {file_path}")
        return

    try:
        with file_path.open("r", encoding="utf-8") as file:
            response = json.load(file)

        items = parse_receipt_response(response)

        print(f"\nНайдено товаров: {len(items)}\n")

        for index, item in enumerate(items, start=1):
            print(f"Товар №{index}")
            print(f"  Название:       {item['name']}")
            print(f"  Бренд:          {item['brand']}")
            print(f"  Количество:     {item['quantity']}")
            print(
                f"  Фасовка:        "
                f"{item['package_quantity']} {item['package_unit']}"
            )
            print()

    except (json.JSONDecodeError, ValueError) as error:
        print(f"Ошибка обработки: {error}")


if __name__ == "__main__":
    main()