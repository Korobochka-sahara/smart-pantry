from concurrent.futures import ThreadPoolExecutor
from decimal import Decimal
from threading import Barrier

import jwt
import pytest
from alembic import command
from alembic.config import Config
from pathlib import Path
from sqlalchemy import event, text
from sqlalchemy.orm import Session

from app.db.test_safety import validate_test_database_url
from app.schemas.inventory_item import InventoryItemCreate
from app.schemas.product import ProductCreate
from app.security import SECRET_KEY, ALGORITHM
from app.services.inventory_service import create_inventory_item, change_inventory_quantity
from app.services.product_matching import catalog_candidates, find_product_candidates
from app.services.product_service import create_product as create_product_service
from app.services.auth_service import register_user
from app.schemas.auth import RegisterRequest
from app.services.auxiliary_functions import ProductConflictError


@pytest.fixture
def pantry(client, create_user, login_user, create_household, create_product):
    create_user()
    token = login_user()
    household = create_household(token)
    product = create_product(name="Молоко Простоквашино", unit="l")
    return household["id"], product["id"], {"Authorization": f"Bearer {token}"}


def test_refresh_cannot_access_api_even_after_logout(client, create_user):
    create_user()
    tokens = client.post("/auth/login", json={
        "email": "user@example.com", "password": "StrongPassword123!",
    }).json()
    headers = {"Authorization": "Bearer " + tokens["refresh_token"]}
    assert client.get("/auth/me", headers=headers).status_code == 401
    client.post("/auth/logout", json={"refresh_token": tokens["refresh_token"]})
    assert client.get("/auth/me", headers=headers).status_code == 401
    assert client.post("/auth/refresh", json={"refresh_token": tokens["access_token"]}).status_code == 401


@pytest.mark.parametrize("payload", [
    {"sub": "1", "type": "access"},
    {"sub": "invalid", "type": "access", "exp": 4000000000},
    {"sub": "1", "exp": 4000000000},
])
def test_invalid_access_claims_return_401(client, payload):
    token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
    assert client.get("/auth/me", headers={"Authorization": "Bearer " + token}).status_code == 401


def test_protected_catalog_and_ocr_reject_anonymous_requests(client):
    assert client.post("/products", json={}).status_code == 401
    assert client.post("/ocr/receipts", files={"file": ("r.jpg", b"image", "image/jpeg")}).status_code == 401


def test_missing_household_members_return_controlled_errors(client, pantry, create_user, login_user):
    household_id, _, headers = pantry
    other = create_user(email="other@example.com", username="user")
    outsider_headers = {"Authorization": "Bearer " + login_user(email=other["email"])}
    path = f"/households/{household_id}"
    assert client.post(path + "/leave", headers=outsider_headers).status_code == 404
    assert client.patch(path + f"/members/{other['id']}/role", headers=outsider_headers,
                        json={"role": "ADMIN"}).status_code == 403
    assert client.patch(path + "/members/999999/role", headers=headers,
                        json={"role": "ADMIN"}).status_code == 404
    assert client.delete(path + "/members/999999", headers=headers).status_code == 404


@pytest.mark.parametrize("existing", [False, True])
def test_parallel_topups_keep_every_increment(db, pantry, existing):
    household_id, product_id, _ = pantry
    # User is the household owner, not the fixture's catalog user.
    user_id = db.scalar(text("SELECT user_id FROM household_member WHERE household_id=:h"), {"h": household_id})
    engine = db.get_bind()
    if existing:
        create_inventory_item(db, household_id, user_id, InventoryItemCreate(product_id=product_id, quantity="1"))
    barrier = Barrier(8)
    def increment(_):
        with Session(engine) as session:
            barrier.wait(timeout=15)
            for _ in range(5):
                create_inventory_item(session, household_id, user_id,
                                      InventoryItemCreate(product_id=product_id, quantity="0.125"))
    with ThreadPoolExecutor(max_workers=8) as pool:
        list(pool.map(increment, range(8)))
    quantity = db.scalar(text("SELECT quantity FROM inventory_item WHERE household_id=:h AND product_id=:p"),
                         {"h": household_id, "p": product_id})
    assert quantity == Decimal("5") + int(existing)


def test_atomic_decrement_and_stale_manual_edit(client, pantry):
    household_id, product_id, headers = pantry
    path = f"/households/{household_id}/inventory"
    client.post(path, headers=headers, json={"product_id": product_id, "quantity": "2"})
    client.post(path, headers=headers, json={"product_id": product_id, "quantity": "1"})
    response = client.patch(path + f"/{product_id}", headers=headers,
                            json={"quantity": "7", "expected_quantity": "2"})
    assert response.status_code == 409
    response = client.post(path + f"/{product_id}/adjust", headers=headers, json={"delta": "-1"})
    assert response.json()["quantity"] == "2.000"
    response = client.post(path + f"/{product_id}/adjust", headers=headers, json={"delta": "-10"})
    assert response.json()["quantity"] == "0.000"
    assert client.post(path + f"/{product_id}/adjust", headers=headers, json={"delta": "0"}).status_code == 422


