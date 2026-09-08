from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.schemas.household import HouseholdCreate, HouseholdResponse
from app.services.household_service import (
    create_household,
    get_household,
)

router = APIRouter(prefix = "/household", tags= ["household"])

@router.post(  
    "",
    response_model=HouseholdResponse,
)
def create_household_endpoint(
    household_data: HouseholdCreate,
    db: Session = Depends(get_db),
):
    return create_household(db, household_data)


@router.get(
    "/{household_id}",
    response_model=HouseholdResponse,
)
def get_household_endpoint(
    household_id: int,
    db: Session = Depends(get_db),
):
    household = get_household(db, household_id)

    if household is None:
        raise HTTPException(
            status_code=404,
            detail="Household not found",
        )

    return household