from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime


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


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int


class VerifyResponse(BaseModel):
    valid: bool
    user_id: Optional[str] = None
    email: Optional[str] = None
    role: Optional[str] = None


# Database model (hur det sparas i MongoDB)
class UserInDB(BaseModel):
    email: EmailStr
    hashed_password: str
    name: str
    role: str = "user"
    created_at: datetime = Field(default_factory=datetime.utcnow)
