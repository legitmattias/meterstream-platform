from pydantic_settings import BaseSettings
from pydantic import ConfigDict
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = ConfigDict(env_file=".env")

    # MongoDB
    mongodb_url: str = "mongodb://localhost:27017"
    database_name: str = "meterstream_auth"

    # JWT
    jwt_secret: str = "super-secret-key-change-in-production"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 60
    jwt_refresh_expire_days: int = 7

    # Service
    service_name: str = "Meterstream auth-service"
    debug: bool = True
    log_level: str = "INFO"

    # Bootstrap admin (only used if no admin exists)
    bootstrap_admin_email: str = "admin@meterstream.local"
    bootstrap_admin_password: str | None = None

"""Singelton pattern, create only once"""
@lru_cache
def get_settings() -> Settings:
    return Settings()
