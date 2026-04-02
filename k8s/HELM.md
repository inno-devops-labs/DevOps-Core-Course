# Lab 10 — Helm Package Manager

## 1. Chart Overview

### Directory Structure

```
k8s/
├── devops-python-chart/        # Main application chart (Tasks 2-4)
│   ├── Chart.yaml              # Chart metadata and dependencies
│   ├── values.yaml             # Default configuration values
│   ├── values-dev.yaml         # Development environment overrides
│   ├── values-prod.yaml        # Production environment overrides
│   └── templates/
│       ├── _helpers.tpl        # Named template helpers (name, labels)
│       ├── deployment.yaml     # Deployment template
│       ├── service.yaml        # Service template
│       ├── ingress.yaml        # Ingress template (conditional)
│       ├── NOTES.txt           # Post-install user instructions
│       └── hooks/
│           ├── pre-install-job.yaml   # Pre-install validation job
│           └── post-install-job.yaml  # Post-install smoke test job
├── common-lib/                 # Bonus: shared library chart
│   ├── Chart.yaml
│   └── templates/
│       ├── _common.tpl         # Template index/documentation
│       ├── _names.tpl          # common.name, common.fullname, common.chart
│       └── _labels.tpl         # common.labels, common.selectorLabels
└── devops-go-chart/            # Bonus: second application chart
    ├── Chart.yaml
    ├── values.yaml
    └── templates/
        ├── _helpers.tpl        # Thin wrappers delegating to common-lib
        ├── deployment.yaml
        ├── service.yaml
        └── NOTES.txt
```

### Template Files and Purpose

| File | Purpose |
|------|---------|
| `_helpers.tpl` | Named templates for name generation and labels. Used throughout other templates via `include`. |
| `deployment.yaml` | Kubernetes Deployment with templated replicas, image, probes, resources, env vars. |
| `service.yaml` | Kubernetes Service. NodePort/LoadBalancer type and nodePort field are conditional on values. |
| `ingress.yaml` | Nginx Ingress. Entire resource is conditional: only created when `ingress.enabled: true`. |
| `NOTES.txt` | Rendered and printed to terminal after install. Shows access URL based on service type. |
| `hooks/pre-install-job.yaml` | Job that runs before installation. Simulates environment validation. |
| `hooks/post-install-job.yaml` | Job that runs after installation. Simulates smoke test against the service. |

### Values Design

Values are organized into logical groups (image, service, resources, env, probes, ingress, rollingUpdate). Environment-specific files only override what differs — they are **not** full copies of `values.yaml`. Helm merges them at install time.

---

## 2. Configuration Guide

### Key Values

| Value | Default | Description |
|-------|---------|-------------|
| `replicaCount` | `3` | Number of pod replicas |
| `image.repository` | `mirana18/devops-info-service` | Container image repository |
| `image.tag` | `"latest"` | Image tag. Use `Chart.AppVersion` as fallback. |
| `image.pullPolicy` | `Never` | `Never` for local minikube; `IfNotPresent` for registries |
| `service.type` | `NodePort` | `NodePort` / `LoadBalancer` / `ClusterIP` |
| `service.port` | `80` | Service port (cluster-internal) |
| `service.targetPort` | `5001` | Container port the service forwards to |
| `service.nodePort` | `30080` | NodePort (only applied when `service.type: NodePort`) |
| `resources.requests.cpu` | `100m` | CPU request |
| `resources.requests.memory` | `128Mi` | Memory request |
| `resources.limits.cpu` | `200m` | CPU limit |
| `resources.limits.memory` | `256Mi` | Memory limit |
| `env.port` | `"5001"` | PORT env variable passed to the container |
| `env.host` | `"0.0.0.0"` | HOST env variable |
| `env.debug` | `"False"` | DEBUG env variable |
| `livenessProbe.initialDelaySeconds` | `10` | Seconds before first liveness check |
| `readinessProbe.initialDelaySeconds` | `5` | Seconds before first readiness check |
| `ingress.enabled` | `true` | Create Ingress resource |
| `ingress.host` | `devops.local` | Ingress hostname |
| `ingress.tls.enabled` | `true` | Enable TLS on the Ingress |
| `ingress.tls.secretName` | `devops-tls-secret` | TLS secret name |

### Environment Customization