def test_topup_overflow_is_a_conflict_without_changing_stock(client, pantry):
    household_id, product_id, headers = pantry
    path = f"/households/{household_id}/inventory"
    assert client.post(path, headers=headers, json={"product_id": product_id, "quantity": "9999999.999"}).status_code == 201
    assert client.post(path, headers=headers, json={"product_id": product_id, "quantity": "0.001"}).status_code == 409
    assert client.get(path + f"/{product_id}", headers=headers).json()["quantity"] == "9999999.999"


def test_email_conflict_after_precheck_rolls_back(db, create_user, monkeypatch):
    create_user()
    monkeypatch.setattr(db, "scalar", lambda *args, **kwargs: None)
    with pytest.raises(ValueError, match="Email already registered"):
        register_user(db, RegisterRequest(email="user@example.com", username="user", password="StrongPassword123!"))
    assert db.is_active


def test_same_refresh_token_cannot_be_rotated_twice_in_parallel(client, create_user):
    create_user()
    tokens = client.post("/auth/login", json={"email": "user@example.com", "password": "StrongPassword123!"}).json()
    barrier = Barrier(2)
    def refresh(_):
        barrier.wait(timeout=15)
        return client.post("/auth/refresh", json={"refresh_token": tokens["refresh_token"]}).status_code
    with ThreadPoolExecutor(max_workers=2) as pool:
        assert sorted(pool.map(refresh, range(2))) == [200, 401]


@pytest.mark.parametrize("changes", [
    {"unit": "bottle"}, {"package_unit": "bottle"}, {"category": "unknown"},
    {"name": " \t\n "}, {"package_quantity": "1.0001"}, {"package_quantity": "10000000"},
])
def test_product_validation_matches_storage(client, catalog_headers, changes):
    payload = {"name": "Milk", "category": "dairy", "unit": "l", **changes}
    assert client.post("/products", headers=catalog_headers, json=payload).status_code == 422


def test_product_name_is_normalized(client, catalog_headers):
    response = client.post("/products", headers=catalog_headers,
                           json={"name": "  Молоко   свежее  ", "category": "dairy", "unit": "l"})
    assert response.status_code == 201
    assert response.json()["name"] == "Молоко свежее"


def test_fractional_threshold_including_low_stock(client, pantry):
    household_id, product_id, headers = pantry
    path = f"/households/{household_id}/tracked-products"
    response = client.post(path, headers=headers, json={"product_id": product_id, "minimum_quantity": "0.500"})
    assert response.status_code == 201
    assert Decimal(response.json()["minimum_quantity"]) == Decimal("0.5")
    client.post(f"/households/{household_id}/inventory", headers=headers,
                json={"product_id": product_id, "quantity": "0.125"})
    item = client.get(path + "/low-stock", headers=headers).json()[0]
    assert Decimal(item["current_quantity"]) == Decimal("0.125")
    assert Decimal(item["minimum_quantity"]) == Decimal("0.500")


def test_duplicate_barcode_after_racing_precheck_is_409(db, create_product, monkeypatch):
    create_product(barcode="duplicate")
    # Simulate a competing insert committing after our pre-check saw no row.
    monkeypatch.setattr(db, "scalar", lambda *args, **kwargs: None)
    with pytest.raises(ProductConflictError):
        create_product_data = ProductCreate(name="Milk", barcode="duplicate", category="dairy", unit="l")
        create_product_service(db, create_product_data)
    assert db.is_active


def test_receipt_matching_uses_bounded_sql_pool(db, create_product):
    from app.models.product import Product
    from app.enums.category import ProductCategory
    from app.enums.unit import Unit
    db.add_all([Product(name=f"Печенье {i}", category=ProductCategory.SWEETS,
                        unit=Unit.pcs, package_quantity=1) for i in range(230)])
    db.commit()
    product = create_product(name="Молоко Простоквашино", barcode=None)
    statements = []
    def record(connection, cursor, statement, parameters, context, executemany):
        if statement.lstrip().startswith("SELECT") and "product" in statement:
            statements.append(statement)
    event.listen(db.get_bind(), "before_cursor_execute", record)
    try:
        pool = catalog_candidates(db, "Молоко Простоквашино")
        result = find_product_candidates(db, {"name": "Молко Простоквашино", "unit": "l"})
    finally:
        event.remove(db.get_bind(), "before_cursor_execute", record)
    assert len(pool) == 200
    assert result[0]["product_id"] == product["id"]
    assert statements and all("LIMIT" in statement and "<->" in statement for statement in statements)


@pytest.mark.parametrize("test_url, app_url", [
    (None, None),
    ("postgresql://localhost/smart_pantry", None),
    ("sqlite:///pantry_test", None),
    ("postgresql://localhost/pantry_test", "postgresql://127.0.0.1/pantry_test"),
])
def test_unsafe_test_database_configuration_is_rejected(test_url, app_url):
    with pytest.raises(RuntimeError):
        validate_test_database_url(test_url, app_url)


def test_migrated_schema_matches_models(db):
    config = Config(str(Path(__file__).resolve().parents[1] / "alembic.ini"))
    config.attributes["connection"] = db.connection()
    command.check(config)
