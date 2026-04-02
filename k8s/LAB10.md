# Lab 10 Report — Helm Package Manager

## 1. Chart Overview

This lab converts the Lab 9 Kubernetes manifests into Helm charts and adds multi-environment support, lifecycle hooks, and a reusable library chart.

Implemented chart structure:

```text
k8s/
├── LAB10.md
├── common-lib/
│   ├── Chart.yaml
│   └── templates/_helpers.tpl
├── devops-info/
│   ├── Chart.yaml
│   ├── values.yaml
│   ├── values-dev.yaml
│   ├── values-prod.yaml
│   └── templates/
│       ├── _helpers.tpl
│       ├── deployment.yaml
│       ├── service.yaml
│       ├── serviceaccount.yaml
│       ├── NOTES.txt
│       └── hooks/
│           ├── pre-install-job.yaml
│           └── post-install-job.yaml
└── devops-info-app2/
    ├── Chart.yaml
    ├── values.yaml
    └── templates/
        ├── _helpers.tpl
        ├── deployment.yaml
        ├── service.yaml
        └── serviceaccount.yaml
```

Key template files:

- `k8s/common-lib/templates/_helpers.tpl`: shared naming, selector labels, common labels, and service-account name helpers for both application charts.
- `k8s/devops-info/templates/deployment.yaml`: main Flask app Deployment with templated image, replicas, resources, and probes.
- `k8s/devops-info/templates/service.yaml`: main Service with templated type, port, and optional `nodePort`.
- `k8s/devops-info/templates/hooks/*.yaml`: lifecycle hook Jobs for pre-install validation and post-install smoke testing.
- `k8s/devops-info-app2/templates/*.yaml`: bonus second application chart using the same helper library.

Values organization strategy:

- `values.yaml` keeps safe production-style defaults for the chart itself.
- `values-dev.yaml` overrides replicas/resources for development.
- `values-prod.yaml` overrides replicas/resources/service type for production-style deployment.
- The main chart keeps health probes enabled at all times and exposes only their settings through values.

## 2. Helm Fundamentals

### Helm value proposition

Helm solves three problems that raw manifests do not solve well:

- reusable templating across environments
- versioned releases with history and rollback
- standardized packaging for dependencies, hooks, and operational workflows

### Helm installation and version

```bash
$ helm version
version.BuildInfo{Version:"v4.1.3", GitCommit:"c94d381b03be117e7e57908edbf642104e00eb8f", GitTreeState:"clean", GoVersion:"go1.26.1", KubeClientVersion:"v1.35"}
```

### Public repository setup and chart exploration

```bash
$ helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
"prometheus-community" has been added to your repositories

$ helm repo update
Hang tight while we grab the latest from your chart repositories...
...Successfully got an update from the "prometheus-community" chart repository
Update Complete. ⎈Happy Helming!⎈

$ helm search repo prometheus-community/prometheus
NAME                            CHART VERSION   APP VERSION   DESCRIPTION
prometheus-community/prometheus 28.15.0         v3.11.0       Prometheus is a monitoring system and time series database.

$ helm show chart prometheus-community/prometheus
apiVersion: v2
name: prometheus
type: application
version: 28.15.0
appVersion: v3.11.0
description: Prometheus is a monitoring system and time series database.
dependencies:
- name: alertmanager
- name: kube-state-metrics
- name: prometheus-node-exporter
- name: prometheus-pushgateway
```

What this public chart demonstrates:

- a chart is just metadata plus templates
- real charts commonly use dependencies
- versioned chart metadata is separate from application version

## 3. Configuration Guide

### Important values

| Value | Purpose |
|---|---|
| `replicaCount` | Number of Pods in the Deployment |
| `image.repository` / `image.tag` | Container image location and version |
| `service.type` | Exposure mode: `NodePort`, `ClusterIP`, or `LoadBalancer` |
| `service.nodePort` | Fixed local NodePort for the dev environment |
| `resources.*` | CPU and memory requests/limits |
| `env` | Application runtime variables such as `APP_ENV` and `APP_REVISION` |
| `startupProbe` / `livenessProbe` / `readinessProbe` | Health-check settings |
| `hookJobs.*` | Hook image, weights, retry behavior, and observation delay |

### Environment-specific values

| Setting | Dev | Prod |
|---|---|---|
| Replicas | `1` | `4` |
| Service type | `NodePort` | `LoadBalancer` |
| CPU request/limit | `50m` / `100m` | `200m` / `500m` |
| Memory request/limit | `64Mi` / `128Mi` | `256Mi` / `512Mi` |
| `APP_ENV` | `helm-dev` | `helm-prod` |
| `APP_REVISION` | `dev-v1` | `prod-v1` |

Example installations:

