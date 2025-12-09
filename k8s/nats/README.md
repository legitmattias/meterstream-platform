# NATS JetStream - Kubernetes Manifests

Message queue for the data pipeline.

## Components

| File | Description |
|------|-------------|
| `statefulset.yaml` | NATS server with persistent storage |
| `service.yaml` | ClusterIP service for internal access |
| `configmap.yaml` | JetStream configuration |

## Deploy

```bash
kubectl apply -f configmap.yaml
kubectl apply -f service.yaml
kubectl apply -f statefulset.yaml
```

## Connection

From within the cluster:
```
nats://nats:4222
```

## Stream Configuration

- **Stream**: `METER_DATA`
- **Subject**: `meter.readings`
- **Storage**: 2Gi persistent volume

## Verify

```bash
kubectl get pods -l app=nats
kubectl logs -l app=nats
```

Port-forward for monitoring:
```bash
kubectl port-forward svc/nats 8222:8222
curl http://localhost:8222/jsz
```
