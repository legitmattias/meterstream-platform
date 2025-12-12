"""JWT validation middleware for API Gateway."""

import logging
from datetime import datetime, timezone
from typing import Optional

from fastapi import HTTPException, Request
from jose import JWTError, jwt
from pydantic import BaseModel

from .config import settings

logger = logging.getLogger(__name__)


class TokenPayload(BaseModel):
    """JWT token payload structure."""

    sub: str  # User ID
    role: Optional[str] = None  # customer, internal, admin
    customer_id: Optional[str] = None
    exp: int  # Expiration timestamp


def decode_token(token: str) -> TokenPayload:
    """
    Decode and validate a JWT token.

    Args:
        token: JWT token string

    Returns:
        TokenPayload with decoded claims

    Raises:
        HTTPException: If token is invalid or expired
    """
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret,
            algorithms=[settings.jwt_algorithm],
        )

        # Check expiration
        exp = payload.get("exp")
        if exp and datetime.fromtimestamp(exp, tz=timezone.utc) < datetime.now(
            tz=timezone.utc
        ):
            raise HTTPException(status_code=401, detail="Token expired")

        return TokenPayload(**payload)

    except JWTError as e:
        logger.warning("Invalid JWT token: %s", e)
        raise HTTPException(status_code=401, detail="Invalid token") from e


def extract_token_from_header(request: Request) -> str:
    """
    Extract JWT token from Authorization header.

    Args:
        request: FastAPI request object

    Returns:
        JWT token string

    Raises:
        HTTPException: If Authorization header is missing or malformed
    """
    auth_header = request.headers.get("Authorization")

    if not auth_header:
        raise HTTPException(status_code=401, detail="Missing Authorization header")

    parts = auth_header.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(
            status_code=401, detail="Invalid Authorization header format"
        )

    return parts[1]


async def validate_jwt(request: Request) -> TokenPayload:
    """
    Validate JWT token from request and return payload.

    Args:
        request: FastAPI request object

    Returns:
        TokenPayload with decoded claims
    """
    token = extract_token_from_header(request)
    return decode_token(token)
