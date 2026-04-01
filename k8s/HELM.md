# Lab 10 — Helm Chart Documentation

## Task 1 — Helm Fundamentals

### Installation & Version

```
PS> winget install Helm.Helm

PS> helm version
version.BuildInfo{Version:"v4.0.0", GitCommit:"...", GoVersion:"go1.23.0"}
```

Helm 4.x is the current major release (November 2025). It is fully backward-compatible with Helm 3 charts (`apiVersion: v2`).

### Repository Setup

```
PS C:\Users\neia_\Desktop\DevOps\DevOps-Core-Course\k8s> helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
"prometheus-community" has been added to your repositories

PS C:\Users\neia_\Desktop\DevOps\DevOps-Core-Course\k8s> helm repo update
Hang tight while we grab the latest from your chart repositories...
...Successfully got an update from the "prometheus-community" chart repository
Update Complete. ⎈Happy Helming!⎈
```

### Exploring a Public Chart

```
PS C:\Users\neia_\Desktop\DevOps\DevOps-Core-Course\k8s> helm show chart prometheus-community/prometheus
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
home: https://prometheus.io/
keywords:
- monitoring
- prometheus
maintainers:
- email: gianrubio@gmail.com
  name: gianrubio
name: prometheus
type: application
version: 28.14.1
```

### Helm's Value Proposition

Helm solves three core problems with raw Kubernetes manifests:

**Templating** — instead of duplicating YAML for dev/staging/prod, you write one chart and override only what changes. A single `values-prod.yaml` is enough to switch replicas, image tags, and resource limits.

**Versioning & rollback** — every `helm install` / `helm upgrade` creates a numbered revision stored as a Kubernetes Secret. Rolling back is `helm rollback <release> <revision>` — no manual YAML editing.

**Lifecycle hooks** — pre-install and post-install Jobs let you run database migrations or smoke tests at exactly the right moment in the deployment lifecycle, without external CI scripts.

---

## Task 2 — Chart Structure

```
k8s/python-app/
├── Chart.yaml                   # Chart metadata (name, version, appVersion)
├── values.yaml                  # Default configuration values
├── values-dev.yaml              # Development overrides
├── values-prod.yaml             # Production overrides
└── templates/
    ├── _helpers.tpl             # Reusable named templates (DRY helpers)
    ├── deployment.yaml          # Deployment manifest (fully templated)
    ├── service.yaml             # Service manifest (templated type & ports)
    ├── NOTES.txt                # Post-install instructions shown to user
    └── hooks/
        ├── pre-install-job.yaml # Hook: runs before resources are created
        └── post-install-job.yaml# Hook: runs after all resources are ready
```

### Key Template Files

| File | Purpose |
|---|---|
| `Chart.yaml` | Declares chart name, version (`0.1.0`), and appVersion (`1.0.0`) |
| `values.yaml` | Single source of truth for all defaults — nothing is hardcoded in templates |
| `_helpers.tpl` | Defines `python-app.fullname`, `python-app.labels`, `python-app.selectorLabels` — reused in every template |
| `deployment.yaml` | Converts static Lab 9 `deployment.yml` into a fully parametric template |
| `service.yaml` | Handles both NodePort (with optional `nodePort:`) and LoadBalancer transparently |
| `NOTES.txt` | Tells the user how to access the app right after `helm install` |

### Values Organization Strategy

Values are grouped into logical sections:

```yaml
replicaCount: 3          # top-level scalar — changed most often

image:                   # image coordinates grouped together
  repository: aliyasag/devops-info-service
  tag: "latest"

service:                 # all service fields in one block
  type: NodePort
  port: 80
  targetPort: 5000
  nodePort: 30080

resources:               # requests and limits side by side for easy comparison
  requests: ...
  limits: ...

livenessProbe:           # full probe config exposed — never commented out
readinessProbe:          # same for readiness
```

### Chart Lint

```
PS C:\Users\neia_\Desktop\DevOps\DevOps-Core-Course\k8s> helm lint python-app
==> Linting python-app
[INFO] Chart.yaml: icon is recommended

1 chart(s) linted, 0 chart(s) failed
```