**Development** — 1 replica, reduced resources, no ingress, debug enabled:
```bash
helm install devops-dev k8s/devops-python-chart \
  -f k8s/devops-python-chart/values-dev.yaml
```

**Production** — 3 replicas, pinned image tag, LoadBalancer, ingress enabled:
```bash
helm install devops-prod k8s/devops-python-chart \
  -f k8s/devops-python-chart/values-prod.yaml
```

**Override a single value on the fly:**
```bash
helm install devops-dev k8s/devops-python-chart \
  -f k8s/devops-python-chart/values-dev.yaml \
  --set replicaCount=2
```

---

## 3. Hook Implementation

### What Are Hooks?

Helm hooks are Kubernetes resources (usually Jobs) annotated to run at specific points in the release lifecycle. They run to completion before Helm proceeds.

### Hooks Implemented

| Hook | File | Type | Weight | When |
|------|------|------|--------|------|
| Pre-install validation | `hooks/pre-install-job.yaml` | `pre-install,pre-upgrade` | `-5` | Before any chart resources are created |
| Post-install smoke test | `hooks/post-install-job.yaml` | `post-install,post-upgrade` | `5` | After all resources are ready |

### Execution Timeline

```
helm install
    │
    ├─ [weight -5] pre-install Job runs
    │     └─ Validates prerequisites, prints chart/release info
    │
    ├─ Main resources created (Deployment, Service, Ingress)
    │
    └─ [weight  5] post-install Job runs
          └─ Waits 10s, runs wget smoke test against service DNS
```

### Annotation Details

```yaml
# Pre-install hook
"helm.sh/hook": pre-install,pre-upgrade
"helm.sh/hook-weight": "-5"
"helm.sh/hook-delete-policy": hook-succeeded
```

```yaml
# Post-install hook
"helm.sh/hook": post-install,post-upgrade
"helm.sh/hook-weight": "5"
"helm.sh/hook-delete-policy": hook-succeeded
```

### Why `hook-succeeded`?

`hook-succeeded` deletes the Job and its pods automatically after successful completion. This keeps the cluster clean without manual cleanup. On **failure**, the Job remains — allowing `kubectl logs` and `kubectl describe` for debugging.

Alternative policies:
- `before-hook-creation` — deletes the **previous** hook resource when a new one is created. Useful during debugging (keeps logs accessible longer).
- `hook-failed` — deletes only on failure (opposite of hook-succeeded).

---

## 4. Installation Evidence

### Task 1 — Helm Setup

```
$ helm version
version.BuildInfo{Version:"v4.1.3", GitCommit:"c94d381b03be117e7e57908edbf642104e00eb8f", GitTreeState:"clean", GoVersion:"go1.26.1", KubeClientVersion:"v1.35"}
```

```
$ helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
"prometheus-community" has been added to your repositories

$ helm repo update
Hang tight while we grab the latest from your chart repositories...
...Successfully got an update from the "prometheus-community" chart repository
Update Complete. ⎈Happy Helming!⎈
```

```
$ helm show chart prometheus-community/prometheus
annotations:
  artifacthub.io/license: Apache-2.0
  artifacthub.io/links: |
    - name: Chart Source
      url: https://github.com/prometheus-community/helm-charts
    - name: Upstream Project
      url: https://github.com/prometheus/prometheus
apiVersion: v2
appVersion: v3.10.0
dependencies:
- condition: alertmanager.enabled
  name: alertmanager
  repository: https://prometheus-community.github.io/helm-charts
  version: 1.34.*
- condition: kube-state-metrics.enabled
  name: kube-state-metrics
  repository: https://prometheus-community.github.io/helm-charts
  version: 7.2.*
- condition: prometheus-node-exporter.enabled
  name: prometheus-node-exporter
  repository: https://prometheus-community.github.io/helm-charts
  version: 4.52.*
- condition: prometheus-pushgateway.enabled
  name: prometheus-pushgateway
  repository: https://prometheus-community.github.io/helm-charts
  version: 3.6.*
description: Prometheus is a monitoring system and time series database.
```

**Helm value proposition:** Helm acts as a package manager for Kubernetes — similar to `apt` or `brew`. Instead of managing raw YAML manifests, you work with versioned, configurable charts. A single chart can be deployed to dev with 1 replica and prod with 3 replicas by just swapping a values file. Helm also tracks release history, enabling rollbacks, and supports lifecycle hooks for migration and smoke test automation.

