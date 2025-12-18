"""Models for query service responses."""

from pydantic import BaseModel


class ConsumptionDataPoint(BaseModel):
    """Single consumption data point."""

    timestamp: str
    consumption: float


class ConsumptionResponse(BaseModel):
    """Consumption query response."""

    customer_id: str
    period: str
    data: list[ConsumptionDataPoint]


class SummaryResponse(BaseModel):
    """Summary statistics response."""

    customer_id: str
    period: str
    total: float
    average: float


class DashboardResponse(BaseModel):
    """Complete dashboard data response."""

    customer_id: str
    period: str
    consumption: list[ConsumptionDataPoint]
    summary: SummaryResponse


class HealthResponse(BaseModel):
    """Health check response."""

    status: str = "ok"
