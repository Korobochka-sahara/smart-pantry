from sqlalchemy import select

from pwdlib import PasswordHash
from sqlalchemy.orm import Session

from app.models.user import User
from app.schemas.auth import RegisterRequest

from datetime import datetime, timedelta, timezone
import hashlib

from app.models.refresh_token import RefreshToken
from app.security import REFRESH_TOKEN_EXPIRE_DAYS, create_refresh_token

password_hash = PasswordHash.recommended()


def register_user( db: Session, user_data: RegisterRequest) -> User:
    existing_email = db.scalar(select(User).where(User.email == user_data.email))

    if existing_email is not None:
        raise ValueError("Email already registered")

    existing_username = db.scalar(select(User).where(User.username == user_data.username))

    if existing_username is not None:
        raise ValueError("Username already taken")

    hashed_password = password_hash.hash(user_data.password)

    user = User(email=user_data.email, username = user_data.username, password_hash = hashed_password)

    db.add(user)
    db.commit()
    db.refresh(user)

    return user

def authenticate_user(db: Session, email: str, password: str) -> User | None:
    user = db.scalar(select(User).where(User.email == email))

    if user is None:
        return None
    
    if  not password_hash.verify(password, user.password_hash):
        return None

    return user

def save_refresh_token(
    db: Session,
    user_id: int,
    refresh_token: str,
) -> RefreshToken:
    token_hash = hashlib.sha256(
        refresh_token.encode()
    ).hexdigest()

    refresh_token_record = RefreshToken(
        user_id=user_id,
        token_hash=token_hash,
        expires_at=(
            datetime.now(timezone.utc)
            + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
        ),
        created_at=datetime.now(timezone.utc),
    )

    db.add(refresh_token_record)

    return refresh_token_record


def revoke_refresh_token(
    db: Session,
    refresh_token: str,
) -> None:
    token_hash = hashlib.sha256(
        refresh_token.encode()
    ).hexdigest()

    refresh_token_record = db.scalar(
        select(RefreshToken).where(
            RefreshToken.token_hash == token_hash
        )
    )

    if (
        refresh_token_record is not None
        and refresh_token_record.revoked_at is None
    ):
        refresh_token_record.revoked_at = datetime.now(timezone.utc)