### Task 2 — Chart Validation

```
$ helm lint k8s/devops-python-chart
==> Linting k8s/devops-python-chart
[INFO] Chart.yaml: icon is recommended

1 chart(s) linted, 0 chart(s) failed

$ helm lint k8s/devops-python-chart -f k8s/devops-python-chart/values-dev.yaml
==> Linting k8s/devops-python-chart
[INFO] Chart.yaml: icon is recommended

1 chart(s) linted, 0 chart(s) failed

$ helm lint k8s/devops-python-chart -f k8s/devops-python-chart/values-prod.yaml
==> Linting k8s/devops-python-chart
[INFO] Chart.yaml: icon is recommended

1 chart(s) linted, 0 chart(s) failed
```

```
$ helm install --dry-run --debug test-release k8s/devops-python-chart -f k8s/devops-python-chart/values-dev.yaml
level=WARN msg="--dry-run is deprecated and should be replaced with '--dry-run=client'"
level=DEBUG msg="Original chart version" version=""
level=DEBUG msg="Chart path" path=".../k8s/devops-python-chart"
level=DEBUG msg="number of dependencies in the chart" chart=devops-python-chart dependencies=1
level=DEBUG msg="number of dependencies in the chart" chart=common-lib dependencies=0
NAME: test-release
LAST DEPLOYED: Thu Apr  2 12:19:09 2026
NAMESPACE: default
STATUS: pending-install
REVISION: 1
DESCRIPTION: Dry run complete
TEST SUITE: None
USER-SUPPLIED VALUES:
env:
  debug: "True"
image:
  pullPolicy: Never
  tag: latest
ingress:
  enabled: false
replicaCount: 1
resources:
  limits:
    cpu: 100m
    memory: 128Mi
  requests:
    cpu: 50m
    memory: 64Mi
service:
  nodePort: 30080
  type: NodePort
```

### Task 2 — Install (dev environment)

```
$ helm install devops-dev k8s/devops-python-chart -f k8s/devops-python-chart/values-dev.yaml
NAME: devops-dev
LAST DEPLOYED: Thu Apr  2 12:26:59 2026
NAMESPACE: default
STATUS: deployed
REVISION: 1
DESCRIPTION: Install complete
TEST SUITE: None
NOTES:
1. Application devops-dev-devops-python-chart has been deployed.
2. Access the application via NodePort:

   export NODE_IP=$(kubectl get nodes -o jsonpath="{.items[0].status.addresses[0].address}")
   echo "http://$NODE_IP:30080/health"

   Or use minikube:
   minikube service devops-dev-devops-python-chart-service --url
```

```
$ helm list
NAME        NAMESPACE  REVISION  UPDATED                              STATUS    CHART                     APP VERSION
devops-dev  default    1         2026-04-02 12:26:59.798317 +0300 MSK deployed  devops-python-chart-0.1.0  1.0.0
```

```
$ kubectl get all
NAME                                                  READY   STATUS    RESTARTS   AGE
pod/devops-dev-devops-python-chart-84754f84f-nwffl    1/1     Running   0          3m18s

NAME                                             TYPE        CLUSTER-IP    EXTERNAL-IP   PORT(S)        AGE
service/devops-dev-devops-python-chart-service   NodePort    10.98.68.33   <none>        80:30080/TCP   3m18s
service/kubernetes                               ClusterIP   10.96.0.1     <none>        443/TCP        73m

NAME                                             READY   UP-TO-DATE   AVAILABLE   AGE
deployment.apps/devops-dev-devops-python-chart   1/1     1            1           3m18s

NAME                                                       DESIRED   CURRENT   READY   AGE
replicaset.apps/devops-dev-devops-python-chart-84754f84f   1         1         1       3m18s
```

### Task 3 — Multi-Environment: Upgrade to prod

```
$ helm upgrade devops-dev k8s/devops-python-chart -f k8s/devops-python-chart/values-prod.yaml
Release "devops-dev" has been upgraded. Happy Helming!
NAME: devops-dev
LAST DEPLOYED: Thu Apr  2 12:30:16 2026
NAMESPACE: default
STATUS: deployed
REVISION: 2
DESCRIPTION: Upgrade complete
```

