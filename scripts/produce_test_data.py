#!/usr/bin/env python3
"""
Test data producer script.

Reads meter readings from CSV and sends them to the Ingestion Service via the API Gateway.
Authenticates as data-loader user and sends readings in batches at a configurable rate.

Usage:
    # Against staging (uses default data-loader credentials)
    python produce_test_data.py --url http://194.47.170.217

    # With custom password (for production)
    TEST_USER_PASSWORD=strongpass python produce_test_data.py --url http://prod.example

    # Local development (direct to ingestion service, no auth)
    python produce_test_data.py --no-auth --url http://localhost:8000
"""

import argparse
import csv
import os
import sys
import time
from pathlib import Path

import requests


# Default credentials for data-loader user (seeded by auth service)
DEFAULT_EMAIL = "data-loader@example.com"
DEFAULT_PASSWORD = os.environ.get("TEST_USER_PASSWORD", "testpassword123")


def login(base_url: str, email: str, password: str) -> str | None:
    """Login to get JWT access token."""
    try:
        response = requests.post(
            f"{base_url}/api/auth/login",
            json={"email": email, "password": password},
            timeout=30,
        )
        if response.status_code == 200:
            return response.json().get("access_token")
        print(f"Login failed: {response.status_code} - {response.text}")
        return None
    except requests.RequestException as e:
        print(f"Login request failed: {e}")
        return None


def load_readings(file_path: Path) -> list[dict]:
    """Load meter readings from CSV file."""
    readings = []
    with open(file_path, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            readings.append({
                "DateTime": row["DateTime"],
                "CUSTOMER": row["CUSTOMER"],
                "AREA": row["AREA"],
                "Power_Consumption": float(row["Power_Consumption"]),
            })
    return readings


def send_batch(url: str, readings: list[dict], token: str | None = None) -> bool:
    """Send a batch of readings to the ingestion service."""
    headers = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"

    try:
        response = requests.post(
            url,
            json={"readings": readings},
            headers=headers,
            timeout=30,
        )
        if response.status_code == 200:
            data = response.json()
            print(f"Sent {data['accepted']} readings")
            return True
        print(f"Error: {response.status_code} - {response.text}")
        return False
    except requests.RequestException as e:
        print(f"Request failed: {e}")
        return False


def main():
    """
    Main entry point for the test data producer.

    Command-line arguments:
        --file: Path to CSV file with test data (default: ../data/test_data_small.csv)
        --url: API Gateway URL (default: http://localhost:8000)
        --email: Login email (default: data-loader@example.com)
        --batch-size: Number of readings per batch (default: 50)
        --rate: Batches per second rate limit (default: 10)
        --limit: Maximum readings to send, 0 for all (default: 0)
        --no-auth: Skip authentication (for local dev with direct ingestion access)
    """
    parser = argparse.ArgumentParser(
        description="Send test data to the Ingestion Service.",
        epilog="""
Examples:
  %(prog)s --url http://staging.example    # Send to staging
  %(prog)s --limit 100                     # Send only 100 readings
  %(prog)s --rate 2 --limit 50             # Send slowly for debugging
  %(prog)s --file ../data/test_data_medium.csv  # Use medium dataset
  %(prog)s --batch-size 200 --rate 0       # Large batches, no rate limit
  %(prog)s --no-auth --url http://localhost:8000  # Local dev, no auth

Environment:
  TEST_USER_PASSWORD    Password for data-loader user (default: testpassword123)
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--file",
        type=Path,
        default=Path(__file__).parent.parent / "data" / "test_data_small.csv",
        help="Path to CSV file (default: data/test_data_small.csv)",
    )
    parser.add_argument(
        "--url",
        default="http://localhost:8000",
        help="API Gateway URL (default: http://localhost:8000)",
    )
    parser.add_argument(
        "--email",
        default=DEFAULT_EMAIL,
        help=f"Login email (default: {DEFAULT_EMAIL})",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=50,
        help="Readings per HTTP request (default: 50)",
    )
    parser.add_argument(
        "--rate",
        type=float,
        default=10,
        help="Batches per second, 0 for unlimited (default: 10)",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=0,
        help="Max readings to send, 0 for all (default: 0)",
    )
    parser.add_argument(
        "--no-auth",
        action="store_true",
        help="Skip authentication (for local dev)",
    )
    args = parser.parse_args()

    # Determine ingest endpoint based on auth mode
    if args.no_auth:
        ingest_url = f"{args.url}/ingest"
        token = None
        print("Running without authentication (local dev mode)")
    else:
        ingest_url = f"{args.url}/api/ingest"
        print(f"Logging in as {args.email}...")
        token = login(args.url, args.email, DEFAULT_PASSWORD)
        if not token:
            print("Failed to authenticate. Use --no-auth for local dev without auth.")
            sys.exit(1)
        print("Login successful")

    print(f"Loading data from {args.file}")
    readings = load_readings(args.file)
    print(f"Loaded {len(readings)} readings")

    if args.limit > 0:
        readings = readings[: args.limit]
        print(f"Limited to {len(readings)} readings")

    delay = 1.0 / args.rate if args.rate > 0 else 0
    total_sent = 0
    batches = 0
    start_time = time.time()

    print(f"Sending to {ingest_url}...")
    try:
        for i in range(0, len(readings), args.batch_size):
            batch = readings[i : i + args.batch_size]
            if send_batch(ingest_url, batch, token):
                total_sent += len(batch)
                batches += 1

            if delay > 0:
                time.sleep(delay)

    except KeyboardInterrupt:
        print("\nInterrupted by user")

    elapsed = time.time() - start_time
    print("\nSummary:")
    print(f"  Total sent: {total_sent} readings")
    print(f"  Batches: {batches}")
    print(f"  Elapsed: {elapsed:.2f}s")
    if elapsed > 0:
        print(f"  Rate: {total_sent / elapsed:.1f} readings/sec")


if __name__ == "__main__":
    main()
