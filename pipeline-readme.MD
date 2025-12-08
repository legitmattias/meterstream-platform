# CI/CD Pipeline - MeterStream

## Översikt

Pipelinen bygger container-images och deployar (automatiskt) till staging, med manuell godkännande för produktion.

```
Push till main → Build images → Deploy Staging (manuell for now) → Deploy Production (manuell)
```

---

## Pipeline-Steg

| Steg | Vad händer | Trigger |
|------|------------|---------|
| **Build** | Kaniko bygger Docker-images för alla services | Automatisk vid push till `main` |
| **Deploy Staging** | Uppdaterar staging-klustret med nya images | Manuell (klicka i GitLab UI) |
| **Deploy Production** | Uppdaterar produktions-klustret | Manuell (klicka i GitLab UI) |

---

## Mappstruktur exempel

```
meterstream/
├── .gitlab-ci.yml              # Pipeline-konfiguration
├── services/
│   ├── ingestion/
│   │   └── Dockerfile          # Byggs som: <registry>/ingestion:tag
│   ├── processor/
│   │   └── Dockerfile          # Byggs som: <registry>/processor:tag
│   └── auth/
│       └── Dockerfile          # Byggs som: <registry>/auth:tag
└── k8s/
    └── deployments/            # Kubernetes manifests
```

---

## Container Registry

**Registry URL:** `gitlab.lnu.se:5050`

**Image-sökväg:** `gitlab.lnu.se:5050/2dv013/student/team-2025-04-meterstream3/meterstream/<service-namn>`

---

### Image Tags

Varje build skapar två taggar:

| Tag | Exempel | Användning |
|-----|---------|------------|
| Commit SHA | `ingestion:a1b2c3d` | Unik per commit, används vid deploy |
| Latest | `ingestion:latest` | Senaste versionen |

### Visa images i Registry

GitLab → **Deploy** → **Container Registry**

---

## CI/CD Variabler

Konfigureras i: **Settings → CI/CD → Variables**

| Variabel | Beskrivning | Typ |
|----------|-------------|-----|
| `KUBE_CONFIG_STAGING_B64` | Kubeconfig för staging (base64) | Masked, Protected |
| `KUBE_CONFIG_PROD_B64` | Kubeconfig för produktion (base64) | Masked, Protected |

---


## development-strategi (Feature Branch)

Just nu kör vi all kod via en `development`-branch först för att verifiera 
att allt fungerar innan vi mergar till `main`.

### Så här gör du:

1. Ändra branch-villkor i `.gitlab-ci.yml` (main → development)
2. Ta bort Protected från CI/CD-variabler (behåll Masked!)
3. Pusha till development-branch
4. När allt fungerar: Ändra tillbaka till main


---

### Uppdatera kubeconfig

Om klustret återskapas behöver kubeconfig uppdateras:

```bash
# På servern
cat kubeconfig-external.yaml | base64 -w0

# Kopiera output → klistra in i GitLab CI/CD Variables
```

---

## Lägga till en ny Service

### 1. Skapa service-mapp

```
services/
└── <ny-service>/
    └── Dockerfile
```

### 2. Lägg till build-jobb i `.gitlab-ci.yml`

```yaml
build-<ny-service>:
  extends: .build
  variables:
    SERVICE_NAME: <ny-service>
```

### 3. Lägg till i deploy-stegen

```yaml
# I deploy-staging och deploy-production
- kubectl -n meterstream set image deploy/<ny-service> <ny-service>="${IMAGE_BASE}/<ny-service>:${TAG}"
- kubectl -n meterstream rollout status deploy/<ny-service> --timeout=120s
```

### 4. Uppdatera `needs` i deploy-staging

```yaml
deploy-staging:
  needs:
    - build-ingestion
    - build-processor
    - build-auth
    - build-<ny-service>  # Lägg till
```

---

## Image Pull Secret

Kubernetes behöver credentials för att hämta images från GitLab Registry.

### Steg 1: Skapa Deploy Token i GitLab

1. Gå till: **Settings → Repository → Deploy tokens**
2. Fyll i:
   - Name: `k8s-image-pull`
   - Scopes: ☑️ `read_registry`
3. Klicka "Create deploy token"
4. **Kopiera username och token direkt!** (visas bara en gång)

### Steg 2: Skapa secret i båda klustren

**Staging:**
```bash
export KUBECONFIG=~/.kube/meterstream-staging.yaml

kubectl create namespace meterstream

kubectl -n meterstream create secret docker-registry gitlab-registry \
  --docker-server=gitlab.lnu.se:5050 \
  --docker-username=<deploy-token-username> \
  --docker-password=<deploy-token> \
  --docker-email=meterstream@example.com
```

**Production:**
```bash
export KUBECONFIG=~/.kube/meterstream-prod.yaml

kubectl create namespace meterstream

kubectl -n meterstream create secret docker-registry gitlab-registry \
  --docker-server=gitlab.lnu.se:5050 \
  --docker-username=<deploy-token-username> \
  --docker-password=<deploy-token> \
  --docker-email=meterstream@example.com
```

### Steg 3: Verifiera

```bash
kubectl -n meterstream get secrets
# Ska visa: gitlab-registry
```

### Steg 4: Referera i deployment.yaml

```yaml
spec:
  template:
    spec:
      imagePullSecrets:
        - name: gitlab-registry
      containers:
        - name: ingestion
          image: gitlab.lnu.se:5050/2dv013/student/team-2025-04-meterstream3/meterstream/ingestion:latest
          imagePullPolicy: Always
```

---

## Felsökning

### Pipeline misslyckas på build

- Kontrollera att `Dockerfile` finns i rätt mapp
- Kontrollera att Dockerfile-syntax är korrekt

### Pipeline misslyckas på deploy

- Verifiera att kubeconfig är korrekt (testa med connection-test)
- Kontrollera att deployment finns i klustret
- Kontrollera att namespace `meterstream` existerar

### "connection refused" eller "timeout"

- Port 6443 måste vara öppen i OpenStack security groups
- Kontrollera att K3s körs: `sudo systemctl status k3s`

### "image pull error" / ErrImagePull

- Kontrollera att `gitlab-registry` secret finns: `kubectl -n meterstream get secrets`
- Kontrollera att image-sökvägen är korrekt (använd `gitlab.lnu.se:5050`)
- Kontrollera att `imagePullSecrets` finns i deployment
- Testa att logga in manuellt: `docker login gitlab.lnu.se:5050`

---

## Vanliga kommandon

```bash
# Visa pods
kubectl -n meterstream get pods

# Visa deployments
kubectl -n meterstream get deployments

# Visa loggar
kubectl -n meterstream logs deploy/ingestion

# Beskriv deployment (bra för felsökning)
kubectl -n meterstream describe deploy/ingestion

# Visa events (bra för image pull errors)
kubectl -n meterstream get events --sort-by='.lastTimestamp'
```
