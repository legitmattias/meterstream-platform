import logging
from fastapi import APIRouter, HTTPException, status, Depends, Request, Header, Response
from datetime import datetime, UTC
from bson import ObjectId
from bson.errors import InvalidId
from slowapi import Limiter
from slowapi.util import get_remote_address
from typing import Optional

from .models import (
    UserRegister,
    UserLogin,
    UserResponse,
    VerifyResponse,
    RefreshTokenRequest,
    TokenPairResponse
)
from .jwt_service import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
    verify_token,
    verify_refresh_token
)
from .mongodb import get_users_collection

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/auth", tags=["Authentication"])

# Rate limiter instance
limiter = Limiter(key_func=get_remote_address)


# ============================================================================
# ENDPOINTS
# ============================================================================


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit("5/minute")  # Max 5 registrations per minute per IP
async def register(request: Request, response: Response, user_data: UserRegister, users=Depends(get_users_collection)):
    """
    Register a new user.

    - Checks if email already exists
    - Hashes password
    - Saves user to MongoDB
    """
    # TODO: SECURITY - Add input validation if we keep email-based authentication
    # Currently relying on Pydantic's EmailStr validation

    # Check if user already exists
    existing_user = await users.find_one({"email": user_data.email})
    if existing_user:
        # Audit log for duplicate registration attempt
        logger.warning(
            "Duplicate registration attempt",
            extra={"email": user_data.email, **get_client_info(request)}
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

    # Create user document
    user_doc = {
        "email": user_data.email,
        "hashed_password": hash_password(user_data.password),
        "name": user_data.name,
        "role": "customer",
        "customer_id": None,
        "created_at": datetime.now(UTC)
    }

    # Insert into database
    try:
        result = await users.insert_one(user_doc)
    except Exception as e:
        logger.error(
            "Database error during registration",
            extra={
                "error": str(e),
                "email": user_data.email
            }
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Registration failed"
        )

    # Audit log for successful registration
    logger.info(
        "User registered successfully",
        extra={
            "email": user_data.email,
            "user_id": str(result.inserted_id),
            **get_client_info(request)
        }
    )

    return UserResponse(
        id=str(result.inserted_id),
        email=user_doc["email"],
        name=user_doc["name"],
        created_at=user_doc["created_at"],
        role=user_doc["role"],
        customer_id=user_doc["customer_id"]
    )


@router.post("/login", response_model=TokenPairResponse)
@limiter.limit("10/minute")  # Max 10 login attempts per minute per IP
async def login(request: Request, response: Response, user_data: UserLogin, users=Depends(get_users_collection)):
    """
    Login and receive JWT token.

    - Verifies email exists
    - Verifies password
    - Returns JWT token

    Security: Uses constant-time comparison to prevent timing attacks
    """
    # Find user
    user = await users.find_one({"email": user_data.email})

    # SECURITY: Always verify password even if user doesn't exist (constant-time operation)
    # This prevents timing attacks that could reveal if an email is registered
    dummy_hash = "$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYFj3YCqqjm"  # Dummy bcrypt hash
    hashed_password = user["hashed_password"] if user else dummy_hash

    # Always run password verification (constant time regardless of user existence)
    password_valid = verify_password(user_data.password, hashed_password)

    # Check both conditions together to prevent timing leaks
    if not user or not password_valid:
        # Audit log for security monitoring
        logger.warning(
            "Failed login attempt",
            extra={
                "email": user_data.email,
                "reason": "invalid_credentials",
                **get_client_info(request)
            }
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )

    # Create tokens
    user_id = str(user["_id"])
    tokens = create_token_pair(
        user_id=user_id,
        email=user["email"],
        role=user.get("role", "customer"),
        customer_id=user.get("customer_id")
    )

    # Audit log for successful login
    logger.info(
        "Successful login",
        extra={
            "email": user_data.email,
            "user_id": user_id,
            **get_client_info(request)
        }
    )

    # Set JWT as HttpOnly cookie
    response.set_cookie(
        key="access_token",
        value=tokens.access_token,
        httponly=True,        # Cannot be read by JavaScript
        secure=False,          # False for HTTP, True for HTTPS
        samesite="lax",       # CSRF protection
        max_age=3600,         # 1 hour (match JWT expiry)
        path="/"
    )

    return tokens


@router.post("/logout")
@limiter.limit("30/minute")
async def logout(request: Request, response: Response):
    """
    Logout user by clearing authentication cookie.

    Returns:
        Success message
    """
    # Clear the access_token cookie
    response.delete_cookie(key="access_token", path="/")

    # Audit log for logout
    logger.info(
        "User logged out",
        extra=get_client_info(request)
    )

    return {"message": "Logged out successfully"}


@router.post("/refresh", response_model=TokenPairResponse)
@limiter.limit("5/hour")  # Max 5 refresh requests per hour per IP (access tokens expire every 60 min)
async def refresh(request: Request, token_data: RefreshTokenRequest, users=Depends(get_users_collection)):
    """
    Get new access token using refresh token.

    TODO: SECURITY - Implement Refresh Token Rotation
    Current: Refresh tokens can be reused unlimited times for 7 days
    Problem: Stolen token = attacker can generate unlimited JWTs for 7 days
    Solution: One-time use refresh tokens
      - Each refresh token can only be used ONCE
      - Returns new access token + NEW refresh token
      - Reuse detection = security alert + revoke all user tokens
      - Requires: MongoDB collection to track used tokens
    Or remove refresh token??
    """
    # Verify refresh token
    user_id = verify_refresh_token(token_data.refresh_token)
    if not user_id:
        logger.warning("Invalid refresh token attempt", extra=get_client_info(request))
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token"
        )

    # Get user with validation
    user = await get_user_by_id(user_id, users, request)

    # Create new tokens
    tokens = create_token_pair(
        user_id=user_id,
        email=user["email"],
        role=user.get("role", "customer"),
        customer_id=user.get("customer_id")
    )

    # Audit log for token refresh
    logger.info(
        "Token refreshed",
        extra={
            "email": user["email"],
            "user_id": user_id,
            **get_client_info(request)
        }
    )

    return tokens

