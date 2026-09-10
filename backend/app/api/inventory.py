from sqlalchemy.orm import Session
from fastapi import APIRouter, Depends, HTTPException, Path, Response

from app.db.database import get_db
from app.schemas.inventory_item import InventoryItemCreate, InventoryItemResponse, InventoryItemUpdate
from app.services.inventory_service import (
    InventoryNotFoundError,
    InventoryPermissionError,
    InventoryValidationError,
    create_inventory_item,
    get_household_inventory,
    get_inventory_item,
    require_household_access,
    update_inventory_item,
)

from app.security import get_current_user
from app.models.user import User


router = APIRouter(
    prefix="/households/{household_id}/inventory",
    tags=["inventory"],
)


@router.get("", response_model=list[InventoryItemResponse])
def get_inventory(
    household_id: int = Path(gt=0),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    try:
        require_household_access(
            db,
            household_id,
            current_user.id,
        )

        return get_household_inventory(
            db,
            household_id,
        )

    except InventoryPermissionError:
        raise HTTPException(
            status_code=403,
            detail="User is not a member of this household",
        )


@router.get(
    "/{inventory_item_id}",
    response_model=InventoryItemResponse,
)
def get_inventory_item_by_id(
    household_id: int = Path(gt=0),
    inventory_item_id: int = Path(gt=0),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    try:
        require_household_access(
            db,
            household_id,
            current_user.id,
        )

        item = get_inventory_item(
            db,
            household_id,
            inventory_item_id,
        )

        if item is None:
            raise InventoryNotFoundError(
                "Inventory item not found"
            )

        return item

    except InventoryPermissionError:
        raise HTTPException(
            status_code=403,
            detail="User is not a member of this household",
        )

    except InventoryNotFoundError:
        raise HTTPException(
            status_code=404,
            detail="Inventory item not found",
        )

@router.post(
    "",
    response_model=InventoryItemResponse,
    status_code=201,
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

    except InventoryPermissionError as error:
        raise HTTPException(
            status_code=403,
            detail=str(error),
        )

    except InventoryNotFoundError as error:
        raise HTTPException(
            status_code=404,
            detail=str(error),
        )


@router.patch(
    "/{inventory_item_id}",
    response_model=InventoryItemResponse,
)
def update_inventory_item_endpoint(
    item_data: InventoryItemUpdate,
    household_id: int = Path(gt=0),
    inventory_item_id: int = Path(gt=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        item = update_inventory_item(
            db,
            household_id,
            current_user.id,
            inventory_item_id,
            item_data,
        )

        if item is None:
            return Response(status_code=204)

        return item

    except InventoryPermissionError as error:
        raise HTTPException(
            status_code=403,
            detail=str(error),
        )

    except InventoryNotFoundError as error:
        raise HTTPException(
            status_code=404,
            detail=str(error),
        )

    except InventoryValidationError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error),
        )