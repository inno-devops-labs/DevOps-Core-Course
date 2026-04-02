# Lab 10 — Helm Package Manager

## Task 1 — Helm Fundamentals

### Installation

Downloaded Helm 4.1.3 and placed it in `~/bin/helm`:

```
$ helm version
version.BuildInfo{Version:"v4.1.3", GitCommit:"c94d381b03be117e7e57908edbf642104e00eb8f", GitTreeState:"clean", GoVersion:"go1.25.8", KubeClientVersion:"v1.35"}
```

### Exploring a public chart

```
$ helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
$ helm repo update
$ helm show chart prometheus-community/prometheus

annotations:
  artifacthub.io/license: Apache-2.0
apiVersion: v2
appVersion: v3.11.0
dependencies:
- condition: alertmanager.enabled
  name: alertmanager
  version: 1.34.*
- condition: kube-state-metrics.enabled
  name: kube-state-metrics
  version: 7.2.*
- condition: prometheus-node-exporter.enabled
  name: prometheus-node-exporter
  version: 4.44.*
description: Prometheus is a monitoring system and time series database.
name: prometheus
type: application
version: 27.12.0
```

### Why Helm

Without Helm you have a folder full of YAML files with hardcoded values. You copy-paste them for every environment, change image tags by hand, and forget one line somewhere. Helm turns these files into templates where you fill in the blanks from a single `values.yaml`. You can install the same chart in dev with 1 replica and in prod with 5 replicas using one command. You also get release tracking — Helm remembers what you installed and lets you rollback with one command if something breaks.

---

## Task 2 — Chart Structure

The chart lives in `k8s/devops-info-service/`.

```
k8s/devops-info-service/
├── Chart.yaml              # chart metadata (name, version, appVersion)
├── values.yaml             # default values
├── values-dev.yaml         # dev environment overrides
├── values-prod.yaml        # prod environment overrides
└── templates/
    ├── _helpers.tpl        # template helpers (fullname, labels, selector labels)
    ├── deployment.yaml     # Deployment with templated image, replicas, probes
    ├── service.yaml        # Service with templated type and ports
    ├── NOTES.txt           # post-install instructions
    └── hooks/
        ├── pre-install-job.yaml   # runs before install
        └── post-install-job.yaml  # runs after install
```

### Key values

| Value | Default | Purpose |
|-------|---------|---------|
| `replicaCount` | 3 | number of pod replicas |
| `image.repository` | devops-info-service | Docker image name |
| `image.tag` | latest | image tag |
| `image.pullPolicy` | Never | kind cluster: always use local images |
| `service.type` | NodePort | service exposure type |
| `service.nodePort` | 30080 | NodePort number |
| `resources.*` | 100m/128Mi req, 200m/256Mi lim | CPU and memory limits |
| `livenessProbe` | GET /health :8000, delay 10s | restarts pod if app hangs |
| `readinessProbe` | GET /health :8000, delay 5s | gates traffic until app is ready |
| `podSecurityContext` | runAsNonRoot, runAsUser 1000 | non-root security |

### Lint output

```
$ helm lint k8s/devops-info-service
==> Linting k8s/devops-info-service
[INFO] Chart.yaml: icon is recommended
1 chart(s) linted, 0 chart(s) failed
```

### Template preview

```
$ helm template myapp k8s/devops-info-service
---
# Source: devops-info-service/templates/service.yaml
apiVersion: v1
kind: Service
metadata:
  name: myapp-devops-info-service
spec:
  type: NodePort
  ports:
    - protocol: TCP
      port: 80
      targetPort: 8000
      nodePort: 30080
---
# Source: devops-info-service/templates/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: myapp-devops-info-service
spec:
  replicas: 3
  ...
  containers:
    - image: devops-info-service:latest
      livenessProbe:
        httpGet:
          path: /health
          port: 8000
      readinessProbe:
        httpGet:
          path: /health
          port: 8000
```

---

## Task 3 — Multi-Environment Support

### values-dev.yaml

- 1 replica (minimal resources)
- ClusterIP service (no NodePort needed for dev)
- lower CPU/memory limits
- shorter probe delays (faster feedback)

### values-prod.yaml

- 5 replicas (high availability)
- ClusterIP service (in real prod you would use Ingress)
- higher CPU/memory limits
- longer probe initial delays (app gets time to warm up)

### Installation

```bash
# Dev
helm install myapp-dev k8s/devops-info-service \
  -f k8s/devops-info-service/values-dev.yaml \
  -n dev --create-namespace

# Prod
helm install myapp-prod k8s/devops-info-service \
  -f k8s/devops-info-service/values-prod.yaml \
  -n prod --create-namespace
```

