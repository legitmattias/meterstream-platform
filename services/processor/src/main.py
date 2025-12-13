"""Data Processing Service - retrieves and processes meter readings from NATS JetStream."""
import asyncio
import json
import logging
from contextlib import asynccontextmanager

import nats
from fastapi import FastAPI, HTTPException
from pydantic import ValidationError

from src.config import settings
from src.models import MeterReading, HealthResponse

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

_nc = None
_js = None
_consumer_task = None

async def _connect_with_retry():
    """Connect to NATS (retry until it works)."""
    while True:
        try:
            nc = await nats.connect(settings.nats_url)
            return nc
        except Exception as e:
            logger.warning("Failed to connect to NATS: %s. Retrying...", e)
            await asyncio.sleep(1)

async def _subscribe_with_retry():
    """Create pull subscription (retry until it works)."""
    while True:
        try:
            return await _js.pull_subscribe(
                subject=settings.nats_subject,
                durable="dataprocessor",
                stream=settings.nats_stream,
            )
        except Exception as e:
            logger.warning("Failed to subscribe: %s. Retrying...", e)
            await asyncio.sleep(1)

async def _process_reading(reading: MeterReading) -> None: 
    """Process one reading.""" 
    if reading.power_consumption < 0:
        raise ValueError(f"Negative consumption: {reading.power_consumption}") 

    # TODO 
    # 1) Aggregering 
    # 2) Skriv till InfluxDB
    return


async def _consume_messages() -> None:
    """Minimal NATS consumer loop."""
    sub = await _subscribe_with_retry()

    while True:
        try:
            msgs = await sub.fetch(batch=10, timeout=1)
        except nats.errors.TimeoutError:
            continue
        except asyncio.CancelledError:
            break
        except Exception as e:
            logger.warning("Consumer fetch error: %s", e)
            await asyncio.sleep(1)
            continue

        for msg in msgs:
            try:
                data = json.loads(msg.data.decode("utf-8"))
                reading = MeterReading(**data)

                logger.info(
                    "Parsed reading: %s %s %s %.3f",
                    reading.timestamp,
                    reading.customer,
                    reading.area,
                    reading.power_consumption
                )

                await _process_reading(reading) #Processa

                await msg.ack()
                logger.info("Acked message")
            except (json.JSONDecodeError, ValidationError) as e:
                logger.warning("Bad message, terminating: %s", e)
                await msg.term()
            
            except Exception as e:
                logger.warning("Failed to process message (not acked): %s", e)
                # Lämna ej acknowledged => JetStream kan redelivera

@asynccontextmanager
async def lifespan(_app: FastAPI):
    global _nc, _js, _consumer_task

    logger.info("Starting data processor")

    _nc = await _connect_with_retry()
    _js = _nc.jetstream()
    
    _consumer_task = asyncio.create_task(_consume_messages())

    try:
        yield
    finally:
        logger.info("Shutting down data processor")
        if _consumer_task:
            _consumer_task.cancel()
            try:
                await _consumer_task
            except asyncio.CancelledError:
                pass

        if _nc:
            await _nc.drain()


app = FastAPI(
    title="Data Processor",
    description="Consumes meter readings from NATS",
    version="0.1.0",
    lifespan=lifespan,
)


@app.get("/health", response_model=HealthResponse)
async def health():
    return HealthResponse()


@app.get("/ready", response_model=HealthResponse)
async def ready():
    if _nc is None or not _nc.is_connected:
        raise HTTPException(status_code=503, detail="NATS not connected")
    return HealthResponse()
