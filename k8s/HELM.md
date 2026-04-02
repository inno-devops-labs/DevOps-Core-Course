# Lab 10 - Helm Package Manager

Run date: April 2, 2026

## Chart Overview

This lab converts the Lab 9 Kubernetes manifests into Helm charts and adds a shared library chart for reusable helpers.

Chart layout:

- `k8s/devops-info-service/`: primary Python application chart
- `k8s/devops-info-service-go/`: secondary Go application chart for the bonus task
- `k8s/common-lib/`: library chart with shared naming and label helpers
- `k8s/kind-config-lab10.yml`: Lab 10-specific `kind` config used for this run

Key template files:

- `templates/deployment.yaml`: Deployment template with values-driven image, replica, resources, and health probes
- `templates/service.yaml`: Service template with configurable type, port, target port, and optional `nodePort`
- `templates/hooks/pre-install-job.yaml`: pre-install validation hook
- `templates/hooks/post-install-job.yaml`: post-install smoke-test hook
- `templates/_helpers.tpl`: chart-local wrappers around the shared library helpers
- `templates/NOTES.txt`: post-install usage notes

Values organization strategy:

- base defaults live in `values.yaml`
- environment overrides for the primary chart live in `values-dev.yaml` and `values-prod.yaml`
- common metadata labels are centralized in `commonLabels`
- health checks stay enabled and configurable under `probes`
- hook behavior is configurable under `hooks`

## Helm Fundamentals

Helm value proposition:

- it turns static manifests into reusable, environment-aware packages
- it keeps release history so upgrades and rollbacks are first-class operations
- it supports hooks for lifecycle checks and automation
- it standardizes Kubernetes deployment structure across applications

I installed Helm as a repo-local binary in `.tools/helm.exe` so the lab stays self-contained.

Helm version:

```text
version.BuildInfo{Version:"v4.1.3", GitCommit:"c94d381b03be117e7e57908edbf642104e00eb8f", GitTreeState:"clean", GoVersion:"go1.25.8", KubeClientVersion:"v1.35"}
```

Repository setup and exploration:

```text
"prometheus-community" has been added to your repositories
"grafana" has been added to your repositories
Hang tight while we grab the latest from your chart repositories...
...Successfully got an update from the "grafana" chart repository
...Successfully got an update from the "prometheus-community" chart repository
Update Complete. ⎈Happy Helming!⎈
```

```text
NAME                                     CHART VERSION  APP VERSION  DESCRIPTION
prometheus-community/prometheus          28.15.0        v3.11.0      Prometheus is a monitoring system and time series database.
```

`helm show chart prometheus-community/prometheus` excerpt:

```yaml
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

## Configuration Guide

Important values in `k8s/devops-info-service/values.yaml`:

- `replicaCount`: number of application pods
- `image.repository` and `image.tag`: container image source
- `container.port`: container listener port and `PORT` env var source
- `service.type`, `service.port`, `service.targetPort`, `service.nodePort`: service exposure settings
- `resources.requests` and `resources.limits`: CPU and memory policy
- `probes.startup`, `probes.liveness`, `probes.readiness`: configurable health checks
- `hooks.*`: lifecycle hook enablement, weights, and deletion policy

Environment overrides:

- `values-dev.yaml`: `1` replica, lighter resources, `NodePort`, image tag `lab10-dev`
- `values-prod.yaml`: `3` replicas, stronger resources, `LoadBalancer`, image tag `lab10-prod`

Example commands:

```powershell
.\.tools\helm.exe dependency build .\k8s\devops-info-service
.\.tools\helm.exe install devops-info-service .\k8s\devops-info-service --namespace lab10 -f .\k8s\devops-info-service\values-dev.yaml
.\.tools\helm.exe upgrade devops-info-service .\k8s\devops-info-service --namespace lab10 -f .\k8s\devops-info-service\values-prod.yaml
.\.tools\helm.exe install devops-info-service-go .\k8s\devops-info-service-go --namespace lab10
```

## Hook Implementation

Implemented hooks:

- `pre-install`: validates basic chart values before workloads are created
- `post-install`: runs a smoke test against the deployed service `/health` endpoint

Execution order and policies:

- pre-install hook weight: `-5`
- post-install hook weight: `5`
- deletion policy: `before-hook-creation,hook-succeeded`

The hooks reuse the application image instead of a separate utility image, which keeps the install path self-contained in the local `kind` cluster.

Pre-install job describe output excerpt:

```text
Name:                        devops-info-service-pre-install
Namespace:                   lab10
Annotations:                 helm.sh/hook: pre-install
                             helm.sh/hook-delete-policy: before-hook-creation,hook-succeeded
                             helm.sh/hook-weight: -5
