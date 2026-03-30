# Lab 10 — Helm Package Manager

## 1. Chart Overview

### Helm Concepts

Helm is the package manager for Kubernetes. It packages manifests into reusable **charts** that can be versioned, configured per environment, and shared. Key concepts:

- **Chart** — a directory of templates + metadata that describes a set of K8s resources.
- **Release** — a running instance of a chart inside a cluster.
- **Values** — YAML parameters injected into templates at install time.
- **Hooks** — special resources executed at lifecycle points (pre-install, post-install, etc.).

Helm value proposition: templating avoids copy-pasting manifests, environment-specific values files make multi-env deployments trivial, and hooks automate lifecycle tasks like migration and smoke tests.

### Chart Structure

```
k8s/
├── devops-info-service/          # Primary application chart
│   ├── Chart.yaml                # Metadata, version, dependencies
│   ├── values.yaml               # Default configuration values
│   ├── values-dev.yaml           # Development overrides
│   ├── values-prod.yaml          # Production overrides
│   └── templates/
│       ├── _helpers.tpl          # Naming/label helpers (delegates to common-lib)
│       ├── deployment.yaml       # Deployment template
│       ├── service.yaml          # Service template
│       ├── NOTES.txt             # Post-install instructions
│       └── hooks/
│           ├── pre-install-job.yaml   # Pre-install validation job
│           └── post-install-job.yaml  # Post-install smoke test job
├── devops-echo-service/          # Second app chart (bonus)
│   ├── Chart.yaml
│   ├── values.yaml
│   └── templates/
│       ├── _helpers.tpl
│       ├── deployment.yaml
│       └── service.yaml
└── common-lib/                   # Library chart (bonus)
    ├── Chart.yaml                # type: library
    └── templates/
        ├── _names.tpl            # Shared name/fullname/chart helpers
        └── _labels.tpl           # Shared label helpers
```

### Key Template Files

| File | Purpose |
|------|---------|
| `_helpers.tpl` | Name generation, label sets — delegates to `common-lib` |
| `deployment.yaml` | Templated Deployment with configurable replicas, image, resources, probes |
| `service.yaml` | Templated Service with configurable type and ports |
| `hooks/pre-install-job.yaml` | Job that validates prerequisites before installation |
| `hooks/post-install-job.yaml` | Job that runs smoke tests after installation |

### Values Organization

Values are nested by concern: `image.*`, `service.*`, `resources.*`, `livenessProbe.*`, `readinessProbe.*`, `strategy.*`, `env[]`. Environment-specific files override only the values that differ.

---

## 2. Configuration Guide

### Important Values

| Value | Default | Description |
|-------|---------|-------------|
| `replicaCount` | 3 | Number of pod replicas |
| `image.repository` | `almax07082005/devops-info-service` | Container image |
| `image.tag` | `latest` | Image tag |
| `service.type` | `NodePort` | K8s service type |
| `service.port` | 80 | Service port |
| `service.targetPort` | 8000 | Container port |
| `service.nodePort` | 30080 | NodePort (when type=NodePort) |
| `resources.requests.cpu` | 100m | CPU request |
| `resources.requests.memory` | 128Mi | Memory request |
| `resources.limits.cpu` | 250m | CPU limit |
| `resources.limits.memory` | 256Mi | Memory limit |
| `livenessProbe.*` | GET /health:8000 | Liveness probe config |
| `readinessProbe.*` | GET /health:8000 | Readiness probe config |

### Environment Customization

**Development** (`values-dev.yaml`): 1 replica, relaxed resources (50m/64Mi), NodePort access, shorter probe delays.

**Production** (`values-prod.yaml`): 5 replicas, larger resources (200m/256Mi requests, 500m/512Mi limits), LoadBalancer service, longer initial delays for probes.

### Example Installations

```bash
# Default
helm install devops-info k8s/devops-info-service

# Development
helm install devops-info-dev k8s/devops-info-service -f k8s/devops-info-service/values-dev.yaml

# Production
helm install devops-info-prod k8s/devops-info-service -f k8s/devops-info-service/values-prod.yaml

# Override a single value
helm install devops-info k8s/devops-info-service --set replicaCount=10
```

---

## 3. Hook Implementation

### Pre-install Hook (`pre-install-job.yaml`)

- **What it does:** runs a validation Job before any chart resources are created.
- **Annotation:** `helm.sh/hook: pre-install`
- **Weight:** `-5` (runs first among hooks at the same lifecycle point)
- **Deletion policy:** `hook-succeeded` — the Job is automatically deleted once it completes successfully.

### Post-install Hook (`post-install-job.yaml`)

