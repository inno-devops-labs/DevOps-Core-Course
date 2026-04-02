## Chart Overview

### Structure

```
k8s/
├── devops-info-service/        # Main application chart
│   ├── Chart.yaml              # Chart metadata and dependencies
│   ├── values.yaml             # Default configuration values
│   ├── values-dev.yaml         # Development environment overrides
│   ├── values-prod.yaml        # Production environment overrides
│   ├── charts/                 # Packaged dependencies (common-lib)
│   └── templates/
│       ├── _helpers.tpl        # Named template helpers (labels, fullname)
│       ├── deployment.yaml     # Deployment manifest template
│       ├── service.yaml        # Service manifest template
│       ├── NOTES.txt           # Post-install instructions
│       └── hooks/
│           ├── pre-install-job.yaml   # Pre-install Job hook
│           └── post-install-job.yaml  # Post-install Job hook
├── echo-service/               # Second application (bonus - uses common-lib)
│   ├── Chart.yaml
│   ├── values.yaml
│   ├── charts/                 # Packaged common-lib dependency
│   └── templates/
│       ├── deployment.yaml
│       └── service.yaml
└── common-lib/                 # Library chart (bonus)
    ├── Chart.yaml              # type: library
    └── templates/
        └── _helpers.tpl        # Shared named templates
```

### Key Template Files

| File                                    | Purpose                                                                                |
|-----------------------------------------|----------------------------------------------------------------------------------------|
| `templates/_helpers.tpl`                | Defines named templates: `fullname`, `labels`, `selectorLabels`, `chart`               |
| `templates/deployment.yaml`             | Deployment with configurable replicas, image, resources, probes, and security contexts |
| `templates/service.yaml`                | Service with conditional `nodePort` rendering based on service type                    |
| `templates/hooks/pre-install-job.yaml`  | Job that runs before installation to validate prerequisites                            |
| `templates/hooks/post-install-job.yaml` | Job that runs after installation as a smoke test                                       |

### Values Organization

Values are structured into logical groups:
- `image` - repository, tag, pull policy
- `service` - type, ports, nodePort
- `resources` - CPU/memory requests and limits
- `livenessProbe` / `readinessProbe` - health check configuration
- `securityContext` / `containerSecurityContext` - pod and container security
- `strategy` - rolling update parameters
- `env` - application environment variables

---

## Configuration Guide

### Important Values

| Key                                  | Default          | Description                         |
|--------------------------------------|------------------|-------------------------------------|
| `replicaCount`                       | `3`              | Number of pod replicas              |
| `image.repository`                   | `andiazdi/lab02` | Container image repository          |
| `image.tag`                          | `1.0.0`          | Container image tag                 |
| `image.pullPolicy`                   | `IfNotPresent`   | Image pull policy                   |
| `service.type`                       | `NodePort`       | Kubernetes Service type             |
| `service.port`                       | `80`             | Service port                        |
| `service.nodePort`                   | `30080`          | NodePort external port              |
| `resources.requests.cpu`             | `100m`           | CPU request                         |
| `resources.requests.memory`          | `128Mi`          | Memory request                      |
| `resources.limits.cpu`               | `200m`           | CPU limit                           |
| `resources.limits.memory`            | `256Mi`          | Memory limit                        |
| `livenessProbe.initialDelaySeconds`  | `15`             | Delay before liveness probe starts  |
| `readinessProbe.initialDelaySeconds` | `5`              | Delay before readiness probe starts |

### Environment-Specific Customization

```bash
# Development
helm install myapp k8s/devops-info-service -f k8s/devops-info-service/values-dev.yaml

# Production
helm install myapp k8s/devops-info-service -f k8s/devops-info-service/values-prod.yaml
```

**Dev vs Prod differences:**

| Setting                             | Dev        | Prod           |
|-------------------------------------|------------|----------------|
| `replicaCount`                      | 1          | 5              |
| `image.tag`                         | `latest`   | `1.0.0`        |
| `image.pullPolicy`                  | `Always`   | `IfNotPresent` |
| `service.type`                      | `NodePort` | `LoadBalancer` |
| `resources.limits.cpu`              | `100m`     | `500m`         |
| `resources.limits.memory`           | `128Mi`    | `512Mi`        |
| `livenessProbe.initialDelaySeconds` | `5`        | `30`           |

---

## Hook Implementation

### Hooks Overview

