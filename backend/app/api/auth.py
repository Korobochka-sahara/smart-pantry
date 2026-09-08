from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.database import get_db
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
    save_refresh_token,
)

from app.models.user import User

router = APIRouter(prefix = "/auth", tags= ["auth"])

@router.post(
    "/register",
    response_model = UserResponse
)
def register(
    user_data: RegisterRequest,
    db: Session = Depends(get_db)
):
    try:
        return register_user(db,user_data)
    except ValueError as error:
        raise HTTPException(
            status_code = 400,
            detail = str(error)
        )

@router.post("/login", response_model = TokenResponse)
def login(
    login_data: LoginRequest,
    db: Session = Depends(get_db)
):
    user = authenticate_user(db, login_data.email, login_data.password)

    if user is None:
        raise HTTPException(status_code=401, detail="Invalid email or password")

    access_token = create_access_token(user.id)
    refresh_token = create_refresh_token(user.id)

    save_refresh_token(db, user.id, refresh_token)

    return{
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer"
    }

@router.post("/refresh", response_model = TokenResponse)
def refresh(
    refresh_data: RefreshTokenRequest,
    db: Session = Depends(get_db)
):
    user_id = decode_refresh_token(refresh_data.refresh_token)
    user = db.get(User, user_id)

    if user is None:
        raise HTTPException(
            status_code=401, 
            detail="User not found")

    access_token = create_access_token(user.id)
    refresh_token = create_refresh_token(user.id)

    return{
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer"
    }



#test
@router.get(
    "/me",
    response_model=UserResponse,
)
def get_me(
    current_user: User = Depends(get_current_user),
):
    return current_user