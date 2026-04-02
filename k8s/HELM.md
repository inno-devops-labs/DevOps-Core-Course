# Lab 10 — Helm Package Manager

## Chart Overview

This lab converts the Lab 9 raw Kubernetes manifests into reusable Helm charts and adds the bonus library chart for shared template logic.

Implemented chart layout:

```text
k8s/
├── common-lib/
│   ├── Chart.yaml
│   └── templates/_helpers.tpl
├── python-app/
│   ├── Chart.yaml
│   ├── Chart.lock
│   ├── charts/common-lib-0.1.0.tgz
│   ├── values.yaml
│   ├── values-dev.yaml
│   ├── values-prod.yaml
│   └── templates/
│       ├── deployment.yaml
│       ├── service.yaml
│       ├── hooks-pre-install-job.yaml
│       ├── hooks-post-install-job.yaml
│       └── NOTES.txt
└── go-app/
    ├── Chart.yaml
    ├── Chart.lock
    ├── charts/common-lib-0.1.0.tgz
    ├── values.yaml
    ├── values-dev.yaml
    ├── values-prod.yaml
    └── templates/
        ├── deployment.yaml
        ├── service.yaml
        └── NOTES.txt
```

Key design decisions:

- `common-lib` is a Helm `library` chart used by both application charts.
- Shared helpers were extracted into the library: `common.name`, `common.fullname`, `common.chart`, `common.selectorLabels`, and `common.labels`.
- `python-app` contains the main Task 2-4 implementation: deployment, service, configurable probes, dev/prod values, and lifecycle hooks.
- `go-app` is the bonus application chart that reuses the same shared library helpers.
- Original Lab 9 manifests remain in `k8s/*.yml` for traceability; Helm charts were added alongside them instead of replacing them.

Values organization strategy:

- `values.yaml` holds the base chart defaults.
- `values-dev.yaml` contains development-friendly overrides.
- `values-prod.yaml` contains production-oriented overrides.
- Nested value groups are used for `image`, `service`, `resources`, `env`, security contexts, and probes.

## Helm Fundamentals

Local tooling used:

```bash
helm version
kubectl version --client --output=yaml
minikube version
```

Observed output:

```text
version.BuildInfo{Version:"v3.17.1", GitCommit:"980d8ac1939e39138101364400756af2bdee1da5", GitTreeState:"clean", GoVersion:"go1.23.6"}
```

```text
clientVersion:
  gitVersion: v1.32.2
  platform: darwin/arm64
```

Important note:

- The lab brief references Helm 4.x, but the workstation had Helm `v3.17.1`.
- The implemented charts use `apiVersion: v2`, so they are fully compatible with Helm 3 and align with current chart best practices.

Public repository exploration:

```bash
HELM_CONFIG_HOME=/tmp/helm-lab10 HELM_CACHE_HOME=/tmp/helm-lab10/cache HELM_DATA_HOME=/tmp/helm-lab10/data \
  helm repo add prometheus-community https://prometheus-community.github.io/helm-charts

HELM_CONFIG_HOME=/tmp/helm-lab10 HELM_CACHE_HOME=/tmp/helm-lab10/cache HELM_DATA_HOME=/tmp/helm-lab10/data \
  helm repo update

HELM_CONFIG_HOME=/tmp/helm-lab10 HELM_CACHE_HOME=/tmp/helm-lab10/cache HELM_DATA_HOME=/tmp/helm-lab10/data \
  helm search repo prometheus-community/prometheus

HELM_CONFIG_HOME=/tmp/helm-lab10 HELM_CACHE_HOME=/tmp/helm-lab10/cache HELM_DATA_HOME=/tmp/helm-lab10/data \
  helm show chart prometheus-community/prometheus
```

Repository search output excerpt:

```text
NAME                                    CHART VERSION  APP VERSION  DESCRIPTION
prometheus-community/prometheus         28.15.0        v3.11.0      Prometheus is a monitoring system and time series database.
```

`helm show chart` excerpt:

```text
apiVersion: v2
name: prometheus
type: application
version: 28.15.0
appVersion: v3.11.0
description: Prometheus is a monitoring system and time series database.
```

Helm value proposition in this lab:

