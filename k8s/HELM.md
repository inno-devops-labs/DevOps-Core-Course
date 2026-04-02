# Lab 10 Helm Implementation

## Chart Overview

This lab converts the Lab 9 Kubernetes manifests into reusable Helm charts and adds a shared library chart for common template logic.

Chart layout:

```text
k8s/
├── common-lib/
│   ├── Chart.yaml
│   └── templates/_helpers.tpl
├── devops-info-service/
│   ├── Chart.yaml
│   ├── values.yaml
│   ├── values-dev.yaml
│   ├── values-prod.yaml
│   └── templates/
│       ├── _helpers.tpl
│       ├── deployment.yaml
│       ├── service.yaml
│       ├── hooks-pre-install-job.yaml
│       ├── hooks-post-install-job.yaml
│       └── NOTES.txt
└── devops-info-service-go/
    ├── Chart.yaml
    ├── values.yaml
    └── templates/
        ├── _helpers.tpl
        ├── deployment.yaml
        ├── service.yaml
        └── NOTES.txt
```

Key files:

- `common-lib/templates/_helpers.tpl`: shared naming and label helpers used by both app charts.
- `devops-info-service/templates/deployment.yaml`: main FastAPI deployment with replica count, image, resources, probes, and security settings sourced from values.
- `devops-info-service/templates/service.yaml`: environment-specific service exposure, including optional `NodePort`.
- `devops-info-service/templates/hooks-*.yaml`: lifecycle jobs for pre-install validation and post-install smoke-test behavior.
- `devops-info-service-go/templates/*.yaml`: second application chart used for the bonus library-chart task.

Values strategy:

- `values.yaml` contains sane defaults based on Lab 9.
- `values-dev.yaml` optimizes for local development: `1` replica, smaller resources, `NodePort`.
- `values-prod.yaml` optimizes for production-style settings: `3` replicas, larger resources, `LoadBalancer`.

## Helm Fundamentals

Helm value proposition:

- Packages Kubernetes resources as versioned charts.
- Separates templates from environment-specific values.
- Tracks release history for upgrades and rollbacks.
- Supports hooks for install and upgrade lifecycle actions.
- Reduces duplication with dependencies and library charts.

Installed Helm version:

```bash
$ helm version --short
v4.1.3+gc94d381
```

Public repository and chart exploration:

```bash
$ helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
"prometheus-community" has been added to your repositories

$ helm repo update
Hang tight while we grab the latest from your chart repositories...
...Successfully got an update from the "prometheus-community" chart repository
Update Complete. ⎈Happy Helming!⎈
```

```bash
$ helm show chart prometheus-community/prometheus
apiVersion: v2
name: prometheus
type: application
version: 28.15.0
appVersion: v3.11.0
description: Prometheus is a monitoring system and time series database.
...
```

## Configuration Guide

Important values:

- `replicaCount`: pod count per environment.
- `image.repository` / `image.tag`: image source and version.
- `service.type`: `NodePort` in dev, `LoadBalancer` in prod.
- `service.nodePort`: fixed local-cluster port for dev installs.
- `resources.requests` / `resources.limits`: environment-specific sizing.
- `livenessProbe` / `readinessProbe`: configurable health-check timing without removing the probes.
- `hooks.*`: lifecycle job image, command, and hook weight configuration.

Example commands:

```bash
# dependencies
helm dependency update k8s/devops-info-service
helm dependency update k8s/devops-info-service-go

# lint
helm lint k8s/devops-info-service
helm lint k8s/devops-info-service-go

# render templates
helm template dev-release k8s/devops-info-service -f k8s/devops-info-service/values-dev.yaml
helm template prod-release k8s/devops-info-service -f k8s/devops-info-service/values-prod.yaml
helm template go-release k8s/devops-info-service-go

# install dev
helm install lab10-dev k8s/devops-info-service \
  -n devops-lab10 --create-namespace \
  -f k8s/devops-info-service/values-dev.yaml

# upgrade to prod
helm upgrade lab10-dev k8s/devops-info-service \
  -n devops-lab10 \
  -f k8s/devops-info-service/values-prod.yaml

# install second app
helm install lab10-go k8s/devops-info-service-go -n devops-lab10
```

