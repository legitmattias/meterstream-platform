"""Helper functions for authentication router.

This module contains reusable helper functions for:
- Admin access verification
- User retrieval and validation
- Token pair creation
- Client information extraction
"""

import logging
from typing import Optional
from fastapi import HTTPException, Request, status
from bson import ObjectId
from bson.errors import InvalidId

from .jwt_service import verify_token, create_access_token, create_refresh_token
from .models import TokenPairResponse

logger = logging.getLogger(__name__)


async def verify_admin_access(authorization: Optional[str], request: Request) -> dict:
    """
    Verify that request has valid admin authorization.

    Extracts and verifies JWT token from Authorization header,
    then checks that user has admin role.

    Args:
        authorization: Authorization header value (format: "Bearer <token>")
        request: FastAPI request object for logging

    Returns:
        dict: Token payload if valid admin

    Raises:
        HTTPException: If unauthorized or not admin
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
