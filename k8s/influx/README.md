# InfluxDB - Kubernetes Manifests

Deploys **InfluxDB 2.x** to Kubernetes as a **StatefulSet** with persistent storage.

InfluxDB is used as the time-series database for MeterStream:
- **Processor** writes meter readings to InfluxDB
- **Grafana** queries InfluxDB (Flux) to visualize data
- **Queries** service reads analytics data from InfluxDB

---

## Components

| File | Description |
|------|-------------|
| `influx.yaml` | InfluxDB StatefulSet (persistent volume + init env vars + probes) |

---

## Prerequisites

A Kubernetes Secret named **`influxdb-init`** must exist in namespace `meterstream` and contain:

- `DOCKER_INFLUXDB_INIT_MODE`
- `DOCKER_INFLUXDB_INIT_USERNAME`
- `DOCKER_INFLUXDB_INIT_PASSWORD`
- `DOCKER_INFLUXDB_INIT_ORG`
- `DOCKER_INFLUXDB_INIT_BUCKET`
- `DOCKER_INFLUXDB_INIT_ADMIN_TOKEN`
- `DOCKER_INFLUXDB_INIT_RETENTION`

> These env vars are used by InfluxDB on first startup to bootstrap the initial org, bucket, and admin token.

---

## Deploy

Apply the Service first, then the StatefulSet:

```bash
kubectl -n meterstream apply -f service.yaml
kubectl -n meterstream apply -f statefulset.yaml
