from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.models.product import Product
from app.schemas.product import ProductCreate

from app.services.auxiliary_functions import ProductConflictError


def normalize_text(value: str) -> str:
    return " ".join(value.strip().split())


def search_products(
    db: Session,
    query: str,
) -> list[Product]:

    query = normalize_text(query)

    if not query:
        return []

    search_pattern = f"%{query}%"

    stmt = (
        select(Product)
        .where(
            or_(
                Product.name.ilike(search_pattern),
                Product.brand.ilike(search_pattern),
                Product.barcode.ilike(search_pattern),
            )
        )
        .order_by(Product.name)
    )

    return list(db.scalars(stmt).all())


def create_product(
    db: Session,
    product_data: ProductCreate,
) -> Product:

    name = normalize_text(product_data.name)

    brand = (
        normalize_text(product_data.brand)
        if product_data.brand is not None
        else None
    )

    barcode = (
        product_data.barcode.strip()
        if product_data.barcode is not None
        else None
    )

    # проверяем уникальность штрихкода
    if barcode is not None:
        existing_product = db.scalar(
            select(Product).where(
                Product.barcode == barcode
            )
        )

        if existing_product is not None:
            raise ProductConflictError(
                "Product with this barcode already exists"
            )

    product = Product(
        barcode=barcode,
        name=name,
        brand=brand,
        category=product_data.category,
        unit=product_data.unit,
        package_quantity=product_data.package_quantity,
        package_unit=product_data.package_unit,
    )

    db.add(product)
    db.commit()
    db.refresh(product)

    return product


def get_product(
    db: Session,
    product_id: int,
) -> Product | None:

    return db.get(Product, product_id)