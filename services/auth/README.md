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

# Start MongoDB (from project root)
make mongo-up

# View MongoDB logs (shows last 50 lines)
make mongo-logs

# Stop MongoDB
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
# Should move to api gateway
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
make auth-test
```

## Deployment

The service is deployed to Kubernetes via GitLab CI/CD:

1. **Build**: `build-auth` job builds Docker image with Kaniko
2. **Deploy**: `deploy-auth-staging` job deploys to K8s cluster
3. **Health checks**: Pipeline verifies /health and /ready endpoints

See `.gitlab-ci.yml` for pipeline configuration.

## Design Decisions & Discussion Points

### Role and Customer ID Assignment Strategy

**Current Implementation Status:**
- All new users automatically get `role: "customer"` at registration
- All new users get `customer_id: null` at registration
- No mechanism exists yet to create `admin` or `internal` users
- No mechanism exists yet to assign users to customers

**Questions for Team Discussion:**

#### 1. How should we create admin and internal users?

**Option A: Manual MongoDB insertion (MVP approach)**
- Create first admin user directly in MongoDB
- Admin can then manage other users via API (future endpoint)
- Pros: Simple, works immediately
- Cons: Requires MongoDB access, not scalable

**Option B: CLI script**
```bash
python scripts/create_admin.py --email admin@example.com --password xxx
```
- Pros: Repeatable, no direct DB access needed
- Cons: Requires server/pod access

**Option C: Seed data in CI/CD**
- Init container creates default admin on deployment
- Pros: Fully automated
- Cons: Credential management complexity

**Team Decision Needed:** Which approach should we implement first?

---

#### 2. How and when should customer_id be assigned?

**Current State:** All users have `customer_id: null`

**Option A: Invite code system (Self-service registration)**
```python
# Registration with invite code
POST /auth/register
{
  "email": "user@example.com",
  "password": "xxx",
  "name": "John",
  "invite_code": "ABC-123"  # Links to customer
}
```
Workflow:
1. Admin creates invite code linked to customer
2. Customer receives invite code
3. User registers with code → `customer_id` auto-assigned

**Option B: Admin assigns after registration**
```python
# New admin endpoint needed
PATCH /auth/users/{user_id}/customer
{
  "customer_id": "cust-123"
}
```
Workflow:
1. User registers normally (customer_id = null)
2. Admin sees new users in admin panel
3. Admin manually links user to customer

**Option C: Defer until real customers exist**
- Keep `customer_id: null` for now
- Implement assignment logic when we have actual customers
- Pros: Don't build what we don't need yet
- Cons: Must be done before production launch

**Team Decision Needed:**
- Which option fits our use case?
- Do we have real customers now, or is this for later?
- Who will be responsible for customer-user linking?

---

#### 3. Role-based data access enforcement

**Contract Requirements:**

| Role | customer_id | Data Access |
|------|-------------|-------------|
| `customer` | `"cust-123"` | Only own customer data in InfluxDB |
| `internal` | `null` or `"internal"` | All data (Kalmar Energi employee) |
| `admin` | `null` | All data + user management |

**Implementation Location:** Backend services (Dashboard, Ingest, etc.)

**Example in Dashboard service:**
```python
# Extract from JWT headers forwarded by Gateway
role = request.headers.get("X-User-Role")
customer_id = request.headers.get("X-Customer-ID")

if role == "customer" and customer_id:
    # Filter InfluxDB query
    query = f'... WHERE customer_id = "{customer_id}"'
elif role in ["admin", "internal"]:
    # No filtering - show all data
    query = '...'
```

**Team Decision Needed:**
- Is each backend service responsible for this filtering?
- Should we create a shared library for role-based filtering?
- Who validates the role/customer_id headers are not spoofed? (Gateway's job)

---

#### 4. API Gateway Integration Checklist

**Critical Changes Required:**

- [ ] **Port mismatch:** Change auth service from port 8001 → 8000
  - Files: `k8s/auth/deployment.yaml`, `k8s/auth/service.yaml`
  - Gateway expects `http://auth:8000`


- [ ] **New endpoint:** `GET /auth/me` ✅ (Implemented)
  - Returns current user info from JWT token
  - Gateway proxies: `GET /api/auth/me` → `GET /auth/me`

**Already Compatible:**
- ✅ Algorithm: HS256
- ✅ Required JWT claims: sub, role, customer_id, exp
- ✅ Roles: admin, internal, customer
- ✅ Endpoints: /login, /register
- ✅ K8s service name: `auth`


---

#### 5. Missing Admin Endpoints (Future Work)

To fully implement role/customer management, we'll need:

```python
# User management (admin only)
PATCH /auth/users/{user_id}/role
  → Update user role

PATCH /auth/users/{user_id}/customer
  → Assign user to customer

GET /auth/users
  → List all users (paginated)

# Customer management (admin only)
POST /auth/customers
  → Create new customer organization

GET /auth/customers
  → List all customers

# Invite system (if we choose Option A above)
POST /auth/invites
  → Generate invite code for customer

GET /auth/invites/{code}
  → Validate invite code
```

**Team Decision Needed:**
- Which endpoints are MVP vs. future work?
- Should this be separate "Admin API" service?

---

### Action Items Before Gateway Integration

1. **Immediate (this sprint):**
   - [ ] Decide on admin user creation strategy (recommend: manual MongoDB for MVP)
   - [ ] Create first admin user in MongoDB
   - [ ] Test admin login flow
   - [ ] Change ports from 8001 → 8000
   - [ ] Coordinate JWT_SECRET naming with Gateway team

2. **Before production (next sprint):**
   - [ ] Decide customer_id assignment strategy
   - [ ] Implement chosen customer assignment mechanism
   - [ ] Document role-based access control for backend teams
   - [ ] Test full auth flow: register → login → /me → backend access

3. **Future enhancements:**
   - [ ] Admin endpoints for user management
   - [ ] Customer management system
   - [ ] Invite code system (if needed)

## Future Migration to API Gateway

**NOTE:** The following components are marked for migration to the API Gateway service:

### Components to migrate:
- **GET /auth/verify endpoint** ([auth_router.py:158-187](services/auth/src/auth_router.py#L158-L187))
- **verify_token() function** ([jwt_service.py:52-77](services/auth/src/jwt_service.py#L52-L77))
- **VerifyResponse model** ([models.py:32-43](services/auth/src/models.py#L32-L43))

### Components that stay in Auth Service:
- **verify_refresh_token()** - Only Auth Service handles refresh tokens
- All other endpoints (/register, /login, /refresh)

### Migration considerations:
- The API Gateway will need the same JWT secret key (`JWT_SECRET`) to verify tokens
- The API Gateway will validate tokens for all incoming requests to protected endpoints
- After migration, the /verify endpoint can be removed from Auth Service

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
