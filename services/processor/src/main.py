"""Data Processing Service - retrieves and processes meter readings from NATS JetStream."""
import asyncio
import json
import logging
from contextlib import asynccontextmanager

import aiohttp
import nats
from fastapi import FastAPI, HTTPException
from pydantic import ValidationError

from src.config import settings
from src.models import HealthResponse, MeterReading

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

_nats_connection = None
_jetstream = None
_consumer_task = None
_http_session: aiohttp.ClientSession | None = None


async def _connect_with_retry():
    """Connect to NATS (retry until it works)."""
    while True:
        try:
            return await nats.connect(settings.nats_url)
        except asyncio.CancelledError:
            raise
        except Exception as e:
            logger.warning("Failed to connect to NATS: %s. Retrying...", e)
            await asyncio.sleep(1)


async def _create_subscription_with_retry():
    """Create pull subscription (retry until it works)."""
    while True:
        try:
            return await _jetstream.pull_subscribe(
                subject=settings.nats_subject,
                durable="dataprocessor",
                stream=settings.nats_stream,
            )
        except asyncio.CancelledError:
            raise
        except Exception as e:
            logger.warning("Failed to subscribe: %s. Retrying...", e)
            await asyncio.sleep(1)


def _escape_tag_value(value: str) -> str:
    """Escape special characters for InfluxDB line protocol tags.

    In line protocol, tag values must escape: backslash, space, comma, equals.
    """
    return (value
            .replace("\\", "\\\\")
            .replace(" ", "\\ ")
            .replace(",", "\\,")
            .replace("=", "\\="))


def _to_influx_line_protocol(reading: MeterReading) -> str:
    """Convert MeterReading -> Influx line protocol."""
    timestamp_nanoseconds = int(reading.timestamp.timestamp() * 1_000_000_000)
    customer = _escape_tag_value(reading.customer)
    area = _escape_tag_value(reading.area)

    return (
        f"{settings.influx_measurement},customer={customer},area={area} "
        f"power_consumption={float(reading.power_consumption)} {timestamp_nanoseconds}"
    )


async def _write_line_to_influxdb(line: str) -> None:
    """Write one line to InfluxDB."""
    if _http_session is None:
        raise RuntimeError("HTTP client not initialized")
    if not settings.influx_token:
        raise RuntimeError("Missing INFLUX_TOKEN (settings.influx_token)")

    url = settings.influx_url.rstrip("/") + "/api/v2/write"
    params = {
        "org": settings.influx_org,
        "bucket": settings.influx_bucket,
        "precision": "ns",
    }
    headers = {"Authorization": f"Token {settings.influx_token}"}

    async with _http_session.post(url, params=params, data=line + "\n", headers=headers) as resp:
        if resp.status >= 300:
            text = await resp.text()
            raise RuntimeError(f"Influx write failed: {resp.status} {text}")


async def _process_reading(reading: MeterReading) -> None:
    """Process one reading and write to InfluxDB."""
    line = _to_influx_line_protocol(reading)
    await _write_line_to_influxdb(line)


async def _consume_messages() -> None:
    """Main method - NATS consumer loop."""
    subscription = await _create_subscription_with_retry()

    while True:
        try:
            messages = await subscription.fetch(batch=50, timeout=1)
        except nats.errors.TimeoutError:
            continue
        except asyncio.CancelledError:
            break
        except Exception as e:
            logger.warning("Consumer fetch error: %s", e)
            await asyncio.sleep(1)
            continue

        for message in messages:
            try:
                payload = json.loads(message.data.decode("utf-8"))
                reading = MeterReading(**payload)

                logger.info(
                    "Parsed reading: %s %s %s %.6f",
                    reading.timestamp,
                    reading.customer,
                    reading.area,
                    reading.power_consumption,
                )

                await _process_reading(reading)

                await message.ack()
                logger.info("Acked message")

            except (json.JSONDecodeError, ValidationError) as e:
                logger.warning("Bad message, terminating: %s", e)
                await message.term()

            except Exception as e:
                logger.warning("Failed to process/write (not acked): %s", e)


@asynccontextmanager
async def lifespan(_app: FastAPI):
    global _nats_connection, _jetstream, _consumer_task, _http_session

    logger.info("Starting data processor")

    _http_session = aiohttp.ClientSession()
    _nats_connection = await _connect_with_retry()
    _jetstream = _nats_connection.jetstream()

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

        if _nats_connection:
            await _nats_connection.drain()

        if _http_session:
            await _http_session.close()


app = FastAPI(
    title="Data Processor",
    description="Consumes meter readings from NATS and writes to InfluxDB",
    version="0.1.0",
    lifespan=lifespan,
)


@app.get("/health", response_model=HealthResponse)
async def health():
    return HealthResponse()


@app.get("/ready", response_model=HealthResponse)
async def ready():
    if _nats_connection is None or not _nats_connection.is_connected:
        raise HTTPException(status_code=503, detail="NATS not connected")
    return HealthResponse()
