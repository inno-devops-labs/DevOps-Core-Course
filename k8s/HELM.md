# Lab 10 - Helm Package Manager

Validated on `2026-04-02` with:

- `helm v4.1.3`
- `kubectl v1.35.3`
- `kind v0.31.0`
- Kubernetes context `kind-lab09`

## 1. Helm Fundamentals

### Why Helm

Helm gives this project a reusable deployment package instead of a fixed set of manifests:

- one chart can be installed multiple times as different releases
- environment changes move into `values` files instead of editing YAML by hand
- upgrades, rollbacks, and hook-driven lifecycle tasks are built in
- shared templates can be extracted into a library chart to reduce duplication

### Helm installation

I installed Helm locally from the official release tarball into `~/.local/bin/helm`.

```bash
$ ~/.local/bin/helm version
version.BuildInfo{Version:"v4.1.3", GitCommit:"c94d381b03be117e7e57908edbf642104e00eb8f", GitTreeState:"clean", GoVersion:"go1.25.8", KubeClientVersion:"v1.35"}
```

### Public chart exploration

Repository setup and chart inspection:

```bash
$ helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
$ helm repo update
$ helm show chart prometheus-community/prometheus
```

Relevant output:

```yaml
apiVersion: v2
name: prometheus
description: Prometheus is a monitoring system and time series database.
type: application
version: 28.15.0
appVersion: v3.11.0
dependencies:
  - name: alertmanager
  - name: kube-state-metrics
  - name: prometheus-node-exporter
  - name: prometheus-pushgateway
```

This confirmed the standard Helm chart structure: metadata in `Chart.yaml`, configurable defaults in `values.yaml`, templates in `templates/`, and optional dependencies.

## 2. Chart Overview

### Structure

```text
k8s/
├── HELM.md
├── common-lib/
│   ├── Chart.yaml
│   └── templates/
│       ├── _helpers.tpl
│       ├── _probes.tpl
│       └── _security.tpl
├── devops-info/
│   ├── Chart.yaml
│   ├── Chart.lock
│   ├── charts/common-lib-0.1.0.tgz
│   ├── values.yaml
│   ├── values-dev.yaml
│   ├── values-prod.yaml
│   └── templates/
│       ├── _helpers.tpl
│       ├── deployment.yaml
│       ├── service.yaml
│       ├── NOTES.txt
│       └── hooks/
│           ├── post-install-job.yaml
│           └── pre-install-job.yaml
└── devops-info-alt/
    ├── Chart.yaml
    ├── Chart.lock
    ├── charts/common-lib-0.1.0.tgz
    ├── values.yaml
    └── templates/
        ├── _helpers.tpl
        ├── deployment.yaml
        └── service.yaml
```

### Main chart files

- `k8s/devops-info/Chart.yaml`: primary application chart metadata and dependency on `common-lib`
- `k8s/devops-info/values.yaml`: shared defaults for image, probes, resources, security context, and hooks
- `k8s/devops-info/values-dev.yaml`: development overrides
- `k8s/devops-info/values-prod.yaml`: production overrides
- `k8s/devops-info/templates/deployment.yaml`: templated workload with resources and health checks
- `k8s/devops-info/templates/service.yaml`: templated service with configurable type and ports
- `k8s/devops-info/templates/hooks/*.yaml`: lifecycle jobs
- `k8s/common-lib/templates/*.tpl`: shared naming, labels, probes, and security snippets

### Values organization strategy

Defaults live in `values.yaml`, and environment differences are layered with focused override files:

- shared baseline: image, security, probes, rollout strategy
- dev overrides: `1` replica, lower resources, `NodePort`
- prod overrides: `4` replicas, higher resources, `LoadBalancer`

## 3. Configuration Guide

### Important values

| Value | Purpose |
|---|---|
| `image.repository`, `image.tag`, `image.pullPolicy` | Container image source |
| `replicaCount` | Number of application pods |
| `service.type`, `service.port`, `service.targetPort`, `service.nodePort` | Service exposure strategy |
| `resources.requests`, `resources.limits` | CPU and memory guarantees and caps |
| `probes.startup`, `probes.liveness`, `probes.readiness` | Health check configuration |
| `securityContext.pod`, `securityContext.container` | Non-root and capability hardening |
| `env.*` | Runtime metadata passed into the FastAPI app |
| `hooks.*` | Hook image, weights, and smoke-test settings |

### Environment values

Development:

```yaml
replicaCount: 1
service:
  type: NodePort
  nodePort: 30090
resources:
  requests:
    cpu: 50m
    memory: 64Mi
  limits:
    cpu: 100m
    memory: 128Mi
```

Production:

```yaml
replicaCount: 4
service:
  type: LoadBalancer
resources:
  requests:
    cpu: 200m
    memory: 256Mi
  limits:
    cpu: 500m
    memory: 512Mi
```

### Example commands

