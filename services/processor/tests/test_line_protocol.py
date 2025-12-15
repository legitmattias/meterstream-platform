from datetime import datetime, timezone

import pytest

from src.models import MeterReading
from src.config import settings
from src.main import _to_influx_line_protocol


def test_to_influx_line_protocol_contains_expected_parts():
    reading = MeterReading(
        DateTime=datetime(2020, 1, 1, 0, 0, 0),
        CUSTOMER="106",
        AREA="Kvarnholmen",
        Power_Consumption=0.0112,
    )

    line = _to_influx_line_protocol(reading)

    assert "customer=106" in line
    assert "area=Kvarnholmen" in line
    assert "power_consumption=" in line

    timestamp_token = line.split()[-1]
    assert timestamp_token.isdigit()

def test_to_influx_line_protocol_contains_expected_parts_and_timestamp():
    dt = datetime(2020, 1, 1, 0, 0, 0, tzinfo=timezone.utc)

    reading = MeterReading(
        DateTime=dt,
        CUSTOMER="1060598736",
        AREA="Kvarnholmen",
        Power_Consumption=0.0112,
    )

    line = _to_influx_line_protocol(reading)

    expected_ts_ns = int(dt.timestamp() * 1_000_000_000)

    assert line.startswith(
        f"{settings.influx_measurement},customer=1060598736,area=Kvarnholmen "
    )

    assert f"power_consumption=0.0112 {expected_ts_ns}" in line