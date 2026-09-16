from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.household_member import HouseholdMember
from app.models.inventory_item import InventoryItem
from app.models.product import Product
from app.models.tracked_product import TrackedProduct
from app.schemas.tracked_product import (
    TrackedProductCreate,
    TrackedProductUpdate,
)

from app.services.auxiliary_functions import (
    ProductNotFoundError,
    TrackedProductConflictError,
    TrackedProductNotFoundError,
    require_household_access,
)


def get_tracked_product(
    db: Session,
    household_id: int,
    product_id: int,
) -> TrackedProduct | None:
    stmt = select(TrackedProduct).where(
        TrackedProduct.household_id == household_id,
        TrackedProduct.product_id == product_id,
    )

    return db.scalar(stmt)


def get_household_tracked_products(
    db: Session,
    household_id: int,
) -> list[TrackedProduct]:
    stmt = (
        select(TrackedProduct)
        .where(
            TrackedProduct.household_id == household_id,
        )
        .order_by(TrackedProduct.product_id)
    )

    return list(db.scalars(stmt).all())


def create_tracked_product(
    db: Session,
    household_id: int,
    user_id: int,
    data: TrackedProductCreate,
) -> TrackedProduct:

    require_household_access(
        db,
        household_id,
        user_id,
    )

    product = db.get(
        Product,
        data.product_id,
    )

    if product is None:
        raise ProductNotFoundError(
            "Product not found"
        )

    existing = get_tracked_product(
        db,
        household_id,
        data.product_id,
    )

    if existing is not None:
        raise TrackedProductConflictError(
            "Product is already being tracked"
        )

    tracked_product = TrackedProduct(
        household_id=household_id,
        product_id=data.product_id,
        minimum_quantity=data.minimum_quantity,
    )

    db.add(tracked_product)
    db.commit()
    db.refresh(tracked_product)

    return tracked_product


def update_tracked_product(
    db: Session,
    household_id: int,
    user_id: int,
    product_id: int,
    data: TrackedProductUpdate,
) -> TrackedProduct:

    require_household_access(
        db,
        household_id,
        user_id,
    )

    tracked_product = get_tracked_product(
        db,
        household_id,
        product_id,
    )

    if tracked_product is None:
        raise TrackedProductNotFoundError(
            "Tracked product not found"
        )

    tracked_product.minimum_quantity = data.minimum_quantity

    db.commit()
    db.refresh(tracked_product)

    return tracked_product


def delete_tracked_product(
    db: Session,
    household_id: int,
    user_id: int,
    product_id: int,
) -> None:

    require_household_access(
        db,
        household_id,
        user_id,
    )

    tracked_product = get_tracked_product(
        db,
        household_id,
        product_id,
    )

    if tracked_product is None:
        raise TrackedProductNotFoundError(
            "Tracked product not found"
        )

    db.delete(tracked_product)
    db.commit()


def get_low_stock_products(
    db: Session,
    household_id: int,
) -> list[tuple[TrackedProduct, float]]:

    current_quantity = func.coalesce(
        InventoryItem.quantity,
        0,
    )

    stmt = (
        select(
            TrackedProduct,
            current_quantity.label("current_quantity"),
        )
        .outerjoin(
            InventoryItem,
            (
                (InventoryItem.household_id == TrackedProduct.household_id)
                & (
                    InventoryItem.product_id
                    == TrackedProduct.product_id
                )
            ),
        )
        .where(
            TrackedProduct.household_id == household_id,
            current_quantity < TrackedProduct.minimum_quantity,
        )
        .order_by(TrackedProduct.product_id)
    )

    return [
        (tracked_product, float(quantity))
        for tracked_product, quantity in db.execute(stmt).all()
    ]