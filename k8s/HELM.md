# Helm Chart Documentation

## Overview

This directory contains the Helm chart created for Lab 10 based on the Kubernetes deployment from Lab 9.

Chart location:
- `k8s/app-python-chart/`

The chart packages the Python application into reusable templates and supports installation through different values files for development and production-like scenarios.

Main chart files:
- `Chart.yaml` — chart metadata
- `values.yaml` — default values
- `values-dev.yaml` — development overrides
- `values-prod.yaml` — production overrides
- `templates/deployment.yaml` — application Deployment
- `templates/service.yaml` — application Service
- `templates/_helpers.tpl` — naming and labels
- `templates/hooks/pre-install-job.yaml` — pre-install lifecycle hook
- `templates/hooks/post-install-job.yaml` — post-install lifecycle hook

---

## Chart Structure

```text
k8s/app-python-chart/
├── Chart.yaml
├── values.yaml
├── values-dev.yaml
├── values-prod.yaml
└── templates/
    ├── _helpers.tpl
    ├── deployment.yaml
    ├── service.yaml
    └── hooks/
        ├── pre-install-job.yaml
        └── post-install-job.yaml
```

---

## Configuration Guide

### Default values
The default configuration is stored in `values.yaml`.

Key parameters:
- `replicaCount`
- `image.repository`
- `image.tag`
- `image.pullPolicy`
- `service.type`
- `service.port`
- `containerPort`
- `resources`
- `readinessProbe`
- `livenessProbe`
- `env`

### Development profile
`values-dev.yaml` is intended for lightweight local testing.

Important characteristics:
- 1 replica
- `NodePort` service
- smaller resource requests and limits

### Production profile
`values-prod.yaml` is intended to demonstrate a production-oriented override set.

Important characteristics:
- 3 replicas
- `LoadBalancer` service
- increased resource requests and limits
- more conservative probe timing

---

## Installation Commands

### Validate the chart

```bash
helm lint k8s/app-python-chart
helm template app-python-dev k8s/app-python-chart
helm install --dry-run --debug app-python-dev k8s/app-python-chart
```

### Create namespace

```bash
kubectl create namespace devops-lab10 --dry-run=client -o yaml | kubectl apply -f -
```

### Install development release

```bash
helm install app-python-dev k8s/app-python-chart \
  -n devops-lab10 \
  -f k8s/app-python-chart/values-dev.yaml
```

### Check release and resources

```bash
helm list -n devops-lab10
kubectl get all -n devops-lab10
```

### Access the application in minikube

```bash
DEV_URL=$(minikube service app-python-dev-app-python-chart -n devops-lab10 --url)
curl "$DEV_URL/health"
```

### Upgrade to production values

```bash
helm upgrade app-python-dev k8s/app-python-chart \
  -n devops-lab10 \
  -f k8s/app-python-chart/values-prod.yaml
```

---

## Hook Implementation

Two chart hooks are implemented as `Job` resources.

### Pre-install hook
File:
- `templates/hooks/pre-install-job.yaml`

Purpose:
- run a lightweight validation step before installation

### Post-install hook
File:
- `templates/hooks/post-install-job.yaml`

Purpose:
- run a lightweight smoke-test style step after installation

Both jobs use Helm hook annotations and `hook-succeeded` cleanup.

---

## Validation Notes

The chart was validated using:
- `helm lint`
- `helm template`
- `helm install --dry-run --debug`
- `helm install` with development values
- `helm upgrade` with production values

Validation screenshots are stored in:
- `k8s/docs/screenshots/`

Relevant evidence files:
- `task_1_helm_version.png`
- `task_1_helm_repo.png`
- `task_1_helm_chart.png`
- `task_2_create.png`
- `task_2_helm_lint_template.png`
- `task_2_helm_install.png`
- `task_3_helm_install.png`
- `task_3_helm_list.png`
- `task_3_curl_health_check.png`
- `task_3_helm_upgrade.png`
- `task_4_helm_template.png`
- `task_4_helm_install.png`

---

## Operational Notes

### Common commands

List releases:

```bash
helm list -n devops-lab10
```

Inspect rendered manifests from the installed release:

```bash
helm get manifest app-python-dev -n devops-lab10
```

Inspect applied values:

```bash
helm get values app-python-dev -n devops-lab10
```

Uninstall release:

```bash
helm uninstall app-python-dev -n devops-lab10
```

---

## Troubleshooting

### Kubernetes API unavailable after reboot
If `kubectl` cannot reach the cluster after a host reboot, verify that Docker and minikube are running:

```bash
systemctl status docker --no-pager
minikube status
minikube start --driver=docker
```

### Helm lint errors after `helm create`
The default scaffold may contain extra templates that are not used in this lab. Remove or adapt unnecessary templates before validation.

### Service access in local environment
For local development under minikube, the recommended way to access the service is:

```bash
minikube service app-python-dev-app-python-chart -n devops-lab10 --url
```

---

## Summary

This chart provides a reusable and configurable way to deploy the Lab 9 Python application with Helm. It supports:
- chart templating
- environment-specific values
- health-check preservation
- install and upgrade workflows
- lifecycle hook integration

The result is a more maintainable and realistic Kubernetes packaging approach than static manifests alone.