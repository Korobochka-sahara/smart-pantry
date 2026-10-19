# Smart Pantry

Smart Pantry — клиент-серверный проект для учёта продуктов дома. Backend хранит каталог товаров и запасы домохозяйств, управляет пользователями и правами доступа. ML/OCR-сервис распознаёт фотографии чеков; после распознавания пользователь должен проверить позиции и подтвердить, какие товары добавлять в инвентарь.

> **Текущий статус:** backend и API управления данными реализованы; OCR-процесс интегрирован через отдельный HTTP-сервис MinerU и парсер Qwen/Ollama. Android-клиент находится в планах и в этом репозитории пока отсутствует. OCR не должен автоматически менять `InventoryItem`: добавление происходит отдельным подтверждённым запросом.

## Возможности

- Регистрация, вход, access/refresh JWT, ротация и отзыв refresh-токенов.
- Домохозяйства (`household`) и роли `OWNER`, `ADMIN`, `MEMBER`.
- Каталог продуктов (`Product`) и домашние запасы (`InventoryItem`).
- Отслеживание товаров и поиск позиций с низким остатком (`TrackedProduct`).
- OCR чеков: загрузка изображения → MinerU → парсер Qwen через Ollama → поиск кандидатов в каталоге.
- Миграции схемы БД через Alembic и API-тесты через pytest.
- Эксперименты сравнения MinerU, EasyOCR и PaddleOCR.

## Архитектура

```text
Клиент (пока Swagger / будущий Android)
                 |
                 v
       Backend — FastAPI :8000
       |       |        |
       |       |        +-- Ollama API / Qwen (отдельный процесс)
       |       +----------- PostgreSQL :5432
       +------------------- ML OCR service :8001
                                  |
                                  +-- MinerU
```

В Docker Compose поднимаются **три контейнера**: `backend`, `ml` и `postgres`. Два контейнера приложения — backend и ML; PostgreSQL — отдельная инфраструктурная БД. Ollama/Qwen — отдельный runtime: в текущей конфигурации он должен быть доступен backend по адресу `OLLAMA_HOST` (по умолчанию клиент Ollama использует `http://localhost:11434`). Если backend работает в Docker Desktop, укажи `OLLAMA_HOST=http://host.docker.internal:11434`, когда Ollama запущен на Windows-хосте. Модель должна быть скачана в Ollama, например `ollama pull qwen2.5:7b-instruct`.

### Поток OCR

1. Клиент отправляет изображение в `POST /ocr/receipts` backend API.
2. Backend отправляет файл в ML-сервис `POST /ocr`.
3. ML-сервис вызывает MinerU и возвращает Markdown.
4. Backend вызывает `parse_receipt()` (Qwen/Ollama), получает структурированные позиции.
5. Backend сопоставляет позиции с `Product` и возвращает кандидатов.
6. Клиент показывает результат пользователю. Только после подтверждения отдельный запрос добавляет выбранные `product_id` и количество через Inventory API.

## Структура репозитория

