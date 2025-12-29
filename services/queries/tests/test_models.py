"""Tests for query service models."""

import pytest
from pydantic import ValidationError

from src.models import (
    ConsumptionDataPoint,
    WeeklyDayData,
    MonthlyDayData,
    HourlyData,
    ConsumptionResponse,
    SummaryResponse,
    DashboardResponse,
    HealthResponse,
    DataQuality,
    ConsumerData,
    TopConsumersResponse,
    LogsResponse,
)


class TestConsumptionDataPoint:
    def test_valid_data_point(self):
        point = ConsumptionDataPoint(timestamp="2024-01-01T00:00:00Z", consumption=1.5)
        assert point.timestamp == "2024-01-01T00:00:00Z"
        assert point.consumption == 1.5

    def test_missing_timestamp_raises_error(self):
        with pytest.raises(ValidationError):
            ConsumptionDataPoint(consumption=1.5)

    def test_missing_consumption_raises_error(self):
        with pytest.raises(ValidationError):
            ConsumptionDataPoint(timestamp="2024-01-01T00:00:00Z")


class TestWeeklyDayData:
    def test_valid_weekly_day(self):
        data = WeeklyDayData(day="Mon", consumption=10.5)
        assert data.day == "Mon"
        assert data.consumption == 10.5


class TestMonthlyDayData:
    def test_valid_monthly_day(self):
        data = MonthlyDayData(day=15, consumption=25.0)
        assert data.day == 15
        assert data.consumption == 25.0


class TestHourlyData:
    def test_valid_hourly_data(self):
        data = HourlyData(hour=14, consumption=3.2)
        assert data.hour == 14
        assert data.consumption == 3.2


class TestHealthResponse:
    def test_default_status_is_ok(self):
        response = HealthResponse()
        assert response.status == "ok"

    def test_custom_status(self):
        response = HealthResponse(status="degraded")
        assert response.status == "degraded"


class TestConsumptionResponse:
    def test_valid_response(self):
        response = ConsumptionResponse(
            customer_id="CUST123",
            period="daily",
            data=[ConsumptionDataPoint(timestamp="2024-01-01T00:00:00Z", consumption=1.0)],
        )
        assert response.customer_id == "CUST123"
        assert response.period == "daily"
        assert len(response.data) == 1

    def test_none_customer_id_for_admin(self):
        response = ConsumptionResponse(customer_id=None, period="weekly", data=[])
        assert response.customer_id is None


class TestSummaryResponse:
    def test_valid_summary(self):
        response = SummaryResponse(
            customer_id="CUST123",
            period="monthly",
            total=100.0,
            average=8.33,
        )
        assert response.total == 100.0
        assert response.average == 8.33


class TestDashboardResponse:
    def test_minimal_dashboard(self):
        response = DashboardResponse(
            customer_id=None,
            year="2024",
            month=None,
            date=None,
            weekly_days=[],
            monthly_days=[],
            hourly=[],
            total=0.0,
            average=0.0,
        )
        assert response.year == "2024"
        assert response.total == 0.0


class TestDataQuality:
    def test_default_none_values(self):
        quality = DataQuality()
        assert quality.completeness is None
        assert quality.accuracy is None
        assert quality.timeliness is None

    def test_with_values(self):
        quality = DataQuality(completeness=0.95, accuracy=0.99, timeliness=0.87)
        assert quality.completeness == 0.95


class TestTopConsumersResponse:
    def test_empty_consumers(self):
        response = TopConsumersResponse(customer_id=None)
        assert response.consumers == []

    def test_with_consumers(self):
        response = TopConsumersResponse(
            customer_id=None,
            consumers=[ConsumerData(name="Customer A", consumption=500.0)],
        )
        assert len(response.consumers) == 1
        assert response.consumers[0].name == "Customer A"


class TestLogsResponse:
    def test_empty_logs(self):
        response = LogsResponse(customer_id="CUST123")
        assert response.logs == []
