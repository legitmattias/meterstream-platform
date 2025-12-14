from datetime import datetime

import pytest

from src.models import MeterReading
from src.main import _to_influx_line_protocol


def test_to_influx_line_protocol_contains_expected_parts():
    reading = MeterReading(
        DateTime=datetime(2020, 1, 1, 0, 0, 0),
        CUSTOMER="106",
        AREA="Kvarnholmen",
        Power_Consumption=0.0112,
    )

    line = _to_influx_line_protocol(reading)

    # Basic sanity checks: measurement + tags + field + timestamp
    assert "customer=106" in line
    assert "area=Kvarnholmen" in line
    assert "power_consumption=" in line

    # Timestamp is last token and numeric
    timestamp_token = line.split()[-1]
    assert timestamp_token.isdigit()


def test_to_influx_line_protocol_negative_raises():
    reading = MeterReading(
        DateTime=datetime(2020, 1, 1, 0, 0, 0),
        CUSTOMER="106",
        AREA="Kvarnholmen",
        Power_Consumption=-1.0,
    )

    with pytest.raises(ValueError):
        _to_influx_line_protocol(reading)