```text
smart-pantry/
├── README.md                     # Главная документация: архитектура, запуск, тесты, Docker
├── docker-compose.yaml            # PostgreSQL + backend + ML OCR service
├── .gitignore                     # Исключения Git
├── backend/
│   ├── Dockerfile                 # Образ FastAPI backend
│   ├── requirements.txt           # Зависимости backend и его тестов
│   ├── .env.example               # Шаблон настроек локального backend
│   ├── .env.test                  # Настройки тестовой БД (не хранить реальные секреты)
│   ├── alembic.ini                # Настройки миграций
│   ├── alembic/
│   │   ├── env.py                 # Подключение Alembic к SQLAlchemy metadata / DATABASE_URL
│   │   └── versions/              # История миграций схемы БД
│   ├── app/
│   │   ├── main.py                # Создание FastAPI, подключение роутеров и scheduler
│   │   ├── security.py            # JWT и проверка текущего пользователя
│   │   ├── api/                   # HTTP endpoints и преобразование ошибок в HTTP-коды
│   │   ├── db/                    # SQLAlchemy engine, SessionLocal, Base, get_db
│   │   ├── enums/                 # Перечисления ролей, категорий и единиц измерения
│   │   ├── models/                # ORM-модели таблиц
│   │   ├── schemas/               # Pydantic-схемы запросов и ответов
│   │   ├── services/              # Бизнес-логика, работа с данными, OCR orchestration
│   │   └── tasks/                 # Периодические фоновые задачи
│   └── tests/                     # API-тесты backend и fixtures
└── ml/
    ├── Dockerfile                 # Образ OCR-сервиса
    ├── requirements.txt           # Зависимости MinerU и OCR-экспериментов
    ├── __init__.py                # Python-пакет ml (нужен для импорта парсера backend)
    ├── ocr_service/               # HTTP-сервис распознавания
    │   ├── main.py                # FastAPI endpoint /ocr и /health
    │   ├── mineru_service.py      # Обёртка MinerU, синхронная обработка в отдельном потоке
    │   └── receipt_parser.py      # Парсер Markdown чека через Qwen/Ollama
    ├── ocr/                       # Экспериментальные скрипты EasyOCR и PaddleOCR
    ├── test_images/                # Изображения чеков для ручных экспериментов
    ├── results/                    # Сохранённые результаты OCR в JSON, по движкам
    └── tests/
        ├── fixtures/               # JSON-фикстуры с результатами OCR
        ├── test_clean_mineru.py    # Проверка очистки результата MinerU
        └── test_receipt_parser_llm.py # Проверка структурирования через Qwen
```

README в соответствующих каталогах дополняют это дерево и описывают конкретные файлы.

## Требования

- Python 3.11 рекомендуется для локальной разработки.
- Docker Desktop + Docker Compose v2 — для контейнерного запуска.
- Ollama с моделью `qwen2.5:7b-instruct` — для LLM-парсинга чеков.
- MinerU может скачать модели при первом запуске; подготовь свободное место на диске и дождись загрузки.
- Для ручных экспериментов EasyOCR/PaddleOCR нужны дополнительные модели и ресурсы. GPU не обязателен для CPU-режима, но распознавание будет медленнее.

В проекте оставлены **ровно два канонических файла зависимостей**: `backend/requirements.txt` и `ml/requirements.txt`. Старый корневой `requirements.txt`, который смешивал зависимости обеих сред и был сохранён в UTF-16, удалён.

## Быстрый запуск через Docker

Из корня репозитория:

```powershell
# 1. (Рекомендуется) создавать корневой .env для Compose-переменных,
#    например SECRET_KEY и OLLAMA_HOST. Не коммитеть этот файл.
# 2. Запустить сборку и три сервиса
docker compose up --build
```

После старта:

- Backend Swagger: http://localhost:8000/docs
- Backend root: http://localhost:8000/
- ML health: http://localhost:8001/health
- PostgreSQL на хосте: `localhost:5433`, внутри Compose-сети: `postgres:5432`.

Compose выполняет `alembic upgrade head` перед запуском backend. Первый build ML-образа и первая загрузка моделей могут занимать много времени. Для просмотра логов:

```powershell
docker compose logs -f backend
docker compose logs -f ml
docker compose logs -f postgres
```

Остановить контейнеры, сохранив данные БД:

```powershell
docker compose down
```

Удалить также данные БД и кеши моделей (необратимо):

```powershell
docker compose down -v
```

### Ollama / Qwen

Compose не запускает Ollama отдельным контейнером. Установить/запустить Ollama на хосте, скачать модель и передать адрес backend-контейнеру:

```powershell
ollama pull qwen2.5:7b-instruct
```

В `docker-compose.yaml` для backend по умолчанию используется `OLLAMA_HOST=http://host.docker.internal:11434`. Убедитесь, что Ollama принимает запросы от Docker Desktop. Если Ollama ещё не настроен, API-эндпоинты без OCR продолжат работать, но запросы OCR не завершат этап парсинга.

## Локальный запуск без Docker для Python-сервисов

### 1. PostgreSQL

Можно использовать Compose только для базы:

```powershell
docker compose up -d postgres
```

### 2. Backend

```powershell
cd backend
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
Copy-Item .env.example .env
```

Проверьте `backend/.env`: `DATABASE_URL` должен указывать на PostgreSQL хоста, например `postgresql://smart_pantry:smart_pantry_password@localhost:5433/smart_pantry`, а `SECRET_KEY` нужно заменить на случайную строку не короче 32 байт.

