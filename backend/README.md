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

Из корня репозитория:

```powershell
cd backend
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.example .env
# Отредактируй .env: DATABASE_URL и SECRET_KEY
alembic upgrade head
.\run_local.ps1
```

Swagger: http://127.0.0.1:8000/docs. PostgreSQL должен быть запущен. По умолчанию локальная конфигурация ожидает `localhost:5433`.

## Переменные окружения

- `DATABASE_URL` — строка подключения к PostgreSQL.
- `SECRET_KEY` — секрет JWT; используй уникальное значение длиной не менее 32 байт.
- `MINERU_BASE_URL` — адрес ML-сервиса, по умолчанию `http://127.0.0.1:8001`.
- `OLLAMA_HOST` — адрес Ollama, если он задан клиентом Ollama в окружении.

## Тесты

Тесты используют `backend/.env.test`, а не `.env`. Инструкции — в `tests/README.md`. Не направляй тестовую конфигурацию на рабочую БД.
