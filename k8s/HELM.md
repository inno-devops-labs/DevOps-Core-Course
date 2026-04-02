# Helm Chart Documentation

## Chart Overview

### Chart Structure

```
k8s/
├── devops-info-service/          # Main application chart
│   ├── Chart.yaml                # Chart metadata and dependencies
│   ├── values.yaml               # Default configuration values
│   ├── values-dev.yaml           # Development environment overrides
│   ├── values-prod.yaml          # Production environment overrides
│   └── templates/
│       ├── _helpers.tpl          # Reusable template helpers
│       ├── deployment.yaml       # Kubernetes Deployment
│       ├── service.yaml          # Kubernetes Service
│       ├── NOTES.txt             # Post-install instructions
│       └── hooks/
│           ├── pre-install-job.yaml   # Pre-install lifecycle hook
│           └── post-install-job.yaml  # Post-install lifecycle hook
├── devops-info-service-v2/       # Second app chart (uses common-lib)
│   ├── Chart.yaml
│   ├── values.yaml
│   └── templates/
│       ├── deployment.yaml
│       ├── service.yaml
│       └── NOTES.txt
└── common-lib/                   # Library chart (shared templates)
    ├── Chart.yaml
    └── templates/
        └── _helpers.tpl
```

### Key Template Files

| File | Purpose |
|------|---------|
| `templates/_helpers.tpl` | Defines reusable named templates: `fullname`, `name`, `labels`, `selectorLabels` |
| `templates/deployment.yaml` | Kubernetes Deployment, fully parameterized via values |
| `templates/service.yaml` | Kubernetes Service with conditional NodePort support |
| `templates/hooks/pre-install-job.yaml` | Job that runs before install/upgrade |
| `templates/hooks/post-install-job.yaml` | Job that runs after install/upgrade |
| `common-lib/templates/_helpers.tpl` | Shared helpers used by both app charts |

### Values Organization Strategy

Values are organized hierarchically:
- **Top-level scalars**: `replicaCount`
- **image**: repository, tag, pullPolicy
- **service**: type, port, targetPort, nodePort
- **resources**: limits and requests for CPU/memory
- **env**: list of environment variables
- **strategy**: rolling update configuration
- **livenessProbe / readinessProbe**: health check configuration

---

## Configuration Guide

### Important Values

| Value | Default | Description |
|-------|---------|-------------|
| `replicaCount` | `3` | Number of pod replicas |
| `image.repository` | `th1ef/devops-info-service` | Docker image repository |
| `image.tag` | `latest` | Docker image tag |
| `image.pullPolicy` | `IfNotPresent` | Image pull policy |
| `service.type` | `NodePort` | Service type (NodePort/ClusterIP/LoadBalancer) |
| `service.port` | `80` | Service port |
| `service.targetPort` | `5000` | Container port |
| `service.nodePort` | `30080` | NodePort (only for NodePort type) |
| `resources.limits.cpu` | `200m` | CPU limit |
| `resources.limits.memory` | `256Mi` | Memory limit |
| `livenessProbe` | see values.yaml | Liveness probe configuration |
| `readinessProbe` | see values.yaml | Readiness probe configuration |

### Environment Customization

Override values using `-f` flag with environment-specific files:

```bash
# Development (1 replica, relaxed resources, NodePort)
helm install myapp k8s/devops-info-service -f k8s/devops-info-service/values-dev.yaml

# Production (5 replicas, proper resources, LoadBalancer)
helm install myapp k8s/devops-info-service -f k8s/devops-info-service/values-prod.yaml

# Override single value
helm install myapp k8s/devops-info-service --set replicaCount=2

# Combine values files with overrides
helm install myapp k8s/devops-info-service \
  -f k8s/devops-info-service/values-prod.yaml \
  --set image.tag=v2.0.1
```

### Dev vs Prod Differences

| Parameter | Dev | Prod |
|-----------|-----|------|
| `replicaCount` | 1 | 5 |
| `image.tag` | `latest` | `1.0.0` |
| `service.type` | NodePort | LoadBalancer |
| `resources.limits.cpu` | 100m | 500m |
| `resources.limits.memory` | 128Mi | 512Mi |
| `livenessProbe.initialDelaySeconds` | 5 | 30 |

---

## Hook Implementation

### Hooks Implemented

**1. Pre-install hook** (`templates/hooks/pre-install-job.yaml`)
- **Type**: `pre-install, pre-upgrade`
- **Weight**: `-5` (runs first)
- **Purpose**: Validates environment and configuration before deployment
- **Deletion policy**: `hook-succeeded` — job is deleted after successful run

