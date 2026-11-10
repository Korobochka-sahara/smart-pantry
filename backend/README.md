# Backend

FastAPI-приложение Smart Pantry: HTTP API, аутентификация, права доступа к домохозяйствам, каталог товаров, запасы, отслеживание остатков, OCR orchestration и периодическая очистка refresh-токенов.

## Состав

- `app/main.py` — создание приложения, подключение роутеров, настройка логирования и scheduler.
- `app/api/` — HTTP-слой.
- `app/services/` — бизнес-логика.
- `app/models/` — ORM-модели SQLAlchemy.
- `app/schemas/` — Pydantic-контракты API.
- `app/db/` — подключение к БД и сессии.
- `app/security.py` — JWT и текущий пользователь.
- `app/tasks/` — фоновые задачи.
- `alembic/` — миграции схемы.
- `tests/` — тесты API.
- `requirements.txt` — единственный список зависимостей backend.
- `Dockerfile` — контейнерный образ backend.
- `run_local.ps1` — файл для запуска backend.

## Локальный запуск (PowerShell)

Из корня репозитория запустите PostgreSQL командой docker compose up -d --wait postgres. Затем настройте Python:

```powershell
cd backend
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.example .env
# Отредактируй .env: DATABASE_URL и SECRET_KEY
python -m alembic upgrade head
.\run_local.ps1
```

Swagger: http://127.0.0.1:8000/docs. PostgreSQL должен быть запущен. По умолчанию локальная конфигурация ожидает `127.0.0.1:5433`.

## Переменные окружения

- `DATABASE_URL` — строка подключения к PostgreSQL.
- `SECRET_KEY` — секрет JWT; используй уникальное значение длиной не менее 32 байт.
- `MINERU_BASE_URL` — адрес ML-сервиса, по умолчанию `http://127.0.0.1:8001`.
- `OLLAMA_HOST` — адрес Ollama, если он задан клиентом Ollama в окружении.

## Тесты

Запустите `docker compose --profile test up -d --wait postgres-test` из корня проекта. Затем выполните `python -m pytest tests -q` из каталога backend с активным окружением. Тесты используют `TEST_DATABASE_URL` из `.env.test` и применяют миграции к отдельной схеме. [Подробнее](tests/README.md).

## Поведение API

- Access-токен используется для защищённых запросов. Refresh-токен обновляет сессию. Для `POST /products` и `POST /ocr/receipts` нужен access-токен.
- Пополнение прибавляет количество в PostgreSQL одной операцией. Маршрут `POST /households/{household_id}/inventory/{product_id}/adjust` принимает `delta`. При списании остаток ограничивается нулём.
- При ручной установке остатка Android отправляет `expected_quantity`. Если остаток уже изменился, API возвращает 409.
- Остатки, пороги и количество в упаковке поддерживают три знака после запятой. Единицы измерения проверяются по перечислению, названия очищаются от лишних пробелов. Одинаковые имена пользователей разрешены, email уникален.
- Поиск по названию и бренду отбирает кандидатов в PostgreSQL, затем ранжирует их в Python. Сопоставление позиций чека использует текстовое описание товара.
