# Lab 10: Helm Chart for DevOps Info Service

## 1. Chart Overview

Helm chart created at `k8s/devops-info-service`.

```text
k8s/
|-- deployment.yml
|-- service.yml
|-- HELM.md
`-- devops-info-service/
    |-- Chart.yaml
    |-- values.yaml
    |-- values-dev.yaml
    |-- values-prod.yaml
    `-- templates/
        |-- _helpers.tpl
        |-- deployment.yaml
        |-- service.yaml
        |-- NOTES.txt
        `-- hooks/
            |-- pre-install-job.yaml
            `-- post-install-job.yaml
```

Key files:

- `k8s/deployment.yml`, `k8s/service.yml`: static manifests from Lab 9 baseline.
- `templates/deployment.yaml`: templated Deployment with replicas, resources, probes, and rolling strategy.
- `templates/service.yaml`: templated Service type/ports.
- `templates/_helpers.tpl`: shared naming and label helpers.
- `templates/hooks/*.yaml`: lifecycle hooks (`pre-install`, `post-install`).

Values strategy:

- `values.yaml`: defaults for all environments.
- `values-dev.yaml`: development overrides (1 replica, lower resources, NodePort).
- `values-prod.yaml`: production overrides (5 replicas, higher resources, LoadBalancer).

## 2. Configuration Guide

Important values:

| Value | Purpose |
|---|---|
| `replicaCount` | Number of application replicas |
| `image.repository`, `image.tag` | Container image settings |
| `service.type`, `service.port`, `service.targetPort` | Service exposure |
| `resources.requests/limits` | CPU and memory guarantees/limits |
| `livenessProbe.*`, `readinessProbe.*` | Health check behavior |
| `hooks.preInstall.*`, `hooks.postInstall.*` | Hook execution settings |

Install examples:

```bash
# Default
helm install devops-info k8s/devops-info-service

# Development
helm install devops-info-dev k8s/devops-info-service -f k8s/devops-info-service/values-dev.yaml

# Production
helm install devops-info-prod k8s/devops-info-service -f k8s/devops-info-service/values-prod.yaml

# One-off override
helm upgrade --install devops-info k8s/devops-info-service --set replicaCount=10
```

## 3. Hook Implementation

Implemented hooks:

1. `pre-install` hook
   - File: `templates/hooks/pre-install-job.yaml`
   - Weight: `-5`
   - Delete policy: `hook-succeeded`
   - Purpose: run validation before resource creation.
2. `post-install` hook
   - File: `templates/hooks/post-install-job.yaml`
   - Weight: `5`
   - Delete policy: `hook-succeeded`
   - Purpose: run smoke-check after install.

Execution order: `pre-install` (weight `-5`) -> chart resources -> `post-install` (weight `5`).

## 4. Installation Evidence

### 4.1 Helm Fundamentals (Task 1)

Current environment output:

```powershell
PS> helm version
helm : The term 'helm' is not recognized...
```

Kubernetes client is present:

```powershell
PS> kubectl version --client
Client Version: v1.34.1
Kustomize Version: v5.7.1
```

Commands to run locally after installing Helm 4.x:

```bash
helm version
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo update
helm show chart prometheus-community/prometheus
```

Helm value proposition summary:

- Reusable package format for Kubernetes resources.
- Environment customization through values files.
- Versioned release lifecycle (install/upgrade/rollback/uninstall).
- Hooks for pre/post lifecycle automation.

### 4.2 Multi-Environment Deployment (Task 3)

```bash
helm install devops-info-dev k8s/devops-info-service -f k8s/devops-info-service/values-dev.yaml
helm upgrade devops-info-dev k8s/devops-info-service -f k8s/devops-info-service/values-prod.yaml
helm get values devops-info-dev
kubectl get deploy,svc,pods
```

### 4.3 Hook Verification (Task 4)

```bash
helm lint k8s/devops-info-service
helm install --dry-run --debug test-release k8s/devops-info-service
helm install devops-info k8s/devops-info-service
kubectl get jobs
kubectl describe job devops-info-devops-info-service-pre-install
kubectl describe job devops-info-devops-info-service-post-install
```

## 5. Operations

Install:

```bash
helm install devops-info k8s/devops-info-service
```

Upgrade:

```bash
helm upgrade devops-info k8s/devops-info-service -f k8s/devops-info-service/values-prod.yaml
```

Rollback:

```bash
helm history devops-info
helm rollback devops-info 1
```

Uninstall:

```bash
helm uninstall devops-info
```

## 6. Testing and Validation

Validation commands:

```bash
helm lint k8s/devops-info-service
helm template devops-info k8s/devops-info-service
helm install --dry-run --debug devops-info-dryrun k8s/devops-info-service
```

Accessibility checks:

```bash
# NodePort
kubectl get svc
curl http://<node-ip>:<node-port>/health

# Port-forward
kubectl port-forward svc/devops-info-devops-info-service 8080:80
curl http://127.0.0.1:8080/health
```

Current session constraints:

- Helm CLI is not installed in this environment.
- Active Kubernetes API server is not available from this session.
- Commands above are provided as an executable runbook for local verification.
