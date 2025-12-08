from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext

from app.config import get_settings

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

settings = get_settings()


def hash_password(password: str) -> str:
    """Hash a password using bcrypt."""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against a hash."""
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(user_id: str, email: str, role: str) -> tuple[str, int]:
    """
    Create a JWT access token.
    
    Returns:
        tuple: (token, expires_in_seconds)
    """
    expires_delta = timedelta(minutes=settings.jwt_expire_minutes)
    expire = datetime.utcnow() + expires_delta
    
    payload = {
        "sub": user_id,           # subject (user id)
        "email": email,
        "role": role,
        "exp": expire,            # expiration time
        "iat": datetime.utcnow()  # issued at
    }
    
    token = jwt.encode(
        payload, 
        settings.jwt_secret_key, 
        algorithm=settings.jwt_algorithm
    )
    
    return token, int(expires_delta.total_seconds())


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
            "role": payload.get("role")
        }
    except JWTError:
        return None
