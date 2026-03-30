# Helm Chart Documentation - Lab 10

Date of validation: March 30, 2026

## Chart Overview

### Repository structure

```text
k8s/
|-- devops-info-chart/           # Main app chart (Task 2-4)
|   |-- Chart.yaml
|   |-- values.yaml
|   |-- values-dev.yaml
|   |-- values-prod.yaml
|   |-- charts/
|   |   `-- common-lib/          # Embedded dependency
|   `-- templates/
|       |-- deployment.yaml
|       |-- service.yaml
|       |-- NOTES.txt
|       `-- hooks/
|           |-- pre-install-job.yaml
|           `-- post-install-job.yaml
|
|-- app2-chart/                  # Second app chart (Bonus)
|   |-- Chart.yaml
|   |-- values.yaml
|   |-- values-dev.yaml
|   |-- charts/
|   |   `-- common-lib/
|   `-- templates/
|       |-- deployment.yaml
|       |-- service.yaml
|       `-- NOTES.txt
|
`-- common-lib/                  # Library chart (Bonus)
    |-- Chart.yaml
    `-- templates/
        `-- _helpers.tpl
```

### Key template files and purpose

- `devops-info-chart/templates/deployment.yaml`: templated Deployment (image, replicas, resources, probes, strategy, env).
- `devops-info-chart/templates/service.yaml`: templated Service (type/ports/conditional NodePort).
- `devops-info-chart/templates/hooks/pre-install-job.yaml`: pre-install validation hook.
- `devops-info-chart/templates/hooks/post-install-job.yaml`: post-install smoke-test hook.
- `common-lib/templates/_helpers.tpl`: shared naming/labels helpers (`common.fullname`, `common.labels`, `common.selectorLabels`, etc.).

### Values organization strategy

`values.yaml` contains sane defaults; `values-dev.yaml` and `values-prod.yaml` override only environment-specific parts.

- `replicaCount`
- `image.repository`, `image.tag`, `image.pullPolicy`
- `service.type`, `service.port`, `service.targetPort`, optional `service.nodePort`
- `resources.requests/limits`
- `livenessProbe` and `readinessProbe` (not commented out)
- `strategy`

## Helm Fundamentals (Task 1)

### Helm 4 installation and version

Global `helm` in PATH is not used for Lab 10 because this machine has Helm 3 there.
Lab validation is done with local Helm 4 binary:

`tools/helm4/windows-amd64/helm.exe`

```powershell
PS> & .\tools\helm4\windows-amd64\helm.exe version
version.BuildInfo{Version:"v4.1.3", GitCommit:"c94d381b03be117e7e57908edbf642104e00eb8f", GitTreeState:"clean", GoVersion:"go1.25.8", KubeClientVersion:"v1.35"}
```

### Public chart exploration

```powershell
PS> & .\tools\helm4\windows-amd64\helm.exe repo add prometheus-community https://prometheus-community.github.io/helm-charts --repository-config .tmp/helm-repo/repositories.yaml --repository-cache .tmp/helm-repo/cache
"prometheus-community" has been added to your repositories

PS> & .\tools\helm4\windows-amd64\helm.exe repo update --repository-config .tmp/helm-repo/repositories.yaml --repository-cache .tmp/helm-repo/cache
...Successfully got an update from the "prometheus-community" chart repository

PS> & .\tools\helm4\windows-amd64\helm.exe search repo prometheus --repository-config .tmp/helm-repo/repositories.yaml --repository-cache .tmp/helm-repo/cache
NAME                                           CHART VERSION  APP VERSION  DESCRIPTION
prometheus-community/prometheus                28.14.1        v3.10.0      Prometheus is a monitoring system...
...

PS> & .\tools\helm4\windows-amd64\helm.exe show chart prometheus-community/prometheus --repository-config .tmp/helm-repo/repositories.yaml --repository-cache .tmp/helm-repo/cache
apiVersion: v2
appVersion: v3.10.0
description: Prometheus is a monitoring system and time series database.
...
```

