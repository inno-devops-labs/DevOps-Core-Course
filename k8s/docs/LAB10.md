# Lab 10 — Helm Chart Documentation

## Chart Overview

### Structure

```
k8s/app-python/
├── Chart.yaml                        # Chart metadata
├── values.yaml                       # Default configuration values
├── values-dev.yaml                   # Development environment overrides
├── values-prod.yaml                  # Production environment overrides
└── templates/
    ├── _helpers.tpl                  # Reusable template helpers
    ├── deployment.yaml               # Deployment manifest template
    ├── service.yaml                  # Service manifest template
    ├── NOTES.txt                     # Post-install instructions
    └── hooks/
        ├── pre-install-job.yaml      # Pre-install validation hook
        └── post-install-job.yaml     # Post-install smoke test hook
```

### Key Template Files

| File | Purpose |
|------|---------|
| `Chart.yaml` | Chart metadata: name, version, description |
| `values.yaml` | Default values — image, replicas, resources, probes |
| `templates/_helpers.tpl` | Named templates for name, fullname, labels, selector labels |
| `templates/deployment.yaml` | Fully templated Deployment with health probes |
| `templates/service.yaml` | Service with configurable type and ports |
| `templates/hooks/pre-install-job.yaml` | Job that validates environment before install |
| `templates/hooks/post-install-job.yaml` | Job that runs smoke tests after install |

### Values Organization Strategy

Values are grouped by concern:
- **Image**: `image.repository`, `image.tag`, `image.pullPolicy`
- **Scaling**: `replicaCount`
- **Networking**: `service.type`, `service.port`, `service.targetPort`, `service.nodePort`
- **Resources**: `resources.requests`, `resources.limits`
- **Health**: `livenessProbe`, `readinessProbe`
- **App Config**: `env`
- **Security**: `securityContext`
- **Rollout**: `strategy`

---

## Configuration Guide

### Important Values

| Value | Default | Description |
|-------|---------|-------------|
| `replicaCount` | `3` | Number of pod replicas |
| `image.repository` | `4hellboy4/devops-info-service` | Docker image repository |
| `image.tag` | `latest` | Docker image tag |
| `image.pullPolicy` | `Never` | Image pull policy (use Never for local minikube image) |
| `service.type` | `NodePort` | Service type: NodePort, ClusterIP, LoadBalancer |
| `service.port` | `80` | External service port |
| `service.targetPort` | `8000` | Container port |
| `service.nodePort` | `30080` | NodePort (only for NodePort type) |
| `resources.requests.memory` | `128Mi` | Memory request |
| `resources.requests.cpu` | `100m` | CPU request |
| `resources.limits.memory` | `256Mi` | Memory limit |
| `resources.limits.cpu` | `200m` | CPU limit |
| `livenessProbe.initialDelaySeconds` | `10` | Liveness probe initial delay |
| `readinessProbe.initialDelaySeconds` | `5` | Readiness probe initial delay |

### Environment-Specific Configurations

#### Development (`values-dev.yaml`)
- 1 replica (minimal resource usage)
- Relaxed resources: 50m CPU / 64Mi memory requests
- `pullPolicy: Never` (uses locally loaded minikube image)
- Faster probe intervals for quick dev feedback
- NodePort 30080 for easy local access

#### Production (`values-prod.yaml`)
- 3 replicas for high availability
- Full resources: 100m CPU / 128Mi memory requests
- `pullPolicy: Never` (uses locally loaded minikube image)
- Strict probe delays (30s liveness initial delay) to give app time to start
- NodePort 30081 (separate port to allow co-existence with dev)

### Example Installations

```bash
# Default install
helm install app-python k8s/app-python

# Development environment
helm install app-python-dev k8s/app-python -f k8s/app-python/values-dev.yaml

# Production environment
helm install app-python-prod k8s/app-python -f k8s/app-python/values-prod.yaml

# Override a specific value
helm install app-python k8s/app-python --set replicaCount=5

# Upgrade with new values
helm upgrade app-python-dev k8s/app-python -f k8s/app-python/values-dev.yaml
```

