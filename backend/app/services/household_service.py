from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.enums.household import HouseholdRole
from app.models.household import Household
from app.models.household_member import HouseholdMember
from app.models.user import User
from app.schemas.household import HouseholdCreate, HouseholdMemberAdd


MAX_CREATED_HOUSEHOLDS = 5
MAX_HOUSEHOLD_MEMBERS = 20

# ошибки
class HouseholdNotFoundError(Exception):
    pass

class HouseholdPermissionError(Exception):
    pass

class HouseholdConflictError(Exception):
    pass


# вспомогательные функции
def get_household_member(
    db: Session,
    household_id: int,
    user_id: int,
) -> HouseholdMember:

    member = db.scalar(
        select(HouseholdMember).where(
            HouseholdMember.household_id == household_id,
            HouseholdMember.user_id == user_id,
        )
    )

    if member is None:
        raise HouseholdNotFoundError(
            "Household not found"
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

    member = db.scalar(
        select(HouseholdMember).where(
            HouseholdMember.household_id == household_id,
            HouseholdMember.user_id == target_user_id,
        )
    )

    if member is None:
        raise HouseholdNotFoundError(
            "Member not found"
        )

    return member

def create_household(
    db: Session,
    household_data: HouseholdCreate,
    user_id: int,
) -> Household:

    created_count = db.scalar(
        select(func.count())
        .select_from(HouseholdMember)
        .where(
            HouseholdMember.user_id == user_id,
            HouseholdMember.role == HouseholdRole.OWNER,
        )
    )

    if created_count >= MAX_CREATED_HOUSEHOLDS:
        raise HouseholdConflictError(
            "You can create a maximum of 5 households"
        )

    household = Household(
        name=household_data.name,
    )

    db.add(household)
    db.flush()

    member = HouseholdMember(
        household_id=household.id,
        user_id=user_id,
        role=HouseholdRole.OWNER,
    )

    db.add(member)

    db.commit()
    db.refresh(household)

    return household

def get_user_households(
    db: Session,
    user_id: int,
) -> list[Household]:

    stmt = (
        select(Household)
        .join(
            HouseholdMember,
            HouseholdMember.household_id == Household.id,
        )
        .where(
            HouseholdMember.user_id == user_id,
        )
        .order_by(Household.id)
    )

    return list(db.scalars(stmt).all())

def get_household_for_user(
    db: Session,
    household_id: int,
    user_id: int,
) -> Household | None:

    stmt = (
        select(Household)
        .join(
            HouseholdMember,
            HouseholdMember.household_id == Household.id,
        )
        .where(
            Household.id == household_id,
            HouseholdMember.user_id == user_id,
        )
    )

    return db.scalar(stmt)

def get_household_members(
    db: Session,
    household_id: int,
    user_id: int,
) -> list[HouseholdMember]:

    get_household_member(
        db,
        household_id,
        user_id,
    )

    stmt = (
        select(HouseholdMember)
        .where(
            HouseholdMember.household_id == household_id,
        )
        .order_by(HouseholdMember.joined_at)
    )

    return list(db.scalars(stmt).all())

def add_household_member(
    db: Session,
    household_id: int,
    current_user_id: int,
    member_data: HouseholdMemberAdd,
) -> HouseholdMember:
    
    current_member = get_household_member(
        db,
        household_id,
        current_user_id,
    )

    require_household_role(
        current_member,
        HouseholdRole.OWNER,
        HouseholdRole.ADMIN,
    )

    members_count = db.scalar(
        select(func.count())
        .select_from(HouseholdMember)
        .where(
            HouseholdMember.household_id == household_id,
        )
    )

    if members_count >= MAX_HOUSEHOLD_MEMBERS:
        raise HouseholdConflictError(
            "Household can have a maximum of 20 members"
        )

    user = db.scalar(
        select(User).where(
            User.username == member_data.username,
        )
    )

    if user is None:
        raise HouseholdNotFoundError("User not found")

    existing_member = db.scalar(
        select(HouseholdMember).where(
            HouseholdMember.household_id == household_id,
            HouseholdMember.user_id == user.id,
        )
    )

    if existing_member is not None:
        raise HouseholdConflictError(
            "User is already a member of this household"
        )

    member = HouseholdMember(
        household_id=household_id,
        user_id=user.id,
        role=HouseholdRole.MEMBER,
    )

    db.add(member)
    db.commit()
    db.refresh(member)

    return member

def update_household_member_role(
    db: Session,
    household_id: int,
    current_user_id: int,
    target_user_id: int,
    new_role: HouseholdRole,
) -> HouseholdMember:

    current_member = get_household_member(
        db,
        household_id,
        current_user_id,
    )

    require_household_role(
        current_member,
        HouseholdRole.OWNER,
        HouseholdRole.ADMIN,
    )

    target_member = get_target_member(
        db,
        household_id,
        target_user_id,
    )

    if new_role == HouseholdRole.OWNER:
        raise HouseholdConflictError(
            "Owner role cannot be assigned this way"
        )

    if target_member.role == HouseholdRole.OWNER:
        raise HouseholdPermissionError(
            "Owner role cannot be changed this way"
        )

    if (
        current_member.role == HouseholdRole.ADMIN
        and target_member.role != HouseholdRole.MEMBER
    ):
        raise HouseholdPermissionError(
            "Admin can only change roles of members"
        )

    target_member.role = new_role

    db.commit()
    db.refresh(target_member)

    return target_member

def remove_household_member(
    db: Session,
    household_id: int,
    current_user_id: int,
    target_user_id: int,
) -> None:

    current_member = get_household_member(
        db,
        household_id,
        current_user_id,
    )

    require_household_role(
        current_member,
        HouseholdRole.OWNER,
        HouseholdRole.ADMIN,
    )

    target_member = get_target_member(
        db,
        household_id,
        target_user_id,
    )

    if current_user_id == target_user_id:
        raise HouseholdConflictError(
            "You cannot remove yourself from the household"
        )

    if target_member.role == HouseholdRole.OWNER:
        raise HouseholdPermissionError(
            "Owner cannot be removed"
        )

    if (
        current_member.role == HouseholdRole.ADMIN
        and target_member.role == HouseholdRole.ADMIN
    ):
        raise HouseholdPermissionError(
            "Admin cannot remove another admin"
        )

    db.delete(target_member)
    db.commit()

def leave_household(
    db: Session,
    household_id: int,
    user_id: int,
) -> None:

    current_member = get_household_member(
        db,
        household_id,
        user_id,
    )

    # Обычный мембер или админ просто выходит
    if current_member.role != HouseholdRole.OWNER:
        db.delete(current_member)
        db.commit()
        return

    # хозяин выходит, ищем других участников исключая текущего хозяина
    other_members_stmt = (
        select(HouseholdMember)
        .join(User, User.id == HouseholdMember.user_id)
        .where(
            HouseholdMember.household_id == household_id,
            HouseholdMember.user_id != user_id,
        )
        .order_by(User.username)
    )

    other_members = list(
        db.scalars(other_members_stmt).all()
    )

    if not other_members:
        household = db.get(Household, household_id)

        db.delete(current_member)
        db.delete(household)

        db.commit()
        return

    new_owner = next(
        (
            member
            for member in other_members
            if member.role == HouseholdRole.ADMIN
        ),
        None,
    )

    # если админа нет берём первого мембера
    if new_owner is None:
        new_owner = next(
            (
                member
                for member in other_members
                if member.role == HouseholdRole.MEMBER
            ),
            None,
        )

    # новый владелец обязан существовать тк other_members не пуст
    if new_owner is None:
        raise HouseholdConflictError(
            "Cannot determine new household owner"
        )

    new_owner.role = HouseholdRole.OWNER

    db.delete(current_member)

    db.commit()