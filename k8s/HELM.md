# Helm Package Manager — Lab 10

## Task 1 — Helm Fundamentals

### Installation

I installed Helm 4 directly from the apt package manager and verified the version:

```
$ sudo apt install helm
$ helm version
version.BuildInfo{Version:"v4.1.3", GitCommit:"c94d381b03be117e7e57908edbf642104e00eb8f", GitTreeState:"clean", GoVersion:"go1.26.1", KubeClientVersion:"v1.35"}
```

Helm 4 is the current major release (November 2025). It keeps full backward compatibility with Helm 3 charts (`apiVersion: v2`) and no longer requires Tiller — it talks to the Kubernetes API directly.

### Exploring a Public Chart

I added the Prometheus Community repository and inspected its chart metadata:

```
$ helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
$ helm repo update
$ helm show chart prometheus-community/prometheus
annotations:
  artifacthub.io/license: Apache-2.0
apiVersion: v2
appVersion: v3.11.0
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
kubeVersion: '>=1.19.0-0'
maintainers:
- email: gianrubio@gmail.com
  name: gianrubio
name: prometheus
type: application
version: 28.15.0
```

Inspecting this chart showed how real-world charts manage multi-component applications via sub-chart dependencies and conditions.

### Why Helm Matters

Without Helm every environment requires its own copy of manifests with values edited by hand. Helm solves this with Go templating: one chart can be installed into dev with 1 replica and relaxed resource limits, or into prod with 5 replicas and tighter limits, by just passing a different values file. It also provides versioned rollbacks and lifecycle hooks for free.

---

## 1. Chart Overview

### Chart Structure

I created the chart in `k8s/testiks/` using `helm create k8s/testiks` as a scaffold, then replaced the generated templates with ones based on the Lab 9 manifests.

```
k8s/testiks/
├── Chart.yaml                          # chart metadata
├── values.yaml                         # default configuration
├── values-dev.yaml                     # development overrides
├── values-prod.yaml                    # production overrides
└── templates/
    ├── _helpers.tpl                    # named template definitions
    ├── deployment.yaml                 # Deployment resource
    ├── service.yaml                    # Service resource
    ├── NOTES.txt                       # post-install usage message
    └── hooks/
        ├── pre-install-job.yaml        # pre-install hook Job
        └── post-install-job.yaml       # post-install hook Job
```

### Key Template Files

**`Chart.yaml`** — chart metadata with `apiVersion: v2` (Helm 3+), semantic version, and app version:

```yaml
apiVersion: v2
name: testiks
description: Helm chart for py web application
type: application
version: 0.1.0
appVersion: "1.0.0"
keywords:
  - python
  - web
maintainers:
  - name: CacucoH
    email: dfffd7800@gmail.com
```

**`_helpers.tpl`** — named templates called with `include` across all resources:
- `testiks.fullname` — `<release>-<chart>`, truncated to 63 characters
- `testiks.labels` — full set of `app.kubernetes.io/*` labels
- `testiks.selectorLabels` — subset used in `matchLabels` and pod labels

**`deployment.yaml`** — all per-environment values (replicas, image, resources, probe timing) are read from `.Values` via Go templates.

**`service.yaml`** — `type`, `port`, and `nodePort` all come from `.Values.service`; `nodePort` is only emitted when `service.type == NodePort`.

**`hooks/pre-install-job.yaml`** and **`hooks/post-install-job.yaml`** — Kubernetes Jobs managed by Helm outside the normal release resources.

### Values Organisation Strategy

Values are grouped by concern rather than by Kubernetes kind, making environment overrides intuitive:

```yaml
replicaCount: 3

image:
  repository: cacucoh/testiks
  tag: "1.0.0"
  pullPolicy: IfNotPresent

containerPort: 5000

service:
  type: NodePort
  port: 80
  targetPort: 5000
  nodePort: 30081

resources:
  requests:
    cpu: 100m
    memory: 128Mi
  limits:
    cpu: 250m
    memory: 256Mi

livenessProbe:
  httpGet:
    path: /health
    port: 5000
  initialDelaySeconds: 15
  periodSeconds: 10
  timeoutSeconds: 2
  failureThreshold: 3

readinessProbe:
  httpGet:
    path: /health
    port: 5000
  initialDelaySeconds: 5
  periodSeconds: 5
  timeoutSeconds: 2
  failureThreshold: 3

hooks:
  deleteAfterSuccess: true
```