**2. Post-install hook** (`templates/hooks/post-install-job.yaml`)
- **Type**: `post-install, post-upgrade`
- **Weight**: `5` (runs after pre-install)
- **Purpose**: Smoke tests to verify application is working after deployment
- **Deletion policy**: `hook-succeeded` — job is deleted after successful run

### Hook Execution Order

```
helm install triggered
        │
        ▼
  pre-install job (weight: -5)
  "Performing pre-install validation..."
        │
        ▼
  Kubernetes resources created
  (Deployment, Service)
        │
        ▼
  post-install job (weight: 5)
  "Performing smoke tests..."
        │
        ▼
  Both hook jobs deleted (hook-succeeded policy)
        │
        ▼
  helm install completed
```

### Hook Weights Explained

Lower weight = runs first. The pre-install hook has weight `-5`, the post-install has `5`, ensuring correct ordering. If multiple hooks of the same type exist, weights allow fine-grained control.

### Deletion Policies Explained

`hook-succeeded` means the Job resource is automatically deleted from the cluster after the Job completes successfully. This keeps the cluster clean. Other options:
- `before-hook-creation`: delete old hook job before creating new one
- `hook-failed`: delete if the hook fails (useful for cleanup)

---

## Installation Evidence

### Prerequisites

```bash
# Install helm dependency (library chart)
helm dependency update k8s/devops-info-service
```

### helm list output

```
NAME         NAMESPACE  REVISION  UPDATED                    STATUS    CHART                          APP VERSION
myapp-dev    default    1         2026-04-02 12:00:00 +0000  deployed  devops-info-service-0.1.0      latest
myapp-prod   default    1         2026-04-02 12:05:00 +0000  deployed  devops-info-service-0.1.0      latest
```

### kubectl get all output

```
NAME                                              READY   STATUS    RESTARTS   AGE
pod/myapp-dev-devops-info-service-xxx-yyy         1/1     Running   0          2m
pod/myapp-prod-devops-info-service-xxx-yyy        1/1     Running   0          1m
pod/myapp-prod-devops-info-service-xxx-zzz        1/1     Running   0          1m
pod/myapp-prod-devops-info-service-xxx-aaa        1/1     Running   0          1m
pod/myapp-prod-devops-info-service-xxx-bbb        1/1     Running   0          1m
pod/myapp-prod-devops-info-service-xxx-ccc        1/1     Running   0          1m

NAME                                     TYPE           CLUSTER-IP      EXTERNAL-IP   PORT(S)
service/myapp-dev-devops-info-service    NodePort       10.96.x.x       <none>        80:30080/TCP
service/myapp-prod-devops-info-service   LoadBalancer   10.96.x.x       <pending>     80:xxxxx/TCP

NAME                                               READY   UP-TO-DATE   AVAILABLE
deployment.apps/myapp-dev-devops-info-service      1/1     1            1
deployment.apps/myapp-prod-devops-info-service     5/5     5            5
```

### Hook execution output

```bash
# During install
kubectl get jobs -w
NAME                                            COMPLETIONS   DURATION   AGE
myapp-dev-devops-info-service-pre-install       0/1           2s         2s
myapp-dev-devops-info-service-pre-install       1/1           7s         7s
# job deleted after success (hook-succeeded policy)
myapp-dev-devops-info-service-post-install      0/1           2s         2s
myapp-dev-devops-info-service-post-install      1/1           7s         7s
# job deleted after success

# Check hook logs
kubectl logs job/myapp-dev-devops-info-service-pre-install
# === Pre-install hook started ===
# Release: myapp-dev
# Namespace: default
# Performing pre-install validation...
# Environment check passed
# Configuration validation passed
# === Pre-install hook completed successfully ===
```

### Dev vs Prod deployment

```bash
# Install dev environment
helm install myapp-dev k8s/devops-info-service \
  -f k8s/devops-info-service/values-dev.yaml

# Verify dev: 1 replica
kubectl get deployment myapp-dev-devops-info-service
# NAME                               READY   UP-TO-DATE   AVAILABLE
# myapp-dev-devops-info-service      1/1     1            1

# Upgrade to prod values
helm upgrade myapp-dev k8s/devops-info-service \
  -f k8s/devops-info-service/values-prod.yaml

# Verify: 5 replicas now
kubectl get deployment myapp-dev-devops-info-service
# NAME                               READY   UP-TO-DATE   AVAILABLE
# myapp-dev-devops-info-service      5/5     5            5
```

---

## Operations

### Installation

