# Auth Service

FastAPI service for user authentication with JWT tokens and MongoDB storage.

## API Endpoints

### Authentication Endpoints
| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| POST | `/auth/register` | Register new user (⚠️ deprecated) | No |
| POST | `/auth/login` | Login, returns access + refresh tokens | No |
| POST | `/auth/logout` | Logout (clears cookie) | No |
| POST | `/auth/refresh` | Get new access token using refresh token | No |
| GET | `/auth/me` | Get current user info | Yes (header or cookie) |

### Admin User Management Endpoints
| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| GET | `/auth/users` | List all users (paginated) | Admin only |
| GET | `/auth/users/{user_id}` | Get specific user by ID | Admin only |
| POST | `/auth/users` | Create user with role & customer_id | Admin only |
| PUT | `/auth/users/{user_id}` | Update user (all fields optional) | Admin only |
| DELETE | `/auth/users/{user_id}` | Delete user | Admin only |

### Health Check Endpoints
| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| GET | `/health` | Liveness probe | No |
| GET | `/ready` | Readiness probe (checks MongoDB) | No |

**Note:** ⚠️ `/auth/register` is deprecated. Use `/auth/users` (admin only) to create users with proper `customer_id` assignment.

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

**Roles:** `admin`, `internal`, `customer`, `device`

**Tokens:**
- Access token: 60 min, used for API requests
- Refresh token: 7 days, used to get new access tokens

## Admin User Management Examples

All admin endpoints require `Authorization: Bearer <token>` header with admin role.

### List Users (with pagination)
```bash
GET /auth/users?page=1&page_size=50
Authorization: Bearer <admin_token>
```

### Create User
```bash
POST /auth/users
Authorization: Bearer <admin_token>
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "securepass123",
  "name": "John Doe",
  "role": "customer",
  "customer_id": "1060598736"
}
```

### Update User (partial update)
```bash
PUT /auth/users/{user_id}
Authorization: Bearer <admin_token>
Content-Type: application/json

{
  "role": "admin",
  "customer_id": "1234567890"
}
```

All fields are optional in update requests - only provided fields are updated.

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
