# CI/CD Pipeline - MeterStream

## Översikt

Pipelinen bygger container-images och deployar till staging och produktion.

```
Push → Build images → Deploy Staging (manuell) → Deploy Production (git tags)
```

---

## Pipeline Stages

| Stage | Vad händer | Trigger |
|-------|------------|---------|
| **test-connection** | Verifierar kubectl-anslutning till kluster | Manuell |
| **build** | Kaniko bygger Docker-images för alla services | Manuell (eller automatisk vid git tag) |
| **deploy-staging** | Deployar till staging-klustret | Manuell |
| **deploy-prod** | Deployar till produktion | Manuell (kräver git tag `v*.*.*`) |

---

## Services

Pipeline bygger och deployar följande services:

| Service | Beskrivning | Dependencies |
|---------|-------------|--------------|
| **mongodb** | Databas för auth-service | - |
| **nats** | Message queue för event streaming | - |
| **influxdb** | Tidsseriedatabas för mätdata | - |
| **auth** | JWT authentication service | MongoDB |
| **ingestion** | Tar emot mätdata via API | NATS |
| **processor** | Processar mätdata från NATS till InfluxDB | NATS, InfluxDB |
| **gateway** | API gateway och routing | Auth, Ingestion |
| **frontend** | Statisk webbapp (nginx) | - |
| **grafana** | Visualisering av mätdata | InfluxDB |

---

## Image Tags

Varje build skapar följande taggar:

| Tag | Exempel | Användning |
|-----|---------|------------|
| Commit SHA | `ingestion:a1b2c3d` | Specifik commit |
| Latest | `ingestion:latest` | Senaste versionen |
| Version (vid git tag) | `ingestion:v1.0.0` | Release-version |

**Registry URL:** `gitlab.lnu.se:5050/2dv013/student/team-2025-04-meterstream3/meterstream`

---

## CI/CD Variabler

Konfigureras i: **Settings → CI/CD → Variables**

### Kubernetes

| Variabel | Beskrivning | Typ |
|----------|-------------|-----|
| `KUBE_CONFIG_STAGING_B64` | Kubeconfig för staging (base64) | Masked, Protected |
| `KUBE_CONFIG_PROD_B64` | Kubeconfig för produktion (base64) | Masked, Protected |

### Docker Registry

| Variabel | Beskrivning |
|----------|-------------|
| `DOCKERHUB_USERNAME` | Docker Hub användarnamn (för base images) |
| `DOCKERHUB_TOKEN` | Docker Hub access token |

### MongoDB

| Variabel | Miljö | Beskrivning |
|----------|-------|-------------|
| `MONGODB_USERNAME` | Båda | MongoDB användarnamn |
| `MONGODB_PASSWORD_STAGING` | Staging | MongoDB lösenord |
| `MONGODB_PASSWORD_PROD` | Production | MongoDB lösenord |

### InfluxDB

| Variabel | Miljö | Beskrivning |
|----------|-------|-------------|
| `STAG_INFLUXDB_INIT_MODE` | Staging | Init mode (setup) |
| `STAG_INFLUXDB_INIT_USERNAME` | Staging | Admin username |
| `STAG_INFLUXDB_INIT_PASSWORD` | Staging | Admin password |
| `STAG_INFLUXDB_INIT_ORG` | Staging | Organization |
| `STAG_INFLUXDB_INIT_BUCKET` | Staging | Bucket name |
| `STAG_INFLUXDB_INIT_ADMIN_TOKEN` | Staging | Admin token |
| `STAG_INFLUXDB_INIT_RETENTION` | Staging | Data retention |
| `PROD_INFLUXDB_INIT_*` | Production | Samma som ovan för prod |

### Auth Service

| Variabel | Miljö | Beskrivning |
|----------|-------|-------------|
| `JWT_SECRET_STAGING` | Staging | JWT signing secret |
| `JWT_SECRET_PROD` | Production | JWT signing secret |
| `STAG_BOOTSTRAP_ADMIN_PASSWORD` | Staging | Initial admin password |
| `PROD_BOOTSTRAP_ADMIN_PASSWORD` | Production | Initial admin password |
| `TEST_USER_PASSWORD` | Production | Lösenord för test-användare i production (staging använder default: `testpassword123`) |

---

## Deploy-ordning

Services måste deployas i rätt ordning på grund av dependencies:

### Staging

1. **Infrastruktur** (körs först):
   ```
   deploy-mongodb-staging
   deploy-nats-staging
   deploy-influx-staging
   ```

2. **Services** (när infrastruktur är redo):
   ```
   deploy-auth-staging        (depends: mongodb)
   deploy-ingestion-staging   (depends: nats)
   deploy-processor-staging   (depends: nats, influxdb)
   deploy-grafana-staging     (depends: influxdb)
   ```

