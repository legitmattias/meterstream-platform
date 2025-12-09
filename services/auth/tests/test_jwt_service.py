"""Tests for JWT service functions."""

import pytest
from datetime import datetime, timedelta

from src.jwt_service import (
    hash_password,
    verify_password,
    create_access_token,
    verify_token
)


class TestPasswordHashing:
    """Tests for password hashing functions."""

    def test_hash_password(self):
        """Test that password is hashed."""
        password = "securepass123"
        hashed = hash_password(password)

        assert hashed != password
        assert len(hashed) > 20  # Bcrypt hashes are long
        assert hashed.startswith("$2b$")  # Bcrypt prefix

    def test_verify_password_correct(self):
        """Test verifying correct password."""
        password = "securepass123"
        hashed = hash_password(password)

        assert verify_password(password, hashed) is True

    def test_verify_password_incorrect(self):
        """Test verifying incorrect password."""
        password = "securepass123"
        hashed = hash_password(password)

        assert verify_password("wrongpassword", hashed) is False

    def test_same_password_different_hashes(self):
        """Test that same password produces different hashes (salt)."""
        password = "securepass123"
        hash1 = hash_password(password)
        hash2 = hash_password(password)

        assert hash1 != hash2
        assert verify_password(password, hash1) is True
        assert verify_password(password, hash2) is True


class TestJWTTokens:
    """Tests for JWT token functions."""

    def test_create_access_token(self):
        """Test creating an access token."""
        user_id = "507f1f77bcf86cd799439011"
        email = "test@example.com"
        role = "user"

        token, expires_in = create_access_token(user_id, email, role)

        assert isinstance(token, str)
        assert len(token) > 50  # JWT tokens are long
        assert isinstance(expires_in, int)
        assert expires_in > 0

    def test_verify_valid_token(self):
        """Test verifying a valid token."""
        user_id = "507f1f77bcf86cd799439011"
        email = "test@example.com"
        role = "user"

        token, _ = create_access_token(user_id, email, role)
        payload = verify_token(token)

        assert payload is not None
        assert payload["user_id"] == user_id
        assert payload["email"] == email
        assert payload["role"] == role

    def test_verify_invalid_token(self):
        """Test verifying an invalid token."""
        invalid_token = "invalid.token.here"
        payload = verify_token(invalid_token)

        assert payload is None

    def test_verify_tampered_token(self):
        """Test verifying a tampered token."""
        user_id = "507f1f77bcf86cd799439011"
        email = "test@example.com"
        role = "user"

        token, _ = create_access_token(user_id, email, role)
        tampered_token = token[:-5] + "XXXXX"
        payload = verify_token(tampered_token)

        assert payload is None

    def test_token_expiration(self):
        """Test that token expiration is set correctly."""
        user_id = "507f1f77bcf86cd799439011"
        email = "test@example.com"
        role = "user"

        _, expires_in = create_access_token(user_id, email, role)

        # Should be around 60 minutes (3600 seconds) by default
        assert expires_in == 3600
