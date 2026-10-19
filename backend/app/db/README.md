# Database connection

`database.py` загружает `backend/.env`, создаёт SQLAlchemy `engine`, `SessionLocal` и декларативный `Base`, а также предоставляет dependency `get_db()` для FastAPI.

Для PostgreSQL используется драйвер psycopg 3: `postgresql://...` преобразуется в `postgresql+psycopg://...`. Таблицы в обычном приложении создаются миграциями Alembic, а не ручным `Base.metadata.create_all()`.

Не помещайте пароли БД в исходный код. В Docker `DATABASE_URL` должен указывать на имя Compose-сервиса `postgres`, а не на `localhost`.
