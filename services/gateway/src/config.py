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
    grafana_service_url: str = "http://grafana:3000"

    # ==== ANALYTICS INTEGRATION: Queries service URL and dev/test toggles ====
    queries_service_url: str = "http://queries:8000"
    disable_auth_for_data: bool = False  # Set true to bypass JWT for /api/data/*
    dev_customer_id: str = "demo-customer"  # Used if DISABLE_AUTH_FOR_DATA is true and no X-Customer-ID is provided
    # ==== END ANALYTICS INTEGRATION ====

    log_level: str = "INFO"


settings = Settings()