| Hook               | Type           | Weight | Delete Policy    | Purpose                                           |
|--------------------|----------------|--------|------------------|---------------------------------------------------|
| `pre-install-job`  | `pre-install`  | `-5`   | `hook-succeeded` | Validates prerequisites before chart installation |
| `post-install-job` | `post-install` | `+5`   | `hook-succeeded` | Runs smoke test after all resources are ready     |

### Execution Order

```
helm install ->
  [weight -5] pre-install Job runs and completes ->
  Main resources created (Deployment, Service) ->
  [weight +5] post-install Job runs and completes ->
  Release marked as "deployed"
```

### Hook Annotations

```yaml
annotations:
  "helm.sh/hook": pre-install          # Hook type
  "helm.sh/hook-weight": "-5"          # Lower = runs first
  "helm.sh/hook-delete-policy": hook-succeeded  # Auto-cleanup on success
```

### Deletion Policy

`hook-succeeded` - Kubernetes deletes the Job automatically after it exits with code `0`. 
This keeps the cluster clean, failed hooks are preserved for debugging.

---

## Installation Evidence

### Helm Installation

```
helm version
version.BuildInfo{Version:"v4.0.0", GitCommit:"99cd1964357c793351be481d55abbe21c6b2f4ec",
GitTreeState:"clean", GoVersion:"go1.25.3", KubeClientVersion:"v1.34"}
```

### Repository Exploration

```
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm show chart prometheus-community/prometheus

annotations:
  artifacthub.io/license: Apache-2.0
apiVersion: v2
appVersion: v3.10.0
description: Prometheus is a monitoring system and time series database.
name: prometheus
version: 28.14.1
```

### helm lint Output

```
helm lint k8s/devops-info-service
==> Linting k8s/devops-info-service
[INFO] Chart.yaml: icon is recommended

1 chart(s) linted, 0 chart(s) failed
```

### helm template Verification (excerpt)

```yaml
# Source: devops-info-service/templates/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: devops-app-devops-info-service
  labels:
    helm.sh/chart: devops-info-service-0.1.0
    app.kubernetes.io/name: devops-info-service
    app.kubernetes.io/instance: devops-app
    app.kubernetes.io/version: "1.0.0"
    app.kubernetes.io/managed-by: Helm
spec:
  replicas: 3
  ...
```

### Dev Environment Install

```
helm install devops-dev k8s/devops-info-service -f k8s/devops-info-service/values-dev.yaml --wait

NAME: devops-dev
LAST DEPLOYED: Thu Apr  2 10:58:45 2026
NAMESPACE: default
STATUS: deployed
REVISION: 1
DESCRIPTION: Install complete
```

### Upgrade to Prod

```
helm upgrade devops-dev k8s/devops-info-service -f k8s/devops-info-service/values-prod.yaml --wait

Release "devops-dev" has been upgraded. Happy Helming!
NAME: devops-dev
STATUS: deployed
REVISION: 2
```

### Rollback

```
helm rollback devops-dev 1

Rollback was a success! Happy Helming!
```

### Helm Release History

```
REVISION  UPDATED                   STATUS      CHART                     APP VERSION  DESCRIPTION
1         Thu Apr  2 10:58:45 2026  superseded  devops-info-service-0.1.0  1.0.0       Install complete
2         Thu Apr  2 10:59:34 2026  superseded  devops-info-service-0.1.0  1.0.0       Upgrade complete
3         Thu Apr  2 11:00:15 2026  deployed    devops-info-service-0.1.0  1.0.0       Rollback to 1
```

### helm list

```
NAME       NAMESPACE  REVISION  UPDATED                               STATUS    CHART                     APP VERSION
devops-dev default    3         2026-04-02 11:00:15.4424245 +0300 MSK deployed  devops-info-service-0.1.0  1.0.0
echo-app   default    1         2026-04-02 11:02:22.401563 +0300 MSK  deployed  echo-service-0.1.0         latest
```

### kubectl get all

```
NAME                                                  READY   STATUS    RESTARTS   AGE
pod/devops-dev-devops-info-service-5957555684-xtgdq   1/1     Running   0          2m26s
pod/echo-app-echo-service-7c9bdfcfc6-6sdnn            1/1     Running   0          19s

NAME                                     TYPE        CLUSTER-IP      EXTERNAL-IP   PORT(S)        AGE
service/devops-dev-devops-info-service   NodePort    10.96.190.255   <none>        80:30080/TCP   3m46s
service/echo-app-echo-service            NodePort    10.100.51.59    <none>        80:30081/TCP   19s
service/kubernetes                       ClusterIP   10.96.0.1       <none>        443/TCP        6d22h

NAME                                             READY   UP-TO-DATE   AVAILABLE   AGE
deployment.apps/devops-dev-devops-info-service   1/1     1            1           3m46s
deployment.apps/echo-app-echo-service            1/1     1            1           19s
```