```bash
# Build local dependency from the library chart
helm dependency build k8s/devops-info
helm dependency build k8s/devops-info-app2

# Development install
helm install devops-info k8s/devops-info -f k8s/devops-info/values-dev.yaml

# Production upgrade
helm upgrade devops-info k8s/devops-info -f k8s/devops-info/values-prod.yaml

# Bonus second application
helm install devops-info-app2 k8s/devops-info-app2
```

Note about my live verification:

- The `default` namespace already had the Lab 9 Service `devops-info-service` using NodePort `30082`.
- To avoid collisions, I installed Lab 10 into namespace `lab10`.
- I used `--set service.nodePort=30083` for the live dev install, then upgraded the same release to the production values.
- After the in-place upgrade to `LoadBalancer`, Kubernetes kept the already allocated node port `30083`, so the live Service output still shows `80:30083/TCP`.

## 4. Hook Implementation

Implemented hooks in `k8s/devops-info/templates/hooks/`:

- pre-install and pre-upgrade Job
- post-install and post-upgrade Job

Hook behavior:

- Pre hook name: `lab10-devops-info-pre-install`
- Purpose: validate cluster DNS before install/upgrade
- Weight: `-5`
- Post hook name: `lab10-devops-info-post-install`
- Purpose: smoke-test `http://lab10-devops-info:80/health`
- Weight: `5`
- Deletion policy: `hook-succeeded`

Stored hook manifests from the deployed release:

```bash
$ helm get hooks lab10-devops-info -n lab10
...
annotations:
  "helm.sh/hook": post-install,post-upgrade
  "helm.sh/hook-weight": "5"
  "helm.sh/hook-delete-policy": hook-succeeded
...
annotations:
  "helm.sh/hook": pre-install,pre-upgrade
  "helm.sh/hook-weight": "-5"
  "helm.sh/hook-delete-policy": hook-succeeded
```

Execution order:

1. pre-install/pre-upgrade hook runs first because weight is `-5`
2. application resources are installed or upgraded
3. post-install/post-upgrade hook runs last because weight is `5`

Live hook execution evidence captured during install/upgrade:

```bash
$ kubectl get jobs -n lab10 -w
NAME                            STATUS               COMPLETIONS   DURATION   AGE
lab10-devops-info-pre-install   Running              0/1                      0s
lab10-devops-info-pre-install   SuccessCriteriaMet   0/1           4s         4s
lab10-devops-info-pre-install   Complete             1/1           4s         4s
lab10-devops-info-post-install  Running              0/1                      0s
lab10-devops-info-post-install  SuccessCriteriaMet   0/1           3s         3s
lab10-devops-info-post-install  Complete             1/1           3s         3s
```

Because the deletion policy is `hook-succeeded`, the Job object disappears immediately after successful completion. That is why a post-run `describe` looks like this:

```bash
$ kubectl describe job lab10-devops-info-pre-install -n lab10
Error from server (NotFound): jobs.batch "lab10-devops-info-pre-install" not found
```

Cleanup confirmation:

```bash
$ kubectl get jobs -n lab10
No resources found in lab10 namespace.
```

## 5. Installation Evidence

### Release list

```bash
$ helm list -n lab10
NAME                   NAMESPACE   REVISION   STATUS    CHART                  APP VERSION
lab10-devops-info      lab10       3          deployed  devops-info-0.1.0      lab2
lab10-devops-info-app2 lab10       1          deployed  devops-info-app2-0.1.0 lab2
```

### Dev-to-prod transition

```bash
$ helm history lab10-devops-info -n lab10
REVISION   UPDATED                   STATUS      CHART             APP VERSION   DESCRIPTION
1          Thu Apr  2 18:37:02 2026 superseded  devops-info-0.1.0 lab2          Install complete
2          Thu Apr  2 18:39:56 2026 superseded  devops-info-0.1.0 lab2          Upgrade complete
3          Thu Apr  2 18:42:03 2026 deployed    devops-info-0.1.0 lab2          Upgrade complete
```

### Kubernetes resources

```bash
$ kubectl get all -n lab10
NAME                                          READY   STATUS    RESTARTS   AGE
pod/lab10-devops-info-9dbbf4764-9c9tx         1/1     Running   0          25m
pod/lab10-devops-info-9dbbf4764-lbbdt         1/1     Running   0          25m
pod/lab10-devops-info-9dbbf4764-ll9ll         1/1     Running   0          25m
pod/lab10-devops-info-9dbbf4764-vf646         1/1     Running   0          25m
pod/lab10-devops-info-app2-558b8f94b6-n7hv9   1/1     Running   0          21m
pod/lab10-devops-info-app2-558b8f94b6-x67rk   1/1     Running   0          21m

service/lab10-devops-info        LoadBalancer   10.96.24.209   <pending>   80:30083/TCP
service/lab10-devops-info-app2   ClusterIP      10.96.25.75    <none>      80/TCP

deployment.apps/lab10-devops-info        4/4
deployment.apps/lab10-devops-info-app2   2/2
```