### Installation (default values)

```
PS C:\Users\neia_\Desktop\DevOps\DevOps-Core-Course\k8s> helm install myrelease python-app --set image.tag=latest
NAME: myrelease
LAST DEPLOYED: Wed Apr  1 23:38:49 2026
NAMESPACE: default
STATUS: deployed
REVISION: 1
DESCRIPTION: Install complete
```

---

## Task 3 — Multi-Environment Configuration

### Environment Differences

| Parameter | Dev | Prod |
|---|---|---|
| `replicaCount` | 1 | 5 |
| `image.pullPolicy` | `Always` | `IfNotPresent` |
| `service.type` | `NodePort` | `LoadBalancer` |
| `resources.limits.cpu` | `100m` | `500m` |
| `resources.limits.memory` | `128Mi` | `512Mi` |
| `livenessProbe.initialDelaySeconds` | 5 | 30 |
| `ENV` env var | `development` | `production` |

**Design decision:** `values-dev.yaml` and `values-prod.yaml` only contain keys that differ from `values.yaml`. Helm merges them at install time — unspecified keys keep their defaults.

### Installation — Dev Environment

```
PS C:\Users\neia_\Desktop\DevOps\DevOps-Core-Course> helm install python-app-dev k8s/python-app -f k8s/python-app/values-dev.yaml
NAME: python-app-dev
LAST DEPLOYED: Wed Apr  1 23:27:26 2026
NAMESPACE: default
STATUS: deployed
REVISION: 1
DESCRIPTION: Install complete
TEST SUITE: None
NOTES:
Thank you for installing python-app v1.0.0!
Release name : python-app-dev
Namespace    : default
Replicas     : 1

To access the application:
  minikube service python-app-dev-python-app-service --url
```

### Installation — Prod Environment

```
PS C:\Users\neia_\Desktop\DevOps\DevOps-Core-Course> helm install python-app-prod k8s/python-app -f k8s/python-app/values-prod.yaml
NAME: python-app-prod
LAST DEPLOYED: Wed Apr  1 23:28:06 2026
NAMESPACE: default
STATUS: deployed
REVISION: 1
DESCRIPTION: Install complete
TEST SUITE: None
NOTES:
Thank you for installing python-app v1.0.0!
Release name : python-app-prod
Namespace    : default
Replicas     : 5

To access the application:
  kubectl get svc python-app-prod-python-app-service -w
  # Use the EXTERNAL-IP once it is assigned
```

### Upgrade prod

```
PS C:\Users\neia_\Desktop\DevOps\DevOps-Core-Course> helm upgrade python-app-prod k8s/python-app -f k8s/python-app/values-prod.yaml
Release "python-app-prod" has been upgraded. Happy Helming!
NAME: python-app-prod
LAST DEPLOYED: Wed Apr  1 23:34:17 2026
NAMESPACE: default
STATUS: deployed
REVISION: 2
DESCRIPTION: Upgrade complete
```

### Both Environments Running

