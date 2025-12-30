"""Tests for query service models."""

import pytest
from pydantic import ValidationError

from src.models import ConsumptionDataPoint, HealthResponse


class TestConsumptionDataPoint:
    def test_missing_timestamp_raises_error(self):
        with pytest.raises(ValidationError):
            ConsumptionDataPoint(consumption=1.5)

    def test_missing_consumption_raises_error(self):
        with pytest.raises(ValidationError):
            ConsumptionDataPoint(timestamp="2025-01-01T00:00:00Z")


class TestHealthResponse:
    def test_default_status_is_ok(self):
        response = HealthResponse()
        assert response.status == "ok"
