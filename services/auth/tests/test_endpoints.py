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


class TestAdminUserManagement:
    """Tests for admin user management endpoints."""

    def test_list_users_as_admin(self, client, mock_users_collection):
        """Test admin can list all users."""
        user_id = "507f1f77bcf86cd799439011"
        admin_token, _ = create_access_token(
            user_id=user_id,
            email="admin@example.com",
            role="admin",
        )

        # Mock user list - need to properly chain the mock methods
        mock_to_list = AsyncMock(
            return_value=[
                {
                    "_id": "507f1f77bcf86cd799439011",
                    "email": "user1@example.com",
                    "name": "User One",
                    "role": "customer",
                    "customer_id": "cust-1",
                    "created_at": datetime.now(UTC),
                },
                {
                    "_id": "507f1f77bcf86cd799439012",
                    "email": "user2@example.com",
                    "name": "User Two",
                    "role": "admin",
                    "customer_id": None,
                    "created_at": datetime.now(UTC),
                },
            ]
        )

        mock_limit = MagicMock()
        mock_limit.to_list = mock_to_list

        mock_skip = MagicMock()
        mock_skip.limit = MagicMock(return_value=mock_limit)

        mock_find = MagicMock()
        mock_find.skip = MagicMock(return_value=mock_skip)

        mock_users_collection.count_documents = AsyncMock(return_value=2)
        mock_users_collection.find = MagicMock(return_value=mock_find)

        response = client.get(
            "/auth/users?page=1&page_size=50",
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert "users" in data
        assert "total" in data
        assert data["total"] == 2
        assert len(data["users"]) == 2

    def test_list_users_as_non_admin_fails(self, client):
        """Test non-admin cannot list users."""
        user_id = "507f1f77bcf86cd799439011"
        customer_token, _ = create_access_token(
            user_id=user_id,
            email="customer@example.com",
            role="customer",
        )

        response = client.get(
            "/auth/users",
            headers={"Authorization": f"Bearer {customer_token}"},
        )

        assert response.status_code == 403
        assert "Admin access required" in response.json()["detail"]

    def test_get_user_by_id_as_admin(self, client, mock_users_collection):
        """Test admin can get specific user by ID."""
        admin_id = "507f1f77bcf86cd799439011"
        target_user_id = "507f1f77bcf86cd799439012"
        admin_token, _ = create_access_token(
            user_id=admin_id,
            email="admin@example.com",
            role="admin",
        )

        mock_users_collection.find_one.return_value = {
            "_id": target_user_id,
            "email": "target@example.com",
            "name": "Target User",
            "role": "customer",
            "customer_id": "cust-123",
            "created_at": datetime.now(UTC),
        }

        response = client.get(
            f"/auth/users/{target_user_id}",
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "target@example.com"
        assert data["role"] == "customer"

    def test_create_user_as_admin(self, client, mock_users_collection):
        """Test admin can create new user with role and customer_id."""
        admin_id = "507f1f77bcf86cd799439011"
        admin_token, _ = create_access_token(
            user_id=admin_id,
            email="admin@example.com",
            role="admin",
        )

        # Mock: User doesn't exist
        mock_users_collection.find_one.return_value = None
        mock_users_collection.insert_one.return_value = MagicMock(inserted_id="507f1f77bcf86cd799439099")

        response = client.post(
            "/auth/users",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "email": "newuser@example.com",
                "password": "SecurePass123!",
                "name": "New User",
                "role": "customer",
                "customer_id": "1060598736",
            },
        )

        assert response.status_code == 201
        data = response.json()
        assert data["email"] == "newuser@example.com"
        assert data["role"] == "customer"
        assert data["customer_id"] == "1060598736"

        # Verify insert was called
        mock_users_collection.insert_one.assert_called_once()

    def test_create_user_with_invalid_role_fails(self, client, mock_users_collection):
        """Test creating user with invalid role returns 422."""
        admin_id = "507f1f77bcf86cd799439011"
        admin_token, _ = create_access_token(
            user_id=admin_id,
            email="admin@example.com",
            role="admin",
        )

        response = client.post(
            "/auth/users",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "email": "newuser@example.com",
                "password": "SecurePass123!",
                "name": "New User",
                "role": "invalid_role",  # Invalid role
                "customer_id": "1060598736",
            },
        )

        assert response.status_code == 422

    def test_update_user_as_admin(self, client, mock_users_collection):
        """Test admin can update user fields."""
        admin_id = "507f1f77bcf86cd799439011"
        target_user_id = "507f1f77bcf86cd799439012"
        admin_token, _ = create_access_token(
            user_id=admin_id,
            email="admin@example.com",
            role="admin",
        )

        # Mock update result
        mock_result = MagicMock()
        mock_result.matched_count = 1
        mock_users_collection.update_one.return_value = mock_result

        # Mock the updated user
        mock_users_collection.find_one.return_value = {
            "_id": target_user_id,
            "email": "updated@example.com",
            "name": "Updated User",
            "role": "admin",
            "customer_id": "new-cust-id",
            "created_at": datetime.now(UTC),
        }

        response = client.put(
            f"/auth/users/{target_user_id}",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "role": "admin",
                "customer_id": "new-cust-id",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["role"] == "admin"
        assert data["customer_id"] == "new-cust-id"

        # Verify update was called
        mock_users_collection.update_one.assert_called_once()

    def test_update_user_with_no_fields_fails(self, client, mock_users_collection):
        """Test updating user without any fields returns 400."""
        admin_id = "507f1f77bcf86cd799439011"
        target_user_id = "507f1f77bcf86cd799439012"
        admin_token, _ = create_access_token(
            user_id=admin_id,
            email="admin@example.com",
            role="admin",
        )

        response = client.put(
            f"/auth/users/{target_user_id}",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={},  # No fields to update
        )

        assert response.status_code == 400
        assert "No fields provided for update" in response.json()["detail"]

    def test_update_nonexistent_user_fails(self, client, mock_users_collection):
        """Test updating non-existent user returns 404."""
        admin_id = "507f1f77bcf86cd799439011"
        target_user_id = "507f1f77bcf86cd799439012"
        admin_token, _ = create_access_token(
            user_id=admin_id,
            email="admin@example.com",
            role="admin",
        )

        # Mock: User not found
        mock_result = MagicMock()
        mock_result.matched_count = 0
        mock_users_collection.update_one.return_value = mock_result

        response = client.put(
            f"/auth/users/{target_user_id}",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"role": "admin"},
        )

        assert response.status_code == 404
        assert "User not found" in response.json()["detail"]

    def test_admin_endpoints_without_token_fail(self, client):
        """Test all admin endpoints require authorization."""
        endpoints = [
            ("GET", "/auth/users"),
            ("GET", "/auth/users/507f1f77bcf86cd799439011"),
            ("POST", "/auth/users"),
            ("PUT", "/auth/users/507f1f77bcf86cd799439011"),
        ]

        for method, path in endpoints:
            if method == "GET":
                response = client.get(path)
            elif method == "POST":
                # Valid payload to avoid 422 validation errors
                response = client.post(path, json={
                    "email": "test@example.com",
                    "password": "password123",
                    "name": "Test User",
                    "role": "customer"
                })
            elif method == "PUT":
                response = client.put(path, json={"role": "admin"})

            assert response.status_code == 401, f"{method} {path} should return 401 without token"
