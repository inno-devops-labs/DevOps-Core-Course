# Lab 10 - Helm Package Manager

Validated locally on April 2, 2026 against the existing `kind-devops-lab9` cluster (`Kubernetes v1.34.3`).

Lab 11 extends the same Python chart with `Secret`, `ServiceAccount`, and Vault Agent Injector templates. Those additions are documented separately in [SECRETS.md](SECRETS.md), and the repeatable Vault dev-mode bootstrap helper lives at [scripts/bootstrap-lab11-vault.sh](scripts/bootstrap-lab11-vault.sh).

## Prerequisites

The main Python chart defaults to the Lab 9 image and service behavior.

The bonus Go chart defaults to the same local image workflow used in Lab 9. On a clean `kind` machine, build and load the image first:

```bash
docker build -t devops-info-go:lab02 app_go
kind load docker-image devops-info-go:lab02 --name devops-lab9
helm install lab10-go k8s/devops-info-go \
  --namespace lab10
```

If you are deploying to a cluster that cannot see local kind images, override `image.repository` and `image.tag` with a registry-backed image instead. The optional `k8s/devops-info-go/values-kind.yaml` file keeps the same local-kind image settings as an explicit profile.

## Helm Fundamentals

Helm solves three concrete problems in this repository:

- it replaces duplicated static manifests with reusable templates;
- it moves environment-specific settings into values files instead of hardcoded YAML;
- it gives release lifecycle controls such as install, upgrade, rollback, and hook-based validation.

Helm was installed locally into `/tmp/helm-v4` to avoid changing the global workstation setup:

```text
$ /tmp/helm-v4/darwin-arm64/helm version
version.BuildInfo{Version:"v4.0.0", GitCommit:"99cd1964357c793351be481d55abbe21c6b2f4ec", GitTreeState:"clean", GoVersion:"go1.25.3", KubeClientVersion:"v1.34"}
```

Public chart repository exploration:

```text
$ helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
"prometheus-community" has been added to your repositories

$ helm repo update
...Successfully got an update from the "prometheus-community" chart repository
Update Complete. Happy Helming!

$ helm show chart prometheus-community/prometheus
apiVersion: v2
appVersion: v3.10.0
description: Prometheus is a monitoring system and time series database.
home: https://prometheus.io/
keywords:
- monitoring
- prometheus
name: prometheus
type: application
version: 28.14.1
```

## Chart Overview

Implemented chart layout:

```text
k8s/
|-- common-lib/
|   |-- Chart.yaml
|   `-- templates/_helpers.tpl
|-- devops-info-python/
|   |-- Chart.yaml
|   |-- Chart.lock
|   |-- charts/common-lib-0.1.0.tgz
|   |-- values.yaml
|   |-- values-dev.yaml
|   |-- values-prod.yaml
|   `-- templates/
|       |-- deployment.yaml
|       |-- service.yaml
|       |-- NOTES.txt
|       `-- hooks/
|           |-- pre-install-job.yaml
|           `-- post-install-job.yaml
`-- devops-info-go/
    |-- Chart.yaml
    |-- Chart.lock
    |-- charts/common-lib-0.1.0.tgz
    |-- values.yaml
    |-- values-kind.yaml
    `-- templates/
        |-- deployment.yaml
        `-- service.yaml
