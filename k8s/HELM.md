# HELM — Lab 10 Documentation

## 1) Chart Overview

### Chart location
- `k8s/devops-app`

### Structure
- `Chart.yaml` — chart metadata (name, version, appVersion).
- `values.yaml` — default app configuration.
- `values-dev.yaml` — development overrides.
- `values-prod.yaml` — production overrides.
- `templates/deployment.yaml` — templated Deployment.
- `templates/service.yaml` — templated Service.
- `templates/_helpers.tpl` — shared naming/labels helpers.
- `templates/hooks/pre-install-job.yaml` — pre-install hook job.
- `templates/hooks/post-install-job.yaml` — post-install hook job.

### Values organization strategy
Values are grouped by concern:
- `image` (repository/tag/pull policy)
- `service` (type/ports/nodePort)
- `resources` (requests/limits)
- `livenessProbe` and `readinessProbe`
- `replicaCount`, `env`, and security contexts

---

## 2) Configuration Guide

### Important values
- `replicaCount`: number of pods.
- `image.repository`, `image.tag`: container source/version.
- `service.type`: `NodePort` (dev) or `LoadBalancer` (prod).
- `resources.requests` / `resources.limits`: CPU and memory guarantees/limits.
- `livenessProbe` / `readinessProbe`: health-check behavior.

### Environment customization
- Dev (`values-dev.yaml`):
  - 1 replica
  - relaxed resources
  - NodePort service
  - `image.tag=latest`
- Prod (`values-prod.yaml`):
  - 3 replicas
  - higher resources
  - LoadBalancer-ready service
  - fixed image tag (`1.0.0`)

### Example installs
```bash
# default
helm install myrelease k8s/devops-app

# development
helm upgrade --install devops-env k8s/devops-app -f k8s/devops-app/values-dev.yaml

# production
helm upgrade devops-env k8s/devops-app -f k8s/devops-app/values-prod.yaml
```

---

## 3) Hook Implementation

### Implemented hooks and purpose
- **Pre-install hook** (`pre-install-job.yaml`): lightweight validation before main resources are installed.
- **Post-install hook** (`post-install-job.yaml`): smoke-check after install.

### Execution order and weights
- Pre-install job: `helm.sh/hook-weight: "-5"`
- Post-install job: `helm.sh/hook-weight: "5"`

Lower weight runs first, so pre-install executes before post-install.

### Deletion policy
Both jobs use:
- `helm.sh/hook-delete-policy: hook-succeeded`

This removes hook jobs after successful completion.

---

## 4) Installation Evidence

### `helm list`
```text
NAME        NAMESPACE  REVISION  STATUS    CHART            APP VERSION
devops-env  default    3         deployed  devops-app-0.1.0 1.0.0
hook-run    default    1         deployed  devops-app-0.1.0 1.0.0
myrelease   default    1         deployed  devops-app-0.1.0 1.0.0
```

### `kubectl get all`
```text
# Main resources are present:
- deployments: devops-env-devops-app, hook-run-devops-app, myrelease-devops-app
- services:    devops-env-devops-app, hook-run-devops-app, myrelease-devops-app
- pods:        running for each release
```

### Hook execution evidence
```text
kubectl get jobs -n default
No resources found in default namespace.
```

```text
kubectl describe job hook-run-devops-app-pre-install -n default
Error from server (NotFound): jobs.batch "hook-run-devops-app-pre-install" not found
```

(Reason: jobs were deleted by `hook-succeeded` policy.)

Hook lifecycle was confirmed from events:
- pre-install job created and completed
- post-install job created and completed

### Dev vs Prod deployments
```text
# Current prod values on devops-env
helm get values devops-env
replicaCount: 3
service.type: LoadBalancer
image.tag: 1.0.0
resources: higher limits/requests
```

Release history confirms environment upgrade path:
```text
helm history devops-env
REVISION 2: Upgrade complete (dev profile)
REVISION 3: Upgrade complete (prod profile)
```

---

## 5) Operations

### Installation
```bash
helm install myrelease k8s/devops-app
```

### Upgrade
```bash
helm upgrade myrelease k8s/devops-app -f k8s/devops-app/values-prod.yaml
```

### Rollback
```bash
helm history myrelease
helm rollback myrelease <REVISION>
```

### Uninstall
```bash
helm uninstall myrelease
```

---

## 6) Testing & Validation

### Lint
```text
helm lint k8s/devops-app
1 chart(s) linted, 0 chart(s) failed
```

### Template rendering
```text
helm template mychart k8s/devops-app
# renders Service, Deployment, and hook manifests
```

### Dry-run
```text
helm install --dry-run=client --debug test-release k8s/devops-app
STATUS: pending-install
HOOKS:
MANIFEST:
```

### Application accessibility verification
Verified from inside cluster with temporary busybox pod:
```text
kubectl run wget-check --rm -i --restart=Never --image=busybox:1.36 --command -- wget -qO- http://devops-env-devops-app/health
{"status":"healthy", ...}
```

---

## Notes
- Fixed NodePort can conflict if already allocated. In that case, use another port override:
```bash
helm install myrelease k8s/devops-app --set service.nodePort=30081
```
