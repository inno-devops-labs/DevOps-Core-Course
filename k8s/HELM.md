# Lab 10 - Helm Package Manager

## 1. Chart Overview

### Helm Fundamentals

Helm is valuable here because it turns the static Lab 9 manifests into a reusable package with:

- templated configuration instead of hardcoded values
- release history for upgrade and rollback
- environment-specific overrides via values files
- lifecycle hooks for validation and smoke testing

### Helm Setup Evidence

Helm is installed from the apt repository and the active binary resolves to `/usr/sbin/helm`.

`helm version`:

```text
version.BuildInfo{Version:"v3.20.0", GitCommit:"b2e4314fa0f229a1de7b4c981273f61d69ee5a59", GitTreeState:"clean", GoVersion:"go1.25.6"}
```

Repository setup:

```bash
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo update
```

Repository exploration:

```text
NAME                            CHART VERSION  APP VERSION  DESCRIPTION
prometheus-community/prometheus 28.15.0        v3.11.0      Prometheus is a monitoring system and time series database.
```

`helm show chart prometheus-community/prometheus` excerpt:

```text
apiVersion: v2
name: prometheus
description: Prometheus is a monitoring system and time series database.
type: application
version: 28.15.0
appVersion: v3.11.0
```

### Chart Structure

Chart location:

```text
k8s/devops-info-service/
├── Chart.yaml
├── values.yaml
├── values-dev.yaml
├── values-prod.yaml
└── templates/
    ├── _helpers.tpl
    ├── deployment.yaml
    ├── service.yaml
    ├── NOTES.txt
    └── hooks/
        ├── pre-install-job.yaml
        └── post-install-job.yaml
```

Key template files:

- `templates/deployment.yaml`: main Flask Deployment with probes, resources, rolling update strategy, and non-root security settings
- `templates/service.yaml`: Service template supporting `NodePort` and `LoadBalancer`
- `templates/_helpers.tpl`: reusable naming and labels helpers
- `templates/hooks/pre-install-job.yaml`: validates basic values before install
- `templates/hooks/post-install-job.yaml`: smoke-tests `/health` after install
- `templates/NOTES.txt`: post-install operator hints

### Values Organization Strategy

The values structure mirrors the Kubernetes manifest concerns:

- `image.*` for repository, tag, and pull policy
- `service.*` for type and port exposure
- `resources.*` for requests and limits
- `livenessProbe` and `readinessProbe` kept configurable, never removed
- `hooks.*` for lifecycle behavior
- `deploymentStrategy`, `minReadySeconds`, and `revisionHistoryLimit` for rollout behavior

## 2. Configuration Guide

### Important Values

- `replicaCount`: number of pod replicas
- `image.repository` / `image.tag`: container image source
- `containerPort`: container listening port
- `service.type`: `NodePort` for local access, `LoadBalancer` for production-style exposure
- `service.nodePort`: fixed local NodePort for dev install
- `resources.requests` / `resources.limits`: scheduler and runtime resource boundaries
- `livenessProbe` / `readinessProbe`: health-check timings and paths
- `hooks.enabled`: enables lifecycle Jobs

### Default Values

The chart default in `values.yaml` matches the Lab 9 baseline:

- `replicaCount: 3`
- image `devops-info-service:lab09`
- `NodePort` service
- resource requests `100m / 128Mi`
- resource limits `250m / 256Mi`

### Environment-Specific Values

`values-dev.yaml`:

- `replicaCount: 1`
- `NodePort` service on `30081`
- lighter resources: `50m / 64Mi` requests and `100m / 128Mi` limits
- faster probe startup timings

`values-prod.yaml`:

- `replicaCount: 3`
- `LoadBalancer` service
- stronger resources: `150m / 192Mi` requests and `500m / 512Mi` limits
- production-style probe timings

### Example Commands

Development install:

```bash
helm install lab10-devops k8s/devops-info-service -f k8s/devops-info-service/values-dev.yaml --wait --wait-for-jobs --debug
```

