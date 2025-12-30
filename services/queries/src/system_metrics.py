"""System metrics collection for admin dashboard."""

import asyncio
import logging
from datetime import datetime
from typing import Any

import httpx

from .config import settings

logger = logging.getLogger(__name__)

# Service endpoints for health checks (internal K8s DNS)
# Ordered by pipeline flow: Gateway -> Auth -> Ingestion -> NATS -> Processor -> InfluxDB -> Grafana -> Portal
SERVICES = {
    "gateway": "http://gateway:8000/health",
    "auth": "http://auth:8000/health",
    "ingestion": "http://ingestion:8000/health",
    "processor": "http://processor:8000/health",
    "influxdb": "http://influxdb:8086/health",
    "grafana": "http://grafana:3000/api/health",
    "portal": "http://portal:80",
}
# Note: MongoDB has no HTTP health endpoint (requires pymongo)
# Note: Queries service can't check itself (circular dependency)

# NATS monitoring endpoint - include streams and consumers detail for lag calculation
NATS_MONITORING_URL = "http://nats:8222/jsz?streams=true&consumers=true"


async def fetch_nats_metrics() -> dict[str, Any]:
    """Fetch NATS JetStream metrics from monitoring endpoint."""
    start_time = datetime.utcnow()
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(NATS_MONITORING_URL)
            latency_ms = (datetime.utcnow() - start_time).total_seconds() * 1000
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
                "latency_ms": round(latency_ms, 1),
                "messages": data.get("messages", 0),
                "bytes": data.get("bytes", 0),
                "streams": stream_count,
                "consumers": consumer_count,
                "consumer_lag": consumer_lag,
            }
    except httpx.RequestError as e:
        latency_ms = (datetime.utcnow() - start_time).total_seconds() * 1000
        logger.warning("Failed to fetch NATS metrics: %s", e)
        return {
            "status": "unhealthy",
            "latency_ms": round(latency_ms, 1),
            "messages": 0,
            "bytes": 0,
            "streams": 0,
            "consumers": 0,
            "consumer_lag": 0,
            "error": str(e),
        }
    except Exception as e:
        latency_ms = (datetime.utcnow() - start_time).total_seconds() * 1000
        logger.error("Unexpected error fetching NATS metrics: %s", e)
        return {
            "status": "error",
            "latency_ms": round(latency_ms, 1),
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


async def get_storage_stats() -> dict[str, Any]:
    """Get data storage and replication statistics.

    Fetches replication stats from the write instance to show:
    - Current replication queue size
    - Bytes remaining to sync
    - Sync status (based on latest response code)
    """
    try:
        # Fetch replication stats from write instance
        if not settings.influx_write_token:
            logger.warning("Write instance token not configured, skipping replication stats")
            return {
                "replication_queue_bytes": 0,
                "replication_remaining_bytes": 0,
                "replication_status": "not_configured",
                "replication_max_queue_bytes": 0,
            }

        async with httpx.AsyncClient(timeout=5.0) as client:
            # Get org ID if not configured (replication API requires org ID, not name)
            org_id = settings.influx_write_org_id
            if not org_id:
                orgs_response = await client.get(
                    f"{settings.influx_write_url}/api/v2/orgs",
                    headers={"Authorization": f"Token {settings.influx_write_token}"},
                )
                orgs_response.raise_for_status()
                orgs_data = orgs_response.json()
                orgs = orgs_data.get("orgs", [])
                if not orgs:
                    logger.warning("No organizations found on write instance")
                    return {
                        "replication_queue_bytes": 0,
                        "replication_remaining_bytes": 0,
                        "replication_status": "no_org",
                        "replication_max_queue_bytes": 0,
                    }
                org_id = orgs[0].get("id", "")

            response = await client.get(
                f"{settings.influx_write_url}/api/v2/replications",
                params={"orgID": org_id},
                headers={"Authorization": f"Token {settings.influx_write_token}"},
            )
            response.raise_for_status()
            data = response.json()

            replications = data.get("replications", [])
            if not replications:
                return {
                    "replication_queue_bytes": 0,
                    "replication_remaining_bytes": 0,
                    "replication_status": "no_replication",
                    "replication_max_queue_bytes": 0,
                }

            # Use the first replication (we only have one)
            repl = replications[0]
            status_code = repl.get("latestResponseCode", 0)

            # Determine sync status
            if status_code == 204:
                sync_status = "syncing"
            elif status_code == 0:
                sync_status = "initializing"
            else:
                sync_status = "error"

            return {
                "replication_queue_bytes": repl.get("currentQueueSizeBytes", 0),
                "replication_remaining_bytes": repl.get("remainingBytesToBeSynced", 0),
                "replication_status": sync_status,
                "replication_max_queue_bytes": repl.get("maxQueueSizeBytes", 0),
            }

    except httpx.RequestError as e:
        logger.warning("Failed to fetch replication stats: %s", e)
        return {
            "replication_queue_bytes": 0,
            "replication_remaining_bytes": 0,
            "replication_status": "unreachable",
            "replication_max_queue_bytes": 0,
            "error": str(e),
        }
    except Exception as e:
        logger.error("Unexpected error fetching storage stats: %s", e)
        return {
            "replication_queue_bytes": 0,
            "replication_remaining_bytes": 0,
            "replication_status": "error",
            "replication_max_queue_bytes": 0,
            "error": str(e),
        }


async def collect_all_metrics() -> dict[str, Any]:
    """Collect all system metrics."""
    # Run all metric collections concurrently
    nats_task = fetch_nats_metrics()
    services_task = check_all_services()
    storage_task = get_storage_stats()

    nats_metrics, services_health, storage_stats = await asyncio.gather(
        nats_task, services_task, storage_task
    )

    return {
        "nats": nats_metrics,
        "services": services_health,
        "storage": storage_stats,
        "timestamp": datetime.utcnow().isoformat() + "Z",
    }
