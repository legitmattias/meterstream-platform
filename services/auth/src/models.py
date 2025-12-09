from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime, UTC


# Request models (vad API:et tar emot)
class UserRegister(BaseModel):
    """ Model for user registration posts """
    email: EmailStr
    password: str = Field(..., min_length=8)
    name: str = Field(..., min_length=2)


class UserLogin(BaseModel):
    """ Model for user login posts """
    email: EmailStr
    password: str


# Response models (vad API:et returnerar)
class UserResponse(BaseModel):
    """Model for user data in API responses (register, login, refresh)"""
    id: str
    email: EmailStr
    name: str
    created_at: datetime
    role: str = "user"
    customer_id: Optional[str] = None



class VerifyResponse(BaseModel):
    """Model for JWT token verification response"""
    valid: bool
    user_id: Optional[str] = None
    email: Optional[str] = None
    role: Optional[str] = None
    customer_id: Optional[str] = None


# Database model (hur det sparas i MongoDB)
class UserInDB(BaseModel):
    """Model for user document stored in MongoDB"""
    email: EmailStr
    hashed_password: str
    name: str
    role: str = "user"
    customer_id: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

# Refresh token models
class RefreshTokenRequest(BaseModel):
    """Model for refresh token request body"""
    refresh_token: str


class TokenPairResponse(BaseModel):
    """Model for login/refresh response with access + refresh tokens"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int

class HealthResponse(BaseModel):
    """Model for health check endpoint response"""
    status: str = "ok"
    service: str = "auth"



# class TokenResponse(BaseModel):
#     """Model for single access token response (deprecated - use TokenPairResponse)"""
#     access_token: str
#     token_type: str = "bearer"
#     expires_in: int