"""Tests for Pydantic models."""

from datetime import datetime

import pytest

from src.models import MeterReading, MeterReadingBatch


class TestMeterReading:
    """Tests for MeterReading model."""

    def test_valid_reading(self):
        """Test creating a valid meter reading."""
        reading = MeterReading(
            DateTime=datetime(2020, 1, 1, 0, 0, 0),
            CUSTOMER="1060598736",
            AREA="Kvarnholmen",
            Power_Consumption=0.0112,
        )
        assert reading.customer == "1060598736"
        assert reading.area == "Kvarnholmen"
        assert reading.power_consumption == 0.0112

    def test_reading_from_dict(self):
        """Test creating a reading from CSV-style dict."""
        data = {
            "DateTime": "2020-01-01T00:00:00",
            "CUSTOMER": "1060598736",
            "AREA": "Kvarnholmen",
            "Power_Consumption": 0.0112,
        }
        reading = MeterReading(**data)
        assert reading.customer == "1060598736"

    def test_reading_serialization(self):
        """Test that reading serializes with original field names."""
        reading = MeterReading(
            DateTime=datetime(2020, 1, 1, 0, 0, 0),
            CUSTOMER="1060598736",
            AREA="Kvarnholmen",
            Power_Consumption=0.0112,
        )
        data = reading.model_dump(by_alias=True)
        assert "DateTime" in data
        assert "CUSTOMER" in data
        assert "Power_Consumption" in data

    def test_invalid_reading_missing_field(self):
        """Test that missing required field raises error."""
        with pytest.raises(Exception):
            MeterReading(
                DateTime=datetime(2020, 1, 1, 0, 0, 0),
                CUSTOMER="1060598736",
                # Missing AREA and Power_Consumption
            )

    def test_customer_too_long(self):
        """Test that customer field over 50 chars is rejected."""
        with pytest.raises(Exception):
            MeterReading(
                DateTime=datetime(2020, 1, 1, 0, 0, 0),
                CUSTOMER="x" * 51,
                AREA="Kvarnholmen",
                Power_Consumption=0.0112,
            )

    def test_area_too_long(self):
        """Test that area field over 100 chars is rejected."""
        with pytest.raises(Exception):
            MeterReading(
                DateTime=datetime(2020, 1, 1, 0, 0, 0),
                CUSTOMER="1060598736",
                AREA="x" * 101,
                Power_Consumption=0.0112,
            )

    def test_negative_power_consumption(self):
        """Test that negative power consumption is rejected."""
        with pytest.raises(Exception):
            MeterReading(
                DateTime=datetime(2020, 1, 1, 0, 0, 0),
                CUSTOMER="1060598736",
                AREA="Kvarnholmen",
                Power_Consumption=-1.0,
            )

    def test_power_consumption_above_limit(self):
        """Test that power consumption above 10M is rejected."""
        with pytest.raises(Exception):
            MeterReading(
                DateTime=datetime(2020, 1, 1, 0, 0, 0),
                CUSTOMER="1060598736",
                AREA="Kvarnholmen",
                Power_Consumption=10_000_001,
            )


class TestMeterReadingBatch:
    """Tests for MeterReadingBatch model."""

    def test_empty_batch_rejected(self):
        """Test that empty batch is rejected (min_length=1)."""
        with pytest.raises(Exception):
            MeterReadingBatch(readings=[])

    def test_batch_with_readings(self):
        """Test creating a batch with readings."""
        readings = [
            MeterReading(
                DateTime=datetime(2020, 1, 1, 0, 0, 0),
                CUSTOMER="1060598736",
                AREA="Kvarnholmen",
                Power_Consumption=0.0112,
            ),
            MeterReading(
                DateTime=datetime(2020, 1, 1, 1, 0, 0),
                CUSTOMER="1060598736",
                AREA="Kvarnholmen",
                Power_Consumption=0.0098,
            ),
        ]
        batch = MeterReadingBatch(readings=readings)
        assert len(batch.readings) == 2
