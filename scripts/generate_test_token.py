#!/usr/bin/env python3
"""Generate test JWT tokens for API Gateway testing."""

import argparse
import json
from datetime import datetime, timedelta, timezone

from jose import jwt

# Default secret for local testing - must match JWT_SECRET env var used by gateway
DEFAULT_SECRET = "test-secret-for-local-dev"
ALGORITHM = "HS256"


def generate_token(
    user_id: str = "test-user-123",
    role: str = "customer",
    customer_id: str | None = "cust-456",
    expires_in_hours: int = 24,
    secret: str = DEFAULT_SECRET,
) -> str:
    """
    Generate a JWT token for testing.

    Args:
        user_id: User identifier (sub claim)
        role: User role (customer, internal_staff, admin)
        customer_id: Optional customer ID
        expires_in_hours: Token validity period
        secret: JWT signing secret

    Returns:
        Encoded JWT token string
    """
    exp = datetime.now(tz=timezone.utc) + timedelta(hours=expires_in_hours)

    payload = {
        "sub": user_id,
        "role": role,
        "exp": int(exp.timestamp()),
    }

    if customer_id:
        payload["customer_id"] = customer_id

    return jwt.encode(payload, secret, algorithm=ALGORITHM)


def main():
    """Parse arguments and generate a test JWT token."""
    parser = argparse.ArgumentParser(description="Generate test JWT tokens")
    parser.add_argument("--user-id", default="test-user-123", help="User ID")
    parser.add_argument(
        "--role",
        default="customer",
        choices=["customer", "internal", "admin"],
        help="User role",
    )
    parser.add_argument("--customer-id", default="cust-456", help="Customer ID")
    parser.add_argument(
        "--expires", type=int, default=24, help="Expiration in hours"
    )
    parser.add_argument("--secret", default=DEFAULT_SECRET, help="JWT secret")
    parser.add_argument(
        "--decode", action="store_true", help="Also decode and show payload"
    )

    args = parser.parse_args()

    token = generate_token(
        user_id=args.user_id,
        role=args.role,
        customer_id=args.customer_id if args.customer_id != "none" else None,
        expires_in_hours=args.expires,
        secret=args.secret,
    )

    print(f"Token: {token}")
    print()
    print(f"Authorization header: Bearer {token}")

    if args.decode:
        print()
        decoded = jwt.decode(token, args.secret, algorithms=[ALGORITHM])
        print("Decoded payload:")
        print(json.dumps(decoded, indent=2))


if __name__ == "__main__":
    main()