TTL Seconds After Finished:  30
Containers:
 pre-install:
  Image:      ravwvil/devops-info-service:lab10-dev
  Command:
    sh
    -c
    echo "Validating chart values for devops-info-service"
    test 8000 -gt 0
    test 80 -gt 0
    sleep 12
    echo "Pre-install validation completed"
Events:
  Normal  SuccessfulCreate  Created pod: devops-info-service-pre-install-wr22r
```

Post-install job describe output excerpt:

```text
Name:                        devops-info-service-post-install
Namespace:                   lab10
Annotations:                 helm.sh/hook: post-install
                             helm.sh/hook-delete-policy: before-hook-creation,hook-succeeded
                             helm.sh/hook-weight: 5
TTL Seconds After Finished:  30
Containers:
 post-install:
  Image:      ravwvil/devops-info-service:lab10-dev
  Command:
    sh
    -c
    echo "Running smoke test for devops-info-service"
    python -c "import json, urllib.request; ..."
    sleep 12
    echo "Post-install smoke test completed"
Events:
  Normal  SuccessfulCreate  Created pod: devops-info-service-post-install-dgbjd
```

Observed job lifecycle during install:

```text
NAME                              STATUS               COMPLETIONS   DURATION   AGE
devops-info-service-pre-install   Running             0/1                      0s
devops-info-service-pre-install   Complete            1/1           13s        13s
devops-info-service-post-install  Running             0/1                      0s
devops-info-service-post-install  Complete            1/1           15s        16s
```

Deletion policy verification after install:

```text
No resources found in lab10 namespace.
```

## Installation Evidence

### Cluster Setup

I created a dedicated `kind` cluster for this lab:

```powershell
.\.tools\kind.exe create cluster --name lab10 --config .\k8s\kind-config-lab10.yml --kubeconfig .\k8s\lab10-kubeconfig
kubectl --kubeconfig .\k8s\lab10-kubeconfig get nodes -o wide
```

Actual node output:

```text
NAME                  STATUS   ROLES           AGE    VERSION   INTERNAL-IP   EXTERNAL-IP   OS-IMAGE                         KERNEL-VERSION                     CONTAINER-RUNTIME
lab10-control-plane   Ready    control-plane   3m1s   v1.35.0   172.19.0.3    <none>        Debian GNU/Linux 12 (bookworm)   6.6.87.2-microsoft-standard-WSL2   containerd://2.2.0
```

Note: this machine already had ports `80`, `443`, and `30080` occupied, so `k8s/kind-config-lab10.yml` intentionally avoids host port mappings. The dev chart still uses a `NodePort` service; application access was verified with `kubectl port-forward`.

### Images Built From This Branch

Commands:

```powershell
docker build -t ravwvil/devops-info-service:lab10-dev -t ravwvil/devops-info-service:lab10-prod .\app_python
docker build -t ravwvil/devops-info-service-go:latest .\app_go
.\.tools\kind.exe load docker-image ravwvil/devops-info-service:lab10-dev ravwvil/devops-info-service:lab10-prod ravwvil/devops-info-service-go:latest --name lab10
```

### Dev Install

Install command:

```powershell
kubectl --kubeconfig .\k8s\lab10-kubeconfig create namespace lab10 --dry-run=client -o yaml | kubectl --kubeconfig .\k8s\lab10-kubeconfig apply -f -
.\.tools\helm.exe install devops-info-service .\k8s\devops-info-service --kubeconfig .\k8s\lab10-kubeconfig --namespace lab10 -f .\k8s\devops-info-service\values-dev.yaml --wait --wait-for-jobs --timeout 5m
```

Actual install output:

```text
NAME: devops-info-service
LAST DEPLOYED: Thu Apr  2 22:57:06 2026
NAMESPACE: lab10
STATUS: deployed
REVISION: 1
DESCRIPTION: Install complete
```

`helm list -n lab10` after dev install:

```text
NAME                NAMESPACE  REVISION  UPDATED                               STATUS    CHART                     APP VERSION
devops-info-service lab10      1         2026-04-02 22:57:06.7417439 +0300 MSK deployed devops-info-service-0.1.0 1.0.0
```

`kubectl get all -n lab10` after dev install:

```text
NAME                                      READY   STATUS    RESTARTS   AGE
pod/devops-info-service-f85b86d55-l4brs   1/1     Running   0          76s

