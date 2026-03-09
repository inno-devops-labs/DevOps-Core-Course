# Helm Chart Documentation — DevOps Info Service

## Task 1 — Helm Fundamentals

### Installation

```bash
# Install Helm (Windows via winget)
winget install Helm.Helm

# Verify installation
helm version
# version.BuildInfo{Version:"v4.x.x", ...}
```

### Exploring Public Charts

```bash
# Add Prometheus community repo
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo update

# Search for charts
helm search repo prometheus

# Inspect a chart
helm show chart prometheus-community/prometheus
```

### Helm's Value Proposition

| Without Helm | With Helm |
|---|---|
| Static YAML files per environment | Single chart + values overrides |
| Manual resource tracking | `helm list` shows all releases |
| No rollback mechanism | `helm rollback <release> <revision>` |
| Duplicate labels/helpers | Shared library templates |
| No dependency management | `Chart.yaml` dependencies |

---

## Task 2 — Chart Structure

### Directory Layout

```
k8s/
├── devops-info-chart/          # Main application chart (Task 2–4)
│   ├── Chart.yaml              # Chart metadata and dependencies
│   ├── values.yaml             # Default configuration values
│   ├── values-dev.yaml         # Dev environment overrides (Task 3)
│   ├── values-prod.yaml        # Prod environment overrides (Task 3)
│   ├── charts/
│   │   └── common-lib/         # Embedded library chart dependency
│   └── templates/
│       ├── _helpers.tpl        # Chart-specific name/fullname helpers
│       ├── deployment.yaml     # Deployment template
│       ├── service.yaml        # Service template
│       ├── NOTES.txt           # Post-install instructions
│       └── hooks/
│           ├── pre-install-job.yaml   # Pre-install validation job
│           └── post-install-job.yaml  # Post-install smoke test job
│
├── app2-chart/                 # Second app chart (Bonus)
│   ├── Chart.yaml
│   ├── values.yaml
│   ├── values-dev.yaml
│   ├── charts/
│   │   └── common-lib/         # Same embedded library
│   └── templates/
│       ├── _helpers.tpl
│       ├── deployment.yaml
│       ├── service.yaml
│       └── NOTES.txt
│
└── common-lib/                 # Source of the library chart (Bonus)
    ├── Chart.yaml
    └── templates/
        └── _helpers.tpl        # Shared: common.labels, common.selectorLabels,
                                #         common.fullname, common.name, common.chart
```

### Key Template Files

| File | Purpose |
|---|---|
| `Chart.yaml` | Chart name, version, appVersion, and dependency on `common-lib` |
| `values.yaml` | Sensible production-like defaults |
| `_helpers.tpl` | Chart-specific `fullname` and `name` helpers |
| `deployment.yaml` | Templated Deployment using values + common-lib labels |
| `service.yaml` | Templated Service with conditional NodePort |
| `NOTES.txt` | Post-install instructions shown after `helm install` |
| `hooks/pre-install-job.yaml` | Runs before deployment — validates configuration |
| `hooks/post-install-job.yaml` | Runs after deployment — smoke tests |

### Values Organization

```yaml
replicaCount: 3           # Pod replica count

image:                    # Container image configuration
  repository: ...
  tag: ...
  pullPolicy: ...

service:                  # Kubernetes Service configuration
  type: NodePort | LoadBalancer | ClusterIP
  port: 80
  targetPort: 5000
  nodePort: 30080         # Only used when type=NodePort

env: []                   # Environment variables as list of {name, value}

resources:                # CPU and memory requests/limits
  requests: ...
  limits: ...

livenessProbe:            # Liveness probe (httpGet on /health)
readinessProbe:           # Readiness probe (httpGet on /health)
strategy:                 # Rolling update strategy
```

---

## Task 3 — Multi-Environment Support

### Environment Differences

| Configuration | Dev | Prod |
|---|---|---|
| Replicas | 1 | 5 |
| Image tag | `latest` | `lab02` (pinned) |
| CPU request | 50m | 200m |
| Memory limit | 128Mi | 512Mi |
| Service type | NodePort (30080) | LoadBalancer |
| Liveness delay | 5s | 30s |
| Readiness period | 10s | 3s |

### Usage

```bash
# Development
helm install dev-release k8s/devops-info-chart \
  -f k8s/devops-info-chart/values-dev.yaml

# Production
helm install prod-release k8s/devops-info-chart \
  -f k8s/devops-info-chart/values-prod.yaml

# One-off override
helm install myapp k8s/devops-info-chart --set replicaCount=10

# Upgrade dev to use a new tag
helm upgrade dev-release k8s/devops-info-chart \
  -f k8s/devops-info-chart/values-dev.yaml \
  --set image.tag=lab03
```

### Verification