- Helm removes duplication by turning static manifests into parameterized templates.
- Releases make upgrades and rollbacks much easier than editing raw YAML by hand.
- Values files provide clean environment separation for dev and prod.
- Hooks add controlled lifecycle actions around installation.
- Library charts make shared logic reusable across multiple applications.

## Configuration Guide

Base Python values:

```yaml
replicaCount: 3

image:
  repository: ellilin/devops-info-service
  tag: latest
  pullPolicy: Always

service:
  type: NodePort
  port: 80
  targetPort: 8000
  nodePort: 30080
```

Important Python chart values:

- `replicaCount`: number of pod replicas.
- `image.repository`, `image.tag`, `image.pullPolicy`: container image configuration.
- `service.type`, `service.port`, `service.nodePort`: service exposure strategy.
- `resources.requests` and `resources.limits`: scheduling and runtime limits.
- `env`: application environment variables.
- `livenessProbe`, `readinessProbe`, `startupProbe`: probe configuration kept fully enabled and configurable.
- `podSecurityContext` and `containerSecurityContext`: pod/container hardening.
- `hooks.*`: lifecycle hook image, commands, and weights.

Development overrides used for the Python chart:

```yaml
replicaCount: 1
service:
  type: NodePort
resources:
  requests:
    cpu: 50m
    memory: 64Mi
  limits:
    cpu: 100m
    memory: 128Mi
env:
  RELEASE_TRACK: dev
```

Production overrides used for the Python chart:

```yaml
replicaCount: 3
service:
  type: LoadBalancer
resources:
  requests:
    cpu: 150m
    memory: 192Mi
  limits:
    cpu: 300m
    memory: 384Mi
env:
  RELEASE_TRACK: prod
```

Go chart differences:

- Uses image `ellilin/devops-info-service-go`.
- Uses container port `8080`.
- Uses NodePort `30081` in dev mode.
- Reuses the same naming and label helpers from `common-lib`.

Dependency setup:

```yaml
dependencies:
  - name: common-lib
    version: 0.1.0
    repository: "file://../common-lib"
```

Dependency build commands:

```bash
helm dependency build k8s/python-app --skip-refresh
helm dependency build k8s/go-app --skip-refresh
```

Output:

```text
Saving 1 charts
Deleting outdated charts
```

## Hook Implementation

Hooks were implemented in the Python chart:

- `pre-install` Job:
  validates that the release namespace variable is present before installation.
- `post-install` Job:
  runs a simple smoke-test placeholder command after the application is installed.

Hook annotations:

```yaml
annotations:
  "helm.sh/hook": pre-install
  "helm.sh/hook-weight": "-5"
  "helm.sh/hook-delete-policy": before-hook-creation,hook-succeeded
```

```yaml
annotations:
  "helm.sh/hook": post-install
  "helm.sh/hook-weight": "5"
  "helm.sh/hook-delete-policy": before-hook-creation,hook-succeeded
```

Execution order:

- Pre-install hook weight `-5` runs before main resources.
- Post-install hook weight `5` runs after main resources are ready.

Deletion policy:

- `hook-succeeded` removes successful Jobs automatically.
- `before-hook-creation` prevents old hook resources from lingering between installs.

Dry-run verification:

```bash
helm lint k8s/python-app
helm install --dry-run --debug python-dryrun k8s/python-app -n devops-lab10 -f k8s/python-app/values-dev.yaml
```

Output excerpt:

```text
1 chart(s) linted, 0 chart(s) failed
```

```text
HOOKS:
# Source: python-app/templates/hooks-post-install-job.yaml
# Source: python-app/templates/hooks-pre-install-job.yaml
```

Observed live pre-install hook during install:

```bash
kubectl get jobs -n devops-lab10
kubectl describe job -n devops-lab10 python-dev-devops-info-python-pre-install
```

Output excerpt:

```text
NAME                                        STATUS    COMPLETIONS   DURATION   AGE
python-dev-devops-info-python-pre-install   Running   0/1           8s         8s
```

```text
Annotations:      helm.sh/hook: pre-install
                  helm.sh/hook-delete-policy: before-hook-creation,hook-succeeded
                  helm.sh/hook-weight: -5
```

Hook cleanup verification after successful install:

```bash
kubectl get jobs -n devops-lab10
```

```text
No resources found in devops-lab10 namespace.
```

Rendered hooks from the installed release:

```bash
helm get hooks python-dev -n devops-lab10
```

