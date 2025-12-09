import logging
from fastapi import APIRouter, HTTPException, status, Depends
from datetime import datetime, UTC
from bson import ObjectId

from .models import (
    UserRegister,
    UserLogin,
    UserResponse,
    TokenResponse,
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


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(user_data: UserRegister, users=Depends(get_users_collection)):
    """
    Register a new user.
    
    - Checks if email already exists
    - Hashes password
    - Saves user to MongoDB
    """
    # Check if user already exists
    existing_user = await users.find_one({"email": user_data.email})
    if existing_user:
        logger.error("Email already registered")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create user document
    user_doc = {
        "email": user_data.email,
        "hashed_password": hash_password(user_data.password),
        "name": user_data.name,
        "role": "user",
        "customer_id": None,
        "created_at": datetime.now(UTC)
    }
    
    # Insert into database
    result = await users.insert_one(user_doc)
    logger.info("User registered: %s", user_data.email)

    return UserResponse(
        id=str(result.inserted_id),
        email=user_doc["email"],
        name=user_doc["name"],
        created_at=user_doc["created_at"],
        role=user_doc["role"],
        customer_id=user_doc["customer_id"]
    )


@router.post("/login", response_model=TokenPairResponse)
async def login(user_data: UserLogin, users=Depends(get_users_collection)):
    """
    Login and receive JWT token.
    
    - Verifies email exists
    - Verifies password
    - Returns JWT token
    """
    # Find user
    user = await users.find_one({"email": user_data.email})
    if not user:
        logger.warning("Failed login attempt - user not found: %s", user_data.email)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )

    # Verify password
    if not verify_password(user_data.password, user["hashed_password"]):
        logger.warning("Failed login attempt - invalid password: %s", user_data.email)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    
    # Create token
    access_token, expires_in = create_access_token(
        user_id=str(user["_id"]),
        email=user["email"],
        role=user.get("role", "user"),
        customer_id=user.get("customer_id")
    )
    refresh_token = create_refresh_token(user_id=str(user["_id"]))

    logger.info("User logged in: %s", user_data.email)

    return TokenPairResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=expires_in
    )

@router.post("/refresh", response_model=TokenPairResponse)
async def refresh(token_data: RefreshTokenRequest, users=Depends(get_users_collection)):
    """
    Get new access token using refresh token.
    """
    # Verify refresh token
    user_id = verify_refresh_token(token_data.refresh_token)
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token"
        )
    
    # Get user from database
    user = await users.find_one({"_id": ObjectId(user_id)})
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )
    
    # Create new tokens
    access_token, expires_in = create_access_token(
        user_id=user_id,
        email=user["email"],
        role=user.get("role", "user"),
        customer_id=user.get("customer_id")
    )
    refresh_token = create_refresh_token(user_id=user_id)
    
    return TokenPairResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=expires_in
    )


@router.get("/verify", response_model=VerifyResponse)
async def verify(token: str):
    """
    Verify a JWT token.
    
    - Used by API Gateway to validate requests
    - Returns user info if valid
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


@router.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy", "service": "auth"}