---

## 2. Configuration Guide

### Important Values

| Value | Default | Purpose |
|---|---|---|
| `replicaCount` | `3` | Number of pod replicas |
| `image.repository` | `cacucoh/testiks` | Container image name |
| `image.tag` | `1.0.0` | Image tag; falls back to `appVersion` |
| `image.pullPolicy` | `IfNotPresent` | Pull policy |
| `containerPort` | `5000` | Port the application listens on |
| `service.type` | `NodePort` | `NodePort` for local, `LoadBalancer` for cloud |
| `service.port` | `80` | Service port |
| `service.nodePort` | `30081` | Fixed NodePort (only applied when type is NodePort) |
| `resources.requests.*` | see above | Scheduler resource requests |
| `resources.limits.*` | see above | Runtime resource caps |
| `livenessProbe.*` | see above | Liveness check path, port, and timing |
| `readinessProbe.*` | see above | Readiness check path, port, and timing |
| `hooks.deleteAfterSuccess` | `true` | Delete hook Jobs after successful completion |

### Environment Customization

**`values-dev.yaml`** — minimal footprint, fixed NodePort, `latest` tag:

```yaml
replicaCount: 1

image:
  tag: "latest"
  pullPolicy: Always

service:
  type: NodePort
  nodePort: 30081

resources:
  requests:
    cpu: 50m
    memory: 64Mi
  limits:
    cpu: 100m
    memory: 128Mi

livenessProbe:
  initialDelaySeconds: 5
  periodSeconds: 10

readinessProbe:
  initialDelaySeconds: 3
  periodSeconds: 5
```

**`values-prod.yaml`** — high-availability, LoadBalancer, pinned tag:

```yaml
replicaCount: 5

image:
  tag: "1.0.0"
  pullPolicy: IfNotPresent

service:
  type: LoadBalancer

resources:
  requests:
    cpu: 200m
    memory: 256Mi
  limits:
    cpu: 500m
    memory: 512Mi

livenessProbe:
  initialDelaySeconds: 30
  periodSeconds: 5

readinessProbe:
  initialDelaySeconds: 10
  periodSeconds: 3
```

### Example Installations

```bash
# Development
helm install dev ./k8s/testiks \
  -f k8s/testiks/values-dev.yaml \
  --namespace lab10-dev --create-namespace

# Production
helm install prod ./k8s/testiks \
  -f k8s/testiks/values-prod.yaml \
  --namespace lab10-prod --create-namespace

# Single value override without a file
helm install dev ./k8s/testiks \
  -f k8s/testiks/values-dev.yaml \
  --set replicaCount=2 \
  --namespace lab10-dev --create-namespace
```

---

## 3. Hook Implementation

### What I Implemented and Why

**Pre-install hook** (`templates/hooks/pre-install-job.yaml`) — a `busybox` Job that runs before any chart resources are created. It prints the release name and namespace as a validation step. In a real scenario this slot would hold a database schema migration or secrets check.

**Post-install hook** (`templates/hooks/post-install-job.yaml`) — a `curlimages/curl` Job that polls `GET /health` on the newly installed Service with a retry loop (30 attempts, 2 s apart). Helm only marks the release `deployed` after this Job completes successfully, giving an automated smoke test.

### Execution Order and Weights

| Hook | `helm.sh/hook` | Weight | Image |
|---|---|---|---|
| Pre-install | `pre-install` | `-5` | `busybox:1.36` |
| Post-install | `post-install` | `5` | `curlimages/curl:8.5.0` |

Lower weight executes first. Pre-install and post-install are separate lifecycle phases so they cannot race, but explicit weights make the order unambiguous when adding more hooks later.

### Deletion Policies

Both hooks use `"helm.sh/hook-delete-policy": hook-succeeded` by default, which deletes the Job as soon as it completes successfully, keeping the namespace clean. Setting `hooks.deleteAfterSuccess: false` in values switches to `before-hook-creation`, leaving Jobs around for debugging.

---

## 4. Installation Evidence

### Cluster Setup