NAME                          TYPE       CLUSTER-IP     EXTERNAL-IP   PORT(S)        AGE
service/devops-info-service   NodePort   10.96.77.220   <none>        80:30080/TCP   76s

NAME                                  READY   UP-TO-DATE   AVAILABLE   AGE
deployment.apps/devops-info-service   1/1     1            1           76s
```

Accessibility verification:

```powershell
kubectl --kubeconfig .\k8s\lab10-kubeconfig port-forward svc/devops-info-service 18080:80 -n lab10
Invoke-RestMethod http://127.0.0.1:18080/health
Invoke-RestMethod http://127.0.0.1:18080/ready
```

Actual output:

```json
{"status":"healthy","timestamp":"2026-04-02T19:59:30.654237+00:00","uptime_seconds":118}
{"status":"ready","timestamp":"2026-04-02T19:59:30.733709+00:00"}
```

### Prod Upgrade

Upgrade command:

```powershell
.\.tools\helm.exe upgrade devops-info-service .\k8s\devops-info-service --kubeconfig .\k8s\lab10-kubeconfig --namespace lab10 -f .\k8s\devops-info-service\values-prod.yaml --wait --timeout 5m
```

Actual output:

```text
Release "devops-info-service" has been upgraded. Happy Helming!
NAME: devops-info-service
STATUS: deployed
REVISION: 2
DESCRIPTION: Upgrade complete
```

`helm history devops-info-service -n lab10`:

```text
REVISION  UPDATED                  STATUS      CHART                     APP VERSION  DESCRIPTION
1         Thu Apr  2 22:57:06 2026 superseded  devops-info-service-0.1.0 1.0.0        Install complete
2         Thu Apr  2 22:59:40 2026 deployed    devops-info-service-0.1.0 1.0.0        Upgrade complete
```

`helm get values devops-info-service --all -n lab10` excerpt:

```yaml
image:
  repository: ravwvil/devops-info-service
  tag: lab10-prod
replicaCount: 3
service:
  type: LoadBalancer
resources:
  requests:
    cpu: 200m
    memory: 256Mi
  limits:
    cpu: 500m
    memory: 512Mi
probes:
  readiness:
    initialDelaySeconds: 10
    periodSeconds: 3
```

### Bonus - Library Chart and Second App

Install command:

```powershell
.\.tools\helm.exe install devops-info-service-go .\k8s\devops-info-service-go --kubeconfig .\k8s\lab10-kubeconfig --namespace lab10 --wait --timeout 5m
```

Final `helm list -n lab10`:

```text
NAME                   NAMESPACE  REVISION  UPDATED                               STATUS    CHART                        APP VERSION
devops-info-service    lab10      2         2026-04-02 22:59:40.3412936 +0300 MSK deployed devops-info-service-0.1.0    1.0.0
devops-info-service-go lab10      1         2026-04-02 23:00:53.3893765 +0300 MSK deployed devops-info-service-go-0.1.0 1.0.0
```

Final `kubectl get all -n lab10`:

```text
NAME                                         READY   STATUS    RESTARTS   AGE
pod/devops-info-service-6857b5df76-5nhwk     1/1     Running   0          2m45s
pod/devops-info-service-6857b5df76-74jvx     1/1     Running   0          2m23s
pod/devops-info-service-6857b5df76-ksx4x     1/1     Running   0          2m2s
pod/devops-info-service-go-894cd778b-sgrtf   1/1     Running   0          91s
pod/devops-info-service-go-894cd778b-xhfn7   1/1     Running   0          91s

NAME                             TYPE           CLUSTER-IP      EXTERNAL-IP   PORT(S)        AGE
service/devops-info-service      LoadBalancer   10.96.77.220    <pending>     80:30080/TCP   5m3s
service/devops-info-service-go   ClusterIP      10.96.104.197   <none>        80/TCP         91s