Build dependencies:

```bash
helm dependency build k8s/devops-info
helm dependency build k8s/devops-info-alt
```

Install dev:

```bash
helm install devops-info k8s/devops-info \
  -n devops-lab10 --create-namespace \
  -f k8s/devops-info/values-dev.yaml
```

Upgrade to prod:

```bash
helm upgrade devops-info k8s/devops-info \
  -n devops-lab10 \
  -f k8s/devops-info/values-prod.yaml
```

Install the secondary chart:

```bash
helm install devops-info-alt k8s/devops-info-alt -n devops-lab10
```

## 4. Hook Implementation

### Implemented hooks

- `pre-install`: validates required values before resources are created
- `post-install`: runs an in-cluster smoke test against `http://<service>:80/health`

### Execution order

- pre-install weight: `-5`
- post-install weight: `5`

Lower weight runs first, so validation happens before workload creation and smoke testing happens after install.

### Deletion policy

Both jobs use:

```yaml
"helm.sh/hook-delete-policy": before-hook-creation,hook-succeeded
```

This removes old hook jobs before the next run and deletes successful jobs after completion.

### Hook evidence

`kubectl get jobs,pods -n devops-lab10` while the pre-install job was running:

```text
NAME                                STATUS    COMPLETIONS   DURATION   AGE
job.batch/devops-info-pre-install   Running   0/1           8s         8s

NAME                                READY   STATUS              RESTARTS   AGE
pod/devops-info-pre-install-bjjl6   0/1     ContainerCreating   0          8s
```

`kubectl describe job devops-info-pre-install -n devops-lab10`:

```text
Annotations:      helm.sh/hook: pre-install
                  helm.sh/hook-delete-policy: before-hook-creation,hook-succeeded
                  helm.sh/hook-weight: -5
...
Command:
  sh
  -c
  set -eu
  test -n "devops-info-service"
  test 80 -gt 0
  test 5000 -gt 0
  echo "Validated Helm values for devops-info"
  sleep 8
```

After install, successful hook cleanup was confirmed with:

```bash
$ kubectl get jobs -n devops-lab10
No resources found in devops-lab10 namespace.
```

Hook manifests are still visible through Helm metadata:

```bash
helm get hooks devops-info -n devops-lab10
```

## 5. Installation Evidence

### Dry-run validation

```bash
$ helm install --dry-run --debug devops-info k8s/devops-info \
  -n devops-lab10 --create-namespace \
  -f k8s/devops-info/values-dev.yaml
```

Result:

```text
NAME: devops-info
NAMESPACE: devops-lab10
STATUS: pending-install
DESCRIPTION: Dry run complete
```

The rendered manifest showed:

- dev service type `NodePort`
- `replicaCount: 1`
- hook manifests present
- health probes still enabled

### Dev install

```bash
$ helm install devops-info k8s/devops-info \
  -n devops-lab10 --create-namespace \
  -f k8s/devops-info/values-dev.yaml --wait
```

Result:

```text
NAME: devops-info
STATUS: deployed
REVISION: 1
DESCRIPTION: Install complete
```

Dev-state resources before the prod upgrade:

```text
NAME                               READY   STATUS    RESTARTS   AGE
pod/devops-info-689f48866b-fgl42   1/1     Running   0          36s

NAME                  TYPE       CLUSTER-IP    EXTERNAL-IP   PORT(S)        AGE
service/devops-info   NodePort   10.96.15.17   <none>        80:30090/TCP   36s

NAME                          READY   UP-TO-DATE   AVAILABLE   AGE
deployment.apps/devops-info   1/1     1            1           36s
```

### Prod upgrade

```bash
$ helm upgrade devops-info k8s/devops-info \
  -n devops-lab10 \
  -f k8s/devops-info/values-prod.yaml --wait
```

Result:

```text
Release "devops-info" has been upgraded. Happy Helming!
NAME: devops-info
STATUS: deployed
REVISION: 2
DESCRIPTION: Upgrade complete
```

Applied values after the upgrade:

```yaml
USER-SUPPLIED VALUES:
env:
  SERVICE_DESCRIPTION: Production deployment of the DevOps info service
  SERVICE_VERSION: 1.0.1
replicaCount: 4
service:
  nodePort: null
  type: LoadBalancer
```

### `helm list`

```text
NAME            NAMESPACE    REVISION  UPDATED                                 STATUS    CHART                 APP VERSION
devops-info     devops-lab10 2         2026-04-02 18:47:51.323415435 +0300 MSK deployed  devops-info-0.1.0     1.0.0
devops-info-alt devops-lab10 1         2026-04-02 18:49:06.993532843 +0300 MSK deployed  devops-info-alt-0.1.0 1.1.0
```

### `kubectl get all`