### Hook Execution

Hooks ran as Jobs during `helm install`.
After successful completion they were automatically deleted by `hook-delete-policy: hook-succeeded`:

```
kubectl get jobs
No resources found in default namespace.
# Both pre-install and post-install jobs completed and were auto-deleted per deletion policy
```

Hook logs:
```
=== Pre-install validation ===
Chart: devops-info-service v0.1.0
Release: devops-dev
Namespace: default
Checking environment prerequisites...
=== Pre-install completed successfully ===

=== Post-install smoke test ===
Release devops-dev deployed successfully
App version: 1.0.0
Expected replicas: 1
Running smoke test...
=== Post-install smoke test passed ===
```

### Application Accessibility

```
kubectl port-forward service/devops-dev-devops-info-service 8088:80
curl http://127.0.0.1:8088/health

StatusCode: 200
Content: {"status":"healthy","timestamp":"2026-04-02T08:00:52.733985","uptime_seconds":24}
```

---

## Operations

### Installation

```bash
# Install with default values
helm install devops-dev k8s/devops-info-service

# Install with dev overrides
helm install devops-dev k8s/devops-info-service -f k8s/devops-info-service/values-dev.yaml

# Install with prod overrides
helm install devops-prod k8s/devops-info-service -f k8s/devops-info-service/values-prod.yaml

# Dry-run to preview manifests
helm install --dry-run=client --debug test k8s/devops-info-service
```

### Upgrade

```bash
# Upgrade existing release to prod configuration
helm upgrade devops-dev k8s/devops-info-service -f k8s/devops-info-service/values-prod.yaml --wait

# Override a single value inline
helm upgrade devops-dev k8s/devops-info-service --set replicaCount=5
```

### Rollback

```bash
# View release history
helm history devops-dev

# Roll back to previous revision
helm rollback devops-dev

# Roll back to specific revision
helm rollback devops-dev 1
```

### Uninstall

```bash
helm uninstall devops-dev
helm uninstall echo-app
```

---

## Testing & Validation

### Lint

```bash
helm lint k8s/devops-info-service
# 1 chart(s) linted, 0 chart(s) failed

helm lint k8s/echo-service
# 1 chart(s) linted, 0 chart(s) failed
```

### Template Rendering

```bash
# Render with default values
helm template devops-app k8s/devops-info-service

# Render with dev overrides
helm template devops-dev k8s/devops-info-service -f k8s/devops-info-service/values-dev.yaml

# Render with prod overrides
helm template devops-prod k8s/devops-info-service -f k8s/devops-info-service/values-prod.yaml
```

### Dry-run

```bash
helm install --dry-run=client --debug test-release k8s/devops-info-service
```

---

## Library Chart (common-lib)

### Purpose

`common-lib` is a Helm library chart (`type: library`) that contains shared named templates. 
Library charts cannot be installed directly - they are used only as dependencies.

### Shared Templates

| Template                          | Description                                                   |
|-----------------------------------|---------------------------------------------------------------|
| `common.name`                     | Chart name, respects `nameOverride`                           |
| `common.fullname`                 | `<release>-<chart>`, respects `fullnameOverride`              |
| `common.chart`                    | `<chart>-<version>` for `helm.sh/chart` label                 |
| `common.labels`                   | Full set of `app.kubernetes.io/*` labels                      |
| `common.selectorLabels`           | Minimal labels for pod selector matching                      |
| `common.podSecurityContext`       | Standard non-root pod security context                        |
| `common.containerSecurityContext` | Standard container security context with dropped capabilities |

### How Charts Use the Library

Both `devops-info-service` and `echo-service` declare `common-lib` as a dependency:

```yaml
# Chart.yaml
dependencies:
  - name: common-lib
    version: 0.1.0
    repository: "file://../common-lib"
```

After running `helm dependency update`, the library is packaged into `charts/common-lib-0.1.0.tgz` and templates reference it:

```yaml
# templates/deployment.yaml
metadata:
  name: {{ include "common.fullname" . }}
  labels:
    {{- include "common.labels" . | nindent 4 }}
```

### Benefits

- **DRY**: Labels and helpers are defined once, used everywhere
- **Consistency**: All apps produce identical `app.kubernetes.io/*` labels
- **Maintainability**: Updating label conventions requires a single file change
- **Standardization**: Security contexts are enforced uniformly across all charts