Replicas changed from 1 (dev) to 3 (prod):
```
$ kubectl get deployment devops-dev-devops-python-chart -o wide
NAME                             READY   UP-TO-DATE   AVAILABLE   CONTAINERS            IMAGES
devops-dev-devops-python-chart   3/3     1            3           devops-python-chart   mirana18/devops-info-service:1.0.0
```

```
$ helm history devops-dev
REVISION  UPDATED                   STATUS      CHART                     APP VERSION  DESCRIPTION
1         Thu Apr  2 12:26:59 2026  superseded  devops-python-chart-0.1.0  1.0.0       Install complete
2         Thu Apr  2 12:30:16 2026  deployed    devops-python-chart-0.1.0  1.0.0       Upgrade complete
```

### Task 4 — Hooks

Hook jobs captured during install (using `before-hook-creation` policy temporarily for visibility):

```
$ kubectl get jobs
NAME                                          STATUS     COMPLETIONS   DURATION   AGE
devops-dev-devops-python-chart-pre-install    Complete   1/1           10s        42s
devops-dev-devops-python-chart-post-install   Complete   1/1           14s        32s
```

```
$ kubectl describe job devops-dev-devops-python-chart-pre-install
Name:             devops-dev-devops-python-chart-pre-install
Namespace:        default
Annotations:      helm.sh/hook: pre-install,pre-upgrade
                  helm.sh/hook-delete-policy: before-hook-creation
                  helm.sh/hook-weight: -5
Completions:      1
Start Time:       Thu, 02 Apr 2026 12:26:59 +0300
Completed At:     Thu, 02 Apr 2026 12:27:09 +0300
Duration:         10s
Pods Statuses:    0 Active / 1 Succeeded / 0 Failed
Events:
  Normal  SuccessfulCreate  38s  job-controller  Created pod: devops-dev-devops-python-chart-pre-install-67mdr
  Normal  Completed         28s  job-controller  Job completed
```

```
$ kubectl logs job/devops-dev-devops-python-chart-pre-install
=== Pre-install validation ===
Chart: devops-python-chart v0.1.0
Release: devops-dev
Namespace: default

Checking environment prerequisites...
Cluster connectivity: OK
Namespace available: OK
Prerequisites validated successfully.

Proceeding with installation.
```

```
$ kubectl logs job/devops-dev-devops-python-chart-post-install
=== Post-install smoke test ===
Release: devops-dev
Waiting for service to be ready...

Running smoke test against http://devops-dev-devops-python-chart-service/health
Smoke test NOTE: service not reachable via cluster DNS (expected in dry-run or minikube)

Post-install smoke test complete.
```

After switching back to `hook-succeeded` policy — jobs are automatically deleted after success:
```
$ kubectl get jobs
No resources found in default namespace.
```

### Application Health Check

```
$ kubectl port-forward service/devops-dev-devops-python-chart-service 8080:80 &
$ curl http://localhost:8080/health
{
  "status": "healthy",
  "timestamp": "2026-04-02T09:29:58.263288.000Z",
  "uptime_seconds": 153.67
}
```

### Rollback

```
$ helm rollback devops-dev 1
Rollback was a success! Happy Helming!

$ helm history devops-dev
REVISION  UPDATED                   STATUS      CHART                     APP VERSION  DESCRIPTION
1         Thu Apr  2 12:26:59 2026  superseded  devops-python-chart-0.1.0  1.0.0       Install complete
2         Thu Apr  2 12:30:16 2026  superseded  devops-python-chart-0.1.0  1.0.0       Upgrade complete
3         Thu Apr  2 12:30:24 2026  deployed    devops-python-chart-0.1.0  1.0.0       Rollback to 1
```

---

## 5. Operations Reference

### Install

```bash
# Default values
helm install <release-name> k8s/devops-python-chart

# Development environment
helm install devops-dev k8s/devops-python-chart \
  -f k8s/devops-python-chart/values-dev.yaml

# Production environment
helm install devops-prod k8s/devops-python-chart \
  -f k8s/devops-python-chart/values-prod.yaml

# Override a specific value
helm install devops-dev k8s/devops-python-chart \
  -f k8s/devops-python-chart/values-dev.yaml \
  --set replicaCount=2
```

### Upgrade

