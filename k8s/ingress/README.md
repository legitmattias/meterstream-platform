# MongoDB - Kubernetes Manifests

Deploys **MongoDB** to Kubernetes as a **StatefulSet** with persistent storage.

MongoDB is used by the **Auth service** for user data (accounts, credentials, etc.).

---

## Components

| File | Description |
|------|-------------|
| `service.yaml` | Headless Service (`clusterIP: None`) for stable StatefulSet networking |
| `statefulset.yaml` | MongoDB StatefulSet (PVC + probes + root credentials from Secret) |

---

## Prerequisites

A Kubernetes Secret named **`mongodb-secret`** must exist in namespace `meterstream` and contain:

- `username`
- `password`

> These values are used as `MONGO_INITDB_ROOT_USERNAME` and `MONGO_INITDB_ROOT_PASSWORD`.

---

## Deploy

Apply the Service first, then the StatefulSet:

```bash
kubectl -n meterstream apply -f service.yaml
kubectl -n meterstream apply -f statefulset.yaml
