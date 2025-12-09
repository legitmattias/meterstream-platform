"""Application configuration loaded from environment variables."""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    nats_url: str = "nats://nats:4222"
    nats_stream: str = "METER_DATA"
    nats_subject: str = "meter.readings"

    log_level: str = "INFO"

    class Config:  # pylint: disable=too-few-public-methods
        """Pydantic config."""

        env_prefix = ""


settings = Settings()