```

Purpose of each chart:

- `devops-info-python`: main Lab 10 application chart, derived from `k8s/deployment.yml` and `k8s/service.yml`.
- `devops-info-go`: bonus second application chart, derived from `k8s/go-deployment.yml` and `k8s/go-service.yml`.
- `common-lib`: shared library chart for names, labels, selectors, and HTTP probe rendering.

Shared helpers extracted into `common-lib`:

- `common.name`
- `common.fullname`
- `common.chart`
- `common.selectorLabels`
- `common.labels`
- `common.httpProbe`

Values organization strategy:

- defaults in `values.yaml` preserve the Lab 9 runtime behavior, including Python `NodePort 30080`;
- `values-dev.yaml` is optimized for a light local deployment and moves the Python service to deterministic `NodePort 30091` to avoid clashing with existing lab services in the cluster;
- `values-prod.yaml` raises replica count and resource requests, keeps the service internal as `ClusterIP`, and disables persistence because the Lab 12 single-writer `ReadWriteOnce` PVC design is not safe for a multi-replica Deployment.
- `k8s/devops-info-go/values-kind.yaml` mirrors the default bonus image settings as an explicit local-kind profile.

## Configuration Guide

Important values in `k8s/devops-info-python/values.yaml`:

| Value | Purpose | Default |
| --- | --- | --- |
| `image.repository` / `image.tag` | Python container image | `pepegx/devops-info-service:lab12` |
| `replicaCount` | Deployment size | `1` |
| `service.type` | Exposed Service type | `NodePort` |
| `service.port` | Service port | `80` |
| `service.targetPort` | Backend target port | `http` |
| `service.nodePort` | Fixed local access port for the default profile | `30080` |
| `resources` | CPU and memory requests/limits | `100m/128Mi` requests, `250m/256Mi` limits |
| `config.host`, `config.port`, `config.logLevel` | Container env vars | `0.0.0.0`, `3000`, `INFO` |
| `livenessProbe` / `readinessProbe` | Health-check behavior | `/health` with configurable delays and periods |
| `hooks.preInstall.*` | Validation job before install | BusyBox validation job |
| `hooks.postInstall.*` | Smoke test after install | BusyBox service check |

Environment-specific overrides for the Python chart:

| Setting | `values-dev.yaml` | `values-prod.yaml` |
| --- | --- | --- |
| `replicaCount` | `1` | `2` |
| `service.type` | `NodePort` | `ClusterIP` |
| `service.nodePort` | `30091` | not set |
| `persistence.enabled` | `true` | `false` |
| `resources.requests.cpu` | `50m` | `150m` |
| `resources.limits.cpu` | `100m` | `500m` |
| `resources.requests.memory` | `64Mi` | `192Mi` |
| `resources.limits.memory` | `128Mi` | `512Mi` |
| `config.logLevel` | `DEBUG` | `INFO` |
| `livenessProbe.initialDelaySeconds` | `5` | `30` |
| `readinessProbe.initialDelaySeconds` | `3` | `10` |

Example commands:

```bash
helm install lab10-python k8s/devops-info-python \
  --namespace lab10 \
  --create-namespace \
  -f k8s/devops-info-python/values-dev.yaml

helm upgrade lab10-python k8s/devops-info-python \
  --namespace lab10 \
  -f k8s/devops-info-python/values-prod.yaml

docker build -t devops-info-go:lab02 app_go
kind load docker-image devops-info-go:lab02 --name devops-lab9

helm install lab10-go k8s/devops-info-go \
  --namespace lab10
```

## Hook Implementation

Implemented hooks in the Python chart:

- `pre-install` with weight `-5`: validates critical values before workload creation.
- `post-install` with weight `5`: runs a smoke test against `http://<service>/health`.
- delete policy for both hooks: `before-hook-creation,hook-succeeded`.

Why these hooks:

- the pre-install job fails fast if core chart values are inconsistent;
- the post-install job proves the Service is reachable and the app returns healthy JSON;
- `hook-succeeded` keeps the namespace clean after successful installation.

Live evidence was captured in a temporary namespace `lab10-hooks` with longer hook sleep values and then cleaned up. Pre-install hook while running:

```text
$ kubectl get jobs,pods -n lab10-hooks -o wide
NAME                                                    STATUS    COMPLETIONS   DURATION   AGE   CONTAINERS    IMAGES           SELECTOR
job.batch/hooks-python-devops-info-python-pre-install   Running   0/1           12s        12s   pre-install   busybox:1.36.1   batch.kubernetes.io/controller-uid=56ac7d92-c222-4960-a02e-be27aab06bb5

NAME                                                    READY   STATUS    RESTARTS   AGE   IP            NODE
pod/hooks-python-devops-info-python-pre-install-69fb2   1/1     Running   0          12s   10.244.1.19   devops-lab9-worker
```

```text
$ kubectl describe job -n lab10-hooks hooks-python-devops-info-python-pre-install
Annotations:      helm.sh/hook: pre-install
                  helm.sh/hook-delete-policy: before-hook-creation,hook-succeeded
                  helm.sh/hook-weight: -5
Backoff Limit:    0
Command:
  sh
  -c
  echo "[pre-install] validating release hooks-python"; test -n "pepegx/devops-info-service"; test -n "lab02"; test "3000" = "3000"; echo "[pre-install] configuration looks valid"; sleep 30;
```

```text
$ kubectl logs -n lab10-hooks job/hooks-python-devops-info-python-pre-install
[pre-install] validating release hooks-python
[pre-install] configuration looks valid
```

Post-install hook while running:

