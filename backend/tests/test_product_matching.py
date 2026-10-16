from app.services.product_matching import find_product_candidates


def test_exact_product_match(db, create_product):
    """Точное название и размер упаковки должны находиться."""

    create_product(
        barcode="4600000000001",
        name="Milk",
        brand="TestBrand",
        category="dairy",
        unit="l",
        package_quantity=1,
        package_unit="l",
    )

    candidates = find_product_candidates(
        db,
        {
            "name": "Milk",
            "brand": "TestBrand",
            "quantity": 1,
            "unit": "l",
            "package_quantity": 1,
            "package_unit": "l",
        },
    )

    assert len(candidates) >= 1
    assert candidates[0]["name"] == "Milk"
    assert candidates[0]["score"] >= 90


def test_exact_package_ranks_higher(db, create_product):
    """При прочих равных размер упаковки влияет на рейтинг."""

    create_product(
        barcode="4600000000002",
        name="Milk",
        brand="TestBrand",
        category="dairy",
        unit="l",
        package_quantity=1,
        package_unit="l",
    )

    create_product(
        barcode="4600000000003",
        name="Milk",
        brand="TestBrand",
        category="dairy",
        unit="l",
        package_quantity=2,
        package_unit="l",
    )

    candidates = find_product_candidates(
        db,
        {
            "name": "Milk",
            "brand": "TestBrand",
            "quantity": 1,
            "unit": "l",
            "package_quantity": 1,
            "package_unit": "l",
        },
    )

    assert len(candidates) == 2
    assert candidates[0]["package_quantity"] == 1.0
    assert candidates[0]["score"] > candidates[1]["score"]


def test_unrelated_product_is_not_suggested(db, create_product):
    """Совершенно другое название не должно попасть в кандидаты."""

    create_product(
        barcode="4600000000004",
        name="Milk",
        brand="TestBrand",
        category="dairy",
        unit="l",
        package_quantity=1,
        package_unit="l",
    )

    candidates = find_product_candidates(
        db,
        {
            "name": "нев.конд.батончик ср.кл.",
            "brand": None,
            "quantity": 1,
            "unit": "pcs",
            "package_quantity": 50,
            "package_unit": "g",
        },
    )

    assert candidates == []


def test_candidate_limit(db, create_product):
    """Сервис должен возвращать не больше заданного количества кандидатов."""

    for index in range(5):
        create_product(
            barcode=f"46000000001{index:03d}",
            name=f"Milk {index}",
            brand="TestBrand",
            category="dairy",
            unit="l",
            package_quantity=1,
            package_unit="l",
        )

    candidates = find_product_candidates(
        db,
        {
            "name": "Milk",
            "brand": "TestBrand",
            "quantity": 1,
            "unit": "l",
            "package_quantity": 1,
            "package_unit": "l",
        },
        limit=3,
    )

    assert len(candidates) <= 3