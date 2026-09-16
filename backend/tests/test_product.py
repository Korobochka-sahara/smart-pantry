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


# ---------------------------------------------------------
# Создание
# ---------------------------------------------------------


def test_create_product(client):
    response = client.post(
        "/products",
        json={
            "barcode": "4601234567890",
            "name": "Milk",
            "brand": "Prostokvashino",
            "category": "dairy",
            "unit": "L",
            "package_quantity": "1.000",
            "package_unit": "L",
        },
    )

    assert response.status_code == 201

    data = response.json()

    assert "id" in data
    assert data["barcode"] == "4601234567890"
    assert data["name"] == "Milk"
    assert data["brand"] == "Prostokvashino"
    assert data["category"] == "dairy"
    assert data["unit"] == "L"
    assert data["package_quantity"] == "1.000"
    assert data["package_unit"] == "L"


def test_create_product_without_barcode(client):
    response = client.post(
        "/products",
        json={
            "name": "Apple",
            "brand": "No Brand",
            "category": "fruits",
            "unit": "kg",
            "package_quantity": "1.000",
            "package_unit": "kg",
        },
    )

    assert response.status_code == 201

    data = response.json()

    assert data["barcode"] is None
    assert data["name"] == "Apple"


def test_create_product_duplicate_barcode(client):
    create_product(client)

    response = client.post(
        "/products",
        json={
            "barcode": "4601234567890",
            "name": "Another Milk",
            "brand": "Another Brand",
            "category": "dairy",
            "unit": "L",
            "package_quantity": "1.000",
            "package_unit": "L",
        },
    )

    assert response.status_code == 409


# ---------------------------------------------------------
# Получение
# ---------------------------------------------------------


def test_get_product(client):
    product = create_product(client)

    response = client.get(
        f"/products/{product['id']}",
    )

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == product["id"]
    assert data["name"] == "Milk"
    assert data["brand"] == "Prostokvashino"


def test_get_nonexistent_product(client):
    response = client.get(
        "/products/999999",
    )

    assert response.status_code == 404


# ---------------------------------------------------------
# Поиск
# ---------------------------------------------------------


def test_search_product_by_name(client):
    create_product(
        client,
        barcode="4601234567890",
        name="Milk",
    )

    create_product(
        client,
        barcode="4601234567891",
        name="Apple Juice",
        brand="Rich",
        category="drinks",
        unit="L",
        package_unit="L",
    )

    response = client.get(
        "/products/search",
        params={
            "q": "Milk",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 1
    assert data[0]["name"] == "Milk"


def test_search_product_by_brand(client):
    create_product(
        client,
        barcode="4601234567890",
        name="Milk",
        brand="Prostokvashino",
    )

    response = client.get(
        "/products/search",
        params={
            "q": "Prostokvashino",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 1
    assert data[0]["brand"] == "Prostokvashino"


def test_search_product_by_barcode(client):
    create_product(
        client,
        barcode="4601234567890",
        name="Milk",
    )

    response = client.get(
        "/products/search",
        params={
            "q": "4601234567890",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 1
    assert data[0]["barcode"] == "4601234567890"


def test_search_product_case_insensitive(client):
    create_product(
        client,
        name="Milk",
    )

    response = client.get(
        "/products/search",
        params={
            "q": "milk",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 1
    assert data[0]["name"] == "Milk"


def test_search_products_returns_multiple_results(client):
    create_product(
        client,
        barcode="4601234567890",
        name="Milk",
        brand="Prostokvashino",
    )

    create_product(
        client,
        barcode="4601234567891",
        name="Milk Chocolate",
        brand="Alpen Gold",
        category="sweets",
        unit="kg",
        package_quantity=0.1,
        package_unit="kg",
    )

    response = client.get(
        "/products/search",
        params={
            "q": "Milk",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 2