```text
$ kubectl get jobs,pods -n lab10-hooks -o wide
NAME                                                     STATUS    COMPLETIONS   DURATION   AGE   CONTAINERS     IMAGES           SELECTOR
job.batch/hooks-python-devops-info-python-post-install   Running   0/1           18s        18s   post-install   busybox:1.36.1   batch.kubernetes.io/controller-uid=bad1978f-1671-4c5c-8e05-1c1fc5eb099c

NAME                                                     READY   STATUS    RESTARTS   AGE   IP            NODE
pod/hooks-python-devops-info-python-79895f9557-dwl5s     1/1     Running   0          35s   10.244.1.20   devops-lab9-worker
pod/hooks-python-devops-info-python-post-install-qksc8   1/1     Running   0          18s   10.244.1.21   devops-lab9-worker
```

```text
$ kubectl describe job -n lab10-hooks hooks-python-devops-info-python-post-install
Annotations:      helm.sh/hook: post-install
                  helm.sh/hook-delete-policy: before-hook-creation,hook-succeeded
                  helm.sh/hook-weight: 5
Backoff Limit:    0
Command:
  sh
  -c
  echo "[post-install] starting smoke test"; i=0; until wget -qO- "http://hooks-python-devops-info-python:80/health" | grep -q healthy; do
    i=$((i+1));
    if [ "$i" -ge 24 ]; then
      echo "[post-install] smoke test failed";
      exit 1;
    fi;
    sleep 5;
  done; echo "[post-install] smoke test passed"; sleep 30;
```

```text
$ kubectl logs -n lab10-hooks job/hooks-python-devops-info-python-post-install
[post-install] starting smoke test
[post-install] smoke test passed
```

Deletion policy verification:

```text
$ kubectl get jobs -n lab10-hooks
No resources found in lab10-hooks namespace.

$ kubectl get jobs -n lab10
No resources found in lab10 namespace.
```

## Installation Evidence

Dependency build and static validation:

```text
$ helm dependency build k8s/devops-info-python
Saving 1 charts
Deleting outdated charts

$ helm dependency build k8s/devops-info-go
Saving 1 charts
Deleting outdated charts

$ helm lint k8s/devops-info-python
==> Linting k8s/devops-info-python
[INFO] Chart.yaml: icon is recommended

1 chart(s) linted, 0 chart(s) failed

$ helm lint k8s/devops-info-go
==> Linting k8s/devops-info-go
[INFO] Chart.yaml: icon is recommended

1 chart(s) linted, 0 chart(s) failed

$ helm template review-go k8s/devops-info-go
# Source: devops-info-go/templates/service.yaml
kind: Service
metadata:
  name: review-go-devops-info-go
...
```

Rendered template verification:

```text
$ helm template lab10-python k8s/devops-info-python -f k8s/devops-info-python/values-dev.yaml
# Source: devops-info-python/templates/service.yaml
kind: Service
metadata:
  name: lab10-python-devops-info-python
...
# Source: devops-info-python/templates/deployment.yaml
kind: Deployment
spec:
  replicas: 1
...
# Source: devops-info-python/templates/hooks/post-install-job.yaml
kind: Job
metadata:
  name: lab10-python-devops-info-python-post-install
...

$ helm template review-go k8s/devops-info-go -f k8s/devops-info-go/values-kind.yaml
# Source: devops-info-go/templates/service.yaml
kind: Service
metadata:
  name: review-go-devops-info-go
...
# Source: devops-info-go/templates/deployment.yaml
kind: Deployment
spec:
  replicas: 2
...

$ helm template prod-python k8s/devops-info-python -f k8s/devops-info-python/values-prod.yaml
# Source: devops-info-python/templates/service.yaml
kind: Service
spec:
  type: LoadBalancer
  allocateLoadBalancerNodePorts: false
  ports:
    - name: http
      port: 80
      targetPort: http
      protocol: TCP
      nodePort: null
...
```

Dry-run verification:

```text
$ helm install --dry-run=client --debug dryrun-python-client k8s/devops-info-python -f k8s/devops-info-python/values-dev.yaml
NAME: dryrun-python-client
STATUS: pending-install
DESCRIPTION: Dry run complete
HOOKS:
---
# Source: devops-info-python/templates/hooks/post-install-job.yaml
...
# Source: devops-info-python/templates/hooks/pre-install-job.yaml
...
MANIFEST:
---
# Source: devops-info-python/templates/service.yaml
...
```

Real installs and upgrade:

