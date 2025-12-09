# Auth Service

FastAPI service that handles user authentication with JWT tokens and MongoDB storage.

## Architecture

```
HTTP POST /auth/register → Auth Service → MongoDB (users collection)
HTTP POST /auth/login → Auth Service → JWT Token
HTTP GET /auth/verify → Auth Service → Token Validation
```

## Local Development

```bash
cd services/auth
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# (requires MongoDB running locally)
# from root
make mongo-up
# or run
docker run -d --name mongodb-dev -p 27017:27017 mongo:7


# Run app
make auth-run
# or
uvicorn src.main:app --reload
```

## API

### POST /auth/register

Register a new user:

```json
{
  "email": "user@example.com",
  "password": "securepassword123",
  "name": "John Doe"
}
```

Response:
```json
{
  "id": "507f1f77bcf86cd799439011",
  "email": "user@example.com",
  "name": "John Doe",
  "created_at": "2025-01-01T12:00:00",
  "role": "user"
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
  "token_type": "bearer",
  "expires_in": 3600
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
  "role": "user"
}
```

### GET /auth/health

Liveness probe - returns 200 if running.

### GET /ready

Readiness probe - returns 200 only if MongoDB is connected.

