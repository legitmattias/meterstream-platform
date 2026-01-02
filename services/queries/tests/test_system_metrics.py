"""Tests for system metrics collection."""

from unittest.mock import AsyncMock, patch, MagicMock

import pytest
import httpx

from src.system_metrics import (
    fetch_nats_metrics,
    check_service_health,
    get_storage_stats,
)


@pytest.mark.asyncio
class TestFetchNatsMetrics:
    async def test_returns_healthy_on_success(self):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.raise_for_status = MagicMock()
        mock_response.json.return_value = {
            "messages": 1000,
            "bytes": 50000,
            "streams": 2,
            "consumers": 3,
        }

        with patch("src.system_metrics.httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                return_value=mock_response
            )
            result = await fetch_nats_metrics()

        assert result["status"] == "healthy"
        assert result["messages"] == 1000
        assert result["bytes"] == 50000
        assert "latency_ms" in result

    async def test_returns_unhealthy_on_request_error(self):
        with patch("src.system_metrics.httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                side_effect=httpx.RequestError("Connection failed")
            )
            result = await fetch_nats_metrics()

        assert result["status"] == "unhealthy"
        assert "error" in result

    async def test_extracts_consumer_lag_from_details(self):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.raise_for_status = MagicMock()
        mock_response.json.return_value = {
            "messages": 100,
            "bytes": 5000,
            "account_details": [
                {
                    "stream_detail": [
                        {
                            "consumer_detail": [
                                {"num_pending": 10},
                                {"num_pending": 5},
                            ]
                        }
                    ]
                }
            ],
        }

        with patch("src.system_metrics.httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                return_value=mock_response
            )
            result = await fetch_nats_metrics()

        assert result["consumer_lag"] == 15
        assert result["streams"] == 1
        assert result["consumers"] == 2


@pytest.mark.asyncio
class TestCheckServiceHealth:
    async def test_healthy_on_200(self):
        mock_response = MagicMock()
        mock_response.status_code = 200

        with patch("src.system_metrics.httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                return_value=mock_response
            )
            result = await check_service_health("test-service", "http://test:8000/health")

        assert result["status"] == "healthy"
        assert result["status_code"] == 200
        assert "latency_ms" in result

    async def test_unhealthy_on_non_200(self):
        mock_response = MagicMock()
        mock_response.status_code = 503

        with patch("src.system_metrics.httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                return_value=mock_response
            )
            result = await check_service_health("test-service", "http://test:8000/health")

        assert result["status"] == "unhealthy"
        assert result["status_code"] == 503

    async def test_unhealthy_on_connection_error(self):
        with patch("src.system_metrics.httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                side_effect=httpx.RequestError("Connection refused")
            )
            result = await check_service_health("test-service", "http://test:8000/health")

        assert result["status"] == "unhealthy"
        assert "error" in result


@pytest.mark.asyncio
class TestGetStorageStats:
    async def test_not_configured_without_token(self):
        with patch("src.system_metrics.settings") as mock_settings:
            mock_settings.influx_write_token = ""
            result = await get_storage_stats()

        assert result["replication_status"] == "not_configured"

    async def test_syncing_status_on_204(self):
        mock_orgs_response = MagicMock()
        mock_orgs_response.raise_for_status = MagicMock()
        mock_orgs_response.json.return_value = {"orgs": [{"id": "org123"}]}

        mock_repl_response = MagicMock()
        mock_repl_response.raise_for_status = MagicMock()
        mock_repl_response.json.return_value = {
            "replications": [
                {
                    "latestResponseCode": 204,
                    "currentQueueSizeBytes": 1024,
                    "remainingBytesToBeSynced": 512,
                    "maxQueueSizeBytes": 10240,
                }
            ]
        }

        with patch("src.system_metrics.settings") as mock_settings:
            mock_settings.influx_write_token = "test-token"
            mock_settings.influx_write_org_id = ""
            mock_settings.influx_write_url = "http://influxdb:8086"

            with patch("src.system_metrics.httpx.AsyncClient") as mock_client:
                mock_instance = mock_client.return_value.__aenter__.return_value
                mock_instance.get = AsyncMock(
                    side_effect=[mock_orgs_response, mock_repl_response]
                )
                result = await get_storage_stats()

        assert result["replication_status"] == "syncing"
        assert result["replication_queue_bytes"] == 1024
        assert result["replication_remaining_bytes"] == 512

    async def test_no_replication_when_empty(self):
        mock_orgs_response = MagicMock()
        mock_orgs_response.raise_for_status = MagicMock()
        mock_orgs_response.json.return_value = {"orgs": [{"id": "org123"}]}

        mock_repl_response = MagicMock()
        mock_repl_response.raise_for_status = MagicMock()
        mock_repl_response.json.return_value = {"replications": []}

        with patch("src.system_metrics.settings") as mock_settings:
            mock_settings.influx_write_token = "test-token"
            mock_settings.influx_write_org_id = ""
            mock_settings.influx_write_url = "http://influxdb:8086"

            with patch("src.system_metrics.httpx.AsyncClient") as mock_client:
                mock_instance = mock_client.return_value.__aenter__.return_value
                mock_instance.get = AsyncMock(
                    side_effect=[mock_orgs_response, mock_repl_response]
                )
                result = await get_storage_stats()

        assert result["replication_status"] == "no_replication"

    async def test_unreachable_on_request_error(self):
        with patch("src.system_metrics.settings") as mock_settings:
            mock_settings.influx_write_token = "test-token"
            mock_settings.influx_write_org_id = "org123"
            mock_settings.influx_write_url = "http://influxdb:8086"

            with patch("src.system_metrics.httpx.AsyncClient") as mock_client:
                mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                    side_effect=httpx.RequestError("Connection failed")
                )
                result = await get_storage_stats()

        assert result["replication_status"] == "unreachable"
        assert "error" in result
