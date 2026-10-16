import json
from pathlib import Path

from ml.ocr_service.receipt_parser import parse_receipt


FIXTURES_DIR = Path("ml/tests/fixtures")


def test_parse_one_fixture():
    fixture_files = list(FIXTURES_DIR.glob("*.json"))
    assert fixture_files, "В fixtures нет JSON-файлов"

    path = fixture_files[0]
    source = json.loads(path.read_text(encoding="utf-8"))

    items = parse_receipt(source)

    print(f"\nFixture: {path.name}")
    print(json.dumps(items, ensure_ascii=False, indent=2))

    assert isinstance(items, list)

    for item in items:
        assert item["raw_name"]
        assert item["name"]
        assert item["quantity"] > 0


if __name__ == "__main__":
    test_parse_one_fixture()