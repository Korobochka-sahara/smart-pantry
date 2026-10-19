# OCR HTTP service

Отдельный FastAPI-сервис для распознавания изображений чеков. `main.py` предоставляет `GET /health` и `POST /ocr`, валидирует MIME type и лимит 10 MiB, сохраняет изображение во временный файл, вызывает `MinerUService` и удаляет временный файл. `mineru_service.py` вызывает MinerU SDK и выполняет синхронную обработку через `asyncio.to_thread`, чтобы не блокировать event loop. `receipt_parser.py` содержит Qwen-парсер структурированных товарных позиций, который использует backend orchestration.

Запуск из `ml/ocr_service/` с активным ML venv:

```powershell
python -m uvicorn main:app --host 127.0.0.1 --port 8001 --reload
```

Проверка:

```powershell
curl.exe http://127.0.0.1:8001/health
curl.exe -X POST "http://127.0.0.1:8001/ocr" -F "file=@../test_images/receipt_01.jpg;type=image/jpeg"
```

В контейнере сервис должен слушать `0.0.0.0:8001`. Настройки: `MINERU_TIER` (`standard` по умолчанию). Не выводи содержимое чеков целиком в обычные production-логи.
