# MeterStream Tests

Integration and load tests for the MeterStream pipeline.

## Structure

```
tests/
├── integration/           # API integration tests (Newman/Postman)
│   ├── collections/
│   │   └── meterstream-api.json
│   └── environments/
│       └── staging.json
└── load/                  # Load tests (Locust)
    ├── locustfile.py
    └── requirements.txt
```

## Integration Tests (Newman)

```bash
# Install
npm install -g newman

# Run
newman run tests/integration/collections/meterstream-api.json \
  --environment tests/integration/environments/staging.json \
  --env-var "admin_password=YOUR_ADMIN_PASSWORD"
```

### Test Scenarios

| Folder | Tests |
|--------|-------|
| 1. Health Checks | Gateway health endpoint |
| 2. Unauthenticated Error Cases | Ingest/query/auth without credentials |
| 3. Auth Flow | Register, login, refresh token, logout |
| 4. Ingestion | Single reading, batch readings |
| 5. Full Pipeline | Seeded user → ingest → query dashboard/consumption/summary |
| 6. Cleanup | Delete test user (requires admin) |

The **Full Pipeline** tests verify complete data flow using a seeded user with `customer_id`.

### Environment Variables

| Variable | Description |
|----------|-------------|
| `base_url` | API base URL |
| `test_email` / `test_password` | Test user credentials |
| `seeded_user_email` / `seeded_user_password` | Seeded user with customer_id |
| `seeded_user_customer_id` | Customer ID for pipeline tests |
| `admin_password` | Admin password (pass via CLI) |

## Load Tests (Locust)

```bash
# Install
pip install -r tests/load/requirements.txt

# Run (interactive - opens web UI at http://localhost:8089)
locust -f tests/load/locustfile.py --host=http://194.47.170.217

# Run (headless)
locust -f tests/load/locustfile.py \
  --host=http://194.47.170.217 \
  --users 50 --spawn-rate 10 --run-time 5m --headless
```

### User Classes

- **MeterStreamUser** - Standard user, mixed operations (single/batch ingestion, health, auth)
- **HighVolumeUser** - Stress testing, sends large batches rapidly

### Load Profiles

| Profile | Users | Spawn Rate | Duration | Purpose |
|---------|-------|------------|----------|---------|
| Smoke | 1 | 1 | 30s | Verify tests work |
| Normal | 10 | 5 | 2m | Baseline performance |
| Stress | 50 | 10 | 5m | Trigger HPA scaling |
| Spike | 100 | 50 | 1m | Sudden load burst |

### Example Commands

```bash
# Smoke test
locust -f tests/load/locustfile.py \
  --host=http://194.47.170.217 \
  --users 1 --spawn-rate 1 --run-time 30s --headless

# Stress test (for HPA demo)
locust -f tests/load/locustfile.py \
  --host=http://194.47.170.217 \
  --users 50 --spawn-rate 10 --run-time 5m --headless

# Use only HighVolumeUser class
locust -f tests/load/locustfile.py \
  --host=http://194.47.170.217 \
  --users 20 --spawn-rate 5 --run-time 3m --headless \
  HighVolumeUser
```

**Environment:** `TEST_USER_PASSWORD` - Password for test user (default: testpassword123)
