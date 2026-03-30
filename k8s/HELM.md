# Lab 10 — Helm Package Manager

## 1. Chart Overview

This lab converts the static Kubernetes manifests from Lab 09 into a reusable Helm chart.

Chart location:

```text
k8s/python-app/
```

Chart structure:

```text
k8s/python-app/
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

Purpose of the key files:

- `Chart.yaml` — chart metadata such as chart name, version, and application version.
- `values.yaml` — default configuration shared by all environments.
- `values-dev.yaml` — development overrides with 1 replica and lighter resources.
- `values-prod.yaml` — production-style overrides with more resources and `LoadBalancer`-ready service type.
- `templates/_helpers.tpl` — reusable helper templates for names and labels.
- `templates/deployment.yaml` — templated Deployment based on Lab 09 manifest.
- `templates/service.yaml` — templated Service based on Lab 09 manifest.
- `templates/hooks/*.yaml` — Helm hook Jobs executed before and after installation.
- `templates/NOTES.txt` — post-install usage instructions.

Values organization strategy:

- image settings are grouped under `image`
- application environment variables are grouped under `app`
- networking is grouped under `service`
- probes are split into `readinessProbe` and `livenessProbe`
- lifecycle jobs are grouped under `hooks`

---

## 2. Helm Fundamentals

### Why Helm is useful

Helm is a package manager for Kubernetes. Instead of copying raw YAML files and editing them manually, Helm lets us keep one chart and change behavior through values files. This is useful because:

- the same app can be deployed to dev and prod without duplicating manifests
- image tags, replica count, service type, and resource limits are configurable
- upgrades, rollbacks, and uninstall operations are standardized
- hooks allow small lifecycle actions during install and upgrade

Official Helm documentation describes charts as packages of Kubernetes resources and explains chart structure, values, and templates. Hooks are documented as special resources executed during release lifecycle events. 

### Helm installation

On macOS:

```bash
brew install helm
helm version
```

Example repository exploration:

```bash
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo update
helm search repo prometheus
helm show chart prometheus-community/prometheus
```

Helm’s official site documents installation and general usage, and the chart guide explains the standard chart structure. 

### Important note about Helm 4

The lab text mentions Helm 4.x, while some Helm documentation pages still note that certain template guide pages are being updated for Helm 4. The values system and chart structure used in this lab remain the normal Helm chart pattern. 

---

## 3. Configuration Guide

### Default installation

```bash
helm lint k8s/python-app
helm template demo k8s/python-app
helm install python-app-dev k8s/python-app -f k8s/python-app/values-dev.yaml
```

### Production-style installation

```bash
helm install python-app-prod k8s/python-app -f k8s/python-app/values-prod.yaml
```

### Upgrade dev release to prod settings

```bash
helm upgrade python-app-dev k8s/python-app -f k8s/python-app/values-prod.yaml
```

### Important values

- `replicaCount` — number of application Pods
- `image.repository` / `image.tag` / `image.pullPolicy` — container image settings
- `app.name` / `app.version` / `app.description` — environment variables passed into FastAPI container
- `service.type` — `NodePort` for local Minikube, `LoadBalancer` for production-like deployment
- `service.nodePort` — fixed NodePort used for local access
- `resources.*` — CPU and memory requests/limits
- `readinessProbe.*` and `livenessProbe.*` — health checks retained from Lab 09
- `hooks.*` — configuration for Helm lifecycle Jobs

### Environment differences

#### Development (`values-dev.yaml`)

- `replicaCount: 1`
- lighter CPU and memory requests/limits
- `service.type: NodePort`
- fixed NodePort for easy access in Minikube
- app version string `lab10-dev`

#### Production (`values-prod.yaml`)

- `replicaCount: 3`
- stronger CPU and memory requests/limits
- `service.type: LoadBalancer`
- app version string `lab10-prod`

This exactly matches the lab requirement: dev is smaller and local-friendly; prod is multi-replica and more production-ready.

---

## 4. Hook Implementation

Two hook Jobs were implemented.

### Pre-install hook

File:

```text
templates/hooks/pre-install-job.yaml
```

Purpose:

- runs before installation
- acts as a lightweight validation placeholder
- useful as a simple example of lifecycle automation

Configuration:

- hook type: `pre-install`
- hook weight: `-5`
- delete policy: `before-hook-creation,hook-succeeded`

### Post-install hook

File:

```text
templates/hooks/post-install-job.yaml
```

Purpose:

- runs after installation
- acts as a small smoke-test style placeholder
- demonstrates post-install automation

Configuration:

- hook type: `post-install`
- hook weight: `5`
- delete policy: `before-hook-creation,hook-succeeded`

Official Helm docs explain that hook ordering is controlled by `helm.sh/hook-weight`, and cleanup is controlled by `helm.sh/hook-delete-policy`. 

Why this policy is good here:

- `before-hook-creation` prevents stale hook resources from blocking future installs/upgrades
- `hook-succeeded` cleans successful Jobs automatically

---

## 5. Operations

### Install chart

```bash
helm install python-app-dev k8s/python-app -f k8s/python-app/values-dev.yaml
```

### Check release

```bash
helm list
helm status python-app-dev
kubectl get all
```

### Render templates locally

```bash
helm template python-app-dev k8s/python-app -f k8s/python-app/values-dev.yaml
```

### Dry run

```bash
helm install --dry-run --debug python-app-dev k8s/python-app -f k8s/python-app/values-dev.yaml
```

### Upgrade release

```bash
helm upgrade python-app-dev k8s/python-app -f k8s/python-app/values-prod.yaml
```

The `helm upgrade` command updates an existing release to a new chart version or configuration.

### Rollback release

```bash
helm rollback python-app-dev 1
```

### Uninstall release

```bash
helm uninstall python-app-dev
```

Helm documentation notes that uninstall removes the release record unless `--keep-history` is used. 

---

## 6. Testing and Validation

### Linting

```bash
helm lint k8s/python-app
```

Expected result: chart passes validation with no template syntax errors.

### Local manifest rendering

```bash
helm template python-app-dev k8s/python-app -f k8s/python-app/values-dev.yaml
```

What to check:

- Deployment is rendered with the correct image and replica count
- Service type changes according to the chosen values file
- probes are still present
- resource requests and limits are rendered correctly
- hook Jobs appear with correct annotations

### Dry-run validation

```bash
helm install --dry-run --debug python-app-dev k8s/python-app -f k8s/python-app/values-dev.yaml
```

What to check:

- no template errors
- release object renders correctly
- hooks are visible in output

### Runtime validation in Minikube

Install development version:

```bash
helm install python-app-dev k8s/python-app -f k8s/python-app/values-dev.yaml
kubectl get deployments
kubectl get pods
kubectl get svc
minikube service python-app-dev --url
```

Then test endpoints:

```bash
curl http://127.0.0.1:PORT/
curl http://127.0.0.1:PORT/health
curl http://127.0.0.1:PORT/metrics
```

Upgrade to production-style settings:

```bash
helm upgrade python-app-dev k8s/python-app -f k8s/python-app/values-prod.yaml
kubectl get deployments
kubectl get pods
kubectl get svc
```

### Hook verification

```bash
kubectl get jobs
kubectl describe job python-app-dev-pre-install
kubectl describe job python-app-dev-post-install
kubectl get pods
```

If deletion policy works quickly, the Jobs may disappear after success. That is normal and is exactly what `hook-succeeded` is supposed to do. Helm docs explicitly note that hook resources are not automatically tracked like standard release resources, so delete policy matters. 

### Application accessibility verification (Evidence)

minikube service python-app-dev --url

```bash
http://127.0.0.1:61620
Because you are using a Docker driver on darwin, the terminal needs to be open to run it.
```

curl http://127.0.0.1:61620/health

```bash
{"status":"healthy","timestamp":"2026-03-30T19:32:58.820100+00:00","uptime_seconds":2259}
```

curl http://127.0.0.1:61620/

```bash
{"service":{"name":"python-app","version":"lab10-dev","description":"DevOps course info service","framework":"FastAPI"},"system":{"hostname":"python-app-dev-67bf5ddbb7-gq852","platform":"Linux","platform_version":"Linux-6.12.67-linuxkit-aarch64-with-glibc2.41","architecture":"aarch64","cpu_count":11,"python_version":"3.13.11"},"runtime":{"uptime_seconds":2259,"uptime_human":"0 hours, 37 minutes","current_time":"2026-03-30T19:32:58.873733+00:00","timezone":"UTC"},"request":{"client_ip":"10.244.0.1","user_agent":"curl/8.7.1","method":"GET","path":"/"},"endpoints":[{"path":"/","method":"GET","description":"Service information"},{"path":"/health","method":"GET","description":"Health check"},{"path":"/metrics","method":"GET","description":"Prometheus metrics"}]}
```

curl http://127.0.0.1:61620/metrics
```bash
# HELP python_gc_objects_collected_total Objects collected during gc
# TYPE python_gc_objects_collected_total counter
python_gc_objects_collected_total{generation="0"} 11915.0
python_gc_objects_collected_total{generation="1"} 2274.0
# HELP python_info Python platform information
# TYPE python_info gauge
python_info{implementation="CPython",major="3",minor="13",patchlevel="11",version="3.13.11"} 1.0
# HELP app_requests_total Total number of HTTP requests
# TYPE app_requests_total counter
app_requests_total{endpoint="/health",method="GET",status_code="200"} 580.0
```

---

## 7. Installation Evidence

This section should be filled with your actual terminal output after you run the commands locally.

### `helm version`

```bash
version.BuildInfo{Version:"v4.1.3", GitCommit:"c94d381b03be117e7e57908edbf642104e00eb8f", GitTreeState:"clean", GoVersion:"go1.26.1", KubeClientVersion:"v1.35"}
```

### `helm show chart prometheus-community/prometheus`

```bash
annotations:
  artifacthub.io/license: Apache-2.0
  artifacthub.io/links: |
    - name: Chart Source
      url: https://github.com/prometheus-community/helm-charts
    - name: Upstream Project
      url: https://github.com/prometheus/prometheus
apiVersion: v2
appVersion: v3.10.0
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
icon: https://raw.githubusercontent.com/prometheus/prometheus.github.io/master/assets/prometheus_logo-cb55bb5c346.png
keywords:
- monitoring
- prometheus
kubeVersion: '>=1.19.0-0'
maintainers:
- email: gianrubio@gmail.com
  name: gianrubio
  url: https://github.com/gianrubio
- email: zanhsieh@gmail.com
  name: zanhsieh
  url: https://github.com/zanhsieh
- email: miroslav.hadzhiev@gmail.com
  name: Xtigyro
  url: https://github.com/Xtigyro
- email: naseem@transit.app
  name: naseemkullah
  url: https://github.com/naseemkullah
- email: rootsandtrees@posteo.de
  name: zeritti
  url: https://github.com/zeritti
name: prometheus
sources:
- https://github.com/prometheus/alertmanager
- https://github.com/prometheus/prometheus
- https://github.com/prometheus/pushgateway
- https://github.com/prometheus/node_exporter
- https://github.com/kubernetes/kube-state-metrics
type: application
version: 28.14.1
```

### `helm list`

```bash
NAME            NAMESPACE   REVISION   STATUS    CHART            APP VERSION
python-app-dev  default     1          deployed  python-app-0.1.0 lab10
```

### `kubectl get all`

```bash
NAME                                  READY   STATUS    RESTARTS   AGE
pod/python-app-dev-67bf5ddbb7-gq852   1/1     Running   0          3m3s

NAME                     TYPE       CLUSTER-IP       EXTERNAL-IP   PORT(S)        AGE
service/python-app-dev   NodePort   10.104.215.121   <none>        80:30081/TCP   3m3s

NAME                             READY   UP-TO-DATE   AVAILABLE   AGE
deployment.apps/python-app-dev   1/1     1            1           3m3s

NAME                                        DESIRED   CURRENT   READY   AGE
replicaset.apps/python-app-dev-67bf5ddbb7   1         1         1       3m3s
```

### `kubectl get jobs`

```bash
No resources found in default namespace. 
(Hook jobs were automatically deleted after successful completion because the chart uses the hook-succeeded deletion policy.)
```

### `helm lint`

```bash
==> Linting k8s/python-app
[INFO] Chart.yaml: icon is recommended

1 chart(s) linted, 0 chart(s) failed
```

### `helm install --dry-run --debug`

```bash
level=WARN msg="--dry-run is deprecated and should be replaced with '--dry-run=client'"
level=DEBUG msg="Original chart version" version=""
level=DEBUG msg="Chart path" path=/Users/darriyano/Desktop/DevOps-Core-Course-lab10/k8s/python-app
level=DEBUG msg="number of dependencies in the chart" chart=python-app dependencies=0
NAME: python-app-dev
LAST DEPLOYED: Tue Mar 31 00:18:53 2026
NAMESPACE: default
STATUS: pending-install
REVISION: 1
DESCRIPTION: Dry run complete
TEST SUITE: None

USER-SUPPLIED VALUES:
app:
  version: lab10-dev
image:
  pullPolicy: Never
  tag: latest
replicaCount: 1
resources:
  limits:
    cpu: 100m
    memory: 128Mi
  requests:
    cpu: 50m
    memory: 64Mi
service:
  nodePort: 30081
  port: 80
  targetPort: 5000
  type: NodePort

HOOKS:
---
# Source: python-app/templates/hooks/post-install-job.yaml
apiVersion: batch/v1
kind: Job
metadata:
  name: "python-app-dev-post-install"
  annotations:
    "helm.sh/hook": post-install
    "helm.sh/hook-weight": "5"
    "helm.sh/hook-delete-policy": "before-hook-creation,hook-succeeded"
---
# Source: python-app/templates/hooks/pre-install-job.yaml
apiVersion: batch/v1
kind: Job
metadata:
  name: "python-app-dev-pre-install"
  annotations:
    "helm.sh/hook": pre-install
    "helm.sh/hook-weight": "-5"
    "helm.sh/hook-delete-policy": "before-hook-creation,hook-succeeded"

MANIFEST:
---
# Source: python-app/templates/service.yaml
apiVersion: v1
kind: Service
metadata:
  name: python-app-dev
spec:
  type: NodePort
  ports:
    - name: http
      port: 80
      targetPort: 5000
      nodePort: 30081
---
# Source: python-app/templates/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: python-app-dev
spec:
  replicas: 1

NOTES:
1. Get the release status:
   helm status python-app-dev

2. Check the Kubernetes objects:
   kubectl get all -l app.kubernetes.io/instance=python-app-dev

3. If the service type is NodePort, get the URL with Minikube:
   minikube service python-app-dev --url
```

---

### `helm upgrade python-app-dev k8s/python-app -f k8s/python-app/values-prod.yaml`

```bash
Release "python-app-dev" has been upgraded. Happy Helming!
NAME: python-app-dev
LAST DEPLOYED: Tue Mar 31 00:33:30 2026
NAMESPACE: default
STATUS: deployed
REVISION: 2
DESCRIPTION: Upgrade complete
TEST SUITE: None
```

### `helm list after upgrade`

```bash
NAME            NAMESPACE       REVISION        UPDATED                                 STATUS   CHART            APP VERSION
python-app-dev  default         2               2026-03-31 00:33:30.735542 +0500 +05    deployed python-app-0.1.0 lab10
```

### `kubectl get deployment python-app-dev`

```bash
NAME             READY   UP-TO-DATE   AVAILABLE   AGE
python-app-dev   3/3     3            3           41m
```

### `kubectl get pods -l app.kubernetes.io/instance=python-app-dev`

```bash
NAME                              READY   STATUS    RESTARTS   AGE
python-app-dev-7b4974577c-97xr6   1/1     Running   0          3m26s
python-app-dev-7b4974577c-qjcml   1/1     Running   0          3m11s
python-app-dev-7b4974577c-s95jr   1/1     Running   0          3m18s
```

### `kubectl get svc python-app-dev`

```bash
NAME             TYPE           CLUSTER-IP       EXTERNAL-IP   PORT(S)        AGE
python-app-dev   LoadBalancer   10.104.215.121   <pending>     80:30081/TCP   41m
```

### `kubectl rollout status deployment/python-app-dev`

```bash
deployment "python-app-dev" successfully rolled out
```