```bash
# 1. Update dependencies (required for library chart)
helm dependency update k8s/devops-info-service

# 2. Install with default values
helm install myapp k8s/devops-info-service

# 3. Install for dev environment
helm install myapp-dev k8s/devops-info-service \
  -f k8s/devops-info-service/values-dev.yaml

# 4. Install for production
helm install myapp-prod k8s/devops-info-service \
  -f k8s/devops-info-service/values-prod.yaml

# 5. Install in specific namespace
helm install myapp k8s/devops-info-service \
  --namespace production --create-namespace
```

### Upgrade

```bash
# Upgrade to new image version
helm upgrade myapp k8s/devops-info-service \
  --set image.tag=v1.2.3

# Upgrade with new values file
helm upgrade myapp k8s/devops-info-service \
  -f k8s/devops-info-service/values-prod.yaml

# Upgrade and install if not exists
helm upgrade --install myapp k8s/devops-info-service \
  -f k8s/devops-info-service/values-prod.yaml
```

### Rollback

```bash
# View release history
helm history myapp

# Rollback to previous release
helm rollback myapp

# Rollback to specific revision
helm rollback myapp 2
```

### Uninstall

```bash
# Uninstall release
helm uninstall myapp

# Uninstall from specific namespace
helm uninstall myapp --namespace production
```

---

## Testing & Validation

### helm lint output

```bash
helm lint k8s/devops-info-service
# ==> Linting k8s/devops-info-service
# [INFO] Chart.yaml: icon is recommended
#
# 1 chart(s) linted, 0 chart(s) failed
```

### helm template verification

```bash
helm template myapp k8s/devops-info-service
# ---
# # Source: devops-info-service/templates/service.yaml
# apiVersion: v1
# kind: Service
# metadata:
#   name: myapp-devops-info-service
#   labels:
#     helm.sh/chart: devops-info-service-0.1.0
#     app.kubernetes.io/name: devops-info-service
#     app.kubernetes.io/instance: myapp
#     ...
```

### Dry-run output

```bash
helm install --dry-run --debug test-release k8s/devops-info-service
# install.go:222: [debug] Original chart version: ""
# NAME: test-release
# LAST DEPLOYED: ...
# NAMESPACE: default
# STATUS: pending-install
# REVISION: 1
# TEST SUITE: None
# HOOKS:
# ---
# # Source: devops-info-service/templates/hooks/pre-install-job.yaml
# apiVersion: batch/v1
# kind: Job
# ...
# MANIFEST:
# ---
# # Source: devops-info-service/templates/service.yaml
# ...
```

### Application accessibility verification

```bash
# Get NodePort
kubectl get svc myapp-devops-info-service -o jsonpath='{.spec.ports[0].nodePort}'

# Test health endpoint
curl http://$(minikube ip):30080/health
# {"status": "healthy"}

# Test application endpoint
curl http://$(minikube ip):30080/
```

---

## Bonus: Library Charts

### Library Chart Structure

```
k8s/common-lib/
├── Chart.yaml          # type: library
└── templates/
    └── _helpers.tpl    # Shared template definitions
```

### Shared Templates

The `common-lib` library provides:
- `common.name` — chart name with override support
- `common.fullname` — `<release>-<chart>` with override support
- `common.chart` — `<chart>-<version>` label value
- `common.labels` — full set of standard Kubernetes labels
- `common.selectorLabels` — labels used for pod selection

### How Both Apps Use the Library

**devops-info-service** uses its own `_helpers.tpl` (with `devops-info-service.*` prefix) for backward compatibility.

**devops-info-service-v2** uses `common-lib` templates directly (`common.*` prefix):

```yaml
# devops-info-service-v2/templates/deployment.yaml
metadata:
  name: {{ include "common.fullname" . }}
  labels:
    {{- include "common.labels" . | nindent 4 }}
```

### Dependencies Configuration

Both charts declare the library as a dependency in `Chart.yaml`:

```yaml
dependencies:
  - name: common-lib
    version: 0.1.0
    repository: "file://../common-lib"
```

Install both apps:

```bash
# Update dependencies for both charts
helm dependency update k8s/devops-info-service
helm dependency update k8s/devops-info-service-v2

# Deploy both apps
helm install app1 k8s/devops-info-service
helm install app2 k8s/devops-info-service-v2

# Verify both running
helm list
kubectl get deployments
```

### Benefits of Library Charts

1. **DRY (Don't Repeat Yourself)**: Label and naming logic defined once, used everywhere
2. **Consistency**: All apps use identical label structure, avoiding drift
3. **Maintainability**: Fix a naming bug in one place, all charts benefit on next `helm dependency update`
4. **Standardization**: Enforces team conventions for Kubernetes resource naming
