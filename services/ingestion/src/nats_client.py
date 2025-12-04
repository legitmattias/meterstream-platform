"""NATS JetStream client for publishing meter readings."""

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

    async def connect(self):
        """Connect to NATS and set up JetStream."""
        logger.info("Connecting to NATS at %s", settings.nats_url)
        self._nc = await nats.connect(settings.nats_url)
        self._js = self._nc.jetstream()

        # Ensure stream exists
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
