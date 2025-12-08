"""Application configuration loaded from environment variables."""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # JWT configuration (jwt_secret is required - no default for security)
    jwt_secret: str
    jwt_algorithm: str = "HS256"

    # Backend service URLs (K8s service DNS names)
    auth_service_url: str = "http://auth:8000"
    ingestion_service_url: str = "http://ingestion:8000"

    log_level: str = "INFO"

    class Config:  # pylint: disable=too-few-public-methods
        """Pydantic config."""

        env_prefix = ""
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