---

## Hook Implementation

### Pre-install Hook (`templates/hooks/pre-install-job.yaml`)

**Purpose:** Validates the environment before the application is installed. Logs deployment configuration details (app name, image, replica count).

**Annotation:** `helm.sh/hook: pre-install`
**Weight:** `-5` (runs first among hooks with weight < 0)
**Delete Policy:** `hook-succeeded` — job is automatically deleted after successful execution

### Post-install Hook (`templates/hooks/post-install-job.yaml`)

**Purpose:** Runs a smoke test after all resources are installed and ready. Confirms the release name and namespace, waits briefly, then signals success.

**Annotation:** `helm.sh/hook: post-install`
**Weight:** `5` (runs after any weight-0 hooks)
**Delete Policy:** `hook-succeeded` — job is automatically deleted after successful execution

### Hook Execution Order

```
1. pre-install (weight -5)  → validates environment
2. Helm installs Deployment, Service
3. post-install (weight +5) → smoke test
```

### Why `hook-succeeded` Deletion Policy?

Keeps the cluster clean — successfully completed jobs are removed automatically. Failed jobs remain for debugging.

---

## Installation Evidence

### Helm Version

```
version.BuildInfo{Version:"v4.1.3", GitCommit:"c94d381b03be117e7e57908edbf642104e00eb8f", GitTreeState:"clean", GoVersion:"go1.26.1", KubeClientVersion:"v1.35"}
```

### Helm Repository Exploration (Task 1)

```
$ helm show chart prometheus-community/prometheus
annotations:
  artifacthub.io/license: Apache-2.0
apiVersion: v2
appVersion: v3.11.0
dependencies:
- condition: alertmanager.enabled
  name: alertmanager
  repository: https://prometheus-community.github.io/helm-charts
  version: 1.34.*
- condition: kube-state-metrics.enabled
  name: kube-state-metrics
  repository: https://prometheus-community.github.io/helm-charts
  version: 7.2.*
- condition: prometheus-node-exporter.enabled
  name: prometheus-node-exporter
  repository: https://prometheus-community.github.io/helm-charts
  version: 4.52.*
- condition: prometheus-pushgateway.enabled
  name: prometheus-pushgateway
  repository: https://prometheus-community.github.io/helm-charts
  version: 3.6.*
description: Prometheus is a monitoring system and time series database.
home: https://prometheus.io/
keywords:
- monitoring
- prometheus
kubeVersion: '>=1.19.0-0'
name: prometheus
type: application
version: 28.15.0
```

**Helm Value Proposition:** Helm acts as a package manager for Kubernetes — it templates manifests, manages releases with versioning and rollbacks, handles lifecycle hooks, and allows reuse across multiple environments via values files. Compared to raw manifests, Helm enables DRY configurations, consistent deployments, and one-command rollbacks.

### `helm lint` Output

```
$ helm lint k8s/app-python
==> Linting k8s/app-python
[INFO] Chart.yaml: icon is recommended

1 chart(s) linted, 0 chart(s) failed
```

### `helm template` Verification

