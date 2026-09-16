# =========================================================
# ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ (сохранена исходная структура)
# =========================================================

def create_user(client, username="testuser", email="test@example.com"):
    response = client.post(
        "/auth/register",
        json={
            "username": username,
            "email": email,
            "password": "Password123",
        },
    )
    assert response.status_code == 201
    return response.json()


def login_user(client, email="test@example.com"):
    response = client.post(
        "/auth/login",
        json={
            "email": email,
            "password": "Password123",
        },
    )
    assert response.status_code == 200
    # ВОЗВРАЩАЕМ ТОЛЬКО ТОКЕН, без мутации client.headers
    return response.json()["access_token"]


def create_household(client, token, name="My Household"):
    response = client.post(
        "/households",
        headers={"Authorization": f"Bearer {token}"},
        json={"name": name},
    )
    assert response.status_code == 201
    return response.json()


def create_product(
    client,
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
            "barcode": barcode,
            "name": name,
            "brand": brand,
            "category": category,
            "unit": unit,
            "package_quantity": package_quantity,
            "package_unit": package_unit,
        },
    )
    assert response.status_code == 201
    return response.json()


def setup_household_and_product(client):
    user = create_user(client)
    # Получаем токен для этого конкретного пользователя
    token = login_user(client, email=user["email"])
    household = create_household(client, token)
    product = create_product(client)
    # Возвращаем токен, чтобы тесты могли использовать его в заголовках
    return token, household, product


def create_tracked_product(client, token, household_id, product_id, minimum_quantity=1):
    response = client.post(
        f"/households/{household_id}/tracked-products",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "product_id": product_id,
            "minimum_quantity": minimum_quantity,
        },
    )
    assert response.status_code == 201
    return response.json()


# =========================================================
# CREATE
# =========================================================

def test_create_tracked_product(client):
    token, household, product = setup_household_and_product(client)

    response = client.post(
        f"/households/{household['id']}/tracked-products",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "product_id": product["id"],
            "minimum_quantity": 3,
        },
    )

    assert response.status_code == 201
    data = response.json()

    assert data["household_id"] == household["id"]
    assert data["product_id"] == product["id"]
    assert data["minimum_quantity"] == 3
    assert "created_at" in data
    assert "updated_at" in data


def test_create_tracked_product_with_default_minimum_quantity(client):
    token, household, product = setup_household_and_product(client)

    response = client.post(
        f"/households/{household['id']}/tracked-products",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "product_id": product["id"],
        },
    )

    assert response.status_code == 201
    data = response.json()
    assert data["minimum_quantity"] == 1


def test_create_tracked_product_with_nonexistent_product(client):
    token, household, product = setup_household_and_product(client)

    response = client.post(
        f"/households/{household['id']}/tracked-products",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "product_id": 999999,
            "minimum_quantity": 2,
        },
    )

    assert response.status_code == 404


def test_create_duplicate_tracked_product(client):
    token, household, product = setup_household_and_product(client)

    create_tracked_product(client, token, household["id"], product["id"], minimum_quantity=2)

    response = client.post(
        f"/households/{household['id']}/tracked-products",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "product_id": product["id"],
            "minimum_quantity": 5,
        },
    )

    assert response.status_code == 409


def test_create_tracked_product_with_zero_minimum_quantity(client):
    token, household, product = setup_household_and_product(client)

    response = client.post(
        f"/households/{household['id']}/tracked-products",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "product_id": product["id"],
            "minimum_quantity": 0,
        },
    )

    assert response.status_code == 422


def test_create_tracked_product_with_negative_minimum_quantity(client):
    token, household, product = setup_household_and_product(client)

    response = client.post(
        f"/households/{household['id']}/tracked-products",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "product_id": product["id"],
            "minimum_quantity": -1,
        },
    )

    assert response.status_code == 422


def test_create_tracked_product_with_invalid_product_id(client):
    token, household, product = setup_household_and_product(client)

    response = client.post(
        f"/households/{household['id']}/tracked-products",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "product_id": 0,
            "minimum_quantity": 1,
        },
    )

    assert response.status_code == 422


# =========================================================
# GET
# =========================================================

