from datetime import datetime, timedelta, UTC
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext

from .config import get_settings

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

settings = get_settings()


def hash_password(password: str) -> str:
    """Hash a password using bcrypt."""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against a hash."""
    return pwd_context.verify(plain_password, hashed_password)


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
        settings.jwt_secret_key, 
        algorithm=settings.jwt_algorithm
    )
    
    return token, int(expires_delta.total_seconds())

# TODO: flytta till api gateway??
def verify_token(token: str) -> Optional[dict]:
    """
    Verify and decode a JWT token.
    
    Returns:
        dict with user info if valid, None if invalid
    """
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret_key,
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
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm
    )

# TODO: flytta till api gateway??
def verify_refresh_token(token: str) -> Optional[str]:
    """
    Verify a refresh token and return user_id.
    
    Returns:
        user_id if valid, None if invalid
    """
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm]
        )
        
        # Check it's a refresh token
        if payload.get("type") != "refresh":
            return None
            
        return payload.get("sub")
    except JWTError:
        return None