import os
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]

sys.path.insert(0, str(BASE_DIR.parent))

if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

import pytest
from uuid import uuid4
from dotenv import dotenv_values
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from alembic import command
from alembic.config import Config
from app.db.test_safety import validate_test_database_url

# Read without overwriting an explicitly supplied test URL (e.g. CI).
settings = dotenv_values(BASE_DIR / ".env.test")
application_url = os.getenv("DATABASE_URL") or dotenv_values(BASE_DIR / ".env").get("DATABASE_URL")
TEST_DATABASE_URL = validate_test_database_url(
    os.getenv("TEST_DATABASE_URL") or settings.get("TEST_DATABASE_URL"), application_url
)
# Only this pytest process points application imports at the TEST database.
os.environ["DATABASE_URL"] = TEST_DATABASE_URL.render_as_string(hide_password=False)
os.environ["SECRET_KEY"] = settings["SECRET_KEY"]

# Each run owns a freshly generated schema. No pre-existing schema is cleared.
TEST_SCHEMA = "pantry_test_" + uuid4().hex
test_engine = create_engine(TEST_DATABASE_URL, connect_args={
    "options": f"-csearch_path={TEST_SCHEMA},public"
})
TestingSessionLocal = sessionmaker(bind=test_engine, autoflush=False, autocommit=False)


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
    with test_engine.begin() as connection:
        connection.execute(text(f'CREATE SCHEMA "{TEST_SCHEMA}"'))
    try:
        # Exercise every migration from base to head, rather than create_all().
        config = Config(str(BASE_DIR / "alembic.ini"))
        with test_engine.begin() as connection:
            config.attributes["connection"] = connection
            command.upgrade(config, "head")
        yield
    finally:
        with test_engine.begin() as connection:
            connection.execute(text(f'DROP SCHEMA "{TEST_SCHEMA}" CASCADE'))
        test_engine.dispose()


# ---------------------------------------------------------
# 6. Очищаем БД перед каждым тестом
# ---------------------------------------------------------

@pytest.fixture(autouse=True)
def clean_database(setup_database):
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
def create_product(client, catalog_headers):
    def _create_product(
        barcode="4601234567890",
        name="Milk",
        brand="Prostokvashino",
        category="dairy",
        unit="l",
        package_quantity=1,
        package_unit="l",
    ):
        response = client.post(
            "/products",
            headers=catalog_headers,
            json={
                "barcode": barcode, "name": name, "brand": brand,
                "category": category, "unit": unit,
                "package_quantity": package_quantity, "package_unit": package_unit,
            },
        )
        assert response.status_code == 201
        return response.json()
    return _create_product

@pytest.fixture
def catalog_headers(db):
    from app.models.user import User
    from app.security import create_access_token
    # Catalog fixtures do not change client.headers or another user's session.
    user = User(email="catalog-fixture@example.com", username="catalog-fixture", password_hash="unused")
    db.add(user)
    db.commit()
    return {"Authorization": "Bearer " + create_access_token(user.id)}


@pytest.fixture
def catalog_auth(client, catalog_headers):
    client.headers.update(catalog_headers)
    yield
    client.headers.pop("Authorization", None)
