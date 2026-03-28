# Lab 10 - Helm Package Manager

## 1. Chart Overview

This lab converts static Kubernetes manifests from Lab 9 into reusable Helm charts with environment-specific configuration, lifecycle hooks, and shared templates via a library chart.

### Implemented chart structure

```text
k8s/
├── common-lib/
│   ├── Chart.yaml
│   ├── values.yaml
│   └── templates/
│       └── _helpers.tpl
├── devops-python/
│   ├── Chart.yaml
│   ├── Chart.lock
│   ├── values.yaml
│   ├── values-dev.yaml
│   ├── values-prod.yaml
│   ├── charts/common-lib-0.1.0.tgz
│   └── templates/
│       ├── _helpers.tpl
│       ├── deployment.yaml
│       ├── service.yaml
│       ├── serviceaccount.yaml
│       └── hooks/
│           ├── pre-install-job.yaml
│           └── post-install-job.yaml
└── devops-python-v2/
    ├── Chart.yaml
    ├── Chart.lock
    ├── values.yaml
    ├── charts/common-lib-0.1.0.tgz
    └── templates/
        ├── _helpers.tpl
        ├── deployment.yaml
        ├── service.yaml
        └── serviceaccount.yaml
```

### Key template files and purpose

- `templates/deployment.yaml`: templated replica count, image, resources, probes, and env vars.
- `templates/service.yaml`: templated service type/ports including optional NodePort.
- `templates/serviceaccount.yaml`: optional ServiceAccount with configurable token automount.
- `templates/hooks/pre-install-job.yaml`: validation task before install.
- `templates/hooks/post-install-job.yaml`: smoke check after install.
- `templates/_helpers.tpl`: names/labels/selector labels delegated to shared library helpers.

### Values organization strategy

- `values.yaml`: default baseline values.
- `values-dev.yaml`: dev profile (lighter resources, NodePort, 1 replica).
- `values-prod.yaml`: prod profile (more replicas/resources, LoadBalancer-ready service).

---

## 2. Configuration Guide

### Important values

- `replicaCount`: desired number of pods.
- `image.repository`, `image.tag`, `image.pullPolicy`: container image settings.
- `service.type`, `service.port`, `service.targetPort`, `service.nodePort`: service behavior.
- `resources.requests/limits`: CPU and memory sizing.
- `livenessProbe`, `readinessProbe`: health checks (kept active and configurable).
- `hooks.*`: hook enable flag, image, and commands.

### Environment customization

Development (`values-dev.yaml`):
- `replicaCount: 1`
- lower requests/limits
- `service.type: NodePort`

Production (`values-prod.yaml`):
- `replicaCount: 3`
- higher requests/limits
- `service.type: LoadBalancer`

### Example installs

```bash
helm install dev-release k8s/devops-python -f k8s/devops-python/values-dev.yaml
helm upgrade dev-release k8s/devops-python -f k8s/devops-python/values-prod.yaml
```

---

## 3. Hook Implementation

### Implemented hooks

- `pre-install` hook job:
  - Runs before main resources.
  - Purpose: simple pre-install validation message.
  - Weight: `-5`.
- `post-install` hook job:
  - Runs after resources are installed.
  - Purpose: smoke test (`/health`) against service endpoint.
  - Weight: `5`.

### Hook deletion policy

Both jobs use:

- `hook-succeeded`
- `before-hook-creation`

This keeps cluster clean and ensures old hook jobs are removed before re-running.

---

## 4. Installation Evidence

### Helm installation/version

```bash
$ helm version --short
v4.0.0+g99cd196
```

### Public chart exploration

```bash
$ helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
"prometheus-community" has been added to your repositories

$ helm search repo prometheus-community/prometheus | head -n 5
NAME                                        CHART VERSION   APP VERSION   DESCRIPTION
prometheus-community/prometheus             28.14.1         v3.10.0       Prometheus is a monitoring system...
...

$ helm show chart prometheus-community/prometheus
apiVersion: v2
appVersion: v3.10.0
description: Prometheus is a monitoring system and time series database.
...
```

### Lint and rendering

```bash
$ helm lint k8s/devops-python
1 chart(s) linted, 0 chart(s) failed

$ helm lint k8s/devops-python-v2
1 chart(s) linted, 0 chart(s) failed

$ helm template dev-release k8s/devops-python -f k8s/devops-python/values-dev.yaml --kube-version 1.32.2
# rendered manifests produced successfully
```

