#!/usr/bin/env python3
"""
Test data producer script.

Reads meter readings from CSV and sends them to the Ingestion Service.
Simulates a data stream by sending readings in batches at a configurable rate.

Usage:
    python produce_test_data.py --file ../data/test_data_small.csv
    python produce_test_data.py --file ../data/test_data_small.csv --rate 50 --batch-size 100
"""

import argparse
import csv
import time
from pathlib import Path

import requests


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


def send_batch(url: str, readings: list[dict]) -> bool:
    """Send a batch of readings to the ingestion service."""
    try:
        response = requests.post(
            f"{url}/ingest",
            json={"readings": readings},
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
        --url: Ingestion service URL (default: http://localhost:8000)
        --batch-size: Number of readings per batch (default: 50)
        --rate: Batches per second rate limit (default: 10)
        --limit: Maximum readings to send, 0 for all (default: 0)
    """
    parser = argparse.ArgumentParser(
        description="Send test data to the Ingestion Service.",
        epilog="""
Examples:
  %(prog)s                              # Send all data from small dataset
  %(prog)s --limit 100                  # Send only 100 readings
  %(prog)s --rate 2 --limit 50          # Send slowly for debugging
  %(prog)s --file ../data/test_data_medium.csv  # Use medium dataset
  %(prog)s --batch-size 200 --rate 0    # Large batches, no rate limit
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
        help="Ingestion service URL (default: http://localhost:8000)",
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
    args = parser.parse_args()

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

    try:
        for i in range(0, len(readings), args.batch_size):
            batch = readings[i : i + args.batch_size]
            if send_batch(args.url, batch):
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
    print(f"  Rate: {total_sent / elapsed:.1f} readings/sec")


if __name__ == "__main__":
    main()
