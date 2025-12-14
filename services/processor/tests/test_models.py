from datetime import datetime

import pytest
from pydantic import ValidationError

from src.models import MeterReading, HealthResponse


def test_health_response_default_ok():
    res = HealthResponse()
    assert res.status == "ok"


def test_meter_reading_valid_with_aliases():
    reading = MeterReading(
        DateTime=datetime(2020, 1, 1, 0, 0, 0),
        CUSTOMER="1060598736",
        AREA="Kvarnholmen",
        Power_Consumption=0.0112,
    )
    assert reading.customer == "1060598736"
    assert reading.area == "Kvarnholmen"
    assert reading.power_consumption == 0.0112

def test_meterreading_missing_required_field_raises_validationerror():
    # Saknar AREA och Power_Consumption -> ska faila
    with pytest.raises(ValidationError):
        MeterReading(
            DateTime="2020-01-01T00:00:00",
            CUSTOMER="1060598736",
        )