Dev vs prod differences:

| Setting | Dev | Prod |
|---|---|---|
| Replicas | `1` | `3` |
| Image tag | `latest` | `1.0.0` |
| Service type | `NodePort` | `LoadBalancer` |
| NodePort | `30090` | not set |
| CPU request | `50m` | `200m` |
| Memory request | `64Mi` | `256Mi` |
| CPU limit | `100m` | `500m` |
| Memory limit | `128Mi` | `512Mi` |

## Hook Implementation

Implemented hooks:

- `pre-install`: validates release metadata before the main resources are installed.
- `post-install`: performs a lightweight smoke-test style action after install completes.

Hook configuration:

- Pre-install weight: `-5`
- Post-install weight: `5`
- Deletion policy: `before-hook-creation,hook-succeeded`

Rendered installed hooks:

```bash
$ helm get hooks lab10-dev -n devops-lab10
# Source: devops-info-service/templates/hooks-post-install-job.yaml
...
annotations:
  "helm.sh/hook": post-install
  "helm.sh/hook-weight": "5"
  "helm.sh/hook-delete-policy": before-hook-creation,hook-succeeded
...

# Source: devops-info-service/templates/hooks-pre-install-job.yaml
...
annotations:
  "helm.sh/hook": pre-install
  "helm.sh/hook-weight": "-5"
  "helm.sh/hook-delete-policy": before-hook-creation,hook-succeeded
...
```

Deletion-policy verification:

```bash
$ kubectl get jobs -n devops-lab10
No resources found in devops-lab10 namespace.
```

The absence of completed hook jobs after a successful install confirms `hook-succeeded` cleanup worked as intended.

Live hook-inspection capture:

To satisfy `kubectl describe job` evidence without weakening the default chart behavior, I ran a temporary verification release with the pre-install hook retained just for the capture window.

```bash
$ kubectl get jobs -n devops-lab10-capture
NAME                                          STATUS    COMPLETIONS   DURATION   AGE
capture-dev-devops-info-service-pre-install   Running   0/1           3s         3s

$ kubectl describe job capture-dev-devops-info-service-pre-install -n devops-lab10-capture
Name:             capture-dev-devops-info-service-pre-install
Namespace:        devops-lab10-capture
Annotations:      helm.sh/hook: pre-install
                  helm.sh/hook-delete-policy: before-hook-creation
                  helm.sh/hook-weight: -5
Pods Statuses:    1 Active (1 Ready) / 0 Succeeded / 0 Failed
Containers:
  pre-install-validation:
    Image:      devops-info-service:lab09
    Command:
      sh
      -c
      echo pre-install capture && sleep 120 && echo pre-install complete
Events:
  Type    Reason            Age   From            Message
  Normal  SuccessfulCreate  3s    job-controller  Created pod: capture-dev-devops-info-service-pre-install-fkvpw
```

## Installation Evidence

Live verification was performed against a local `kind` cluster named `lab10`.

Helm release list:

```bash
$ helm list -n devops-lab10
NAME      NAMESPACE    REVISION STATUS   CHART                        APP VERSION
lab10-dev devops-lab10 2        deployed devops-info-service-0.1.0    1.0.0
lab10-go  devops-lab10 1        deployed devops-info-service-go-0.1.0 1.0.0
```

Release history showing dev install then prod upgrade:

```bash
$ helm history lab10-dev -n devops-lab10
REVISION UPDATED                  STATUS     CHART                     APP VERSION DESCRIPTION
1        Thu Apr  2 17:01:12 2026 superseded devops-info-service-0.1.0 1.0.0      Install complete
2        Thu Apr  2 17:03:24 2026 deployed   devops-info-service-0.1.0 1.0.0      Upgrade complete
```

Cluster resources after production upgrade:

```bash
$ kubectl get deployment,svc,pods -n devops-lab10 -o wide
NAME                                          READY   UP-TO-DATE   AVAILABLE   AGE   IMAGES
deployment.apps/lab10-dev-devops-info-service 3/3     3            3           ...   devops-info-service:1.0.0
deployment.apps/lab10-go-devops-info-service-go
                                              2/2     2            2           ...   devops-info-service-go:lab09

NAME                                      TYPE           CLUSTER-IP      EXTERNAL-IP PORT(S)
service/lab10-dev-devops-info-service     LoadBalancer   10.96.55.186    <pending>   80:30090/TCP
service/lab10-go-devops-info-service-go   ClusterIP      10.96.186.133   <none>      80/TCP
```

