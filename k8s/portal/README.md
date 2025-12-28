# Portal Kubernetes Manifests

Deploys the MeterStream frontend portal (React + Nginx).

## Files

- `deployment.yaml`: Portal deployment (2 replicas, Nginx serving React)
- `service.yaml`: ClusterIP service on port 80

## Environment Variables

Set via deployment env or ConfigMap:
- `VITE_API_BASE_URL`: Gateway/API base URL
- `VITE_GRAFANA_URL`: Grafana base URL
- `VITE_GRAFANA_DASHBOARD_UID`: (Optional) Direct dashboard embed

## Deploy

```bash
kubectl apply -f k8s/portal/ -n meterstream
kubectl rollout status deploy/portal -n meterstream
```

## Access

Via Traefik Ingress:
- Create IngressRoute pointing `portal.yourdomain` to `portal.meterstream.svc.cluster.local:80`

Or port-forward for testing:
```bash
kubectl port-forward -n meterstream svc/portal 8080:80
# Open http://localhost:8080
```
