import logging
from fastapi import APIRouter, HTTPException, status, Depends, Request, Header
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


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit("5/minute")  # Max 5 registrations per minute per IP
async def register(request: Request, user_data: UserRegister, users=Depends(get_users_collection)):
    """
    Register a new user.
    
    - Checks if email already exists
    - Hashes password
    - Saves user to MongoDB
    """
    # Check if user already exists
    existing_user = await users.find_one({"email": user_data.email})
    if existing_user:
        # Audit log for duplicate registration attempt
        logger.warning(
            "Duplicate registration attempt",
            extra={
                "email": user_data.email,
                "ip": request.client.host if request.client else "unknown",
                "user_agent": request.headers.get("user-agent", "unknown")
            }
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
            "ip": request.client.host if request.client else "unknown",
            "user_agent": request.headers.get("user-agent", "unknown")
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
async def login(request: Request, user_data: UserLogin, users=Depends(get_users_collection)):
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
                "ip": request.client.host if request.client else "unknown",
                "user_agent": request.headers.get("user-agent", "unknown"),
                "reason": "invalid_credentials"
            }
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )

    # Create tokens
    access_token, expires_in = create_access_token(
        user_id=str(user["_id"]),
        email=user["email"],
        role=user.get("role", "customer"),
        customer_id=user.get("customer_id")
    )
    refresh_token = create_refresh_token(user_id=str(user["_id"]))

    # Audit log for successful login
    logger.info(
        "Successful login",
        extra={
            "email": user_data.email,
            "user_id": str(user["_id"]),
            "ip": request.client.host if request.client else "unknown",
            "user_agent": request.headers.get("user-agent", "unknown")
        }
    )

    return TokenPairResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=expires_in
    )

@router.post("/refresh", response_model=TokenPairResponse)
@limiter.limit("20/minute")  # Max 20 refresh requests per minute per IP
async def refresh(request: Request, token_data: RefreshTokenRequest, users=Depends(get_users_collection)):
    """
    Get new access token using refresh token.
    """
    # Verify refresh token
    user_id = verify_refresh_token(token_data.refresh_token)
    if not user_id:
        logger.warning(
            "Invalid refresh token attempt",
            extra={
                "ip": request.client.host if request.client else "unknown"
            }
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token"
        )

    # Get user from database with exception handling
    try:
        user = await users.find_one({"_id": ObjectId(user_id)})
    except InvalidId:
        logger.warning(
            "Invalid ObjectId in refresh token",
            extra={
                "user_id": user_id,
                "ip": request.client.host if request.client else "unknown"
            }
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )
    except Exception as e:
        logger.error(
            "Database error in /refresh endpoint",
            extra={
                "error": str(e),
                "user_id": user_id
            }
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

    if not user:
        logger.warning(
            "Refresh token references non-existent user",
            extra={
                "user_id": user_id,
                "ip": request.client.host if request.client else "unknown"
            }
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )

    # Create new tokens
    access_token, expires_in = create_access_token(
        user_id=user_id,
        email=user["email"],
        role=user.get("role", "customer"),
        customer_id=user.get("customer_id")
    )
    refresh_token = create_refresh_token(user_id=user_id)

    # Audit log for token refresh
    logger.info(
        "Token refreshed",
        extra={
            "email": user["email"],
            "user_id": user_id,
            "ip": request.client.host if request.client else "unknown"
        }
    )

    return TokenPairResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=expires_in
    )

@router.get("/me", response_model=UserResponse)
@limiter.limit("30/minute")  # Max 30 requests per minute per IP
async def me(request: Request, authorization: Optional[str] = Header(None), users=Depends(get_users_collection)):
    """
    Get current user information from JWT token.

    - Extracts JWT from Authorization header
    - Verifies token
    - Returns current user data
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

    # Get user from database
    user_id = payload.get("user_id")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload"
        )

    # SECURITY: Specific exception handling to prevent IDOR attacks
    try:
        user = await users.find_one({"_id": ObjectId(user_id)})
    except InvalidId:
        # Invalid ObjectId format - potential attack
        logger.warning(
            "Invalid ObjectId in token",
            extra={
                "user_id": user_id,
                "ip": request.client.host if request.client else "unknown"
            }
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )
    except Exception as e:
        # Unexpected database error
        logger.error(
            "Database error in /me endpoint",
            extra={
                "error": str(e),
                "user_id": user_id
            }
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

    if not user:
        # Valid ObjectId but user doesn't exist (deleted account?)
        logger.warning(
            "Token references non-existent user",
            extra={
                "user_id": user_id,
                "ip": request.client.host if request.client else "unknown"
            }
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )

    # Audit log for successful user info retrieval
    logger.info(
        "User info retrieved",
        extra={
            "email": user["email"],
            "user_id": user_id,
            "ip": request.client.host if request.client else "unknown"
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

# TODO: MIGRATE TO API GATEWAY
# This endpoint should be moved to the API Gateway service
# The API Gateway will be responsible for verifying JWT tokens for all incoming requests
@router.get("/verify", response_model=VerifyResponse)
async def verify(token: str):
    """
    Verify a JWT token.

    - Used by API Gateway to validate requests
    - Returns user info if valid

    NOTE: This endpoint will be migrated to API Gateway in the future
    """
    payload = verify_token(token)

    if not payload:
        logger.warning("Token verification failed - invalid or expired token")
        return VerifyResponse(valid=False)

    # Don't accept refresh tokens for verification
    if payload.get("type") == "refresh":
        return VerifyResponse(valid=False)

    return VerifyResponse(
        valid=True,
        user_id=payload["user_id"],
        email=payload["email"],
        role=payload["role"],
        customer_id=payload.get("customer_id")
    )
