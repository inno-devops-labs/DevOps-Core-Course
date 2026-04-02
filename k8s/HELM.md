# Lab 10 - Helm Package Manager

## What I built

For this lab I stopped treating the Kubernetes YAML as one-off files and turned it into reusable Helm charts.

The main chart is for the Python service from Lab 9. It keeps the same core behavior:

- configurable image, replicas, resources, and service settings
- startup, readiness, and liveness probes kept intact
- rolling update strategy kept in values
- pre-install and post-install hooks for validation and smoke testing

I also completed the bonus task:

- the Rust service has its own installable Helm chart
- both application charts depend on a shared library chart
- common naming and label helpers now live in one place instead of being copied around

I kept the old raw manifests in `k8s/` untouched. The Helm work lives next to them so Lab 9 and Lab 10 are easy to compare.

## Helm fundamentals

### Installed version

```text
$ helm version
version.BuildInfo{Version:"v4.1.3", GitCommit:"c94d381b03be117e7e57908edbf642104e00eb8f", GitTreeState:"clean", GoVersion:"go1.26.1", KubeClientVersion:"v1.35"}
```

### Repository exploration

```text
$ helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
"prometheus-community" has been added to your repositories

$ helm repo update
...Successfully got an update from the "prometheus-community" chart repository
Update Complete. ⎈Happy Helming!⎈

$ helm search repo prometheus-community/prometheus
NAME                            CHART VERSION  APP VERSION  DESCRIPTION
prometheus-community/prometheus 28.15.0        v3.11.0      Prometheus is a monitoring system and time series database.
```

I also inspected a real public chart:

```text
$ helm show chart prometheus-community/prometheus
apiVersion: v2
appVersion: v3.11.0
description: Prometheus is a monitoring system and time series database.
name: prometheus
type: application
version: 28.15.0
```

### Why Helm is worth it here

For this repo, Helm solves three practical problems:

- I no longer have to copy and edit static YAML for every environment.
- The Python and Rust apps can share naming and label logic without drifting apart.
- Install, upgrade, rollback, and uninstall are now release-level operations instead of a pile of `kubectl apply` commands.

## Chart overview

### Structure

```text
k8s/
├── common-lib/
│   ├── Chart.yaml
│   └── templates/
│       └── _helpers.tpl
├── devops-info-service/
│   ├── Chart.yaml
│   ├── Chart.lock
│   ├── charts/
│   │   └── common-lib-0.1.0.tgz
│   ├── templates/
│   │   ├── deployment.yaml
│   │   ├── service.yaml
│   │   └── hooks/
│   │       ├── post-install-job.yaml
│   │       └── pre-install-job.yaml
│   ├── values.yaml
│   ├── values-dev.yaml
│   └── values-prod.yaml
└── devops-info-service-rust/
    ├── Chart.yaml
    ├── Chart.lock
    ├── charts/
    │   └── common-lib-0.1.0.tgz
    ├── templates/
    │   ├── deployment.yaml
    │   ├── service.yaml
    │   └── hooks/
    │       ├── post-install-job.yaml
    │       └── pre-install-job.yaml
    └── values.yaml
```

### What each chart does

- `k8s/common-lib`
  This is the bonus library chart. It only contains helper templates for `name`, `fullname`, `selectorLabels`, and `labels`.

- `k8s/devops-info-service`
  This is the main application chart for the Flask app. It includes the deployment, service, environment-specific values files, and both install hooks.

- `k8s/devops-info-service-rust`
  This is the second application chart for the Rust service. It reuses the same shared helpers and follows the same release structure.

### Values strategy

I kept the base values file focused on sane defaults and used overrides only where the environment really changes.

For the Python chart:

- `values.yaml` keeps the Lab 9 baseline: 3 replicas, NodePort service, original probe settings, and the original resource profile.
- `values-dev.yaml` cuts the deployment down to 1 replica and lighter resource requests.
- `values-prod.yaml` restores 3 replicas, raises requests and limits, and switches the service to `LoadBalancer`.

The Rust chart only needed one values file for this lab because the bonus requirement was about the second chart plus the shared library, not separate Rust environments.

## Bonus: library chart

The shared logic now lives in `k8s/common-lib/templates/_helpers.tpl`.

Both application charts declare the same dependency:

```yaml
dependencies:
  - name: common-lib
    version: 0.1.0
    repository: file://../common-lib
```

After that, both charts can use the same helper names:

```yaml
metadata:
  name: {{ include "common-lib.fullname" . }}
  labels:
    {{- include "common-lib.labels" . | nindent 4 }}
```

That got rid of the usual duplication around release naming and label blocks. The benefit is simple:

- one place to fix naming logic
- one label layout across both charts
- less copy-paste in future labs

## Configuration guide

### Important values

Python chart:

- `image.repository`, `image.tag`, `image.pullPolicy`
- `replicaCount`
- `service.type`, `service.port`, `service.containerPort`, `service.nodePort`
- `resources.requests`, `resources.limits`
- `startupProbe`, `readinessProbe`, `livenessProbe`
- `env.serviceVersion`, `env.serviceDescription`, `env.serviceFramework`
- `hooks.preInstall.*`, `hooks.postInstall.*`

Rust chart:

- `image.repository`, `image.tag`, `image.pullPolicy`
- `replicaCount`
- `service.type`, `service.port`, `service.containerPort`
- `resources.requests`, `resources.limits`
- `env.port`, `env.rustLog`
- `hooks.preInstall.*`, `hooks.postInstall.*`

### Environment differences for the Python chart

| Setting | Dev | Prod |
| --- | --- | --- |
| `replicaCount` | `1` | `3` |
| Service type | `NodePort` | `LoadBalancer` |
| CPU request | `50m` | `150m` |
| CPU limit | `100m` | `300m` |
| Memory request | `64Mi` | `192Mi` |
| Memory limit | `128Mi` | `384Mi` |

### Commands I used

First, I built the local dependency bundles:

```bash
helm dependency update k8s/devops-info-service
helm dependency update k8s/devops-info-service-rust
```

Development install for the Python chart:

```bash
helm install devops-info-service k8s/devops-info-service \
  -n lab10 \
  -f k8s/devops-info-service/values-dev.yaml \
  --set service.nodePort=30081 \
  --wait --wait-for-jobs --timeout 180s
```

I used `30081` only during local testing because the old Lab 9 service was still running in the cluster on `30080`. The chart default in the repo is still `30080`.

Production upgrade for the same release:

```bash
helm upgrade devops-info-service k8s/devops-info-service \
  -n lab10 \
  -f k8s/devops-info-service/values-prod.yaml \
  --wait --timeout 180s
```

Rust chart install:

```bash
helm install devops-info-service-rust k8s/devops-info-service-rust \
  -n lab10 \
  --wait --wait-for-jobs --timeout 180s
```

## Hook implementation

I implemented two install hooks in both application charts.

### Pre-install hook

- Type: `pre-install`
- Weight: `-5`
- Deletion policy: `before-hook-creation,hook-succeeded`

This job does a small sanity check before Helm creates the workload:

- image repository is not empty
- service port is greater than zero
- container port is greater than zero

### Post-install hook

- Type: `post-install`
- Weight: `5`
- Deletion policy: `before-hook-creation,hook-succeeded`

This job runs a real smoke test from inside the cluster with BusyBox `wget`:

- it hits `http://<service-name>:80/health`
- it retries for a configurable number of attempts
- it exits non-zero if the service never becomes healthy

I left a short `sleep 5` after a successful smoke test so I could reliably capture `kubectl describe job` before Helm cleaned the Job up. That pause is only there to make the hook lifecycle visible during the lab run.

### Execution order

The order is straightforward:

1. pre-install validation job runs first because its weight is `-5`
2. Helm creates the deployment and service
3. post-install smoke test runs after that because its weight is `5`
4. successful Jobs are deleted automatically

## Installation evidence

### Helm releases

```text
$ helm list -n lab10
NAME                     NAMESPACE  REVISION  UPDATED                              STATUS    CHART                          APP VERSION
devops-info-service      lab10      2         2026-04-02 21:26:39.948983 +0300    deployed  devops-info-service-0.1.0      1.0.0
devops-info-service-rust lab10      1         2026-04-02 21:25:49.142478 +0300    deployed  devops-info-service-rust-0.1.0 1.0.0
```

### Dev install state before the prod upgrade

