from sqlalchemy.orm import Session

from app.models.household import Household
from app.schemas.household import HouseholdCreate


def create_household(db: Session, household_data: HouseholdCreate,) -> Household:
    household = Household(
        name=household_data.name,
    )

    db.add(household)
    db.commit()
    db.refresh(household)

    return household


def get_household(
    db: Session,
    household_id: int,
) -> Household | None:
    return db.get(Household, household_id)