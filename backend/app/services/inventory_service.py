from decimal import Decimal
from sqlalchemy import select, update, func
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from app.models.inventory_item import InventoryItem
from app.models.product import Product
from app.schemas.inventory_item import (
    InventoryItemCreate,
    InventoryItemUpdate,
)
from app.services.auxiliary_functions import ( 
    ProductNotFoundError,
    InventoryNotFoundError,
    InventoryConflictError,
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

    statement = insert(InventoryItem).values(
        household_id=household_id,
        product_id=item_data.product_id,
        quantity=item_data.quantity,
    )
    statement = statement.on_conflict_do_update(
        index_elements=[InventoryItem.household_id, InventoryItem.product_id],
        set_={
            "quantity": InventoryItem.quantity + statement.excluded.quantity,
            "updated_at": func.now(),
        },
        where=InventoryItem.quantity + statement.excluded.quantity <= Decimal("9999999.999"),
    ).returning(InventoryItem)
    item = db.scalar(statement, execution_options={"populate_existing": True})
    if item is None:
        db.rollback()
        raise InventoryConflictError("Quantity exceeds maximum 9999999.999")
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

    if item_data.quantity is None:
        item = get_inventory_item(db, household_id, product_id)
        if item is None:
            raise InventoryNotFoundError("Inventory item not found")
        return item

    conditions = [InventoryItem.household_id == household_id, InventoryItem.product_id == product_id]
    if item_data.expected_quantity is not None:
        conditions.append(InventoryItem.quantity == item_data.expected_quantity)
    item = db.scalar(
        update(InventoryItem).where(*conditions)
        .values(quantity=item_data.quantity, updated_at=func.now()).returning(InventoryItem),
        execution_options={"populate_existing": True},
    )
    if item is None:
        if get_inventory_item(db, household_id, product_id) is None:
            raise InventoryNotFoundError("Inventory item not found")
        raise InventoryConflictError("Stock changed; reload before setting quantity")
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


def change_inventory_quantity(db, household_id, user_id, product_id, delta):
    """Change the current DB value, never a previously read client snapshot."""
    require_household_access(db, household_id, user_id)
    statement = (
        update(InventoryItem)
        .where(
            InventoryItem.household_id == household_id,
            InventoryItem.product_id == product_id,
            InventoryItem.quantity + delta <= Decimal("9999999.999"),
        )
        .values(
            quantity=func.greatest(0, InventoryItem.quantity + delta),
            updated_at=func.now(),
        )
        .returning(InventoryItem)
    )
    item = db.scalar(statement, execution_options={"populate_existing": True})
    if item is None:
        if get_inventory_item(db, household_id, product_id) is not None:
            raise InventoryConflictError("Quantity exceeds maximum 9999999.999")
        raise InventoryNotFoundError("Inventory item not found")
    db.commit()
    db.refresh(item)
    return item
