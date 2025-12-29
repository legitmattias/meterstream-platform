"""Helper functions for authentication router.

This module contains reusable helper functions for:
- Token extraction from headers and cookies
- Admin access verification
- User retrieval and validation
- Token pair creation
- Client information extraction
- Refresh token storage and revocation
"""

import logging
from typing import Optional
from datetime import datetime, UTC
from fastapi import HTTPException, Request, status
from bson import ObjectId
from bson.errors import InvalidId

from .jwt_service import verify_token, create_access_token, create_refresh_token
from .models import TokenPairResponse
from .config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


def extract_token(authorization: Optional[str], request: Request) -> Optional[str]:
    """
    Extract JWT token from Authorization header or cookie.

    Tries Authorization header first, then falls back to cookie.
    This allows both header-based and cookie-based authentication.

    Args:
        authorization: Authorization header value (format: "Bearer <token>")
        request: FastAPI request object (for cookie access)

    Returns:
        str: JWT token if found, None otherwise
    """
    token = None

    # Try Authorization header first
    if authorization:
        parts = authorization.split()
        if len(parts) == 2 and parts[0].lower() == "bearer":
            token = parts[1]

    # If no header token, try cookie
    if not token:
        token = request.cookies.get("access_token")

    return token


async def verify_admin_access(authorization: Optional[str], request: Request) -> dict:
    """
    Verify that request has valid admin authorization.

    Extracts and verifies JWT token from Authorization header or cookie,
    then checks that user has admin role.

    Args:
        authorization: Authorization header value (format: "Bearer <token>")
        request: FastAPI request object for logging and cookie access

    Returns:
        dict: Token payload if valid admin

    Raises:
        HTTPException: If unauthorized or not admin
    """
    # Extract token from header or cookie
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

    # Check admin role
    if payload.get("role") != "admin":
        logger.warning(
            "Non-admin attempted admin operation",
            extra={"requester_id": payload.get("user_id"), **get_client_info(request)}
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )

    return payload


def get_client_info(request: Request) -> dict:
    """
    Extract client IP and user agent from request for logging.

    Args:
        request: FastAPI request object

    Returns:
        dict: Client IP and user agent
    """
    return {
        "ip": request.client.host if request.client else "unknown",
        "user_agent": request.headers.get("user-agent", "unknown")
    }


async def get_user_by_id(user_id: str, users, request: Request) -> dict:
    """
    Get user from database by ID with validation and error handling.

    Validates ObjectId format, handles database errors, and logs security events.

    Args:
        user_id: MongoDB ObjectId as string (24 hex characters)
        users: MongoDB users collection
        request: FastAPI request object for logging

    Returns:
        dict: User document from database

    Raises:
        HTTPException: If user ID invalid, user not found, or database error
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
    """
    Create access and refresh tokens for a user.

    Args:
        user_id: User's MongoDB ObjectId as string
        email: User's email address
        role: User's role (customer, admin, internal, device)
        customer_id: User's customer ID (optional)

    Returns:
        TokenPairResponse: Access token, refresh token, and metadata
    """
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


async def store_refresh_token(refresh_token: str, user_id: str, refresh_tokens_collection) -> None:
    """
    Store a refresh token in the database.

    Args:
        refresh_token: The refresh token to store
        user_id: User's MongoDB ObjectId as string
        refresh_tokens_collection: MongoDB refresh_tokens collection
    """
    from datetime import timedelta

    expires_at = datetime.now(UTC) + timedelta(days=settings.jwt_refresh_expire_days)

    await refresh_tokens_collection.insert_one({
        "token": refresh_token,
        "user_id": user_id,
        "created_at": datetime.now(UTC),
        "expires_at": expires_at,
        "revoked": False
    })


async def revoke_refresh_token(refresh_token: str, refresh_tokens_collection) -> bool:
    """
    Revoke a refresh token by marking it as revoked in the database.

    Args:
        refresh_token: The refresh token to revoke
        refresh_tokens_collection: MongoDB refresh_tokens collection

    Returns:
        bool: True if token was found and revoked, False otherwise
    """
    result = await refresh_tokens_collection.update_one(
        {"token": refresh_token},
        {"$set": {"revoked": True, "revoked_at": datetime.now(UTC)}}
    )
    return result.modified_count > 0


async def is_refresh_token_valid(refresh_token: str, refresh_tokens_collection) -> bool:
    """
    Check if a refresh token is valid (exists and not revoked).

    Args:
        refresh_token: The refresh token to validate
        refresh_tokens_collection: MongoDB refresh_tokens collection

    Returns:
        bool: True if token is valid, False otherwise
    """
    token_doc = await refresh_tokens_collection.find_one({
        "token": refresh_token,
        "revoked": False,
        "expires_at": {"$gt": datetime.now(UTC)}
    })
    return token_doc is not None


async def revoke_all_user_refresh_tokens(user_id: str, refresh_tokens_collection) -> int:
    """
    Revoke all refresh tokens for a specific user.

    Args:
        user_id: User's MongoDB ObjectId as string
        refresh_tokens_collection: MongoDB refresh_tokens collection

    Returns:
        int: Number of tokens revoked
    """
    result = await refresh_tokens_collection.update_many(
        {"user_id": user_id, "revoked": False},
        {"$set": {"revoked": True, "revoked_at": datetime.now(UTC)}}
    )
    return result.modified_count