```
$ helm install dev-release k8s/devops-info-chart \
    -f k8s/devops-info-chart/values-dev.yaml --set service.nodePort=30091
NAME: dev-release
LAST DEPLOYED: Mon Mar  9 23:12:30 2026
NAMESPACE: default
STATUS: deployed
REVISION: 1
NOTES:
Replicas: 1
Image: vladimirzhidkov/devops-info-service:latest
Get the application URL:
  http://$(minikube ip):30091
```

```bash
# Verify dev uses 1 replica vs myrelease's 3
kubectl get deployment -l app.kubernetes.io/instance=dev-release
# NAME                           READY   UP-TO-DATE   AVAILABLE
# dev-release-devops-info-chart  1/1     1            1

kubectl get deployment -l app.kubernetes.io/instance=myrelease
# NAME                             READY   UP-TO-DATE   AVAILABLE
# myrelease-devops-info-chart      3/3     3            3
```

---

## Task 4 — Chart Hooks

### Hook Overview

| Hook | Type | Weight | Delete Policy | Purpose |
|---|---|---|---|---|
| `pre-install-job` | `pre-install` | `-5` | `hook-succeeded` | Validate configuration before deploy |
| `post-install-job` | `post-install` | `5` | `hook-succeeded` | Smoke test after deploy |

### Execution Order

```
helm install
    │
    ├── 1. pre-install hook (weight -5)   ← validates image, replicas, service type
    │       Job runs in cluster, exits 0
    │       Job deleted automatically (hook-succeeded policy)
    │
    ├── 2. Main resources installed
    │       Deployment, Service created and brought to Ready
    │
    └── 3. post-install hook (weight 5)   ← waits 10s, confirms app is ready
            Job runs in cluster, exits 0
            Job deleted automatically (hook-succeeded policy)
```

### Hook Annotations Explained

```yaml
annotations:
  "helm.sh/hook": pre-install        # When to run
  "helm.sh/hook-weight": "-5"        # Execution order (lower = earlier)
  "helm.sh/hook-delete-policy": hook-succeeded  # Cleanup policy
```

**Delete policies:**
- `hook-succeeded` — delete after successful completion (keeps cluster clean)
- `before-hook-creation` — delete previous hook before running new one
- `hook-failed` — delete only on failure (useful for debugging)

### Testing Hooks

```bash
# Dry-run to see hook templates rendered
helm install --dry-run --debug test-release k8s/devops-info-chart

# Install and watch hooks
helm install myrelease k8s/devops-info-chart
kubectl get jobs -w

# Check hook output
kubectl describe job myrelease-devops-info-chart-pre-install
kubectl logs job/myrelease-devops-info-chart-pre-install

# Verify hooks were cleaned up (hook-succeeded)
kubectl get jobs
# Should show no hook jobs once they have completed
```

---

## Task 5 — Installation Evidence

### helm lint

```
$ helm lint k8s/devops-info-chart
==> Linting k8s/devops-info-chart
[INFO] Chart.yaml: icon is recommended

1 chart(s) linted, 0 chart(s) failed

$ helm lint k8s/app2-chart
==> Linting k8s/app2-chart
[INFO] Chart.yaml: icon is recommended

1 chart(s) linted, 0 chart(s) failed
```

### helm template (dry render)

```bash
helm template myrelease k8s/devops-info-chart --set service.nodePort=30090
```

### Install

```
$ helm install myrelease k8s/devops-info-chart --set service.nodePort=30090
NAME: myrelease
LAST DEPLOYED: Mon Mar  9 23:08:10 2026
NAMESPACE: default
STATUS: deployed
REVISION: 1
TEST SUITE: None
NOTES:
1. DevOps Info Service has been deployed!

Release: myrelease
Namespace: default
Chart version: 0.1.0
App version: lab02

Replicas: 3
Image: vladimirzhidkov/devops-info-service:lab02

Get the application URL:
  http://$(minikube ip):30090

Health check endpoint: /health
```

### helm list

```
NAME          NAMESPACE  REVISION  UPDATED                            STATUS    CHART                    APP VERSION
app2-release  default    1         2026-03-09 23:12:59 +0300 MSK      deployed  app2-chart-0.1.0         latest
dev-release   default    1         2026-03-09 23:12:30 +0300 MSK      deployed  devops-info-chart-0.1.0  lab02
myrelease     default    1         2026-03-09 23:08:10 +0300 MSK      deployed  devops-info-chart-0.1.0  lab02
```

### kubectl get all (myrelease)

```
NAME                                              READY   STATUS    RESTARTS   AGE
pod/myrelease-devops-info-chart-99f6f7db6-d996k   1/1     Running   0          4m50s
pod/myrelease-devops-info-chart-99f6f7db6-vxqkj   1/1     Running   0          4m50s
pod/myrelease-devops-info-chart-99f6f7db6-w55d8   1/1     Running   0          4m50s

NAME                                  TYPE       CLUSTER-IP      EXTERNAL-IP   PORT(S)        AGE
service/myrelease-devops-info-chart   NodePort   10.107.234.12   <none>        80:30090/TCP   4m50s

NAME                                          READY   UP-TO-DATE   AVAILABLE   AGE
deployment.apps/myrelease-devops-info-chart   3/3     3            3           4m50s

NAME                                                    DESIRED   CURRENT   READY   AGE
replicaset.apps/myrelease-devops-info-chart-99f6f7db6   3         3         3       4m50s
```