Запуск миграций и сервера:

```powershell
alembic upgrade head
python -m uvicorn app.main:app --reload
```

### 3. ML OCR-сервис

В отдельном PowerShell-окне из корня репозитория:

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

Локальный backend по умолчанию обращается к `http://127.0.0.1:8001`. Если меняете адрес ML-сервиса, установиье `MINERU_BASE_URL` в окружении backend.

### 4. Проверка OCR

Откройте http://localhost:8000/docs и вызовите `POST /ocr/receipts`, передав JPG/PNG/WebP не более 10 MiB. Для прямой проверки ML-сервиса:

```powershell
curl.exe http://127.0.0.1:8001/health
curl.exe -X POST "http://127.0.0.1:8001/ocr" -F "file=@ml/test_images/receipt_01.jpg;type=image/jpeg"
```

Ожидайте длительную обработку: MinerU может обрабатывать даже одностраничный чек несколько минут. В backend настроен отдельный таймаут чтения до 600 секунд.

## Тесты

### Backend API-тесты

Тесты используют отдельную БД, указанную в `backend/.env.test`. Перед первым запуском создайте БД `smart_pantry_test`:

```powershell
docker exec -it smart-pantry-postgres psql -U smart_pantry -d smart_pantry -c "CREATE DATABASE smart_pantry_test;"
```

Если база уже существует, команду повторять не нужно. Затем:

```powershell
cd backend
.\.venv\Scripts\Activate.ps1
python -m pytest tests -v
```

Тесты удаляют и создают таблицы в тестовой БД. **Не указывайте в `.env.test` URL рабочей БД.**

### ML / парсер

Из корня репозитория в ML-окружении:

```powershell
python -m pytest ml/tests -v
```

Эти тесты используют сохранённые JSON-фикстуры и вызывают парсер Qwen, поэтому для LLM-теста Ollama должна работать и иметь модель `qwen2.5:7b-instruct`. Для запуска отдельных сценариев:

```powershell
python -m ml.tests.test_clean_mineru
python -m ml.tests.test_receipt_parser_llm
```

Подробности — в `backend/tests/README.md` и `ml/tests/README.md`.

## Эксперименты OCR

Запускать из корня репозитория в активном ML-окружении:

```powershell
python ml/ocr/easyocr_test.py
python ml/ocr/paddleocr_test.py
```

Скрипты читают `ml/test_images/receipt_01.jpg` и записывают JSON в `ml/results/easyocr/` или `ml/results/paddleocr/`. Для MinerU CLI и сравнения `standard`, `basic`, `flash` см. `ml/ocr/README.md`. Результаты не следует считать автоматическим benchmark: для сравнения фиксируйте одинаковые входные изображения, режимы, время и критерии качества.

## Миграции базы данных

Из каталога `backend/`:

```powershell
alembic current
alembic history
alembic upgrade head
```

Создание миграции после изменения ORM-моделей:

```powershell
alembic revision --autogenerate -m "describe schema change"
```

Всегда проверяйте сгенерированную миграцию перед применением. Не редактируйте старые миграции, уже применённые в других окружениях; добавляйте новую.

## Конфигурация и безопасность

- Не коммитеть реальные `.env`, ключи, токены, дампы БД или приватные чеки.
- `backend/.env.example` — шаблон, а `backend/.env.test` предназначен только для локальных тестов.
- Пароль PostgreSQL в Compose по умолчанию учебный. Для постоянного окружения передавайте свои переменные и не публикуйте порт БД наружу без необходимости.
- Не выводите полный Markdown чеков и содержимое пользовательских изображений в production-логи: там могут быть личные данные.
- OCR не является безошибочным. Пользователь должен подтвердить распознанные позиции перед записью в `InventoryItem`.

## Текущие ограничения / известные нюансы

- В репозитории нет Android-клиента; Swagger используется для проверки API.
- Ollama — отдельный процесс и не входит в Compose как контейнер.
- MinerU, EasyOCR и PaddleOCR могут требовать значительных ресурсов и загружать модели при первом запуске.
- Ветка OCR возвращает распознанные позиции и кандидатов, но не должна автоматически сохранять их в инвентарь.
- Набор результатов в `ml/results/` — сохранённые артефакты экспериментов, а не гарантированный эталон качества.
