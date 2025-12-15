# Processor Service - Kubernetes Manifests

Deploys the Data Processor service to Kubernetes.

Processor consumes meter readings from **NATS JetStream** and writes them to **InfluxDB**.

## Components

| File | Description |
|------|-------------|
| `deployment.yaml` | Processor deployment |
| `service.yaml` | ClusterIP service |

## Deploy

```bash
kubectl apply -f service.yaml
kubectl apply -f deployment.yaml
```


### Prerequisites

* **NATS** is running in namespace `meterstream` (Service name `nats`).
* **InfluxDB** is running in namespace `meterstream` (Service name `influxdb`).
* **Secret** `influxdb-init` exists in namespace `meterstream` and contains:
  * `DOCKER_INFLUXDB_INIT_ORG`
  * `DOCKER_INFLUXDB_INIT_BUCKET`
  * `DOCKER_INFLUXDB_INIT_ADMIN_TOKEN`

## Configuration

Environment variables (set in `deployment.yaml`):

### NATS

* **`NATS_URL`** - NATS server address (e.g. `nats://nats:4222`)
* **`NATS_STREAM`** - JetStream stream name (e.g. `METER_DATA`)
* **`NATS_SUBJECT`** - Subject to consume (e.g. `meter.readings`)

### InfluxDB

* **`INFLUX_URL`** - InfluxDB base URL (e.g. `http://influxdb:8086`)
* **`INFLUX_ORG`** - From K8s secret `influxdb-init` key `DOCKER_INFLUXDB_INIT_ORG`
* **`INFLUX_BUCKET`** - From K8s secret `influxdb-init` key `DOCKER_INFLUXDB_INIT_BUCKET`
* **`INFLUX_TOKEN`** - From K8s secret `influxdb-init` key `DOCKER_INFLUXDB_INIT_ADMIN_TOKEN`

## Verify

```bash
kubectl -n meterstream get pods -l app=processor
kubectl -n meterstream logs -l app=processor
kubectl -n meterstream get svc processor
```

(Optional) Port-forward the service and test endpoints:

```bash
kubectl -n meterstream port-forward svc/processor 8000:8000
curl -sS http://127.0.0.1:8000/health
curl -sS http://127.0.0.1:8000/ready
```

## Endpoints

| Path | Method | Description |
|------|--------|-------------|
| `/health` | GET | Liveness probe |
| `/ready` | GET | Readiness probe (checks NATS connection) |