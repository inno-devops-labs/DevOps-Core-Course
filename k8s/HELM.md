# Helm Implementation Guide

## 1. Chart Overview

This lab converts static Kubernetes manifests into Helm charts and adds shared templates through a library chart.

### Implemented chart structure

```text
k8s/
├── common-lib/
│   ├── Chart.yaml
│   └── templates/
│       └── _helpers.tpl
├── devops-info/
│   ├── Chart.yaml
│   ├── values.yaml
│   ├── values-dev.yaml
│   ├── values-prod.yaml
│   ├── charts/
│   │   └── common-lib-0.1.0.tgz
│   └── templates/
│       ├── _helpers.tpl
│       ├── deployment.yaml
│       ├── service.yaml
│       └── hooks/
│           ├── pre-install-job.yaml
│           └── post-install-job.yaml
└── hello-app/
    ├── Chart.yaml
    ├── values.yaml
    ├── charts/
    │   └── common-lib-0.1.0.tgz
    └── templates/
        ├── _helpers.tpl
        ├── deployment.yaml
        └── service.yaml
```

### Key templates and purpose

- `common-lib/templates/_helpers.tpl`: shared naming/labels helpers (`common.name`, `common.fullname`, `common.labels`, `common.selectorLabels`).
- `devops-info/templates/deployment.yaml`: main API Deployment with env vars, resources, and liveness/readiness/startup probes.
- `devops-info/templates/service.yaml`: configurable Service (`NodePort` or `LoadBalancer`).
- `devops-info/templates/hooks/*.yaml`: lifecycle hook Jobs for pre-install and post-install.
- `hello-app/templates/*`: second app chart (bonus) using shared helpers from library chart.

### Values organization strategy

- Base defaults in `values.yaml`.
- Environment overrides in `values-dev.yaml` and `values-prod.yaml`.
- Nested keys for readability: `image`, `service`, `resources`, `probes`, `hooks`.

## 2. Configuration Guide

### Important values

- `replicaCount`: number of pod replicas.
- `image.repository`, `image.tag`, `image.pullPolicy`: container image source/version.
- `service.type`, `service.port`, `service.targetPort`, `service.nodePort`: service exposure.
- `resources.requests`, `resources.limits`: CPU/memory reservations and caps.
- `probes.liveness`, `probes.readiness`, `probes.startup`: health checks.
- `hooks.*`: hook toggles, hook image, weight, and hook command.

### Environment customization

- Development profile (`values-dev.yaml`):
  - `replicaCount: 1`
  - lighter resource requests/limits
  - `service.type: NodePort`
  - faster probe startup values
- Production profile (`values-prod.yaml`):
  - `replicaCount: 5`
  - stronger resource requests/limits
  - `service.type: LoadBalancer`
  - slower, safer probe startup values

### Example installations

```bash
# Base install
.tools/helm install devops-info k8s/devops-info

# Development
.tools/helm install devops-info-dev k8s/devops-info -f k8s/devops-info/values-dev.yaml

# Production
.tools/helm install devops-info-prod k8s/devops-info -f k8s/devops-info/values-prod.yaml

# Upgrade dev -> prod
.tools/helm upgrade devops-info-dev k8s/devops-info -f k8s/devops-info/values-prod.yaml
```

## 3. Hook Implementation

### Implemented hooks and reason

- `pre-install` hook (`weight: -5`): lightweight pre-deployment validation placeholder.
- `post-install` hook (`weight: 5`): lightweight smoke-check placeholder.

### Execution order

- Lower weight runs earlier.
- Pre-install hook runs before main resources.
- Post-install hook runs after resources are rendered/applied.

### Deletion policy

Both hooks use:

- `helm.sh/hook-delete-policy: hook-succeeded`

This automatically deletes successful hook Jobs and keeps namespace cleaner.

## 4. Installation Evidence

### Helm fundamentals evidence

```bash
$ .tools/helm version
version.BuildInfo{Version:"v4.0.0", GitCommit:"99cd1964357c793351be481d55abbe21c6b2f4ec", ...}
```

```bash
$ .tools/helm repo list
NAME                    URL
prometheus-community    https://prometheus-community.github.io/helm-charts
```

```bash
$ .tools/helm search repo prometheus-community/prometheus
NAME                                    CHART VERSION   APP VERSION   DESCRIPTION
prometheus-community/prometheus         28.14.1         v3.10.0       Prometheus is a monitoring system...
```

```bash
$ .tools/helm show chart prometheus-community/prometheus
apiVersion: v2
name: prometheus
version: 28.14.1
type: application
...
```

### Environment rendering evidence

```bash
$ .tools/helm template devops-info-dev k8s/devops-info -f k8s/devops-info/values-dev.yaml
# replicas: 1
# image: graymansion/devops-info-service:latest
# service.type: NodePort
```

```bash
$ .tools/helm template devops-info-prod k8s/devops-info -f k8s/devops-info/values-prod.yaml
# replicas: 5
# image: graymansion/devops-info-service:lab02
# service.type: LoadBalancer
```

### Hook rendering evidence

```bash
$ .tools/helm install --dry-run --debug test-devops k8s/devops-info -f k8s/devops-info/values-dev.yaml
HOOKS:
  ... "helm.sh/hook": pre-install
  ... "helm.sh/hook-weight": "-5"
  ... "helm.sh/hook-delete-policy": hook-succeeded
  ... "helm.sh/hook": post-install
  ... "helm.sh/hook-weight": "5"
```

### Cluster-dependent evidence status

Live runtime outputs (`helm list`, `kubectl get all`, `kubectl get jobs`, `kubectl describe job`) require an accessible Kubernetes cluster and installed `kubectl` binary.

Current environment limitations:

- `kubectl` is not installed (`command not found`).
- `helm list` reports cluster unreachable (`127.0.0.1:8080 connection refused`).

## 5. Operations

### Commands used

```bash
# Dependencies
.tools/helm dependency update k8s/devops-info
.tools/helm dependency update k8s/hello-app

# Validation
.tools/helm lint k8s/common-lib
.tools/helm lint k8s/devops-info
.tools/helm lint k8s/hello-app
.tools/helm template devops-info k8s/devops-info
.tools/helm install --dry-run --debug test-devops k8s/devops-info -f k8s/devops-info/values-dev.yaml
```

### Upgrade

```bash
.tools/helm upgrade devops-info-dev k8s/devops-info -f k8s/devops-info/values-prod.yaml
```

### Rollback

```bash
.tools/helm rollback devops-info-dev 1
```

### Uninstall

```bash
.tools/helm uninstall devops-info-dev
.tools/helm uninstall devops-info-prod
.tools/helm uninstall hello-app
```

## 6. Testing and Validation

### Lint

```bash
$ .tools/helm lint k8s/common-lib
1 chart(s) linted, 0 chart(s) failed

$ .tools/helm lint k8s/devops-info
1 chart(s) linted, 0 chart(s) failed

$ .tools/helm lint k8s/hello-app
1 chart(s) linted, 0 chart(s) failed
```

### Template verification

`helm template` confirms:

- Service and Deployment render correctly.
- Probes are present and not commented out.
- Hook resources render with expected annotations.
- Values overrides are applied by environment.

### Dry-run verification

`helm install --dry-run --debug` confirms:

- Chart installation flow is valid.
- Hook blocks are rendered in `HOOKS:` section.
- Final computed values include dev/prod overrides.

### Accessibility verification

In this environment, only static/render validation was possible. Runtime accessibility checks (`kubectl port-forward`, service endpoint tests, ingress tests) require a reachable Kubernetes cluster.