```text
$ kubectl config current-context
minikube

$ kubectl cluster-info
Kubernetes control plane is running at https://127.0.0.1:65035
CoreDNS is running at https://127.0.0.1:65035/api/v1/namespaces/kube-system/services/kube-dns:dns/proxy

$ kubectl get nodes
NAME       STATUS   ROLES           AGE   VERSION
minikube   Ready    control-plane   8d    v1.32.0
```

### Development Install

```text
$ helm install dev ./k8s/testiks \
  -f k8s/testiks/values-dev.yaml \
  --namespace lab10-dev --create-namespace
NAME: dev
LAST DEPLOYED: Thu Apr  2 19:39:50 2026
NAMESPACE: lab10-dev
STATUS: deployed
REVISION: 1
TEST SUITE: None
NOTES:
1. Get the application URL by running these commands:
  export NODE_PORT=$(kubectl get --namespace lab10-dev -o jsonpath="{.spec.ports[0].nodePort}" services dev-testiks)
  export NODE_IP=$(kubectl get nodes --namespace lab10-dev -o jsonpath="{.items[0].status.addresses[0].address}")
  echo http://$NODE_IP:$NODE_PORT/health

Release: dev
Namespace: lab10-dev
```

```text
$ helm list -n lab10-dev
NAME  NAMESPACE  REVISION  UPDATED                              STATUS    CHART          APP VERSION
dev   lab10-dev  1         2026-04-02 19:39:50.110994 +0300    deployed  testiks-0.1.0  1.0.0
```

```text
$ kubectl get all -n lab10-dev
NAME                                       READY   STATUS    RESTARTS   AGE
pod/dev-testiks-84579bd9bb-8mnkp           1/1     Running   0          62s

NAME                          TYPE       CLUSTER-IP       EXTERNAL-IP   PORT(S)        AGE
service/dev-testiks           NodePort   10.103.117.200   <none>        80:30081/TCP   62s

NAME                              READY   UP-TO-DATE   AVAILABLE   AGE
deployment.apps/dev-testiks       1/1     1            1           62s

NAME                                         DESIRED   CURRENT   READY   AGE
replicaset.apps/dev-testiks-84579bd9bb       1         1         1       62s
```

### Hook Execution

With default `hooks.deleteAfterSuccess: true` the hook Jobs disappear after success. I reinstalled with `hooks.deleteAfterSuccess: false` to inspect them:

```text
$ kubectl get jobs -n lab10-dev
NAME                            STATUS     COMPLETIONS   DURATION   AGE
dev-testiks-pre-install         Complete   1/1           3s         15s
dev-testiks-post-install        Complete   1/1           4s         12s
```

```text
$ kubectl describe job dev-testiks-pre-install -n lab10-dev
Name:             dev-testiks-pre-install
Namespace:        lab10-dev
Annotations:      helm.sh/hook: pre-install
                  helm.sh/hook-weight: -5
Pods Statuses:    0 Active / 1 Succeeded / 0 Failed
Start Time:       Thu, 02 Apr 2026 19:48:28 +0300
Completed At:     Thu, 02 Apr 2026 19:48:31 +0300
Duration:         3s
Events:
  Normal  SuccessfulCreate  22s  job-controller  Created pod: dev-testiks-pre-install-q8xgb
  Normal  Completed         19s  job-controller  Job completed
```

```text
$ kubectl logs -n lab10-dev job/dev-testiks-pre-install
pre-install: release=dev ns=lab10-dev
pre-install OK
```

```text
$ kubectl logs -n lab10-dev job/dev-testiks-post-install
post-install: smoke GET http://dev-testiks.lab10-dev.svc.cluster.local:80/health
{"status":"healthy","timestamp":"2026-04-02T16:48:32.488027+00:00","uptime_seconds":507}
post-install OK
```

### Production Install

```text
$ helm install prod ./k8s/testiks \
  -f k8s/testiks/values-prod.yaml \
  --namespace lab10-prod --create-namespace
NAME: prod
LAST DEPLOYED: Thu Apr  2 19:51:57 2026
NAMESPACE: lab10-prod
STATUS: deployed
REVISION: 1
```