Production-style upgrade:

```bash
helm upgrade lab10-devops k8s/devops-info-service -f k8s/devops-info-service/values-prod.yaml --wait --debug
```

Render without installing:

```bash
helm template lab10-devops k8s/devops-info-service -f k8s/devops-info-service/values-dev.yaml
```

## 3. Hook Implementation

### Implemented Hooks

#### Pre-install Hook

File: `templates/hooks/pre-install-job.yaml`

Purpose:

- validate critical values before installation starts
- fail early if `replicaCount` or `containerPort` is invalid

Behavior:

- hook type: `pre-install`
- weight: `-5`
- delete policy: `before-hook-creation,hook-succeeded`

#### Post-install Hook

File: `templates/hooks/post-install-job.yaml`

Purpose:

- run a basic smoke test against `http://<service>:80/health`
- verify the application actually responds after install

Behavior:

- hook type: `post-install`
- weight: `5`
- delete policy: `before-hook-creation,hook-succeeded`

### Execution Order

1. Pre-install validation job runs first because of weight `-5`
2. Helm creates the Service and Deployment
3. Helm waits for the workload to become ready
4. Post-install smoke test runs last because of weight `5`

### Hook Evidence

`kubectl get jobs` snapshots during install:

```text
--- snapshot 11 ---
NAME                                           STATUS    COMPLETIONS   DURATION   AGE
lab10-devops-devops-info-service-pre-install   Running   0/1           0s         0s

--- snapshot 42 ---
NAME                                            STATUS    COMPLETIONS   DURATION   AGE
lab10-devops-devops-info-service-post-install   Running   0/1           0s         0s
```

`kubectl describe job lab10-devops-devops-info-service-pre-install` excerpt:

```text
Annotations:      helm.sh/hook: pre-install
                  helm.sh/hook-delete-policy: before-hook-creation,hook-succeeded
                  helm.sh/hook-weight: -5
Image:            busybox:1.36
Command:
  echo "Validating Helm values before install"
  test 1 -ge 1
  test 5000 -ge 1
```

`kubectl describe job lab10-devops-devops-info-service-post-install` excerpt:

```text
Annotations:      helm.sh/hook: post-install
                  helm.sh/hook-delete-policy: before-hook-creation,hook-succeeded
                  helm.sh/hook-weight: 5
Image:            busybox:1.36
Command:
  RESPONSE="$(wget -qO- http://lab10-devops-devops-info-service:80/health)"
```

Deletion policy verification:

```text
$ kubectl get jobs
No resources found in default namespace.
```

That confirms the hook Jobs were cleaned up after successful execution.

## 4. Installation Evidence

### Helm List After Dev Install

```text
NAME         NAMESPACE  REVISION  UPDATED                                 STATUS    CHART                     APP VERSION
lab10-devops default    1         2026-04-02 23:04:43.723913299 +0300 MSK deployed  devops-info-service-0.1.0 1.0.0
```

### `kubectl get all` After Dev Install

```text
NAME                                                   READY   STATUS    RESTARTS   AGE
pod/lab10-devops-devops-info-service-6dfddc876-26xv4   1/1     Running   0          47s

NAME                                       TYPE       CLUSTER-IP       EXTERNAL-IP   PORT(S)        AGE
service/lab10-devops-devops-info-service   NodePort   10.101.159.210   <none>        80:30081/TCP   47s

NAME                                               READY   UP-TO-DATE   AVAILABLE   AGE
deployment.apps/lab10-devops-devops-info-service   1/1     1            1           47s
```

### Application Accessibility Verification

`minikube service lab10-devops-devops-info-service --url`:

```text
http://127.0.0.1:33097
Because you are using a Docker driver on linux, the terminal needs to be open to run it.
```

`curl` output:

```text
curl -s http://127.0.0.1:33097/health
{"status":"healthy","timestamp":"2026-04-02T20:06:12.183364+00:00","uptime_seconds":57}
```

### Environment Deployment Differences

