# Helm Chart Documentation

## Chart Overview

### Structure

```
k8s/
├── app-python/                  # Main application chart
│   ├── Chart.yaml
│   ├── values.yaml
│   ├── values-dev.yaml
│   ├── values-prod.yaml
│   └── templates/
│       ├── _helpers.tpl
│       ├── deployment.yaml
│       ├── service.yaml
│       ├── NOTES.txt
│       └── hooks/
│           ├── pre-install-job.yaml
│           └── post-install-job.yaml
├── app-go/                      # Second application chart (bonus)
│   ├── Chart.yaml
│   ├── values.yaml
│   └── templates/
│       ├── _helpers.tpl
│       ├── deployment.yaml
│       ├── service.yaml
│       └── NOTES.txt
├── common-lib/                  # Library chart (bonus)
│   ├── Chart.yaml
│   └── templates/
│       └── _labels.tpl
```

### Key Template Files

- `templates/deployment.yaml` — Deployment with replicas, image, probes, and resources all from values
- `templates/service.yaml` — Service with type and ports from values
- `templates/_helpers.tpl` — Name/label helpers; delegates to `common-lib` templates
- `templates/hooks/pre-install-job.yaml` — Job that runs before install
- `templates/hooks/post-install-job.yaml` — Job that runs after install
- `templates/NOTES.txt` — Post-install instructions printed to the user

### Values Organization

`values.yaml` holds all defaults. Environment-specific files only override what differs:

- `values-dev.yaml` — low resources, 1 replica, NodePort, `latest` tag
- `values-prod.yaml` — higher resources, 3 replicas, LoadBalancer, pinned tag

---

## Configuration Guide

### Important Values

| Key                                  | Default                          | Description                   |
| ------------------------------------ | -------------------------------- | ----------------------------- |
| `replicaCount`                       | `2`                              | Number of pod replicas        |
| `image.repository`                   | `polinanime/devops-info-service` | Docker image repository       |
| `image.tag`                          | `latest`                         | Image tag                     |
| `image.pullPolicy`                   | `IfNotPresent`                   | Pull policy                   |
| `service.type`                       | `NodePort`                       | Service type                  |
| `service.port`                       | `80`                             | Service port                  |
| `service.targetPort`                 | `8000`                           | Container port                |
| `resources.limits.cpu`               | `200m`                           | CPU limit                     |
| `resources.limits.memory`            | `256Mi`                          | Memory limit                  |
| `livenessProbe.initialDelaySeconds`  | `10`                             | Liveness probe initial delay  |
| `readinessProbe.initialDelaySeconds` | `5`                              | Readiness probe initial delay |

### Environment Differences

| Setting                             | Dev        | Prod           |
| ----------------------------------- | ---------- | -------------- |
| `replicaCount`                      | 1          | 3              |
| `image.tag`                         | `latest`   | `1.0`          |
| `service.type`                      | `NodePort` | `LoadBalancer` |
| `resources.limits.cpu`              | `100m`     | `500m`         |
| `resources.limits.memory`           | `128Mi`    | `512Mi`        |
| `livenessProbe.initialDelaySeconds` | `5`        | `30`           |

### Example Installations

```bash
# Default
helm install myapp k8s/app-python

# Development
helm install myapp k8s/app-python -f k8s/app-python/values-dev.yaml

# Production
helm install myapp k8s/app-python -f k8s/app-python/values-prod.yaml

# Override a single value
helm install myapp k8s/app-python --set replicaCount=5
```

---

## Hook Implementation

### Hooks Implemented

**Pre-install** (`templates/hooks/pre-install-job.yaml`)

- Runs a `busybox` Job before any chart resources are created
- Simulates environment validation (prints config values)
- Weight: `-5` (runs before any other hooks)
- Deletion policy: `hook-succeeded` (deleted after success)

**Post-install** (`templates/hooks/post-install-job.yaml`)

- Runs a `busybox` Job after all resources are installed and ready
- Simulates a smoke test / notification
- Weight: `5` (runs after resources are up)
- Deletion policy: `hook-succeeded` (deleted after success)

### Execution Order

```
helm install
    └── pre-install Job  (weight -5)  → chart resources created → post-install Job (weight 5)
```

### Deletion Policy

Both hooks use `hook-succeeded`. This means the Job is deleted automatically after it completes successfully, keeping the namespace clean. If a hook fails, the Job remains for debugging.

---

## Installation Evidence

### helm version

