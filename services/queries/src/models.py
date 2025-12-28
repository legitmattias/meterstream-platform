"""Models for query service responses."""

from pydantic import BaseModel


class ConsumptionDataPoint(BaseModel):
    """Single consumption data point."""

    timestamp: str
    consumption: float


class WeeklyDayData(BaseModel):
    """Weekly per-day data point."""

    day: str  # Mon, Tue, Wed, etc.
    consumption: float


class MonthlyDayData(BaseModel):
    """Monthly per-day data point."""

    day: int  # 1-31
    consumption: float


class HourlyData(BaseModel):
    """Hourly data point."""

    hour: int  # 0-23
    consumption: float


class ConsumptionResponse(BaseModel):
    """Consumption query response."""

    customer_id: str | None  # None for internal/admin users (global view)
    period: str
    data: list[ConsumptionDataPoint]


class SummaryResponse(BaseModel):
    """Summary statistics response."""

    customer_id: str | None  # None for internal/admin users (global view)
    period: str
    total: float
    average: float


class DashboardResponse(BaseModel):
    """Complete dashboard data response."""

    customer_id: str | None  # None for internal/admin users (global view)
    year: str | None  # "2024", "2025", or "All"
    month: int | None  # 1-12 if monthly view requested
    date: str | None  # YYYY-MM-DD if hourly view requested
    weekly_days: list[WeeklyDayData]
    monthly_days: list[MonthlyDayData]
    hourly: list[HourlyData]
    total: float
    average: float


class HealthResponse(BaseModel):
    """Health check response."""

    status: str = "ok"


class DataQuality(BaseModel):
    """Data quality metrics (placeholders until implemented)."""

    completeness: float | None = None
    accuracy: float | None = None
    timeliness: float | None = None


class ConsumerData(BaseModel):
    """Top consumer entry."""

    name: str
    consumption: float


class TopConsumersResponse(BaseModel):
    """Response for top consumers endpoint."""

    customer_id: str | None  # None for internal/admin users (global view)
    consumers: list[ConsumerData] = []


class LogsResponse(BaseModel):
    """Simple logs response placeholder."""

    customer_id: str | None  # None for internal/admin users (global view)
    logs: list[str] = []
