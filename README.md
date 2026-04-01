# MeterStream

A cloud-native platform for ingesting, processing, and visualizing energy meter data in real time. Built as a team project in the Cloud Native course (2DV013) at Linnaeus University.

**[Project wiki](https://github.com/legitmattias/meterstream-wiki)** — sprint reports, architecture decisions, post-mortem, and testing documentation.
- [Post-mortem report](https://github.com/legitmattias/meterstream-wiki/blob/main/post-mortem.md)
- [Final report](https://github.com/legitmattias/meterstream-wiki/blob/main/report-2.md)

## What it does

MeterStream receives energy consumption readings through a REST API, routes them through a message queue for async processing, stores them in a time-series database, and serves them back through query endpoints and Grafana dashboards. The system handles multi-tenant data with JWT-based authentication.

```
Client → Gateway → Ingestion → NATS JetStream → Processor → InfluxDB → Grafana
                       ↕                                         ↕
                   Auth (MongoDB)                           Queries API
```

## Architecture

Six microservices, each with its own container and Kubernetes deployment:

| Service | Role |
|---|---|
| **gateway** | API routing, JWT validation, request forwarding (Python/FastAPI) |
| **auth** | User/tenant management, JWT issuance, MongoDB (Python/FastAPI) |
| **ingestion** | Accepts meter readings, publishes to NATS JetStream (Python/FastAPI) |
| **processor** | Consumes from NATS, writes time-series data to InfluxDB (Python/FastAPI) |
| **queries** | Reads from InfluxDB, serves historical and aggregated data (Python/FastAPI) |
| **portal** | React frontend with admin dashboard, internal staff views, and a customer-facing "Mina sidor" with energy consumption graphs (Recharts) |

Supporting infrastructure: **NATS JetStream** for event streaming, **InfluxDB** for time-series storage, **MongoDB** for auth state, **Grafana** for dashboards.

## Infrastructure

- **Kubernetes (K3s)** on OpenStack with separate staging and production clusters
- **KEDA** autoscaling on the processor service based on NATS queue depth
- **GitLab CI/CD** with Kaniko container builds, staged rollouts, and git-tag-based production releases
- **Ansible** for cluster provisioning
- **Docker Compose** for local development

## Running locally

```bash
cp .env.example .env
# Edit .env with your InfluxDB and MongoDB credentials
docker compose -f docker-compose.dev.yaml up -d
```

Individual services can also run outside Docker and connect to the containerized infrastructure.

## Team

Built by a four-person team. My primary responsibilities were project planning, the gateway, ingestion service, NATS integration, database replication, as well as setting up the development environment with custom scripting. I also did significant work on the portal, Kubernetes manifests, CI/CD pipeline, and was involved across all parts of the system.
