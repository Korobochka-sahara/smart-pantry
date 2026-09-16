import os
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]

if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

import pytest
from dotenv import load_dotenv
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# ---------------------------------------------------------
# 1. Загружаем настройки тестовой БД
# ---------------------------------------------------------

BASE_DIR = Path(__file__).resolve().parents[1]
ENV_TEST_FILE = BASE_DIR / ".env.test"

load_dotenv(ENV_TEST_FILE, override=True)

TEST_DATABASE_URL = os.getenv("DATABASE_URL")

if not TEST_DATABASE_URL:
    raise RuntimeError(
        f"DATABASE_URL is not set. Expected .env.test at: {ENV_TEST_FILE}"
    )

if TEST_DATABASE_URL.startswith("postgresql://"):
    TEST_DATABASE_URL = TEST_DATABASE_URL.replace(
        "postgresql://",
        "postgresql+psycopg://",
        1,
    )


# ---------------------------------------------------------
# 2. Тестовый engine и тестовые сессии
# ---------------------------------------------------------

test_engine = create_engine(TEST_DATABASE_URL)

TestingSessionLocal = sessionmaker(
    bind=test_engine,
    autoflush=False,
    autocommit=False,
)


# ---------------------------------------------------------
# 3. Импортируем модели
# ---------------------------------------------------------
# Важно: импорт моделей нужен для того, чтобы SQLAlchemy
# зарегистрировал их в Base.metadata.

from app.db.database import Base, get_db

from app.models.user import User
from app.models.household import Household
from app.models.household_member import HouseholdMember
from app.models.product import Product
from app.models.inventory_item import InventoryItem
from app.models.receipt import Receipt
from app.models.receipt_item import ReceiptItem
from app.models.refresh_token import RefreshToken
from app.models.tracked_product import TrackedProduct


# ---------------------------------------------------------
# 4. Импортируем FastAPI-приложение
# ---------------------------------------------------------

from app.main import app


# ---------------------------------------------------------
# 5. Создаём таблицы перед всеми тестами
# ---------------------------------------------------------

@pytest.fixture(scope="session", autouse=True)
def setup_database():
    Base.metadata.create_all(bind=test_engine)

    yield

    Base.metadata.drop_all(bind=test_engine)
    test_engine.dispose()


# ---------------------------------------------------------
# 6. Очищаем БД перед каждым тестом
# ---------------------------------------------------------

@pytest.fixture(autouse=True)
def clean_database():
    db = TestingSessionLocal()

    try:
        # Удаляем таблицы в обратном порядке зависимостей.
        for table in reversed(Base.metadata.sorted_tables):
            db.execute(table.delete())

        db.commit()

    finally:
        db.close()

    yield


# ---------------------------------------------------------
# 7. Тестовая SQLAlchemy-сессия
# ---------------------------------------------------------

@pytest.fixture
def db():
    session = TestingSessionLocal()

    try:
        yield session
    finally:
        session.close()


# ---------------------------------------------------------
# 8. Переопределяем FastAPI dependency get_db
# ---------------------------------------------------------

@pytest.fixture
def client():
    def override_get_db():
        db = TestingSessionLocal()

        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db

    client = TestClient(app)

    try:
        yield client
    finally:
        client.close()
        app.dependency_overrides.clear()