That command shows both Jobs still stored in the release metadata even though Kubernetes deleted the completed hook resources.

## Installation Evidence

Cluster setup:

```bash
minikube start -p lab10 --driver=docker --kubernetes-version=v1.32.0
```

Observed output excerpt:

```text
* Done! kubectl is now configured to use "lab10" cluster and "default" namespace by default
```

Python dev install:

```bash
helm install python-dev k8s/python-app -n devops-lab10 --create-namespace -f k8s/python-app/values-dev.yaml --wait --timeout 240s
```

Output:

```text
NAME: python-dev
STATUS: deployed
REVISION: 1
```

Python dev workload evidence:

```bash
kubectl get all -n devops-lab10
```

```text
NAME                                                 READY   STATUS    RESTARTS   AGE
pod/python-dev-devops-info-python-6c4b56fcb4-5sn4q   1/1     Running   0          47s

NAME                                    TYPE       CLUSTER-IP     EXTERNAL-IP   PORT(S)        AGE
service/python-dev-devops-info-python   NodePort   10.101.60.49   <none>        80:30080/TCP   47s
```

Development accessibility verification:

```bash
minikube service python-dev-devops-info-python -n devops-lab10 --url -p lab10
curl -fsS http://127.0.0.1:63582/health
curl -fsS http://127.0.0.1:63582/
```

Output:

```text
http://127.0.0.1:63582
```

```json
{"status":"healthy","timestamp":"2026-04-02T20:26:36.306628+00:00","uptime_seconds":45}
```

Production upgrade:

```bash
helm upgrade python-dev k8s/python-app -n devops-lab10 -f k8s/python-app/values-prod.yaml --wait --timeout 240s
```

Final successful output:

```text
Release "python-dev" has been upgraded. Happy Helming!
NAME: python-dev
STATUS: deployed
REVISION: 3
```

During the first prod attempt, I hit a real-world issue:

- `image.tag: stable` did not exist in Docker Hub for `ellilin/devops-info-service`.
- I corrected `values-prod.yaml` to use `latest`, removed the stale pending Helm revision secret, enabled `minikube tunnel`, and reran the upgrade successfully.

Production release verification:

```bash
helm get values python-dev -n devops-lab10
kubectl get svc -n devops-lab10 python-dev-devops-info-python -o wide
kubectl get deployment python-dev-devops-info-python -n devops-lab10 -o jsonpath='{.spec.template.spec.containers[0].image} {.spec.replicas} {.spec.template.spec.containers[0].env[3].value} {.spec.template.spec.containers[0].resources.requests.cpu} {.spec.template.spec.containers[0].resources.limits.memory} {.spec.template.spec.containers[0].livenessProbe.initialDelaySeconds} {.spec.template.spec.containers[0].readinessProbe.initialDelaySeconds} {"\n"}'
```

Output:

```text
USER-SUPPLIED VALUES:
env:
  RELEASE_TRACK: prod
image:
  tag: latest
service:
  type: LoadBalancer
```

```text
NAME                            TYPE           CLUSTER-IP     EXTERNAL-IP   PORT(S)        AGE   SELECTOR
python-dev-devops-info-python   LoadBalancer   10.101.60.49   127.0.0.1     80:30080/TCP   10m   app.kubernetes.io/instance=python-dev,app.kubernetes.io/name=devops-info-python
```

```text
ellilin/devops-info-service:latest 3 prod 150m 384Mi 20 8
```

Prod accessibility verification:

```bash
kubectl port-forward -n devops-lab10 svc/python-dev-devops-info-python 18080:80
curl -fsS http://127.0.0.1:18080/health
curl -fsS http://127.0.0.1:18080/
```

Output:

```json
{"status":"healthy","timestamp":"2026-04-02T20:36:42.006198+00:00","uptime_seconds":209}
```

Bonus Go chart install:

```bash
helm install go-dev k8s/go-app -n devops-lab10 -f k8s/go-app/values-dev.yaml --wait --timeout 240s
```

Output:

```text
NAME: go-dev
STATUS: deployed
REVISION: 1
```

Go accessibility verification:

```bash
minikube service go-dev-devops-info-go -n devops-lab10 --url -p lab10
curl -fsS http://127.0.0.1:63839/health
```

Output:

```text
http://127.0.0.1:63839
```

