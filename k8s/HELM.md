# Lab 10: Helm Package Manager

## 1. Chart Overview

```
k8s/pythonapp/
├── Chart.yaml                 # Chart metadata (name, version, appVersion)
├── values.yaml                # Default values (3 replicas, NodePort)
├── values-dev.yaml            # Dev overrides (1 replica, minimal resources)
├── values-prod.yaml           # Prod overrides (5 replicas, LoadBalancer)
└── templates/
    ├── _helpers.tpl            # Helper templates (names, labels, selectors)
    ├── deployment.yaml         # Templatized Deployment
    ├── service.yaml            # Templatized Service
    ├── NOTES.txt               # Post-install instructions
    └── hooks/
        ├── pre-install-job.yaml   # Validation before install
        └── post-install-job.yaml  # Smoke test after install
```

**Templates**:
- `_helpers.tpl` — defines `pythonapp.name`, `pythonapp.fullname`, `pythonapp.chart`, `pythonapp.labels`, `pythonapp.selectorLabels`
- `deployment.yaml` — reads replicas, image, resources, probes, env from values
- `service.yaml` — configurable type (NodePort/LoadBalancer), port, nodePort

**Values strategy**: Nested structure by resource type. All values have sensible defaults; env-specific overrides in separate files.

## 2. Configuration Guide

| Value | Default | Dev | Prod |
|-------|---------|-----|------|
| `replicaCount` | 3 | 1 | 5 |
| `image.tag` | latest | latest | 1.0.0 |
| `service.type` | NodePort | NodePort | LoadBalancer |
| `resources.limits.cpu` | 200m | 100m | 500m |
| `resources.limits.memory` | 256Mi | 128Mi | 512Mi |
| `resources.requests.cpu` | 100m | 50m | 200m |
| `resources.requests.memory` | 128Mi | 64Mi | 256Mi |
| `livenessProbe.initialDelaySeconds` | 10 | 5 | 30 |

### Installation Examples

```bash
# Dev environment (1 replica, NodePort, minimal resources)
helm install pythonapp-dev k8s/pythonapp -f k8s/pythonapp/values-dev.yaml

# Prod environment (5 replicas, LoadBalancer, higher resources)
helm install pythonapp-prod k8s/pythonapp -f k8s/pythonapp/values-prod.yaml

# Override specific value
helm install pythonapp k8s/pythonapp --set replicaCount=7

# Upgrade from dev to prod
helm upgrade pythonapp-dev k8s/pythonapp -f k8s/pythonapp/values-prod.yaml
```

## 3. Hook Implementation

| Hook | Type | Weight | Deletion Policy | Purpose |
|------|------|--------|----------------|---------|
| `pre-install-job.yaml` | `pre-install` | -5 | `hook-succeeded` | Validates environment readiness before deploying |
| `post-install-job.yaml` | `post-install` | 5 | `hook-succeeded` | Runs smoke test after deployment completes |

- **Weight -5** ensures pre-install runs first (lower weight = earlier execution).
- **Weight 5** ensures post-install runs after all resources are created.
- **`hook-succeeded`** automatically deletes hook jobs after successful completion. Verified by `kubectl get jobs` returning "No resources found" after install.
- Hooks use the application image instead of busybox to guarantee image availability.

## 4. Installation Evidence

### Helm Version
```
$ helm version --short
v4.1.3+gc94d381
```

### Helm Lint
```
$ helm lint k8s/pythonapp
==> Linting k8s/pythonapp
[INFO] Chart.yaml: icon is recommended

1 chart(s) linted, 0 chart(s) failed
```

### DEV Install → PROD Upgrade
```
$ helm install pythonapp-dev k8s/pythonapp -f k8s/pythonapp/values-dev.yaml --wait
NAME: pythonapp-dev
STATUS: deployed
REVISION: 1

$ helm upgrade pythonapp-dev k8s/pythonapp -f k8s/pythonapp/values-prod.yaml --wait
Release "pythonapp-dev" has been upgraded. Happy Helming!
STATUS: deployed
REVISION: 2
DESCRIPTION: Upgrade complete
```

### Current State (after PROD upgrade)
```
$ helm list
NAME          NAMESPACE  REVISION  STATUS    CHART            APP VERSION
pythonapp-dev default    2         deployed  pythonapp-0.1.0  1.0.0

$ kubectl get pods
NAME                                       READY   STATUS    RESTARTS   AGE
pythonapp-dev-pythonapp-75465fb9f-5xj7r    1/1     Running   0          24m
pythonapp-dev-pythonapp-75465fb9f-f9g8z    1/1     Running   0          24m
pythonapp-dev-pythonapp-75465fb9f-kf77w    1/1     Running   0          24m
pythonapp-dev-pythonapp-75465fb9f-m72wv    1/1     Running   0          24m
pythonapp-dev-pythonapp-75465fb9f-qwnj9    1/1     Running   0          24m

$ kubectl get svc
NAME                      TYPE           CLUSTER-IP      EXTERNAL-IP   PORT(S)        AGE
pythonapp-dev-pythonapp   LoadBalancer   10.103.84.248   <pending>     80:31757/TCP   24m

$ kubectl get jobs
No resources found in default namespace.
# ^ hooks were deleted per hook-succeeded policy

$ helm history pythonapp-dev
REVISION  STATUS      CHART            APP VERSION  DESCRIPTION
1         superseded  pythonapp-0.1.0  1.0.0        Install complete
2         deployed    pythonapp-0.1.0  1.0.0        Upgrade complete
```

## 5. Operations

```bash
# Install
helm install <release> k8s/pythonapp -f k8s/pythonapp/<values-file>.yaml

# Upgrade
helm upgrade <release> k8s/pythonapp -f k8s/pythonapp/<values-file>.yaml

# Rollback to previous revision
helm rollback <release> <revision>

# Uninstall
helm uninstall <release>

# Dry-run (preview without applying)
helm install --dry-run --debug test k8s/pythonapp
```

## 6. Testing & Validation

```
$ helm lint k8s/pythonapp
==> Linting k8s/pythonapp
1 chart(s) linted, 0 chart(s) failed

$ helm template test k8s/pythonapp
# Renders: Service, Deployment (3 replicas, probes, resources), pre-install Job, post-install Job
# All templates render without errors
# Labels include: helm.sh/chart, app.kubernetes.io/name, instance, version, managed-by
```