def test_get_tracked_product(client):
    token, household, product = setup_household_and_product(client)

    create_tracked_product(client, token, household["id"], product["id"], minimum_quantity=4)

    response = client.get(
        f"/households/{household['id']}/tracked-products",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    data = response.json()

    assert len(data) == 1
    assert data[0]["household_id"] == household["id"]
    assert data[0]["product_id"] == product["id"]
    assert data[0]["minimum_quantity"] == 4


def test_get_tracked_products_empty(client):
    token, household, product = setup_household_and_product(client)

    response = client.get(
        f"/households/{household['id']}/tracked-products",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    assert response.json() == []


def test_get_multiple_tracked_products(client):
    token, household, product1 = setup_household_and_product(client)

    product2 = create_product(
        client,
        barcode="4601234567891",
        name="Apple",
        brand="No Brand",
        category="fruits",
        unit="kg",
        package_quantity=1,
        package_unit="kg",
    )

    create_tracked_product(client, token, household["id"], product1["id"], minimum_quantity=2)
    create_tracked_product(client, token, household["id"], product2["id"], minimum_quantity=5)

    response = client.get(
        f"/households/{household['id']}/tracked-products",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    data = response.json()

    assert len(data) == 2
    assert data[0]["product_id"] == product1["id"]
    assert data[0]["minimum_quantity"] == 2
    assert data[1]["product_id"] == product2["id"]
    assert data[1]["minimum_quantity"] == 5


def test_get_tracked_product_from_list_by_product_id(client):
    token, household, product = setup_household_and_product(client)

    create_tracked_product(client, token, household["id"], product["id"], minimum_quantity=3)

    response = client.get(
        f"/households/{household['id']}/tracked-products",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    data = response.json()

    matching_items = [item for item in data if item["product_id"] == product["id"]]
    assert len(matching_items) == 1


# =========================================================
# UPDATE
# =========================================================

def test_update_tracked_product(client):
    token, household, product = setup_household_and_product(client)

    create_tracked_product(client, token, household["id"], product["id"], minimum_quantity=2)

    response = client.patch(
        f"/households/{household['id']}/tracked-products/{product['id']}",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "minimum_quantity": 10,
        },
    )

    assert response.status_code == 200
    data = response.json()

    assert data["product_id"] == product["id"]
    assert data["minimum_quantity"] == 10


def test_update_tracked_product_with_zero_minimum_quantity(client):
    token, household, product = setup_household_and_product(client)

    create_tracked_product(client, token, household["id"], product["id"], minimum_quantity=2)

    response = client.patch(
        f"/households/{household['id']}/tracked-products/{product['id']}",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "minimum_quantity": 0,
        },
    )

    assert response.status_code == 422


def test_update_tracked_product_with_negative_minimum_quantity(client):
    token, household, product = setup_household_and_product(client)

    create_tracked_product(client, token, household["id"], product["id"], minimum_quantity=2)

    response = client.patch(
        f"/households/{household['id']}/tracked-products/{product['id']}",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "minimum_quantity": -5,
        },
    )

    assert response.status_code == 422


def test_update_nonexistent_tracked_product(client):
    token, household, product = setup_household_and_product(client)

    response = client.patch(
        f"/households/{household['id']}/tracked-products/{product['id']}",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "minimum_quantity": 5,
        },
    )

    assert response.status_code == 404


# =========================================================
# DELETE
# =========================================================