```json
{"status":"healthy","timestamp":"2026-04-02T20:36:42Z","uptime_seconds":117}
```

Final release list:

```bash
helm list -n devops-lab10
```

```text
NAME       NAMESPACE     REVISION  UPDATED                              STATUS    CHART            APP VERSION
go-dev     devops-lab10  1         2026-04-02 23:34:34.699228 +0300 MSK deployed  go-app-0.1.0     1.0.0
python-dev devops-lab10  3         2026-04-02 23:36:11.025246 +0300 MSK deployed  python-app-0.1.0 1.0.0
```

Final Kubernetes state:

```bash
kubectl get all -n devops-lab10
```

```text
NAME                                                READY   STATUS    RESTARTS   AGE
pod/go-dev-devops-info-go-666c7c86f-tblvz           1/1     Running   0          19s
pod/python-dev-devops-info-python-9bc964c59-745jf   1/1     Running   0          74s
pod/python-dev-devops-info-python-9bc964c59-jxdml   1/1     Running   0          105s
pod/python-dev-devops-info-python-9bc964c59-tdvnh   1/1     Running   0          85s

NAME                                    TYPE           CLUSTER-IP      EXTERNAL-IP   PORT(S)        AGE
service/go-dev-devops-info-go           NodePort       10.111.17.165   <none>        80:30081/TCP   19s
service/python-dev-devops-info-python   LoadBalancer   10.101.60.49    127.0.0.1     80:30080/TCP   10m
```

## Operations

Install:

```bash
helm install python-dev k8s/python-app -n devops-lab10 --create-namespace -f k8s/python-app/values-dev.yaml --wait --timeout 240s
helm install go-dev k8s/go-app -n devops-lab10 -f k8s/go-app/values-dev.yaml --wait --timeout 240s
```

Upgrade:

```bash
helm upgrade python-dev k8s/python-app -n devops-lab10 -f k8s/python-app/values-prod.yaml --wait --timeout 240s
```

Rollback:

```bash
helm history python-dev -n devops-lab10
helm rollback python-dev 1 -n devops-lab10 --wait
```

Uninstall:

```bash
helm uninstall python-dev -n devops-lab10
helm uninstall go-dev -n devops-lab10
kubectl delete namespace devops-lab10
```

Dependency refresh after editing the library:

```bash
helm dependency build k8s/python-app --skip-refresh
helm dependency build k8s/go-app --skip-refresh
```

## Testing & Validation

Lint:

```bash
helm lint k8s/python-app
helm lint k8s/go-app
```

Output:

```text
==> Linting k8s/python-app
[INFO] Chart.yaml: icon is recommended

1 chart(s) linted, 0 chart(s) failed
```

```text
==> Linting k8s/go-app
[INFO] Chart.yaml: icon is recommended

1 chart(s) linted, 0 chart(s) failed
```

Template rendering:

```bash
helm template python-dev k8s/python-app -f k8s/python-app/values-dev.yaml
helm template go-dev k8s/go-app -f k8s/go-app/values-dev.yaml
```

Observed Python render highlights:

```text
kind: Service
name: python-dev-devops-info-python
type: NodePort
replicas: 1
image: "ellilin/devops-info-service:latest"
```

Observed Go render highlights:

```text
kind: Service
name: go-dev-devops-info-go
type: NodePort
replicas: 1
image: "ellilin/devops-info-service-go:latest"
```

Dry-run debug validation:

```bash
helm install --dry-run --debug python-dryrun k8s/python-app -n devops-lab10 -f k8s/python-app/values-dev.yaml
```

Verified in dry-run output:

- user-supplied values from `values-dev.yaml`
- computed values after merges
- rendered hook manifests
- rendered deployment and service manifests

## Bonus — Library Chart

The bonus task is implemented through `k8s/common-lib/`.

Library chart metadata:

```yaml
apiVersion: v2
name: common-lib
type: library
version: 0.1.0
```

Shared templates extracted into the library:

- chart label generation
- resource naming
- selector labels
- common labels

Benefits of the library chart approach:

- DRY: no duplicated helper logic between Python and Go charts.
- Consistency: both charts generate names and labels the same way.
- Maintainability: shared changes only need to be made once.
- Scalability: adding another application chart is straightforward.

Both app charts use the same dependency and render successfully with the shared templates, which satisfies the bonus requirement to eliminate duplication across multiple application charts.
