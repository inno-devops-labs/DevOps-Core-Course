# Lab 10 - Helm Package Manager (Implementation)

## 1. Chart Overview

Helm chart location: `k8s/devops-info`

### Chart structure

```text
k8s/devops-info/
├── Chart.yaml
├── values.yaml
├── values-dev.yaml
├── values-prod.yaml
└── templates/
    ├── _helpers.tpl
    ├── rollout.yaml
    ├── service-preview.yaml
    ├── service.yaml
    ├── hooks-pre-install-job.yaml
    └── hooks-post-install-job.yaml
```

### Key templates

- `templates/rollout.yaml`: Argo Rollouts `Rollout` (Lab 14); canary by default, optional blue-green via `values-bluegreen.yaml`.
- `templates/service-preview.yaml`: preview Service for blue-green only.
- `templates/service.yaml`: production Service (active in blue-green).
- `templates/_helpers.tpl`: reusable naming and label helpers.
- `templates/hooks-pre-install-job.yaml`: pre-install validation hook.
- `templates/hooks-post-install-job.yaml`: post-install smoke-test hook.

### Values organization strategy

- Base defaults in `values.yaml` (safe common configuration).
- Environment overrides:
  - `values-dev.yaml`: lighter resources, `replicaCount: 1`, `NodePort`, `latest` image tag.
  - `values-prod.yaml`: stronger resources, `replicaCount: 3`, `LoadBalancer`, pinned tag `1.0.0`.

## 2. Helm Fundamentals

### Helm installation verification

```text
$ helm version
version.BuildInfo{Version:"v3.20.0", GitCommit:"b2e4314fa0f229a1de7b4c981273f61d69ee5a59", GitTreeState:"clean", GoVersion:"go1.25.6"}
```

### Public chart exploration

Attempted:

```bash
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo update
helm show chart prometheus-community/prometheus
```

In this session, external repository access did not complete successfully (network/timeout), so no public chart metadata was captured from the CLI run.

### Helm value proposition (brief)

Helm packages Kubernetes manifests as versioned charts and uses templating plus values overrides, so one chart can be reused across environments with predictable install/upgrade/rollback workflows.

## 3. Configuration Guide

Important values in `values.yaml`:

- `replicaCount`: rollout replica count.
- `image.repository`, `image.tag`, `image.pullPolicy`: container image configuration.
- `service.type`, `service.port`, `service.targetPort`: service exposure model.
- `resources.requests` / `resources.limits`: CPU and memory controls.
- `livenessProbe` / `readinessProbe`: health check behavior (kept enabled and configurable).
- `strategy.maxSurge` / `strategy.maxUnavailable`: reserved for non-Helm raw manifests; the chart workload uses `rollout.strategy` (canary / blue-green) instead of Deployment rolling parameters.
- `rollout`: progressive delivery settings; see `k8s/ROLLOUTS.md`.

Environment customization examples:

```bash
# Dev deployment
helm install devops-info-dev k8s/devops-info -f k8s/devops-info/values-dev.yaml

# Prod deployment
helm install devops-info-prod k8s/devops-info -f k8s/devops-info/values-prod.yaml

# One-off override
helm upgrade --install devops-info-dev k8s/devops-info -f k8s/devops-info/values-dev.yaml --set replicaCount=2
```

## 4. Hook Implementation

Implemented hooks:

- **Pre-install hook** (`templates/hooks-pre-install-job.yaml`)
  - annotations:
    - `helm.sh/hook: pre-install`
    - `helm.sh/hook-weight: "-5"`
    - `helm.sh/hook-delete-policy: hook-succeeded`
  - purpose: run pre-install validation before main resources.

- **Post-install hook** (`templates/hooks-post-install-job.yaml`)
  - annotations:
    - `helm.sh/hook: post-install`
    - `helm.sh/hook-weight: "5"`
    - `helm.sh/hook-delete-policy: hook-succeeded`
  - purpose: run smoke-test style task after install.

Execution order:

1. Pre-install job (weight `-5`)
2. Main chart resources
3. Post-install job (weight `5`)

Deletion policy:

- `hook-succeeded` removes successful hook Jobs automatically to avoid stale artifacts.

## 5. Installation Evidence

### Rendered environment differences

Rendered with:

```bash
helm template devops-info-dev k8s/devops-info -f k8s/devops-info/values-dev.yaml > /tmp/lab10-dev-render.yaml
helm template devops-info-prod k8s/devops-info -f k8s/devops-info/values-prod.yaml > /tmp/lab10-prod-render.yaml
```

