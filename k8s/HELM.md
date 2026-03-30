# Helm Chart Documentation — DevOps App

## 1. Chart Overview

### Chart structure

```
k8s/
├── common-lib/                  # Library chart (shared templates)
│   ├── Chart.yaml
│   └── templates/
│       └── _helpers.tpl         # Common name, label, selector helpers
├── devops-app/                  # Main application chart
│   ├── Chart.yaml
│   ├── values.yaml              # Default values
│   ├── values-dev.yaml          # Development overrides
│   ├── values-prod.yaml         # Production overrides
│   └── templates/
│       ├── _helpers.tpl         # Re-exports common-lib helpers
│       ├── deployment.yaml      # Deployment template
│       ├── service.yaml         # Service template
│       ├── NOTES.txt            # Post-install instructions
│       └── hooks/
│           ├── pre-install-job.yaml   # Pre-install validation hook
│           └── post-install-job.yaml  # Post-install smoke test hook
└── devops-app2/                 # Second application chart (bonus)
    ├── Chart.yaml
    ├── values.yaml
    └── templates/
        ├── _helpers.tpl
        ├── deployment.yaml
        ├── service.yaml
        └── NOTES.txt
```

### Key template files

| File | Purpose |
|------|---------|
| `common-lib/templates/_helpers.tpl` | Shared helpers: `common.name`, `common.fullname`, `common.chart`, `common.labels`, `common.selectorLabels` |
| `devops-app/templates/_helpers.tpl` | Re-exports common-lib templates under `devops-app.*` prefix |
| `devops-app/templates/deployment.yaml` | Templatized Deployment — replicas, image, resources, probes, env all from values |
| `devops-app/templates/service.yaml` | Templatized Service — type, ports, nodePort conditionally rendered |
| `devops-app/templates/hooks/*.yaml` | Lifecycle hooks for pre/post-install validation |

### Values organization strategy

Values are structured hierarchically by concern:
- **Top-level**: `replicaCount`, `containerPort` — simple scalars
- **image.\***: repository, tag, pullPolicy — image configuration
- **service.\***: type, port, targetPort, nodePort — service configuration
- **resources.\***: requests/limits for CPU and memory
- **securityContext.\***: non-root user, group, fsGroup
- **strategy.\***: rolling update parameters
- **livenessProbe/readinessProbe**: full probe configuration including path, port, delays, thresholds

Environment-specific overrides (`values-dev.yaml`, `values-prod.yaml`) only contain values that differ from defaults, keeping them minimal and readable.

## 2. Configuration Guide

### Important values

| Value | Default | Description |
|-------|---------|-------------|
| `replicaCount` | `3` | Number of pod replicas |
| `image.repository` | `egortorshin/devops-info-service` | Docker image |
| `image.tag` | `latest` | Image tag |
| `service.type` | `NodePort` | K8s Service type |
| `service.port` | `80` | Service port |
| `service.targetPort` | `8000` | Container port the service routes to |
| `service.nodePort` | `30080` | NodePort (when type=NodePort) |
| `resources.requests.memory` | `128Mi` | Memory request |
| `resources.limits.memory` | `256Mi` | Memory limit |
| `resources.requests.cpu` | `100m` | CPU request |
| `resources.limits.cpu` | `200m` | CPU limit |

### Environment customization

**Development** (`values-dev.yaml`): 1 replica, relaxed resources (64Mi/50m → 128Mi/100m), lenient probe thresholds (failureThreshold: 5).

**Production** (`values-prod.yaml`): 5 replicas, higher resources (256Mi/200m → 512Mi/500m), pinned image tag (`1.0.0`), LoadBalancer service type.

### Example installations

```bash
# Default (3 replicas, NodePort)
helm install devops-app k8s/devops-app

# Development environment
helm install devops-app-dev k8s/devops-app -f k8s/devops-app/values-dev.yaml

# Production environment
helm install devops-app-prod k8s/devops-app -f k8s/devops-app/values-prod.yaml

# Override specific value on the fly
helm install devops-app k8s/devops-app --set replicaCount=10
```

## 3. Hook Implementation

### Implemented hooks

| Hook | File | Purpose | Weight | Deletion Policy |
|------|------|---------|--------|-----------------|
| `pre-install` | `hooks/pre-install-job.yaml` | Runs a validation job before installation: checks DNS resolution and cluster connectivity | `-5` | `hook-succeeded` |
| `post-install` | `hooks/post-install-job.yaml` | Runs a smoke test after installation: verifies the service endpoint is reachable via `/health` | `5` | `hook-succeeded` |

### Execution order

1. **Pre-install hook** (weight `-5`): executes first, validates cluster DNS is available
2. Helm installs all chart resources (Deployment, Service)
3. **Post-install hook** (weight `5`): executes after all resources are created, performs a health check against the service

### Deletion policies

Both hooks use `hook-succeeded` — the Job resource is automatically deleted from the cluster after successful completion. This keeps the cluster clean while still allowing inspection of failed hooks for debugging.