### Helm value proposition (brief)

- Reusable chart + environment overrides instead of many copied YAML manifests.
- Release lifecycle commands (`install`, `upgrade`, `rollback`, `uninstall`).
- Standardized packaging and dependency management.
- Hooks for release lifecycle automation.

## Configuration Guide

### Important values

| Value | Purpose |
|---|---|
| `replicaCount` | Number of pods |
| `image.repository` / `image.tag` | Container image selection |
| `service.type` | `NodePort` in dev, `LoadBalancer` in prod |
| `resources` | CPU/memory requests and limits |
| `livenessProbe` / `readinessProbe` | Health checks |
| `strategy` | RollingUpdate behavior |

### Environment specific files

- `values-dev.yaml`
  - `replicaCount: 1`
  - `service.type: NodePort`
  - lighter resources
  - faster probe settings
- `values-prod.yaml`
  - `replicaCount: 5`
  - `service.type: LoadBalancer`
  - higher resources
  - stricter probe settings

### Example installation commands

```powershell
# Dev install (Task 3 first step)
& .\tools\helm4\windows-amd64\helm.exe install myrelease k8s/devops-info-chart -f k8s/devops-info-chart/values-dev.yaml --set service.nodePort=30091

# Upgrade same release to prod values (Task 3 second step)
& .\tools\helm4\windows-amd64\helm.exe upgrade myrelease k8s/devops-info-chart -f k8s/devops-info-chart/values-prod.yaml
```

## Hook Implementation

Implemented hooks:

- `pre-install` job (`helm.sh/hook-weight: "-5"`)
- `post-install` job (`helm.sh/hook-weight: "5"`)
- deletion policy: `hook-succeeded`

### Hook annotations used

```yaml
annotations:
  "helm.sh/hook": pre-install|post-install
  "helm.sh/hook-weight": "-5"|"5"
  "helm.sh/hook-delete-policy": hook-succeeded
```

### Hook evidence

```powershell
PS> & .\tools\helm4\windows-amd64\helm.exe get hooks myrelease
# Source: devops-info-chart/templates/hooks/post-install-job.yaml
...
"helm.sh/hook": post-install
"helm.sh/hook-weight": "5"
"helm.sh/hook-delete-policy": hook-succeeded
...
# Source: devops-info-chart/templates/hooks/pre-install-job.yaml
...
"helm.sh/hook": pre-install
"helm.sh/hook-weight": "-5"
"helm.sh/hook-delete-policy": hook-succeeded
```

```powershell
PS> kubectl get jobs
No resources found in default namespace.
```

```powershell
PS> # Capture describe output during hook execution (before auto-delete):
PS> & .\tools\helm4\windows-amd64\helm.exe install hookproof k8s/devops-info-chart -f k8s/devops-info-chart/values-dev.yaml --set service.nodePort=30093
PS> kubectl describe job hookproof-devops-info-chart-pre-install
Name:             hookproof-devops-info-chart-pre-install
Namespace:        default
Labels:           app.kubernetes.io/instance=hookproof
                  app.kubernetes.io/name=devops-info-chart
Annotations:      helm.sh/hook: pre-install
                  helm.sh/hook-delete-policy: hook-succeeded
                  helm.sh/hook-weight: -5
Pods Statuses:    1 Active / 0 Succeeded / 0 Failed
Containers:
  pre-install-job:
    Image:      busybox:1.36
Events:
  Type    Reason            Age   From            Message
  Normal  SuccessfulCreate  4s    job-controller  Created pod: hookproof-devops-info-chart-pre-install-...
```

This confirms hooks are created and executed, and `kubectl get jobs` confirms they are deleted afterward by `hook-succeeded`.

## Installation Evidence

### Cluster context and versions

```powershell
PS> kubectl config current-context
minikube

PS> kubectl version --output=yaml
clientVersion.gitVersion: v1.29.2
serverVersion.gitVersion: v1.35.1
```

### Real release history and state (March 30, 2026)

