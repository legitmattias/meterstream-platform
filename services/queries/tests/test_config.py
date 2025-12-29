"""Tests for query service configuration."""

from src.config import Settings


class TestSettings:
    def test_default_read_instance_url(self):
        settings = Settings()
        assert settings.influx_url == "http://influxdb-read:8086"

    def test_default_write_instance_url(self):
        settings = Settings()
        assert settings.influx_write_url == "http://influxdb:8086"

    def test_default_org(self):
        settings = Settings()
        assert settings.influx_org == "meterstream"

    def test_default_bucket(self):
        settings = Settings()
        assert settings.influx_bucket == "meterstream"

    def test_default_measurement(self):
        settings = Settings()
        assert settings.influx_measurement == "meter_readings"

    def test_default_log_level(self):
        settings = Settings()
        assert settings.log_level == "INFO"

    def test_empty_tokens_by_default(self):
        settings = Settings()
        assert settings.influx_token == ""
        assert settings.influx_write_token == ""

    def test_empty_org_id_by_default(self):
        settings = Settings()
        assert settings.influx_write_org_id == ""
