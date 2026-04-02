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
- `values-dev.yaml`: development overrides.
- `values-prod.yaml`: production overrides.

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

Repository and public chart exploration:

```powershell
PS> helm version
version.BuildInfo{Version:"v4.1.3", GitCommit:"c94d381b03be117e7e57908edbf642104e00eb8f", GitTreeState:"clean", GoVersion:"go1.25.8", KubeClientVersion:"v1.35"}

PS> helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
"prometheus-community" has been added to your repositories

PS> helm repo update
...Successfully got an update from the "prometheus-community" chart repository
Update Complete. Happy Helming!

PS> helm show chart prometheus-community/prometheus
name: prometheus
type: application
version: 28.15.0
appVersion: v3.11.0
```

Helm value proposition:

- Reusable package format for Kubernetes resources.
- Environment customization through values files.
- Versioned release lifecycle (install/upgrade/rollback/uninstall).
- Hooks for pre/post lifecycle automation.

### 4.2 Chart Validation and Rendering (Task 2)

```powershell
PS> helm lint k8s/devops-info-service
==> Linting k8s/devops-info-service
[INFO] Chart.yaml: icon is recommended
1 chart(s) linted, 0 chart(s) failed

PS> helm template devops-info k8s/devops-info-service
# Rendered: Service, Deployment, pre-install Job hook, post-install Job hook
```

Dry-run with debug:

```powershell
PS> helm install --dry-run=client --debug test-release k8s/devops-info-service
STATUS: pending-install
DESCRIPTION: Dry run complete
HOOKS: pre-install + post-install rendered
```

### 4.3 Multi-Environment Deployment (Task 3)

Deployment evidence (`helm list`):

```powershell
PS> helm list
NAME            NAMESPACE  REVISION  STATUS    CHART                       APP VERSION
devops-info     default    1         deployed  devops-info-service-0.1.0  1.0.0
devops-info-dev default    2         deployed  devops-info-service-0.1.0  1.0.0
```

Cluster resources evidence:

```powershell
PS> kubectl get all
deployment.apps/devops-info-dev-devops-info-service   5/5
deployment.apps/devops-info-devops-info-service       3/3
service/devops-info-dev-devops-info-service           LoadBalancer 80:31911/TCP
service/devops-info-devops-info-service               NodePort     80:32071/TCP
pods: all Running
```

Environment difference confirmed:

- `devops-info-dev` uses production-scale settings after upgrade (`replicas=5`, `LoadBalancer` service).
- `devops-info` keeps default settings (`replicas=3`, `NodePort` service).

Applied values for `devops-info-dev`:

```powershell
PS> helm get values devops-info-dev
USER-SUPPLIED VALUES:
image:
  tag: 1.0.0
livenessProbe:
  initialDelaySeconds: 30
  periodSeconds: 5
readinessProbe:
  initialDelaySeconds: 10
  periodSeconds: 3
replicaCount: 5
resources:
  limits:
    cpu: 500m
    memory: 512Mi
  requests:
    cpu: 200m
    memory: 256Mi
service:
  nodePort: null
  type: LoadBalancer
```

### 4.4 Hooks Verification (Task 4)

Hook deletion policy behavior:

```powershell
PS> kubectl get jobs
No resources found in default namespace.

PS> kubectl describe job devops-info-devops-info-service-pre-install
Error from server (NotFound): jobs.batch "...-pre-install" not found

PS> kubectl describe job devops-info-devops-info-service-post-install
Error from server (NotFound): jobs.batch "...-post-install" not found
```

This is expected due `helm.sh/hook-delete-policy: hook-succeeded`.

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

Validation commands used:

```bash
helm lint k8s/devops-info-service
helm template devops-info k8s/devops-info-service
helm install --dry-run=client --debug test-release k8s/devops-info-service
```

Live deployment checks used:

```bash
helm list
kubectl get all
kubectl get jobs
```

Health endpoint verification (successful) via `port-forward`:

```bash
kubectl port-forward svc/devops-info-devops-info-service 8080:80
curl.exe http://127.0.0.1:8080/health
{"status":"healthy","timestamp":"2026-04-02T21:36:20.552Z","uptime_seconds":1593}
```
