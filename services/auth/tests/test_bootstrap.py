"""Tests for bootstrap admin functionality."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.bootstrap import ensure_admin_exists


class TestEnsureAdminExists:
    """Tests for ensure_admin_exists function."""

    @pytest.fixture
    def mock_users_collection(self):
        """Create a mock users collection."""
        collection = AsyncMock()
        return collection

    @pytest.fixture
    def mock_mongodb(self, mock_users_collection):
        """Create a mock mongodb instance."""
        mongodb = MagicMock()
        mongodb.get_users_collection.return_value = mock_users_collection
        return mongodb

    @pytest.mark.asyncio
    async def test_skips_when_password_not_set(self, mock_mongodb):
        """Test that bootstrap is skipped when password is not set."""
        with patch("src.bootstrap.settings") as mock_settings, \
             patch("src.bootstrap.mongodb", mock_mongodb):
            mock_settings.bootstrap_admin_password = None
            mock_settings.bootstrap_admin_email = "admin@test.local"

            await ensure_admin_exists()

            # Should not even check for existing admin
            mock_mongodb.get_users_collection.assert_not_called()

    @pytest.mark.asyncio
    async def test_skips_when_password_empty_string(self, mock_mongodb):
        """Test that bootstrap is skipped when password is empty string."""
        with patch("src.bootstrap.settings") as mock_settings, \
             patch("src.bootstrap.mongodb", mock_mongodb):
            mock_settings.bootstrap_admin_password = ""
            mock_settings.bootstrap_admin_email = "admin@test.local"

            await ensure_admin_exists()

            # Should not even check for existing admin
            mock_mongodb.get_users_collection.assert_not_called()

    @pytest.mark.asyncio
    async def test_skips_when_admin_exists(self, mock_mongodb, mock_users_collection):
        """Test that bootstrap is skipped when an admin already exists."""
        mock_users_collection.find_one.return_value = {
            "_id": "existing-admin-id",
            "email": "existing@admin.com",
            "role": "admin"
        }

        with patch("src.bootstrap.settings") as mock_settings, \
             patch("src.bootstrap.mongodb", mock_mongodb):
            mock_settings.bootstrap_admin_password = "test-password"
            mock_settings.bootstrap_admin_email = "admin@test.local"

            await ensure_admin_exists()

            # Should check for existing admin
            mock_users_collection.find_one.assert_called_once_with({"role": "admin"})
            # Should NOT insert new admin
            mock_users_collection.insert_one.assert_not_called()

    @pytest.mark.asyncio
    async def test_creates_admin_when_none_exists(self, mock_mongodb, mock_users_collection):
        """Test that bootstrap creates admin when none exists."""
        mock_users_collection.find_one.return_value = None

        with patch("src.bootstrap.settings") as mock_settings, \
             patch("src.bootstrap.mongodb", mock_mongodb), \
             patch("src.bootstrap.hash_password") as mock_hash:
            mock_settings.bootstrap_admin_password = "test-password"
            mock_settings.bootstrap_admin_email = "admin@test.local"
            mock_hash.return_value = "hashed-password"

            await ensure_admin_exists()

            # Should check for existing admin
            mock_users_collection.find_one.assert_called_once_with({"role": "admin"})

            # Should insert new admin
            mock_users_collection.insert_one.assert_called_once()
            inserted_doc = mock_users_collection.insert_one.call_args[0][0]

            assert inserted_doc["email"] == "admin@test.local"
            assert inserted_doc["hashed_password"] == "hashed-password"
            assert inserted_doc["role"] == "admin"
            assert inserted_doc["customer_id"] is None
            assert "created_at" in inserted_doc

    @pytest.mark.asyncio
    async def test_uses_correct_password_for_hashing(self, mock_mongodb, mock_users_collection):
        """Test that the correct password is passed to hash_password."""
        mock_users_collection.find_one.return_value = None

        with patch("src.bootstrap.settings") as mock_settings, \
             patch("src.bootstrap.mongodb", mock_mongodb), \
             patch("src.bootstrap.hash_password") as mock_hash:
            mock_settings.bootstrap_admin_password = "my-secret-password"
            mock_settings.bootstrap_admin_email = "admin@test.local"
            mock_hash.return_value = "hashed"

            await ensure_admin_exists()

            mock_hash.assert_called_once_with("my-secret-password")

    @pytest.mark.asyncio
    async def test_idempotent_multiple_calls(self, mock_mongodb, mock_users_collection):
        """Test that multiple calls are idempotent."""
        # First call: no admin exists
        mock_users_collection.find_one.return_value = None

        with patch("src.bootstrap.settings") as mock_settings, \
             patch("src.bootstrap.mongodb", mock_mongodb), \
             patch("src.bootstrap.hash_password") as mock_hash:
            mock_settings.bootstrap_admin_password = "test-password"
            mock_settings.bootstrap_admin_email = "admin@test.local"
            mock_hash.return_value = "hashed"

            # First call - creates admin
            await ensure_admin_exists()
            assert mock_users_collection.insert_one.call_count == 1

            # Simulate admin now exists
            mock_users_collection.find_one.return_value = {"role": "admin"}

            # Second call - should skip
            await ensure_admin_exists()
            # insert_one should still be 1 (not called again)
            assert mock_users_collection.insert_one.call_count == 1
