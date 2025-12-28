"""Tests for API Gateway endpoints."""

import time

import pytest
from fastapi.testclient import TestClient
from jose import jwt

from src.config import settings
from src.main import app


def create_test_token(payload: dict) -> str:
    """Helper to create JWT tokens for testing."""
    return jwt.encode(
        payload,
        settings.jwt_secret,
        algorithm=settings.jwt_algorithm,
    )


@pytest.fixture(name="client")
def client_fixture():
    """Create test client with lifespan context."""
    with TestClient(app, raise_server_exceptions=False) as test_client:
        yield test_client


class TestHealthEndpoint:
    """Tests for health check endpoint."""

    def test_health_returns_ok_without_auth(self, client):
        """Test health endpoint returns 200 without authentication."""
        response = client.get("/health")

        assert response.status_code == 200
        assert response.json()["status"] == "ok"


class TestAuthProxy:
    """Tests for auth service proxy (no JWT required)."""

    def test_auth_route_does_not_require_jwt(self, client):
        """Test that /api/auth routes don't require JWT validation."""
        response = client.post("/api/auth/login", json={
            "username": "test",
            "password": "test",
        })

        # 502 means gateway tried to proxy (no auth failure).
        # If JWT was required, response would be 401.
        assert response.status_code == 502


class TestIngestProxy:
    """Tests for ingestion service proxy (JWT required, role restricted)."""

    def test_missing_token_returns_401(self, client):
        """Test that request without token returns 401."""
        response = client.post("/api/ingest", json={"readings": []})

        assert response.status_code == 401

    def test_invalid_token_returns_401(self, client):
        """Test that malformed token returns 401."""
        response = client.post(
            "/api/ingest",
            json={"readings": []},
            headers={"Authorization": "Bearer invalid-token"},
        )

        assert response.status_code == 401

    def test_expired_token_returns_401(self, client):
        """Test that expired token returns 401."""
        exp = int(time.time()) - 3600  # 1 hour ago
        token = create_test_token({"sub": "user-123", "exp": exp})

        response = client.post(
            "/api/ingest",
            json={"readings": []},
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 401

    def test_customer_role_returns_403(self, client):
        """Test that customer role cannot ingest data."""
        exp = int(time.time()) + 3600
        token = create_test_token({
            "sub": "user-123",
            "role": "customer",
            "exp": exp,
        })

        response = client.post(
            "/api/ingest",
            json={"readings": []},
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 403
        assert "device, admin, or internal" in response.json()["detail"]

    def test_device_role_allows_ingest(self, client):
        """Test that device role can ingest data."""
        exp = int(time.time()) + 3600
        token = create_test_token({
            "sub": "device-123",
            "role": "device",
            "exp": exp,
        })

        response = client.post(
            "/api/ingest",
            json={"readings": []},
            headers={"Authorization": f"Bearer {token}"},
        )

        # 502 means auth passed and gateway tried to reach backend
        assert response.status_code == 502

    def test_internal_role_allows_ingest(self, client):
        """Test that internal role can ingest data."""
        exp = int(time.time()) + 3600
        token = create_test_token({
            "sub": "staff-123",
            "role": "internal",
            "exp": exp,
        })

        response = client.post(
            "/api/ingest",
            json={"readings": []},
            headers={"Authorization": f"Bearer {token}"},
        )

        # 502 means auth passed and gateway tried to reach backend
        assert response.status_code == 502

    def test_admin_role_allows_ingest(self, client):
        """Test that admin role can ingest data."""
        exp = int(time.time()) + 3600
        token = create_test_token({
            "sub": "admin-123",
            "role": "admin",
            "exp": exp,
        })

        response = client.post(
            "/api/ingest",
            json={"readings": []},
            headers={"Authorization": f"Bearer {token}"},
        )

        # 502 means auth passed and gateway tried to reach backend
        assert response.status_code == 502


class TestGrafanaProxy:
    """Tests for Grafana proxy (JWT required)."""

    def test_missing_token_returns_401(self, client):
        """Test that request without token returns 401."""
        response = client.get("/api/grafana/")

        assert response.status_code == 401

    def test_invalid_token_returns_401(self, client):
        """Test that malformed token returns 401."""
        response = client.get(
            "/api/grafana/",
            headers={"Authorization": "Bearer invalid-token"},
        )

        assert response.status_code == 401

    def test_valid_token_allows_proxy(self, client):
        """Test that valid token passes auth and attempts to proxy."""
        exp = int(time.time()) + 3600
        token = create_test_token({
            "sub": "user-123",
            "role": "customer",
            "exp": exp,
        })

        response = client.get(
            "/api/grafana/",
            headers={"Authorization": f"Bearer {token}"},
        )

        # 502 means auth passed and gateway tried to reach Grafana
        assert response.status_code == 502

    def test_valid_token_with_path(self, client):
        """Test that Grafana subpaths work with valid token."""
        exp = int(time.time()) + 3600
        token = create_test_token({
            "sub": "user-123",
            "role": "admin",
            "exp": exp,
        })

        response = client.get(
            "/api/grafana/d/dashboard-id/my-dashboard",
            headers={"Authorization": f"Bearer {token}"},
        )

        # 502 means auth passed and gateway tried to reach Grafana
        assert response.status_code == 502


class TestHeaderSecurity:
    """Tests for header security (preventing header injection attacks)."""

    def test_client_cannot_inject_user_headers(self, client):
        """Test that client-provided X-User-* headers don't bypass auth.

        Malicious clients might try to inject X-User-ID headers to
        impersonate other users. The gateway must strip these headers
        and only set them from validated JWT claims.
        """
        exp = int(time.time()) + 3600
        token = create_test_token({"sub": "real-user", "role": "device", "exp": exp})

        # Attempt to inject fake admin headers
        response = client.post(
            "/api/ingest",
            json={"readings": []},
            headers={
                "Authorization": f"Bearer {token}",
                "X-User-ID": "fake-admin",
                "X-User-Role": "admin",
            },
        )

        # Request proceeds to proxy stage (502), meaning:
        # 1. Auth passed (token was valid)
        # 2. Injected headers didn't cause auth to use fake identity
        # Note: Full verification that headers are stripped requires
        # integration testing with a real backend.
        assert response.status_code == 502
