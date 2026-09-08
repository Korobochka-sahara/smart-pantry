from datetime import datetime, timedelta, timezone
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
import hashlib
from dotenv import load_dotenv

import os
import jwt
from jwt.exceptions import InvalidTokenError

from app.db.database import get_db
from app.models.user import User

from app.models.refresh_token import RefreshToken

load_dotenv()
SECRET_KEY = os.getenv("SECRET_KEY")
if not SECRET_KEY:
    raise RuntimeError("SECRET_KEY is not set")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60
REFRESH_TOKEN_EXPIRE_DAYS = 30
bearer_scheme = HTTPBearer()

def create_access_token(user_id: int) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes = ACCESS_TOKEN_EXPIRE_MINUTES)

    payload = {
        "sub": str(user_id),
        "exp": expire
    }

    return jwt.encode(
        payload,
        SECRET_KEY,
        algorithm = ALGORITHM
    )


def create_refresh_token(user_id: int) -> str:
    expire = datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)

    payload = {
        "sub": str(user_id),
        "exp": expire,
        "type": "refresh"
    }

    return jwt.encode(
        payload,
        SECRET_KEY,
        algorithm=ALGORITHM
    )

def decode_refresh_token(token: str, db: Session) -> int:
    try:
        payload = jwt.decode(
            token,
            SECRET_KEY,
            algorithms=[ALGORITHM]
        )

        # Проверка на то что это рефреш
        if payload.get("type") != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token",
            )

        user_id = payload.get("sub")

        # Проверка на существование юзера
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token",
            )

        # Проверка существования токена в БД
        token_hash = hashlib.sha256(token.encode()).hexdigest()
        refresh_token_record = db.query(RefreshToken).filter(
            RefreshToken.token_hash == token_hash
        ).first()

        if refresh_token_record is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Refresh token not found",
            )

        # Проверка срока действия
        if refresh_token_record.expires_at < datetime.now(timezone.utc):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Refresh token expired",
            )

        # Проверка отзыва токена
        if refresh_token_record.revoked_at is not None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Refresh token has been revoked",
            )

        return int(user_id)
    
    except (InvalidTokenError, ValueError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
        )


def get_current_user(
        credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
        db: Session = Depends(get_db)
        ) -> User:
    token = credentials.credentials

    try:
        payload = jwt.decode(
            token,
            SECRET_KEY,
            algorithms=[ALGORITHM]
        )

        user_id = payload.get("sub")

        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token",
            )

    except InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
        )

    user = db.get(User, int(user_id))

    if user is None:
        raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="User not found",
                )
    
    return user