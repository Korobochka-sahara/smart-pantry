import pytest

# ---------------------------------------------------------
# Фикстуры
# ---------------------------------------------------------

@pytest.fixture
def setup_household_and_product(create_user, login_user, create_household, create_product):
    """Создает пользователя, входит в систему, создает домохозяйство и продукт."""
    create_user()
    token = login_user()
    household = create_household(token)
    product = create_product()
    return token, household, product


# ---------------------------------------------------------
# Создание
# ---------------------------------------------------------

def test_create_inventory_item(client, setup_household_and_product, auth_headers):
    token, household, product = setup_household_and_product

    response = client.post(
        f"/households/{household['id']}/inventory",
        headers=auth_headers(token),
        json={
            "product_id": product["id"],
            "quantity": "2.500",
        },
    )

    assert response.status_code == 201
    data = response.json()

    assert data["household_id"] == household["id"]
    assert data["product_id"] == product["id"]
    assert data["quantity"] == "2.500"
    assert "created_at" in data
    assert "updated_at" in data


# ---------------------------------------------------------
# Получение
# ---------------------------------------------------------

def test_get_inventory_item(client, setup_household_and_product, auth_headers):
    token, household, product = setup_household_and_product

    create_response = client.post(
        f"/households/{household['id']}/inventory",
        headers=auth_headers(token),
        json={
            "product_id": product["id"],
            "quantity": "2.500",
        },
    )
    assert create_response.status_code == 201

    response = client.get(
        f"/households/{household['id']}/inventory/{product['id']}",
        headers=auth_headers(token),
    )

    assert response.status_code == 200
    data = response.json()

    assert data["household_id"] == household["id"]
    assert data["product_id"] == product["id"]
    assert data["quantity"] == "2.500"


def test_get_nonexistent_inventory_item(client, setup_household_and_product, auth_headers):
    token, household, product = setup_household_and_product

    response = client.get(
        f"/households/{household['id']}/inventory/{product['id']}",
        headers=auth_headers(token),
    )
    assert response.status_code == 404


# ---------------------------------------------------------
# Бизнес-логика количества
# ---------------------------------------------------------

def test_create_inventory_item_increases_existing_quantity(client, setup_household_and_product, auth_headers):
    token, household, product = setup_household_and_product

    first_response = client.post(
        f"/households/{household['id']}/inventory",
        headers=auth_headers(token),
        json={
            "product_id": product["id"],
            "quantity": "2.500",
        },
    )
    assert first_response.status_code == 201
    assert first_response.json()["quantity"] == "2.500"

    second_response = client.post(
        f"/households/{household['id']}/inventory",
        headers=auth_headers(token),
        json={
            "product_id": product["id"],
            "quantity": "1.250",
        },
    )
    assert second_response.status_code == 201

    data = second_response.json()
    assert data["quantity"] == "3.750"


