# Helm Chart Documentation — devops-info-service

## Task 1 — Helm Fundamentals

### Installation

Helm was installed using the official installation script and placed in `~/bin/`:

```
$ helm version
version.BuildInfo{Version:"v3.20.1", GitCommit:"a2369ca71c0ef633bf6e4fccd66d634eb379b371", GitTreeState:"clean", GoVersion:"go1.25.8"}
```

### Repository Setup

```bash
# Add Prometheus Community repository
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
# "prometheus-community" has been added to your repositories

# Search public hub
helm search hub nginx --max-col-width 60
# URL                                                           CHART VERSION  APP VERSION
# https://artifacthub.io/packages/helm/bitnami-aks/nginx        13.2.12        1.23.2
# ...
```

### Exploring a Public Chart

```bash
$ helm show chart oci://registry-1.docker.io/bitnamicharts/nginx
Pulled: registry-1.docker.io/bitnamicharts/nginx:22.6.10
Digest: sha256:d5095131fcc79a343c83f7f826fe0e7f70a797bc9c8f47ed8e9e0cff5c4cf62c
apiVersion: v2
appVersion: 1.29.7
dependencies:
  - name: common
    ...
description: NGINX Open Source is a web server...
name: nginx
type: application
version: 22.6.10
```

### Why Helm?

| Problem (raw K8s) | Helm Solution |
|---|---|
| Duplicate YAML across envs | Single chart + values files |
| No versioning of "app state" | Releases with history and rollback |
| Hard-coded values | `values.yaml` with `--set` overrides |
| Manual lifecycle management | Hooks for pre/post install/upgrade/delete |
| Complex multi-service apps | Dependency management via `Chart.yaml` |

Helm is the industry-standard package manager for Kubernetes — it does for K8s what `apt`/`yum` does for Linux.

---

## Task 2 — Chart Structure

### Directory Layout

```
k8s/devops-info-service/
├── Chart.yaml                      # Chart metadata (name, version, appVersion)
├── values.yaml                     # Default configuration values
├── values-dev.yaml                 # Development overrides
├── values-prod.yaml                # Production overrides
└── templates/
    ├── _helpers.tpl                # Reusable named templates (DRY)
    ├── deployment.yaml             # Deployment manifest (templated)
    ├── service.yaml                # Service manifest (templated)
    ├── NOTES.txt                   # Post-install usage notes
    └── hooks/
        ├── pre-install-job.yaml    # Pre-install/upgrade lifecycle hook
        └── post-install-job.yaml   # Post-install/upgrade lifecycle hook
```

### Key Template Files

| File | Purpose |
|---|---|
| `Chart.yaml` | Chart identity: name, version, appVersion, maintainers |
| `values.yaml` | All tunable parameters with sensible defaults |
| `_helpers.tpl` | Named templates for fullname, labels, selectorLabels — used in every resource |
| `deployment.yaml` | Templated Deployment with probes, resources, env vars |
| `service.yaml` | Templated Service with conditional NodePort |
| `hooks/pre-install-job.yaml` | Validation job that runs before install/upgrade |
| `hooks/post-install-job.yaml` | Smoke test job that runs after install/upgrade |

### Values Organisation

Values are grouped into logical sections:

```yaml
# Replica count
replicaCount: 3

# Image config
image:
  repository: lanebo1/devops-info-service
  tag: "latest"
  pullPolicy: IfNotPresent

# Service exposure
service:
  type: NodePort
  port: 80
  targetPort: 5000
  nodePort: 30080

# Resource constraints
resources:
  limits: { cpu: 200m, memory: 256Mi }
  requests: { cpu: 100m, memory: 128Mi }

# Health checks (always enabled, never commented out)
livenessProbe:
  httpGet: { path: /health, port: 5000 }
  initialDelaySeconds: 15
  ...

readinessProbe:
  httpGet: { path: /health, port: 5000 }
  initialDelaySeconds: 5
  ...

# Hook configuration
hooks:
  preInstall:  { enabled: true, image: busybox, weight: "-5" }
  postInstall: { enabled: true, image: busybox, weight: "5"  }
```

### Helper Templates

`_helpers.tpl` defines three named templates used by all resources:

```
devops-info-service.name          — Chart name (truncated to 63 chars)
devops-info-service.fullname      — Release-name + chart-name combination
devops-info-service.chart         — Chart name+version (used in helm.sh/chart label)
devops-info-service.labels        — Full Kubernetes recommended label set
devops-info-service.selectorLabels — Stable selector labels for Deployment/Service
```

### Chart Lint Output

```
$ helm lint k8s/devops-info-service
==> Linting /home/lanebo1/DevOps-Core-Course/k8s/devops-info-service
[INFO] Chart.yaml: icon is recommended

1 chart(s) linted, 0 chart(s) failed

$ helm lint k8s/devops-info-service -f k8s/devops-info-service/values-dev.yaml
==> Linting /home/lanebo1/DevOps-Core-Course/k8s/devops-info-service
[INFO] Chart.yaml: icon is recommended

1 chart(s) linted, 0 chart(s) failed

$ helm lint k8s/devops-info-service -f k8s/devops-info-service/values-prod.yaml
==> Linting /home/lanebo1/DevOps-Core-Course/k8s/devops-info-service
[INFO] Chart.yaml: icon is recommended

1 chart(s) linted, 0 chart(s) failed
```

### helm template Output (default values)

```yaml
$ helm template test-release k8s/devops-info-service
---
# Source: devops-info-service/templates/service.yaml
apiVersion: v1
kind: Service
metadata:
  name: test-release-devops-info-service
  labels:
    helm.sh/chart: devops-info-service-0.1.0
    app.kubernetes.io/name: devops-info-service
    app.kubernetes.io/instance: test-release
    app.kubernetes.io/version: "1.0.0"
    app.kubernetes.io/managed-by: Helm
spec:
  type: NodePort
  selector:
    app.kubernetes.io/name: devops-info-service
    app.kubernetes.io/instance: test-release
  ports:
    - protocol: TCP
      port: 80
      targetPort: 5000
      nodePort: 30080
---
# Source: devops-info-service/templates/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: test-release-devops-info-service
  labels:
    helm.sh/chart: devops-info-service-0.1.0
    app.kubernetes.io/name: devops-info-service
    app.kubernetes.io/instance: test-release
    app.kubernetes.io/version: "1.0.0"
    app.kubernetes.io/managed-by: Helm
spec:
  replicas: 3
  selector:
    matchLabels:
      app.kubernetes.io/name: devops-info-service
      app.kubernetes.io/instance: test-release
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 1
      maxUnavailable: 0
  template:
    ...
    spec:
      securityContext:
        fsGroup: 999
        runAsGroup: 999
        runAsUser: 999
      containers:
        - name: devops-info-service
          image: "lanebo1/devops-info-service:latest"
          ...
          livenessProbe:
            httpGet:
              path: /health
              port: 5000
            initialDelaySeconds: 15
            periodSeconds: 10
            timeoutSeconds: 5
            failureThreshold: 3
          readinessProbe:
            httpGet:
              path: /health
              port: 5000
            initialDelaySeconds: 5
            periodSeconds: 5
            timeoutSeconds: 3
            failureThreshold: 3
```

---

## Task 3 — Multi-Environment Support

### Environment Differences

| Parameter | Dev (`values-dev.yaml`) | Prod (`values-prod.yaml`) |
|---|---|---|
| `replicaCount` | 1 | 5 |
| `image.tag` | `latest` | `latest` (pin to a digest in real prod) |
| `image.pullPolicy` | `Always` | `IfNotPresent` |
| `service.type` | `NodePort` (30080) | `LoadBalancer` |
| `resources.limits.cpu` | `100m` | `500m` |
| `resources.limits.memory` | `128Mi` | `512Mi` |
| `resources.requests.cpu` | `50m` | `200m` |
| `resources.requests.memory` | `64Mi` | `256Mi` |
| `livenessProbe.initialDelaySeconds` | `5` | `30` |
| `readinessProbe.initialDelaySeconds` | `3` | `10` |

### Usage

```bash
# Development
helm install myapp-dev k8s/devops-info-service -f k8s/devops-info-service/values-dev.yaml

# Production
helm install myapp-prod k8s/devops-info-service -f k8s/devops-info-service/values-prod.yaml

# Override a single value at install time
helm install myapp k8s/devops-info-service --set replicaCount=2
```

### Dev → Prod Upgrade Demonstration

