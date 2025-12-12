"""Tests for Pydantic models."""

from datetime import datetime, UTC
import pytest

from src.models import (
    UserRegister,
    UserLogin,
    UserResponse,
    VerifyResponse,
    UserInDB
)


class TestUserRegister:
    """Tests for UserRegister model."""

    def test_valid_user_register(self):
        """Test creating a valid user registration."""
        user = UserRegister(
            email="test@example.com",
            password="securepass123",
            name="Test User"
        )
        assert user.email == "test@example.com"
        assert user.password == "securepass123"
        assert user.name == "Test User"

    def test_invalid_email(self):
        """Test that invalid email raises error."""
        with pytest.raises(Exception):
            UserRegister(
                email="not-an-email",
                password="securepass123",
                name="Test User"
            )

    def test_password_too_short(self):
        """Test that password shorter than 8 chars raises error."""
        with pytest.raises(Exception):
            UserRegister(
                email="test@example.com",
                password="short",
                name="Test User"
            )

    def test_name_too_short(self):
        """Test that name shorter than 2 chars raises error."""
        with pytest.raises(Exception):
            UserRegister(
                email="test@example.com",
                password="securepass123",
                name="A"
            )


class TestUserLogin:
    """Tests for UserLogin model."""

    def test_valid_user_login(self):
        """Test creating a valid user login."""
        login = UserLogin(
            email="test@example.com",
            password="securepass123"
        )
        assert login.email == "test@example.com"
        assert login.password == "securepass123"


class TestUserResponse:
    """Tests for UserResponse model."""

    def test_valid_user_response(self):
        """Test creating a valid user response."""
        response = UserResponse(
            id="507f1f77bcf86cd799439011",
            email="test@example.com",
            name="Test User",
            created_at=datetime.now(UTC),
            role="customer"
        )
        assert response.id == "507f1f77bcf86cd799439011"
        assert response.email == "test@example.com"
        assert response.role == "customer"


# class TestTokenResponse:
#     """Tests for TokenResponse model."""

#     def test_valid_token_response(self):
#         """Test creating a valid token response."""
#         response = TokenResponse(
#             access_token="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
#             token_type="bearer",
#             expires_in=3600
#         )
#         assert response.access_token == "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
#         assert response.token_type == "bearer"
#         assert response.expires_in == 3600


class TestVerifyResponse:
    """Tests for VerifyResponse model."""

    def test_valid_verify_response(self):
        """Test creating a valid verify response."""
        response = VerifyResponse(
            valid=True,
            user_id="507f1f77bcf86cd799439011",
            email="test@example.com",
            role="customer"
        )
        assert response.valid is True
        assert response.user_id == "507f1f77bcf86cd799439011"

    def test_invalid_verify_response(self):
        """Test creating an invalid verify response."""
        response = VerifyResponse(valid=False)
        assert response.valid is False
        assert response.user_id is None
        assert response.email is None