def test_update_inventory_item_replaces_quantity(client, setup_household_and_product, auth_headers):
    token, household, product = setup_household_and_product

    create_response = client.post(
        f"/households/{household['id']}/inventory",
        headers=auth_headers(token),
        json={
            "product_id": product["id"],
            "quantity": "5.500",
        },
    )
    assert create_response.status_code == 201

    response = client.patch(
        f"/households/{household['id']}/inventory/{product['id']}",
        headers=auth_headers(token),
        json={
            "quantity": "2.250",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["quantity"] == "2.250"


def test_update_inventory_item_without_quantity_does_not_change_quantity(client, setup_household_and_product, auth_headers):
    token, household, product = setup_household_and_product

    create_response = client.post(
        f"/households/{household['id']}/inventory",
        headers=auth_headers(token),
        json={
            "product_id": product["id"],
            "quantity": "5.500",
        },
    )
    assert create_response.status_code == 201

    response = client.patch(
        f"/households/{household['id']}/inventory/{product['id']}",
        headers=auth_headers(token),
        json={},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["quantity"] == "5.500"


# ---------------------------------------------------------
# Валидация
# ---------------------------------------------------------

def test_create_inventory_item_with_nonexistent_product(client, setup_household_and_product, auth_headers):
    token, household, product = setup_household_and_product

    response = client.post(
        f"/households/{household['id']}/inventory",
        headers=auth_headers(token),
        json={
            "product_id": 999999,
            "quantity": "1.000",
        },
    )
    assert response.status_code == 404


def test_create_inventory_item_with_zero_quantity(client, setup_household_and_product, auth_headers):
    token, household, product = setup_household_and_product

    response = client.post(
        f"/households/{household['id']}/inventory",
        headers=auth_headers(token),
        json={
            "product_id": product["id"],
            "quantity": "0",
        },
    )
    assert response.status_code == 422


def test_create_inventory_item_with_negative_quantity(client, setup_household_and_product, auth_headers):
    token, household, product = setup_household_and_product

    response = client.post(
        f"/households/{household['id']}/inventory",
        headers=auth_headers(token),
        json={
            "product_id": product["id"],
            "quantity": "-1.000",
        },
    )
    assert response.status_code == 422


def test_update_inventory_item_with_negative_quantity(client, setup_household_and_product, auth_headers):
    token, household, product = setup_household_and_product

    create_response = client.post(
        f"/households/{household['id']}/inventory",
        headers=auth_headers(token),
        json={
            "product_id": product["id"],
            "quantity": "5.000",
        },
    )
    assert create_response.status_code == 201

    response = client.patch(
        f"/households/{household['id']}/inventory/{product['id']}",
        headers=auth_headers(token),
        json={
            "quantity": "-1.000",
        },
    )
    assert response.status_code == 422


def test_update_inventory_item_to_zero(client, setup_household_and_product, auth_headers):
    token, household, product = setup_household_and_product

    create_response = client.post(
        f"/households/{household['id']}/inventory",
        headers=auth_headers(token),
        json={
            "product_id": product["id"],
            "quantity": "5.000",
        },
    )
    assert create_response.status_code == 201

    response = client.patch(
        f"/households/{household['id']}/inventory/{product['id']}",
        headers=auth_headers(token),
        json={
            "quantity": "0",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["quantity"] == "0.000"


# ---------------------------------------------------------
# Удаление
# ---------------------------------------------------------

def test_delete_inventory_item(client, setup_household_and_product, auth_headers):
    token, household, product = setup_household_and_product

    create_response = client.post(
        f"/households/{household['id']}/inventory",
        headers=auth_headers(token),
        json={
            "product_id": product["id"],
            "quantity": "2.500",
        },
    )
    assert create_response.status_code == 201

    response = client.delete(
        f"/households/{household['id']}/inventory/{product['id']}",
        headers=auth_headers(token),
    )
    assert response.status_code == 204

    get_response = client.get(
        f"/households/{household['id']}/inventory/{product['id']}",
        headers=auth_headers(token),
    )
    assert get_response.status_code == 404


def test_delete_nonexistent_inventory_item(client, setup_household_and_product, auth_headers):
    token, household, product = setup_household_and_product

    response = client.delete(
        f"/households/{household['id']}/inventory/{product['id']}",
        headers=auth_headers(token),
    )
    assert response.status_code == 404


# ---------------------------------------------------------
# Список inventory
# ---------------------------------------------------------

def test_get_household_inventory(client, setup_household_and_product, create_product, auth_headers):
    token, household, product1 = setup_household_and_product

    product2 = create_product(
        barcode="4601234567891",
        name="Apple",
        brand="No Brand",
        category="fruits",
        unit="kg",
        package_quantity=1,
        package_unit="kg",
    )

    client.post(
        f"/households/{household['id']}/inventory",
        headers=auth_headers(token),
        json={
            "product_id": product1["id"],
            "quantity": "2.500",
        },
    )

    client.post(
        f"/households/{household['id']}/inventory",
        headers=auth_headers(token),
        json={
            "product_id": product2["id"],
            "quantity": "3.000",
        },
    )

    response = client.get(
        f"/households/{household['id']}/inventory",
        headers=auth_headers(token),
    )
    assert response.status_code == 200
    data = response.json()

    assert len(data) == 2
    assert data[0]["product_id"] == product1["id"]
    assert data[0]["quantity"] == "2.500"
    assert data[1]["product_id"] == product2["id"]
    assert data[1]["quantity"] == "3.000"


def test_get_empty_household_inventory(client, setup_household_and_product, auth_headers):
    token, household, product = setup_household_and_product

    response = client.get(
        f"/households/{household['id']}/inventory",
        headers=auth_headers(token),
    )
    assert response.status_code == 200
    data = response.json()
    assert data == []


# ---------------------------------------------------------
# Права доступа
# ---------------------------------------------------------

def test_user_cannot_access_another_household_inventory(client, create_user, login_user, create_household, create_product, auth_headers):
    create_user(username="user1", email="user1@example.com")
    token1 = login_user(email="user1@example.com")

    household = create_household(token1)
    product = create_product()

    create_response = client.post(
        f"/households/{household['id']}/inventory",
        headers=auth_headers(token1),
        json={
            "product_id": product["id"],
            "quantity": "2.000",
        },
    )
    assert create_response.status_code == 201

    create_user(username="user2", email="user2@example.com")
    token2 = login_user(email="user2@example.com")

    response = client.get(
        f"/households/{household['id']}/inventory",
        headers=auth_headers(token2),
    )
    assert response.status_code == 403


def test_user_cannot_get_inventory_item_from_another_household(client, create_user, login_user, create_household, create_product, auth_headers):
    create_user(username="user1", email="user1@example.com")
    token1 = login_user(email="user1@example.com")

    household = create_household(token1)
    product = create_product()

    create_response = client.post(
        f"/households/{household['id']}/inventory",
        headers=auth_headers(token1),
        json={
            "product_id": product["id"],
            "quantity": "2.000",
        },
    )
    assert create_response.status_code == 201

    create_user(username="user2", email="user2@example.com")
    token2 = login_user(email="user2@example.com")

    response = client.get(
        f"/households/{household['id']}/inventory/{product['id']}",
        headers=auth_headers(token2),
    )
    assert response.status_code == 403


def test_user_cannot_update_another_household_inventory(client, create_user, login_user, create_household, create_product, auth_headers):
    create_user(username="user1", email="user1@example.com")
    token1 = login_user(email="user1@example.com")

    household = create_household(token1)
    product = create_product()

    create_response = client.post(
        f"/households/{household['id']}/inventory",
        headers=auth_headers(token1),
        json={
            "product_id": product["id"],
            "quantity": "2.000",
        },
    )
    assert create_response.status_code == 201

    create_user(username="user2", email="user2@example.com")
    token2 = login_user(email="user2@example.com")

    response = client.patch(
        f"/households/{household['id']}/inventory/{product['id']}",
        headers=auth_headers(token2),
        json={
            "quantity": "10.000",
        },
    )
    assert response.status_code == 403


def test_user_cannot_delete_another_household_inventory(client, create_user, login_user, create_household, create_product, auth_headers):
    create_user(username="user1", email="user1@example.com")
    token1 = login_user(email="user1@example.com")

    household = create_household(token1)
    product = create_product()

    create_response = client.post(
        f"/households/{household['id']}/inventory",
        headers=auth_headers(token1),
        json={
            "product_id": product["id"],
            "quantity": "2.000",
        },
    )
    assert create_response.status_code == 201

    create_user(username="user2", email="user2@example.com")
    token2 = login_user(email="user2@example.com")

    response = client.delete(
        f"/households/{household['id']}/inventory/{product['id']}",
        headers=auth_headers(token2),
    )
    assert response.status_code == 403


def test_household_inventory_is_isolated(client, create_user, login_user, create_household, create_product, auth_headers):
    create_user()
    token = login_user()

    household1 = create_household(token, name="Household 1")

    product1 = create_product(
        barcode="4601234567891",
        name="Milk",
    )

    product2 = create_product(
        barcode="4601234567892",
        name="Apple",
        category="fruits",
        unit="kg",
        package_quantity=1,
        package_unit="kg",
    )

    client.post(
        f"/households/{household1['id']}/inventory",
        headers=auth_headers(token),
        json={
            "product_id": product1["id"],
            "quantity": "2.000",
        },
    )
    client.post(
        f"/households/{household1['id']}/inventory",
        headers=auth_headers(token),
        json={
            "product_id": product2["id"],
            "quantity": "3.000",
        },
    )

    household2 = create_household(token, name="Household 2")

    client.post(
        f"/households/{household2['id']}/inventory",
        headers=auth_headers(token),
        json={
            "product_id": product1["id"],
            "quantity": "10.000",
        },
    )

    response1 = client.get(
        f"/households/{household1['id']}/inventory",
        headers=auth_headers(token),
    )
    assert response1.status_code == 200
    data1 = response1.json()
    assert len(data1) == 2
    
    quantities1 = {item["product_id"]: item["quantity"] for item in data1}
    assert quantities1[product1["id"]] == "2.000"
    assert quantities1[product2["id"]] == "3.000"

    # Проверяем второе домохозяйство
    response2 = client.get(
        f"/households/{household2['id']}/inventory",
        headers=auth_headers(token),
    )
    assert response2.status_code == 200
    data2 = response2.json()
    assert len(data2) == 1
    assert data2[0]["product_id"] == product1["id"]
    assert data2[0]["quantity"] == "10.000"


# ---------------------------------------------------------
# Несуществующий household
# ---------------------------------------------------------

def test_get_inventory_from_nonexistent_household(client, create_user, login_user, auth_headers):
    create_user()
    token = login_user()

    response = client.get(
        "/households/999999/inventory",
        headers=auth_headers(token),
    )
    assert response.status_code in (403, 404)


def test_create_inventory_in_nonexistent_household(client, create_user, create_product, login_user, auth_headers):
    create_user()
    token = login_user()
    product = create_product()

    response = client.post(
        "/households/999999/inventory",
        headers=auth_headers(token),
        json={
            "product_id": product["id"],
            "quantity": "2.000",
        },
    )
    assert response.status_code in (403, 404)


# ---------------------------------------------------------
# Валидация product_id
# ---------------------------------------------------------

def test_create_inventory_with_zero_product_id(client, create_product, create_household, login_user, create_user, auth_headers):
    create_user(email="inventory_test@example.com", username="inventory_tester")

    token = login_user(email="inventory_test@example.com")
    
    household = create_household(token, name="Second Household")

    product = create_product(
        barcode="4601234567899",
        name="Apple",
        category="fruits",
        unit="kg",
        package_quantity=1,
        package_unit="kg",
    )

    response = client.post(
        f"/households/{household['id']}/inventory",
        headers=auth_headers(token),
        json={
            "product_id": 0,
            "quantity": "1.000",
        },
    )
    assert response.status_code == 422


def test_create_inventory_with_negative_product_id(client, setup_household_and_product, auth_headers):
    token, household, product = setup_household_and_product

    response = client.post(
        f"/households/{household['id']}/inventory",
        headers=auth_headers(token),
        json={
            "product_id": -1,
            "quantity": "1.000",
        },
    )
    assert response.status_code == 422


# ---------------------------------------------------------
# Валидация количества
# ---------------------------------------------------------

def test_create_inventory_with_too_many_decimal_places(client, setup_household_and_product, auth_headers):
    token, household, product = setup_household_and_product

    response = client.post(
        f"/households/{household['id']}/inventory",
        headers=auth_headers(token),
        json={
            "product_id": product["id"],
            "quantity": "1.1234",
        },
    )
    assert response.status_code == 422


def test_update_inventory_with_too_many_decimal_places(client, setup_household_and_product, auth_headers):
    token, household, product = setup_household_and_product

    client.post(
        f"/households/{household['id']}/inventory",
        headers=auth_headers(token),
        json={
            "product_id": product["id"],
            "quantity": "1.000",
        },
    )

    response = client.patch(
        f"/households/{household['id']}/inventory/{product['id']}",
        headers=auth_headers(token),
        json={
            "quantity": "2.1234",
        },
    )
    assert response.status_code == 422


def test_create_inventory_with_too_many_digits(client, setup_household_and_product, auth_headers):
    token, household, product = setup_household_and_product

    response = client.post(
        f"/households/{household['id']}/inventory",
        headers=auth_headers(token),
        json={
            "product_id": product["id"],
            "quantity": "12345678.123",
        },
    )
    assert response.status_code == 422


def test_update_inventory_with_too_many_digits(client, setup_household_and_product, auth_headers):
    token, household, product = setup_household_and_product

    client.post(
        f"/households/{household['id']}/inventory",
        headers=auth_headers(token),
        json={
            "product_id": product["id"],
            "quantity": "1.000",
        },
    )

    response = client.patch(
        f"/households/{household['id']}/inventory/{product['id']}",
        headers=auth_headers(token),
        json={
            "quantity": "12345678.123",
        },
    )
    assert response.status_code == 422