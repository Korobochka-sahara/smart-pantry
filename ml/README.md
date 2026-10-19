# ML / OCR

`ml/` содержит OCR-сервис и исследовательские скрипты распознавания чеков. Основной контейнерный сервис использует MinerU. Экспериментальные скрипты позволяют отдельно оценивать EasyOCR и PaddleOCR на тех же изображениях.

## Каталоги

- `ocr_service/` — FastAPI OCR-сервис и адаптер MinerU.
- `ocr/` — скрипты экспериментов EasyOCR/PaddleOCR.
- `test_images/` — входные изображения чеков.
- `results/` — сохранённые JSON-результаты по OCR-движкам.
- `tests/` — тесты очистки MinerU и LLM-парсера.
- `requirements.txt` — единственный список зависимостей ML и OCR-экспериментов.
- `Dockerfile` — образ HTTP OCR-сервиса.

## Установка и запуск локально

```powershell
cd ml
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
$env:MINERU_TIER = "standard"
cd ocr_service
python -m uvicorn main:app --host 127.0.0.1 --port 8001 --reload
```

Проверка: `http://127.0.0.1:8001/health`. Endpoint `POST /ocr` принимает multipart-поле `file` (JPEG/PNG/WebP, до 10 MiB) и возвращает `status`, `tier`, `markdown`.

## MinerU

Сервис вызывает Python API MinerU через `mineru.parser.parse` и исполняет синхронную обработку в отдельном потоке. Первый запуск может скачивать модели и занимать несколько минут. Уровень задаётся переменной `MINERU_TIER` (по умолчанию `standard`). Ручные эксперименты с CLI описаны в `ocr/README.md`.

## Qwen / Ollama

`receipt_parser.py` вызывает Qwen через клиент Ollama. Ollama — отдельный процесс; установи/запусти его и загрузи модель `qwen2.5:7b-instruct`:

```powershell
ollama pull qwen2.5:7b-instruct
```

Тест парсера зависит от работающего Ollama и загруженной модели. MinerU endpoint возвращает Markdown, а LLM-парсер запускается orchestration-слоем backend.

## Тесты и эксперименты

Из корня репозитория:

```powershell
python -m pytest ml/tests -v
python ml/ocr/easyocr_test.py
python ml/ocr/paddleocr_test.py
```

Для CLI MinerU и трактовки результатов см. `ocr/README.md`. JSON-результаты — исследовательские артефакты, не гарантия точности для любого чека.
