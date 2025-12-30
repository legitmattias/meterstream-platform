# Load Tests (Locust)

Load and stress tests for the MeterStream pipeline.

**Note:** Load tests are manual and NOT included in the CI/CD pipeline.

## Running Load Tests

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

## User Classes

- **MeterStreamUser** - Standard user, mixed operations (single/batch ingestion, health, auth)
- **HighVolumeUser** - Stress testing, sends large batches rapidly

## Load Profiles

| Profile | Users | Spawn Rate | Duration | Purpose |
|---------|-------|------------|----------|---------|
| Smoke | 1 | 1 | 30s | Verify tests work |
| Normal | 10 | 5 | 2m | Baseline performance |
| Stress | 50 | 10 | 5m | Trigger HPA scaling |
| Spike | 100 | 50 | 1m | Sudden load burst |

## Example Commands

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

## Environment Variables

| Variable | Description |
|----------|-------------|
| `TEST_USER_PASSWORD` | Password for test user (default: testpassword123) |
