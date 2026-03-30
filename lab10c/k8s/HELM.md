# Lab 10 — Helm Package Manager

All required tasks are completed. Bonus task (library charts) is intentionally not included.

## 1) Chart Overview

Chart path: `lab10c/k8s/devops-info`

Main files:

- `Chart.yaml` — chart metadata (`apiVersion: v2`, app chart).
- `values.yaml` — default config (replicas, image, service, probes, resources, hook settings).
- `templates/deployment.yaml` — app Deployment template.
- `templates/service.yaml` — Service template.
- `templates/_helpers.tpl` — shared labels/naming helpers.
- `templates/hooks-pre-install-job.yaml` — pre-install hook job.
- `templates/hooks-post-install-job.yaml` — post-install hook job.
- `values-dev.yaml` / `values-prod.yaml` — environment overrides.

## 2) Configuration Guide

Important values:

- `replicaCount` — pod count.
- `image.repository`, `image.tag`, `image.pullPolicy` — container image settings.
- `service.type`, `service.port`, `service.targetPort`, `service.nodePort` — service exposure.
- `resources.requests/limits` — CPU and memory control.
- `livenessProbe.*`, `readinessProbe.*` — health checks (kept enabled).
- `hooks.*` — pre/post install hook behavior.

Environment files:

- `values-dev.yaml`: 1 replica, smaller resources, NodePort, `RELEASE_ID=dev`.
- `values-prod.yaml`: 3 replicas, stronger resources, LoadBalancer-ready, `RELEASE_ID=prod`.

Example commands:

```bash
helm install devops-dev lab10c/k8s/devops-info -f lab10c/k8s/devops-info/values-dev.yaml
helm upgrade devops-dev lab10c/k8s/devops-info -f lab10c/k8s/devops-info/values-prod.yaml
```

## 3) Hook Implementation

Implemented hooks:

- **pre-install** job (`weight: -5`) — runs before resource install.
- **post-install** job (`weight: 5`) — runs after install.

Annotations used:

- `"helm.sh/hook": pre-install` / `post-install`
- `"helm.sh/hook-weight": ...`
- `"helm.sh/hook-delete-policy": hook-succeeded,before-hook-creation`

Why:

- pre-install: quick validation step before main resources.
- post-install: smoke-check style task after release is up.

Execution order:

- lower weight runs first (`-5` before `5`).

Deletion behavior:

- successful jobs are cleaned automatically (`hook-succeeded`).

## 4) Installation Evidence

Helm fundamentals:

```text
helm version -> v4.0.0
kubectl cluster-info (kind-lab10) -> control plane reachable
helm show chart prometheus-community/prometheus -> chart metadata displayed
```

Release state:

```text
helm list
NAME       NAMESPACE REVISION STATUS   CHART             APP VERSION
devops-dev default   2        deployed devops-info-0.1.0 1.0.0
```

Kubernetes resources:

```text
kubectl get deploy,svc,pods -l app.kubernetes.io/instance=devops-dev
deployment/devops-dev-devops-info READY 3/3
service/devops-dev-devops-info   TYPE LoadBalancer
pods                              3/3 Running
```

Hook execution evidence:

```text
kubectl get events ... includes:
- SuccessfulCreate job/devops-dev-devops-info-pre-install
- Completed      job/devops-dev-devops-info-pre-install
- SuccessfulCreate job/devops-dev-devops-info-post-install
- Completed      job/devops-dev-devops-info-post-install
```

Hook cleanup evidence:

```text
kubectl get jobs -l app.kubernetes.io/instance=devops-dev
No resources found
```

## 5) Operations

Install:

```bash
helm install devops-dev lab10c/k8s/devops-info -f lab10c/k8s/devops-info/values-dev.yaml --wait
```

Upgrade:

```bash
helm upgrade devops-dev lab10c/k8s/devops-info -f lab10c/k8s/devops-info/values-prod.yaml --wait
```

Rollback:

```bash
helm history devops-dev
helm rollback devops-dev 1 --wait
```

Uninstall:

```bash
helm uninstall devops-dev
```

## 6) Testing & Validation

Lint:

```text
helm lint lab10c/k8s/devops-info -> 0 chart(s) failed
```

Template render:

```text
helm template devops-dev lab10c/k8s/devops-info -f values-dev.yaml
Rendered Deployment, Service, and hook Jobs with expected values.
```

Dry run:

```text
helm install --dry-run --debug devops-dev ... -f values-dev.yaml
Rendered hooks and final manifests correctly.
```

App accessibility check:

```bash
kubectl port-forward service/devops-dev-devops-info 8084:80
curl http://127.0.0.1:8084/health
```

```text
{"status":"healthy", ...}
```

## Short value statement

Helm turns static Kubernetes YAML into reusable packages.  
It makes deployments consistent, configurable per environment, and easier to upgrade/rollback.