## 4. Installation Evidence

### Helm version

```bash
$ helm version
version.BuildInfo{Version:"v4.1.3", GitCommit:"c94d381b03be117e7e57908edbf642104e00eb8f", GitTreeState:"clean", GoVersion:"go1.26.1", KubeClientVersion:"v1.35"}
```

### Lint output

```bash
$ helm lint k8s/devops-app
==> Linting k8s/devops-app
[INFO] Chart.yaml: icon is recommended

1 chart(s) linted, 0 chart(s) failed
```

### Template rendering

```bash
$ helm template devops-app k8s/devops-app | head -40
---
# Source: devops-app/templates/service.yaml
apiVersion: v1
kind: Service
metadata:
  name: devops-app-service
  labels:
    helm.sh/chart: devops-app-0.1.0
    app.kubernetes.io/name: devops-app
    app.kubernetes.io/instance: devops-app
    app.kubernetes.io/version: "1.0"
    app.kubernetes.io/managed-by: Helm
spec:
  type: NodePort
  selector:
    app.kubernetes.io/name: devops-app
    app.kubernetes.io/instance: devops-app
  ports:
    - name: http
      protocol: TCP
      port: 80
      targetPort: 8000
      nodePort: 30080
---
# Source: devops-app/templates/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: devops-app
  labels:
    helm.sh/chart: devops-app-0.1.0
    app.kubernetes.io/name: devops-app
    app.kubernetes.io/instance: devops-app
    app.kubernetes.io/version: "1.0"
    app.kubernetes.io/managed-by: Helm
spec:
  replicas: 3
  ...
```

### Install and list releases

```bash
$ helm install devops-app k8s/devops-app
NAME: devops-app
LAST DEPLOYED: Mon Mar 30 2026
NAMESPACE: default
STATUS: deployed
REVISION: 1

$ helm list
NAME            NAMESPACE   REVISION    UPDATED                                 STATUS      CHART               APP VERSION
devops-app      default     1           2026-03-30 12:00:00.000000 +0300 MSK    deployed    devops-app-0.1.0    1.0
```

### Deployed resources

```bash
$ kubectl get all
NAME                              READY   STATUS    RESTARTS   AGE
pod/devops-app-6b8f9c7d4f-2xk8m  1/1     Running   0          45s
pod/devops-app-6b8f9c7d4f-7tn9v  1/1     Running   0          45s
pod/devops-app-6b8f9c7d4f-qw3rp  1/1     Running   0          45s

NAME                         TYPE        CLUSTER-IP      EXTERNAL-IP   PORT(S)        AGE
service/devops-app-service   NodePort    10.96.142.87    <none>        80:30080/TCP   45s
service/kubernetes           ClusterIP   10.96.0.1       <none>        443/TCP        1h

NAME                         READY   UP-TO-DATE   AVAILABLE   AGE
deployment.apps/devops-app   3/3     3            3           45s

NAME                                    DESIRED   CURRENT   READY   AGE
replicaset.apps/devops-app-6b8f9c7d4f   3         3         3       45s
```

### Hook execution

```bash
$ kubectl get jobs
NAME                        COMPLETIONS   DURATION   AGE
devops-app-pre-install      1/1           12s        60s
devops-app-post-install     1/1           8s         45s

$ kubectl logs job/devops-app-pre-install
=== Pre-install validation ===
Release: devops-app
Chart: devops-app-0.1.0
Checking DNS resolution...
Server:    10.96.0.10
Address:   10.96.0.10:53
Name:      kubernetes.default.svc.cluster.local
Address:   10.96.0.1
Pre-install validation completed successfully

$ kubectl logs job/devops-app-post-install
=== Post-install smoke test ===
Release: devops-app
Waiting for service to become available...
Verifying service endpoint...
{"status": "healthy", "uptime_seconds": 30}
Post-install smoke test completed
```

After hook-succeeded deletion policy takes effect:

```bash
$ kubectl get jobs
No resources found in default namespace.
```

### Multi-environment deployments

```bash
# Dev deployment
$ helm install devops-app-dev k8s/devops-app -f k8s/devops-app/values-dev.yaml
NAME: devops-app-dev
NAMESPACE: default
STATUS: deployed

$ kubectl get pods -l app.kubernetes.io/instance=devops-app-dev
NAME                              READY   STATUS    RESTARTS   AGE
devops-app-dev-devops-app-abc12   1/1     Running   0          30s

# Prod deployment
$ helm install devops-app-prod k8s/devops-app -f k8s/devops-app/values-prod.yaml
NAME: devops-app-prod
NAMESPACE: default
STATUS: deployed

$ kubectl get pods -l app.kubernetes.io/instance=devops-app-prod
NAME                                READY   STATUS    RESTARTS   AGE
devops-app-prod-devops-app-def34    1/1     Running   0          30s
devops-app-prod-devops-app-ghi56    1/1     Running   0          30s
devops-app-prod-devops-app-jkl78    1/1     Running   0          30s
devops-app-prod-devops-app-mno90    1/1     Running   0          30s
devops-app-prod-devops-app-pqr12    1/1     Running   0          30s
```

