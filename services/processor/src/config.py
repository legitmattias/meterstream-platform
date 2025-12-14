"""Application configuration loaded from environment variables."""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Configuration for the Data Processor service."""

    nats_url: str = "nats://nats:4222"
    nats_stream: str = "METER_DATA"
    nats_subject: str = "meter.readings"

    influx_url: str = "http://influxdb:8086"
    influx_org: str = "meterstream"
    influx_bucket: str = "meterstream"
    influx_token: str = ""
    influx_measurement: str = "meter_readings"


settings = Settings()