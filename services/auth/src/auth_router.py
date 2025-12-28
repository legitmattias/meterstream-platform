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
    TokenPairResponse,
    AdminUserCreate,
    AdminUserUpdate,
    UserListResponse
)
from .jwt_service import (
    hash_password,
    verify_password,
    verify_token,
    verify_refresh_token
)
from .mongodb import get_users_collection
from .auth_helpers import (
    extract_token,
    verify_admin_access,
    get_client_info,
    get_user_by_id,
    create_token_pair
)

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

    DEPRECATED: This endpoint will be deprecated in favor of admin-created users.
    Self-registration creates users without proper customer_id assignment.
    Use POST /auth/users (admin only) for creating users with correct customer_id.

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

@router.get("/me", response_model=UserResponse)
@limiter.limit("30/minute")  # Max 30 requests per minute per IP
async def me(request: Request, authorization: Optional[str] = Header(None), users=Depends(get_users_collection)):
    """
    Get current user information from JWT token.

    - Extracts JWT from Authorization header OR cookie
    - Verifies token
    - Returns current user data
    """
    # Extract token from header or cookie (uses helper)
    token = extract_token(authorization, request)

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


#===========================================================================
# ADMIN USER MANAGEMENT ENDPOINTS
#===========================================================================

@router.get("/users", response_model=UserListResponse)
@limiter.limit("200/minute")  # Higher limit for admin-only search endpoint
async def list_users(
    request: Request,
    page: int = 1,
    page_size: int = 50,
    search: Optional[str] = None,
    role: Optional[str] = None,
    authorization: Optional[str] = Header(None),
    users=Depends(get_users_collection)
):
    """
    List all users with pagination, search, and filtering. Admin only.

    Query params:
    - page: Page number (default: 1)
    - page_size: Users per page (default: 50, max: 100)
    - search: Search in email, name, or customer_id (optional)
    - role: Filter by role: customer, admin, internal, device (optional)
    """
    # Verify admin access
    await verify_admin_access(authorization, request)

    # Validate pagination params
    page = max(1, page)
    page_size = min(max(1, page_size), 100)
    skip = (page - 1) * page_size

    # Build query filter
    query = {}

    # Add search filter (case-insensitive regex on email, name, customer_id)
    if search:
        search_regex = {"$regex": search, "$options": "i"}
        query["$or"] = [
            {"email": search_regex},
            {"name": search_regex},
            {"customer_id": search_regex}
        ]

    # Add role filter
    if role:
        query["role"] = role

    # Get total count and users with filters
    total = await users.count_documents(query)
    user_docs = await users.find(query).skip(skip).limit(page_size).to_list(length=page_size)

    # Convert to response format
    user_responses = [
        UserResponse(
            id=str(user["_id"]),
            email=user["email"],
            name=user["name"],
            created_at=user["created_at"],
            role=user.get("role", "customer"),
            customer_id=user.get("customer_id")
        )
        for user in user_docs
    ]

    logger.info(
        "Users listed",
        extra={
            "page": page,
            "page_size": page_size,
            "total": total,
            "search": search,
            "role_filter": role,
            **get_client_info(request)
        }
    )

    return UserListResponse(
        users=user_responses,
        total=total,
        page=page,
        page_size=page_size
    )


@router.get("/users/{user_id}", response_model=UserResponse)
@limiter.limit("30/minute")
async def get_user(
    request: Request,
    user_id: str,
    authorization: Optional[str] = Header(None),
    users=Depends(get_users_collection)
):
    """
    Get a specific user by ID. Admin only.
    """
    # Verify admin access
    await verify_admin_access(authorization, request)

    # Get user with validation (reuses existing helper)
    user = await get_user_by_id(user_id, users, request)

    logger.info(
        "User retrieved by admin",
        extra={"target_user_id": user_id, **get_client_info(request)}
    )

    return UserResponse(
        id=str(user["_id"]),
        email=user["email"],
        name=user["name"],
        created_at=user["created_at"],
        role=user.get("role", "customer"),
        customer_id=user.get("customer_id")
    )