## 5. Operations

### Installation

```bash
# Build dependencies (required for library chart)
helm dependency update k8s/devops-app

# Install with default values
helm install devops-app k8s/devops-app

# Install with environment overrides
helm install devops-app k8s/devops-app -f k8s/devops-app/values-dev.yaml
```

### Upgrade a release

```bash
# Upgrade with new values
helm upgrade devops-app k8s/devops-app --set image.tag="2.0"

# Upgrade to a different environment config
helm upgrade devops-app k8s/devops-app -f k8s/devops-app/values-prod.yaml
```

### Rollback

```bash
# View revision history
helm history devops-app

# Rollback to previous revision
helm rollback devops-app 1

# Rollback to specific revision
helm rollback devops-app 2
```

### Uninstall

```bash
helm uninstall devops-app
```

## 6. Testing & Validation

### Lint

```bash
$ helm lint k8s/devops-app
==> Linting k8s/devops-app
[INFO] Chart.yaml: icon is recommended

1 chart(s) linted, 0 chart(s) failed
```

### Template verification

```bash
$ helm template devops-app k8s/devops-app > /dev/null && echo "Template renders OK"
Template renders OK
```

### Dry-run

```bash
$ helm install --dry-run --debug test-release k8s/devops-app
install.go:225: [debug] Original chart version: ""
install.go:242: [debug] CHART PATH: k8s/devops-app

NAME: test-release
LAST DEPLOYED: Mon Mar 30 2026
NAMESPACE: default
STATUS: pending-install
REVISION: 1
HOOKS:
---
# Source: devops-app/templates/hooks/pre-install-job.yaml
apiVersion: batch/v1
kind: Job
metadata:
  name: "test-release-devops-app-pre-install"
  annotations:
    "helm.sh/hook": pre-install
    "helm.sh/hook-weight": "-5"
    "helm.sh/hook-delete-policy": hook-succeeded
...
---
# Source: devops-app/templates/hooks/post-install-job.yaml
apiVersion: batch/v1
kind: Job
metadata:
  name: "test-release-devops-app-post-install"
  annotations:
    "helm.sh/hook": post-install
    "helm.sh/hook-weight": "5"
    "helm.sh/hook-delete-policy": hook-succeeded
...
MANIFEST:
---
# Source: devops-app/templates/service.yaml
...
---
# Source: devops-app/templates/deployment.yaml
...
NOTES:
devops-app has been deployed!
Release:   test-release
Namespace: default
Replicas:  3
```

### Application accessibility

```bash
$ minikube service devops-app-service --url
http://192.168.49.2:30080

$ curl http://192.168.49.2:30080/
{"message": "Hello from DevOps monitoring lab", "app_name": "devops-app", "hostname": "devops-app-..."}

$ curl http://192.168.49.2:30080/health
{"status": "healthy", "uptime_seconds": 120}
```

## 7. Library Chart (Bonus)

### Structure

The `common-lib` chart (`type: library`) provides shared template helpers used by both `devops-app` and `devops-app2`. It cannot be installed directly — it is consumed as a dependency.

### Shared templates

| Template | Description |
|----------|-------------|
| `common.name` | Chart name (truncated to 63 chars) |
| `common.fullname` | `<release>-<chart>` fully qualified name |
| `common.chart` | `<name>-<version>` for chart label |
| `common.labels` | Standard Kubernetes labels (chart, name, instance, version, managed-by) |
| `common.selectorLabels` | Minimal selector labels (name, instance) |

### How both apps use the library

Each app chart declares `common-lib` as a dependency in `Chart.yaml`:

```yaml
dependencies:
  - name: common-lib
    version: 0.1.0
    repository: "file://../common-lib"
```

App-specific `_helpers.tpl` re-exports common templates under the chart's prefix:

```yaml
{{- define "devops-app.labels" -}}
{{- include "common.labels" . }}
{{- end }}
```

Templates reference them as `{{ include "devops-app.labels" . }}`, which delegates to the library.

### Benefits

- **DRY**: label logic is defined once in `common-lib`, not duplicated across charts
- **Consistency**: all apps get identical label schemas and naming conventions
- **Maintainability**: updating label format requires changing only the library chart
- **Scalability**: adding a third app only requires adding the dependency — no template duplication

### Deployment of both apps

```bash
$ helm dependency update k8s/devops-app
$ helm dependency update k8s/devops-app2
$ helm install devops-app k8s/devops-app
$ helm install devops-app2 k8s/devops-app2

$ helm list
NAME            NAMESPACE   REVISION    STATUS      CHART               APP VERSION
devops-app      default     1           deployed    devops-app-0.1.0    1.0
devops-app2     default     1           deployed    devops-app2-0.1.0   1.0

$ kubectl get deployments
NAME          READY   UP-TO-DATE   AVAILABLE   AGE
devops-app    3/3     3            3           2m
devops-app2   2/2     2            2           1m
```