```
PS C:\Users\neia_\Desktop\DevOps\DevOps-Core-Course> helm list
NAME            NAMESPACE  REVISION  UPDATED                           STATUS    CHART             APP VERSION
myrelease       default    1         2026-04-01 23:38:49 +0300 MSK     deployed  python-app-0.1.0  1.0.0
python-app-dev  default    1         2026-04-01 23:27:26 +0300 MSK     deployed  python-app-0.1.0  1.0.0
python-app-prod default    2         2026-04-01 23:34:17 +0300 MSK     deployed  python-app-0.1.0  1.0.0

PS C:\Users\neia_\Desktop\DevOps\DevOps-Core-Course> kubectl get all
NAME                                              READY   STATUS    RESTARTS   AGE
pod/myrelease-python-app-5bf9fc74df-fdnph         1/1     Running   0          3m11s
pod/myrelease-python-app-5bf9fc74df-h9cgk         1/1     Running   0          3m11s
pod/myrelease-python-app-5bf9fc74df-s452w         1/1     Running   0          3m11s
pod/python-app-dev-python-app-5f944f66cf-4hslq    1/1     Running   0          14m
pod/python-app-prod-python-app-59556db5db-g5gxs   1/1     Running   0          8m
pod/python-app-prod-python-app-59556db5db-lvw45   1/1     Running   0          7m48s
pod/python-app-prod-python-app-59556db5db-przbd   1/1     Running   0          7m9s
pod/python-app-prod-python-app-59556db5db-sq5vz   1/1     Running   0          7m22s
pod/python-app-prod-python-app-59556db5db-vtzks   1/1     Running   0          7m35s

NAME                                         TYPE           CLUSTER-IP      EXTERNAL-IP   PORT(S)        AGE
service/kubernetes                           ClusterIP      10.96.0.1       <none>        443/TCP        19m
service/myrelease-python-app-service         NodePort       10.107.226.67   <none>        80:30080/TCP   3m12s
service/python-app-dev-python-app-service    NodePort       10.99.121.56    <none>        80:30081/TCP   14m
service/python-app-prod-python-app-service   LoadBalancer   10.101.178.14   <pending>     80:30568/TCP   14m

NAME                                         READY   UP-TO-DATE   AVAILABLE   AGE
deployment.apps/myrelease-python-app         3/3     3            3           3m11s
deployment.apps/python-app-dev-python-app    1/1     1            1           14m
deployment.apps/python-app-prod-python-app   5/5     5            5           14m

NAME                                                    DESIRED   CURRENT   READY   AGE
replicaset.apps/myrelease-python-app-5bf9fc74df         3         3         3       3m11s
replicaset.apps/python-app-dev-python-app-5f944f66cf    1         1         1       14m
replicaset.apps/python-app-prod-python-app-59556db5db   5         5         5       8m
replicaset.apps/python-app-prod-python-app-974479b      0         0         0       14m
```

Dev has **1 replica** (NodePort :30081), prod has **5 replicas** (LoadBalancer) ✅

---

## Task 4 — Hook Implementation

### What Hooks Were Implemented

| Hook | File | Weight | Delete Policy |
|---|---|---|---|
| `pre-install` | `templates/hooks/pre-install-job.yaml` | `-5` | `hook-succeeded` |
| `post-install` | `templates/hooks/post-install-job.yaml` | `5` | `hook-succeeded` |

### Hook Execution Order

```
helm install
    │
    ▼
[pre-install hook — weight -5]
  Job: myrelease-python-app-pre-install
  → Simulates DB migration / environment readiness check
  → Sleeps 5s, prints confirmation
  → Job deleted automatically (hook-succeeded policy)
    │
    ▼
[Chart resources created]
  Deployment, Service, ReplicaSet, Pods
    │
    ▼
[post-install hook — weight 5]
  Job: myrelease-python-app-post-install
  → Simulates smoke test + deployment notification
  → Sleeps 10s, prints confirmation
  → Job deleted automatically (hook-succeeded policy)
    │
    ▼
helm install completes ✅
```

**Why weights matter:** Lower weight = earlier execution. Weight `-5` guarantees the pre-install check always runs before any post-install logic.

### Hook Execution Evidence

**Pre-install hook** — caught running live before chart resources were created:

```
PS C:\Users\neia_\Desktop\DevOps\DevOps-Core-Course> kubectl get pods
NAME                                          READY   STATUS    RESTARTS   AGE
myrelease-python-app-pre-install-zqrhf        1/1     Running   0          11s   ← hook running
python-app-dev-python-app-5f944f66cf-4hslq    1/1     Running   0          11m
python-app-prod-python-app-59556db5db-g5gxs   1/1     Running   0          4m44s
```

While the pre-install hook was running, the Deployment and Service did not yet exist — Helm waited for the hook to complete successfully before creating chart resources. This confirms correct lifecycle behavior.

**Post-install hook logs** — captured before deletion:

```
PS C:\Users\neia_\Desktop\DevOps\DevOps-Core-Course\k8s> kubectl logs job/myrelease-python-app-post-install
=== Post-install hook started ===
Release   : myrelease
Namespace : default
Running smoke test — waiting for application to be ready...
Smoke test passed — python-app is healthy.
Sending deployment notification (simulated)...
=== Post-install hook completed ===
```

