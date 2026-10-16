from sqlalchemy.orm import Session
from fastapi import APIRouter, Depends, HTTPException, Path, Query

from app.db.database import get_db
from app.schemas.product import ProductCreate, ProductResponse
from app.services.product_service import (
    create_product,
    get_product,
)
from app.services.product_matching import search_catalog_products
from app.services.auxiliary_functions import ProductConflictError

from app.enums.category import ProductCategory

router = APIRouter(
    prefix="/products",
    tags=["products"],
)


@router.get(
    "/search",
    response_model=list[ProductResponse],
)
def search(
    q: str = Query(
        min_length=1,
        max_length=255,
    ),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
):
    return search_catalog_products(
        db=db,
        query=q,
        limit=limit,
        offset=offset,
    )


@router.post(
    "",
    response_model=ProductResponse,
    status_code=201,
)
def create(
    product_data: ProductCreate,
    db: Session = Depends(get_db),
):
    try:
        return create_product(db, product_data)

    except ProductConflictError:
        raise HTTPException(
            status_code=409,
            detail="Product with this barcode already exists",
        )


@router.get(
    "/{product_id}",
    response_model=ProductResponse,
)
def get(
    product_id: int = Path(gt=0),
    db: Session = Depends(get_db),
):
    product = get_product(db, product_id)

    if product is None:
        raise HTTPException(
            status_code=404,
            detail="Product not found",
        )

    return product