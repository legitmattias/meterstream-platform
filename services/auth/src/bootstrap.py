"""Bootstrap admin user on startup."""

import logging
from datetime import datetime, UTC

from .config import get_settings
from .mongodb import mongodb
from .jwt_service import hash_password

settings = get_settings()
logger = logging.getLogger(__name__)


async def ensure_admin_exists():
    """Create bootstrap admin if no admin exists.

    Idempotent: only creates admin if none exists.
    Password comes from BOOTSTRAP_ADMIN_PASSWORD env var.
    """
    if not settings.bootstrap_admin_password:
        logger.info("Bootstrap admin password not set, skipping bootstrap")
        return

    users = mongodb.get_users_collection()

    # Check if any admin exists
    existing_admin = await users.find_one({"role": "admin"})
    if existing_admin:
        logger.debug("Admin user already exists, skipping bootstrap")
        return

    # Create bootstrap admin
    admin_doc = {
        "email": settings.bootstrap_admin_email,
        "hashed_password": hash_password(settings.bootstrap_admin_password),
        "name": "Bootstrap Admin",
        "role": "admin",
        "customer_id": None,
        "created_at": datetime.now(UTC)
    }

    await users.insert_one(admin_doc)
    logger.info("Created bootstrap admin user: %s", settings.bootstrap_admin_email)
