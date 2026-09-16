# tests/test_inventory.py

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

    data = response.json()

    client.headers.update(
        {
            "Authorization": f"Bearer {data['access_token']}"
        }
    )

    return data


def create_household(client, name="My Household"):
    response = client.post(
        "/households",
        json={
            "name": name,
        },
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
    create_user(client)
    login_user(client)
    household = create_household(client)
    product = create_product(client)

    return household, product


# ---------------------------------------------------------
# Создание
# ---------------------------------------------------------


def test_create_inventory_item(client):
    household, product = setup_household_and_product(client)

    response = client.post(
        f"/households/{household['id']}/inventory",
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


def test_get_inventory_item(client):
    household, product = setup_household_and_product(client)

    create_response = client.post(
        f"/households/{household['id']}/inventory",
        json={
            "product_id": product["id"],
            "quantity": "2.500",
        },
    )

    assert create_response.status_code == 201

    response = client.get(
        f"/households/{household['id']}/inventory/{product['id']}",
    )

    assert response.status_code == 200

    data = response.json()

    assert data["household_id"] == household["id"]
    assert data["product_id"] == product["id"]
    assert data["quantity"] == "2.500"


def test_get_nonexistent_inventory_item(client):
    household, product = setup_household_and_product(client)

    response = client.get(
        f"/households/{household['id']}/inventory/{product['id']}",
    )

    assert response.status_code == 404

# ---------------------------------------------------------
# Бизнес-логика количества
# ---------------------------------------------------------


def test_create_inventory_item_increases_existing_quantity(client):
    household, product = setup_household_and_product(client)

    first_response = client.post(
        f"/households/{household['id']}/inventory",
        json={
            "product_id": product["id"],
            "quantity": "2.500",
        },
    )

    assert first_response.status_code == 201
    assert first_response.json()["quantity"] == "2.500"

    second_response = client.post(
        f"/households/{household['id']}/inventory",
        json={
            "product_id": product["id"],
            "quantity": "1.250",
        },
    )

    assert second_response.status_code == 201

    data = second_response.json()

    # 2.500 + 1.250 = 3.750
    assert data["quantity"] == "3.750"

def test_update_inventory_item_replaces_quantity(client):
    household, product = setup_household_and_product(client)

    create_response = client.post(
        f"/households/{household['id']}/inventory",
        json={
            "product_id": product["id"],
            "quantity": "5.500",
        },
    )

    assert create_response.status_code == 201

    response = client.patch(
        f"/households/{household['id']}/inventory/{product['id']}",
        json={
            "quantity": "2.250",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["quantity"] == "2.250"

def test_update_inventory_item_without_quantity_does_not_change_quantity(client):
    household, product = setup_household_and_product(client)

    create_response = client.post(
        f"/households/{household['id']}/inventory",
        json={
            "product_id": product["id"],
            "quantity": "5.500",
        },
    )

    assert create_response.status_code == 201

    response = client.patch(
        f"/households/{household['id']}/inventory/{product['id']}",
        json={},
    )

    assert response.status_code == 200

    data = response.json()

    assert data["quantity"] == "5.500"

# ---------------------------------------------------------
# Валидация
# ---------------------------------------------------------


def test_create_inventory_item_with_nonexistent_product(client):
    household, product = setup_household_and_product(client)

    response = client.post(
        f"/households/{household['id']}/inventory",
        json={
            "product_id": 999999,
            "quantity": "1.000",
        },
    )

    assert response.status_code == 404


def test_create_inventory_item_with_zero_quantity(client):
    household, product = setup_household_and_product(client)

    response = client.post(
        f"/households/{household['id']}/inventory",
        json={
            "product_id": product["id"],
            "quantity": "0",
        },
    )

    assert response.status_code == 422


def test_create_inventory_item_with_negative_quantity(client):
    household, product = setup_household_and_product(client)

    response = client.post(
        f"/households/{household['id']}/inventory",
        json={
            "product_id": product["id"],
            "quantity": "-1.000",
        },
    )

    assert response.status_code == 422


def test_update_inventory_item_with_negative_quantity(client):
    household, product = setup_household_and_product(client)

    create_response = client.post(
        f"/households/{household['id']}/inventory",
        json={
            "product_id": product["id"],
            "quantity": "5.000",
        },
    )

    assert create_response.status_code == 201

    response = client.patch(
        f"/households/{household['id']}/inventory/{product['id']}",
        json={
            "quantity": "-1.000",
        },
    )

    assert response.status_code == 422

def test_update_inventory_item_to_zero(client):
    household, product = setup_household_and_product(client)

    create_response = client.post(
        f"/households/{household['id']}/inventory",
        json={
            "product_id": product["id"],
            "quantity": "5.000",
        },
    )

    assert create_response.status_code == 201

    response = client.patch(
        f"/households/{household['id']}/inventory/{product['id']}",
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


def test_delete_inventory_item(client):
    household, product = setup_household_and_product(client)

    create_response = client.post(
        f"/households/{household['id']}/inventory",
        json={
            "product_id": product["id"],
            "quantity": "2.500",
        },
    )

    assert create_response.status_code == 201

    response = client.delete(
        f"/households/{household['id']}/inventory/{product['id']}",
    )

    assert response.status_code == 204

    get_response = client.get(
        f"/households/{household['id']}/inventory/{product['id']}",
    )

    assert get_response.status_code == 404


def test_delete_nonexistent_inventory_item(client):
    household, product = setup_household_and_product(client)

    response = client.delete(
        f"/households/{household['id']}/inventory/{product['id']}",
    )

    assert response.status_code == 404

# ---------------------------------------------------------
# Список inventory
# ---------------------------------------------------------


def test_get_household_inventory(client):
    household, product1 = setup_household_and_product(client)

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

    client.post(
        f"/households/{household['id']}/inventory",
        json={
            "product_id": product1["id"],
            "quantity": "2.500",
        },
    )

    client.post(
        f"/households/{household['id']}/inventory",
        json={
            "product_id": product2["id"],
            "quantity": "3.000",
        },
    )

    response = client.get(
        f"/households/{household['id']}/inventory",
    )

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 2

    assert data[0]["product_id"] == product1["id"]
    assert data[0]["quantity"] == "2.500"

    assert data[1]["product_id"] == product2["id"]
    assert data[1]["quantity"] == "3.000"

def test_get_empty_household_inventory(client):
    household, product = setup_household_and_product(client)

    response = client.get(
        f"/households/{household['id']}/inventory",
    )

    assert response.status_code == 200

    data = response.json()

    assert data == []

# ---------------------------------------------------------
# Права доступа
# ---------------------------------------------------------


def test_user_cannot_access_another_household_inventory(client):
    # Первый пользователь создаёт household
    create_user(
        client,
        username="user1",
        email="user1@example.com",
    )

    login_user(
        client,
        email="user1@example.com",
    )

    household = create_household(client)

    product = create_product(client)

    create_response = client.post(
        f"/households/{household['id']}/inventory",
        json={
            "product_id": product["id"],
            "quantity": "2.000",
        },
    )

    assert create_response.status_code == 201

    # Регистрируем второго пользователя
    create_user(
        client,
        username="user2",
        email="user2@example.com",
    )

    login_user(
        client,
        email="user2@example.com",
    )

    response = client.get(
        f"/households/{household['id']}/inventory",
    )

    assert response.status_code == 403

def test_user_cannot_get_inventory_item_from_another_household(client):
    create_user(
        client,
        username="user1",
        email="user1@example.com",
    )

    login_user(
        client,
        email="user1@example.com",
    )

    household = create_household(client)
    product = create_product(client)

    create_response = client.post(
        f"/households/{household['id']}/inventory",
        json={
            "product_id": product["id"],
            "quantity": "2.000",
        },
    )

    assert create_response.status_code == 201

    create_user(
        client,
        username="user2",
        email="user2@example.com",
    )

    login_user(
        client,
        email="user2@example.com",
    )

    response = client.get(
        f"/households/{household['id']}/inventory/{product['id']}",
    )

    assert response.status_code == 403

def test_user_cannot_update_another_household_inventory(client):
    create_user(
        client,
        username="user1",
        email="user1@example.com",
    )

    login_user(
        client,
        email="user1@example.com",
    )

    household = create_household(client)
    product = create_product(client)

    create_response = client.post(
        f"/households/{household['id']}/inventory",
        json={
            "product_id": product["id"],
            "quantity": "2.000",
        },
    )

    assert create_response.status_code == 201

    create_user(
        client,
        username="user2",
        email="user2@example.com",
    )

    login_user(
        client,
        email="user2@example.com",
    )

    response = client.patch(
        f"/households/{household['id']}/inventory/{product['id']}",
        json={
            "quantity": "10.000",
        },
    )

    assert response.status_code == 403

def test_user_cannot_delete_another_household_inventory(client):
    create_user(
        client,
        username="user1",
        email="user1@example.com",
    )

    login_user(
        client,
        email="user1@example.com",
    )

    household = create_household(client)
    product = create_product(client)

    create_response = client.post(
        f"/households/{household['id']}/inventory",
        json={
            "product_id": product["id"],
            "quantity": "2.000",
        },
    )

    assert create_response.status_code == 201

    create_user(
        client,
        username="user2",
        email="user2@example.com",
    )

    login_user(
        client,
        email="user2@example.com",
    )

    response = client.delete(
        f"/households/{household['id']}/inventory/{product['id']}",
    )

    assert response.status_code == 403

def test_household_inventory_is_isolated(client):
    create_user(client)
    login_user(client)

    household1 = create_household(client, name="Household 1")

    product1 = create_product(
        client,
        barcode="4601234567891",
        name="Milk",
    )

    product2 = create_product(
        client,
        barcode="4601234567892",
        name="Apple",
        category="fruits",
        unit="kg",
        package_quantity=1,
        package_unit="kg",
    )

    # Добавляем оба продукта в первое домохозяйство
    response = client.post(
        f"/households/{household1['id']}/inventory",
        json={
            "product_id": product1["id"],
            "quantity": "2.000",
        },
    )
    assert response.status_code == 201

    response = client.post(
        f"/households/{household1['id']}/inventory",
        json={
            "product_id": product2["id"],
            "quantity": "3.000",
        },
    )
    assert response.status_code == 201

    # Создаём второе домохозяйство тем же пользователем
    household2 = create_household(client, name="Household 2")

    # Добавляем туда только product1
    response = client.post(
        f"/households/{household2['id']}/inventory",
        json={
            "product_id": product1["id"],
            "quantity": "10.000",
        },
    )
    assert response.status_code == 201

    # Проверяем первое домохозяйство
    response = client.get(
        f"/households/{household1['id']}/inventory",
    )

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 2

    assert data[0]["household_id"] == household1["id"]
    assert data[1]["household_id"] == household1["id"]

    quantities = {
        item["product_id"]: item["quantity"]
        for item in data
    }

    assert quantities[product1["id"]] == "2.000"
    assert quantities[product2["id"]] == "3.000"

    # Проверяем второе домохозяйство
    response = client.get(
        f"/households/{household2['id']}/inventory",
    )

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 1
    assert data[0]["household_id"] == household2["id"]
    assert data[0]["product_id"] == product1["id"]
    assert data[0]["quantity"] == "10.000"

# ---------------------------------------------------------
# Изоляция inventory между household
# ---------------------------------------------------------

def test_household_inventory_is_isolated(client):
    create_user(client)
    login_user(client)

    household1 = create_household(client, name="Household 1")

    product1 = create_product(
        client,
        barcode="4601234567891",
        name="Milk",
    )

    product2 = create_product(
        client,
        barcode="4601234567892",
        name="Apple",
        category="fruits",
        unit="kg",
        package_quantity=1,
        package_unit="kg",
    )

    response = client.post(
        f"/households/{household1['id']}/inventory",
        json={
            "product_id": product1["id"],
            "quantity": "2.000",
        },
    )
    assert response.status_code == 201

    response = client.post(
        f"/households/{household1['id']}/inventory",
        json={
            "product_id": product2["id"],
            "quantity": "3.000",
        },
    )
    assert response.status_code == 201

    household2 = create_household(client, name="Household 2")

    response = client.post(
        f"/households/{household2['id']}/inventory",
        json={
            "product_id": product1["id"],
            "quantity": "10.000",
        },
    )
    assert response.status_code == 201

    # В первом household остаются только его данные
    response = client.get(
        f"/households/{household1['id']}/inventory",
    )

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 2

    quantities = {
        item["product_id"]: item["quantity"]
        for item in data
    }

    assert quantities[product1["id"]] == "2.000"
    assert quantities[product2["id"]] == "3.000"

    # Во втором household — только его данные
    response = client.get(
        f"/households/{household2['id']}/inventory",
    )

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 1
    assert data[0]["product_id"] == product1["id"]
    assert data[0]["quantity"] == "10.000"


# ---------------------------------------------------------
# Несуществующий household
# ---------------------------------------------------------

def test_get_inventory_from_nonexistent_household(client):
    create_user(client)
    login_user(client)

    response = client.get(
        "/households/999999/inventory",
    )

    assert response.status_code in (403, 404)


def test_create_inventory_in_nonexistent_household(client):
    create_user(client)
    login_user(client)

    product = create_product(client)

    response = client.post(
        "/households/999999/inventory",
        json={
            "product_id": product["id"],
            "quantity": "2.000",
        },
    )

    assert response.status_code in (403, 404)


# ---------------------------------------------------------
# Валидация product_id
# ---------------------------------------------------------

def test_create_inventory_with_zero_product_id(client):
    setup_household_and_product(client)

    household = create_household(client, name="Second Household")

    product = create_product(
        client,
        barcode="4601234567899",
        name="Apple",
        category="fruits",
        unit="kg",
        package_quantity=1,
        package_unit="kg",
    )

    response = client.post(
        f"/households/{household['id']}/inventory",
        json={
            "product_id": 0,
            "quantity": "1.000",
        },
    )

    assert response.status_code == 422


def test_create_inventory_with_negative_product_id(client):
    household, product = setup_household_and_product(client)

    response = client.post(
        f"/households/{household['id']}/inventory",
        json={
            "product_id": -1,
            "quantity": "1.000",
        },
    )

    assert response.status_code == 422


# ---------------------------------------------------------
# Валидация количества
# ---------------------------------------------------------

def test_create_inventory_with_too_many_decimal_places(client):
    household, product = setup_household_and_product(client)

    response = client.post(
        f"/households/{household['id']}/inventory",
        json={
            "product_id": product["id"],
            "quantity": "1.1234",
        },
    )

    assert response.status_code == 422


def test_update_inventory_with_too_many_decimal_places(client):
    household, product = setup_household_and_product(client)

    response = client.post(
        f"/households/{household['id']}/inventory",
        json={
            "product_id": product["id"],
            "quantity": "1.000",
        },
    )

    assert response.status_code == 201

    response = client.patch(
        f"/households/{household['id']}/inventory/{product['id']}",
        json={
            "quantity": "2.1234",
        },
    )

    assert response.status_code == 422


def test_create_inventory_with_too_many_digits(client):
    household, product = setup_household_and_product(client)

    response = client.post(
        f"/households/{household['id']}/inventory",
        json={
            "product_id": product["id"],
            "quantity": "12345678.123",
        },
    )

    assert response.status_code == 422


def test_update_inventory_with_too_many_digits(client):
    household, product = setup_household_and_product(client)

    response = client.post(
        f"/households/{household['id']}/inventory",
        json={
            "product_id": product["id"],
            "quantity": "1.000",
        },
    )

    assert response.status_code == 201

    response = client.patch(
        f"/households/{household['id']}/inventory/{product['id']}",
        json={
            "quantity": "12345678.123",
        },
    )

    assert response.status_code == 422