# Auth Service

FastAPI service for user authentication with JWT tokens and MongoDB storage.

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/auth/register` | Register new user |
| POST | `/auth/login` | Login, returns access + refresh tokens |
| POST | `/auth/refresh` | Get new access token using refresh token |
| GET | `/auth/me` | Get current user info (requires auth header) |
| DELETE | `/auth/users/{user_id}` | Delete user (admin only) |
| GET | `/health` | Liveness probe |
| GET | `/ready` | Readiness probe (checks MongoDB) |

## JWT Structure

```json
{
  "sub": "user-id",
  "email": "user@example.com",
  "role": "customer",
  "customer_id": "1060598736",
  "exp": 1734567890
}
```

**Roles:** `admin`, `internal`, `customer`

**Tokens:**
- Access token: 60 min, used for API requests
- Refresh token: 7 days, used to get new access tokens

## Local Development

```bash
cd services/auth
cp .env.example .env

# Start MongoDB (from project root)
make mongo-up

# Run service
make auth-run

# Run tests
make auth-test
```

## Environment Variables

| Variable | Description |
|----------|-------------|
| `MONGODB_URL` | MongoDB connection string |
| `DATABASE_NAME` | Database name |
| `JWT_SECRET` | Secret key for JWT signing |
| `BOOTSTRAP_ADMIN_PASSWORD` | Auto-creates admin user on startup |
| `SEED_TEST_DATA` | Set `true` to seed test users (staging only) |
| `TEST_USER_PASSWORD` | Password for seeded test users (default: testpassword123) |

## Bootstrap & Seeding

On startup, the service:
1. Creates admin user if `BOOTSTRAP_ADMIN_PASSWORD` is set and no admin exists
2. Seeds test users if `SEED_TEST_DATA=true` (31 users including integration-test and data-loader)

Both are idempotent - safe to run multiple times.

## Deployment

Deployed via GitLab CI/CD. See `.gitlab-ci.yml` for pipeline configuration.
