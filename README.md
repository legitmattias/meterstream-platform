# MeterStream

A cloud-native platform for ingesting, processing, and visualizing energy meter data in real time. Built as a team project in the Cloud Native course (2DV013) at Linnaeus University.

**[Project wiki](https://github.com/legitmattias/meterstream-wiki)** — sprint reports, architecture decisions, post-mortem, and testing documentation.

## What it does

MeterStream receives energy consumption readings through a REST API, routes them through a message queue for async processing, stores them in a time-series database, and serves them back through query endpoints and Grafana dashboards. The system handles multi-tenant data with JWT-based authentication.

```
Client → Gateway → Ingestion → NATS JetStream → Processor → InfluxDB → Grafana
                       ↕                                         ↕
                   Auth (MongoDB)                           Queries API
```

## Architecture

Six Python (FastAPI) microservices, each with its own container and Kubernetes deployment:

| Service | Role |
|---|---|
| **gateway** | API routing, JWT validation, request forwarding |
| **auth** | User/tenant management, JWT issuance (MongoDB) |
| **ingestion** | Accepts meter readings, publishes to NATS JetStream |
| **processor** | Consumes from NATS, writes time-series data to InfluxDB |
| **queries** | Reads from InfluxDB, serves historical and aggregated data |
| **portal** | Web frontend served via nginx |

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

Built by a four-person team over one semester. My primary responsibilities were project planning, the gateway, ingestion service, NATS integration, and setting up the development environment and custom scripting. I also did significant work on the portal, Kubernetes manifests, and CI/CD pipeline, and was involved across all parts of the system.