### kubectl get all -n dev (1 replica, ClusterIP)

```
NAME                                                 READY   STATUS    RESTARTS   AGE
pod/myapp-dev-devops-info-service-c8d7849db-jhqsv    1/1     Running   0          3m17s

NAME                                    TYPE        CLUSTER-IP      PORT(S)   AGE
service/myapp-dev-devops-info-service   ClusterIP   10.96.144.213   80/TCP    3m17s

NAME                                            READY   UP-TO-DATE   AVAILABLE   AGE
deployment.apps/myapp-dev-devops-info-service   1/1     1            1           3m17s
```

### kubectl get all -n prod (5 replicas, ClusterIP)

```
NAME                                                  READY   STATUS    RESTARTS   AGE
pod/myapp-prod-devops-info-service-648c9c9b5f-8jqt9   1/1     Running   0          2m50s
pod/myapp-prod-devops-info-service-648c9c9b5f-h9rts   1/1     Running   0          2m50s
pod/myapp-prod-devops-info-service-648c9c9b5f-q2stk   1/1     Running   0          2m50s
pod/myapp-prod-devops-info-service-648c9c9b5f-ssptn   1/1     Running   0          2m50s
pod/myapp-prod-devops-info-service-648c9c9b5f-zc6mc   1/1     Running   0          2m50s

NAME                                     TYPE        CLUSTER-IP     PORT(S)   AGE
service/myapp-prod-devops-info-service   ClusterIP   10.96.94.145   80/TCP    2m50s

NAME                                             READY   UP-TO-DATE   AVAILABLE   AGE
deployment.apps/myapp-prod-devops-info-service   5/5     5            5           2m50s
```

---

## Task 4 — Chart Hooks

Two hooks are implemented in `templates/hooks/`:

### Pre-install hook

File: `templates/hooks/pre-install-job.yaml`

- **When:** runs before any chart resources are created
- **Weight:** -5 (runs first if there are multiple hooks)
- **What it does:** simulates environment validation (prints release name, namespace, sleeps 5s)
- **Deletion policy:** `hook-succeeded` — Kubernetes Job is deleted after it completes successfully

### Post-install hook

File: `templates/hooks/post-install-job.yaml`

- **When:** runs after all chart resources are installed and ready
- **Weight:** 5
- **What it does:** simulates a smoke test (prints replica count, sleeps 5s)
- **Deletion policy:** `hook-succeeded` — deleted after success

### Hook annotations

```yaml
annotations:
  "helm.sh/hook": pre-install        # or post-install
  "helm.sh/hook-weight": "-5"        # execution order (lower = earlier)
  "helm.sh/hook-delete-policy": hook-succeeded
```

### Verification

Hooks ran during install and were deleted by the deletion policy:

```bash
$ helm install myapp k8s/devops-info-service
NAME: myapp
STATUS: deployed

$ kubectl get jobs
No resources found in default namespace.
# Jobs were deleted after successful completion per hook-succeeded policy
```

Dry-run shows hooks in the manifest:

```bash
$ helm install --dry-run --debug myapp k8s/devops-info-service | grep -A 3 "helm.sh/hook"
    "helm.sh/hook": pre-install
    "helm.sh/hook-weight": "-5"
    "helm.sh/hook-delete-policy": hook-succeeded
    ...
    "helm.sh/hook": post-install
    "helm.sh/hook-weight": "5"
    "helm.sh/hook-delete-policy": hook-succeeded
```

---

## Task 5 — Installation Evidence

### helm list -A

```
NAME       NAMESPACE  REVISION  STATUS    CHART                        APP VERSION
myapp      default    1         deployed  devops-info-service-0.1.0    1.0
myapp-dev  dev        3         deployed  devops-info-service-0.1.0    1.0
myapp-prod prod       1         deployed  devops-info-service-0.1.0    1.0
myapp-v2   default    1         deployed  devops-info-service-v2-0.1.0 1.0
```

### kubectl get all (default namespace)

```
NAME                                                  READY   STATUS    RESTARTS   AGE
pod/myapp-devops-info-service-6dcfbdcd7c-7nnrq        1/1     Running   0          4m25s
pod/myapp-devops-info-service-6dcfbdcd7c-kjcvh        1/1     Running   0          4m25s
pod/myapp-devops-info-service-6dcfbdcd7c-wt74g        1/1     Running   0          4m25s
pod/myapp-v2-devops-info-service-v2-5f9fd789b-b7m8s   1/1     Running   0          28s
pod/myapp-v2-devops-info-service-v2-5f9fd789b-zmwb7   1/1     Running   0          28s

NAME                                      TYPE        CLUSTER-IP     EXTERNAL-IP   PORT(S)        AGE
service/myapp-devops-info-service         NodePort    10.96.253.79   <none>        80:30080/TCP   4m25s
service/myapp-v2-devops-info-service-v2   ClusterIP   10.96.69.80    <none>        80/TCP         28s

NAME                                              READY   UP-TO-DATE   AVAILABLE   AGE
deployment.apps/myapp-devops-info-service         3/3     3            3           4m25s
deployment.apps/myapp-v2-devops-info-service-v2   2/2     2            2           28s
```

