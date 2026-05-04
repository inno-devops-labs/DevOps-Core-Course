# Lab 10 — Helm Package Manager

## Chart Overview

```
k8s/helm/
├── common-lib/              # Library chart — shared templates
│   ├── Chart.yaml           # type: library
│   └── templates/
│       └── _helpers.tpl     # common.labels, common.selectorLabels, common.fullname
├── devops-info/             # Primary application chart
│   ├── Chart.yaml
│   ├── values.yaml          # Default values
│   ├── values-dev.yaml      # Dev environment overrides
│   ├── values-prod.yaml     # Prod environment overrides
│   └── templates/
│       ├── _helpers.tpl     # Chart-specific helpers
│       ├── deployment.yaml  # Deployment with RollingUpdate + probes + resources
│       ├── service.yaml     # NodePort / LoadBalancer service
│       ├── NOTES.txt        # Post-install instructions
│       └── hooks/
│           ├── pre-install-job.yaml   # Validation before install/upgrade
│           └── post-install-job.yaml  # Smoke test after install/upgrade
└── devops-info-v2/          # Second app chart that uses common-lib
    ├── Chart.yaml           # depends on common-lib via file://
    ├── values.yaml
    └── templates/
        ├── deployment.yaml  # uses common.fullname / common.labels
        └── service.yaml
```

### Key template files

| File | Purpose |
|------|---------|
| `_helpers.tpl` | Name generation, label blocks — used everywhere to stay DRY |
| `deployment.yaml` | Templatised Deployment with `.Values.replicaCount`, image, resources, probes, env |
| `service.yaml` | NodePort or LoadBalancer with optional `nodePort` field |
| `hooks/pre-install-job.yaml` | Runs busybox validation before install/upgrade |
| `hooks/post-install-job.yaml` | Runs smoke-test message after install/upgrade |

### Values organisation

Values are grouped by concern: `image`, `service`, `resources`, `livenessProbe`,
`readinessProbe`, `rollingUpdate`. Environment-specific files only override what
changes — the base `values.yaml` contains safe defaults.

## Configuration Guide

### Important values

| Value | Default | Description |
|-------|---------|-------------|
| `replicaCount` | `3` | Number of Pod replicas |
| `image.repository` | `merkulovlr05/devops-info` | Docker image |
| `image.tag` | `latest` | Image tag |
| `service.type` | `NodePort` | Service type |
| `service.nodePort` | `30080` | NodePort port (NodePort only) |
| `rollingUpdate.maxSurge` | `1` | Extra Pods during update |
| `rollingUpdate.maxUnavailable` | `0` | Zero downtime guarantee |

### Example installations

```bash
# Default (3 replicas, NodePort)
helm install devops-info k8s/helm/devops-info

# Development (1 replica, relaxed probes)
helm install devops-info-dev k8s/helm/devops-info -f k8s/helm/devops-info/values-dev.yaml

# Production (5 replicas, LoadBalancer, tight resources)
helm install devops-info-prod k8s/helm/devops-info -f k8s/helm/devops-info/values-prod.yaml

# One-off override
helm install devops-info k8s/helm/devops-info --set replicaCount=10
```

### Environment differences

| Setting | dev | prod |
|---------|-----|------|
| `replicaCount` | 1 | 5 |
| `image.tag` | `latest` | `v1` |
| `service.type` | NodePort | LoadBalancer |
| `resources.limits.cpu` | 100m | 500m |
| `livenessProbe.initialDelaySeconds` | 5 | 30 |

## Hook Implementation

### Hooks

| Hook | Type | Weight | Delete policy | Purpose |
|------|------|--------|---------------|---------|
| `pre-install-job` | `pre-install, pre-upgrade` | `-5` | `hook-succeeded` | Validates chart/env before deploy |
| `post-install-job` | `post-install, post-upgrade` | `5` | `hook-succeeded` | Smoke test message after deploy |

**Execution order:** pre-install (weight -5) → Deployment + Service → post-install (weight 5).

**Deletion policy `hook-succeeded`** means the Job Pod is cleaned up automatically
on success, so `kubectl get jobs` will be empty after a healthy deploy. To inspect
hook output on a live cluster use `--timeout` in the Job spec or temporarily change
the policy to `hook-failed`.

Real-world extensions:
- pre-install: run `alembic upgrade head` for a database migration
- post-install: curl the `/health` endpoint and fail the release if it returns non-2xx

## Installation Evidence

See raw outputs in [`helm/evidence/`](./helm/evidence):

- `00-helm-version.txt` — `helm version`, repo setup, `helm show chart prometheus-community/prometheus`
- `01-lint-template.txt` — `helm lint` (0 failures) + `helm template` output
- `02-dev-install.txt` — dev release: 1 replica, NodePort, `helm list`, `kubectl get all`
- `03-prod-upgrade.txt` — upgrade to prod: 5 replicas, LoadBalancer
- `04-hooks-rollback.txt` — rollback to rev 1, `helm history`, dry-run hook manifests
- `05-library-bonus.txt` — v2 chart with library dependency, both releases running

## Operations

```bash
# Install
helm install <release> k8s/helm/devops-info [-f values-dev.yaml]

# Upgrade
helm upgrade <release> k8s/helm/devops-info [-f values-prod.yaml]

# Rollback
helm rollback <release> [revision]

# History
helm history <release>

# Uninstall
helm uninstall <release>

# Debug / dry-run
helm install --dry-run --debug test k8s/helm/devops-info
```

## Testing & Validation

```bash
# Lint
helm lint k8s/helm/devops-info
# → 1 chart(s) linted, 0 chart(s) failed

# Render templates locally
helm template devops-info k8s/helm/devops-info

# Dry-run with debug
helm install --dry-run --debug test k8s/helm/devops-info

# Verify app responds
kubectl port-forward svc/devops-info-dev 8080:80 &
curl http://localhost:8080/health
```

## Bonus — Library Charts

The `common-lib` library chart (`type: library`) extracts the shared label and
name helpers into reusable named templates (`common.labels`,
`common.selectorLabels`, `common.fullname`).

`devops-info-v2` declares it as a local dependency:

```yaml
# devops-info-v2/Chart.yaml
dependencies:
  - name: common-lib
    version: 0.1.0
    repository: "file://../common-lib"
```

After `helm dependency update k8s/helm/devops-info-v2`, Helm bundles the library
into the chart's `charts/` directory and its templates become callable inside
`devops-info-v2/templates/`.

**Benefits:**
- **DRY** — label logic lives in one place; both app charts reference it
- **Consistency** — labels are always formatted the same way
- **Maintainability** — change naming convention once, both apps update
- **Testability** — library templates can be unit-tested independently
