# Ingestion Service

FastAPI service that receives meter readings and publishes them to NATS JetStream.

## Architecture

```
HTTP POST /ingest → Ingestion Service → NATS JetStream (meter.readings)
```

## Local Development

```bash
cd services/ingestion
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Run (requires NATS running locally)
uvicorn src.main:app --reload
```

## API

### POST /ingest

Accepts batch of meter readings:

```json
{
  "readings": [
    {
      "DateTime": "2020-01-01T00:00:00",
      "CUSTOMER": "1060598736",
      "AREA": "Kvarnholmen",
      "Power_Consumption": 0.0112
    }
  ]
}
```

Response:
```json
{
  "accepted": 1,
  "message": "Readings published to queue"
}
```

### GET /health

Liveness probe - returns 200 if running.

### GET /ready

Readiness probe - returns 200 only if NATS is connected.

## Docker

```bash
docker build -t ingestion .
docker run -e NATS_URL=nats://host:4222 -p 8000:8000 ingestion
```

## Tests

```bash
pytest tests/
```