```text
$ helm install lab10-python k8s/devops-info-python --namespace lab10 --create-namespace -f k8s/devops-info-python/values-dev.yaml --wait=watcher --wait-for-jobs
NAME: lab10-python
NAMESPACE: lab10
STATUS: deployed
REVISION: 1
DESCRIPTION: Install complete

$ helm upgrade lab10-python k8s/devops-info-python --namespace lab10 -f k8s/devops-info-python/values-prod.yaml --wait=watcher
Release "lab10-python" has been upgraded. Happy Helming!
NAME: lab10-python
STATUS: deployed
REVISION: 2
DESCRIPTION: Upgrade complete

$ docker build -t devops-info-go:lab02 app_go
$ kind load docker-image devops-info-go:lab02 --name devops-lab9

$ helm upgrade --install lab10-go k8s/devops-info-go --namespace lab10 --wait=watcher
NAME: lab10-go
NAMESPACE: lab10
STATUS: deployed
REVISION: 2
DESCRIPTION: Upgrade complete
```

Release inventory:

```text
$ helm list -n lab10
NAME        	NAMESPACE	REVISION	UPDATED                             	STATUS  	CHART                   	APP VERSION
lab10-go    	lab10    	2       	2026-04-02 14:48:04.154838 +0300 MSK	deployed	devops-info-go-0.1.0    	1.0.0
lab10-python	lab10    	3       	2026-04-02 16:01:35.750199 +0300 MSK	deployed	devops-info-python-0.1.0	1.0.0
```

Cluster resources after the final prod rollout:

```text
$ kubectl get all -n lab10
NAME                                                   READY   STATUS    RESTARTS   AGE
pod/lab10-go-devops-info-go-5cdc8dcf6f-7b9bv           1/1     Running   0          10m
pod/lab10-go-devops-info-go-5cdc8dcf6f-v722n           1/1     Running   0          10m
pod/lab10-python-devops-info-python-75c6d5dff8-4mxwh   1/1     Running   0          9m6s
pod/lab10-python-devops-info-python-75c6d5dff8-bkrdk   1/1     Running   0          9m40s
pod/lab10-python-devops-info-python-75c6d5dff8-m6twv   1/1     Running   0          9m58s
pod/lab10-python-devops-info-python-75c6d5dff8-t2kzr   1/1     Running   0          9m23s

NAME                                      TYPE           CLUSTER-IP      EXTERNAL-IP   PORT(S)        AGE
service/lab10-go-devops-info-go           ClusterIP      10.96.37.21     <none>        80/TCP         10m
service/lab10-python-devops-info-python   LoadBalancer   10.96.238.197   <pending>     80/TCP         156m

NAME                                              READY   UP-TO-DATE   AVAILABLE   AGE
deployment.apps/lab10-go-devops-info-go           2/2     2            2           10m
deployment.apps/lab10-python-devops-info-python   4/4     4            4           22m
```

Service-level evidence:

```text
$ kubectl get svc -n lab10 -o wide
NAME                              TYPE           CLUSTER-IP      EXTERNAL-IP   PORT(S)        AGE    SELECTOR
lab10-go-devops-info-go           ClusterIP      10.96.37.21     <none>        80/TCP         144m   app.kubernetes.io/instance=lab10-go,app.kubernetes.io/name=devops-info-go
lab10-python-devops-info-python   LoadBalancer   10.96.238.197   <pending>     80/TCP         156m   app.kubernetes.io/instance=lab10-python,app.kubernetes.io/name=devops-info-python
```

Upgrade result from Kubernetes perspective:

```text
$ kubectl describe deployment -n lab10 lab10-python-devops-info-python
Replicas:               4 desired | 4 updated | 4 total | 4 available | 0 unavailable
StrategyType:           RollingUpdate
RollingUpdateStrategy:  0 max unavailable, 1 max surge
Limits:
  cpu:     500m
  memory:  512Mi
Requests:
  cpu:      150m
  memory:   192Mi
Environment:
  HOST:        0.0.0.0
  PORT:        3000
  LOG_LEVEL:   INFO
```

Fresh prod install versus dev-to-prod upgrade parity:

```text
$ kubectl get svc -n lab10-svc-test fresh-prod-devops-info-python -o yaml
spec:
  allocateLoadBalancerNodePorts: false
  ports:
  - name: http
    port: 80
    protocol: TCP
    targetPort: http
  type: LoadBalancer

$ kubectl get svc -n lab10-svc-test upgrade-prod-devops-info-python -o yaml
spec:
  allocateLoadBalancerNodePorts: false
  ports:
  - name: http
    port: 80
    protocol: TCP
    targetPort: http
  type: LoadBalancer
```

The important point is that neither final Service contains `nodePort`, so `dev -> prod` now converges to the same Service shape as a fresh prod install.