```text
$ kubectl get deployment,svc -n lab10
NAME                                       READY   UP-TO-DATE   AVAILABLE   AGE
deployment.apps/devops-info-service        1/1     1            1           67s
deployment.apps/devops-info-service-rust   2/2     2            2           25s

NAME                               TYPE        CLUSTER-IP      EXTERNAL-IP   PORT(S)        AGE
service/devops-info-service        NodePort    10.96.208.235   <none>        80:30081/TCP   67s
service/devops-info-service-rust   ClusterIP   10.96.200.222   <none>        80/TCP         25s
```

### Prod state after the upgrade

```text
$ kubectl get deployment,svc -n lab10
NAME                                       READY   UP-TO-DATE   AVAILABLE   AGE
deployment.apps/devops-info-service        3/3     3            3           112s
deployment.apps/devops-info-service-rust   2/2     2            2           70s

NAME                               TYPE           CLUSTER-IP      EXTERNAL-IP   PORT(S)        AGE
service/devops-info-service        LoadBalancer   10.96.208.235   <pending>     80:30081/TCP   112s
service/devops-info-service-rust   ClusterIP      10.96.200.222   <none>        80/TCP         70s
```

The Python deployment also picked up the higher production resource values:

```text
$ kubectl get deployment devops-info-service -n lab10 -o jsonpath='{.spec.replicas}{"\n"}{.spec.template.spec.containers[0].resources}{"\n"}'
3
{"limits":{"cpu":"300m","memory":"384Mi"},"requests":{"cpu":"150m","memory":"192Mi"}}
```

### Full namespace view

```text
$ kubectl get all -n lab10
NAME                                            READY   STATUS    RESTARTS   AGE
pod/devops-info-service-5566c45d9f-dj8wm        1/1     Running   0          70s
pod/devops-info-service-5566c45d9f-qzhjj        1/1     Running   0          75s
pod/devops-info-service-5566c45d9f-zn572        1/1     Running   0          80s
pod/devops-info-service-rust-69994898c9-6kjgs   1/1     Running   0          2m7s
pod/devops-info-service-rust-69994898c9-vfvd2   1/1     Running   0          2m7s

NAME                               TYPE           CLUSTER-IP      EXTERNAL-IP   PORT(S)        AGE
service/devops-info-service        LoadBalancer   10.96.208.235   <pending>     80:30081/TCP   2m49s
service/devops-info-service-rust   ClusterIP      10.96.200.222   <none>        80/TCP         2m7s

NAME                                       READY   UP-TO-DATE   AVAILABLE   AGE
deployment.apps/devops-info-service        3/3     3            3           2m49s
deployment.apps/devops-info-service-rust   2/2     2            2           2m7s
```

### Hook execution

Python post-install hook:

```text
$ kubectl describe job devops-info-service-post-install -n lab10
Name:             devops-info-service-post-install
Namespace:        lab10
Labels:           app.kubernetes.io/component=hooks
                  app.kubernetes.io/instance=devops-info-service
                  app.kubernetes.io/name=devops-info-service
Annotations:      helm.sh/hook: post-install
                  helm.sh/hook-delete-policy: before-hook-creation,hook-succeeded
                  helm.sh/hook-weight: 5
Pods Statuses:    1 Active / 0 Succeeded / 0 Failed
Containers:
  post-install-smoke-test:
    Image: busybox:1.37.0
    Command:
      sh
      -ec
      url="http://devops-info-service:80/health"
      ...
Events:
  Type    Reason            Age   From            Message
  Normal  SuccessfulCreate  1s    job-controller  Created pod: devops-info-service-post-install-7pnzd
```

Rust post-install hook:

```text
$ kubectl describe job devops-info-service-rust-post-install -n lab10
Name:             devops-info-service-rust-post-install
Namespace:        lab10
Labels:           app.kubernetes.io/component=hooks
                  app.kubernetes.io/instance=devops-info-service-rust
                  app.kubernetes.io/name=devops-info-service-rust
Annotations:      helm.sh/hook: post-install
                  helm.sh/hook-delete-policy: before-hook-creation,hook-succeeded
                  helm.sh/hook-weight: 5
Pods Statuses:    1 Active / 0 Succeeded / 0 Failed
Containers:
  post-install-smoke-test:
    Image: busybox:1.37.0
    Command:
      sh
      -ec
      url="http://devops-info-service-rust:80/health"
      ...
Events:
  Type    Reason            Age   From            Message
  Normal  SuccessfulCreate  1s    job-controller  Created pod: devops-info-service-rust-post-install-mbpd9
```

