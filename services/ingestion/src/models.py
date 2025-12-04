"""Pydantic models for meter reading data."""

# pylint: disable=too-few-public-methods

from datetime import datetime
from pydantic import BaseModel, Field


class MeterReading(BaseModel):
    """Single meter reading from energy meter."""

    datetime: datetime = Field(..., alias="DateTime")
    customer: str = Field(..., alias="CUSTOMER")
    area: str = Field(..., alias="AREA")
    power_consumption: float = Field(..., alias="Power_Consumption")

    class Config:
        """Pydantic config."""

        populate_by_name = True


class MeterReadingBatch(BaseModel):
    """Batch of meter readings for ingestion."""

    readings: list[MeterReading]


class HealthResponse(BaseModel):
    """Health check response."""

    status: str = "ok"


class IngestResponse(BaseModel):
    """Response from ingest endpoint."""

    accepted: int
    message: str = "Readings published to queue"