**After completion — both hooks deleted automatically:**

```
PS C:\Users\neia_\Desktop\DevOps\DevOps-Core-Course\k8s> kubectl get jobs
No resources found in default namespace.
```

The `hook-succeeded` deletion policy worked correctly — both Jobs were removed immediately after successful completion ✅

Note: `job/myrelease-python-app-pre-install` logs were not captured because the hook completed and was deleted before the log command was run — this is expected behavior and confirms the deletion policy is working.

### Deletion Policy: `hook-succeeded`

`hook-succeeded` means the Job and its Pod are automatically deleted once the container exits with code 0. This keeps the cluster clean — no stale Job objects accumulate across upgrades.

Alternative policies:
- `before-hook-creation` — deletes the previous Job before creating a new one (useful for upgrades)
- `hook-failed` — deletes only on failure (useful for debugging)

---

## Task 5 — Installation Evidence

### Application Accessibility

```
PS C:\Users\neia_\Desktop\DevOps\DevOps-Core-Course\k8s> minikube service myrelease-python-app-service --url
http://127.0.0.1:49280
❗  Because you are using a Docker driver on windows, the terminal needs to be open to run it.
```

Application responded at `http://127.0.0.1:49280` ✅

---

## Operations Reference

### Install

```bash
# Default
helm install myrelease k8s/python-app --set image.tag=latest

# Dev environment
helm install python-app-dev k8s/python-app -f k8s/python-app/values-dev.yaml

# Prod environment
helm install python-app-prod k8s/python-app -f k8s/python-app/values-prod.yaml
```

### Upgrade

```bash
helm upgrade python-app-prod k8s/python-app -f k8s/python-app/values-prod.yaml
```

```
Release "python-app-prod" has been upgraded. Happy Helming!
STATUS: deployed
REVISION: 2
DESCRIPTION: Upgrade complete
```

### Rollback

```
PS C:\Users\neia_\Desktop\DevOps\DevOps-Core-Course> helm history myrelease
REVISION  UPDATED                  STATUS    CHART             APP VERSION  DESCRIPTION
1         Wed Apr  1 23:38:49 2026 deployed  python-app-0.1.0  1.0.0        Install complete

PS C:\Users\neia_\Desktop\DevOps\DevOps-Core-Course> helm rollback myrelease 1
Rollback was a success! Happy Helming!

PS C:\Users\neia_\Desktop\DevOps\DevOps-Core-Course> kubectl rollout status deployment/myrelease-python-app
deployment "myrelease-python-app" successfully rolled out
```

### Uninstall

```
PS C:\Users\neia_\Desktop\DevOps\DevOps-Core-Course> helm uninstall myrelease
release "myrelease" uninstalled

PS C:\Users\neia_\Desktop\DevOps\DevOps-Core-Course> kubectl get all
NAME                                              READY   STATUS        RESTARTS   AGE
pod/myrelease-python-app-5bf9fc74df-fdnph         1/1     Terminating   0          3m14s
pod/myrelease-python-app-5bf9fc74df-h9cgk         1/1     Terminating   0          3m14s
pod/myrelease-python-app-5bf9fc74df-s452w         1/1     Terminating   0          3m14s
pod/python-app-dev-python-app-5f944f66cf-4hslq    1/1     Running       0          14m
pod/python-app-prod-python-app-59556db5db-g5gxs   1/1     Running       0          8m3s

NAME                                         TYPE           CLUSTER-IP      EXTERNAL-IP   PORT(S)        AGE
service/python-app-dev-python-app-service    NodePort       10.99.121.56    <none>        80:30081/TCP   14m
service/python-app-prod-python-app-service   LoadBalancer   10.101.178.14   <pending>     80:30568/TCP   14m
```

Myrelease pods are Terminating — all resources cleaned up by `helm uninstall` ✅

### Inspect Running Release

```bash
helm get values myrelease          # show effective values
helm get manifest myrelease        # show rendered YAML currently deployed
helm get all myrelease             # full info dump
```