```
$ helm template app-python k8s/app-python
---
# Source: app-python/templates/service.yaml
apiVersion: v1
kind: Service
metadata:
  name: app-python-app-python
  labels:
    helm.sh/chart: app-python-0.1.0
    app.kubernetes.io/name: app-python
    app.kubernetes.io/instance: app-python
    app.kubernetes.io/version: "latest"
    app.kubernetes.io/managed-by: Helm
spec:
  type: NodePort
  selector:
    app.kubernetes.io/name: app-python
    app.kubernetes.io/instance: app-python
  ports:
    - protocol: TCP
      port: 80
      targetPort: 8000
      nodePort: 30080
---
# Source: app-python/templates/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: app-python-app-python
  labels:
    helm.sh/chart: app-python-0.1.0
    app.kubernetes.io/name: app-python
    app.kubernetes.io/instance: app-python
    app.kubernetes.io/version: "latest"
    app.kubernetes.io/managed-by: Helm
spec:
  replicas: 3
  selector:
    matchLabels:
      app.kubernetes.io/name: app-python
      app.kubernetes.io/instance: app-python
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 1
      maxUnavailable: 0
  template:
    spec:
      containers:
        - name: app-python
          image: "4hellboy4/devops-info-service:latest"
          livenessProbe:
            httpGet:
              path: /health
              port: 8000
            initialDelaySeconds: 10
            periodSeconds: 10
          readinessProbe:
            httpGet:
              path: /health
              port: 8000
            initialDelaySeconds: 5
            periodSeconds: 5
---
# Source: app-python/templates/hooks/post-install-job.yaml
apiVersion: batch/v1
kind: Job
metadata:
  name: "app-python-app-python-post-install"
  annotations:
    "helm.sh/hook": post-install
    "helm.sh/hook-weight": "5"
    "helm.sh/hook-delete-policy": hook-succeeded
---
# Source: app-python/templates/hooks/pre-install-job.yaml
apiVersion: batch/v1
kind: Job
metadata:
  name: "app-python-app-python-pre-install"
  annotations:
    "helm.sh/hook": pre-install
    "helm.sh/hook-weight": "-5"
    "helm.sh/hook-delete-policy": hook-succeeded
```

### `helm install` — Dev Environment

```
$ helm install app-python-dev k8s/app-python -f k8s/app-python/values-dev.yaml

NAME: app-python-dev
LAST DEPLOYED: Thu Apr  2 22:36:43 2026
NAMESPACE: default
STATUS: deployed
REVISION: 1
DESCRIPTION: Install complete
TEST SUITE: None
NOTES:
1. Get the application URL by running these commands:
  export NODE_PORT=$(kubectl get --namespace default -o jsonpath="{.spec.ports[0].nodePort}" services app-python-dev-app-python)
  export NODE_IP=$(kubectl get nodes --namespace default -o jsonpath="{.items[0].status.addresses[0].address}")
  echo http://$NODE_IP:$NODE_PORT

2. Check health endpoint at /health

3. View all resources:
  kubectl get all -l "app.kubernetes.io/name: app-python
app.kubernetes.io/instance: app-python-dev"
```

### `helm install` — Prod Environment

```
$ helm install app-python-prod k8s/app-python -f k8s/app-python/values-prod.yaml

NAME: app-python-prod
LAST DEPLOYED: Thu Apr  2 22:50:14 2026
NAMESPACE: default
STATUS: deployed
REVISION: 1
DESCRIPTION: Install complete
TEST SUITE: None
NOTES:
1. Get the application URL by running these commands:
  export NODE_PORT=$(kubectl get --namespace default -o jsonpath="{.spec.ports[0].nodePort}" services app-python-prod-app-python)
  export NODE_IP=$(kubectl get nodes --namespace default -o jsonpath="{.items[0].status.addresses[0].address}")
  echo http://$NODE_IP:$NODE_PORT
```

### `helm upgrade` — Dev Environment

```
$ helm upgrade app-python-dev k8s/app-python -f k8s/app-python/values-dev.yaml

Release "app-python-dev" has been upgraded. Happy Helming!
NAME: app-python-dev
LAST DEPLOYED: Thu Apr  2 22:51:30 2026
NAMESPACE: default
STATUS: deployed
REVISION: 3
DESCRIPTION: Upgrade complete
TEST SUITE: None
```

### `helm list` Output

```
$ helm list
NAME             NAMESPACE  REVISION  UPDATED                                   STATUS    CHART             APP VERSION
app-python-dev   default    3         2026-04-02 22:51:30.602695 +0300 MSK      deployed  app-python-0.1.0  latest
app-python-prod  default    1         2026-04-02 22:50:14.354824 +0300 MSK      deployed  app-python-0.1.0  latest
```