```bash
# Step 1: Install with dev values (1 replica, NodePort, relaxed resources)
$ helm install devops-dev k8s/devops-info-service -f k8s/devops-info-service/values-dev.yaml
NAME: devops-dev
STATUS: deployed
REVISION: 1
Replicas: 1

# Step 2: Upgrade to prod values (5 replicas, LoadBalancer, proper resources)
$ helm upgrade devops-dev k8s/devops-info-service -f k8s/devops-info-service/values-prod.yaml
Release "devops-dev" has been upgraded. Happy Helming!
NAME: devops-dev
STATUS: deployed
REVISION: 2
Replicas: 5

# Step 3: Verify rolling update progressed correctly
$ kubectl rollout status deployment/devops-dev-devops-info-service
Waiting for deployment "devops-dev-devops-info-service" rollout to finish: 2 out of 5 new replicas have been updated...
...
deployment "devops-dev-devops-info-service" successfully rolled out
```

---

## Task 4 — Hook Implementation

### Hook Types Implemented

| Hook | Type | Weight | Deletion Policy | Purpose |
|---|---|---|---|---|
| `pre-install-job.yaml` | `pre-install`, `pre-upgrade` | `-5` | `before-hook-creation,hook-succeeded` | Validate environment readiness before resources are created |
| `post-install-job.yaml` | `post-install`, `post-upgrade` | `5` | `before-hook-creation,hook-succeeded` | Run smoke tests after deployment is live |

### Hook Annotations

```yaml
annotations:
  "helm.sh/hook": pre-install,pre-upgrade
  "helm.sh/hook-weight": "-5"
  "helm.sh/hook-delete-policy": before-hook-creation,hook-succeeded
```

### Execution Order

```
helm install/upgrade
    │
    ├── 1. Pre-install hook  (weight -5) — validation job runs & completes
    │        deleted automatically on success (hook-succeeded policy)
    │
    ├── 2. Main resources installed (Deployment + Service)
    │
    └── 3. Post-install hook (weight +5) — smoke test job runs & completes
             deleted automatically on success (hook-succeeded policy)
```

### Deletion Policy Explanation

- **`before-hook-creation`** — if a previous hook Job with the same name exists (from a prior failed attempt), it is deleted before the new hook runs. This prevents "already exists" errors on re-install.
- **`hook-succeeded`** — the Job and its Pods are automatically deleted after successful completion, keeping the namespace clean.

### Hook Execution Evidence

The pre-install job appeared immediately after `helm install` and was deleted after success:

```bash
$ kubectl get jobs -n hook-test -w
NAME                                        STATUS    COMPLETIONS   DURATION   AGE
hook-test-devops-info-service-pre-install   Running   0/1           3s         3s
# → deleted after completion (hook-succeeded policy)

# After installation completed:
$ kubectl get jobs
No resources found in default namespace.
```

Hooks rendered by `helm template` (confirming correct annotations):

```bash
$ helm install --dry-run --debug test-release k8s/devops-info-service | grep -A 20 "hook"
hooks:
# Source: devops-info-service/templates/hooks/post-install-job.yaml
  name: "test-release-devops-info-service-post-install"
    "helm.sh/hook": post-install,post-upgrade
# Source: devops-info-service/templates/hooks/pre-install-job.yaml
  name: "test-release-devops-info-service-pre-install"
    "helm.sh/hook": pre-install,pre-upgrade
```

---

## Task 5 — Installation Evidence

### helm list

```
$ helm list
NAME       NAMESPACE  REVISION  UPDATED                                 STATUS    CHART                     APP VERSION
devops-dev default    4         2026-04-02 22:10:43.654104091 +0300 MSK deployed  devops-info-service-0.1.0 1.0.0
```

### helm history

```
$ helm history devops-dev
REVISION  UPDATED                   STATUS      CHART                     APP VERSION  DESCRIPTION
1         Thu Apr  2 22:05:48 2026  superseded  devops-info-service-0.1.0  1.0.0       Install complete
2         Thu Apr  2 22:06:40 2026  superseded  devops-info-service-0.1.0  1.0.0       Upgrade complete
3         Thu Apr  2 22:10:33 2026  superseded  devops-info-service-0.1.0  1.0.0       Rollback to 1
4         Thu Apr  2 22:10:43 2026  deployed    devops-info-service-0.1.0  1.0.0       Upgrade complete
```

