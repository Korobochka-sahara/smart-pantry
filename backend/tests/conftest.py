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

@pytest.fixture
def auth_headers():
    def _auth_headers(token: str) -> dict:
        return {"Authorization": f"Bearer {token}"}
    return _auth_headers

@pytest.fixture
def create_user(client):
    def _create_user(email="user@example.com", username="user", password="StrongPassword123!"):
        response = client.post(
            "/auth/register",
            json={"email": email, "username": username, "password": password},
        )
        assert response.status_code == 201
        return response.json()
    return _create_user

@pytest.fixture
def login_user(client):
    def _login(email="user@example.com", password="StrongPassword123!"):
        response = client.post(
            "/auth/login",
            json={"email": email, "password": password},
        )
        assert response.status_code == 200, f"Login failed: {response.json()}"
        return response.json()["access_token"]
    return _login

@pytest.fixture
def create_household(client, auth_headers):
    def _create_household(token, name="My Household"):
        response = client.post(
            "/households",
            headers=auth_headers(token),
            json={"name": name},
        )
        assert response.status_code == 201
        return response.json()
    return _create_household

@pytest.fixture
def create_product(client):
    def _create_product(
        barcode="4601234567890",
        name="Milk",
        brand="Prostokvashino",
        category="dairy",
        unit="L",
        package_quantity=1,
        package_unit="L",
    ):
        response = client.post(
            "/products",
            json={
                "barcode": barcode, "name": name, "brand": brand,
                "category": category, "unit": unit,
                "package_quantity": package_quantity, "package_unit": package_unit,
            },
        )
        assert response.status_code == 201
        return response.json()
    return _create_product