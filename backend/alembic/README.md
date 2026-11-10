# Alembic migrations

Каталог миграций схемы PostgreSQL. `env.py` связывает Alembic с `Base.metadata` и `DATABASE_URL`; `versions/` хранит последовательность изменений. `alembic.ini` расположен в `backend/`.

Команды из каталога `backend/`:

```powershell
alembic current
alembic history
alembic upgrade head
alembic revision --autogenerate -m "describe change"
```

Проверьте миграцию вручную перед применением: автогенерация не всегда корректно распознаёт переименование, изменения enum и перенос данных. Не меняйте уже опубликованные миграции без понимания последствий.

Если `upgrade head` завершается ошибкой `connection timeout` на `localhost:5433`, из корня проекта выполните:

```powershell
docker compose up -d --wait postgres
docker compose ps postgres
Test-NetConnection 127.0.0.1 -Port 5433
```

После `TcpTestSucceeded: True` повторите `python -m alembic upgrade head` из каталога backend. Для локального Python адрес берётся из `backend/.env` или из переменной окружения `DATABASE_URL`, если она задана. Проверьте порт, имя БД и пользователя. Для PostgreSQL, установленного отдельно, используйте порт его службы.

Миграция `b6c2d9e41001` добавляет дробные пороги и индекс поиска по названию и бренду. Для индекса требуется расширение `pg_trgm`. Если роль миграций не может установить расширение, его может заранее установить администратор БД.
Для Docker на Windows используйте 127.0.0.1 в DATABASE_URL, чтобы подключаться напрямую к опубликованному IPv4-порту.
