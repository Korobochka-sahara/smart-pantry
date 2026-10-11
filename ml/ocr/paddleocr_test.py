from pathlib import Path
import json
import time
import os

# Важно: задаём до импорта Paddle/PaddleOCR
os.environ["FLAGS_enable_pir_api"] = "0"

from paddleocr import PaddleOCR


BASE_DIR = Path(__file__).resolve().parent.parent

IMAGE_PATH = BASE_DIR / "test_images" / "receipt_01.jpg"
RESULT_PATH = (
    BASE_DIR
    / "results"
    / "paddleocr"
    / "paddleocr_receipt_01.json"
)


def main():
    print("=" * 60)
    print("PADDLEOCR TEST")
    print("=" * 60)

    print(f"Изображение: {IMAGE_PATH}")
    print(f"Результат:   {RESULT_PATH}")

    if not IMAGE_PATH.exists():
        raise FileNotFoundError(
            f"Файл чека не найден: {IMAGE_PATH}"
        )

    print()
    print("1. Создаём PaddleOCR...")

    ocr = PaddleOCR(
        lang="ru",
        device="cpu",
        enable_mkldnn=False,
        text_detection_model_name="PP-OCRv5_mobile_det",
        text_recognition_model_name="PP-OCRv5_mobile_rec",
    )

    print("2. PaddleOCR создан.")
    print("3. Начинаем распознавание...")

    start_time = time.perf_counter()

    result = ocr.predict(
        str(IMAGE_PATH)
    )

    print("4. ocr.predict() завершился.")

    elapsed = time.perf_counter() - start_time

    output = []

    print("5. Обрабатываем результаты...")

    for res in result:
        data = res.json

        if callable(data):
            data = data()

        if isinstance(data, str):
            data = json.loads(data)

        output.append(data)

    print(f"6. Получено результатов: {len(output)}")

    RESULT_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with RESULT_PATH.open(
        "w",
        encoding="utf-8",
    ) as f:
        json.dump(
            {
                "engine": "paddleocr",
                "image": IMAGE_PATH.name,
                "processing_time_seconds": round(
                    elapsed,
                    3,
                ),
                "results": output,
            },
            f,
            ensure_ascii=False,
            indent=2,
        )

    print()
    print("=" * 60)
    print("PADDLEOCR ЗАВЕРШЁН")
    print("=" * 60)
    print(f"Время обработки: {elapsed:.3f} сек.")
    print(f"Результат сохранён: {RESULT_PATH}")
    print("=" * 60)


if __name__ == "__main__":
    main()