```powershell
PS> & .\tools\helm4\windows-amd64\helm.exe install myrelease k8s/devops-info-chart -f k8s/devops-info-chart/values-dev.yaml --set service.nodePort=30091
NAME: myrelease
STATUS: deployed
REVISION: 1
Replicas: 1
Image: vladimirzhidkov/devops-info-service:latest
```

```powershell
PS> & .\tools\helm4\windows-amd64\helm.exe upgrade myrelease k8s/devops-info-chart -f k8s/devops-info-chart/values-prod.yaml
Release "myrelease" has been upgraded.
STATUS: deployed
REVISION: 2
Replicas: 5
Image: vladimirzhidkov/devops-info-service:lab02
```

```powershell
PS> kubectl get deployment myrelease-devops-info-chart -o jsonpath="{.spec.replicas} {.status.readyReplicas}"
5 5

PS> kubectl get svc myrelease-devops-info-chart -o jsonpath="{.spec.type} {.spec.ports[0].port} {.spec.ports[0].targetPort}"
LoadBalancer 80 5000
```

```powershell
PS> & .\tools\helm4\windows-amd64\helm.exe history myrelease
REVISION  UPDATED                  STATUS      CHART                    APP VERSION  DESCRIPTION
1         Mon Mar 30 17:49:14 2026 superseded  devops-info-chart-0.1.0 lab02        Install complete
2         Mon Mar 30 17:51:36 2026 deployed    devops-info-chart-0.1.0 lab02        Upgrade complete
```

### helm list output (required)

```powershell
PS> & .\tools\helm4\windows-amd64\helm.exe list -A
NAME         NAMESPACE  REVISION  UPDATED                               STATUS    CHART                    APP VERSION
app2-release default    1         2026-03-30 17:54:17.3256667 +0300    deployed  app2-chart-0.1.0         latest
myrelease    default    2         2026-03-30 17:51:36.1309087 +0300    deployed  devops-info-chart-0.1.0  lab02
```

### kubectl get all output (required)

```powershell
PS> kubectl get all -l app.kubernetes.io/instance=myrelease
NAME                                               READY   STATUS    RESTARTS   AGE
pod/myrelease-devops-info-chart-...                1/1     Running   0          ...
pod/myrelease-devops-info-chart-...                1/1     Running   0          ...
pod/myrelease-devops-info-chart-...                1/1     Running   0          ...
pod/myrelease-devops-info-chart-...                1/1     Running   0          ...
pod/myrelease-devops-info-chart-...                1/1     Running   0          ...

NAME                                  TYPE           CLUSTER-IP       EXTERNAL-IP  PORT(S)        AGE
service/myrelease-devops-info-chart   LoadBalancer   10.101.110.100   <pending>    80:30091/TCP   ...

NAME                                          READY   UP-TO-DATE   AVAILABLE   AGE
deployment.apps/myrelease-devops-info-chart   5/5     5            5           ...

NAME                                                     DESIRED   CURRENT   READY   AGE
replicaset.apps/myrelease-devops-info-chart-...          5         5         5       ...
```

## Operations

### Install

```powershell
& .\tools\helm4\windows-amd64\helm.exe install myrelease k8s/devops-info-chart -f k8s/devops-info-chart/values-dev.yaml --set service.nodePort=30091
```

### Upgrade

```powershell
& .\tools\helm4\windows-amd64\helm.exe upgrade myrelease k8s/devops-info-chart -f k8s/devops-info-chart/values-prod.yaml
```

### Rollback

```powershell
& .\tools\helm4\windows-amd64\helm.exe history myrelease
& .\tools\helm4\windows-amd64\helm.exe rollback myrelease 1
```

### Uninstall

```powershell
& .\tools\helm4\windows-amd64\helm.exe uninstall myrelease
& .\tools\helm4\windows-amd64\helm.exe uninstall app2-release
```

## Testing and Validation

### Lint and template checks

