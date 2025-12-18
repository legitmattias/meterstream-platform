"""Query Service configuration loaded from environment variables."""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Configuration for the Query Service."""

    influx_url: str = "http://influxdb:8086"
    influx_org: str = "meterstream"
    influx_bucket: str = "meterstream"
    influx_token: str = ""
    influx_measurement: str = "meter_readings"

    log_level: str = "INFO"

    class Config:
        env_file = ".env"


settings = Settings()