def test_delete_tracked_product(client):
    token, household, product = setup_household_and_product(client)

    create_tracked_product(client, token, household["id"], product["id"])

    response = client.delete(
        f"/households/{household['id']}/tracked-products/{product['id']}",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 204

    response = client.get(
        f"/households/{household['id']}/tracked-products",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    assert response.json() == []


def test_delete_nonexistent_tracked_product(client):
    token, household, product = setup_household_and_product(client)

    response = client.delete(
        f"/households/{household['id']}/tracked-products/{product['id']}",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 404


# =========================================================
# PERMISSIONS
# =========================================================

def test_user_cannot_access_another_household_tracked_products(client):
    create_user(client, username="user1", email="user1@example.com")
    token1 = login_user(client, email="user1@example.com")

    household = create_household(client, token1)
    product = create_product(client)

    create_tracked_product(client, token1, household["id"], product["id"])

    create_user(client, username="user2", email="user2@example.com")
    token2 = login_user(client, email="user2@example.com")

    response = client.get(
        f"/households/{household['id']}/tracked-products",
        headers={"Authorization": f"Bearer {token2}"},
    )

    assert response.status_code == 403


def test_user_cannot_create_tracked_product_in_another_household(client):
    create_user(client, username="user1", email="user1@example.com")
    token1 = login_user(client, email="user1@example.com")

    household = create_household(client, token1)
    product = create_product(client)

    create_user(client, username="user2", email="user2@example.com")
    token2 = login_user(client, email="user2@example.com")

    response = client.post(
        f"/households/{household['id']}/tracked-products",
        headers={"Authorization": f"Bearer {token2}"},
        json={
            "product_id": product["id"],
            "minimum_quantity": 2,
        },
    )

    assert response.status_code == 403


def test_user_cannot_update_another_household_tracked_product(client):
    create_user(client, username="user1", email="user1@example.com")
    token1 = login_user(client, email="user1@example.com")

    household = create_household(client, token1)
    product = create_product(client)

    create_tracked_product(client, token1, household["id"], product["id"], minimum_quantity=2)

    create_user(client, username="user2", email="user2@example.com")
    token2 = login_user(client, email="user2@example.com")

    response = client.patch(
        f"/households/{household['id']}/tracked-products/{product['id']}",
        headers={"Authorization": f"Bearer {token2}"},
        json={
            "minimum_quantity": 10,
        },
    )

    assert response.status_code == 403


def test_user_cannot_delete_another_household_tracked_product(client):
    create_user(client, username="user1", email="user1@example.com")
    token1 = login_user(client, email="user1@example.com")

    household = create_household(client, token1)
    product = create_product(client)

    create_tracked_product(client, token1, household["id"], product["id"])

    create_user(client, username="user2", email="user2@example.com")
    token2 = login_user(client, email="user2@example.com")

    response = client.delete(
        f"/households/{household['id']}/tracked-products/{product['id']}",
        headers={"Authorization": f"Bearer {token2}"},
    )

    assert response.status_code == 403


# =========================================================
# LOW STOCK
# =========================================================

def test_get_low_stock_products(client):
    token, household, product = setup_household_and_product(client)

    create_tracked_product(client, token, household["id"], product["id"], minimum_quantity=5)

    response = client.get(
        f"/households/{household['id']}/tracked-products/low-stock",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    data = response.json()

    assert len(data) == 1
    assert data[0]["household_id"] == household["id"]
    assert data[0]["product_id"] == product["id"]
    assert data[0]["minimum_quantity"] == 5
    assert data[0]["current_quantity"] == 0.0


def test_product_is_not_low_stock_when_quantity_is_above_minimum(client):
    token, household, product = setup_household_and_product(client)

    create_tracked_product(client, token, household["id"], product["id"], minimum_quantity=5)

    client.post(
        f"/households/{household['id']}/inventory",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "product_id": product["id"],
            "quantity": "10.000",
        },
    )

    response = client.get(
        f"/households/{household['id']}/tracked-products/low-stock",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    assert response.json() == []


def test_product_is_low_stock_when_quantity_is_below_minimum(client):
    token, household, product = setup_household_and_product(client)

    create_tracked_product(client, token, household["id"], product["id"], minimum_quantity=5)

    client.post(
        f"/households/{household['id']}/inventory",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "product_id": product["id"],
            "quantity": "2.000",
        },
    )

    response = client.get(
        f"/households/{household['id']}/tracked-products/low-stock",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    data = response.json()

    assert len(data) == 1
    assert data[0]["product_id"] == product["id"]
    assert data[0]["minimum_quantity"] == 5
    assert data[0]["current_quantity"] == 2.0


def test_product_is_not_low_stock_when_quantity_equals_minimum(client):
    token, household, product = setup_household_and_product(client)

    create_tracked_product(client, token, household["id"], product["id"], minimum_quantity=5)

    client.post(
        f"/households/{household['id']}/inventory",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "product_id": product["id"],
            "quantity": "5.000",
        },
    )

    response = client.get(
        f"/households/{household['id']}/tracked-products/low-stock",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    assert response.json() == []


def test_low_stock_uses_zero_for_missing_inventory(client):
    token, household, product = setup_household_and_product(client)

    create_tracked_product(client, token, household["id"], product["id"], minimum_quantity=3)

    response = client.get(
        f"/households/{household['id']}/tracked-products/low-stock",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    data = response.json()

    assert len(data) == 1
    assert data[0]["current_quantity"] == 0.0


def test_low_stock_returns_only_low_products(client):
    token, household, product1 = setup_household_and_product(client)

    product2 = create_product(
        client,
        barcode="4601234567891",
        name="Apple",
        brand="No Brand",
        category="fruits",
        unit="kg",
        package_quantity=1,
        package_unit="kg",
    )

    product3 = create_product(
        client,
        barcode="4601234567892",
        name="Juice",
        brand="Rich",
        category="drinks",
        unit="L",
        package_quantity=1,
        package_unit="L",
    )

    create_tracked_product(client, token, household["id"], product1["id"], minimum_quantity=5)
    create_tracked_product(client, token, household["id"], product2["id"], minimum_quantity=3)
    create_tracked_product(client, token, household["id"], product3["id"], minimum_quantity=2)

    client.post(
        f"/households/{household['id']}/inventory",
        headers={"Authorization": f"Bearer {token}"},
        json={"product_id": product1["id"], "quantity": "2.000"},
    )

    client.post(
        f"/households/{household['id']}/inventory",
        headers={"Authorization": f"Bearer {token}"},
        json={"product_id": product2["id"], "quantity": "3.000"},
    )

    client.post(
        f"/households/{household['id']}/inventory",
        headers={"Authorization": f"Bearer {token}"},
        json={"product_id": product3["id"], "quantity": "10.000"},
    )

    response = client.get(
        f"/households/{household['id']}/tracked-products/low-stock",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    data = response.json()

    assert len(data) == 1
    assert data[0]["product_id"] == product1["id"]
    assert data[0]["minimum_quantity"] == 5
    assert data[0]["current_quantity"] == 2.0


def test_user_cannot_access_low_stock_of_another_household(client):
    create_user(client, username="user1", email="user1@example.com")
    token1 = login_user(client, email="user1@example.com")

    household = create_household(client, token1)
    product = create_product(client)

    create_tracked_product(client, token1, household["id"], product["id"], minimum_quantity=5)

    create_user(client, username="user2", email="user2@example.com")
    token2 = login_user(client, email="user2@example.com")

    response = client.get(
        f"/households/{household['id']}/tracked-products/low-stock",
        headers={"Authorization": f"Bearer {token2}"},
    )

    assert response.status_code == 403