Installed prod values:

```bash
$ helm get values lab10-dev -n devops-lab10
USER-SUPPLIED VALUES:
image:
  tag: 1.0.0
replicaCount: 3
service:
  type: LoadBalancer
  nodePort: null
resources:
  requests:
    cpu: 200m
    memory: 256Mi
  limits:
    cpu: 500m
    memory: 512Mi
...
```

Application accessibility verification from inside the cluster node:

```bash
$ curl http://10.96.55.186/health
{"status":"healthy","timestamp":"2026-04-02T17:04:34.248468+00:00","uptime_seconds":44}

$ curl http://10.96.55.186/ready
{"status":"ready","timestamp":"2026-04-02T17:04:34.255671+00:00","service":"devops-info-service"}

$ curl http://10.96.186.133/health
{"status":"healthy","timestamp":"2026-04-02T17:04:34Z","uptime_seconds":206}
```

## Operations

Install:

```bash
helm install lab10-dev k8s/devops-info-service \
  -n devops-lab10 --create-namespace \
  -f k8s/devops-info-service/values-dev.yaml

helm install lab10-go k8s/devops-info-service-go -n devops-lab10
```

Upgrade:

```bash
helm upgrade lab10-dev k8s/devops-info-service \
  -n devops-lab10 \
  -f k8s/devops-info-service/values-prod.yaml
```

Rollback:

```bash
helm rollback lab10-dev 1 -n devops-lab10
```

Uninstall:

```bash
helm uninstall lab10-dev -n devops-lab10
helm uninstall lab10-go -n devops-lab10
kubectl delete namespace devops-lab10
```

## Testing And Validation

Lint:

```bash
$ helm lint k8s/devops-info-service
==> Linting k8s/devops-info-service
[INFO] Chart.yaml: icon is recommended

1 chart(s) linted, 0 chart(s) failed

$ helm lint k8s/devops-info-service-go
==> Linting k8s/devops-info-service-go
[INFO] Chart.yaml: icon is recommended

1 chart(s) linted, 0 chart(s) failed
```

Template rendering:

```bash
$ helm template dev-release k8s/devops-info-service -f k8s/devops-info-service/values-dev.yaml
# rendered NodePort service, 1-replica deployment, and hook jobs

$ helm template prod-release k8s/devops-info-service -f k8s/devops-info-service/values-prod.yaml
# rendered LoadBalancer service, 3-replica deployment, and hook jobs

$ helm template go-release k8s/devops-info-service-go
# rendered Go deployment and ClusterIP service using the shared library helpers
```

Dry-run with hook visibility:

```bash
$ helm install --dry-run --debug dryrun-dev k8s/devops-info-service \
  -n devops-lab10 \
  -f k8s/devops-info-service/values-dev.yaml
NAME: dryrun-dev
STATUS: pending-install
...
HOOKS:
- pre-install job with weight -5
- post-install job with weight 5
MANIFEST:
- NodePort service using port 30090
- 1 replica dev deployment
```

## Bonus: Library Chart

Shared templates extracted into `k8s/common-lib/`:

- `common-lib.name`
- `common-lib.fullname`
- `common-lib.chart`
- `common-lib.selectorLabels`
- `common-lib.labels`

How it is used:

- `k8s/devops-info-service/Chart.yaml` declares `common-lib` as a file dependency.
- `k8s/devops-info-service-go/Chart.yaml` declares the same dependency.
- Both application charts wrap the shared helper names in local helper aliases and use them in deployments and services.

Benefits:

- Eliminates duplicated naming and label templates.
- Keeps labels consistent across both applications.
- Makes future chart additions cheaper to maintain.

Dependency packaging:

```bash
$ helm dependency update k8s/devops-info-service
Saving 1 charts
Deleting outdated charts

$ helm dependency update k8s/devops-info-service-go
Saving 1 charts
Deleting outdated charts
```
