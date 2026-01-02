from datetime import datetime, timedelta, UTC
from typing import Optional
from jose import JWTError, jwt
import bcrypt

from .config import get_settings

settings = get_settings()


def hash_password(password: str) -> str:
    """
    Hash a password using bcrypt.

    Uses bcrypt directly instead of passlib to avoid Python 3.13 deprecation warning.
    Default cost factor is 12 rounds (2^12 iterations).
    """
    password_bytes = password.encode('utf-8')
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password_bytes, salt)
    return hashed.decode('utf-8')


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a password against a bcrypt hash.

    Uses constant-time comparison to prevent timing attacks.
    """
    password_bytes = plain_password.encode('utf-8')
    hashed_bytes = hashed_password.encode('utf-8')
    return bcrypt.checkpw(password_bytes, hashed_bytes)


def create_access_token(user_id: str, email: str, role: str, customer_id: Optional[str] = None) -> tuple[str, int]:
    """
    Create a JWT access token.
    
    Returns:
        tuple: (token, expires_in_seconds)
    """
    expires_delta = timedelta(minutes=settings.jwt_expire_minutes)
    now = datetime.now(UTC)
    expire = now + expires_delta

    payload = {
        "sub": user_id,           # authentication (who are you) mongoDB ID
        "email": email,
        "customer_id": customer_id, # data scoping (what can you see) Data-acess in influxDB
        "role": role,             # authorization (what can you do)
        "exp": expire,            # expiration time
        "iat": now                # issued at
    }
    
    token = jwt.encode(
        payload, 
        settings.jwt_secret, 
        algorithm=settings.jwt_algorithm
    )
    
    return token, int(expires_delta.total_seconds())

# TODO: MIGRATE TO API GATEWAY
# This function should be moved to the API Gateway service
# The API Gateway will need this to verify tokens for incoming requests
def verify_token(token: str) -> Optional[dict]:
    """
    Verify and decode a JWT token.

    Returns:
        dict with user info if valid, None if invalid

    NOTE: This function will be migrated to API Gateway in the future
    """
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret,
            algorithms=[settings.jwt_algorithm]
        )
        return {
            "user_id": payload.get("sub"),
            "email": payload.get("email"),
            "role": payload.get("role"),
            "customer_id": payload.get("customer_id")
        }
    except JWTError:
        return None


def create_refresh_token(user_id: str) -> str:
    """
    Create a refresh token (longer lived).

    Returns:
        Refresh token string
    """
    expires_delta = timedelta(days=settings.jwt_refresh_expire_days)
    now = datetime.now(UTC)
    expire = now + expires_delta

    payload = {
        "sub": user_id,
        "type": "refresh",
        "exp": expire,
        "iat": now
    }
    
    return jwt.encode(
        payload,
        settings.jwt_secret,
        algorithm=settings.jwt_algorithm
    )

# NOTE: This function stays in Auth Service - NOT migrated to API Gateway
# Only the Auth Service handles refresh tokens to issue new access tokens
def verify_refresh_token(token: str) -> Optional[str]:
    """
    Verify a refresh token and return user_id.

    Returns:
        user_id if valid, None if invalid

    NOTE: This function remains in Auth Service (used by /refresh endpoint)
    """
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret,
            algorithms=[settings.jwt_algorithm]
        )

        # Check it's a refresh token
        if payload.get("type") != "refresh":
            return None

        return payload.get("sub")
    except JWTError:
        return None