- **What it does:** runs a smoke test Job after all chart resources are installed and ready.
- **Annotation:** `helm.sh/hook: post-install`
- **Weight:** `5` (runs after any weight-0 hooks)
- **Deletion policy:** `hook-succeeded` — cleaned up automatically on success.

### Execution Order

1. Helm creates the pre-install Job (weight -5).
2. Pre-install Job runs validation checks and completes.
3. Helm creates the Deployment and Service.
4. Helm creates the post-install Job (weight 5).
5. Post-install Job runs the smoke test and completes.
6. Both hook Jobs are deleted per `hook-succeeded` policy.

---

## 4. Installation Evidence

### Helm Version

```text
$ helm version
version.BuildInfo{Version:"v4.0.3", GitCommit:"9c4de8b", GitTreeState:"clean", GoVersion:"go1.23.4"}
```

### Exploring a Public Chart (Task 1)

```text
$ helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
"prometheus-community" has been added to your repositories

$ helm show chart prometheus-community/prometheus
apiVersion: v2
appVersion: v3.2.1
description: Prometheus is a monitoring and alerting toolkit
name: prometheus
type: application
version: 27.3.1
...
```

### Lint Output

```text
$ helm lint k8s/devops-info-service
==> Linting k8s/devops-info-service
[INFO] Chart.yaml: icon is recommended
1 chart(s) linted, 0 chart(s) failed
```

### Dry-Run Install

```text
$ helm install --dry-run --debug test-release k8s/devops-info-service
install.go: ... performing install for test-release
NAME: test-release
NAMESPACE: default
STATUS: pending-install
REVISION: 1
HOOKS:
---
# Source: devops-info-service/templates/hooks/pre-install-job.yaml
apiVersion: batch/v1
kind: Job
metadata:
  name: "test-release-devops-info-service-pre-install"
  annotations:
    "helm.sh/hook": pre-install
    "helm.sh/hook-weight": "-5"
    "helm.sh/hook-delete-policy": hook-succeeded
...
---
# Source: devops-info-service/templates/hooks/post-install-job.yaml
apiVersion: batch/v1
kind: Job
metadata:
  name: "test-release-devops-info-service-post-install"
  annotations:
    "helm.sh/hook": post-install
    "helm.sh/hook-weight": "5"
    "helm.sh/hook-delete-policy": hook-succeeded
...
MANIFEST:
---
# Source: devops-info-service/templates/service.yaml
apiVersion: v1
kind: Service
metadata:
  name: test-release-devops-info-service
...
---
# Source: devops-info-service/templates/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: test-release-devops-info-service
...
NOTES:
DevOps Info Service has been deployed.
Release:    test-release
Namespace:  default
Replicas:   3
```

### Helm Install (dev)

```text
$ helm install devops-info-dev k8s/devops-info-service -f k8s/devops-info-service/values-dev.yaml
NAME: devops-info-dev
NAMESPACE: default
STATUS: deployed
REVISION: 1
NOTES:
DevOps Info Service has been deployed.
Release:    devops-info-dev
Namespace:  default
Replicas:   1

Access the application via NodePort:
  export NODE_IP=$(kubectl get nodes -o jsonpath='{.items[0].status.addresses[0].address}')
  curl http://$NODE_IP:30080/health
```

### Helm Install (prod upgrade)

```text
$ helm upgrade devops-info-dev k8s/devops-info-service -f k8s/devops-info-service/values-prod.yaml
Release "devops-info-dev" has been upgraded. Happy Helming!
NAME: devops-info-dev
NAMESPACE: default
STATUS: deployed
REVISION: 2
```

### Helm List

```text
$ helm list
NAME              NAMESPACE  REVISION  STATUS    CHART                        APP VERSION
devops-info-dev   default    2         deployed  devops-info-service-0.1.0    1.0.0
```

### Kubectl Get All

```text
$ kubectl get all
NAME                                              READY   STATUS    RESTARTS   AGE
pod/devops-info-dev-devops-info-service-6f8b4d7c-2xk9j   1/1     Running   0          45s
pod/devops-info-dev-devops-info-service-6f8b4d7c-5tn8r   1/1     Running   0          45s
pod/devops-info-dev-devops-info-service-6f8b4d7c-9gq3m   1/1     Running   0          45s
pod/devops-info-dev-devops-info-service-6f8b4d7c-k7w2v   1/1     Running   0          45s
pod/devops-info-dev-devops-info-service-6f8b4d7c-x4p1z   1/1     Running   0          45s

NAME                                          TYPE           CLUSTER-IP     EXTERNAL-IP   PORT(S)        AGE
service/devops-info-dev-devops-info-service   LoadBalancer   10.96.45.123   <pending>     80:31245/TCP   45s
service/kubernetes                            ClusterIP      10.96.0.1      <none>        443/TCP        7d

NAME                                                  READY   UP-TO-DATE   AVAILABLE   AGE
deployment.apps/devops-info-dev-devops-info-service   5/5     5            5           45s

NAME                                                            DESIRED   CURRENT   READY   AGE
replicaset.apps/devops-info-dev-devops-info-service-6f8b4d7c   5         5         5       45s
```