### Hook Execution

Хуки выполнились и были автоматически удалены согласно политике `hook-succeeded`:

```
$ kubectl get jobs
No resources found in default namespace.
```

Хуки успешно отработали (pre-install провалидировал конфигурацию, post-install выполнил smoke test) и удалились — кластер чистый.

```
$ helm history myrelease
REVISION  UPDATED                    STATUS    CHART                    APP VERSION  DESCRIPTION
1         Mon Mar  9 23:08:10 2026   deployed  devops-info-chart-0.1.0  lab02        Install complete
```

---

## Operations

### Install

```bash
# Default install
helm install myrelease k8s/devops-info-chart

# With environment values
helm install myrelease k8s/devops-info-chart -f k8s/devops-info-chart/values-dev.yaml

# With namespace
helm install myrelease k8s/devops-info-chart --namespace myns --create-namespace

# Dry-run first
helm install --dry-run --debug myrelease k8s/devops-info-chart
```

### Upgrade

```bash
# Upgrade release in-place
helm upgrade myrelease k8s/devops-info-chart

# Upgrade with new values
helm upgrade myrelease k8s/devops-info-chart -f k8s/devops-info-chart/values-prod.yaml

# Upgrade and install if not exists
helm upgrade --install myrelease k8s/devops-info-chart
```

### Rollback

```bash
# View release history
helm history myrelease

# Rollback to previous revision
helm rollback myrelease

# Rollback to specific revision
helm rollback myrelease 1
```

### Uninstall

```bash
helm uninstall myrelease

# Keep history
helm uninstall myrelease --keep-history
```

---

## Bonus — Library Charts

### Problem: Template Duplication

Without a library chart, `devops-info-chart` and `app2-chart` would each define
their own `labels`, `selectorLabels`, `fullname`, and `name` templates — identical
boilerplate copied in every chart's `_helpers.tpl`.

### Solution: common-lib

`k8s/common-lib` is a **library chart** (`type: library` in `Chart.yaml`). Library
charts cannot be installed directly; they only provide named templates for
dependent charts to `include`.

**Shared templates exported by `common-lib`:**

| Template | Output |
|---|---|
| `common.name` | Chart name (respects `nameOverride`) |
| `common.fullname` | `{release}-{chart}` (respects `fullnameOverride`) |
| `common.chart` | `{chart}-{version}` for the `helm.sh/chart` label |
| `common.labels` | Standard set of `app.kubernetes.io/*` labels |
| `common.selectorLabels` | `app.kubernetes.io/name` + `app.kubernetes.io/instance` |

### Usage in Both Charts

**Chart.yaml** declares the dependency:

```yaml
dependencies:
  - name: common-lib
    version: 0.1.0
    repository: "file://../common-lib"
```

**templates/deployment.yaml** uses library templates directly:

```yaml
metadata:
  name: {{ include "common.fullname" . }}
  labels:
    {{- include "common.labels" . | nindent 4 }}
spec:
  selector:
    matchLabels:
      {{- include "common.selectorLabels" . | nindent 6 }}
```

Both `devops-info-chart` and `app2-chart` use **identical** label generation
logic via `common.labels` — no duplication.

### Setting Up Dependencies

The library is embedded in each chart's `charts/` directory so it works without
running `helm dependency update`. To refresh from source:

```bash
helm dependency update k8s/devops-info-chart
helm dependency update k8s/app2-chart
```

### Deploying Both Apps

```
$ helm install app2-release k8s/app2-chart --set service.nodePort=30092 --set service.type=NodePort
NAME: app2-release
LAST DEPLOYED: Mon Mar  9 23:12:59 2026
NAMESPACE: default
STATUS: deployed
REVISION: 1
NOTES:
Replicas: 2
Image: hashicorp/http-echo:latest
Echo text: "Hello from App 2!"

$ helm list
NAME          NAMESPACE  REVISION  UPDATED                            STATUS    CHART                    APP VERSION
app2-release  default    1         2026-03-09 23:12:59 +0300 MSK      deployed  app2-chart-0.1.0         latest
dev-release   default    1         2026-03-09 23:12:30 +0300 MSK      deployed  devops-info-chart-0.1.0  lab02
myrelease     default    1         2026-03-09 23:08:10 +0300 MSK      deployed  devops-info-chart-0.1.0  lab02
```

### Benefits of Library Charts

- **DRY** — label generation logic lives in one place; fix it once, affects all charts
- **Consistency** — all apps produce identical `app.kubernetes.io/*` labels and naming
- **Maintainability** — add a new standard label to `common-lib`, all apps inherit it
- **Governance** — centralized label policy enforced via shared templates
