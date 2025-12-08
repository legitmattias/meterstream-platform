from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # MongoDB
    mongodb_url: str = "mongodb://localhost:27017"
    database_name: str = "meterstream_auth"
    
    # JWT
    jwt_secret_key: str = "super-secret-key-change-in-production"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 60
    
    # Service
    service_name: str = "auth-service"
    debug: bool = True

    class Config:
        env_file = ".env"

"""Singelton pattern, create only once"""
@lru_cache
def get_settings() -> Settings:
    return Settings()
