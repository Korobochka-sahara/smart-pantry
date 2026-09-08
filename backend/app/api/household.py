from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.schemas.household import HouseholdCreate, HouseholdMemberAdd, HouseholdMemberResponse, HouseholdResponse, HouseholdRoleUpdate
from app.services.household_service import (
    HouseholdConflictError,
    HouseholdNotFoundError,
    HouseholdPermissionError,
    add_household_member,
    create_household,
    get_household_members,
    get_user_households,
    get_household_for_user,
    leave_household,
    remove_household_member,
    update_household_member_role
)
from app.security import get_current_user
from app.models.user import User

router = APIRouter(prefix = "/households", tags= ["households"])

@router.post(
    "",
    response_model=HouseholdResponse,
    status_code=201,
)
def create_household_endpoint(
    household_data: HouseholdCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        return create_household(
            db,
            household_data,
            current_user.id,
        )

    except ValueError as error:
        raise HTTPException(
            status_code=409,
            detail=str(error),
        )


@router.get(
    "",
    response_model=list[HouseholdResponse],
)
def get_my_households(
    db: Session = Depends(get_db),
    currnet_user: User = Depends(get_current_user)
):
    return get_user_households(
        db,
        currnet_user.id
    )

@router.get(
    "/{household_id}",
    response_model=HouseholdResponse
)
def get_household_endpoint(
    household_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    household = get_household_for_user(
        db,
        household_id,
        current_user.id
    )

    if household is None:
        raise HTTPException(
            status_code=404,
            detail="Household not found"
        )
    
    return household

@router.get(
    "/{household_id}/members",
    response_model=list[HouseholdMemberResponse],
)
def get_members(
    household_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        return get_household_members(
            db,
            household_id,
            current_user.id,
        )
    except ValueError as error:
        raise HTTPException(
            status_code=404,
            detail=str(error),
        )

@router.post(
    "/{household_id}/members",
    response_model=HouseholdMemberResponse,
    status_code=201,
)
def add_member(
    household_id: int,
    member_data: HouseholdMemberAdd,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        return add_household_member(
            db,
            household_id,
            current_user.id,
            member_data,
        )

    except HouseholdNotFoundError as error:
        raise HTTPException(
            status_code=404,
            detail=str(error),
        )

    except HouseholdPermissionError as error:
        raise HTTPException(
            status_code=403,
            detail=str(error),
        )

    except HouseholdConflictError as error:
        raise HTTPException(
            status_code=409,
            detail=str(error),
        )

@router.patch(
    "/{household_id}/members/{target_user_id}/role",
    response_model=HouseholdMemberResponse,
)
def update_member_role(
    household_id: int,
    target_user_id: int,
    role_data: HouseholdRoleUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        return update_household_member_role(
            db,
            household_id,
            current_user.id,
            target_user_id,
            role_data.role,
        )

    except HouseholdNotFoundError as error:
        raise HTTPException(
            status_code=404,
            detail=str(error),
        )

    except HouseholdPermissionError as error:
        raise HTTPException(
            status_code=403,
            detail=str(error),
        )

    except HouseholdConflictError as error:
        raise HTTPException(
            status_code=409,
            detail=str(error),
        )

@router.delete(
    "/{household_id}/members/{target_user_id}",
    status_code=204,
)
def remove_member(
    household_id: int,
    target_user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        remove_household_member(
            db,
            household_id,
            current_user.id,
            target_user_id,
        )

    except HouseholdNotFoundError as error:
        raise HTTPException(
            status_code=404,
            detail=str(error),
        )

    except HouseholdPermissionError as error:
        raise HTTPException(
            status_code=403,
            detail=str(error),
        )

    except HouseholdConflictError as error:
        raise HTTPException(
            status_code=409,
            detail=str(error),
        )

@router.post(
    "/{household_id}/leave",
    status_code=204,
)
def leave(
    household_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        leave_household(
            db,
            household_id,
            current_user.id,
        )

    except HouseholdNotFoundError as error:
        raise HTTPException(
            status_code=404,
            detail=str(error),
        )

    except HouseholdConflictError as error:
        raise HTTPException(
            status_code=409,
            detail=str(error),
        )