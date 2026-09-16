from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.household_member import HouseholdMember
from app.models.inventory_item import InventoryItem
from app.models.product import Product
from app.schemas.inventory_item import (
    InventoryItemCreate,
    InventoryItemUpdate,
)
from app.services.auxiliary_functions import ( 
    ProductNotFoundError,
    InventoryNotFoundError,
    get_household_member,
    require_household_access
    )


def get_inventory_item(
    db: Session,
    household_id: int,
    product_id: int,
) -> InventoryItem | None:
    stmt = select(InventoryItem).where(
        InventoryItem.household_id == household_id,
        InventoryItem.product_id == product_id,
    )
    return db.scalar(stmt)


def get_household_inventory(
    db: Session,
    household_id: int,
) -> list[InventoryItem]:
    stmt = (
        select(InventoryItem)
        .where(InventoryItem.household_id == household_id)
        .order_by(InventoryItem.product_id)
    )
    return list(db.scalars(stmt).all())


def create_inventory_item(
    db: Session,
    household_id: int,
    user_id: int,
    item_data: InventoryItemCreate,
) -> InventoryItem:
    require_household_access(db, household_id, user_id)

    product = db.get(Product, item_data.product_id)

    if product is None:
        raise ProductNotFoundError("Product not found")

    existing_item = get_inventory_item(
        db,
        household_id,
        item_data.product_id,
    )

    if existing_item is not None:
        return update_inventory_item(
            db=db,
            household_id=household_id,
            user_id=user_id,
            product_id=item_data.product_id,
            item_data=InventoryItemUpdate(
                quantity=existing_item.quantity + item_data.quantity,
            ),
        )

    item = InventoryItem(
        household_id=household_id,
        product_id=item_data.product_id,
        quantity=item_data.quantity,
    )

    db.add(item)
    db.commit()
    db.refresh(item)

    return item


def update_inventory_item(
    db: Session,
    household_id: int,
    user_id: int,
    product_id: int,
    item_data: InventoryItemUpdate,
) -> InventoryItem:
    require_household_access(db, household_id, user_id)

    item = get_inventory_item(
        db,
        household_id,
        product_id,
    )

    if item is None:
        raise InventoryNotFoundError("Inventory item not found")

    if item_data.quantity is not None:
        item.quantity = item_data.quantity

    db.commit()
    db.refresh(item)

    return item


def delete_inventory_item(
    db: Session,
    household_id: int,
    user_id: int,
    product_id: int,
) -> None:
    require_household_access(db, household_id, user_id)

    item = get_inventory_item(
        db,
        household_id,
        product_id,
    )

    if item is None:
        raise InventoryNotFoundError("Inventory item not found")

    db.delete(item)
    db.commit()
