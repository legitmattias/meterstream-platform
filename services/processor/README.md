# Data Processor Service

A Python-based microservice designed to consume energy meter readings from **NATS JetStream**, validate the data, and persist it to **InfluxDB** for time-series analysis. Built with FastAPI.

## Architecture

1.  **Input:** Subscribes to the `meter.readings` subject on NATS JetStream.
2.  **Processing:** Validates incoming JSON payloads against strict Pydantic models.
3.  **Output:** Converts data to *InfluxDB Line Protocol* and writes to the database.

## Configuration

The application is configured via Environment Variables.

| Variable | Default | Description |
| :--- | :--- | :--- |
| `NATS_URL` | `nats://nats:4222` | NATS server address. |
| `NATS_STREAM` | `METER_DATA` | Name of the JetStream stream. |
| `NATS_SUBJECT` | `meter.readings` | Subject to subscribe to. |
| `INFLUX_URL` | `http://influxdb:8086` | InfluxDB API address. |
| `INFLUX_ORG` | `meterstream` | Target InfluxDB organization. |
| `INFLUX_BUCKET` | `meterstream` | Target InfluxDB bucket. |
| `INFLUX_TOKEN` | *Required* | Authentication token for InfluxDB. |
| `INFLUX_MEASUREMENT`| `meter_readings` | Measurement name for the time series. |

### Kubernetes Integration

In the `meterstream` namespace, the environment variables above are populated from the `influxdb-init` secret.

**Secret Mapping (`influxdb-init`):**
* `INFLUX_ORG` &larr; `DOCKER_INFLUXDB_INIT_ORG`
* `INFLUX_BUCKET` &larr; `DOCKER_INFLUXDB_INIT_BUCKET`
* `INFLUX_TOKEN` &larr; `DOCKER_INFLUXDB_INIT_ADMIN_TOKEN`

## Data Format

The service expects JSON messages in the following format (case-sensitive):

```json
{
  "DateTime": "2023-10-27T10:00:00",
  "CUSTOMER": "1060598736",
  "AREA": "Kvarnholmen",
  "Power_Consumption": 0.0112
}