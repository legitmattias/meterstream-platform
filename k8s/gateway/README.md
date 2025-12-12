# API Gateway - Kubernetes Manifests

Deploys the API Gateway to Kubernetes.

## Components

| File | Description |
|------|-------------|
| `deployment.yaml` | Gateway deployment |
| `service.yaml` | ClusterIP service |

## Prerequisites

Create the JWT secret before deploying (see `k8s/secrets/README.md`).

## Deploy

```bash
kubectl apply -f service.yaml
kubectl apply -f deployment.yaml
```

## Configuration

Environment variables (set in deployment.yaml):
- `JWT_SECRET` - From K8s secret `jwt-secret`
- `AUTH_SERVICE_URL` - Auth service address
- `INGESTION_SERVICE_URL` - Ingestion service address
- `LOG_LEVEL` - Logging level (INFO/DEBUG)

## Verify

```bash
kubectl get pods -l app=gateway
kubectl logs -l app=gateway
```

## Endpoints

| Path | Method | Auth | Description |
|------|--------|------|-------------|
| `/health` | GET | No | Liveness/readiness probe |
| `/api/auth/*` | * | No | Proxy to Auth Service |
| `/api/ingest` | POST | JWT | Proxy to Ingestion Service |
