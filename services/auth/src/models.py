from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime, UTC


# Request models (vad API:et tar emot)
class UserRegister(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8)
    name: str = Field(..., min_length=2)


class UserLogin(BaseModel):
    email: EmailStr
    password: str


# Response models (vad API:et returnerar)
class UserResponse(BaseModel):
    id: str
    email: EmailStr
    name: str
    created_at: datetime
    role: str = "user"
    customer_id: Optional[str] = None


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int


class VerifyResponse(BaseModel):
    valid: bool
    user_id: Optional[str] = None
    email: Optional[str] = None
    role: Optional[str] = None
    customer_id: Optional[str] = None


# Database model (hur det sparas i MongoDB)
class UserInDB(BaseModel):
    email: EmailStr
    hashed_password: str
    name: str
    role: str = "user"
    customer_id: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

# Refresh token models
class RefreshTokenRequest(BaseModel):
    refresh_token: str


class TokenPairResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int