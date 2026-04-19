# Helm Chart Documentation (`k8s/myapp`)

This document describes how to use the Helm chart in `k8s/myapp`.

## Chart Overview

- **Chart name:** `myapp`
- **Chart version:** `0.1.0`
- **Application version:** `1.0`
- **Type:** `application`

The chart deploys:
- A Kubernetes `Deployment` (`my-python-app`)
- A Kubernetes `Service` (`my-app-service`)
- Helm hooks (`pre-install` and `post-install` jobs)

## Directory Layout

- `k8s/myapp/Chart.yaml` - chart metadata
- `k8s/myapp/values.yaml` - default values
- `k8s/myapp/values-dev.yaml` - development overrides
- `k8s/myapp/values-prod.yaml` - production overrides
- `k8s/myapp/templates/deployment.yml` - app deployment template
- `k8s/myapp/templates/service.yml` - service template
- `k8s/myapp/templates/hooks/*` - pre/post install hook jobs

## Prerequisites

- Kubernetes cluster (local or cloud)
- `kubectl` configured for your cluster
- Helm 3+

## Install

### 1) Development install

```bash
helm install myapp-dev ./k8s/myapp \
  -f ./k8s/myapp/values.yaml \
  -f ./k8s/myapp/values-dev.yaml
```

### 2) Production install

```bash
helm install myapp-prod ./k8s/myapp \
  -f ./k8s/myapp/values.yaml \
  -f ./k8s/myapp/values-prod.yaml
```

### 3) Override values from CLI

```bash
helm install myapp ./k8s/myapp \
  --set replicaCount=3 \
  --set image.tag=v1.2.0 \
  --set service.type=LoadBalancer
```

## Upgrade and Uninstall

### Upgrade

```bash
helm upgrade myapp-dev ./k8s/myapp \
  -f ./k8s/myapp/values.yaml \
  -f ./k8s/myapp/values-dev.yaml
```

### Uninstall

```bash
helm uninstall myapp-dev
```

## Values Reference

| Key | Default | Description |
|---|---|---|
| `replicaCount` | `2` | Number of pod replicas |
| `image.repository` | `zsalavat/devops-info-service-python` | Container image repository |
| `image.tag` | `latest` | Container image tag |
| `service.type` | `NodePort` | Kubernetes service type |
| `service.port` | `80` | Service port |
| `service.targetPort` | `8000` | Pod target port in Service |

Environment-specific overrides:
- `values-dev.yaml`: `replicaCount: 1`, `service.type: NodePort`
- `values-prod.yaml`: `replicaCount: 5`, `service.type: LoadBalancer`

## Helm Hooks

The chart includes two hook jobs:

- `pre-install` hook: `templates/hooks/pre-install-job.yaml`
- `post-install` hook: `templates/hooks/post-install-job.yml`

Behavior:
- Both jobs run BusyBox with a short shell command (`echo ... && sleep 5`)
- Both are deleted after success due to `helm.sh/hook-delete-policy: hook-succeeded`

## Validate Chart

### Lint

```bash
helm lint ./k8s/myapp
```

### Render manifests locally

```bash
helm template myapp ./k8s/myapp -f ./k8s/myapp/values.yaml
```

### Dry-run install

```bash
helm install myapp ./k8s/myapp \
  -f ./k8s/myapp/values.yaml \
  --dry-run --debug
```

## Runtime Checks

```bash
kubectl get pods
kubectl get svc
kubectl get deploy
```

If using `NodePort`, access the app through the node IP and service NodePort.

## Known Notes

- `templates/service.yml` sets a fixed `nodePort: 30080`.
  - This is used only when `service.type=NodePort`.
  - For `LoadBalancer`, Kubernetes ignores `nodePort` in many setups, but behavior may vary by cluster.
- `templates/deployment.yml` uses `containerPort: 5000`, while default `service.targetPort` is `8000`.
  - Ensure your app listens on the same port exposed by the Service (`targetPort`) to avoid connectivity issues.

## Quick Troubleshooting

- Pods not ready:
  - Check probes and logs:

```bash
kubectl describe pod <pod-name>
kubectl logs <pod-name>
```

- Service unreachable:
  - Verify selector/labels and ports:

```bash
kubectl describe svc my-app-service
kubectl get endpoints my-app-service
```