```text
NAME                                   READY   STATUS    RESTARTS   AGE
pod/devops-info-9c6c87c89-898j5        1/1     Running   0          95s
pod/devops-info-9c6c87c89-l6n9w        1/1     Running   0          113s
pod/devops-info-9c6c87c89-q2fwf        1/1     Running   0          61s
pod/devops-info-9c6c87c89-q2hrt        1/1     Running   0          78s
pod/devops-info-alt-66679c5f55-g7wlk   1/1     Running   0          37s
pod/devops-info-alt-66679c5f55-mk8d7   1/1     Running   0          37s

NAME                      TYPE           CLUSTER-IP     EXTERNAL-IP   PORT(S)        AGE
service/devops-info       LoadBalancer   10.96.15.17    <pending>     80:30090/TCP   2m54s
service/devops-info-alt   ClusterIP      10.96.17.238   <none>        80/TCP         37s

NAME                              READY   UP-TO-DATE   AVAILABLE   AGE
deployment.apps/devops-info       4/4     4            4           2m54s
deployment.apps/devops-info-alt   2/2     2            2           37s
```

### Accessibility checks

Because this `kind` cluster was originally created with a host mapping for `30080` from Lab 9, I verified the Helm services with `kubectl port-forward`.

Primary service:

```bash
kubectl port-forward svc/devops-info -n devops-lab10 8082:80
curl http://127.0.0.1:8082/health
curl http://127.0.0.1:8082/ready
curl http://127.0.0.1:8082/
```

Output:

```json
{"status":"healthy","service":"devops-info-service","timestamp":"2026-04-02T15:49:32.276791+00:00","uptime_seconds":98}
{"status":"ready","service":"devops-info-service","timestamp":"2026-04-02T15:49:32.279103+00:00"}
{"service":{"name":"devops-info-service","version":"1.0.1","description":"Production deployment of the DevOps info service","framework":"FastAPI","variant":"primary"}}
```

Secondary service:

```bash
kubectl port-forward svc/devops-info-alt -n devops-lab10 8083:80
curl http://127.0.0.1:8083/
```

Output:

```json
{"service":{"name":"devops-info-alt","version":"1.1.0","description":"Secondary Helm deployment of the DevOps info service","framework":"FastAPI","variant":"secondary"}}
```

## 6. Operations

Install:

```bash
helm install devops-info k8s/devops-info \
  -n devops-lab10 --create-namespace \
  -f k8s/devops-info/values-dev.yaml --wait
```

Upgrade:

```bash
helm upgrade devops-info k8s/devops-info \
  -n devops-lab10 \
  -f k8s/devops-info/values-prod.yaml --wait
```

Rollback:

```bash
helm history devops-info -n devops-lab10
helm rollback devops-info 1 -n devops-lab10 --wait
```

Uninstall:

```bash
helm uninstall devops-info -n devops-lab10
helm uninstall devops-info-alt -n devops-lab10
kubectl delete namespace devops-lab10
```

## 7. Testing & Validation

Dependency build:

```text
$ helm dependency build k8s/devops-info
Saving 1 charts
Deleting outdated charts

$ helm dependency build k8s/devops-info-alt
Saving 1 charts
Deleting outdated charts
```

Lint:

```text
$ helm lint k8s/devops-info
==> Linting k8s/devops-info
[INFO] Chart.yaml: icon is recommended
1 chart(s) linted, 0 chart(s) failed

$ helm lint k8s/devops-info-alt
==> Linting k8s/devops-info-alt
[INFO] Chart.yaml: icon is recommended
1 chart(s) linted, 0 chart(s) failed
```

Template verification:

- dev render produced `type: NodePort` and `replicas: 1`
- prod render produced `type: LoadBalancer` and `replicas: 4`
- startup, liveness, and readiness probes remained present in both renders

Dry run:

```text
STATUS: pending-install
DESCRIPTION: Dry run complete
```

Runtime validation:

- dev release installed successfully with hooks
- prod upgrade completed successfully on the same release
- both application charts are deployed in `devops-lab10`
- `GET /health`, `GET /ready`, and `GET /` returned successful responses

## 8. Bonus - Library Chart

### What was extracted

The shared library chart in `k8s/common-lib` provides:

- `common-lib.name`
- `common-lib.fullname`
- `common-lib.selectorLabels`
- `common-lib.labels`
- `common-lib.podSecurityContext`
- `common-lib.containerSecurityContext`
- `common-lib.httpProbe`

### How both charts use it

Both `k8s/devops-info` and `k8s/devops-info-alt` declare:

```yaml
dependencies:
  - name: common-lib
    version: 0.1.0
    repository: "file://../common-lib"
```

Both charts then use the shared templates for:

- naming and release-safe full names
- common labels and selectors
- pod and container security contexts
- HTTP probe rendering

### Benefits

- less duplicate template logic across the two charts
- consistent labels and security defaults
- one place to change shared naming or probe rendering behavior
- better maintainability for future labs such as secrets, config maps, and GitOps
