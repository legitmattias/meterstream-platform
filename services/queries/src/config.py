"""Query Service configuration loaded from environment variables."""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Configuration for the Query Service."""

    # Read instance (for queries)
    influx_url: str = "http://influxdb-read:8086"
    influx_org: str = "meterstream"
    influx_bucket: str = "meterstream"
    influx_token: str = ""
    influx_measurement: str = "meter_readings"

    # Write instance (for replication stats)
    influx_write_url: str = "http://influxdb:8086"
    influx_write_token: str = ""
    influx_write_org_id: str = ""  # Org ID needed for replication API

    log_level: str = "INFO"

    class Config:
        env_file = ".env"


settings = Settings()
