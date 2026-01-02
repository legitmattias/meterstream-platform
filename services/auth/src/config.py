from pydantic_settings import BaseSettings
from pydantic import ConfigDict
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = ConfigDict(env_file=".env")

    # MongoDB
    mongodb_url: str = "mongodb://localhost:27017"
    database_name: str = "meterstream_auth"

    # JWT - CRITICAL: jwt_secret MUST be set via environment variable
    jwt_secret: str  # No default for security - must be set explicitly. use .env for locall testing
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 15  # Reduced from 60 for better security (auto-refresh handles this)
    jwt_refresh_expire_days: int = 7

    # Service
    service_name: str = "Meterstream auth-service"
    debug: bool = False  # SECURITY: Default to False for production safety
    log_level: str = "INFO"

    # Bootstrap admin (only used if no admin exists)
    bootstrap_admin_email: str = "admin@meterstream.com"
    bootstrap_admin_password: str | None = None

    # Seed test data (for staging/development only)
    seed_test_data: bool = False
    test_user_password: str = "testpassword123"

"""Singelton pattern, create only once"""
@lru_cache
def get_settings() -> Settings:
    return Settings()
