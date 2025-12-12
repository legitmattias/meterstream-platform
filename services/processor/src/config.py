"""Application configuration loaded from environment variables."""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Configuration for the Data Processor service."""

    nats_url: str = "nats://nats:4222"
    nats_stream: str = "METER_DATA"
    nats_subject: str = "meter.readings"


settings = Settings()