NAME                                     READY   UP-TO-DATE   AVAILABLE   AGE
deployment.apps/devops-info-service      3/3     3            3           5m3s
deployment.apps/devops-info-service-go   2/2     2            2           91s
```

Go service accessibility verification:

```powershell
kubectl --kubeconfig .\k8s\lab10-kubeconfig port-forward svc/devops-info-service-go 18081:80 -n lab10
Invoke-RestMethod http://127.0.0.1:18081/health
Invoke-RestMethod http://127.0.0.1:18081/ready
```

Actual output:

```json
{"status":"healthy","timestamp":"2026-04-02T20:02:55.709613709Z","uptime_seconds":131}
{"status":"ready","timestamp":"2026-04-02T20:02:55.774490952Z"}
```

Benefits of the library chart:

- one shared source for names and label helpers
- less duplication across both app charts
- consistent metadata and selector patterns
- easier future expansion for more charts

## Operations

Install commands used:

```powershell
.\.tools\helm.exe install devops-info-service .\k8s\devops-info-service --kubeconfig .\k8s\lab10-kubeconfig --namespace lab10 -f .\k8s\devops-info-service\values-dev.yaml --wait --wait-for-jobs --timeout 5m
.\.tools\helm.exe upgrade devops-info-service .\k8s\devops-info-service --kubeconfig .\k8s\lab10-kubeconfig --namespace lab10 -f .\k8s\devops-info-service\values-prod.yaml --wait --timeout 5m
.\.tools\helm.exe install devops-info-service-go .\k8s\devops-info-service-go --kubeconfig .\k8s\lab10-kubeconfig --namespace lab10 --wait --timeout 5m
```

Upgrade a release:

```powershell
.\.tools\helm.exe upgrade devops-info-service .\k8s\devops-info-service --kubeconfig .\k8s\lab10-kubeconfig --namespace lab10 -f .\k8s\devops-info-service\values-prod.yaml
```

Rollback:

```powershell
.\.tools\helm.exe rollback devops-info-service 1 --kubeconfig .\k8s\lab10-kubeconfig --namespace lab10
```

Uninstall:

```powershell
.\.tools\helm.exe uninstall devops-info-service --kubeconfig .\k8s\lab10-kubeconfig --namespace lab10
.\.tools\helm.exe uninstall devops-info-service-go --kubeconfig .\k8s\lab10-kubeconfig --namespace lab10
```

## Testing and Validation

Dependency build and lint:

```text
Saving 1 charts
Deleting outdated charts
Saving 1 charts
Deleting outdated charts
==> Linting d:\Programming\DevOps\DevOps-Core-Course\k8s\devops-info-service
[INFO] Chart.yaml: icon is recommended
1 chart(s) linted, 0 chart(s) failed
==> Linting d:\Programming\DevOps\DevOps-Core-Course\k8s\devops-info-service-go
[INFO] Chart.yaml: icon is recommended
1 chart(s) linted, 0 chart(s) failed
```

`helm template` verification excerpt for the dev profile:

```yaml
spec:
  type: NodePort
  ports:
    - name: http
      port: 80
      targetPort: "http"
      nodePort: 30080
---
annotations:
  "helm.sh/hook": pre-install
  "helm.sh/hook-weight": "-5"
  "helm.sh/hook-delete-policy": "before-hook-creation,hook-succeeded"
---
image: "ravwvil/devops-info-service:lab10-dev"
```

`helm install --dry-run --debug` excerpt:

```text
NAME: devops-info-service
NAMESPACE: lab10
STATUS: pending-install
REVISION: 1
DESCRIPTION: Dry run complete
```

The dry-run also rendered both hooks and confirmed the dev overrides:

```yaml
replicaCount: 1
image:
  repository: ravwvil/devops-info-service
  tag: lab10-dev
service:
  type: NodePort
  nodePort: 30080
```

Application accessibility verification:

- Python service verified through `kubectl port-forward` with successful `/health` and `/ready` responses
- Go service verified through `kubectl port-forward` with successful `/health` and `/ready` responses
- the prod release shows `LoadBalancer` service type and `3` healthy replicas
