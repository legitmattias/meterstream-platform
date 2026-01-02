# Query Service

Analytics query service with customer isolation. Provides weekly, monthly, hourly, and summary consumption data for the portal dashboard.

## Features

- Query weekly per-day consumption (Mon-Sun)
- Query monthly per-day consumption (1-31)
- Query hourly consumption for a specific date (0-23 hours)
- Get summary statistics (total, average) with year filtering
- Customer isolation via X-Customer-ID header (set by gateway)
- Year filtering ("2024", "2025", "All")
- Queries InfluxDB meter_readings bucket with Flux

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

### GET /api/data/dashboard

Get all dashboard data in one request (weekly, monthly, hourly, and summary).

**Headers:**
- `X-Customer-ID`: Customer ID (set by gateway from JWT)

**Query Params:**
- `year`: Optional year filter ("2024", "2025", "All")
- `month`: Optional month (1-12) for monthly view
- `date`: Optional date (YYYY-MM-DD) for hourly view

**Examples:**
```
# Get weekly data for 2025
GET /api/data/dashboard?year=2025

# Get weekly + monthly for Jan 2025
GET /api/data/dashboard?year=2025&month=1

# Get hourly breakdown for specific date
GET /api/data/dashboard?date=2025-12-18

# Get all years data
GET /api/data/dashboard?year=All
```

**Response:**
```json
{
  "customer_id": "1234567890",
  "year": "2025",
  "month": null,
  "date": null,
  "weekly_days": [
    {"day": "Mon", "consumption": 120.5},
    {"day": "Tue", "consumption": 140.2},
    {"day": "Wed", "consumption": 110.8},
    {"day": "Thu", "consumption": 160.3},
    {"day": "Fri", "consumption": 130.1},
    {"day": "Sat", "consumption": 90.4},
    {"day": "Sun", "consumption": 100.6}
  ],
  "monthly_days": [
    {"day": 1, "consumption": 45.2},
    {"day": 2, "consumption": 43.8},
    {"day": 3, "consumption": 48.1}
  ],
  "hourly": [],
  "total": 4523.5,
  "average": 150.8
}
```

### GET /api/health

Health check endpoint.

**Response:**
```json
{
  "status": "ok"
}
```

## Data Flow

```
React Frontend (portal)
    ↓ (GET /api/data/dashboard?year=2025&month=1)
Gateway (validates JWT, extracts customer_id, adds X-Customer-ID header)
    ↓ (proxies with header)
Query Service (validates header, builds Flux queries)
    ↓
InfluxDB (executes queries, returns meter_readings grouped by time)
    ↓
Query Service (aggregates results into weekly/monthly/hourly/summary)
    ↓
Frontend (renders charts with data)
```

## Gateway Routing

The gateway should forward requests to the Query Service with the `X-Customer-ID` header:

```python
# In gateway main.py
@app.api_route(
    "/api/data/{path:path}",
    methods=["GET"],
)
async def query_proxy(request: Request, path: str):
    """Proxy requests to Query Service with customer isolation."""
    # Validate JWT and extract customer_id
    token_payload = await validate_jwt(request)
    customer_id = token_payload.get("customer_id")
    
    # Add customer ID header
    headers = dict(request.headers)
    headers["X-Customer-ID"] = customer_id
    
    # Proxy to Query Service
    target_url = f"{settings.query_service_url}/api/data/{path}"
    async with httpx.AsyncClient() as client:
        response = await client.get(target_url, headers=headers, params=request.query_params)
    return JSONResponse(response.json(), status_code=response.status_code)
```

And in gateway `config.py`:
```python
query_service_url: str = "http://query:8000"
```