```powershell
PS> & .\tools\helm4\windows-amd64\helm.exe lint k8s/devops-info-chart
1 chart(s) linted, 0 chart(s) failed

PS> & .\tools\helm4\windows-amd64\helm.exe lint k8s/app2-chart
1 chart(s) linted, 0 chart(s) failed

PS> & .\tools\helm4\windows-amd64\helm.exe template dev-check k8s/devops-info-chart -f k8s/devops-info-chart/values-dev.yaml
# renders NodePort + replicas 1 + latest image

PS> & .\tools\helm4\windows-amd64\helm.exe template prod-check k8s/devops-info-chart -f k8s/devops-info-chart/values-prod.yaml
# renders LoadBalancer + replicas 5 + lab02 image
```

### Dry-run verification (cluster independent)

```powershell
PS> & .\tools\helm4\windows-amd64\helm.exe install --dry-run=client --debug test-release k8s/devops-info-chart --set service.nodePort=30090
STATUS: pending-install
DESCRIPTION: Dry run complete
HOOKS:
  pre-install and post-install jobs rendered with correct annotations
MANIFEST:
  service + deployment rendered with expected values
```

### Runtime rollout checks

```powershell
PS> kubectl rollout status deployment/myrelease-devops-info-chart --timeout=180s
deployment "myrelease-devops-info-chart" successfully rolled out

PS> kubectl rollout status deployment/app2-release-app2-chart --timeout=180s
deployment "app2-release-app2-chart" successfully rolled out
```

### Application accessibility verification

For Minikube, `LoadBalancer` external IP remains pending, so accessibility was verified via `kubectl port-forward`.

```powershell
PS> kubectl port-forward svc/myrelease-devops-info-chart 18080:80
PS> Invoke-WebRequest http://127.0.0.1:18080/health -UseBasicParsing
STATUSCODE=200
{"status":"healthy","timestamp":"2026-03-30T15:20:49.934Z","uptime_seconds":1711}
```

```powershell
PS> kubectl port-forward svc/app2-release-app2-chart 18081:80
PS> Invoke-WebRequest http://127.0.0.1:18081/ -UseBasicParsing
STATUSCODE=200
Hello from App 2!
```

## Bonus - Library Chart

### Library chart structure

`k8s/common-lib/Chart.yaml`:

```yaml
apiVersion: v2
name: common-lib
type: library
version: 0.1.0
```

### Shared templates implemented

`k8s/common-lib/templates/_helpers.tpl` exports:

- `common.name`
- `common.fullname`
- `common.chart`
- `common.labels`
- `common.selectorLabels`

### Dependency usage in both app charts

Both `devops-info-chart/Chart.yaml` and `app2-chart/Chart.yaml` include:

```yaml
dependencies:
  - name: common-lib
    version: 0.1.0
    repository: "file://../common-lib"
```

Both charts call shared templates from `common-lib` in their Deployment/Service manifests.

### Dependency verification

```powershell
PS> & .\tools\helm4\windows-amd64\helm.exe dependency list k8s/devops-info-chart
NAME       VERSION  REPOSITORY           STATUS
common-lib 0.1.0    file://../common-lib unpacked

PS> & .\tools\helm4\windows-amd64\helm.exe dependency list k8s/app2-chart
NAME       VERSION  REPOSITORY           STATUS
common-lib 0.1.0    file://../common-lib unpacked
```

### Second app deployment evidence

```powershell
PS> & .\tools\helm4\windows-amd64\helm.exe install app2-release k8s/app2-chart -f k8s/app2-chart/values-dev.yaml
STATUS: deployed
REVISION: 1
Replicas: 1
Image: hashicorp/http-echo:latest

PS> kubectl get deployment,svc,pods -l app.kubernetes.io/instance=app2-release -o wide
deployment.apps/app2-release-app2-chart   1/1  1  1  ...
service/app2-release-app2-chart           NodePort  ... 80:30081/TCP
pod/app2-release-app2-chart-...           1/1 Running
```

### Benefits of this approach

- DRY: common naming/labels logic is centralized in one chart.
- Consistency: both apps render the same label schema.
- Maintainability: update shared helpers once for all dependent charts.