## Operations

Commands used for normal lifecycle operations:

```bash
# Install development environment
helm install lab10-python k8s/devops-info-python \
  --namespace lab10 \
  --create-namespace \
  -f k8s/devops-info-python/values-dev.yaml \
  --wait=watcher \
  --wait-for-jobs

# Upgrade to production profile
helm upgrade lab10-python k8s/devops-info-python \
  --namespace lab10 \
  -f k8s/devops-info-python/values-prod.yaml \
  --wait=watcher

# Prepare the local-kind bonus image
docker build -t devops-info-go:lab02 app_go
kind load docker-image devops-info-go:lab02 --name devops-lab9

# Install bonus application
helm install lab10-go k8s/devops-info-go \
  --namespace lab10 \
  --wait=watcher

# Inspect release history
helm history lab10-python -n lab10

# Roll back Python release to revision 1
helm rollback lab10-python 1 -n lab10

# Remove releases
helm uninstall lab10-python -n lab10
helm uninstall lab10-go -n lab10
```

Observed history for rollback target selection:

```text
$ helm history lab10-python -n lab10
REVISION	UPDATED                 	STATUS    	CHART                   	APP VERSION	DESCRIPTION
1       	Thu Apr  2 13:27:53 2026	superseded	devops-info-python-0.1.0	1.0.0      	Install complete
2       	Thu Apr  2 13:37:22 2026	superseded	devops-info-python-0.1.0	1.0.0      	Upgrade complete
3       	Thu Apr  2 16:01:35 2026	deployed  	devops-info-python-0.1.0	1.0.0      	Upgrade complete
```

## Testing And Validation

Application accessibility checks:

```text
$ kubectl port-forward -n lab10 svc/lab10-python-devops-info-python 18080:80
$ curl -s http://127.0.0.1:18080/health
{"status":"healthy","timestamp":"2026-04-02T10:44:15.602538+00:00","uptime_seconds":411}

$ kubectl port-forward -n lab10 svc/lab10-go-devops-info-go 18081:80
$ curl -s http://127.0.0.1:18081/health
{"status":"healthy","timestamp":"2026-04-02T10:44:53.55119792Z","uptime_seconds":477}
```

Final health state in the main namespace:

```text
$ kubectl get pods -n lab10 -o wide
NAME                                               READY   STATUS    RESTARTS   AGE     IP            NODE
lab10-go-devops-info-go-5cdc8dcf6f-7b9bv           1/1     Running   0          10m     10.244.1.10   devops-lab9-worker
lab10-go-devops-info-go-5cdc8dcf6f-v722n           1/1     Running   0          10m     10.244.1.11   devops-lab9-worker
lab10-python-devops-info-python-75c6d5dff8-4mxwh   1/1     Running   0          9m8s    10.244.1.18   devops-lab9-worker
lab10-python-devops-info-python-75c6d5dff8-bkrdk   1/1     Running   0          9m42s   10.244.1.16   devops-lab9-worker
lab10-python-devops-info-python-75c6d5dff8-m6twv   1/1     Running   0          10m     10.244.1.15   devops-lab9-worker
lab10-python-devops-info-python-75c6d5dff8-t2kzr   1/1     Running   0          9m25s   10.244.1.17   devops-lab9-worker
```

## Bonus Task - Library Chart

Bonus requirements were implemented by splitting the workload into two application charts and one reusable library chart:

- `k8s/devops-info-python`
- `k8s/devops-info-go`
- `k8s/common-lib`

Both application charts declare the same dependency:

```yaml
dependencies:
  - name: common-lib
    version: 0.1.0
    repository: file://../common-lib
```

Shared logic moved to the library chart:

- standardized resource names via `common.fullname`;
- common Helm/Kubernetes labels via `common.labels`;
- matching selectors via `common.selectorLabels`;
- reusable HTTP probe rendering via `common.httpProbe`.

Benefits of this approach:

- less duplication between Python and Go charts;
- consistent naming and label conventions across releases;
- future Lab 11+ changes can be applied once in the library helpers instead of editing both charts separately.

Bonus deployment evidence is included in the main `lab10` namespace output above: both `lab10-python` and `lab10-go` were installed successfully and remained healthy.

Important operational note for the bonus chart:

- default `values.yaml` is installable and points to `devops-info-go:lab02`, which matches the Lab 9 local-kind workflow;
- on a clean machine, local `kind` installs still require `docker build` plus `kind load docker-image`;
- non-kind installs should override `image.repository` and `image.tag` to a registry-backed image before running `helm install`.