Observed in rendered outputs:

- **Dev render**
  - `type: NodePort`
  - `replicas: 1`
  - `image: "devops-info-service-python:latest"`
  - hook annotations present for pre/post install.

- **Prod render**
  - `type: LoadBalancer`
  - `replicas: 3`
  - `image: "devops-info-service-python:1.0.0"`
  - hook annotations present for pre/post install.

### Cluster command status in this session

Minikube cluster from Lab 9 profile was created and activated:

```bash
minikube start -p lab09 --driver=docker
kubectl config current-context
kubectl get nodes
```

```text
lab09
NAME    STATUS   ROLES           AGE   VERSION
lab09   Ready    control-plane   10s   v1.35.1
```

Dry-run with cluster context:

```bash
helm install --dry-run --debug devops-info-dev k8s/devops-info -f k8s/devops-info/values-dev.yaml
```

```text
install.go:225: 2026-04-02 15:09:02.844243309 +0300 MSK m=+0.025621858 [debug] Original chart version: ""
install.go:242: 2026-04-02 15:09:02.844273126 +0300 MSK m=+0.025651675 [debug] CHART PATH: /home/user/Inno/DevOps-Core-Course/k8s/devops-info

NAME: devops-info-dev
LAST DEPLOYED: Thu Apr  2 15:09:02 2026
NAMESPACE: default
STATUS: pending-install
REVISION: 1
TEST SUITE: None
USER-SUPPLIED VALUES:
image:
  tag: latest
livenessProbe:
  initialDelaySeconds: 5
  periodSeconds: 10
readinessProbe:
  initialDelaySeconds: 3
  periodSeconds: 5
replicaCount: 1
resources:
  limits:
    cpu: 100m
    memory: 128Mi
  requests:
    cpu: 50m
    memory: 64Mi
service:
  type: NodePort

COMPUTED VALUES:
containerPort: 5000
env:
  debug: "false"
  host: 0.0.0.0
  port: "5000"
image:
  pullPolicy: IfNotPresent
  repository: devops-info-service-python
  tag: latest
livenessProbe:
  failureThreshold: 3
  httpGet:
    path: /health
    port: 5000
  initialDelaySeconds: 5
  periodSeconds: 10
  timeoutSeconds: 2
readinessProbe:
  failureThreshold: 3
  httpGet:
    path: /health
    port: 5000
  initialDelaySeconds: 3
  periodSeconds: 5
  timeoutSeconds: 2
replicaCount: 1
resources:
  limits:
    cpu: 100m
    memory: 128Mi
  requests:
    cpu: 50m
    memory: 64Mi
service:
  port: 80
  targetPort: 5000
  type: NodePort
strategy:
  maxSurge: 1
  maxUnavailable: 0

HOOKS:
---
# Source: devops-info/templates/hooks-post-install-job.yaml
apiVersion: batch/v1
kind: Job
metadata:
  name: "devops-info-dev-post-install"
  labels:
    helm.sh/chart: devops-info-0.1.0
    app.kubernetes.io/name: devops-info
    app.kubernetes.io/instance: devops-info-dev
    app.kubernetes.io/version: "1.0.0"
    app.kubernetes.io/managed-by: Helm
  annotations:
    "helm.sh/hook": post-install
    "helm.sh/hook-weight": "5"
    "helm.sh/hook-delete-policy": hook-succeeded
spec:
  template:
    metadata:
      labels:
        app.kubernetes.io/name: devops-info
        app.kubernetes.io/instance: devops-info-dev
    spec:
      restartPolicy: Never
      containers:
        - name: post-install-smoke
          image: busybox:1.36
          command:
            - sh
            - -c
            - >
              echo "Post-install smoke test for release devops-info-dev";
              sleep 3;
              echo "Smoke test complete";
---
# Source: devops-info/templates/hooks-pre-install-job.yaml
apiVersion: batch/v1
kind: Job
metadata:
  name: "devops-info-dev-pre-install"
  labels:
    helm.sh/chart: devops-info-0.1.0
    app.kubernetes.io/name: devops-info
    app.kubernetes.io/instance: devops-info-dev
    app.kubernetes.io/version: "1.0.0"
    app.kubernetes.io/managed-by: Helm
  annotations:
    "helm.sh/hook": pre-install
    "helm.sh/hook-weight": "-5"
    "helm.sh/hook-delete-policy": hook-succeeded
spec:
  template:
    metadata:
      labels:
        app.kubernetes.io/name: devops-info
        app.kubernetes.io/instance: devops-info-dev
    spec:
      restartPolicy: Never
      containers:
        - name: pre-install-check
          image: busybox:1.36
          command:
            - sh
            - -c
            - >
              echo "Pre-install validation for release devops-info-dev";
              sleep 3;
              echo "Validation complete";
MANIFEST:
---
# Source: devops-info/templates/service.yaml
apiVersion: v1
kind: Service
metadata:
  name: devops-info-dev
  labels:
    helm.sh/chart: devops-info-0.1.0
    app.kubernetes.io/name: devops-info
    app.kubernetes.io/instance: devops-info-dev
    app.kubernetes.io/version: "1.0.0"
    app.kubernetes.io/managed-by: Helm
spec:
  type: NodePort
  ports:
    - port: 80
      targetPort: 5000
      protocol: TCP
      name: http
  selector:
    app.kubernetes.io/name: devops-info
    app.kubernetes.io/instance: devops-info-dev
---
# Source: devops-info/templates/rollout.yaml
apiVersion: argoproj.io/v1alpha1
kind: Rollout
metadata:
  name: devops-info-dev
  labels:
    helm.sh/chart: devops-info-0.1.0
    app.kubernetes.io/name: devops-info
    app.kubernetes.io/instance: devops-info-dev
    app.kubernetes.io/version: "1.0.0"
    app.kubernetes.io/managed-by: Helm
spec:
  replicas: 1
  revisionHistoryLimit: 3
  selector:
    matchLabels:
      app.kubernetes.io/name: devops-info
      app.kubernetes.io/instance: devops-info-dev
  template:
    metadata:
      labels:
        app.kubernetes.io/name: devops-info
        app.kubernetes.io/instance: devops-info-dev
    spec:
      containers:
        - name: devops-info
          image: "devops-info-service-python:latest"
          # … probes, resources, env omitted for brevity
  strategy:
    canary:
      steps:
        - setWeight: 20
        - pause: {}
        - setWeight: 40
        - pause:
            duration: 30s
        - setWeight: 60
        - pause:
            duration: 30s
        - setWeight: 80
        - pause:
            duration: 30s
        - setWeight: 100
```

