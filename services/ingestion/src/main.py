"""Ingestion Service - receives meter readings and publishes to NATS JetStream."""

import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, HTTPException

from .config import settings
from .models import HealthResponse, IngestResponse, MeterReadingBatch
from .nats_client import nats_client

logging.basicConfig(
    level=getattr(logging, settings.log_level),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan manager."""
    logger.info("Starting ingestion service")
    await nats_client.connect()
    yield
    logger.info("Shutting down ingestion service")
    await nats_client.disconnect()


app = FastAPI(
    title="Ingestion Service",
    description="Receives meter readings and publishes to NATS JetStream",
    version="0.1.0",
    lifespan=lifespan,
)


@app.get("/health", response_model=HealthResponse)
async def health():
    """Liveness probe - always returns OK if service is running."""
    return HealthResponse()


@app.get("/ready", response_model=HealthResponse)
async def ready():
    """Readiness probe - returns OK only if NATS is connected."""
    if not nats_client.is_connected:
        raise HTTPException(status_code=503, detail="NATS not connected")
    return HealthResponse()


@app.post("/ingest", response_model=IngestResponse)
async def ingest(batch: MeterReadingBatch):
    """
    Ingest a batch of meter readings.

    Accepts meter reading data and publishes each reading to NATS JetStream.
    """
    if not nats_client.is_connected:
        raise HTTPException(status_code=503, detail="NATS not connected")

    readings_data = [reading.model_dump(by_alias=True) for reading in batch.readings]

    try:
        count = await nats_client.publish_batch(readings_data)
        logger.info("Ingested %d readings", count)
        return IngestResponse(accepted=count)
    except Exception as e:
        logger.error("Failed to publish readings: %s", e)
        raise HTTPException(
            status_code=500, detail="Failed to publish readings"
        ) from e