### Dev install + runtime resources

```bash
$ helm install dev-release k8s/devops-python -f k8s/devops-python/values-dev.yaml --wait
STATUS: deployed
REVISION: 1

$ kubectl get all -n default
pod/dev-release-devops-python-...            1/1 Running
service/dev-release-devops-python            NodePort 80:30080/TCP
deployment.apps/dev-release-devops-python    1/1
```

### Upgrade to prod profile

```bash
$ helm upgrade dev-release k8s/devops-python -f k8s/devops-python/values-prod.yaml --wait
Release "dev-release" has been upgraded. Happy Helming!
REVISION: 3
STATUS: deployed
```

### Rollback

```bash
$ helm rollback dev-release 1 --wait
Rollback was a success! Happy Helming!
```

### Bonus second chart deployment

```bash
$ helm install v2-release k8s/devops-python-v2 --wait
STATUS: deployed
REVISION: 1

$ helm list -A
dev-release  ... deployed devops-python-0.1.0
v2-release   ... deployed devops-python-v2-0.1.0

$ kubectl get all -n default
pod/dev-release-devops-python-...           Running
pod/v2-release-devops-python-v2-...         Running
service/dev-release-devops-python           NodePort 80:30080/TCP
service/v2-release-devops-python-v2         NodePort 80:30081/TCP
```

### Hook execution evidence

Post-install hook execution appeared in cluster events/logging during release lifecycle:

```bash
Normal  SuccessfulCreate  job/dev-release-devops-python-post-install  Created pod
Normal  Completed         job/dev-release-devops-python-post-install  Job completed
```

Hook cleanup check:

```bash
$ kubectl get jobs -n default
No resources found in default namespace.
```

### Uninstall

```bash
$ helm uninstall v2-release
$ helm uninstall dev-release

$ helm list -A
NAME    NAMESPACE   REVISION   UPDATED   STATUS   CHART   APP VERSION

$ kubectl get jobs -n default
No resources found in default namespace.
```

---

## 5. Operations

### Commands used

```bash
# Dependencies
helm dependency update k8s/devops-python
helm dependency update k8s/devops-python-v2

# Validation
helm lint k8s/devops-python
helm lint k8s/devops-python-v2
helm template dev-release k8s/devops-python -f k8s/devops-python/values-dev.yaml --kube-version 1.32.2
helm install --dry-run --debug test-release k8s/devops-python -f k8s/devops-python/values-dev.yaml

# Deploy and lifecycle
helm install dev-release k8s/devops-python -f k8s/devops-python/values-dev.yaml --wait
helm upgrade dev-release k8s/devops-python -f k8s/devops-python/values-prod.yaml --wait
helm rollback dev-release 1 --wait
helm uninstall dev-release

# Bonus chart
helm install v2-release k8s/devops-python-v2 --wait
helm uninstall v2-release
```

---

## 6. Testing and Validation

Validation completed with:

- Helm 4 installation verification.
- Public repository usage and chart introspection.
- `helm lint` success for both application charts.
- Template rendering verification.
- Real install/upgrade/rollback/uninstall cycle on local `kind` cluster.
- Health probes enabled and active in both charts.
- Hook creation/execution observed and cleanup confirmed.

---

## 7. Bonus - Library Charts

### Library chart

`k8s/common-lib` is a true library chart:

- `type: library` in `Chart.yaml`.
- Shared templates in `templates/_helpers.tpl`:
  - `common-lib.name`
  - `common-lib.fullname`
  - `common-lib.chart`
  - `common-lib.selectorLabels`
  - `common-lib.labels`

### How both apps use the library

Both `devops-python` and `devops-python-v2`:

- declare dependency:

```yaml
dependencies:
  - name: common-lib
    version: 0.1.0
    repository: "file://../common-lib"
```

- reuse shared helper logic from their local `_helpers.tpl` wrappers:
  - include `common-lib.name`
  - include `common-lib.fullname`
  - include `common-lib.labels`
  - include `common-lib.selectorLabels`

### Benefits

- DRY templates (reduced duplication).
- Consistent labels and naming across charts.
- Easier maintenance and extension for future charts.
