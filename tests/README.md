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

### CI/CD Pipeline Integration

Integration tests run **automatically in the CI/CD pipeline** after staging deployment:

**Pipeline Stage Order:**
1. `test` - Unit tests
2. `build` - Docker images
3. `deploy-staging` - Deploy to staging
4. **`integration-test`** - Newman tests run here (manual trigger)
5. `deploy-prod` - Production deployment

The `newman-integration-test` job:
- Runs after all core services are deployed to staging
- Uses `postman/newman:alpine` Docker image
- Generates JUnit test reports in GitLab
- **Fails the pipeline** if any test fails
- Must be manually triggered

**Note:** Load tests remain manual and are NOT included in the pipeline.

### Running Locally

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
| 5. Full Pipeline | Internal user ingests, customer queries |
| 6. Cleanup | Delete test user (requires admin) |

### Full Pipeline Tests

The **Full Pipeline** tests verify complete data flow:

1. **Internal user** (`test_email`) logs in and ingests test data
2. **Customer user** (`seeded_user_email`) logs in and queries the data
3. Tests verify exact values are returned (timezone-independent assertions)

**Notes:**
- Uses `internal` role for ingestion (not `device` - that's for IoT meters)
- 5s pre-request delay before querying to allow async pipeline processing
- Assertions check values in sequence, not specific hours (handles CET/CEST timezone shifts)

### Environment Variables

| Variable | Description |
|----------|-------------|
| `base_url` | API base URL |
| `test_email` / `test_password` | Internal user for ingestion |
| `seeded_user_email` / `seeded_user_password` | Customer user for querying |
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
