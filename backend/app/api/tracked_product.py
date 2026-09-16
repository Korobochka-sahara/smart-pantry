from fastapi import APIRouter, Depends, HTTPException, Path, status
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models.user import User
from app.schemas.tracked_product import (
    LowStockItemResponse,
    TrackedProductCreate,
    TrackedProductResponse,
    TrackedProductUpdate,
)
from app.security import get_current_user
from app.services.tracked_product_service import (
    create_tracked_product,
    delete_tracked_product,
    get_household_tracked_products,
    get_low_stock_products,
    update_tracked_product,
)
from app.services.auxiliary_functions import (
    ProductNotFoundError,
    TrackedProductConflictError,
    TrackedProductNotFoundError,
    HouseholdPermissionError,
    require_household_access,
)


router = APIRouter(
    prefix="/households/{household_id}/tracked-products",
    tags=["tracked-products"],
)


@router.get(
    "",
    response_model=list[TrackedProductResponse],
)
def get_tracked_products(
    household_id: int = Path(gt=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        require_household_access(
            db,
            household_id,
            current_user.id,
        )

        return get_household_tracked_products(
            db,
            household_id,
        )

    except HouseholdPermissionError as error:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(error),
        )


@router.post(
    "",
    response_model=TrackedProductResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_tracked_product_endpoint(
    data: TrackedProductCreate,
    household_id: int = Path(gt=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        return create_tracked_product(
            db,
            household_id,
            current_user.id,
            data,
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

    except TrackedProductConflictError as error:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(error),
        )


@router.patch(
    "/{product_id}",
    response_model=TrackedProductResponse,
)
def update_tracked_product_endpoint(
    data: TrackedProductUpdate,
    household_id: int = Path(gt=0),
    product_id: int = Path(gt=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        return update_tracked_product(
            db,
            household_id,
            current_user.id,
            product_id,
            data,
        )

    except HouseholdPermissionError as error:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(error),
        )

    except TrackedProductNotFoundError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(error),
        )


@router.delete(
    "/{product_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_tracked_product_endpoint(
    household_id: int = Path(gt=0),
    product_id: int = Path(gt=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        delete_tracked_product(
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

    except TrackedProductNotFoundError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(error),
        )


@router.get(
    "/low-stock",
    response_model=list[LowStockItemResponse],
)
def get_low_stock(
    household_id: int = Path(gt=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        require_household_access(
            db,
            household_id,
            current_user.id,
        )

        items = get_low_stock_products(
            db,
            household_id,
        )

        return [
            LowStockItemResponse(
                household_id=tracked_product.household_id,
                product_id=tracked_product.product_id,
                minimum_quantity=tracked_product.minimum_quantity,
                current_quantity=current_quantity,
            )
            for tracked_product, current_quantity in items
        ]

    except HouseholdPermissionError as error:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(error),
        )