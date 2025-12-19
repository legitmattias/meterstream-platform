# Scripts

Utility scripts for testing and monitoring.

## Setup

```bash
pip install -r requirements.txt
```

## produce_test_data.py

Sends test data to the Ingestion Service via the API Gateway. Authenticates as `data-loader@example.com` (seeded test user).

```bash
# Send to staging (authenticates automatically)
python produce_test_data.py --url http://194.47.170.217

# Send 100 readings slowly (for debugging)
python produce_test_data.py --url http://staging.example --limit 100 --rate 2

# Use medium dataset with large batches
python produce_test_data.py --url http://staging.example \
  --file ../data/test_data_medium.csv --batch-size 200

# Local development (no auth, direct to ingestion service)
python produce_test_data.py --no-auth --url http://localhost:8000

# Production (with strong password)
TEST_USER_PASSWORD=strongpass python produce_test_data.py --url http://prod.example
```

**Options:**
- `--file` - CSV file path (default: small dataset)
- `--url` - API Gateway URL (default: http://localhost:8000)
- `--email` - Login email (default: data-loader@example.com)
- `--batch-size` - Readings per request (default: 50)
- `--rate` - Batches per second (default: 10, 0 = unlimited)
- `--limit` - Max readings to send (default: 0 = all)
- `--no-auth` - Skip authentication (for local dev)

**Environment:**
- `TEST_USER_PASSWORD` - Password for data-loader user (default: testpassword123)

## generate_test_token.py

Generates JWT tokens for testing the API Gateway.

```bash
# Generate token with defaults
python generate_test_token.py

# Generate and show decoded payload
python generate_test_token.py --decode

# Custom user and role
python generate_test_token.py --user-id user-456 --role admin --decode

# Token without customer_id
python generate_test_token.py --customer-id none --decode

# Short-lived token (for testing expiration)
python generate_test_token.py --expires 0 --decode

# Custom secret (must match gateway's JWT_SECRET)
python generate_test_token.py --secret my-secret --decode
```

**Options:**
- `--user-id` - User identifier (default: test-user-123)
- `--role` - User role: customer, internal, admin (default: customer)
- `--customer-id` - Customer ID, use "none" to omit (default: cust-456)
- `--expires` - Token validity in hours (default: 24)
- `--secret` - JWT signing secret (default: test-secret-for-local-dev)
- `--decode` - Also print the decoded payload

**Usage with gateway:**
```bash
# Terminal 1: Start gateway with matching secret
JWT_SECRET=test-secret-for-local-dev uvicorn src.main:app --reload

# Terminal 2: Generate token and test
TOKEN=$(python generate_test_token.py | head -1 | cut -d' ' -f2)
curl -H "Authorization: Bearer $TOKEN" http://localhost:8000/api/ingest
```

## nats_status.py

Shows NATS JetStream status (requires port-forward to NATS monitor port).

```bash
kubectl port-forward svc/nats 8222:8222 &
python nats_status.py
```

Output:
```
=== NATS JetStream Status ===
Messages:  1,234
Storage:   45 KB
Streams:   1
Consumers: 1
```

## peek_kalmar1_kafka.js

Peek at Kalmar Energi Team 1's Kafka data stream. Useful for checking their data format.

**Requires Node.js:**
```bash
npm install kafkajs
```

```bash
node peek_kalmar1_kafka.js       # Read 5 messages
node peek_kalmar1_kafka.js 1     # Quick peek at 1 message
node peek_kalmar1_kafka.js 20    # Read 20 messages
```

Note: Their stream uses synthetic meter IDs (`meter-001`, `meter-002`, etc.) that cycle continuously - not suitable for customer-based aggregation.