### Application accessibility

Main release:

```bash
$ kubectl port-forward -n lab10 service/lab10-devops-info 8080:80
$ curl -s http://127.0.0.1:8080/
{"service":{"name":"devops-info-service","version":"1.0.0"},"system":{"hostname":"lab10-devops-info-9dbbf4764-ll9ll",...}}

$ curl -s http://127.0.0.1:8080/health
{"status":"healthy","timestamp":"2026-04-02T15:56:03.117812+00:00","uptime_seconds":961}
```

Bonus second chart:

```bash
$ kubectl port-forward -n lab10 service/lab10-devops-info-app2 8081:80
$ curl -s http://127.0.0.1:8081/health
{"status":"healthy","timestamp":"2026-04-02T15:56:26.619191+00:00","uptime_seconds":718}
```

## 6. Operations

Commands used:

```bash
# Build dependencies
helm dependency build k8s/devops-info
helm dependency build k8s/devops-info-app2

# Install dev release in isolated namespace
helm install lab10-devops-info k8s/devops-info \
  -n lab10 --create-namespace \
  -f k8s/devops-info/values-dev.yaml \
  --set service.nodePort=30083 \
  --wait --timeout 5m

# Upgrade to production values
helm upgrade lab10-devops-info k8s/devops-info \
  -n lab10 \
  -f k8s/devops-info/values-prod.yaml \
  --wait --timeout 5m

# Install second app chart
helm install lab10-devops-info-app2 k8s/devops-info-app2 \
  -n lab10 \
  --wait --timeout 5m
```

Useful day-2 operations:

```bash
# Inspect releases
helm list -n lab10
helm history lab10-devops-info -n lab10

# Roll back if needed
helm rollback lab10-devops-info 1 -n lab10

# Uninstall
helm uninstall lab10-devops-info -n lab10
helm uninstall lab10-devops-info-app2 -n lab10
```

## 7. Testing And Validation

### Lint

```bash
$ helm lint k8s/devops-info
==> Linting .../k8s/devops-info
[INFO] Chart.yaml: icon is recommended
1 chart(s) linted, 0 chart(s) failed

$ helm lint k8s/devops-info-app2
==> Linting .../k8s/devops-info-app2
[INFO] Chart.yaml: icon is recommended
1 chart(s) linted, 0 chart(s) failed
```

### Template verification

Dev render:

```bash
$ helm template devops-info-dev k8s/devops-info -f k8s/devops-info/values-dev.yaml
spec:
  type: NodePort
...
spec:
  replicas: 1
```

Prod render:

```bash
$ helm template devops-info-prod k8s/devops-info -f k8s/devops-info/values-prod.yaml
spec:
  type: LoadBalancer
...
spec:
  replicas: 4
```

Bonus chart render:

```bash
$ helm template devops-info-app2 k8s/devops-info-app2
kind: Service
spec:
  type: ClusterIP
...
kind: Deployment
spec:
  replicas: 2
```

### Dry run

```bash
$ helm install --dry-run --debug test-release k8s/devops-info -f k8s/devops-info/values-dev.yaml
NAME: test-release
STATUS: pending-install
DESCRIPTION: Dry run complete
HOOKS:
- test-release-devops-info-post-install
- test-release-devops-info-pre-install
```

Result:

- offline validation passed
- live installation passed
- upgrade to production values passed
- hook Jobs executed and were removed by `hook-succeeded`
- both application charts deployed successfully

## 8. Bonus — Library Chart

The bonus task is implemented with `k8s/common-lib/`.

Shared templates extracted into the library chart:

- `common.name`
- `common.fullname`
- `common.chart`
- `common.selectorLabels`
- `common.labels`
- `common.serviceAccountName`

How both application charts use the library:

- `k8s/devops-info/Chart.yaml` depends on `file://../common-lib`
- `k8s/devops-info-app2/Chart.yaml` depends on `file://../common-lib`
- both Deployment and Service templates call `include "common.*" ...`

Benefits of the library-chart approach:

- eliminates duplicated naming and label logic
- keeps labels consistent across both applications
- makes future extensions easier because helper changes happen in one place
- improves maintainability for later labs built on top of this chart

## 9. Summary

Lab 10 is complete:

- Helm 4 installed and verified
- public repository added and explored
- Lab 9 manifests converted into Helm charts
- dev and prod values files created and tested
- pre/post lifecycle hooks implemented
- hook execution verified and cleanup confirmed
- bonus library chart implemented and used by two app charts
- `k8s/LAB10.md` created with full report and command evidence