```bash
# Upgrade to new values
helm upgrade devops-dev k8s/devops-python-chart \
  -f k8s/devops-python-chart/values-prod.yaml

# Upgrade and install if not exists
helm upgrade --install devops-dev k8s/devops-python-chart \
  -f k8s/devops-python-chart/values-dev.yaml
```

### Rollback

```bash
# View release history
helm history devops-dev

# Rollback to previous revision
helm rollback devops-dev

# Rollback to specific revision
helm rollback devops-dev 1
```

### Uninstall

```bash
helm uninstall devops-dev
```

### Inspect

```bash
# List all releases
helm list

# Get values used by a release
helm get values devops-dev

# Get rendered manifests of a deployed release
helm get manifest devops-dev

# View release status
helm status devops-dev
```

---

## 6. Testing & Validation

### Lint

```
$ helm lint k8s/devops-python-chart
==> Linting k8s/devops-python-chart
[INFO] Chart.yaml: icon is recommended

1 chart(s) linted, 0 chart(s) failed

$ helm lint k8s/devops-python-chart -f k8s/devops-python-chart/values-dev.yaml
==> Linting k8s/devops-python-chart
[INFO] Chart.yaml: icon is recommended

1 chart(s) linted, 0 chart(s) failed

$ helm lint k8s/devops-python-chart -f k8s/devops-python-chart/values-prod.yaml
==> Linting k8s/devops-python-chart
[INFO] Chart.yaml: icon is recommended

1 chart(s) linted, 0 chart(s) failed
```

### Template Rendering (dev values — ingress absent, replicas=1)

```
$ helm template test-release k8s/devops-python-chart -f k8s/devops-python-chart/values-dev.yaml
---
# Source: devops-python-chart/templates/service.yaml
apiVersion: v1
kind: Service
metadata:
  name: test-release-devops-python-chart-service
  labels:
    helm.sh/chart: devops-python-chart-0.1.0
    app.kubernetes.io/name: devops-python-chart
    app.kubernetes.io/instance: test-release
    app.kubernetes.io/version: "1.0.0"
    app.kubernetes.io/managed-by: Helm
spec:
  type: NodePort
  selector:
    app.kubernetes.io/name: devops-python-chart
    app.kubernetes.io/instance: test-release
  ports:
    - protocol: TCP
      port: 80
      targetPort: 5001
      nodePort: 30080
---
# Source: devops-python-chart/templates/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: test-release-devops-python-chart
spec:
  replicas: 1
  ...
  template:
    spec:
      containers:
        - name: devops-python-chart
          image: "mirana18/devops-info-service:latest"
          env:
            - name: PORT
              value: "5001"
            - name: HOST
              value: "0.0.0.0"
            - name: DEBUG
              value: "True"
          livenessProbe:
            httpGet:
              path: /health
              port: 5001
            initialDelaySeconds: 5
          readinessProbe:
            httpGet:
              path: /health
              port: 5001
            initialDelaySeconds: 3
```

Note: no `ingress.yaml` in output — `ingress.enabled: false` in dev values works correctly.

### Dry Run (abbreviated)

```
$ helm install --dry-run --debug test-release k8s/devops-python-chart -f k8s/devops-python-chart/values-dev.yaml
NAME: test-release
LAST DEPLOYED: Thu Apr  2 12:19:09 2026
NAMESPACE: default
STATUS: pending-install
REVISION: 1
DESCRIPTION: Dry run complete
```

---

## Bonus — Library Charts

### Overview

The `common-lib` library chart extracts shared template logic (name generation and labels) into a single location. Both `devops-python-chart` and `devops-go-chart` use it as a dependency instead of duplicating code.

### Library Chart Structure

```
common-lib/
├── Chart.yaml          # type: library — cannot be installed directly
└── templates/
    ├── _common.tpl     # Index of available templates
    ├── _names.tpl      # common.name, common.fullname, common.chart
    └── _labels.tpl     # common.labels, common.selectorLabels
```

**All files in a library chart MUST start with `_`** — otherwise Helm would try to render them as Kubernetes resources and fail.

### Shared Templates

| Template | Description |
|----------|-------------|
| `common.name` | Chart name trimmed to 63 chars, respects `nameOverride` |
| `common.fullname` | `release-name + chart-name` trimmed to 63 chars, respects `fullnameOverride` |
| `common.chart` | `chart-name-version` string used in `helm.sh/chart` label |
| `common.labels` | Full recommended label set (includes version, managed-by) |
| `common.selectorLabels` | Stable selector labels (name + instance only — immutable) |

