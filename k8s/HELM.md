# Lab 10 - Helm Chart Report

## 1. Chart Overview

The Kubernetes manifests from Lab 9 were converted into a Helm chart:

```text
app-python-chart/
|-- Chart.yaml
|-- values.yaml
|-- values-dev.yaml
|-- values-prod.yaml
`-- templates/
    |-- _helpers.tpl
    |-- deployment.yaml
    |-- service.yaml
    `-- hooks/
        |-- pre-install-job.yaml
        `-- post-install-job.yaml
```

`Chart.yaml` defines the chart metadata:

```yaml
apiVersion: v2
name: app-python-chart
description: Helm chart for the DevOps Python application
type: application
version: 0.1.0
appVersion: "1.0.0"
```

The chart templates use values for replica count, image settings, service type, ports, health probes, resources, labels, node selectors, affinity, and tolerations.

## 2. Helm Fundamentals

Helm was installed and verified with:

```bash
helm version
```

Output:

```text
version.BuildInfo{Version:"v4.1.3", GitCommit:"c94d381b03be117e7e57908edbf642104e00eb8f", GitTreeState:"clean", GoVersion:"go1.26.1", KubeClientVersion:"v1.35"}
```

A public chart was inspected with:

```bash
helm show chart oci://registry-1.docker.io/bitnamicharts/nginx
```

Relevant output:

```text
Pulled: registry-1.docker.io/bitnamicharts/nginx:24.0.0
apiVersion: v2
appVersion: 1.31.0
name: nginx
version: 24.0.0
description: NGINX Open Source is a web server that can be also used as a reverse proxy, load balancer, and HTTP cache.
```

Helm's value proposition is that one reusable chart can deploy the same application to multiple environments by changing values files instead of duplicating Kubernetes YAML.

## 3. Configuration Guide

Default installation:

```bash
helm install app-python app-python-chart
```

Development installation:

```bash
helm install app-python-dev app-python-chart -f app-python-chart/values-dev.yaml
```

Production-style installation:

```bash
helm install app-python-prod app-python-chart -f app-python-chart/values-prod.yaml
```

Environment-specific values:

| File | Purpose | Main differences |
|---|---|---|
| `values.yaml` | default local configuration | 3 replicas, `NodePort`, standard resources |
| `values-dev.yaml` | development configuration | 1 replica, `NodePort`, lower CPU/memory, faster probes |
| `values-prod.yaml` | production-style configuration | 3 replicas, `LoadBalancer`, higher CPU/memory, slower startup probes |

Dev render verification:

```text
type: NodePort
replicas: 1
initialDelaySeconds: 5
initialDelaySeconds: 3
cpu: 100m
memory: 128Mi
cpu: 50m
memory: 64Mi
```

Prod render verification:

```text
type: LoadBalancer
replicas: 3
initialDelaySeconds: 30
initialDelaySeconds: 10
cpu: 500m
memory: 512Mi
cpu: 200m
memory: 256Mi
```

## 4. Hook Implementation

Two Helm lifecycle hooks were implemented:

- `templates/hooks/pre-install-job.yaml`
- `templates/hooks/post-install-job.yaml`

The pre-install hook runs before the main application resources are installed. It is used as a lightweight validation step that confirms chart values were loaded.

The post-install hook runs after the release resources are created. It is used as a lightweight post-install validation step.

Hook annotations:

```yaml
"helm.sh/hook": pre-install
"helm.sh/hook-weight": "-5"
"helm.sh/hook-delete-policy": before-hook-creation,hook-succeeded
```

```yaml
"helm.sh/hook": post-install
"helm.sh/hook-weight": "5"
"helm.sh/hook-delete-policy": before-hook-creation,hook-succeeded
```

The negative pre-install weight makes the pre-install job run before later hooks. The positive post-install weight makes the post-install job run after install resources are created. `hook-succeeded` deletes successful hook jobs, and `before-hook-creation` removes older hook jobs before a new install or upgrade creates fresh ones.

## 5. Testing And Validation

Chart lint:

```bash
helm lint app-python-chart
```

Output:

```text
==> Linting app-python-chart
[INFO] Chart.yaml: icon is recommended

1 chart(s) linted, 0 chart(s) failed
```

Template rendering:

```bash
helm template app-python app-python-chart
helm template app-python-dev app-python-chart -f app-python-chart/values-dev.yaml
helm template app-python-prod app-python-chart -f app-python-chart/values-prod.yaml
```

Dry-run install:

```bash
helm install --dry-run=client --debug test-release app-python-chart
```

Relevant output:

```text
NAME: test-release
NAMESPACE: default
STATUS: pending-install
DESCRIPTION: Dry run complete

HOOKS:
# Source: app-python-chart/templates/hooks/post-install-job.yaml
"helm.sh/hook": post-install
"helm.sh/hook-weight": "5"
"helm.sh/hook-delete-policy": before-hook-creation,hook-succeeded

# Source: app-python-chart/templates/hooks/pre-install-job.yaml
"helm.sh/hook": pre-install
"helm.sh/hook-weight": "-5"
"helm.sh/hook-delete-policy": before-hook-creation,hook-succeeded
```

## 6. Installation Evidence And Operations

The live cluster commands for the Lab 10 deployment are:

```bash
minikube start --driver=docker
minikube image build -t app-python:latest ./app_python

helm install app-python-dev app-python-chart -f app-python-chart/values-dev.yaml
helm list
kubectl get all -l app.kubernetes.io/instance=app-python-dev
kubectl get jobs -w
```

Upgrade from dev values to prod-style values:

```bash
helm upgrade app-python-dev app-python-chart -f app-python-chart/values-prod.yaml
kubectl get deployment app-python-dev-app-python-chart
kubectl get service app-python-dev-app-python-chart
```

Rollback:

```bash
helm history app-python-dev
helm rollback app-python-dev 1
```

Uninstall:

```bash
helm uninstall app-python-dev
```

Application access with the dev NodePort configuration:

```bash
minikube service app-python-dev-app-python-chart
curl http://$(minikube ip):30007/health
```

When hooks complete successfully, the jobs are deleted because the chart uses `helm.sh/hook-delete-policy: before-hook-creation,hook-succeeded`. During a live install, use `kubectl get jobs -w` in a second terminal to watch the hook jobs before Helm deletes them.
