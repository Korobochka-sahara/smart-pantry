from sqlalchemy import select
from sqlalchemy.orm import Session

from app.enums.household import HouseholdRole
from app.models.household_member import HouseholdMember


# Ошибки

class ProductConflictError(Exception):
    pass


class HouseholdNotFoundError(Exception):
    pass


class HouseholdMemberNotFoundError(Exception):
    pass


class HouseholdPermissionError(Exception):
    pass


class HouseholdConflictError(Exception):
    pass


class TrackedProductNotFoundError(Exception):
    pass


class TrackedProductConflictError(Exception):
    pass


class ProductNotFoundError(Exception):
    pass


class InventoryNotFoundError(Exception):
    pass


# Вспомогательные функции

def get_household_member(
    db: Session,
    household_id: int,
    user_id: int,
) -> HouseholdMember | None:
    stmt = select(HouseholdMember).where(
        HouseholdMember.household_id == household_id,
        HouseholdMember.user_id == user_id,
    )

    return db.scalar(stmt)


def require_household_access(
    db: Session,
    household_id: int,
    user_id: int,
) -> HouseholdMember:
    member = get_household_member(
        db,
        household_id,
        user_id,
    )

    if member is None:
        raise HouseholdPermissionError(
            "User is not a member of this household"
        )

    return member


def require_household_role(
    member: HouseholdMember,
    *allowed_roles: HouseholdRole,
) -> None:
    if member.role not in allowed_roles:
        raise HouseholdPermissionError(
            "You do not have permission to perform this action"
        )


def get_target_member(
    db: Session,
    household_id: int,
    target_user_id: int,
) -> HouseholdMember:
    member = get_household_member(
        db,
        household_id,
        target_user_id,
    )

    if member is None:
        raise HouseholdMemberNotFoundError(
            "Member not found"
        )

    return member