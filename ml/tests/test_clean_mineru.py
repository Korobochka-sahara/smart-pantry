import json
from pathlib import Path

from ml.ocr_service.receipt_parser import (
    extract_markdown,
    clean_mineru_markdown,
)


FIXTURES_DIR = Path("ml/tests/fixtures")


def test_clean_fixture():
    files = list(FIXTURES_DIR.glob("*.json"))
    assert files, "JSON fixtures не найдены"

    source = json.loads(
        files[8].read_text(encoding="utf-8")
    )

    original = extract_markdown(source)
    cleaned = clean_mineru_markdown(original)

    print(f"before: {len(original):,} symbols")
    print(f"after: {len(cleaned):,} symbols")
    print("\nclean text:\n")
    print(cleaned[:5000])

    assert cleaned
    assert "base64," not in cleaned.lower()
    assert "<img" not in cleaned.lower()


if __name__ == "__main__":
    test_clean_fixture()