# Ingestion Service - Kubernetes Manifests

Deploys the Ingestion Service to Kubernetes.

## Components

| File | Description |
|------|-------------|
| `deployment.yaml` | Ingestion Service deployment |
| `service.yaml` | ClusterIP service |

## Deploy

```bash
kubectl apply -f service.yaml
kubectl apply -f deployment.yaml
```

**Note**: Update the image path in `deployment.yaml` after CI/CD is configured.

## Configuration

Environment variables (set in deployment.yaml):
- `NATS_URL` - NATS server address
- `LOG_LEVEL` - Logging level (INFO/DEBUG)

## Verify

```bash
kubectl get pods -l app=ingestion
kubectl logs -l app=ingestion
```

## Endpoints

| Path | Method | Description |
|------|--------|-------------|
| `/health` | GET | Liveness probe |
| `/ready` | GET | Readiness probe (checks NATS) |
| `/ingest` | POST | Accept meter readings |