```text
$ kubectl get all -n lab10-prod
NAME                                          READY   STATUS    RESTARTS   AGE
pod/prod-testiks-05dff54df9-b77f4             1/1     Running   0          75s
pod/prod-testiks-05dff54df9-lf2j2             1/1     Running   0          75s
pod/prod-testiks-05dff54df9-q54dt             1/1     Running   0          75s
pod/prod-testiks-05dff54df9-sw95m             1/1     Running   0          75s
pod/prod-testiks-05dff54df9-z45wb             1/1     Running   0          75s

NAME                          TYPE           CLUSTER-IP       EXTERNAL-IP   PORT(S)        AGE
service/prod-testiks          LoadBalancer   10.103.135.218   <pending>     80:31854/TCP   75s

NAME                              READY   UP-TO-DATE   AVAILABLE   AGE
deployment.apps/prod-testiks      5/5     5            5           75s

NAME                                         DESIRED   CURRENT   READY   AGE
replicaset.apps/prod-testiks-05dff54df9      5         5         5       75s
```

`EXTERNAL-IP` stays `<pending>` in minikube — accessed via port-forward:

```bash
kubectl port-forward -n lab10-prod svc/prod-testiks 8080:80
```

---

## 5. Operations

### Install

```bash
# Dev
helm install dev ./k8s/testiks \
  -f k8s/testiks/values-dev.yaml \
  --namespace lab10-dev --create-namespace

# Prod
helm install prod ./k8s/testiks \
  -f k8s/testiks/values-prod.yaml \
  --namespace lab10-prod --create-namespace
```

### Upgrade

```bash
helm upgrade prod ./k8s/testiks \
  -f k8s/testiks/values-prod.yaml \
  --namespace lab10-prod
```

```text
Release "prod" has been upgraded. Happy Helming!
NAME: prod
LAST DEPLOYED: Thu Apr  2 19:54:16 2026
NAMESPACE: lab10-prod
STATUS: deployed
REVISION: 2
```

### Rollback

```bash
helm history dev -n lab10-dev
helm rollback dev 1 -n lab10-dev
```

### Uninstall

```bash
helm uninstall dev  -n lab10-dev
helm uninstall prod -n lab10-prod
```

---

## 6. Testing & Validation

### Lint

```text
$ helm lint ./k8s/testiks
==> Linting ./k8s/testiks
[INFO] Chart.yaml: icon is recommended
1 chart(s) linted, 0 chart(s) failed

$ helm lint ./k8s/testiks -f k8s/testiks/values-dev.yaml
==> Linting ./k8s/testiks
[INFO] Chart.yaml: icon is recommended
1 chart(s) linted, 0 chart(s) failed

$ helm lint ./k8s/testiks -f k8s/testiks/values-prod.yaml
==> Linting ./k8s/testiks
[INFO] Chart.yaml: icon is recommended
1 chart(s) linted, 0 chart(s) failed
```

### Template Rendering

Dev environment (1 replica, `latest` tag, NodePort):

```text
$ helm template dev ./k8s/testiks -f k8s/testiks/values-dev.yaml -n lab10-dev
---
# Source: testiks/templates/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: dev-testiks
  labels:
    helm.sh/chart: testiks-0.1.0
    app.kubernetes.io/name: testiks
    app.kubernetes.io/instance: dev
    app.kubernetes.io/version: "1.0.0"
    app.kubernetes.io/managed-by: Helm
spec:
  replicas: 1
  selector:
    matchLabels:
      app.kubernetes.io/name: testiks
      app.kubernetes.io/instance: dev
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 1
      maxUnavailable: 0
  template:
    metadata:
      labels:
        app.kubernetes.io/name: testiks
        app.kubernetes.io/instance: dev
    spec:
      securityContext:
        seccompProfile:
          type: RuntimeDefault
      containers:
        - name: testiks
          image: "cacucoh/testiks:latest"
          imagePullPolicy: Always
          ports:
            - name: http
              containerPort: 5000
              protocol: TCP
          resources:
            limits:
              cpu: 100m
              memory: 128Mi
            requests:
              cpu: 50m
              memory: 64Mi
          securityContext:
            runAsUser: 10001
            runAsGroup: 10001
            runAsNonRoot: true
            allowPrivilegeEscalation: false
            capabilities:
              drop:
                - ALL
          livenessProbe:
            httpGet:
              path: /health
              port: 5000
            initialDelaySeconds: 5
            periodSeconds: 10
            timeoutSeconds: 2
            failureThreshold: 3
          readinessProbe:
            httpGet:
              path: /health
              port: 5000
            initialDelaySeconds: 3
            periodSeconds: 5
            timeoutSeconds: 2
            failureThreshold: 3
---
# Source: testiks/templates/service.yaml
apiVersion: v1
kind: Service
metadata:
  name: dev-testiks
  labels:
    helm.sh/chart: testiks-0.1.0
    app.kubernetes.io/name: testiks
    app.kubernetes.io/instance: dev
    app.kubernetes.io/version: "1.0.0"
    app.kubernetes.io/managed-by: Helm
spec:
  type: NodePort
  selector:
    app.kubernetes.io/name: testiks
    app.kubernetes.io/instance: dev
  ports:
    - name: http
      protocol: TCP
      port: 80
      targetPort: http
      nodePort: 30081
```