### kubectl get all (prod — 5 replicas, LoadBalancer)

```
$ kubectl get all
NAME                                                READY   STATUS    RESTARTS   AGE
pod/devops-dev-devops-info-service-d5957d88-7fqcw   1/1     Running   0          66s
pod/devops-dev-devops-info-service-d5957d88-bwgp2   1/1     Running   0          54s
pod/devops-dev-devops-info-service-d5957d88-nz9dx   1/1     Running   0          41s
pod/devops-dev-devops-info-service-d5957d88-pvnbx   1/1     Running   0          17s
pod/devops-dev-devops-info-service-d5957d88-zcptc   1/1     Running   0          29s

NAME                                     TYPE           CLUSTER-IP     EXTERNAL-IP   PORT(S)        AGE
service/devops-dev-devops-info-service   LoadBalancer   10.108.6.147   <pending>     80:30080/TCP   6m2s
service/kubernetes                       ClusterIP      10.96.0.1      <none>        443/TCP        7d

NAME                                             READY   UP-TO-DATE   AVAILABLE   AGE
deployment.apps/devops-dev-devops-info-service   5/5     5            5           6m2s

NAME                                                        DESIRED   CURRENT   READY   AGE
replicaset.apps/devops-dev-devops-info-service-76744c57c5   0         0         0       6m2s
replicaset.apps/devops-dev-devops-info-service-d5957d88     5         5         5       66s
```

### Application Health Check

```bash
$ curl http://192.168.49.2:30080/health
{"status":"healthy","timestamp":"2026-04-02T19:06:35.090078+00:00","uptime_seconds":17}
```

### kubectl get jobs (after install — hooks cleaned up)

```
$ kubectl get jobs
No resources found in default namespace.
```

Confirms `hook-delete-policy: hook-succeeded` worked as expected — both hook Jobs were deleted after successful completion.

---

## Operations

### Install

```bash
# Default values
helm install myrelease k8s/devops-info-service

# Development environment
helm install myapp-dev k8s/devops-info-service -f k8s/devops-info-service/values-dev.yaml

# Production environment
helm install myapp-prod k8s/devops-info-service -f k8s/devops-info-service/values-prod.yaml

# Override single value
helm install myapp k8s/devops-info-service --set replicaCount=2
```

### Upgrade

```bash
# Upgrade to production config
helm upgrade myapp-dev k8s/devops-info-service -f k8s/devops-info-service/values-prod.yaml

# Upgrade with specific value override
helm upgrade myapp k8s/devops-info-service --set image.tag=v2.0.0

# Verify upgrade
helm get values myapp
kubectl rollout status deployment/myapp-devops-info-service
```

### Rollback

```bash
# View release history
helm history myapp

# Rollback to previous revision
helm rollback myapp

# Rollback to specific revision
helm rollback myapp 1

# Verify rollback
kubectl get pods
helm list
```

### Uninstall

```bash
helm uninstall myapp
# Removes all Kubernetes resources managed by the release
```

---

## Testing & Validation

### helm lint

```
$ helm lint k8s/devops-info-service
==> Linting /home/lanebo1/DevOps-Core-Course/k8s/devops-info-service
[INFO] Chart.yaml: icon is recommended

1 chart(s) linted, 0 chart(s) failed
```

### helm template verification

```bash
# Render templates locally (no cluster required)
helm template test-release k8s/devops-info-service

# Render with dev values
helm template test-release k8s/devops-info-service -f k8s/devops-info-service/values-dev.yaml

# Render with prod values
helm template test-release k8s/devops-info-service -f k8s/devops-info-service/values-prod.yaml
```

### Dry-run

```bash
$ helm install --dry-run --debug test-release k8s/devops-info-service
install.go:242: [debug] CHART PATH: .../k8s/devops-info-service
NAME: test-release
NAMESPACE: default
STATUS: pending-install
hooks:
  # pre-install and post-install hooks visible in output
MANIFEST:
  # Full rendered manifests shown without applying to cluster
```

### Health check verification

```bash
$ curl http://192.168.49.2:30080/health
{"status":"healthy","timestamp":"2026-04-02T19:06:35.090078+00:00","uptime_seconds":17}
```