After successful completion, Helm deleted the Jobs exactly as requested:

```text
$ kubectl get jobs -n lab10
No resources found in lab10 namespace.
```

### Direct application checks

Python service:

```text
$ curl -fsS http://127.0.0.1:18083/health
{"status":"healthy","timestamp":"2026-04-02T18:27:03.082903+00:00","uptime_seconds":95}
```

```text
$ curl -fsS http://127.0.0.1:18083/ | jq '{service: .service, request: .request.path}'
{
  "service": {
    "description": "DevOps course info service",
    "framework": "Flask",
    "name": "devops-info-service",
    "version": "1.0.0"
  },
  "request": "/"
}
```

Rust service:

```text
$ curl -fsS http://127.0.0.1:18084/health
{"status":"healthy","timestamp":"2026-04-02T18:26:32.256743581+00:00","uptime_seconds":38}
```

```text
$ curl -fsS http://127.0.0.1:18084/ | jq '{service: .service, request: .request.path}'
{
  "service": {
    "name": "devops-info-service",
    "version": "1.0.0",
    "description": "DevOps course info service",
    "framework": "Actix-web"
  },
  "request": "/"
}
```

## Operations

### Install

```bash
helm install devops-info-service k8s/devops-info-service \
  -n lab10 \
  -f k8s/devops-info-service/values-dev.yaml \
  --set service.nodePort=30081 \
  --wait --wait-for-jobs --timeout 180s

helm install devops-info-service-rust k8s/devops-info-service-rust \
  -n lab10 \
  --wait --wait-for-jobs --timeout 180s
```

### Upgrade

```bash
helm upgrade devops-info-service k8s/devops-info-service \
  -n lab10 \
  -f k8s/devops-info-service/values-prod.yaml \
  --wait --timeout 180s
```

Release history after the upgrade:

```text
$ helm history devops-info-service -n lab10
REVISION  UPDATED                  STATUS      CHART                     APP VERSION  DESCRIPTION
1         Thu Apr  2 21:25:01 2026 superseded  devops-info-service-0.1.0 1.0.0       Install complete
2         Thu Apr  2 21:26:39 2026 deployed    devops-info-service-0.1.0 1.0.0       Upgrade complete
```

### Rollback

```bash
helm rollback devops-info-service 1 -n lab10 --wait --timeout 180s
```

### Uninstall

```bash
helm uninstall devops-info-service -n lab10
helm uninstall devops-info-service-rust -n lab10
kubectl delete namespace lab10
```

## Testing and validation

### Lint

```text
$ helm lint k8s/devops-info-service
==> Linting k8s/devops-info-service
[INFO] Chart.yaml: icon is recommended

1 chart(s) linted, 0 chart(s) failed

$ helm lint k8s/devops-info-service-rust
==> Linting k8s/devops-info-service-rust
[INFO] Chart.yaml: icon is recommended

1 chart(s) linted, 0 chart(s) failed
```

### Template rendering

```text
$ helm template devops-info-service k8s/devops-info-service -f k8s/devops-info-service/values-dev.yaml --set service.nodePort=30081
---
# Source: devops-info-service/templates/service.yaml
kind: Service
metadata:
  name: devops-info-service
...
---
# Source: devops-info-service/templates/deployment.yaml
kind: Deployment
metadata:
  name: devops-info-service
...
```

### Dry-run install

```text
$ helm install --dry-run=client --debug devops-info-service k8s/devops-info-service -n lab10 -f k8s/devops-info-service/values-dev.yaml --set service.nodePort=30081
NAME: devops-info-service
NAMESPACE: lab10
STATUS: pending-install
DESCRIPTION: Dry run complete
```

The dry run also showed the rendered hooks and computed values, which made it easy to confirm that the environment overrides were applied before I touched the cluster.

### Live validation summary

- both charts lint cleanly
- both charts render cleanly
- the Python chart installs in dev mode
- the Python chart upgrades cleanly to the prod values
- the Rust chart installs cleanly
- both post-install smoke tests execute and are deleted afterward
- both applications respond to `/health` and `/`
