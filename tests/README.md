# MeterStream Tests

This directory contains integration and load tests for the MeterStream pipeline.

## Structure

```
tests/
├── integration/           # API integration tests (Newman/Postman)
│   ├── collections/       # Test collections
│   │   └── meterstream-api.json
│   └── environments/      # Environment configs
│       └── staging.json
└── load/                  # Load tests (Locust)
    ├── locustfile.py
    └── requirements.txt
```

## Integration Tests (Newman)

Newman runs Postman collections from the command line.

### Prerequisites

```bash
npm install -g newman
```

### Running Tests

```bash
# Run against staging (with admin password for cleanup)
newman run tests/integration/collections/meterstream-api.json \
  --environment tests/integration/environments/staging.json \
  --env-var "admin_password=YOUR_ADMIN_PASSWORD"

# With detailed output
newman run tests/integration/collections/meterstream-api.json \
  --environment tests/integration/environments/staging.json \
  --env-var "admin_password=YOUR_ADMIN_PASSWORD" \
  --reporters cli,json \
  --reporter-json-export results.json

# Custom base URL
newman run tests/integration/collections/meterstream-api.json \
  --env-var "base_url=http://localhost:8080" \
  --env-var "admin_password=YOUR_ADMIN_PASSWORD"
```

### Test Scenarios

| Folder | Tests |
|--------|-------|
| 1. Health Checks | Gateway health endpoint |
| 2. Auth Flow | Register, login, get user, refresh token, logout |
| 3. Ingestion | Single reading, batch, without auth (error case) |
| 4. Full Pipeline | Login seeded user → ingest data → query dashboard/consumption/summary |
| 5. Data Query Errors | Query without auth, query with invalid token |
| 6. Auth Error Cases | Wrong password, missing/invalid token |
| 7. Cleanup | Delete test user (requires admin) |

The **Full Pipeline** tests use a seeded user with `customer_id` to verify the complete data flow:
1. Login as seeded user (e.g., alice.andersson@example.com)
2. JWT contains `customer_id` claim
3. Ingest meter data for that customer
4. Query data through `/api/data/*` endpoints
5. Verify gateway adds `X-Customer-ID` header for customer isolation

### Environment Variables

- `base_url` - API base URL (e.g., `http://194.47.170.217`)
- `test_email` - Test user email for basic auth tests
- `test_password` - Test user password
- `seeded_user_email` - Seeded user with customer_id (e.g., alice.andersson@example.com)
- `seeded_user_password` - Seeded user password (default: testpassword123)
- `seeded_user_customer_id` - Customer ID for pipeline tests (e.g., 1060598736)
- `admin_email` - Admin user email (for cleanup)
- `admin_password` - Admin password (**pass via CLI, not stored in file**)
- `access_token` - Set automatically after login
- `refresh_token` - Set automatically after login
- `seeded_user_token` - Set automatically for pipeline tests

## Load Tests (Locust)

Locust simulates concurrent users for load testing and HPA verification.

### Prerequisites

```bash
cd tests/load
pip install -r requirements.txt
# or
uv pip install -r requirements.txt
```

### Running Tests

```bash
# Interactive mode (opens web UI at http://localhost:8089)
locust -f tests/load/locustfile.py --host=http://staging.meterstream.example

# Headless mode
locust -f tests/load/locustfile.py \
  --host=http://staging.meterstream.example \
  --users 50 \
  --spawn-rate 10 \
  --run-time 5m \
  --headless

# With custom password (for production)
TEST_USER_PASSWORD=strongpass locust -f tests/load/locustfile.py \
  --host=http://prod.example --users 10 --spawn-rate 5 --headless
```

**Environment:**
- `TEST_USER_PASSWORD` - Password for integration-test user (default: testpassword123)

### Load Profiles

| Profile | Users | Spawn Rate | Duration | Purpose |
|---------|-------|------------|----------|---------|
| Smoke | 1 | 1 | 30s | Verify tests work |
| Normal | 10 | 5 | 2m | Baseline performance |
| Stress | 50 | 10 | 5m | Trigger HPA scaling |
| Spike | 100 | 50 | 1m | Sudden load burst |

### User Classes

- **MeterStreamUser** - Standard user, mixed operations (single/batch ingestion, health, auth)
- **HighVolumeUser** - Stress testing, sends large batches rapidly

### Example Commands

```bash
# Smoke test
locust -f tests/load/locustfile.py \
  --host=http://staging.meterstream.example \
  --users 1 --spawn-rate 1 --run-time 30s --headless

# Stress test (for HPA demo)
locust -f tests/load/locustfile.py \
  --host=http://staging.meterstream.example \
  --users 50 --spawn-rate 10 --run-time 5m --headless

# Use only HighVolumeUser class
locust -f tests/load/locustfile.py \
  --host=http://staging.meterstream.example \
  --users 20 --spawn-rate 5 --run-time 3m --headless \
  HighVolumeUser
```

## CI/CD Integration

### Newman in GitLab CI

```yaml
integration-test:
  stage: test
  image: postman/newman:alpine
  script:
    - newman run tests/integration/collections/meterstream-api.json
      --environment tests/integration/environments/staging.json
      --env-var "admin_password=$BOOTSTRAP_ADMIN_PASSWORD"
      --reporters cli,junit
      --reporter-junit-export results.xml
  artifacts:
    reports:
      junit: results.xml
  only:
    - development
    - main
```

### Locust in GitLab CI

```yaml
load-test:
  stage: test
  image: python:3.11-slim
  script:
    - pip install -r tests/load/requirements.txt
    - locust -f tests/load/locustfile.py
      --host=$STAGING_URL
      --users 10 --spawn-rate 5 --run-time 2m
      --headless --html=locust-report.html
  artifacts:
    paths:
      - locust-report.html
  when: manual
  only:
    - development
    - main
```

## Scaling Verification

To verify HPA scaling works (requires HPA to be configured):

```bash
# Terminal 1: Watch processor replicas
watch -n 5 "kubectl get deployment processor -n meterstream -o jsonpath='{.status.replicas}'"

# Terminal 2: Run stress test
locust -f tests/load/locustfile.py \
  --host=http://staging.meterstream.example \
  --users 50 --spawn-rate 10 --run-time 5m --headless

# Expected: Processor replicas should increase during load
```

## Troubleshooting

### Newman tests fail with connection errors
- Verify `base_url` is correct
- Check cluster is accessible
- Test health endpoint manually: `curl $base_url/health`

### Locust login fails
- Ensure test user exists in auth service
- Check auth service logs
- Verify JWT secret is configured

### Load test doesn't trigger scaling
- Verify HPA is configured: `kubectl get hpa -n meterstream`
- Check NATS queue depth: `kubectl exec -it nats-0 -n meterstream -- nats stream info METER_DATA`
- Review HPA events: `kubectl describe hpa processor -n meterstream`
