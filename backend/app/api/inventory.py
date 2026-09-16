from fastapi import APIRouter, Depends, HTTPException, Path, status
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models.user import User
from app.schemas.inventory_item import (
    InventoryItemCreate,
    InventoryItemResponse,
    InventoryItemUpdate,
)
from app.security import get_current_user
from app.services.inventory_service import (
    create_inventory_item,
    delete_inventory_item,
    get_household_inventory,
    get_inventory_item,
    update_inventory_item,
)
from app.services.auxiliary_functions import (
    HouseholdPermissionError,
    InventoryNotFoundError,
    ProductNotFoundError,
    require_household_access,
)


router = APIRouter(
    prefix="/households/{household_id}/inventory",
    tags=["inventory"],
)


@router.get(
    "",
    response_model=list[InventoryItemResponse],
)
def get_inventory(
    household_id: int = Path(gt=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        require_household_access(db, household_id, current_user.id)
        return get_household_inventory(db, household_id)

    except HouseholdPermissionError as error:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(error),
        )


@router.get(
    "/{product_id}",
    response_model=InventoryItemResponse,
)
def get_inventory_item_endpoint(
    household_id: int = Path(gt=0),
    product_id: int = Path(gt=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        require_household_access(db, household_id, current_user.id)

        item = get_inventory_item(
            db,
            household_id,
            product_id,
        )

        if item is None:
            raise InventoryNotFoundError("Inventory item not found")

        return item

    except HouseholdPermissionError as error:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(error),
        )

    except InventoryNotFoundError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(error),
        )


@router.post(
    "",
    response_model=InventoryItemResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_inventory_item_endpoint(
    item_data: InventoryItemCreate,
    household_id: int = Path(gt=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        return create_inventory_item(
            db,
            household_id,
            current_user.id,
            item_data,
        )

    except HouseholdPermissionError as error:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(error),
        )

    except ProductNotFoundError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(error),
        )


@router.patch(
    "/{product_id}",
    response_model=InventoryItemResponse,
)
def update_inventory_item_endpoint(
    item_data: InventoryItemUpdate,
    household_id: int = Path(gt=0),
    product_id: int = Path(gt=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        return update_inventory_item(
            db,
            household_id,
            current_user.id,
            product_id,
            item_data,
        )

    except HouseholdPermissionError as error:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(error),
        )

    except InventoryNotFoundError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(error),
        )


@router.delete(
    "/{product_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_inventory_item_endpoint(
    household_id: int = Path(gt=0),
    product_id: int = Path(gt=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        delete_inventory_item(
            db,
            household_id,
            current_user.id,
            product_id,
        )

    except HouseholdPermissionError as error:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(error),
        )

    except InventoryNotFoundError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(error),
        )
