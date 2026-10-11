from pathlib import Path
import json
import time

import easyocr


# Пути
BASE_DIR = Path(__file__).resolve().parent.parent
IMAGE_PATH = BASE_DIR / "test_images" / "receipt_01.jpg"
RESULT_PATH = BASE_DIR / "results" / "easyocr" / "easyocr_receipt_01.json"


def main():
    if not IMAGE_PATH.exists():
        raise FileNotFoundError(
            f"Файл чека не найден: {IMAGE_PATH}"
        )

    print("Загрузка EasyOCR...")

    reader = easyocr.Reader(
        ["ru", "en"],
        gpu=False,
    )

    print(f"Обрабатываем: {IMAGE_PATH}")
    start_time = time.perf_counter()

    results = reader.readtext(
        str(IMAGE_PATH),
        detail=1,
    )

    elapsed = time.perf_counter() - start_time

    output = []

    for bbox, text, confidence in results:
        output.append(
            {
                "text": text,
                "confidence": float(confidence),
                "bbox": [
                    [int(point[0]), int(point[1])]
                    for point in bbox
                ],
            }
        )

    RESULT_PATH.parent.mkdir(parents=True, exist_ok=True)

    with RESULT_PATH.open("w", encoding="utf-8") as f:
        json.dump(
            {
                "engine": "easyocr",
                "image": IMAGE_PATH.name,
                "processing_time_seconds": round(elapsed, 3),
                "results": output,
            },
            f,
            ensure_ascii=False,
            indent=2,
        )

    print()
    print("=" * 60)
    print("РЕЗУЛЬТАТ OCR")
    print("=" * 60)

    for item in output:
        print(
            f"[{item['confidence']:.3f}] "
            f"{item['text']}"
        )

    print("=" * 60)
    print(f"Время обработки: {elapsed:.3f} сек.")
    print(f"Найдено фрагментов: {len(output)}")
    print(f"Результат сохранён: {RESULT_PATH}")


if __name__ == "__main__":
    main()