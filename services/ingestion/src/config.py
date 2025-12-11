"""Application configuration loaded from environment variables."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(env_prefix="")

    nats_url: str = "nats://nats:4222"
    nats_stream: str = "METER_DATA"
    nats_subject: str = "meter.readings"

    log_level: str = "INFO"


settings = Settings()
