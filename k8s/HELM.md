# LAB 10 — Helm Package Manager

## Overview

In this lab, Kubernetes manifests from Lab 9 were converted into a reusable Helm chart.
The goal was to package the application for configurable deployments across multiple environments.

The chart supports:

- templated Deployment and Service
- configurable values
- multiple environments
- Helm lifecycle hooks
- easier upgrades, rollbacks, and reusability

## Helm Fundamentals

Helm is a package manager for Kubernetes.

Key concepts:

- **Chart** — a package of Kubernetes manifests
- **Release** — a deployed instance of a chart
- **Repository** — a collection of charts
- **Values** — configurable parameters passed into templates

### Commands used

```bash
helm version
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo update
helm search repo prometheus
helm show chart prometheus-community/prometheus
```

### Screenshot

`docs/screenshots/10-1-version.png`

## Chart Structure

Chart location:

```text
k8s/devops-chart/
```

Expected structure:

```text
k8s/devops-chart/
├── Chart.yaml
├── values.yaml
├── values-dev.yaml
├── values-prod.yaml
└── templates/
    ├── deployment.yaml
    ├── service.yaml
    ├── pre-install-job.yaml
    ├── post-install-job.yaml
    └── _helpers.tpl
```

## Chart Metadata

File:

```text
k8s/devops-chart/Chart.yaml
```

Contains:

- chart name
- version
- application version
- description
- chart type

## Values Configuration

Default values are stored in:

```text
k8s/devops-chart/values.yaml
```

Environment-specific values:

- `values-dev.yaml`
- `values-prod.yaml`

### Example configurable values

- replica count
- image repository
- image tag
- service type
- ports
- resources
- health checks

## Template Conversion

The Kubernetes manifests from Lab 9 were converted into templates.

### Files converted

- `deployment.yml` → `templates/deployment.yaml`
- `service.yml` → `templates/service.yaml`

### Templated fields

- image repository and tag
- replicas
- ports
- service type
- resource limits
- release-based names

Example:

```yaml
image: "{{ .Values.image.repository }}:{{ .Values.image.tag }}"
replicas: {{ .Values.replicaCount }}
```

## Multi-Environment Support

Two values files were created for different environments.

### Development

File:

```text
k8s/devops-chart/values-dev.yaml
```

Characteristics:

- 1 replica
- NodePort service
- lower resource requirements

### Production

File:

```text
k8s/devops-chart/values-prod.yaml
```

Characteristics:

- 3 or more replicas
- different NodePort or service config
- stronger resource settings

### Commands used

```bash
helm install dev k8s/devops-chart -f k8s/devops-chart/values-dev.yaml
helm install prod k8s/devops-chart -f k8s/devops-chart/values-prod.yaml
helm list
```

### Screenshot

`docs/screenshots/10-2-list.png`

## Hooks

Helm hooks were added to execute jobs during release lifecycle.

### Implemented hooks

- **pre-install hook**
- **post-install hook**

### Example purpose

- validation before install
- smoke test after install

### Commands used

```bash
kubectl get jobs
kubectl describe job <job-name>
kubectl logs job/<job-name>
```

## Chart Validation

Before installation, the chart was validated with:

```bash
helm lint k8s/devops-chart
helm template test k8s/devops-chart
helm install --dry-run --debug test-release k8s/devops-chart
```

## Installation Evidence

### Commands used

```bash
helm install dev k8s/devops-chart -f k8s/devops-chart/values-dev.yaml
helm install prod k8s/devops-chart -f k8s/devops-chart/values-prod.yaml
kubectl get all
kubectl get pods,svc
```

### Screenshot

`docs/screenshots/10-3-pods.png`

## Operations

### Upgrade a release

```bash
helm upgrade dev k8s/devops-chart -f k8s/devops-chart/values-dev.yaml
```

### Rollback

```bash
helm history dev
helm rollback dev 1
```

### Uninstall

```bash
helm uninstall dev
helm uninstall prod
```

### Screenshot

`docs/screenshots/10-4-rollback.png`

## Challenges and Solutions

### 1. Existing Kubernetes resources conflicted with Helm

Problem:
Helm could not install resources that were previously created manually with `kubectl`.

Solution:
Delete manually created Deployment and Service before installing through Helm.

### 2. Release name conflict

Problem:
Multiple releases tried to create the same Service name.

Solution:
Use dynamic names based on:

```yaml
{{ .Release.Name }}
```

### 3. NodePort conflict

Problem:
Both environments attempted to use the same `nodePort`.

Solution:
Move `nodePort` into `values-dev.yaml` and `values-prod.yaml` with different values.

## Conclusion

In this lab, Kubernetes manifests were successfully converted into a reusable Helm chart.

Main outcomes:

- templated deployment and service
- multi-environment support
- lifecycle hooks
- release management with Helm
- easier installation, upgrade, and rollback

Helm provides a more production-ready and maintainable way to manage Kubernetes applications compared to plain manifests.