### `kubectl get all` — Both Environments

```
$ kubectl get all
NAME                                              READY   STATUS    RESTARTS        AGE
pod/app-python-dev-app-python-7644b5c67f-nrrvf    1/1     Running   1 (6m25s ago)   11m
pod/app-python-prod-app-python-55887fff5c-dt629   1/1     Running   0               4m16s
pod/app-python-prod-app-python-55887fff5c-jnnws   1/1     Running   0               4m16s
pod/app-python-prod-app-python-55887fff5c-k92kh   1/1     Running   0               4m16s

NAME                                 TYPE        CLUSTER-IP      EXTERNAL-IP   PORT(S)        AGE
service/app-python-dev-app-python    NodePort    10.106.117.58   <none>        80:30080/TCP   17m
service/app-python-prod-app-python   NodePort    10.107.55.251   <none>        80:30081/TCP   4m16s
service/kubernetes                   ClusterIP   10.96.0.1       <none>        443/TCP        19m

NAME                                         READY   UP-TO-DATE   AVAILABLE   AGE
deployment.apps/app-python-dev-app-python    1/1     1            1           17m
deployment.apps/app-python-prod-app-python   3/3     3            3           4m16s

NAME                                                    DESIRED   CURRENT   READY   AGE
replicaset.apps/app-python-dev-app-python-7644b5c67f    1         1         1       11m
replicaset.apps/app-python-dev-app-python-8479985fdd    0         0         0       17m
replicaset.apps/app-python-prod-app-python-55887fff5c   3         3         3       4m16s
```

Dev uses 1 replica on NodePort 30080, prod uses 3 replicas on NodePort 30081 — environments are properly isolated.

### Hook Execution Output

```
$ kubectl get jobs
No resources found in default namespace.
```

Both pre-install and post-install hooks executed successfully and were automatically deleted per the `hook-succeeded` deletion policy, confirming lifecycle management works correctly.

---

## Operations

### Installation

```bash
# Install with default values
helm install app-python k8s/app-python

# Install with dev values
helm install app-python-dev k8s/app-python -f k8s/app-python/values-dev.yaml

# Install with prod values
helm install app-python-prod k8s/app-python -f k8s/app-python/values-prod.yaml
```

### Upgrade

```bash
# Upgrade dev release to new values
helm upgrade app-python-dev k8s/app-python -f k8s/app-python/values-dev.yaml

# Upgrade with inline override
helm upgrade app-python-dev k8s/app-python --set replicaCount=2
```

### Rollback

```bash
# List revision history
helm history app-python-dev

# Rollback to previous revision
helm rollback app-python-dev

# Rollback to specific revision
helm rollback app-python-dev 1
```

### Uninstall

```bash
helm uninstall app-python-dev
helm uninstall app-python-prod
```

---

## Testing & Validation

### Lint

```bash
helm lint k8s/app-python
```

### Template Rendering

```bash
helm template app-python k8s/app-python
```

### Dry-run

```bash
helm install --dry-run --debug test-release k8s/app-python
```

### Dev vs Prod Comparison

```bash
# Check rendered templates for dev vs prod
helm template dev-release k8s/app-python -f k8s/app-python/values-dev.yaml | grep -E "replicas|memory|cpu"
helm template prod-release k8s/app-python -f k8s/app-python/values-prod.yaml | grep -E "replicas|memory|cpu"
```

### Application Accessibility

On macOS with Docker driver, minikube creates a tunnel to expose NodePort services:

```bash
# Start tunnel (keep this terminal open)
minikube service app-python-dev-app-python --url
# http://127.0.0.1:57252
# ❗  Because you are using a Docker driver on darwin, the terminal needs to be open to run it.

# In another terminal
curl http://127.0.0.1:57252/health
# {"status":"healthy","timestamp":"2026-04-02T20:01:54.103787+00:00","uptime_seconds":723}
```

Application is healthy and responding correctly.
