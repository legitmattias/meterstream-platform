"""Ingestion Service - receives meter readings and publishes to NATS JetStream."""

import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse

from .config import settings

# Maximum request body size: 10MB (enough for 10,000 readings at ~200 bytes each)
MAX_BODY_SIZE = 10 * 1024 * 1024
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


@app.middleware("http")
async def limit_request_size(request: Request, call_next):
    """Reject requests with body larger than MAX_BODY_SIZE."""
    content_length = request.headers.get("content-length")
    if content_length and int(content_length) > MAX_BODY_SIZE:
        return JSONResponse(
            status_code=413,
            content={"detail": f"Request body too large. Maximum size is {MAX_BODY_SIZE // (1024*1024)}MB"}
        )
    return await call_next(request)


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

    readings_data = [
        reading.model_dump(by_alias=True, mode="json") for reading in batch.readings
    ]

    try:
        count = await nats_client.publish_batch(readings_data)
        logger.info("Ingested %d readings", count)
        return IngestResponse(accepted=count)
    except Exception as e:
        logger.error("Failed to publish readings: %s", e)
        raise HTTPException(
            status_code=500, detail="Failed to publish readings"
        ) from e
