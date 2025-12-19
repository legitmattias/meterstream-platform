# Grafana - Kubernetes Manifests

Deploys **Grafana** to Kubernetes with **Dashboards-as-Code**.

Grafana is provisioned with:
- **InfluxDB (Flux) datasource** (auto-created on startup)
- **Dashboard providers** (tells Grafana where to load dashboards from)
- **Dashboards** (exported JSON dashboards mounted from ConfigMap)

> Grafana is deployed **stateless** (no PVC) because dashboards and datasource config are provisioned via ConfigMaps.

---

## Components

| File | Description |
|------|-------------|
| `service.yaml` | ClusterIP service exposing Grafana internally on port `3000` |
| `deployment.yaml` | Grafana Deployment + provisioning mounts + env vars |
| `configmap-datasource.yaml` | Provisions InfluxDB datasource (Flux + org/bucket + token) |
| `configmap-dashboard-provider.yaml` | Dashboard provider configuration (loads dashboards from filesystem path) |
| `configmap-dashboards.yaml` | Grafana dashboards as exported JSON (Dashboards-as-Code) |

---

## Deploy

Apply ConfigMaps first, then Deployment and Service:

```bash
kubectl -n meterstream apply -f configmap-datasource.yaml
kubectl -n meterstream apply -f configmap-dashboard-provider.yaml
kubectl -n meterstream apply -f configmap-dashboards.yaml
kubectl -n meterstream apply -f deployment.yaml
kubectl -n meterstream apply -f service.yaml
