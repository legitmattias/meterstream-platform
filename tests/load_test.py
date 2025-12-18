#!/usr/bin/env python3
"""
Load test script for testing HPA scaling behavior.
Sends many messages to NATS to trigger processor autoscaling.

Usage:
    python tests/load_test.py --count 500 --host YOUR_CLUSTER_IP
"""

import asyncio
import argparse
import json
from datetime import datetime
import sys

try:
    import nats
    from nats.errors import ConnectionClosedError, TimeoutError, NoServersError
except ImportError:
    print("Error: nats-py library not found.")
    print("Install with: pip install nats-py")
    sys.exit(1)


async def send_messages(host: str, port: int, count: int, batch_size: int = 100):
    """Send messages to NATS JetStream."""

    nats_url = f"nats://{host}:{port}"
    print(f"Connecting to NATS at {nats_url}...")

    try:
        nc = await nats.connect(nats_url)
        js = nc.jetstream()

        print(f"Connected! Sending {count} messages...")
        print(f"This should trigger scaling if queue depth exceeds 50 messages.")
        print("-" * 60)

        start_time = datetime.now()

        for i in range(count):
            payload = {
                "meter_id": f"load-test-meter-{i % 20}",
                "value": 100.0 + (i % 100),
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "unit": "kWh"
            }

            await js.publish("meter.readings", json.dumps(payload).encode())

            if (i + 1) % batch_size == 0:
                elapsed = (datetime.now() - start_time).total_seconds()
                rate = (i + 1) / elapsed
                print(f"Sent {i + 1}/{count} messages ({rate:.1f} msg/s)")

        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        avg_rate = count / duration

        print("-" * 60)
        print(f"✓ Successfully sent {count} messages in {duration:.2f} seconds")
        print(f"  Average rate: {avg_rate:.1f} messages/second")
        print()
        print("Next steps:")
        print("  1. Watch pods scale: watch kubectl get pods -n meterstream")
        print("  2. Check HPA: kubectl get hpa -n meterstream")
        print("  3. Check queue: kubectl exec -it nats-0 -n meterstream -- nats consumer info METER_DATA processor-consumer")

        await nc.close()

    except NoServersError:
        print(f"Error: Could not connect to NATS at {nats_url}")
        print("Make sure:")
        print("  1. The cluster IP is correct")
        print("  2. NATS NodePort 30222 is accessible")
        print("  3. NATS is running: kubectl get pods -n meterstream | grep nats")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(
        description="Load test for processor HPA scaling",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Send 500 messages to localhost (port-forward)
  kubectl port-forward -n meterstream svc/nats 4222:4222
  python tests/load_test.py --count 500

  # Send 1000 messages directly to cluster
  python tests/load_test.py --host 192.168.1.100 --port 30222 --count 1000
        """
    )

    parser.add_argument(
        "--host",
        default="localhost",
        help="NATS host (default: localhost for port-forward, or cluster IP)"
    )
    parser.add_argument(
        "--port",
        type=int,
        default=4222,
        help="NATS port (default: 4222 for port-forward, 30222 for NodePort)"
    )
    parser.add_argument(
        "--count",
        type=int,
        default=500,
        help="Number of messages to send (default: 500)"
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=100,
        help="Log progress every N messages (default: 100)"
    )

    args = parser.parse_args()

    print("=" * 60)
    print("NATS Load Test - Processor HPA Scaling")
    print("=" * 60)

    asyncio.run(send_messages(
        host=args.host,
        port=args.port,
        count=args.count,
        batch_size=args.batch_size
    ))


if __name__ == "__main__":
    main()
