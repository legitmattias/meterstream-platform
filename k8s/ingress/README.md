# Ingress - Kubernetes Manifests

Deploys the **MeterStream Ingress** (Traefik) to expose the application via HTTP routing.

The Ingress routes:
- `/api` → **Gateway** service (API)
- `/` → **Portal** service (React frontend)

---

## Components

| File | Description |
|------|-------------|
| `ingress.yaml` | Traefik Ingress routing for Gateway + Portal |

---

## Prerequisites

- **Traefik** is installed in the cluster and configured as an Ingress controller.
- Services exist in namespace `meterstream`:
  - `gateway` on port `8000`
  - `portal` on port `80`

---

## Deploy

```bash
kubectl -n meterstream apply -f ingress.yaml
