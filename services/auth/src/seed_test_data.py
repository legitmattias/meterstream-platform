"""Seed test users for development and staging environments.

Creates test users linked to customer IDs from the test dataset.
Idempotent: skips users that already exist (checks by email).

Enabled by setting SEED_TEST_DATA=true environment variable.
Password for all test users: TEST_USER_PASSWORD (default: testpassword123)
"""

import logging
from datetime import datetime, UTC

from .config import get_settings
from .mongodb import mongodb
from .jwt_service import hash_password

settings = get_settings()
logger = logging.getLogger(__name__)

# Customer IDs from data/test_data_small.csv
# 20 customers total, some with multiple users to simulate realistic scenarios
TEST_USERS = [
    # Integration/load testing user (shared by all load test instances)
    {"email": "integration-test@example.com", "name": "Integration Test", "role": "internal", "customer_id": None},

    # Internal staff user (no customer_id)
    {"email": "staff@example.com", "name": "Test Staff", "role": "internal", "customer_id": None},

    # Customers with 3 users each (family/business accounts)
    {"email": "alice.andersson@example.com", "name": "Alice Andersson", "role": "customer", "customer_id": "1060598736"},
    {"email": "bob.andersson@example.com", "name": "Bob Andersson", "role": "customer", "customer_id": "1060598736"},
    {"email": "carl.andersson@example.com", "name": "Carl Andersson", "role": "customer", "customer_id": "1060598736"},

    {"email": "diana.berg@example.com", "name": "Diana Berg", "role": "customer", "customer_id": "1060598755"},
    {"email": "erik.berg@example.com", "name": "Erik Berg", "role": "customer", "customer_id": "1060598755"},
    {"email": "fiona.berg@example.com", "name": "Fiona Berg", "role": "customer", "customer_id": "1060598755"},

    {"email": "gustav.ek@example.com", "name": "Gustav Ek", "role": "customer", "customer_id": "1060598764"},
    {"email": "hanna.ek@example.com", "name": "Hanna Ek", "role": "customer", "customer_id": "1060598764"},
    {"email": "ivan.ek@example.com", "name": "Ivan Ek", "role": "customer", "customer_id": "1060598764"},

    # Customers with 2 users each
    {"email": "julia.lund@example.com", "name": "Julia Lund", "role": "customer", "customer_id": "1060598773"},
    {"email": "karl.lund@example.com", "name": "Karl Lund", "role": "customer", "customer_id": "1060598773"},

    {"email": "lisa.holm@example.com", "name": "Lisa Holm", "role": "customer", "customer_id": "1060598781"},
    {"email": "martin.holm@example.com", "name": "Martin Holm", "role": "customer", "customer_id": "1060598781"},

    # Customers with 1 user each (remaining 15 customers)
    {"email": "nina.svensson@example.com", "name": "Nina Svensson", "role": "customer", "customer_id": "1060598788"},
    {"email": "oscar.johansson@example.com", "name": "Oscar Johansson", "role": "customer", "customer_id": "1060598846"},
    {"email": "petra.karlsson@example.com", "name": "Petra Karlsson", "role": "customer", "customer_id": "1060598856"},
    {"email": "quinn.nilsson@example.com", "name": "Quinn Nilsson", "role": "customer", "customer_id": "1060598905"},
    {"email": "rosa.eriksson@example.com", "name": "Rosa Eriksson", "role": "customer", "customer_id": "1060598922"},
    {"email": "simon.larsson@example.com", "name": "Simon Larsson", "role": "customer", "customer_id": "1060598963"},
    {"email": "tina.olsson@example.com", "name": "Tina Olsson", "role": "customer", "customer_id": "1060598971"},
    {"email": "ulf.persson@example.com", "name": "Ulf Persson", "role": "customer", "customer_id": "1060598978"},
    {"email": "vera.gustafsson@example.com", "name": "Vera Gustafsson", "role": "customer", "customer_id": "1060599019"},
    {"email": "william.pettersson@example.com", "name": "William Pettersson", "role": "customer", "customer_id": "1060599041"},
    {"email": "xena.lindberg@example.com", "name": "Xena Lindberg", "role": "customer", "customer_id": "1060599047"},
    {"email": "yngve.lindgren@example.com", "name": "Yngve Lindgren", "role": "customer", "customer_id": "1060599053"},
    {"email": "zara.axelsson@example.com", "name": "Zara Axelsson", "role": "customer", "customer_id": "1060599059"},
    {"email": "adam.lindqvist@example.com", "name": "Adam Lindqvist", "role": "customer", "customer_id": "1060599082"},
    {"email": "bella.magnusson@example.com", "name": "Bella Magnusson", "role": "customer", "customer_id": "1060599089"},
]


async def seed_test_data_if_enabled():
    """Create test users if SEED_TEST_DATA is enabled.

    Idempotent: only creates users that don't already exist.
    """
    if not settings.seed_test_data:
        logger.debug("Test data seeding disabled (SEED_TEST_DATA not set)")
        return

    logger.info("Seeding test data (SEED_TEST_DATA=true)")

    users = mongodb.get_users_collection()
    hashed_password = hash_password(settings.test_user_password)

    created = 0
    skipped = 0

    for user_data in TEST_USERS:
        existing = await users.find_one({"email": user_data["email"]})
        if existing:
            logger.debug("User %s already exists, skipping", user_data["email"])
            skipped += 1
            continue

        doc = {
            "email": user_data["email"],
            "hashed_password": hashed_password,
            "name": user_data["name"],
            "role": user_data["role"],
            "customer_id": user_data["customer_id"],
            "created_at": datetime.now(UTC),
        }

        await users.insert_one(doc)
        logger.debug("Created user: %s", user_data["email"])
        created += 1

    logger.info("Test data seeding complete: %d created, %d skipped", created, skipped)