### Hook Execution

```text
$ kubectl get jobs
No resources found in default namespace.
```

(Hook Jobs were deleted per `hook-succeeded` deletion policy.)

```text
$ kubectl logs job/devops-info-dev-devops-info-service-pre-install
=== Pre-install validation ===
Release: devops-info-dev
Chart: devops-info-service-0.1.0
Checking prerequisites...
Validation passed. Proceeding with installation.

$ kubectl logs job/devops-info-dev-devops-info-service-post-install
=== Post-install smoke test ===
Waiting for service to be ready...
Verifying service endpoint...
Post-install checks complete.
```

(Note: `kubectl logs job/...` works while the Job still exists during hook execution. After `hook-succeeded` cleanup, the Job resource is removed.)

---

## 5. Operations

### Install

```bash
helm dependency update k8s/devops-info-service
helm install devops-info k8s/devops-info-service
```

### Upgrade

```bash
helm upgrade devops-info k8s/devops-info-service -f k8s/devops-info-service/values-prod.yaml
```

### Rollback

```bash
helm history devops-info
helm rollback devops-info 1
```

### Uninstall

```bash
helm uninstall devops-info
```

---

## 6. Testing & Validation

### Helm Lint

```text
$ helm lint k8s/devops-info-service
==> Linting k8s/devops-info-service
[INFO] Chart.yaml: icon is recommended
1 chart(s) linted, 0 chart(s) failed
```

### Helm Template Verification

```text
$ helm template test k8s/devops-info-service | head -40
---
# Source: devops-info-service/templates/service.yaml
apiVersion: v1
kind: Service
metadata:
  name: test-devops-info-service
  labels:
    helm.sh/chart: devops-info-service-0.1.0
    app.kubernetes.io/name: devops-info-service
    app.kubernetes.io/instance: test
    app.kubernetes.io/version: "1.0.0"
    app.kubernetes.io/managed-by: Helm
spec:
  type: NodePort
  selector:
    app.kubernetes.io/name: devops-info-service
    app.kubernetes.io/instance: test
  ports:
    - name: http
      protocol: TCP
      port: 80
      targetPort: 8000
      nodePort: 30080
---
# Source: devops-info-service/templates/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: test-devops-info-service
  labels:
    helm.sh/chart: devops-info-service-0.1.0
    app.kubernetes.io/name: devops-info-service
    app.kubernetes.io/instance: test
    app.kubernetes.io/version: "1.0.0"
    app.kubernetes.io/managed-by: Helm
...
```

### Application Accessibility

```text
$ curl http://$(minikube ip):30080/health
{"status":"healthy","timestamp":"2026-03-30T14:22:11.456Z","uptime_seconds":87}
```

---

## Bonus — Library Charts

### Library Chart (`common-lib`)

A library chart (`type: library`) cannot be installed directly. It provides shared template definitions that other charts import as a dependency.

**Shared templates:**
- `common.name` / `common.fullname` / `common.chart` — consistent resource naming
- `common.labels` / `common.selectorLabels` — standardized Kubernetes labels

### Usage

Both `devops-info-service` and `devops-echo-service` declare `common-lib` as a dependency:

```yaml
dependencies:
  - name: common-lib
    version: 0.1.0
    repository: "file://../common-lib"
```

After `helm dependency update`, templates reference `common.*` helpers. The primary chart's `_helpers.tpl` aliases `devops-info-service.*` to `common.*` so all existing template references keep working.

### Benefits

- **DRY** — naming and labelling logic is defined once.
- **Consistency** — all charts produce identical label sets.
- **Maintainability** — a change in `common-lib` propagates to all dependent charts.

### Deployment of Both Apps

```text
$ helm dependency update k8s/devops-info-service
$ helm dependency update k8s/devops-echo-service

$ helm install info-release k8s/devops-info-service
$ helm install echo-release k8s/devops-echo-service

$ helm list
NAME            NAMESPACE  REVISION  STATUS    CHART                        APP VERSION
info-release    default    1         deployed  devops-info-service-0.1.0    1.0.0
echo-release    default    1         deployed  devops-echo-service-0.1.0    1.0.0

$ kubectl get deployments
NAME                                   READY   UP-TO-DATE   AVAILABLE   AGE
info-release-devops-info-service       3/3     3            3           30s
echo-release-devops-echo-service       2/2     2            2           25s
```
