"""Pydantic models for processing data."""

from datetime import datetime as dt
from pydantic import BaseModel, ConfigDict, Field


class MeterReading(BaseModel):
    """Single meter reading from energy meter."""

    model_config = ConfigDict(populate_by_name=True)

    timestamp: dt = Field(..., alias="DateTime")
    customer: str = Field(..., alias="CUSTOMER")
    area: str = Field(..., alias="AREA")
    power_consumption: float = Field(..., alias="Power_Consumption")


class HealthResponse(BaseModel):
    """Health check response."""

    status: str = "ok"