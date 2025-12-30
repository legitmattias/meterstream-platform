# Integration Tests (Newman/Postman)

API integration tests for the MeterStream pipeline.

## CI/CD Pipeline Integration

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

## Running Locally

```bash
# Install
npm install -g newman

# Run
newman run tests/integration/collections/meterstream-api.json \
  --environment tests/integration/environments/staging.json \
  --env-var "admin_password=YOUR_ADMIN_PASSWORD"
```

## Test Scenarios

| Folder | Tests |
|--------|-------|
| 1. Health Checks | Gateway health endpoint |
| 2. Unauthenticated Error Cases | Ingest/query/auth without credentials |
| 3. Auth Flow | Admin creates device user, login, refresh token, logout |
| 4. Ingestion | Device user + internal user ingest data |
| 5. Full Pipeline | Internal user ingests, customer queries |
| 6. Cleanup | Delete created device user (admin) |

## Full Pipeline Tests

The **Full Pipeline** tests verify complete data flow:

1. **Login seeded customer** user for querying
2. **Verify customer cannot ingest** (403 Forbidden)
3. **Internal user** (`ingest_token` from Section 4) ingests test data
4. **Customer user** queries the dashboard and verifies data arrived

**Important:** Pipeline tests require an **empty NATS queue** to work correctly. If there are pending messages from previous test runs, the processor may still be catching up. Failed tests will display a helpful message about checking NATS queue status.

**Notes:**
- Uses both `device` and `internal` roles for ingestion (device is used in production for IoT meters)
- 5s pre-request delay before querying to allow async pipeline processing
- Assertions check values in sequence, not specific hours (handles CET/CEST timezone shifts)

## Environment Variables

| Variable | Description |
|----------|-------------|
| `base_url` | API base URL |
| `test_email` / `test_password` | Internal user for ingestion |
| `seeded_user_email` / `seeded_user_password` | Customer user for querying |
| `seeded_user_customer_id` | Customer ID for pipeline tests |
| `device_email` / `device_password` | Device user for ingestion |
| `admin_email` / `admin_password` | Admin for user creation/cleanup (pass password via CLI) |
