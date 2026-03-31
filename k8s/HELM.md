# Helm Chart Documentation (Lab 10)

## Chart Overview

This chart packages the Lab 9 Python application as a reusable Helm deployment.

### Structure

- `k8s/Chart.yaml` - chart metadata (`apiVersion: v2`, application chart, versioned)
- `k8s/values.yaml` - default config shared across environments
- `k8s/values-dev.yaml` - development overrides
- `k8s/values-prod.yaml` - production overrides
- `k8s/templates/_helpers.tpl` - reusable naming and labeling helpers
- `k8s/templates/deployment.yaml` - application Deployment template
- `k8s/templates/service.yaml` - Service template
- `k8s/templates/hooks/pre-install-job.yaml` - pre-install hook Job
- `k8s/templates/hooks/post-install-job.yaml` - post-install hook Job
- `k8s/templates/NOTES.txt` - post-install release notes

### Values organization strategy

Values are grouped by concern:

- `image` for container image settings (`repository`, `tag`, `pullPolicy`)
- `service` for service exposure (`type`, `port`, `targetPort`)
- `resources` for requests/limits
- `livenessProbe` and `readinessProbe` for health checks
- `replicaCount` and `deployment.strategy` for rollout behavior

## Helm Fundamentals Evidence

### Helm installation verification

```bash
$ ./helm-bin version
version.BuildInfo{Version:"v4.1.3", GitCommit:"c94d381b03be117e7e57908edbf642104e00eb8f", GitTreeState:"clean", GoVersion:"go1.25.8", KubeClientVersion:"v1.35"}
```

### Public chart exploration

Explored an OCI-hosted public chart:

```bash
$ ./helm-bin show chart oci://registry-1.docker.io/bitnamicharts/nginx
Pulled: registry-1.docker.io/bitnamicharts/nginx:22.6.10
Digest: sha256:d5095131fcc79a343c83f7f826fe0e7f70a797bc9c8f47ed8e9e0cff5c4cf62c
apiVersion: v2
name: nginx
version: 22.6.10
appVersion: 1.29.7
description: NGINX Open Source is a web server that can be also used as a reverse proxy, load balancer, and HTTP cache.
dependencies:
- name: common
  repository: oci://registry-1.docker.io/bitnamicharts
  version: 2.37.0
```

### Helm value proposition

Helm provides repeatable, versioned application packaging for Kubernetes through templates and values. This removes manifest duplication, supports environment-specific overrides, and enables lifecycle automation (hooks, upgrades, rollbacks) with a single release abstraction.

## Configuration Guide

### Important values

- `replicaCount` - number of pods
- `image.repository` / `image.tag` - image source and version
- `service.type` - service exposure mode (`NodePort`, `LoadBalancer`)
- `resources.requests` / `resources.limits` - CPU and memory controls
- `livenessProbe` / `readinessProbe` - health check behavior

### Environment customization

Development (`values-dev.yaml`):
- `replicaCount: 1`
- relaxed resources
- `service.type: NodePort`
- faster probe startup

Production (`values-prod.yaml`):
- `replicaCount: 5`
- stronger resources
- `service.type: LoadBalancer`
- stricter probe timings
- pinned image tag (`1.0.0`)

### Example installs

```bash
# Default values
./helm-bin install myrelease ./k8s

# Development
./helm-bin install myapp-dev ./k8s -f ./k8s/values-dev.yaml

# Production
./helm-bin install myapp-prod ./k8s -f ./k8s/values-prod.yaml
```

## Hook Implementation

Two lifecycle hooks are implemented as Kubernetes Jobs:

- `pre-install` hook (`templates/hooks/pre-install-job.yaml`)
  - Weight: `-5`
  - Purpose: run checks/tasks before main resources are installed
- `post-install` hook (`templates/hooks/post-install-job.yaml`)
  - Weight: `5`
  - Purpose: run post-deploy validation

### Execution order

Lower weights run first, so `pre-install` (`-5`) executes before `post-install` (`5`) in their respective hook phases.

### Deletion policy

Both hooks use:

- `"helm.sh/hook-delete-policy": hook-succeeded`

This keeps the cluster clean by deleting successful hook Jobs automatically.

## Installation Evidence

Cluster runtime outputs (`helm list`, `kubectl get all`, `kubectl get jobs`) must be captured on a machine with kubeconfig access to a running cluster. In this workspace, validation was completed with client-side rendering/linting.

### Dry-run output with hooks visible

```bash
$ ./helm-bin install --dry-run --debug test-release k8s
NAME: test-release
STATUS: pending-install
DESCRIPTION: Dry run complete
...
HOOKS:
# Source: my-python-app/templates/hooks/post-install-job.yaml
...
  annotations:
    "helm.sh/hook": post-install
    "helm.sh/hook-weight": "5"
    "helm.sh/hook-delete-policy": hook-succeeded
...
# Source: my-python-app/templates/hooks/pre-install-job.yaml
...
  annotations:
    "helm.sh/hook": pre-install
    "helm.sh/hook-weight": "-5"
    "helm.sh/hook-delete-policy": hook-succeeded
```

### Environment rendering evidence

- Dev render includes `replicas: 1` and `service.type: NodePort`
- Prod render includes `replicas: 5` and `service.type: LoadBalancer`

## Operations

### Install

```bash
./helm-bin install myrelease ./k8s
```

### Upgrade

```bash
./helm-bin upgrade myrelease ./k8s -f ./k8s/values-prod.yaml
```

### Rollback

```bash
./helm-bin history myrelease
./helm-bin rollback myrelease <revision>
```

### Uninstall

```bash
./helm-bin uninstall myrelease
```

## Testing & Validation

### Lint

```bash
$ ./helm-bin lint k8s
==> Linting k8s
[INFO] Chart.yaml: icon is recommended

1 chart(s) linted, 0 chart(s) failed
```

### Template verification

```bash
$ ./helm-bin template test-release k8s
# Renders Service, Deployment, and both hook Jobs with expected names and labels
```

### Dry-run verification

```bash
$ ./helm-bin install --dry-run --debug test-release k8s
# Release renders successfully with computed values and HOOKS section
```

### Application accessibility verification

After real cluster install, verify with:

```bash
kubectl get svc
kubectl get pods
kubectl port-forward svc/<service-name> 8080:80
curl http://localhost:8080/health
```
