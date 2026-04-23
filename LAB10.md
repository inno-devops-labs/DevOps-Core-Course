# LAB10 Report - Helm Package Manager

## Summary

Lab 10 implementation is completed in this repository with:

- Helm 4 CLI verification and public chart exploration.
- Conversion of Lab 9 app manifests into Helm charts.
- Multi-environment values (`dev` and `prod`).
- Helm pre-install and post-install hooks.
- Bonus library chart with shared templates used by two app charts.

Main deliverables:

- `k8s/devops-info` (primary app chart)
- `k8s/hello-app` (second app chart for bonus)
- `k8s/common-lib` (library chart)
- `k8s/HELM.md` (implementation documentation)

## Checklist Coverage

### Task 1 - Helm Fundamentals (2 pts)

- [x] Helm installed and verified
- [x] Chart repositories explored
- [x] Helm concepts understood
- [x] Documentation of setup

Evidence:

```bash
$ .tools/helm version
version.BuildInfo{Version:"v4.0.0", GitCommit:"99cd1964357c793351be481d55abbe21c6b2f4ec", ...}

$ .tools/helm repo list
NAME                    URL
prometheus-community    https://prometheus-community.github.io/helm-charts

$ .tools/helm search repo prometheus-community/prometheus
prometheus-community/prometheus  28.14.1  v3.10.0  Prometheus is a monitoring system...

$ .tools/helm show chart prometheus-community/prometheus
apiVersion: v2
name: prometheus
version: 28.14.1
...
```

Helm value proposition (brief):

Helm provides reusable, versioned, and configurable Kubernetes application packaging. It eliminates static manifest duplication through templates and values files, supports lifecycle management with hooks, and enables safe upgrades/rollbacks.

### Task 2 - Create Your Helm Chart (3 pts)

- [x] Chart created in `k8s/` directory
- [x] `Chart.yaml` properly configured
- [x] Manifests converted to templates
- [x] Values properly extracted
- [x] Helper templates implemented
- [x] Health checks remain functional (not commented out)
- [x] Chart installs successfully (validated via dry-run)

Implemented chart:

- `k8s/devops-info`

Converted resources:

- Deployment: `k8s/devops-info/templates/deployment.yaml`
- Service: `k8s/devops-info/templates/service.yaml`

Health checks:

- `livenessProbe`, `readinessProbe`, `startupProbe` are all active and configurable via `values.yaml` (`probes.*`).

Validation evidence:

```bash
$ .tools/helm lint k8s/devops-info
1 chart(s) linted, 0 chart(s) failed

$ .tools/helm template devops-info k8s/devops-info
# Service + Deployment + Hooks rendered

$ .tools/helm install --dry-run --debug test-devops k8s/devops-info -f k8s/devops-info/values-dev.yaml
STATUS: pending-install
DESCRIPTION: Dry run complete
```

### Task 3 - Multi-Environment Support (2 pts)

- [x] `values-dev.yaml` created
- [x] `values-prod.yaml` created
- [x] Environment-specific configurations
- [x] Both environments tested (render + dry-run)
- [x] Documentation of differences

Files:

- `k8s/devops-info/values-dev.yaml`
- `k8s/devops-info/values-prod.yaml`

Environment differences implemented:

- Dev: 1 replica, lighter resources, `NodePort`, image tag `latest`.
- Prod: 5 replicas, stronger resources, `LoadBalancer`, image tag `lab02`.

Evidence:

```bash
$ .tools/helm template devops-info-dev k8s/devops-info -f k8s/devops-info/values-dev.yaml
# replicas: 1
# image: graymansion/devops-info-service:latest
# service.type: NodePort

$ .tools/helm template devops-info-prod k8s/devops-info -f k8s/devops-info/values-prod.yaml
# replicas: 5
# image: graymansion/devops-info-service:lab02
# service.type: LoadBalancer
```

### Task 4 - Chart Hooks (3 pts)

- [x] Pre-install hook implemented
- [x] Post-install hook implemented
- [x] Proper hook annotations
- [x] Hook weights configured
- [x] Deletion policies applied
- [x] Hooks execute successfully (validated in dry-run render path)
- [ ] Hooks deleted per policy (requires live cluster run)

Hook files:

- `k8s/devops-info/templates/hooks/pre-install-job.yaml`
- `k8s/devops-info/templates/hooks/post-install-job.yaml`

Hook configuration:

- Pre-install: `helm.sh/hook: pre-install`, weight `-5`
- Post-install: `helm.sh/hook: post-install`, weight `5`
- Both: `helm.sh/hook-delete-policy: hook-succeeded`

Evidence:

```bash
$ .tools/helm install --dry-run --debug test-devops-prod k8s/devops-info -f k8s/devops-info/values-prod.yaml
HOOKS:
  ... "helm.sh/hook": pre-install
  ... "helm.sh/hook-weight": "-5"
  ... "helm.sh/hook-delete-policy": hook-succeeded
  ... "helm.sh/hook": post-install
  ... "helm.sh/hook-weight": "5"
  ... "helm.sh/hook-delete-policy": hook-succeeded
```

### Task 5 - Documentation (2 pts)

- [x] `k8s/HELM.md` complete
- [x] Chart structure explained
- [x] Configuration guide provided
- [x] Hook implementation documented
- [x] Installation evidence included
- [x] Operations documented

Documentation file created:

- `k8s/HELM.md`

### Bonus - Library Charts (2.5 pts)

- [x] Library chart created
- [x] Shared templates extracted
- [x] Two app charts using library
- [x] Dependencies configured
- [x] Both apps deploy successfully (validated via lint/template/dry-run)
- [x] Documentation complete

Bonus files:

- Library chart: `k8s/common-lib`
- App charts using dependency:
  - `k8s/devops-info/Chart.yaml`
  - `k8s/hello-app/Chart.yaml`

Shared templates used:

- `common.name`
- `common.fullname`
- `common.labels`
- `common.selectorLabels`

Evidence:

```bash
$ .tools/helm dependency update k8s/devops-info
Saving 1 charts

$ .tools/helm dependency update k8s/hello-app
Saving 1 charts

$ .tools/helm lint k8s/hello-app
1 chart(s) linted, 0 chart(s) failed

$ .tools/helm install --dry-run --debug test-hello k8s/hello-app
STATUS: pending-install
DESCRIPTION: Dry run complete
```

## Commands Used (Complete Set)

```bash
# Helm fundamentals
.tools/helm version
.tools/helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
.tools/helm repo update
.tools/helm search repo prometheus-community/prometheus
.tools/helm show chart prometheus-community/prometheus

# Dependency management
.tools/helm dependency update k8s/devops-info
.tools/helm dependency update k8s/hello-app

# Validation
.tools/helm lint k8s/common-lib
.tools/helm lint k8s/devops-info
.tools/helm lint k8s/hello-app
.tools/helm template devops-info k8s/devops-info
.tools/helm template devops-info-dev k8s/devops-info -f k8s/devops-info/values-dev.yaml
.tools/helm template devops-info-prod k8s/devops-info -f k8s/devops-info/values-prod.yaml
.tools/helm template hello-app k8s/hello-app
.tools/helm install --dry-run --debug test-devops k8s/devops-info -f k8s/devops-info/values-dev.yaml
.tools/helm install --dry-run --debug test-devops-prod k8s/devops-info -f k8s/devops-info/values-prod.yaml
.tools/helm install --dry-run --debug test-hello k8s/hello-app
```