### How App Charts Use the Library

Each app chart declares `common-lib` as a dependency:
```yaml
# devops-python-chart/Chart.yaml
dependencies:
  - name: common-lib
    version: "0.1.0"
    repository: "file://../common-lib"
```

The `_helpers.tpl` in each app chart becomes a thin wrapper:
```yaml
{{- define "devops-go-chart.fullname" -}}
{{- include "common.fullname" . }}
{{- end }}
```

### Benefits

- **DRY** — label and naming logic lives in one place
- **Consistency** — all apps produce identical label structure
- **Maintainability** — changing a label standard requires editing one file, not N charts
- **Testability** — library templates can be tested independently

### Install Bonus Charts

```bash
# Package library dependency first
helm dependency update k8s/devops-python-chart
helm dependency update k8s/devops-go-chart

# Install both apps
helm install python-release k8s/devops-python-chart \
  -f k8s/devops-python-chart/values-dev.yaml
helm install go-release k8s/devops-go-chart
```

```
$ helm dependency update k8s/devops-python-chart
Hang tight while we grab the latest from your chart repositories...
...Successfully got an update from the "prometheus-community" chart repository
Update Complete. ⎈Happy Helming!⎈
Saving 1 charts
Deleting outdated charts

$ helm dependency update k8s/devops-go-chart
Hang tight while we grab the latest from your chart repositories...
...Successfully got an update from the "prometheus-community" chart repository
Update Complete. ⎈Happy Helming!⎈
Saving 1 charts
Deleting outdated charts
```

```
$ helm install python-release k8s/devops-python-chart -f k8s/devops-python-chart/values-dev.yaml
NAME: python-release
LAST DEPLOYED: Thu Apr  2 12:34:08 2026
NAMESPACE: default
STATUS: deployed
REVISION: 1
DESCRIPTION: Install complete

$ helm install go-release k8s/devops-go-chart
NAME: go-release
LAST DEPLOYED: Thu Apr  2 12:34:35 2026
NAMESPACE: default
STATUS: deployed
REVISION: 1
DESCRIPTION: Install complete
```

```
$ helm list
NAME           NAMESPACE  REVISION  UPDATED                              STATUS    CHART                     APP VERSION
go-release     default    1         2026-04-02 12:34:35.367806 +0300 MSK deployed  devops-go-chart-0.1.0     1.0.0
python-release default    1         2026-04-02 12:34:08.813658 +0300 MSK deployed  devops-python-chart-0.1.0  1.0.0
```

```
$ kubectl get all
NAME                                                     READY   STATUS    RESTARTS   AGE
pod/go-release-devops-go-chart-df6fc99c4-n5ktt           1/1     Running   0          21s
pod/go-release-devops-go-chart-df6fc99c4-t695l           1/1     Running   0          21s
pod/python-release-devops-python-chart-649f5f646-hssh8   1/1     Running   0          39s

NAME                                                 TYPE        CLUSTER-IP       EXTERNAL-IP   PORT(S)        AGE
service/go-release-devops-go-chart-service           NodePort    10.107.130.240   <none>        80:30081/TCP   21s
service/kubernetes                                   ClusterIP   10.96.0.1        <none>        443/TCP        77m
service/python-release-devops-python-chart-service   NodePort    10.98.93.163     <none>        80:30080/TCP   39s

NAME                                                 READY   UP-TO-DATE   AVAILABLE   AGE
deployment.apps/go-release-devops-go-chart           2/2     2            2           21s
deployment.apps/python-release-devops-python-chart   1/1     1            1           39s
```

Both services healthy:

```
$ kubectl port-forward service/python-release-devops-python-chart-service 8080:80 &
$ curl -s http://localhost:8080/health
{
  "status": "healthy",
  "timestamp": "2026-04-02T09:37:02.843921.000Z",
  "uptime_seconds": 150.73
}

$ kubectl port-forward service/go-release-devops-go-chart-service 8081:80 &
$ curl -s http://localhost:8081/health
{"status":"healthy","timestamp":"2026-04-02T09:35:07.519Z","uptime_seconds":31.35}
```
