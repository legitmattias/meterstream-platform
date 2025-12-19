"""Application configuration loaded from environment variables."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_prefix="",
        env_file=".env",
        env_file_encoding="utf-8",
    )

    # JWT configuration (jwt_secret is required - no default for security)
    jwt_secret: str
    jwt_algorithm: str = "HS256"

    # Backend service URLs (K8s service DNS names)
    auth_service_url: str = "http://auth:8000"
    ingestion_service_url: str = "http://ingestion:8000"
    queries_service_url: str = "http://queries:8000" # ADDED BY SAS REMOVE

    log_level: str = "INFO"


settings = Settings()