3. **Gateway & Frontend**:
   ```
   deploy-gateway-staging     (depends: auth, ingestion)
   deploy-frontend-staging
   deploy-ingress-staging
   ```

Pipeline verifierar automatiskt att dependencies är klara innan deploy.

### Production

Samma ordning som staging, men jobben triggas endast när du skapar en git tag (`v*.*.*`).

---

## Workflow

### 1. Normal deployment (staging)

```bash
# 1. Gör ändringar i koden
# 2. Push till Git
# 3. Gå till GitLab → CI/CD → Pipelines
# 4. Kör build-jobb manuellt (t.ex. build-ingestion)
# 5. Kör deploy-jobb manuellt (t.ex. deploy-ingestion-staging)
```

### 2. Production deployment (via git tag)

```bash
# 1. Testa att allt fungerar i staging
# 2. Skapa git tag:
git tag -a v1.0.0 -m "Release 1.0.0"
git push origin v1.0.0

# 3. Build-jobben körs automatiskt
# 4. Kör deploy-prod-jobben manuellt i GitLab
```

### 3. Testa anslutning

```bash
# Gå till GitLab → CI/CD → Pipelines
# Kör: test-staging-connection (manuell)
```

---

## Image Pull Secret

Kubernetes behöver credentials för att hämta images från GitLab Registry.

### Skapa Deploy Token

1. **Settings → Repository → Deploy tokens**
2. Name: `k8s-image-pull`
3. Scopes: ☑️ `read_registry`
4. **Kopiera username och token!**

### Skapa Secret i Klustret

**Staging:**
```bash
kubectl -n meterstream create secret docker-registry gitlab-registry \
  --docker-server=gitlab.lnu.se:5050 \
  --docker-username=<deploy-token-username> \
  --docker-password=<deploy-token> \
  --docker-email=meterstream@example.com
```

**Production:**
```bash
# Samma kommando med production kubeconfig
export KUBECONFIG=~/.kube/meterstream-prod.yaml
kubectl -n meterstream create secret docker-registry gitlab-registry \
  --docker-server=gitlab.lnu.se:5050 \
  --docker-username=<deploy-token-username> \
  --docker-password=<deploy-token> \
  --docker-email=meterstream@example.com
```

---

## Felsökning

### Build misslyckas

- Kontrollera att `Dockerfile` finns i `services/<service-name>/`
- Kontrollera Dockerfile-syntax
- Kolla build-loggar i GitLab

### Deploy misslyckas

**"connection refused":**
- Verifiera kubeconfig med `test-staging-connection`
- Kontrollera att K3s körs: `sudo systemctl status k3s`
- Port 6443 måste vara öppen i OpenStack security groups

**"Required service X is not deployed":**
- Deploya dependencies först (se Deploy-ordning ovan)
- Pipeline visar vilken service som saknas

**"image pull error" / ErrImagePull:**
- Verifiera att `gitlab-registry` secret finns: `kubectl -n meterstream get secrets`
- Kontrollera image-sökväg i deployment
- Testa manuellt: `docker login gitlab.lnu.se:5050`

**HPA fungerar inte:**
- Kontrollera att KEDA är installerat: `kubectl get pods -n keda`
- Se [k8s/processor/README.md](k8s/processor/README.md)

---

## Vanliga Kommandon

```bash
# Visa pods
kubectl -n meterstream get pods

# Visa deployments
kubectl -n meterstream get deployments

# Visa services
kubectl -n meterstream get svc

# Visa loggar
kubectl -n meterstream logs deploy/ingestion -f

# Beskriv pod (bra för felsökning)
kubectl -n meterstream describe pod <pod-name>

# Visa events (bra för image pull errors)
kubectl -n meterstream get events --sort-by='.lastTimestamp'

# Visa HPA status
kubectl -n meterstream get hpa
kubectl -n meterstream get scaledobject

# Watch pods (se autoscaling i realtid)
watch kubectl -n meterstream get pods
```

---

## Uppdatera Kubeconfig

Om klustret återskapas:

```bash
# På servern
cat kubeconfig-external.yaml | base64 -w0

# Kopiera output → GitLab → Settings → CI/CD → Variables
# Uppdatera KUBE_CONFIG_STAGING_B64 eller KUBE_CONFIG_PROD_B64
```

---

## Kubectl Apply: Ordning av Kommandon

### Spelar ordningen roll?

När du deployar med kubectl spelar **ordningen av vissa kommandon roll**, men inte alla:

#### ✅ Ordning spelar INTE roll för:

```yaml
# Dessa kan köras i valfri ordning
- kubectl apply -f k8s/auth/          # Applicera manifests
- kubectl set env deploy/auth VAR=val # Sätt env vars
- kubectl set env deploy/auth VAR2=val2
```

