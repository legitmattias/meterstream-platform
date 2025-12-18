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
    # Internal staff user (no customer_id)
    {"email": "staff@test.local", "name": "Test Staff", "role": "internal", "customer_id": None},

    # Customers with 3 users each (family/business accounts)
    {"email": "alice.andersson@test.local", "name": "Alice Andersson", "role": "customer", "customer_id": "1060598736"},
    {"email": "bob.andersson@test.local", "name": "Bob Andersson", "role": "customer", "customer_id": "1060598736"},
    {"email": "carl.andersson@test.local", "name": "Carl Andersson", "role": "customer", "customer_id": "1060598736"},

    {"email": "diana.berg@test.local", "name": "Diana Berg", "role": "customer", "customer_id": "1060598755"},
    {"email": "erik.berg@test.local", "name": "Erik Berg", "role": "customer", "customer_id": "1060598755"},
    {"email": "fiona.berg@test.local", "name": "Fiona Berg", "role": "customer", "customer_id": "1060598755"},

    {"email": "gustav.ek@test.local", "name": "Gustav Ek", "role": "customer", "customer_id": "1060598764"},
    {"email": "hanna.ek@test.local", "name": "Hanna Ek", "role": "customer", "customer_id": "1060598764"},
    {"email": "ivan.ek@test.local", "name": "Ivan Ek", "role": "customer", "customer_id": "1060598764"},

    # Customers with 2 users each
    {"email": "julia.lund@test.local", "name": "Julia Lund", "role": "customer", "customer_id": "1060598773"},
    {"email": "karl.lund@test.local", "name": "Karl Lund", "role": "customer", "customer_id": "1060598773"},

    {"email": "lisa.holm@test.local", "name": "Lisa Holm", "role": "customer", "customer_id": "1060598781"},
    {"email": "martin.holm@test.local", "name": "Martin Holm", "role": "customer", "customer_id": "1060598781"},

    # Customers with 1 user each (remaining 15 customers)
    {"email": "nina.svensson@test.local", "name": "Nina Svensson", "role": "customer", "customer_id": "1060598788"},
    {"email": "oscar.johansson@test.local", "name": "Oscar Johansson", "role": "customer", "customer_id": "1060598846"},
    {"email": "petra.karlsson@test.local", "name": "Petra Karlsson", "role": "customer", "customer_id": "1060598856"},
    {"email": "quinn.nilsson@test.local", "name": "Quinn Nilsson", "role": "customer", "customer_id": "1060598905"},
    {"email": "rosa.eriksson@test.local", "name": "Rosa Eriksson", "role": "customer", "customer_id": "1060598922"},
    {"email": "simon.larsson@test.local", "name": "Simon Larsson", "role": "customer", "customer_id": "1060598963"},
    {"email": "tina.olsson@test.local", "name": "Tina Olsson", "role": "customer", "customer_id": "1060598971"},
    {"email": "ulf.persson@test.local", "name": "Ulf Persson", "role": "customer", "customer_id": "1060598978"},
    {"email": "vera.gustafsson@test.local", "name": "Vera Gustafsson", "role": "customer", "customer_id": "1060599019"},
    {"email": "william.pettersson@test.local", "name": "William Pettersson", "role": "customer", "customer_id": "1060599041"},
    {"email": "xena.lindberg@test.local", "name": "Xena Lindberg", "role": "customer", "customer_id": "1060599047"},
    {"email": "yngve.lindgren@test.local", "name": "Yngve Lindgren", "role": "customer", "customer_id": "1060599053"},
    {"email": "zara.axelsson@test.local", "name": "Zara Axelsson", "role": "customer", "customer_id": "1060599059"},
    {"email": "adam.lindqvist@test.local", "name": "Adam Lindqvist", "role": "customer", "customer_id": "1060599082"},
    {"email": "bella.magnusson@test.local", "name": "Bella Magnusson", "role": "customer", "customer_id": "1060599089"},
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
