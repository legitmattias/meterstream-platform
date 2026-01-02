# Processor Service - Kubernetes Manifests

Deploys the Data Processor service to Kubernetes.

Processor consumes meter readings from **NATS JetStream** and writes them to **InfluxDB**.

## Components

| File | Description |
|------|-------------|
| `deployment.yaml` | Processor deployment |
| `service.yaml` | ClusterIP service |
| `hpa.yaml` | KEDA ScaledObject for autoscaling |

## Deploy

```bash
kubectl apply -f service.yaml
kubectl apply -f deployment.yaml
kubectl apply -f hpa.yaml
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

## Autoscaling (HPA with KEDA)

The processor automatically scales from 1 to 10 pods based on NATS queue depth.

### Verify KEDA is installed

```bash
kubectl get pods -n keda
```

### Check autoscaling status

```bash
kubectl get scaledobject -n meterstream
kubectl get hpa -n meterstream
watch kubectl get pods -n meterstream
```

### Verify NATS consumer

```bash
kubectl exec -it nats-0 -n meterstream -- nats consumer ls METER_DATA
```

If missing, create consumer:

```bash
kubectl exec -it nats-0 -n meterstream -- nats consumer add METER_DATA processor-consumer \
  --pull \
  --deliver all \
  --ack explicit \
  --max-deliver -1 \
  --filter "meter.readings"
```

### Configuration (hpa.yaml)

Key settings to adjust scaling behavior:

```yaml
minReplicaCount: 1     # Minimum pods (always running)
maxReplicaCount: 10    # Maximum pods under load
pollingInterval: 15    # Check queue every N seconds
cooldownPeriod: 60     # Wait N seconds before scaling down
lagThreshold: "50"     # Scale up when queue > N messages
```

**For faster scaling:**
- Decrease `pollingInterval` (e.g., 5)
- Decrease `lagThreshold` (e.g., 25)

**For cost optimization:**
- Increase `cooldownPeriod` (e.g., 300)
- Increase `lagThreshold` (e.g., 100)

### Load testing

For load tests to trigger autoscaling, see [/tests/README.md](../../../tests/README.md)