**Varför?** Kubernetes batchar ändringar. När du gör flera `kubectl set env`, startar pods om bara EN gång med alla ändringar.

#### ⚠️ Ordning spelar roll för:

```yaml
# RÄTT ordning:
- kubectl apply -f k8s/auth/          # 1. Skapa deployment
- kubectl set env deploy/auth VAR=val # 2. Sätt env vars
- kubectl set image deploy/auth ...   # 3. Byt image (triggar rollout)
- kubectl rollout status deploy/auth  # 4. Vänta på completion
```

**Varför?**
- `kubectl set image` triggar en ny rollout
- Du vill att alla env vars ska vara satta INNAN rollout startar
- `kubectl rollout status` måste komma sist för att vänta på deploy

#### 📦 Applicera hela mappar istället för enskilda filer:

```yaml
# ❌ Långsamt och repetitivt
- kubectl apply -f k8s/auth/configmap.yaml
- kubectl apply -f k8s/auth/service.yaml
- kubectl apply -f k8s/auth/deployment.yaml

# ✅ Bättre: applicera hela mappen
- kubectl apply -f k8s/auth/
```

Kubectl applicerar automatiskt alla `.yaml` filer i mappen.

---

## Lägga till ett nytt Deploy-steg

Exempel: Lägg till en ny service `analytics` som beror på InfluxDB.

### 1. Skapa Build-jobb

```yaml
build-analytics:
  extends: .build
  needs:
    - job: test-analytics
      optional: true
  variables:
    SERVICE_NAME: analytics
```

### 2. Skapa Deploy-jobb för Staging

```yaml
deploy-analytics-staging:
  extends: .deploy-base
  needs:
    - job: build-analytics
      optional: true
  script:
    # Verifiera att dependencies finns
    - require_statefulset influxdb

    # Applicera Kubernetes manifests
    - kubectl apply -f k8s/analytics/ -n meterstream

    # Sätt miljövariabler (om behövs)
    - kubectl -n meterstream set env deploy/analytics ENVIRONMENT=staging

    # Uppdatera till nybyggd image
    - kubectl -n meterstream set image deploy/analytics analytics="${IMAGE_BASE}/analytics:${TAG}"

    # Vänta på deploy
    - kubectl -n meterstream rollout status deploy/analytics --timeout=120s
  rules:
    - when: manual
```

### 3. Skapa Deploy-jobb för Production

```yaml
deploy-analytics-prod:
  extends: .deploy-base-prod
  needs:
    - job: build-analytics
      optional: true
  script:
    # Samma som staging men med prod-specifika secrets/configs
    - require_statefulset influxdb

    - kubectl apply -f k8s/analytics/ -n meterstream

    # Production env vars
    - kubectl -n meterstream set env deploy/analytics ENVIRONMENT=production
    - kubectl -n meterstream set env deploy/analytics API_KEY="$PROD_ANALYTICS_API_KEY"

    # Använd version tag om det finns, annars commit SHA
    - |
      if [[ "$CI_COMMIT_TAG" =~ ^v[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
        IMAGE_TAG="${CI_COMMIT_TAG}"
      else
        IMAGE_TAG="${TAG}"
      fi
      kubectl -n meterstream set image deploy/analytics analytics="${IMAGE_BASE}/analytics:${IMAGE_TAG}"

    - kubectl -n meterstream rollout status deploy/analytics --timeout=120s
  rules:
    - if: '$CI_COMMIT_TAG =~ /^v\d+\.\d+\.\d+$/'
      when: manual
```

### 4. Lägg till CI/CD variabler

Gå till **Settings → CI/CD → Variables** och lägg till:
- `PROD_ANALYTICS_API_KEY` (Masked, Protected)

### 5. Skapa Kubernetes manifests

Skapa `k8s/analytics/` med:
- `deployment.yaml`
- `service.yaml`
- `configmap.yaml` (om behövs)

### 6. Uppdatera Dependencies

Om andra services beror på analytics, lägg till dependency check:

```yaml
deploy-frontend-staging:
  script:
    - require_running analytics  # Lägg till detta
    - kubectl apply -f k8s/frontend/
    # ...
```

### Checklista för nya services:

- [ ] Skapa `services/<service-name>/Dockerfile`
- [ ] Skapa `k8s/<service-name>/` med manifests
- [ ] Lägg till `build-<service-name>` i `.gitlab-ci.yml`
- [ ] Lägg till `deploy-<service-name>-staging`
- [ ] Lägg till `deploy-<service-name>-prod`
- [ ] Lägg till CI/CD variabler i GitLab
- [ ] Uppdatera dependency checks i andra jobb
- [ ] Uppdatera denna README med nya variabler/services
