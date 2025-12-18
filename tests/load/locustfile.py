"""
MeterStream Load Testing with Locust

Usage:
    # Interactive mode (opens web UI at http://localhost:8089)
    locust -f locustfile.py --host=http://staging.meterstream.example

    # Headless mode for CI/CD
    locust -f locustfile.py \
        --host=http://staging.meterstream.example \
        --users 50 \
        --spawn-rate 10 \
        --run-time 5m \
        --headless

Load profiles:
    - Smoke:  1 user,  30s  - Verify test works
    - Normal: 10 users, 2m  - Baseline performance
    - Stress: 50 users, 5m  - Trigger HPA scaling
    - Spike:  100 users, 1m - Sudden load burst
"""

import json
import random
from datetime import datetime, timedelta, UTC
from locust import HttpUser, task, between, events


# Shared credentials for seeded test user (password from TEST_USER_PASSWORD env var)
SHARED_TEST_EMAIL = "integration-test@example.com"
SHARED_TEST_PASSWORD = "testpassword123"


class MeterStreamUser(HttpUser):
    """Simulates a user sending meter readings to the system."""

    wait_time = between(0.1, 0.5)  # Fast requests for load testing

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.token = None

    def on_start(self):
        """Login with shared test user to get JWT token."""
        response = self.client.post(
            "/api/auth/login",
            json={
                "email": SHARED_TEST_EMAIL,
                "password": SHARED_TEST_PASSWORD,
            },
        )

        if response.status_code == 200:
            self.token = response.json().get("access_token")

    @task(10)
    def ingest_single_reading(self):
        """POST a single meter reading - most common operation."""
        if not self.token:
            return

        headers = {"Authorization": f"Bearer {self.token}"}
        timestamp = datetime.now(UTC) - timedelta(minutes=random.randint(0, 60))

        data = {
            "readings": [
                {
                    "DateTime": timestamp.isoformat() + "Z",
                    "CUSTOMER": f"LOAD_TEST_{random.randint(1, 100):03d}",
                    "AREA": f"area-{random.randint(1, 5)}",
                    "Power_Consumption": round(random.uniform(50.0, 500.0), 2),
                }
            ]
        }

        self.client.post("/api/ingest", json=data, headers=headers)

    @task(3)
    def ingest_batch_readings(self):
        """POST a batch of meter readings."""
        if not self.token:
            return

        headers = {"Authorization": f"Bearer {self.token}"}
        base_time = datetime.now(UTC) - timedelta(hours=random.randint(1, 24))

        readings = []
        for i in range(random.randint(5, 20)):
            timestamp = base_time + timedelta(minutes=i * 15)
            readings.append(
                {
                    "DateTime": timestamp.isoformat() + "Z",
                    "CUSTOMER": f"LOAD_TEST_{random.randint(1, 100):03d}",
                    "AREA": f"area-{random.randint(1, 5)}",
                    "Power_Consumption": round(random.uniform(50.0, 500.0), 2),
                }
            )

        data = {"readings": readings}
        self.client.post("/api/ingest", json=data, headers=headers)

    @task(1)
    def check_health(self):
        """GET health endpoint - lightweight check."""
        self.client.get("/health")

    @task(1)
    def get_current_user(self):
        """GET current user info."""
        if not self.token:
            return

        headers = {"Authorization": f"Bearer {self.token}"}
        self.client.get("/api/auth/me", headers=headers)


class HighVolumeUser(HttpUser):
    """
    High-volume ingestion user for stress testing.
    Sends larger batches more frequently.
    """

    wait_time = between(0.05, 0.2)  # Very fast

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.token = None

    def on_start(self):
        """Login with shared test user."""
        response = self.client.post(
            "/api/auth/login",
            json={
                "email": SHARED_TEST_EMAIL,
                "password": SHARED_TEST_PASSWORD,
            },
        )
        if response.status_code == 200:
            self.token = response.json().get("access_token")

    @task
    def ingest_large_batch(self):
        """POST large batch of readings to stress the system."""
        if not self.token:
            return

        headers = {"Authorization": f"Bearer {self.token}"}
        base_time = datetime.now(UTC) - timedelta(days=random.randint(1, 30))

        readings = []
        for i in range(50):  # 50 readings per request
            timestamp = base_time + timedelta(hours=i)
            readings.append(
                {
                    "DateTime": timestamp.isoformat() + "Z",
                    "CUSTOMER": f"STRESS_TEST_{random.randint(1, 200):03d}",
                    "AREA": f"area-{random.randint(1, 10)}",
                    "Power_Consumption": round(random.uniform(10.0, 1000.0), 2),
                }
            )

        data = {"readings": readings}
        self.client.post("/api/ingest", json=data, headers=headers)


# Event hooks for reporting
@events.request.add_listener
def on_request(request_type, name, response_time, response_length, exception, **kwargs):
    """Log failed requests for debugging."""
    if exception:
        print(f"Request failed: {request_type} {name} - {exception}")
