# Kubernetes deployment guide

Step-by-step setup for deploying this repository on Kubernetes using the manifests under [`k8s/`](../k8s/) (full stack) or [`k8s-mock/`](../k8s-mock/) (mock UI + in-cluster auth Postgres). For architecture, routes, and environment variable semantics, see [TOPOLOGY_AND_SETUP.md](TOPOLOGY_AND_SETUP.md).

---

## 1. Prerequisites

| Requirement | Notes |
|-------------|--------|
| Kubernetes cluster | 1.24+ recommended (`kubectl` works against your cluster). |
| `kubectl` | Configured with a context that can create Deployments, Services, ConfigMaps, Secrets, Ingress. |
| [NGINX Ingress Controller](https://kubernetes.github.io/ingress-nginx/deploy/) | Example manifests use `ingressClassName: nginx`. Install in your cluster or change the class to match your controller. |
| Container images | Build and push to a registry your nodes can pull, **or** load images locally (kind, minikube, k3s). |
| PostgreSQL | **Path B:** metrics DB external to the cluster (`DB_*`). **Path A:** auth Postgres is defined under [`k8s-mock/`](../k8s-mock/) (StatefulSet); no separate metrics DB. |
| Metrics Server (optional) | Required if you apply **HorizontalPodAutoscaler** manifests under `k8s/*/hpa.yaml`. |

This repo ships plain YAML (no Helm/Kustomize). You can wrap these files in your own tooling later.

For **authentication** (auth DB Secret, rolling upgrades, Globe View egress), see [K8S_DEPLOYMENT_AND_UPDATE.md](K8S_DEPLOYMENT_AND_UPDATE.md).

---

## 2. Choose a deployment path

| Path | Directory | Use case |
|------|-----------|----------|
| **A — Mock + auth DB** | [`k8s-mock/`](../k8s-mock/) | Demo UI with static data (`APP_MODE=mock`) plus in-cluster **PostgreSQL** for RBAC / Settings (same model as [`docker-compose.mock.yml`](../docker-compose.mock.yml)). No metrics APIs or Redis. |
| **B — Full stack** | [`k8s/`](../k8s/) | Dash frontend + three FastAPI services + Redis + Ingress. PostgreSQL is external. |
| **C — Monitoring (optional)** | [`k8s/monitoring/`](../k8s/monitoring/) | Namespace `datalake-monitoring`, Prometheus config, Fluent Bit. Separate from app namespaces. |

---

## 3. Path A — Mock stack with auth PostgreSQL (`k8s-mock/`)

Components:

| Manifest | Purpose |
|----------|---------|
| [`00-auth-secrets-reference.yaml`](../k8s-mock/00-auth-secrets-reference.yaml) | Secret template: `POSTGRES_PASSWORD` (same value as app `AUTH_DB_PASS`), `SECRET_KEY`, `ADMIN_DEFAULT_PASSWORD`, optional `FERNET_KEY` / `API_JWT_SECRET`. **Replace placeholders** or use `kubectl create secret` (see file header). |
| [`auth-configmap.yaml`](../k8s-mock/auth-configmap.yaml) | `AUTH_DB_*`, `POSTGRES_*`, `AUTH_DISABLED`. |
| [`auth-db-service.yaml`](../k8s-mock/auth-db-service.yaml) | ClusterIP service `datalake-webui-mock-auth-db:5432`. |
| [`auth-db-statefulset.yaml`](../k8s-mock/auth-db-statefulset.yaml) | `postgres:15` with 5Gi PVC (edit `storage` / `storageClassName` if your cluster requires it). |
| [`configmap.yaml`](../k8s-mock/configmap.yaml) | UI branding (`APP_BRAND_TITLE`, `APP_BUILD_ID`). |
| [`deployment.yaml`](../k8s-mock/deployment.yaml) | Dash pod: `APP_MODE=mock`, initContainer waits for Postgres, loads secrets for auth bootstrap / seed. |
| [`service.yaml`](../k8s-mock/service.yaml), [`ingress.yaml`](../k8s-mock/ingress.yaml) | Expose the UI. |

Default login after first seed: **`admin`** / value of **`ADMIN_DEFAULT_PASSWORD`** in the Secret (same default as Compose: `Admin123!` in the reference file — change in production).

### 3.1 Build the image

From the repository root (same context as root [`Dockerfile`](../Dockerfile)):

```bash
docker build -t datalake-webui-mock:latest --build-arg APP_BUILD_ID=k8s .
```

### 3.2 Load the image (local clusters)

- **kind:** `kind load docker-image datalake-webui-mock:latest`
- **minikube:** `minikube image load datalake-webui-mock:latest`
- **Remote cluster:** tag and push to your registry, then set `image:` and `imagePullPolicy: Always` in [`k8s-mock/deployment.yaml`](../k8s-mock/deployment.yaml).

### 3.3 Customize branding (optional)

Edit [`k8s-mock/configmap.yaml`](../k8s-mock/configmap.yaml):

- `APP_BRAND_TITLE` — sidebar / tab title
- `APP_BUILD_ID` — build label shown in the UI

### 3.4 Apply manifests

The `00-` prefix ensures a directory-wide apply creates the Secret before the StatefulSet. Prefer:

```bash
kubectl apply -f k8s-mock/
```

Or explicitly:

```bash
kubectl apply -f k8s-mock/00-auth-secrets-reference.yaml   # edit values first, or use your own Secret name/keys
kubectl apply -f k8s-mock/auth-configmap.yaml
kubectl apply -f k8s-mock/auth-db-service.yaml
kubectl apply -f k8s-mock/auth-db-statefulset.yaml
kubectl wait --for=condition=ready pod -l app=datalake-webui-mock-auth-db --timeout=120s
kubectl apply -f k8s-mock/configmap.yaml
kubectl apply -f k8s-mock/deployment.yaml
kubectl apply -f k8s-mock/service.yaml
kubectl apply -f k8s-mock/ingress.yaml
```

Wait until the auth-db pod is **Ready** before the webui pod passes its initContainer and starts.

### 3.5 DNS and access

[`k8s-mock/ingress.yaml`](../k8s-mock/ingress.yaml) uses host **`datalake-demo.local`**.

1. Get the ingress controller external IP or hostname: `kubectl get svc -n <ingress-namespace>`.
2. Add a hosts entry (or DNS record) pointing `datalake-demo.local` to that address.
3. Open `http://datalake-demo.local/` in a browser.

---

## 4. Path B — Full stack (`k8s/`)

### 4.1 Architecture (short)

The browser hits **Ingress**, which routes by path to the Dash app or each API. The **frontend** pod calls the three APIs over the cluster network (HTTP), not through Ingress unless you configure it that way. See the diagram in [TOPOLOGY_AND_SETUP.md](TOPOLOGY_AND_SETUP.md).

### 4.2 Build and tag images

Build from the repository root with the **tags expected by the YAML** (or change YAML `image:` fields to your registry).

| Component | Build context | Example tag in manifests |
|-----------|---------------|---------------------------|
| Dash (frontend) | `.` (root) | `datalake-frontend:latest` |
| datacenter-api | `services/datacenter-api` | `datalake-datacenter-api:latest` |
| customer-api | `services/customer-api` | `datalake-customer-api:latest` |
| query-api | `services/query-api` | `datalake-query-api:latest` |

Example commands:

```bash
docker build -t datalake-frontend:latest --build-arg APP_BUILD_ID=k8s .
docker build -t datalake-datacenter-api:latest services/datacenter-api
docker build -t datalake-customer-api:latest services/customer-api
docker build -t datalake-query-api:latest services/query-api
```

Load or push images the same way as in §3.2. **Redis** uses the public image `redis:7-alpine` from the manifest; no local build required.

### 4.3 Create database Secrets (required)

The repository does **not** commit Secret YAML for database passwords. Each API Deployment expects a Secret named:

| Deployment | Secret name | Key |
|------------|-------------|-----|
| customer-api | `datalake-customer-api-secret` | `DB_PASS` |
| datacenter-api | `datalake-datacenter-api-secret` | `DB_PASS` |
| query-api | `datalake-query-api-secret` | `DB_PASS` |

Example (replace `YOUR_PASSWORD` and optionally set namespace `-n your-namespace`):

```bash
kubectl create secret generic datalake-customer-api-secret \
  --from-literal=DB_PASS='YOUR_PASSWORD'
kubectl create secret generic datalake-datacenter-api-secret \
  --from-literal=DB_PASS='YOUR_PASSWORD'
kubectl create secret generic datalake-query-api-secret \
  --from-literal=DB_PASS='YOUR_PASSWORD'
```

For GitOps, prefer [Sealed Secrets](https://github.com/bitnami-labs/sealed-secrets), [External Secrets](https://external-secrets.io/), or your cloud secret manager instead of committing cleartext.

### 4.4 Edit API ConfigMaps

Before applying, update database connectivity in:

- [`k8s/customer-api/configmap.yaml`](../k8s/customer-api/configmap.yaml)
- [`k8s/datacenter-api/configmap.yaml`](../k8s/datacenter-api/configmap.yaml)
- [`k8s/query-api/configmap.yaml`](../k8s/query-api/configmap.yaml)

Set at least:

- `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER` — must match your PostgreSQL and per-service DB users (see [env.example](../env.example) and [TOPOLOGY_AND_SETUP.md](TOPOLOGY_AND_SETUP.md)).

For **customer-api** and **datacenter-api**, keep Redis pointing at the in-cluster service:

- `REDIS_HOST`: `datalake-redis`
- `REDIS_PORT`: `6379`

These names must match [`k8s/redis/service.yaml`](../k8s/redis/service.yaml).

### 4.5 Frontend → API URLs (ConfigMap)

The Dash app reads URLs from [`src/services/api_client.py`](../src/services/api_client.py): `DATACENTER_API_URL`, `CUSTOMER_API_URL`, `QUERY_API_URL`, or a shared `API_BASE_URL`.

**Recommended** for pods calling ClusterIP Services on port **80** (targets container port 8000):

```yaml
# In k8s/frontend/configmap.yaml (datalake-frontend-config)
DATACENTER_API_URL: "http://datalake-datacenter-api"
CUSTOMER_API_URL: "http://datalake-customer-api"
QUERY_API_URL: "http://datalake-query-api"
```

You can omit `API_BASE_URL` when all three are set. If you use a single reverse proxy inside the cluster, set only `API_BASE_URL` to that gateway’s URL.

**Note:** The checked-in example `API_BASE_URL: "http://datalake-data-api"` does not match a Service name in this repo; adjust it as above or your UI will fail to reach the APIs.

After editing the ConfigMap, restart the frontend Deployment if pods were already running:

```bash
kubectl rollout restart deployment/datalake-frontend
```

### 4.6 Apply order (recommended)

Apply resources so dependencies exist before workloads that need them.

1. **Redis**

   ```bash
   kubectl apply -f k8s/redis/deployment.yaml
   kubectl apply -f k8s/redis/service.yaml
   ```

2. **Secrets** (§4.3) — if not already created.

3. **API ConfigMaps** — after editing (§4.4).

   ```bash
   kubectl apply -f k8s/customer-api/configmap.yaml
   kubectl apply -f k8s/datacenter-api/configmap.yaml
   kubectl apply -f k8s/query-api/configmap.yaml
   ```

4. **API Deployments and Services**

   ```bash
   kubectl apply -f k8s/customer-api/deployment.yaml
   kubectl apply -f k8s/customer-api/service.yaml
   kubectl apply -f k8s/datacenter-api/deployment.yaml
   kubectl apply -f k8s/datacenter-api/service.yaml
   kubectl apply -f k8s/query-api/deployment.yaml
   kubectl apply -f k8s/query-api/service.yaml
   ```

5. **Frontend ConfigMap** (§4.5), then Deployment and Service

   ```bash
   kubectl apply -f k8s/frontend/configmap.yaml
   kubectl apply -f k8s/frontend/deployment.yaml
   kubectl apply -f k8s/frontend/service.yaml
   ```

6. **Ingress**

   ```bash
   kubectl apply -f k8s/ingress.yaml
   ```

7. **HorizontalPodAutoscaler (optional)** — requires Metrics Server.

   ```bash
   kubectl apply -f k8s/customer-api/hpa.yaml
   kubectl apply -f k8s/datacenter-api/hpa.yaml
   kubectl apply -f k8s/query-api/hpa.yaml
   kubectl apply -f k8s/frontend/hpa.yaml
   ```

All of the above use the **default** namespace unless you add `metadata.namespace` to each file or use `kubectl apply -n ...` with adjusted resources.

### 4.7 Ingress routing

[`k8s/ingress.yaml`](../k8s/ingress.yaml) uses host **`datalake.local`** and `ingressClassName: nginx`. Path routing matches [TOPOLOGY_AND_SETUP.md §6](TOPOLOGY_AND_SETUP.md):

| Path prefix | Backend Service |
|-------------|-----------------|
| `/api/v1/sla`, `/api/v1/physical-inventory`, `/api/v1/datacenters`, `/api/v1/dashboard`, `/health` | `datalake-datacenter-api` |
| `/api/v1/customers` | `datalake-customer-api` |
| `/api/v1/queries` | `datalake-query-api` |
| `/` | `datalake-frontend` |

Configure DNS or `/etc/hosts` for `datalake.local` to the ingress entrypoint, same idea as §3.5.

### 4.8 TLS (optional)

The example Ingress manifest does not define TLS. For HTTPS, add a `tls` section and a certificate (e.g. [cert-manager](https://cert-manager.io/) with Let’s Encrypt or your own `Secret` of type `kubernetes.io/tls`).

---

## 5. Path C — Monitoring (`k8s/monitoring/`)

Optional components in namespace **`datalake-monitoring`**:

1. [`k8s/monitoring/namespace.yaml`](../k8s/monitoring/namespace.yaml)
2. [`k8s/monitoring/prometheus-config.yaml`](../k8s/monitoring/prometheus-config.yaml)
3. [`k8s/monitoring/fluent-bit-configmap.yaml`](../k8s/monitoring/fluent-bit-configmap.yaml)
4. [`k8s/monitoring/fluent-bit-daemonset.yaml`](../k8s/monitoring/fluent-bit-daemonset.yaml)

Review and adjust scrape targets and log shipping for your environment before applying. Order: namespace first, then ConfigMaps, then workloads that reference them.

---

## 6. Verification

```bash
kubectl get pods,svc,ingress
kubectl get pods -w   # wait until Running / Ready
```

- **API health:** from inside the cluster or via Ingress, e.g. `GET /health` on datacenter-api (see [TOPOLOGY_AND_SETUP.md](TOPOLOGY_AND_SETUP.md)).
- **Frontend:** open the Ingress host in a browser; Dash listens on container port **8050**, Services map **80 → 8050**.

Check logs on failure:

```bash
kubectl logs deployment/datalake-frontend
kubectl logs deployment/datalake-datacenter-api
```

---

## 7. Troubleshooting

| Symptom | Likely cause |
|---------|----------------|
| `ImagePullBackOff` | Image not in registry / wrong name / `imagePullPolicy` vs local-only images. |
| API pods `CrashLoopBackOff` | Wrong `DB_HOST` / firewall, missing or wrong Secret `DB_PASS`, invalid `DB_USER`. |
| Frontend errors loading data | Frontend ConfigMap URLs wrong (§4.5); APIs not ready; network policies blocking pod-to-pod traffic. |
| Ingress `502` / `504` | Backend Service has no ready endpoints; probes failing; timeout — compare Ingress annotations with [`k8s/ingress.yaml`](../k8s/ingress.yaml). |
| HPA not scaling | Metrics Server not installed or misconfigured. |
| Mock webui `Init:CrashLoop` / stuck init | Auth Postgres not ready; wrong `POSTGRES_PASSWORD` vs Secret; initContainer cannot resolve `datalake-webui-mock-auth-db`. |
| Mock auth-db `Pending` | No default `StorageClass` or insufficient PV — set `spec.volumeClaimTemplates[].spec.storageClassName` in [`auth-db-statefulset.yaml`](../k8s-mock/auth-db-statefulset.yaml). |
| Login fails after deploy | Secret `ADMIN_DEFAULT_PASSWORD` must match seed; delete PVC and re-apply StatefulSet if you changed password after first init (or run SQL to reset admin). |

---

## 8. Production hardening (reading list)

The sample manifests are a starting point. Before production, consider: Pod Security Standards, NetworkPolicies, resource quotas, backup of secrets, separate namespaces per environment, pod disruption budgets, and scanning images for vulnerabilities.

---

## 9. Related documentation

| Document | Content |
|----------|---------|
| [K8S_DEPLOYMENT_AND_UPDATE.md](K8S_DEPLOYMENT_AND_UPDATE.md) | Auth Secrets, frontend ConfigMap/Secret wiring, rolling updates, Globe View egress |
| [AUTH_SYSTEM.md](AUTH_SYSTEM.md) | Auth stack summary and link to full upstream doc |
| [TOPOLOGY_AND_SETUP.md](TOPOLOGY_AND_SETUP.md) | Architecture, env vars, local and Compose setup |
| [DOCKER_SETUP.md](DOCKER_SETUP.md) | Docker and Docker Compose |
| [env.example](../env.example) | Environment variable reference |
