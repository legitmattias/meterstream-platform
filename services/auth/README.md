# Auth Service

FastAPI service that handles user authentication with JWT tokens and MongoDB storage.

## Architecture

```
HTTP POST /auth/register → Auth Service → MongoDB (users collection)
HTTP POST /auth/login → Auth Service → JWT Token (access + refresh)
HTTP POST /auth/refresh → Auth Service → New Access Token
HTTP GET /auth/verify → Auth Service → Token Validation
```

## JWT Token Structure

The service implements **role-based authentication** with **stateless data scoping**:

```json
{
  "sub": "user-id-123",           // Authentication: MongoDB user ID (who are you)
  "email": "user@example.com",
  "role": "customer",             // Authorization: what can you do (admin, internal, customer)
  "customer_id": "cust-456",      // Data scoping: what can you see (InfluxDB access)
  "exp": 1734567890,              // Expiration time
  "iat": 1734564290               // Issued at
}
```

**Token Types:**
- **Access Token**: Short-lived (60 min), contains all claims, used for API requests
- **Refresh Token**: Long-lived (7 days), only contains user_id, used to get new access tokens

**Roles:**
- `admin` - Full system access, customer_id is null
- `internal` - Internal user access, customer_id is null
- `customer` - Customer user access, customer_id links to InfluxDB data

## Local Development

```bash
cd services/auth
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Copy environment template
cp .env.example .env

# (requires MongoDB running locally)
# from root
make mongo-up
# or run
docker run -d --name mongodb-dev -p 27017:27017 mongo:7

# Mongo logs ( shows last 50 lines)
make mongo-logs

# Stop mongo db
make mongo-down


# Run app
make auth-run
# Run tests on auth app
make auth-test
# or
uvicorn src.main:app --reload

# Deactivate venv enviroment
deactivate
```

## API Endpoints

### POST /auth/register

Register a new user:

```json
{
  "email": "user@example.com",
  "password": "securepassword123",
  "name": "John Doe",
  "role": "customer",
  "customer_id": "cust-123"
}
```

Response:
```json
{
  "id": "507f1f77bcf86cd799439011",
  "email": "user@example.com",
  "name": "John Doe",
  "created_at": "2025-01-01T12:00:00",
  "role": "customer",
  "customer_id": "cust-123"
}
```

### POST /auth/login

Login with credentials:

```json
{
  "email": "user@example.com",
  "password": "securepassword123"
}
```

Response:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 3600,
  "user": {
    "id": "507f1f77bcf86cd799439011",
    "email": "user@example.com",
    "name": "John Doe",
    "role": "customer",
    "customer_id": "cust-123"
  }
}
```

### POST /auth/refresh

Get new access token using refresh token:

```json
{
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

Response:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 3600,
  "user": {
    "id": "507f1f77bcf86cd799439011",
    "email": "user@example.com",
    "name": "John Doe",
    "role": "customer",
    "customer_id": "cust-123"
  }
}
```

### GET /auth/verify?token={jwt_token}

Verify JWT token (used by API Gateway):

Response:
```json
{
  "valid": true,
  "user_id": "507f1f77bcf86cd799439011",
  "email": "user@example.com",
  "role": "customer",
  "customer_id": "cust-123"
}
```

### GET /health

Liveness probe - returns 200 if service is running.

Response:
```json
{
  "status": "healthy",
  "service": "auth"
}
```

### GET /ready

Readiness probe - returns 200 only if MongoDB is connected.

Response (ready):
```json
{
  "status": "ready"
}
```

Response (not ready):
```json
{
  "status": "not ready"
}
```
Status: 503

## Testing

```bash
# Run tests
pytest

# Run tests with coverage
pytest --cov=src tests/

# Run specific test file
pytest tests/test_jwt_service.py -v
```

## Deployment

The service is deployed to Kubernetes via GitLab CI/CD:

1. **Build**: `build-auth` job builds Docker image with Kaniko
2. **Deploy**: `deploy-auth-staging` job deploys to K8s cluster
3. **Health checks**: Pipeline verifies /health and /ready endpoints

See `.gitlab-ci.yml` for pipeline configuration.

## Environment Variables

Required environment variables (see `.env.example`):

- `MONGODB_URL` - MongoDB connection string
- `DATABASE_NAME` - MongoDB database name
- `JWT_SECRET_KEY` - Secret key for JWT signing (change in production!)
- `JWT_ALGORITHM` - JWT algorithm (default: HS256)
- `JWT_EXPIRE_MINUTES` - Access token expiration (default: 60)
- `JWT_REFRESH_EXPIRE_DAYS` - Refresh token expiration (default: 7)
- `SERVICE_NAME` - Service name for logging
- `DEBUG` - Debug mode (default: false)
- `LOG_LEVEL` - Logging level (default: INFO)
