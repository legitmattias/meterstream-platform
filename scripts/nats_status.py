#!/usr/bin/env python3
"""Pretty-print NATS JetStream status."""

import json
import sys
import urllib.request
import urllib.error


def main():
    try:
        with urllib.request.urlopen("http://localhost:8222/jsz", timeout=2) as resp:
            data = json.load(resp)
    except urllib.error.URLError:
        print("NATS not running")
        sys.exit(1)

    print("=== NATS JetStream Status ===")
    print(f"Messages:  {data.get('messages', 0):,}")
    print(f"Storage:   {data.get('bytes', 0) // 1024:,} KB")
    print(f"Streams:   {data.get('streams', 0)}")
    print(f"Consumers: {data.get('consumers', 0)}")


if __name__ == "__main__":
    main()
