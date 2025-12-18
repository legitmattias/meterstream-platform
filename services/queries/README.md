# Query Service

Analytics query service with customer isolation.

## Features

- Query consumption data with time aggregation
- Get summary statistics (total, average, max, min)
- Customer isolation via X-Customer-ID header (set by gateway)
- Queries InfluxDB meter_readings bucket

## Environment Variables

```
INFLUX_URL=http://influxdb:8086
INFLUX_ORG=meterstream
INFLUX_BUCKET=meterstream
INFLUX_TOKEN=<token>
INFLUX_MEASUREMENT=meter_readings
LOG_LEVEL=INFO
```

## API Endpoints

### GET /api/data/consumption

Query consumption data for customer.

**Headers:**
- `X-Customer-ID`: Customer ID (set by gateway from JWT)

**Query Params:**
- `period`: "daily" (24 days), "weekly" (4 weeks), or "monthly" (12 months) - default: daily

**Response:**
```json
{
  "customer_id": "1234567890",
  "period": "daily",
  "data": [
    {"timestamp": "2025-12-17T00:00:00Z", "consumption": 45.2},
    {"timestamp": "2025-12-16T00:00:00Z", "consumption": 43.8}
  ]
}
```

### GET /api/data/summary

Get summary statistics for customer.

**Headers:**
- `X-Customer-ID`: Customer ID (set by gateway from JWT)

**Query Params:**
- `period`: "daily" (24 days), "weekly" (4 weeks), or "monthly" (12 months) - default: daily

**Response:**
```json
{
  "customer_id": "1234567890",
  "period": "daily",
  "total": 892.5,
  "average": 37.2
}
```

### GET /api/data/dashboard

Get all dashboard data at once (consumption + summary).

**Headers:**
- `X-Customer-ID`: Customer ID (set by gateway from JWT)

**Query Params:**
- `period`: "daily" (24 days), "weekly" (4 weeks), or "monthly" (12 months) - default: daily

**Response:**
```json
{
  "customer_id": "1234567890",
  "period": "daily",
  "consumption": [
    {"timestamp": "2025-12-17T00:00:00Z", "consumption": 45.2},
    {"timestamp": "2025-12-16T00:00:00Z", "consumption": 43.8}
  ],
  "summary": {
    "customer_id": "1234567890",
    "period": "daily",
    "total": 892.5,
    "average": 37.2
  }
}
```

## Data Flow

```
React Frontend (portal)
    ↓ (GET /api/data/consumption?range_hours=24)
Gateway (validates JWT, adds X-Customer-ID header)
    ↓ (proxies with header)
Query Service (validates header, queries InfluxDB)
    ↓
InfluxDB (returns meter_readings filtered by customer)
    ↓
Query Service (formats response)
    ↓
Frontend (renders with chart library)
```

## Gateway Routing

Add to gateway `main.py`:

```python
# Analytics routes - JWT validation + customer isolation
@app.api_route(
    "/api/data/{path:path}",
    methods=["GET", "POST"],
)
async def analytics_proxy(request: Request, path: str):
    """Proxy requests to Query Service with JWT validation."""
    token_payload = await validate_jwt(request)
    # Extract customer_id from JWT claims
    target_url = f"{settings.query_service_url}/{path}"
    return await proxy_request(request, target_url, token_payload)
```

And in `config.py`:
```python
query_service_url: str = "http://query:8000"
```