### App accessibility

```bash
$ kubectl port-forward service/myapp-devops-info-service 8080:80
$ curl http://localhost:8080/health
{"status":"healthy","timestamp":"2026-04-02T21:46:30.955990+00:00","uptime_seconds":21.65}

$ kubectl port-forward service/myapp-v2-devops-info-service-v2 8081:80
$ curl http://localhost:8081/health
{"status":"healthy","timestamp":"2026-04-02T21:50:38.532132+00:00","uptime_seconds":31.45}
```

---

## Operations

### Install

```bash
# Default (uses values.yaml)
helm install myapp k8s/devops-info-service

# With environment values
helm install myapp-dev k8s/devops-info-service \
  -f k8s/devops-info-service/values-dev.yaml \
  -n dev --create-namespace

helm install myapp-prod k8s/devops-info-service \
  -f k8s/devops-info-service/values-prod.yaml \
  -n prod --create-namespace
```

### Upgrade

```bash
helm upgrade myapp-dev k8s/devops-info-service \
  -f k8s/devops-info-service/values-prod.yaml \
  -n dev
# Release "myapp-dev" has been upgraded. REVISION: 2
```

### Rollback

```bash
helm rollback myapp-dev 1 -n dev
# Rollback was a success! REVISION: 3

helm history myapp-dev -n dev
# REVISION  STATUS      DESCRIPTION
# 1         superseded  Install complete
# 2         superseded  Upgrade complete
# 3         deployed    Rollback to 1
```

### Uninstall

```bash
helm uninstall myapp -n default
```

---

## Testing & Validation

### helm lint

```
$ helm lint k8s/devops-info-service
==> Linting k8s/devops-info-service
[INFO] Chart.yaml: icon is recommended
1 chart(s) linted, 0 chart(s) failed
```

### helm template

```bash
helm template myapp k8s/devops-info-service
# renders full manifests locally without touching the cluster
```

### Dry-run

```bash
helm install --dry-run --debug myapp k8s/devops-info-service
# shows what would be installed, including hooks
```

---

## Bonus — Library Charts

### Why library charts

Both `devops-info-service` and `devops-info-service-v2` need the same helper templates: `fullname`, `labels`, `selectorLabels`. Without a library, you copy-paste the `_helpers.tpl` and maintain it in two places. When you change a label, you have to update both charts. A library chart solves this — one place, used everywhere.

### Library chart structure

```
k8s/common-lib/
├── Chart.yaml              # type: library
└── templates/
    └── _helpers.tpl        # common.name, common.fullname, common.labels, common.selectorLabels
```

`Chart.yaml`:
```yaml
apiVersion: v2
name: common-lib
type: library          # cannot be installed directly
version: 0.1.0
```

### Shared templates

| Template | Purpose |
|----------|---------|
| `common.name` | chart name (truncated to 63 chars) |
| `common.fullname` | release-name + chart-name |
| `common.chart` | chart name + version for labels |
| `common.labels` | standard Kubernetes labels |
| `common.selectorLabels` | labels used in selector/matchLabels |

### Using the library in devops-info-service-v2

`Chart.yaml` dependency:
```yaml
dependencies:
  - name: common-lib
    version: 0.1.0
    repository: "file://../common-lib"
```

Install dependency:
```bash
helm dependency update k8s/devops-info-service-v2
```

In templates, use `common.*` instead of chart-specific helpers:
```yaml
metadata:
  name: {{ include "common.fullname" . }}
  labels:
    {{- include "common.labels" . | nindent 4 }}
```

### Both apps deployed successfully

```bash
$ helm install myapp k8s/devops-info-service
STATUS: deployed

$ helm install myapp-v2 k8s/devops-info-service-v2
STATUS: deployed

$ helm list
NAME      NAMESPACE  STATUS    CHART
myapp     default    deployed  devops-info-service-0.1.0
myapp-v2  default    deployed  devops-info-service-v2-0.1.0
```

### Benefits

- **DRY:** label logic lives in one place
- **Consistency:** both apps use exactly the same label format
- **Maintainability:** changing a label means updating one file, not two
- **Scalability:** any future chart can depend on `common-lib` too
