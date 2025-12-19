"""Tests for Auth service endpoints with mocked MongoDB."""

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, UTC
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from src.auth_router import router as auth_router
from src.jwt_service import create_access_token
from src.mongodb import get_users_collection
from src.models import HealthResponse
from src.config import get_settings

settings = get_settings()


# Create an app without lifespan for testing
app_for_testing = FastAPI(title="Test Auth Service")

# Add rate limiting (required by auth_router)
limiter = Limiter(key_func=get_remote_address)
app_for_testing.state.limiter = limiter
app_for_testing.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app_for_testing.include_router(auth_router)


@app_for_testing.get("/")
async def root():
    """Root endpoint."""
    return {
        "service": settings.service_name,
        "docs": "/docs",
        "api-calls": "/auth/",
        "health": "/health"
    }


@app_for_testing.get("/health")
async def health(response_model=HealthResponse):
    """Liveness probe."""
    return HealthResponse()


@pytest.fixture
def mock_users_collection():
    """Mock users collection."""
    collection = AsyncMock()
    # Set default return values
    collection.find_one = AsyncMock(return_value=None)
    collection.insert_one = AsyncMock()
    collection.update_one = AsyncMock()
    return collection


@pytest.fixture
def client(mock_users_collection):
    """Test client with mocked database dependency."""
    # Create async function that returns the mock collection
    async def get_mock_users_collection():
        return mock_users_collection

    # Override the dependency
    app_for_testing.dependency_overrides[get_users_collection] = get_mock_users_collection

    # Create test client
    with TestClient(app_for_testing, raise_server_exceptions=False) as test_client:
        yield test_client

    # Clean up
    app_for_testing.dependency_overrides.clear()


class TestHealthEndpoints:
    """Tests for health check endpoints."""

    def test_health_returns_ok(self, client):
        """Test health endpoint returns 200."""
        response = client.get("/health")

        assert response.status_code == 200
        assert response.json()["status"] == "ok"

    def test_root_returns_service_info(self, client):
        """Test root endpoint returns service information."""
        response = client.get("/")

        assert response.status_code == 200
        data = response.json()
        assert "service" in data
        assert "docs" in data
        assert "health" in data


class TestRegistrationEndpoint:
    """Tests for user registration."""

    def test_register_new_user_success(self, client, mock_users_collection):
        """Test successful user registration."""
        # Setup: User doesn't exist
        mock_users_collection.find_one.return_value = None
        mock_users_collection.insert_one.return_value = MagicMock(inserted_id="new-user-id")

        # Execute
        response = client.post("/auth/register", json={
            "email": "newuser@example.com",
            "password": "SecurePass123!",
            "name": "New User",
        })

        # Assert
        assert response.status_code == 201
        data = response.json()
        assert "id" in data
        assert data["id"] == "new-user-id"
        assert data["email"] == "newuser@example.com"

        # Verify MongoDB was called
        mock_users_collection.find_one.assert_called()
        mock_users_collection.insert_one.assert_called_once()

    def test_register_duplicate_email_fails(self, client, mock_users_collection):
        """Test that duplicate email returns 400."""
        # Setup: User already exists
        mock_users_collection.find_one.return_value = {
            "_id": "existing-id",
            "email": "existing@example.com",
            "name": "Existing User",
        }

        # Execute
        response = client.post("/auth/register", json={
            "email": "existing@example.com",
            "password": "SecurePass123!",
            "name": "New User",
        })

        # Assert
        assert response.status_code == 400
        assert "already registered" in response.json()["detail"].lower()

    def test_register_invalid_email_fails(self, client):
        """Test that invalid email format returns 422."""
        response = client.post("/auth/register", json={
            "email": "not-an-email",
            "password": "SecurePass123!",
            "name": "Test User",
        })

        assert response.status_code == 422

    def test_register_short_password_fails(self, client):
        """Test that password shorter than 8 chars returns 422."""
        response = client.post("/auth/register", json={
            "email": "test@example.com",
            "password": "short",
            "name": "Test User",
        })

        assert response.status_code == 422


class TestLoginEndpoint:
    """Tests for user login."""

    def test_login_valid_credentials(self, client, mock_users_collection):
        """Test successful login with valid credentials."""
        from src.jwt_service import hash_password

        # Setup: User exists with hashed password
        mock_users_collection.find_one.return_value = {
            "_id": "507f1f77bcf86cd799439011",
            "email": "test@example.com",
            "name": "Test User",
            "hashed_password": hash_password("correctpassword"),
            "role": "customer",
            "customer_id": "cust-456",
            "created_at": datetime.now(UTC),
        }

        # Execute
        response = client.post("/auth/login", json={
            "email": "test@example.com",
            "password": "correctpassword",
        })

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "token_type" in data
        assert data["token_type"] == "bearer"
        assert "expires_in" in data

    def test_login_wrong_password(self, client, mock_users_collection):
        """Test login fails with wrong password."""
        from src.jwt_service import hash_password

        # Setup: User exists
        mock_users_collection.find_one.return_value = {
            "_id": "507f1f77bcf86cd799439011",
            "email": "test@example.com",
            "hashed_password": hash_password("correctpassword"),
        }

        # Execute
        response = client.post("/auth/login", json={
            "email": "test@example.com",
            "password": "wrongpassword",
        })

        # Assert
        assert response.status_code == 401
        assert "Invalid email or password" in response.json()["detail"]

    def test_login_nonexistent_user(self, client, mock_users_collection):
        """Test login fails for non-existent user."""
        # Setup: User doesn't exist
        mock_users_collection.find_one.return_value = None

        # Execute
        response = client.post("/auth/login", json={
            "email": "nonexistent@example.com",
            "password": "password123",
        })

        # Assert
        assert response.status_code == 401
        assert "Invalid email or password" in response.json()["detail"]


class TestMeEndpoint:
    """Tests for /me endpoint (get current user)."""

    def test_me_with_valid_token(self, client, mock_users_collection):
        """Test getting current user info with valid token."""
        # Use valid ObjectId format (24 hex characters)
        user_id = "507f1f77bcf86cd799439011"

        # Create a valid token
        token, _ = create_access_token(
            user_id=user_id,
            email="test@example.com",
            role="customer",
        )

        # Setup: User exists in database
        mock_users_collection.find_one.return_value = {
            "_id": user_id,
            "email": "test@example.com",
            "name": "Test User",
            "role": "customer",
            "customer_id": "cust-456",
            "created_at": datetime.now(UTC),
        }

        # Execute
        response = client.get(
            "/auth/me",
            headers={"Authorization": f"Bearer {token}"},
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "test@example.com"
        assert data["name"] == "Test User"
        assert data["role"] == "customer"

    def test_me_without_token(self, client):
        """Test /me endpoint without token returns 401."""
        response = client.get("/auth/me")

        assert response.status_code == 401
