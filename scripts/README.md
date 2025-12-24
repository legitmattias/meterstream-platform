# Scripts

Utility scripts for testing and monitoring.

## Setup

```bash
pip install -r requirements.txt
```

## produce_test_data.py

Sends test data to the Ingestion Service via the API Gateway. Authenticates as `data-loader@example.com` (seeded test user).

**Features:**
- Checkpoint support: saves progress after each batch, auto-resumes on restart
- Automatic token refresh when JWT expires during long-running loads

```bash
# Send to staging (authenticates automatically, resumes from checkpoint)
python produce_test_data.py --url http://194.47.170.217

# Load large dataset with safe rate (recommended for first load)
python produce_test_data.py --url http://194.47.170.217 \
  --file ../data/test_data_large.csv --batch-size 50 --rate 2

# Start fresh, ignoring any existing checkpoint
python produce_test_data.py --url http://194.47.170.217 --reset-checkpoint

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
- `--reset-checkpoint` - Ignore existing checkpoint and start from beginning
- `--checkpoint-file` - Path to checkpoint file (default: .produce_checkpoint)

**Environment:**
- `TEST_USER_PASSWORD` - Password for data-loader user (default: testpassword123)

## extract_test_data.py

Extracts test data subsets from the full Kalmar Energi dataset. By default, uses customer IDs that match seeded test users in the auth service, ensuring portal users can see their own data.

**Requires:** Access to the source dataset (`meterstream-filer/data/final_df.csv/final_df.csv`)

```bash
# Seeded customers (default), 7 days - small dataset
python extract_test_data.py --start 2020-01-01 --end 2020-01-07 -o test_data_small.csv

# Seeded customers, 3 months - medium dataset
python extract_test_data.py --start 2020-01-01 --end 2020-03-31 -o test_data_medium.csv

# Seeded customers, full 4 years - large dataset
python extract_test_data.py -o test_data_large.csv

# Random 50 customers instead of seeded (for testing)
python extract_test_data.py --random-customers -n 50 -o test_data_random.csv
```

**Options:**
- `-o, --output` - Output filename in data/ directory (required)
- `--start` - Start date YYYY-MM-DD (default: 2020-01-01)
- `--end` - End date YYYY-MM-DD (default: 2023-12-31)
- `--random-customers` - Use random customers instead of seeded customer IDs
- `-n, --customers` - Number of customers (only with --random-customers)
- `--seed` - Random seed for reproducible selection (only with --random-customers)
- `--source` - Custom source file path
- `--output-dir` - Custom output directory

**Seeded customers:** The script includes 20 customer IDs that match the seeded users in `services/auth/src/seed_test_data.py`. This ensures Alice, Bob, and other test users can see their own data in the portal.

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
