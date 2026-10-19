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
