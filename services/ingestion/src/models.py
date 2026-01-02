"""Pydantic models for meter reading data."""

# pylint: disable=too-few-public-methods

from datetime import datetime as dt
from pydantic import BaseModel, ConfigDict, Field


class MeterReading(BaseModel):
    """Single meter reading from energy meter."""

    model_config = ConfigDict(populate_by_name=True)

    timestamp: dt = Field(..., alias="DateTime")
    customer: str = Field(..., alias="CUSTOMER", min_length=1, max_length=50)
    area: str = Field(..., alias="AREA", min_length=1, max_length=100)
    power_consumption: float = Field(..., alias="Power_Consumption", ge=0, le=10_000_000)


class MeterReadingBatch(BaseModel):
    """Batch of meter readings for ingestion."""

    readings: list[MeterReading] = Field(..., min_length=1, max_length=10_000)


class HealthResponse(BaseModel):
    """Health check response."""

    status: str = "ok"


class IngestResponse(BaseModel):
    """Response from ingest endpoint."""

    accepted: int
    message: str = "Readings published to queue"
