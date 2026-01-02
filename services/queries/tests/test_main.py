"""Tests for query service main module."""

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

from src.main import app, get_customer_id


client = TestClient(app)


class TestGetCustomerId:
    def test_returns_customer_id_when_provided(self):
        result = get_customer_id(x_customer_id="CUST123", x_user_role=None)
        assert result == "CUST123"

    def test_returns_none_for_admin_role(self):
        result = get_customer_id(x_customer_id=None, x_user_role="admin")
        assert result is None

    def test_returns_none_for_internal_role(self):
        result = get_customer_id(x_customer_id=None, x_user_role="internal")
        assert result is None

    def test_admin_role_case_insensitive(self):
        result = get_customer_id(x_customer_id=None, x_user_role="Admin")
        assert result is None

    def test_raises_403_when_no_customer_id_and_no_role(self):
        with pytest.raises(HTTPException) as exc_info:
            get_customer_id(x_customer_id=None, x_user_role=None)
        assert exc_info.value.status_code == 403

    def test_raises_403_for_regular_user_without_customer_id(self):
        with pytest.raises(HTTPException) as exc_info:
            get_customer_id(x_customer_id=None, x_user_role="user")
        assert exc_info.value.status_code == 403

    def test_customer_id_takes_precedence_over_role(self):
        result = get_customer_id(x_customer_id="CUST456", x_user_role="admin")
        assert result == "CUST456"


class TestHealthEndpoint:
    def test_health_returns_ok(self):
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}


class TestSystemMetricsEndpoint:
    def test_requires_admin_role(self):
        response = client.get("/api/system/metrics")
        assert response.status_code == 403

    def test_rejects_non_admin_role(self):
        response = client.get("/api/system/metrics", headers={"X-User-Role": "user"})
        assert response.status_code == 403
