"""NATS JetStream client for publishing meter readings."""

import asyncio
import json
import logging
from contextlib import asynccontextmanager

import nats
from nats.js.api import StreamConfig, RetentionPolicy

from .config import settings

logger = logging.getLogger(__name__)


class NATSClient:
    """NATS JetStream client for publishing meter readings."""

    def __init__(self):
        self._nc = None
        self._js = None
        self._connect_task = None

    async def connect(self):
        """Start background connection to NATS (non-blocking)."""
        self._connect_task = asyncio.create_task(self._connect_with_retry())

    async def _connect_with_retry(self):
        """Connect to NATS with retry logic."""
        retry_delay = 1
        max_delay = 30

        while True:
            try:
                logger.info("Connecting to NATS at %s", settings.nats_url)
                self._nc = await nats.connect(settings.nats_url)
                self._js = self._nc.jetstream()

                # Ensure stream exists
                await self._ensure_stream()
                logger.info("Successfully connected to NATS")
                return
            except Exception as e:
                logger.warning(
                    "Failed to connect to NATS: %s. Retrying in %ds...",
                    e, retry_delay
                )
                await asyncio.sleep(retry_delay)
                retry_delay = min(retry_delay * 2, max_delay)

    async def _ensure_stream(self):
        """Create the stream if it doesn't exist."""
        try:
            await self._js.stream_info(settings.nats_stream)
            logger.info("Stream %s already exists", settings.nats_stream)
        except nats.js.errors.NotFoundError:
            logger.info("Creating stream %s", settings.nats_stream)
            await self._js.add_stream(
                config=StreamConfig(
                    name=settings.nats_stream,
                    subjects=[settings.nats_subject],
                    retention=RetentionPolicy.LIMITS,
                    max_bytes=1024 * 1024 * 512,  # 512MB
                    max_age=60 * 60 * 24 * 7,  # 7 days
                )
            )

    async def disconnect(self):
        """Disconnect from NATS."""
        if self._connect_task and not self._connect_task.done():
            self._connect_task.cancel()
            try:
                await self._connect_task
            except asyncio.CancelledError:
                pass
        if self._nc:
            await self._nc.close()
            logger.info("Disconnected from NATS")

    @property
    def is_connected(self) -> bool:
        """Check if connected to NATS."""
        return self._nc is not None and self._nc.is_connected

    async def publish(self, data: dict) -> None:
        """Publish a single reading to JetStream."""
        if not self._js:
            raise RuntimeError("Not connected to NATS")

        payload = json.dumps(data).encode()
        ack = await self._js.publish(settings.nats_subject, payload)
        logger.debug("Published message, seq=%s", ack.seq)

    async def publish_batch(self, readings: list[dict]) -> int:
        """Publish multiple readings to JetStream."""
        count = 0
        for reading in readings:
            await self.publish(reading)
            count += 1
        return count


# Global client instance
nats_client = NATSClient()


@asynccontextmanager
async def lifespan_nats():
    """Context manager for NATS connection lifecycle."""
    await nats_client.connect()
    yield
    await nats_client.disconnect()