### Dry-Run

```text
$ helm install dev-dryrun ./k8s/testiks \
  -f k8s/testiks/values-dev.yaml \
  --namespace lab-dryrun --create-namespace \
  --dry-run=client
NAME: dev-dryrun
LAST DEPLOYED: Thu Apr  2 19:53:17 2026
NAMESPACE: lab-dryrun
STATUS: pending-install
REVISION: 1
TEST SUITE: None
HOOKS:
---
# Source: testiks/templates/hooks/pre-install-job.yaml
apiVersion: batch/v1
kind: Job
metadata:
  name: "dev-dryrun-testiks-pre-install"
  annotations:
    helm.sh/hook: pre-install
    helm.sh/hook-weight: "-5"
    helm.sh/hook-delete-policy: hook-succeeded
  labels:
    helm.sh/chart: testiks-0.1.0
    app.kubernetes.io/name: testiks
    app.kubernetes.io/instance: dev-dryrun
    app.kubernetes.io/version: "1.0.0"
    app.kubernetes.io/managed-by: Helm
spec:
  backoffLimit: 2
  template:
    metadata:
      labels:
        app.kubernetes.io/managed-by: Helm
        helm.sh/hook: pre-install
    spec:
      restartPolicy: Never
      containers:
        - name: pre-install
          image: busybox:1.36
          command:
            - sh
            - -c
            - |
              set -e
              echo "pre-install: release=dev-dryrun ns=lab-dryrun"
              echo "pre-install OK"
---
# Source: testiks/templates/hooks/post-install-job.yaml
apiVersion: batch/v1
kind: Job
metadata:
  name: "dev-dryrun-testiks-post-install"
  annotations:
    helm.sh/hook: post-install
    helm.sh/hook-weight: "5"
    helm.sh/hook-delete-policy: hook-succeeded
  labels:
    helm.sh/chart: testiks-0.1.0
    app.kubernetes.io/name: testiks
    app.kubernetes.io/instance: dev-dryrun
    app.kubernetes.io/version: "1.0.0"
    app.kubernetes.io/managed-by: Helm
spec:
  backoffLimit: 3
  template:
    metadata:
      labels:
        app.kubernetes.io/managed-by: Helm
        helm.sh/hook: post-install
    spec:
      restartPolicy: Never
      containers:
        - name: post-install
          image: "curlimages/curl:8.5.0"
          command:
            - sh
            - -c
            - |
              set -e
              URL="http://dev-dryrun-testiks.lab-dryrun.svc.cluster.local:80/health"
              echo "post-install: smoke GET $URL"
              i=0
              while [ "$i" -lt 30 ]; do
                if curl -fsS --connect-timeout 3 --max-time 10 "$URL"; then
                  echo "post-install OK"
                  exit 0
                fi
                i=$((i + 1))
                echo "post-install: retry $i/30"
                sleep 2
              done
              echo "post-install: health check failed" >&2
              exit 1
```

### Application Accessibility

```text
$ curl -sS -i localhost:8080/health
HTTP/1.1 200 OK
Server: Werkzeug/3.1.7 Python/3.13.12
Date: Thu, 02 Apr 2026 16:52:58 GMT
Content-Type: application/json
Content-Length: 88
Connection: close

{"status":"healthy","timestamp":"2026-04-02T16:52:58.654555+00:00","uptime_seconds":41}
```
