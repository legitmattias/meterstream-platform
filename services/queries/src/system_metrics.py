"""System metrics collection for admin dashboard."""

import asyncio
import logging
from datetime import datetime
from typing import Any

import httpx

from .config import settings

logger = logging.getLogger(__name__)

# Service endpoints for health checks (internal K8s DNS)
SERVICES = {
    "ingestion": "http://ingestion:8000/health",
    "auth": "http://auth:8000/health",
    "gateway": "http://gateway:8000/health",
    "influxdb": "http://influxdb:8086/health",
}

# NATS monitoring endpoint - include streams and consumers detail for lag calculation
NATS_MONITORING_URL = "http://nats:8222/jsz?streams=true&consumers=true"


async def fetch_nats_metrics() -> dict[str, Any]:
    """Fetch NATS JetStream metrics from monitoring endpoint."""
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(NATS_MONITORING_URL)
            response.raise_for_status()
            data = response.json()

            # Extract consumer lag from stream details
            consumer_lag = 0
            stream_count = 0
            consumer_count = 0

            # When using ?streams=true, "streams" becomes a list of stream objects
            streams_data = data.get("account_details", [])
            for account in streams_data:
                for stream in account.get("stream_detail", []):
                    stream_count += 1
                    for consumer in stream.get("consumer_detail", []):
                        consumer_count += 1
                        consumer_lag += consumer.get("num_pending", 0)

            # Fallback to summary counts if detail not available
            if stream_count == 0:
                stream_count = data.get("streams", 0)
            if consumer_count == 0:
                consumer_count = data.get("consumers", 0)

            return {
                "status": "healthy",
                "messages": data.get("messages", 0),
                "bytes": data.get("bytes", 0),
                "streams": stream_count,
                "consumers": consumer_count,
                "consumer_lag": consumer_lag,
            }
    except httpx.RequestError as e:
        logger.warning("Failed to fetch NATS metrics: %s", e)
        return {
            "status": "unhealthy",
            "messages": 0,
            "bytes": 0,
            "streams": 0,
            "consumers": 0,
            "consumer_lag": 0,
            "error": str(e),
        }
    except Exception as e:
        logger.error("Unexpected error fetching NATS metrics: %s", e)
        return {
            "status": "error",
            "messages": 0,
            "bytes": 0,
            "streams": 0,
            "consumers": 0,
            "consumer_lag": 0,
            "error": str(e),
        }


async def check_service_health(service_name: str, url: str) -> dict[str, Any]:
    """Check health of a single service."""
    start_time = datetime.utcnow()
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(url)
            latency_ms = (datetime.utcnow() - start_time).total_seconds() * 1000

            return {
                "status": "healthy" if response.status_code == 200 else "unhealthy",
                "latency_ms": round(latency_ms, 1),
                "status_code": response.status_code,
            }
    except httpx.RequestError as e:
        latency_ms = (datetime.utcnow() - start_time).total_seconds() * 1000
        logger.warning("Health check failed for %s: %s", service_name, e)
        return {
            "status": "unhealthy",
            "latency_ms": round(latency_ms, 1),
            "error": str(e),
        }


async def check_all_services() -> dict[str, dict[str, Any]]:
    """Check health of all services concurrently."""
    tasks = {
        name: check_service_health(name, url)
        for name, url in SERVICES.items()
    }

    results = {}
    for name, task in tasks.items():
        results[name] = await task

    return results


async def get_pipeline_stats() -> dict[str, Any]:
    """Get pipeline statistics from InfluxDB."""
    try:
        from .influx import get_influx_client

        client = get_influx_client()
        query_api = client.query_api()

        # Count total data points
        total_query = f'''
        from(bucket: "{settings.influx_bucket}")
          |> range(start: 2020-01-01T00:00:00Z)
          |> filter(fn: (r) => r._measurement == "{settings.influx_measurement}")
          |> group()
          |> count()
        '''

        total_tables = query_api.query(total_query, org=settings.influx_org)
        total_processed = 0
        for table in total_tables:
            for record in table.records:
                total_processed = record.get_value() or 0

        # Count last hour
        hour_query = f'''
        from(bucket: "{settings.influx_bucket}")
          |> range(start: -1h)
          |> filter(fn: (r) => r._measurement == "{settings.influx_measurement}")
          |> group()
          |> count()
        '''

        hour_tables = query_api.query(hour_query, org=settings.influx_org)
        last_hour = 0
        for table in hour_tables:
            for record in table.records:
                last_hour = record.get_value() or 0

        return {
            "total_processed": total_processed,
            "last_hour": last_hour,
        }
    except Exception as e:
        logger.error("Failed to get pipeline stats: %s", e)
        return {
            "total_processed": 0,
            "last_hour": 0,
            "error": str(e),
        }


async def collect_all_metrics() -> dict[str, Any]:
    """Collect all system metrics."""
    # Run all metric collections concurrently
    nats_task = fetch_nats_metrics()
    services_task = check_all_services()
    pipeline_task = get_pipeline_stats()

    nats_metrics, services_health, pipeline_stats = await asyncio.gather(
        nats_task, services_task, pipeline_task
    )

    return {
        "nats": nats_metrics,
        "services": services_health,
        "pipeline": pipeline_stats,
        "timestamp": datetime.utcnow().isoformat() + "Z",
    }
