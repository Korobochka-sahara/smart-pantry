from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models.user import User
from app.schemas.auth import (
    LoginRequest,
    RefreshTokenRequest,
    RegisterRequest,
    TokenResponse,
    UserResponse,
)
from app.security import (
    create_access_token,
    create_refresh_token,
    decode_refresh_token,
    get_current_user,
)
from app.services.auth_service import (
    authenticate_user,
    register_user,
    revoke_refresh_token,
    save_refresh_token,
)


router = APIRouter(
    prefix="/auth",
    tags=["auth"],
)


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
)
def register(
    user_data: RegisterRequest,
    db: Session = Depends(get_db),
):
    try:
        return register_user(db, user_data)

    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(error),
        )


@router.post(
    "/login",
    response_model=TokenResponse,
)
def login(
    login_data: LoginRequest,
    db: Session = Depends(get_db),
):
    user = authenticate_user(
        db,
        login_data.email,
        login_data.password,
    )

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    access_token = create_access_token(user.id)
    refresh_token = create_refresh_token(user.id)

    refresh_token_record = save_refresh_token(
    db,
    user.id,
    refresh_token,
    )

    db.commit()
    db.refresh(refresh_token_record)

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
    )


@router.post(
    "/refresh",
    response_model=TokenResponse,
)
def refresh(
    refresh_data: RefreshTokenRequest,
    db: Session = Depends(get_db),
):
    user_id = decode_refresh_token(
        refresh_data.refresh_token,
        db,
    )

    user = db.get(User, user_id)

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )

    # Старый refresh token больше нельзя использовать
    revoke_refresh_token(
        db,
        refresh_data.refresh_token,
    )

    # Создаём новую пару токенов
    access_token = create_access_token(user.id)
    refresh_token = create_refresh_token(user.id)

    save_refresh_token(
        db,
        user.id,
        refresh_token,
    )

    db.commit()

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
    )


@router.post(
    "/logout",
    status_code=status.HTTP_204_NO_CONTENT,
)
def logout(
    refresh_data: RefreshTokenRequest,
    db: Session = Depends(get_db),
):
    revoke_refresh_token(
        db,
        refresh_data.refresh_token,
    )

    db.commit()


@router.get(
    "/me",
    response_model=UserResponse,
)
def get_me(
    current_user: User = Depends(get_current_user),
):
    return current_user