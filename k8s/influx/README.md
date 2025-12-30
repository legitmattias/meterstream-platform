# InfluxDB - Kubernetes Manifests

Deploys **InfluxDB 2.x** to Kubernetes with **CQRS (Command Query Responsibility Segregation)** architecture using Edge Data Replication.

## Architecture

MeterStream uses two InfluxDB instances for CQRS separation:

```
                    ┌─────────────────┐
                    │    Processor    │
                    │   (writes)      │
                    └────────┬────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────┐
│                     WRITE PATH                               │
│  ┌─────────────────┐         ┌─────────────────┐            │
│  │  influxdb       │ ──────► │  influxdb-read  │            │
│  │  (write)        │  Edge   │  (read replica) │            │
│  │  StatefulSet    │  Repli- │  StatefulSet    │            │
│  └─────────────────┘  cation └─────────────────┘            │
└─────────────────────────────────────────────────────────────┘
                                       │
                   ┌───────────────────┼───────────────────┐
                   │                   │                   │
                   ▼                   ▼                   ▼
           ┌──────────────┐    ┌──────────────┐    ┌──────────────┐
           │   Queries    │    │   Grafana    │    │   (Future    │
           │   Service    │    │              │    │   readers)   │
           └──────────────┘    └──────────────┘    └──────────────┘
                             READ PATH
```

- **Write instance** (`influxdb`): Processor writes meter readings here
- **Read instance** (`influxdb-read`): Queries/Grafana read from here
- **Replication**: Native InfluxDB Edge Data Replication syncs data

---

## Components

| File | Description |
|------|-------------|
| `influx.yaml` | InfluxDB WRITE instance (Processor writes here) |
| `influx-read.yaml` | InfluxDB READ instance (Queries/Grafana read here) |
| `replication-job.yaml` | Job to configure Edge Data Replication |

---

## Prerequisites

### Write Instance Secret

A Kubernetes Secret named **`influxdb-init`** must exist in namespace `meterstream`:

- `DOCKER_INFLUXDB_INIT_MODE`
- `DOCKER_INFLUXDB_INIT_USERNAME`
- `DOCKER_INFLUXDB_INIT_PASSWORD`
- `DOCKER_INFLUXDB_INIT_ORG`
- `DOCKER_INFLUXDB_INIT_BUCKET`
- `DOCKER_INFLUXDB_INIT_ADMIN_TOKEN`
- `DOCKER_INFLUXDB_INIT_RETENTION`

### Read Instance Secret

A Kubernetes Secret named **`influxdb-read-init`** must exist in namespace `meterstream`:

Same keys as above, but with a **different admin token** for security.

> Both secrets are created by GitLab CI/CD from environment variables.

---

## Deployment Order

1. Deploy write instance: `kubectl apply -f influx.yaml`
2. Deploy read instance: `kubectl apply -f influx-read.yaml`
3. Run replication setup: `kubectl apply -f replication-job.yaml`

The replication job is idempotent - it checks for existing configuration before creating.

---

## Verification

Check replication status:

```bash
kubectl exec -it influxdb-0 -n meterstream -- \
  influx replication list --host http://localhost:8086 --token $TOKEN
```

Verify data is replicated:

```bash
kubectl exec -it influxdb-read-0 -n meterstream -- \
  influx query 'from(bucket:"meterstream") |> range(start:-1h) |> limit(n:5)' \
  --host http://localhost:8086 --token $READ_TOKEN
```

---

## Notes

- **Deletes are not replicated**: Edge Data Replication is optimized for one-way data flow and doesn't sync deletes. This is acceptable for time-series data where deletion is rare.
- **Separate tokens**: Write and read instances use different admin tokens for security.
