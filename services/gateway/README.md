# API Gateway

FastAPI service that validates JWT tokens and proxies requests to backend services.

## Architecture

```
Client → Gateway → Backend Services (Auth, Ingestion, etc.)
            │
            └── Validates JWT
            └── Adds X-User-* headers
```

## Local Development

```bash
cd services/gateway
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Create .env file
cp .env.example .env

# Run
uvicorn src.main:app --reload
```

## Testing

```bash
cd services/gateway
source .venv/bin/activate

# Run all tests
JWT_SECRET=test-secret pytest -v

# Run specific test file
JWT_SECRET=test-secret pytest tests/test_middleware.py -v

# Run with coverage (requires pytest-cov)
JWT_SECRET=test-secret pytest --cov=src --cov-report=term-missing
```

Note: `JWT_SECRET` environment variable is required even for tests.

## API

### Routes

| Path | Auth | Backend |
|------|------|---------|
| `/api/auth/*` | No | Auth Service |
| `/api/ingest` | JWT required | Ingestion Service |
| `/health` | No | Gateway health |

### Headers Added (authenticated routes)

Gateway extracts JWT claims and forwards as headers:
- `X-User-ID` - User identifier (from `sub` claim)
- `X-User-Role` - User role (customer/internal/admin)
- `X-Customer-ID` - Customer identifier (if present)

## Configuration

Environment variables:
- `JWT_SECRET` - Required. Shared with Auth Service. Stored in GitLab CI/CD variables.
- `JWT_ALGORITHM` - Default: HS256
- `AUTH_SERVICE_URL` - Default: http://auth:8000
- `INGESTION_SERVICE_URL` - Default: http://ingestion:8000
- `LOG_LEVEL` - Default: INFO

## Docker

```bash
docker build -t gateway .
docker run -e JWT_SECRET=your-secret -p 8000:8000 gateway
```

## Testing with Mock Tokens

Generate test tokens (requires `python-jose`):

```bash
python scripts/generate_test_token.py --decode
```

Use the token:
```bash
curl -H "Authorization: Bearer <token>" http://localhost:8000/api/ingest
```