```
version.BuildInfo{Version:"v3.18.2", GitCommit:"04cad4610054e5d546aa5c5d9c1b1d5cf68ec1f8", GitTreeState:"clean", GoVersion:"go1.24.3"}
```

### helm repo add + helm search repo

```
$ helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
"prometheus-community" already exists with the same configuration, skipping

$ helm search repo prometheus | head -5
NAME                                               CHART VERSION  APP VERSION  DESCRIPTION
prometheus-community/kube-prometheus-stack         82.16.1        v0.89.0      kube-prometheus-stack collects Kubernetes manif...
prometheus-community/prometheus                    28.15.0        v3.11.0      Prometheus is a monitoring system and time seri...
prometheus-community/prometheus-adapter            5.3.0          v0.12.0      A Helm chart for k8s prometheus adapter
prometheus-community/prometheus-blackbox-exporter  11.9.1         v0.28.0      Prometheus Blackbox Exporter
```

### helm show chart prometheus-community/prometheus (excerpt)

```
apiVersion: v2
appVersion: v3.11.0
dependencies:
- condition: alertmanager.enabled
  name: alertmanager
  repository: https://prometheus-community.github.io/helm-charts
  version: 1.34.*
...
```

### helm lint

```
$ helm lint k8s/app-python
==> Linting k8s/app-python
[INFO] Chart.yaml: icon is recommended

1 chart(s) linted, 0 chart(s) failed
```

### helm template (excerpt)

```
$ helm template myapp k8s/app-python -f k8s/app-python/values-dev.yaml
---
# Source: app-python/templates/service.yaml
apiVersion: v1
kind: Service
metadata:
  name: myapp-app-python
  labels:
    helm.sh/chart: app-python-0.1.0
    app.kubernetes.io/name: app-python
    app.kubernetes.io/instance: myapp
    app.kubernetes.io/version: "1.0"
    app.kubernetes.io/managed-by: Helm
spec:
  type: NodePort
  ports:
    - port: 80
      targetPort: 8000
      protocol: TCP
      name: http
---
# Source: app-python/templates/deployment.yaml
apiVersion: apps/v1
kind: Deployment
...
  replicas: 1
      containers:
        - name: app-python
          image: "polinanime/devops-info-service:latest"
          livenessProbe:
            httpGet:
              path: /health
              port: 8000
            initialDelaySeconds: 5
            periodSeconds: 10
          readinessProbe:
            httpGet:
              path: /health
              port: 8000
            initialDelaySeconds: 3
            periodSeconds: 5
```

### helm install --dry-run --debug (excerpt)

```
$ helm install --dry-run --debug myapp k8s/app-python
...
NOTES:
1. Get the application URL:
  export NODE_PORT=$(kubectl get --namespace default -o jsonpath="{.spec.ports[0].nodePort}" services myapp-app-python)
  export NODE_IP=$(kubectl get nodes --namespace default -o jsonpath="{.items[0].status.addresses[0].address}")
  echo http://$NODE_IP:$NODE_PORT
```

### helm install (dev)

```
$ helm install myapp k8s/app-python -f k8s/app-python/values-dev.yaml
NAME: myapp
LAST DEPLOYED: Thu Apr  2 23:25:03 2026
NAMESPACE: default
STATUS: deployed
REVISION: 1
```

### Hook execution (kubectl get events)

```
$ kubectl get events --sort-by='.lastTimestamp' | grep -i "job\|hook\|pre\|post"
6m10s  Normal  SuccessfulCreate  job/myapp-app-python-pre-install   Created pod: myapp-app-python-pre-install-r5nvq
6m6s   Normal  Started           pod/myapp-app-python-pre-install-r5nvq  Started container pre-install-job
5m58s  Normal  Completed         job/myapp-app-python-pre-install   Job completed
5m58s  Normal  SuccessfulCreate  job/myapp-app-python-post-install  Created pod: myapp-app-python-post-install-wb8sr
5m56s  Normal  Started           pod/myapp-app-python-post-install-wb8sr Started container post-install-job
5m49s  Normal  Completed         job/myapp-app-python-post-install  Job completed
```

Hooks deleted themselves per `hook-succeeded` policy — `kubectl get jobs` returned no resources.

### helm upgrade (prod)

```
$ helm upgrade myapp k8s/app-python -f k8s/app-python/values-prod.yaml --set image.tag=latest
Release "myapp" has been upgraded. Happy Helming!
NAME: myapp
LAST DEPLOYED: Thu Apr  2 23:23:50 2026
NAMESPACE: default
STATUS: deployed
REVISION: 3
```

### kubectl get all (after prod upgrade — 3 replicas, LoadBalancer)