Dev install state:

```text
replicas: 1
service type: NodePort
service port: 80:30081/TCP
resources:
  requests: cpu 50m / memory 64Mi
  limits:   cpu 100m / memory 128Mi
```

Prod upgrade state:

```text
Replicas:               3 desired | 3 updated | 3 total | 3 available | 0 unavailable
Service type:           LoadBalancer
EXTERNAL-IP:            <pending>
Requests:
  cpu:                  150m
  memory:               192Mi
Limits:
  cpu:                  500m
  memory:               512Mi
```

Minikube note:

- `LoadBalancer` changed successfully on the resource
- external IP remained `<pending>` locally because Minikube was not running `minikube tunnel`

## 5. Operations

### Install

```bash
helm install lab10-devops k8s/devops-info-service -f k8s/devops-info-service/values-dev.yaml --wait --wait-for-jobs --debug
```

Result:

```text
STATUS: deployed
REVISION: 1
DESCRIPTION: Install complete
```

### Upgrade

```bash
helm upgrade lab10-devops k8s/devops-info-service -f k8s/devops-info-service/values-prod.yaml --wait --debug
```

Result:

```text
Release "lab10-devops" has been upgraded. Happy Helming!
STATUS: deployed
REVISION: 2
DESCRIPTION: Upgrade complete
```

### Rollback

```bash
helm rollback lab10-devops 1 --wait --debug
```

Result:

```text
Rollback was a success! Happy Helming!
```

Release history after rollback:

```text
REVISION  UPDATED                  STATUS      CHART                     APP VERSION  DESCRIPTION
1         Thu Apr  2 23:04:43 2026 superseded  devops-info-service-0.1.0 1.0.0        Install complete
2         Thu Apr  2 23:06:17 2026 superseded  devops-info-service-0.1.0 1.0.0        Upgrade complete
3         Thu Apr  2 23:07:03 2026 deployed    devops-info-service-0.1.0 1.0.0        Rollback to 1
```

### Uninstall

```bash
helm uninstall lab10-devops
```

Result:

```text
release "lab10-devops" uninstalled
```

Cleanup verification:

```text
$ helm list -A
NAME  NAMESPACE  REVISION  UPDATED  STATUS  CHART  APP VERSION

$ kubectl get deploy,svc,pods -l app.kubernetes.io/instance=lab10-devops
No resources found in default namespace.
```

## 6. Testing and Validation

### `helm lint`

```text
==> Linting k8s/devops-info-service
[INFO] Chart.yaml: icon is recommended

1 chart(s) linted, 0 chart(s) failed
```

### `helm template`

Development render verified:

- `replicas: 1`
- `type: NodePort`
- `nodePort: 30081`
- lighter resource profile

Production render verified:

- `replicas: 3`
- `type: LoadBalancer`
- heavier resource profile

### `helm install --dry-run --debug`

Dry-run confirmed:

- user-supplied values from `values-dev.yaml`
- computed values merged correctly with defaults
- hooks rendered with expected annotations
- deployment and service manifests matched the chart configuration

Key dry-run excerpts:

```text
STATUS: pending-install
DESCRIPTION: Dry run complete
```

```text
HOOKS:
- pre-install job with weight "-5"
- post-install job with weight "5"
```

```text
MANIFEST:
- NodePort service on 30081
- Deployment replicas: 1
```

### Application Validation

- The dev release became reachable through `minikube service`
- `curl /health` returned a healthy JSON payload
- Production upgrade completed successfully with `3/3` available replicas
- Rollback restored the dev release shape and then uninstall cleaned it up

## 7. Summary

Lab 10 is implemented as a reusable Helm chart that preserves the Lab 9 behavior while adding:

- parameterized values
- environment-specific overrides
- install-time validation hooks
- a post-install smoke test
- tested install, upgrade, rollback, and uninstall workflows

The chart passed `helm lint`, rendered correctly for dev and prod, installed successfully on Minikube, and was validated through a full release lifecycle.
