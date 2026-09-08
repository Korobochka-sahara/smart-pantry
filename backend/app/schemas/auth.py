from pydantic import BaseModel, EmailStr, field_validator
import re

class RegisterRequest(BaseModel):
    email: EmailStr
    username: str
    password: str

    @field_validator('password')
    @classmethod
    def validate_password(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        if not re.search(r'[A-Z]', v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not re.search(r'[a-z]', v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not re.search(r'\d', v):
            raise ValueError('Password must contain at least one digit')
            
        return v

class UserResponse(BaseModel):
    id: int
    email: EmailStr
    username: str

    model_config = {
        "from_attributes": True,
    }

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str

class RefreshTokenRequest(BaseModel):
    refresh_token: str