```
NAME                                    READY   STATUS    RESTARTS   AGE
pod/myapp-app-python-5675c5c8f7-lpznx   1/1     Running   0          19s
pod/myapp-app-python-5675c5c8f7-v94d6   1/1     Running   0          7s
pod/myapp-app-python-768589c54-fhmv4    1/1     Running   0          19s

NAME                       TYPE           CLUSTER-IP     EXTERNAL-IP   PORT(S)        AGE
service/myapp-app-python   LoadBalancer   10.98.41.247   <pending>     80:30500/TCP   4m16s

NAME                               READY   UP-TO-DATE   AVAILABLE   AGE
deployment.apps/myapp-app-python   3/3     2            3           4m16s
```

### helm list

```
NAME     NAMESPACE  REVISION  UPDATED                              STATUS    CHART            APP VERSION
myapp    default    2         2026-04-02 23:28:54.537401 +0300 MSK deployed  app-python-0.1.0 1.0
myapp-go default    1         2026-04-02 23:29:57.082412 +0300 MSK deployed  app-go-0.1.0     1.0
```

### kubectl get all (final state — both apps running)

```
NAME                                    READY   STATUS    RESTARTS   AGE
pod/myapp-app-python-548988b49f-fs4f4   1/1     Running   0          4m39s
pod/myapp-go-app-go-5d976bfcfb-nl6df    1/1     Running   0          18s
pod/myapp-go-app-go-5d976bfcfb-wxzcc    1/1     Running   0          18s

NAME                       TYPE        CLUSTER-IP      EXTERNAL-IP   PORT(S)        AGE
service/myapp-app-python   NodePort    10.99.193.184   <none>        80:30093/TCP   4m39s
service/myapp-go-app-go    NodePort    10.98.60.246    <none>        80:32065/TCP   18s

NAME                               READY   UP-TO-DATE   AVAILABLE   AGE
deployment.apps/myapp-app-python   1/1     1            1           4m39s
deployment.apps/myapp-go-app-go    2/2     2            2           18s
```

### Application health check

```
$ kubectl port-forward svc/myapp-app-python 8080:80 &
$ curl -s http://localhost:8080/health
{"status":"healthy","timestamp":"2026-04-02T20:26:55.317297+00:00","uptime_seconds":69}
```

---

## Operations

### Install

```bash
helm install myapp k8s/app-python -f k8s/app-python/values-dev.yaml
```

### Upgrade

```bash
helm upgrade myapp k8s/app-python -f k8s/app-python/values-prod.yaml
```

### Rollback

```bash
helm rollback myapp        # roll back to previous revision
helm rollback myapp 2      # roll back to specific revision
helm history myapp         # view revision history
```

### Uninstall

```bash
helm uninstall myapp
```

---

## Testing & Validation

```bash
# Lint
helm lint k8s/app-python

# Render templates locally
helm template myapp k8s/app-python -f k8s/app-python/values-dev.yaml

# Dry run
helm install --dry-run --debug myapp k8s/app-python
```

---

## Bonus — Library Charts

### Library Chart: common-lib

`k8s/common-lib/` is a chart of `type: library`. It cannot be installed directly. It only contains shared template definitions in `templates/_labels.tpl`:

- `common.name` — chart name, truncated to 63 chars
- `common.fullname` — release + chart name combined
- `common.chart` — chart name + version label value
- `common.labels` — full set of standard `app.kubernetes.io/*` labels
- `common.selectorLabels` — immutable selector labels (name + instance)

### How Both Apps Use It

Both `app-python/Chart.yaml` and `app-go/Chart.yaml` declare the dependency:

```yaml
dependencies:
  - name: common-lib
    version: 0.1.0
    repository: "file://../common-lib"
```

Both `_helpers.tpl` files delegate entirely to the library:

```yaml
{{- define "app-python.labels" -}}
{{- include "common.labels" . }}
{{- end }}
```

This means label generation logic lives in one place. Any change to the label standard only needs to be made in `common-lib`.

### Benefits

- **DRY** — label and naming logic defined once, used everywhere
- **Consistency** — all apps produce identical standard labels
- **Maintainability** — updating a shared template propagates to all consumers via `helm dependency update`

### Deployment of both apps

```
$ helm dependency update k8s/app-python
$ helm dependency update k8s/app-go
$ helm install myapp k8s/app-python -f k8s/app-python/values-dev.yaml
$ helm install myapp-go k8s/app-go
```

Both deployed successfully as shown in the `helm list` and `kubectl get all` output above.