@router.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
@limiter.limit("10/minute")
async def delete_user(
    request: Request,
    user_id: str,
    authorization: Optional[str] = Header(None),
    users=Depends(get_users_collection)
):
    """
    Delete a user by ID. Admin only.
    """
    # Check Authorization header exists
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authorization header",
            headers={"WWW-Authenticate": "Bearer"}
        )

    # Extract token from "Bearer <token>"
    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authorization header format. Expected 'Bearer <token>'",
            headers={"WWW-Authenticate": "Bearer"}
        )

    token = parts[1]

    # Verify token
    payload = verify_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"}
        )

    # Check admin role
    if payload.get("role") != "admin":
        logger.warning(
            "Non-admin attempted to delete user",
            extra={"requester_id": payload.get("user_id"), "target_id": user_id, **get_client_info(request)}
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )

    # Validate user ID format
    if not user_id or len(user_id) != 24 or not all(c in '0123456789abcdefABCDEF' for c in user_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid user ID format"
        )

    # Delete user
    try:
        result = await users.delete_one({"_id": ObjectId(user_id)})
    except InvalidId:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid user ID format"
        )

    if result.deleted_count == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    logger.info(
        "User deleted",
        extra={"deleted_user_id": user_id, "admin_id": payload.get("user_id"), **get_client_info(request)}
    )

    return None


@router.get("/me", response_model=UserResponse)
@limiter.limit("30/minute")  # Max 30 requests per minute per IP
async def me(request: Request, authorization: Optional[str] = Header(None), users=Depends(get_users_collection)):
    """
    Get current user information from JWT token.

    - Extracts JWT from Authorization header OR cookie
    - Verifies token
    - Returns current user data
    """
    token = None

    # Try to get token from Authorization header first
    if authorization:
        # Extract token from "Bearer <token>"
        parts = authorization.split()
        if len(parts) == 2 and parts[0].lower() == "bearer":
            token = parts[1]

    # If no Authorization header, try to get token from cookie
    if not token:
        token = request.cookies.get("access_token")

    # Check if we got a token from either source
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authentication credentials",
            headers={"WWW-Authenticate": "Bearer"}
        )

    # Verify token
    payload = verify_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"}
        )

    # Get user ID from token
    user_id = payload.get("user_id")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload"
        )

    # Get user with validation (DRY - uses helper function)
    user = await get_user_by_id(user_id, users, request)

    # Audit log for successful user info retrieval
    logger.info(
        "User info retrieved",
        extra={
            "email": user["email"],
            "user_id": user_id,
            **get_client_info(request)
        }
    )

    return UserResponse(
        id=str(user["_id"]),
        email=user["email"],
        name=user["name"],
        created_at=user["created_at"],
        role=user.get("role", "customer"),
        customer_id=user.get("customer_id")
    )


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def get_client_info(request: Request) -> dict:
    """Extract client IP and user agent from request for logging."""
    return {
        "ip": request.client.host if request.client else "unknown",
        "user_agent": request.headers.get("user-agent", "unknown")
    }


async def get_user_by_id(user_id: str, users, request: Request) -> dict:
    """
    Get user from database by ID with validation and error handling.

    Validates ObjectId format, handles database errors, and logs security events.
    Returns user document or raises HTTPException.
    """
    # SECURITY: Validate ObjectId format before database query
    # Check if string is 24 hex characters (valid MongoDB ObjectId format)
    if not user_id or len(user_id) != 24 or not all(c in '0123456789abcdefABCDEF' for c in user_id):
        logger.warning(
            "Invalid ObjectId format",
            extra={"user_id": user_id, **get_client_info(request)}
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )

    # Get user from database with exception handling
    try:
        user = await users.find_one({"_id": ObjectId(user_id)})
    except InvalidId:
        logger.warning(
            "Invalid ObjectId",
            extra={"user_id": user_id, **get_client_info(request)}
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )
    except Exception as e:
        logger.error(
            "Database error",
            extra={"error": str(e), "user_id": user_id}
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

    if not user:
        logger.warning(
            "User not found",
            extra={"user_id": user_id, **get_client_info(request)}
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )

    return user


def create_token_pair(user_id: str, email: str, role: str, customer_id: Optional[str]) -> TokenPairResponse:
    """Create access and refresh tokens for a user."""
    access_token, expires_in = create_access_token(
        user_id=user_id,
        email=email,
        role=role,
        customer_id=customer_id
    )
    refresh_token = create_refresh_token(user_id=user_id)

    return TokenPairResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=expires_in
    )
