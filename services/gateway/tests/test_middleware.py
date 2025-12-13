"""Tests for JWT validation middleware."""

import time

import pytest
from fastapi import HTTPException
from jose import jwt

from src.config import settings
from src.middleware import TokenPayload, decode_token, extract_token_from_header


def create_test_token(payload: dict, secret: str = None) -> str:
    """Helper to create JWT tokens for testing."""
    return jwt.encode(
        payload,
        secret or settings.jwt_secret,
        algorithm=settings.jwt_algorithm,
    )


class TestDecodeToken:
    """Tests for JWT token decoding."""

    def test_valid_token_with_all_claims(self):
        """Test decoding a token with all expected claims."""
        exp = int(time.time()) + 3600
        token = create_test_token({
            "sub": "user-123",
            "role": "customer",
            "customer_id": "cust-456",
            "exp": exp,
        })

        payload = decode_token(token)

        assert payload.sub == "user-123"
        assert payload.role == "customer"
        assert payload.customer_id == "cust-456"

    def test_valid_token_with_minimal_claims(self):
        """Test decoding a token with only required claims."""
        exp = int(time.time()) + 3600
        token = create_test_token({"sub": "user-123", "exp": exp})

        payload = decode_token(token)

        assert payload.sub == "user-123"
        assert payload.role is None
        assert payload.customer_id is None

    def test_expired_token_raises_401(self):
        """Test that expired token raises HTTPException with 401."""
        exp = int(time.time()) - 3600  # 1 hour ago
        token = create_test_token({"sub": "user-123", "exp": exp})

        with pytest.raises(HTTPException) as exc_info:
            decode_token(token)

        assert exc_info.value.status_code == 401

    def test_wrong_signature_raises_401(self):
        """Test that token signed with wrong secret raises 401."""
        exp = int(time.time()) + 3600
        token = create_test_token(
            {"sub": "user-123", "exp": exp},
            secret="wrong-secret",
        )

        with pytest.raises(HTTPException) as exc_info:
            decode_token(token)

        assert exc_info.value.status_code == 401

    def test_malformed_token_raises_401(self):
        """Test that malformed token string raises 401."""
        with pytest.raises(HTTPException) as exc_info:
            decode_token("not.a.valid.token")

        assert exc_info.value.status_code == 401


class TestExtractTokenFromHeader:
    """Tests for Authorization header parsing."""

    class MockRequest:
        """Mock FastAPI request object for testing."""

        def __init__(self, headers: dict):
            self.headers = headers

    def test_extracts_token_from_bearer_header(self):
        """Test extracting token from valid Bearer header."""
        request = self.MockRequest({"Authorization": "Bearer abc123"})

        token = extract_token_from_header(request)

        assert token == "abc123"

    def test_bearer_prefix_is_case_insensitive(self):
        """Test that 'bearer' prefix works regardless of case."""
        request = self.MockRequest({"Authorization": "bearer abc123"})

        token = extract_token_from_header(request)

        assert token == "abc123"

    def test_missing_header_raises_401(self):
        """Test that missing Authorization header raises 401."""
        request = self.MockRequest({})

        with pytest.raises(HTTPException) as exc_info:
            extract_token_from_header(request)

        assert exc_info.value.status_code == 401
        assert "Missing" in exc_info.value.detail

    def test_non_bearer_scheme_raises_401(self):
        """Test that non-Bearer auth schemes raise 401."""
        request = self.MockRequest({"Authorization": "Basic abc123"})

        with pytest.raises(HTTPException) as exc_info:
            extract_token_from_header(request)

        assert exc_info.value.status_code == 401
        assert "Invalid" in exc_info.value.detail

    def test_bearer_without_token_raises_401(self):
        """Test that 'Bearer' without token value raises 401."""
        request = self.MockRequest({"Authorization": "Bearer"})

        with pytest.raises(HTTPException) as exc_info:
            extract_token_from_header(request)

        assert exc_info.value.status_code == 401


class TestTokenPayload:
    """Tests for TokenPayload Pydantic model."""

    def test_accepts_all_fields(self):
        """Test model accepts all defined fields."""
        payload = TokenPayload(
            sub="user-123",
            role="admin",
            customer_id="cust-456",
            exp=1234567890,
        )

        assert payload.sub == "user-123"
        assert payload.role == "admin"
        assert payload.customer_id == "cust-456"
        assert payload.exp == 1234567890

    def test_optional_fields_default_to_none(self):
        """Test that role and customer_id are optional."""
        payload = TokenPayload(sub="user-123", exp=1234567890)

        assert payload.role is None
        assert payload.customer_id is None
