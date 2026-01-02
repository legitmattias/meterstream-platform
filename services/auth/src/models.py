from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime, UTC


# Request models (vad API:et tar emot)
class UserLogin(BaseModel):
    """ Model for user login posts """
    email: EmailStr
    password: str


# Response models (vad API:et returnerar)
class UserResponse(BaseModel):
    """Model for user data in API responses (register, login, refresh)"""
    id: str
    email: str  # Use str instead of EmailStr to allow test emails like staff@test.local
    name: str
    created_at: datetime
    role: str = "customer"
    customer_id: Optional[str] = None



# TODO: MIGRATE TO API GATEWAY
# This model should be moved to the API Gateway service
class VerifyResponse(BaseModel):
    """Model for JWT token verification response

    NOTE: This model will be migrated to API Gateway in the future
    """
    valid: bool
    user_id: Optional[str] = None
    email: Optional[str] = None
    role: Optional[str] = None
    customer_id: Optional[str] = None


# Database model (hur det sparas i MongoDB)
class UserInDB(BaseModel):
    """Model for user document stored in MongoDB"""
    email: str  # Use str instead of EmailStr to allow test emails like staff@test.local
    hashed_password: str
    name: str
    role: str = "customer"
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


# ============================================================================
# ADMIN USER MANAGEMENT MODELS
# ============================================================================

class AdminUserCreate(BaseModel):
    """Model for admin creating a new user (bypasses normal registration)"""
    email: EmailStr
    password: str = Field(..., min_length=8)
    name: str = Field(..., min_length=2)
    role: str = Field(default="customer", pattern="^(customer|admin|internal|device)$")
    customer_id: Optional[str] = None


class AdminUserUpdate(BaseModel):
    """Model for admin updating user fields (all fields optional)"""
    email: Optional[EmailStr] = None
    password: Optional[str] = Field(None, min_length=8)
    name: Optional[str] = Field(None, min_length=2)
    role: Optional[str] = Field(None, pattern="^(customer|admin|internal|device)$")
    customer_id: Optional[str] = None


class UserListResponse(BaseModel):
    """Model for paginated user list response"""
    users: list[UserResponse]
    total: int
    page: int
    page_size: int