Live install evidence (after loading local image into minikube):

```bash
docker build -t devops-info-service-python:lab2 app_python
docker tag devops-info-service-python:lab2 devops-info-service-python:latest
minikube -p lab09 image load devops-info-service-python:latest
helm install devops-info-dev k8s/devops-info -f k8s/devops-info/values-dev.yaml --wait --timeout 180s
helm list
kubectl get all
kubectl get jobs
kubectl get rollout
```

```text
NAME            NAMESPACE REVISION STATUS   CHART             APP VERSION
devops-info-dev default   1        deployed devops-info-0.1.0 1.0.0

pod/devops-info-dev-...            1/1 Running
service/devops-info-dev            NodePort 80:31890/TCP
rollout.argoproj.io/devops-info-dev    1/1 available
replicaset.apps/devops-info-dev-... 1/1

No resources found in default namespace.  # kubectl get jobs
```

## 6. Operations

```bash
# Validate chart syntax and structure
helm lint k8s/devops-info

# Render manifests locally
helm template devops-info k8s/devops-info

# Install (dev)
helm install devops-info-dev k8s/devops-info -f k8s/devops-info/values-dev.yaml

# Upgrade dev -> prod profile
helm upgrade devops-info-dev k8s/devops-info -f k8s/devops-info/values-prod.yaml

# Rollback (example to revision 1)
helm rollback devops-info-dev 1

# Uninstall
helm uninstall devops-info-dev
```

## 7. Testing and Validation

### Lint output

```text
$ helm lint k8s/devops-info
==> Linting k8s/devops-info
[INFO] Chart.yaml: icon is recommended

1 chart(s) linted, 0 chart(s) failed
```

### Template verification

- Successfully rendered both `values-dev.yaml` and `values-prod.yaml`.
- Verified that hooks render with correct annotations and weights.
- Verified expected environment-specific changes (replicas, service type, image tag).

### Dry-run note

`helm install --dry-run --debug` executed successfully against the `lab09` minikube context and showed:

- computed values from `values-dev.yaml`
- rendered pre/post install hook Jobs with annotations, weights, and deletion policy
- rendered Rollout and Service manifests with expected dev configuration