@router.post("/users", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit("10/minute")
async def create_user_as_admin(
    request: Request,
    user_data: AdminUserCreate,
    authorization: Optional[str] = Header(None),
    users=Depends(get_users_collection)
):
    """
    Create a new user as admin (bypass normal registration).

    Allows setting:
    - Custom role (customer, admin, internal, device)
    - customer_id assignment
    """
    # Verify admin access
    admin_payload = await verify_admin_access(authorization, request)

    # Check if user already exists
    existing_user = await users.find_one({"email": user_data.email})
    if existing_user:
        logger.warning(
            "Admin tried to create duplicate user",
            extra={"email": user_data.email, "admin_id": admin_payload.get("user_id"), **get_client_info(request)}
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
        "role": user_data.role,
        "customer_id": user_data.customer_id,
        "created_at": datetime.now(UTC)
    }

    # Insert into database
    try:
        result = await users.insert_one(user_doc)
    except Exception as e:
        logger.error(
            "Database error during admin user creation",
            extra={"error": str(e), "email": user_data.email}
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="User creation failed"
        )

    logger.info(
        "User created by admin",
        extra={
            "email": user_data.email,
            "user_id": str(result.inserted_id),
            "role": user_data.role,
            "customer_id": user_data.customer_id,
            "admin_id": admin_payload.get("user_id"),
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


@router.put("/users/{user_id}", response_model=UserResponse)
@limiter.limit("10/minute")
async def update_user(
    request: Request,
    user_id: str,
    user_data: AdminUserUpdate,
    authorization: Optional[str] = Header(None),
    users=Depends(get_users_collection)
):
    """
    Update user fields. Admin only.

    All fields are optional - only provided fields will be updated.
    Password will be hashed if provided.
    """
    # Verify admin access
    admin_payload = await verify_admin_access(authorization, request)

    # Validate user ID format
    if not user_id or len(user_id) != 24 or not all(c in '0123456789abcdefABCDEF' for c in user_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid user ID format"
        )

    # Build update document (only include provided fields)
    update_doc = {}
    if user_data.email is not None:
        # Check if new email already exists
        existing_user = await users.find_one({"email": user_data.email, "_id": {"$ne": ObjectId(user_id)}})
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already in use by another user"
            )
        update_doc["email"] = user_data.email

    if user_data.password is not None:
        update_doc["hashed_password"] = hash_password(user_data.password)

    if user_data.name is not None:
        update_doc["name"] = user_data.name

    if user_data.role is not None:
        update_doc["role"] = user_data.role

    if user_data.customer_id is not None:
        update_doc["customer_id"] = user_data.customer_id

    # Check if there's anything to update
    if not update_doc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No fields provided for update"
        )

    # Update user
    try:
        result = await users.update_one(
            {"_id": ObjectId(user_id)},
            {"$set": update_doc}
        )
    except InvalidId:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid user ID format"
        )

    if result.matched_count == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    # Get updated user
    updated_user = await get_user_by_id(user_id, users, request)

    logger.info(
        "User updated by admin",
        extra={
            "target_user_id": user_id,
            "updated_fields": list(update_doc.keys()),
            "admin_id": admin_payload.get("user_id"),
            **get_client_info(request)
        }
    )

    return UserResponse(
        id=str(updated_user["_id"]),
        email=updated_user["email"],
        name=updated_user["name"],
        created_at=updated_user["created_at"],
        role=updated_user.get("role", "customer"),
        customer_id=updated_user.get("customer_id")
    )

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
    # Verify admin access
    admin_payload = await verify_admin_access(authorization, request)

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
        extra={
            "deleted_user_id": user_id,
            "admin_id": admin_payload.get("user_id"),
            **get_client_info(request)
        }
    )

    return None
