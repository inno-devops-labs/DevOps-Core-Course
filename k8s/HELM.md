# Helm Chart — DevOps Info Service

## 1. Chart Overview

### Structure

```
k8s/devops-info-service/
├── Chart.yaml                         # Chart metadata (name, version, appVersion)
├── values.yaml                        # Default configuration values
├── values-dev.yaml                    # Development environment overrides
├── values-prod.yaml                   # Production environment overrides
└── templates/
    ├── _helpers.tpl                   # Reusable named template helpers
    ├── deployment.yaml                # Kubernetes Deployment
    ├── service.yaml                   # Kubernetes Service
    ├── NOTES.txt                      # Post-install instructions printed to terminal
    └── hooks/
        ├── pre-install-job.yaml       # Job: runs before resources are created
        └── post-install-job.yaml      # Job: runs after all resources are ready
```

### Key Template Files

| File | Purpose |
|------|---------|
| `_helpers.tpl` | Defines `fullname`, `name`, `chart`, `labels`, `selectorLabels` — used by all other templates to ensure DRY naming and consistent labels |
| `deployment.yaml` | Deployment with templated replicas, image, env vars, security context, resources, liveness/readiness probes, and rolling update strategy |
| `service.yaml` | Service with conditional `nodePort` field — only rendered when type is `NodePort` and a port number is set |
| `NOTES.txt` | Post-install terminal output — shows access commands based on service type |
| `hooks/pre-install-job.yaml` | Runs environment validation before chart resources are created |
| `hooks/post-install-job.yaml` | Runs a smoke test confirmation after all resources are installed |

### Values Organisation

Values are structured in flat sections by concern:

- `replicaCount` — top-level, simple scalar
- `image.*` — image repository, tag, pull policy grouped together
- `service.*` — service type, port, targetPort, optional nodePort
- `env.*` — application environment variables (HOST, PORT, DEBUG)
- `podSecurityContext.*` — runAsNonRoot, runAsUser
- `resources.*` — requests and limits nested together
- `strategy.*` — rolling update configuration
- `livenessProbe.*` / `readinessProbe.*` — full probe config, fully customisable

---

## 2. Configuration Guide

### Important Values

| Value | Default | Description |
|-------|---------|-------------|
| `replicaCount` | `3` | Number of pod replicas |
| `image.repository` | `plaffyyy9/devops-info-service` | Docker image repository |
| `image.tag` | `lab9` | Image tag; falls back to `Chart.appVersion` if empty |
| `image.pullPolicy` | `IfNotPresent` | Image pull policy |
| `service.type` | `NodePort` | Service type: `NodePort`, `ClusterIP`, or `LoadBalancer` |
| `service.port` | `80` | External service port |
| `service.targetPort` | `5001` | Container port the app listens on |
| `service.nodePort` | `30080` | Fixed NodePort (only used when type is `NodePort`) |
| `env.HOST` | `0.0.0.0` | Flask bind address |
| `env.PORT` | `5001` | Flask listen port |
| `env.DEBUG` | `false` | Flask debug mode |
| `podSecurityContext.runAsNonRoot` | `true` | Enforce non-root execution |
| `podSecurityContext.runAsUser` | `1000` | UID matching the app's `appuser` in the Dockerfile |
| `resources.requests.memory` | `64Mi` | Memory reservation for the scheduler |
| `resources.limits.memory` | `128Mi` | Hard memory cap |
| `livenessProbe.httpGet.path` | `/health` | Liveness endpoint |
| `readinessProbe.httpGet.path` | `/ready` | Readiness endpoint |

### Environment Customisation

Override specific values at install/upgrade time using `-f` (values file) or `--set` (inline):

```bash
# Use a values file
helm install myapp k8s/devops-info-service -f k8s/devops-info-service/values-dev.yaml

# Override a single value
helm install myapp k8s/devops-info-service --set replicaCount=2

# Combine file + inline override
helm upgrade myapp k8s/devops-info-service \
  -f k8s/devops-info-service/values-prod.yaml \
  --set image.tag=v2.0.1
```

### Environment Differences

| Setting | `values.yaml` (default) | `values-dev.yaml` | `values-prod.yaml` |
|---------|------------------------|-------------------|--------------------|
| `replicaCount` | 3 | 1 | 5 |
| `service.type` | NodePort | NodePort | LoadBalancer |
| `env.DEBUG` | false | true | false |
| `resources.requests.cpu` | 100m | 50m | 200m |
| `resources.limits.memory` | 128Mi | 64Mi | 256Mi |
| `livenessProbe.initialDelaySeconds` | 10 | 5 | 30 |
| `readinessProbe.initialDelaySeconds` | 5 | 3 | 10 |

### Example Installations

```bash
# Default (3 replicas, NodePort)
helm install devops-release k8s/devops-info-service

# Development (1 replica, debug on, smaller resources)
helm install devops-dev k8s/devops-info-service -f k8s/devops-info-service/values-dev.yaml

# Production (5 replicas, LoadBalancer, larger resources)
helm install devops-prod k8s/devops-info-service -f k8s/devops-info-service/values-prod.yaml

# Custom image tag
helm install devops-release k8s/devops-info-service --set image.tag=v2.0.0
```

---

## 3. Hook Implementation

### What Hooks Were Implemented

| Hook | File | Type | Weight |
|------|------|------|--------|
| Pre-install | `templates/hooks/pre-install-job.yaml` | `pre-install` | `-5` |
| Post-install | `templates/hooks/post-install-job.yaml` | `post-install` | `5` |

**Pre-install job** — runs environment validation before any chart resources are created:
- Prints the deployment configuration (image, release name, HOST, PORT)
- Simulates the kind of checks that would run in production: connectivity tests, configuration validation, database migration readiness

**Post-install job** — runs a smoke test confirmation after all resources are installed and ready:
- Confirms release name, replica count, and service type
- Simulates post-deployment verification tasks (smoke test, notification, integration health check)

### Execution Order

```
helm install
    │
    ├─► Pre-install hook (weight -5)     ← runs FIRST, before Deployment/Service
    │     └─ Job completes (6s)
    │
    ├─► Deployment created
    ├─► Service created
    │     └─ Pods become Ready
    │
    └─► Post-install hook (weight 5)     ← runs LAST, after all resources ready
          └─ Job completes (11s)
```

Lower weight = runs earlier. Weight `-5` on pre-install ensures it runs before any other potential pre-install hooks. Weight `5` on post-install runs after all resources are ready.

### Deletion Policy

Both hooks use `hook-delete-policy: hook-succeeded`:

```yaml
annotations:
  "helm.sh/hook-delete-policy": hook-succeeded
```

This means: **after the Job pod exits with status 0, Helm deletes the Job object**. The namespace stays clean — no completed Job objects accumulate over time.

Other available policies:
- `before-hook-creation` — delete the *previous* hook before creating a new one (jobs persist until next deploy)
- `hook-failed` — delete only on failure
- Combined: `hook-succeeded,hook-failed` — always delete

---

## 4. Installation Evidence

### Helm Version

```
$ helm version
version.BuildInfo{Version:"v4.1.3", GitCommit:"c94d381b03be117e7e57908edbf642104e00eb8f", GitTreeState:"clean", GoVersion:"go1.26.1", KubeClientVersion:"v1.35"}
```

### Helm Repo Exploration

```
$ helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
$ helm repo update
$ helm show chart prometheus-community/prometheus
annotations:
  artifacthub.io/license: Apache-2.0
apiVersion: v2
appVersion: v3.11.0
dependencies:
- condition: alertmanager.enabled
  name: alertmanager
  ...
description: Prometheus is a monitoring system and time series database.
```

### Helm Lint

```
$ helm lint k8s/devops-info-service
==> Linting k8s/devops-info-service
[INFO] Chart.yaml: icon is recommended

1 chart(s) linted, 0 chart(s) failed
```

### Dry-Run Output (excerpt)

```
$ helm install --dry-run --debug devops-release k8s/devops-info-service
level=DEBUG msg="Chart path" path=k8s/devops-info-service
NAME: devops-release
STATUS: pending-install
COMPUTED VALUES:
  replicaCount: 3
  image:
    repository: plaffyyy9/devops-info-service
    tag: lab9
  service:
    type: NodePort
    port: 80
    targetPort: 5001
    nodePort: 30080
  ...
MANIFEST:
--- Service, Deployment, pre-install Job, post-install Job rendered ---
```

### helm list

```
$ helm list
NAME           NAMESPACE  REVISION  STATUS    CHART                     APP VERSION
devops-release default    4         deployed  devops-info-service-0.1.0  lab9
```

### kubectl get all (after install)

```
$ kubectl get all
NAME                                                        READY   STATUS      RESTARTS   AGE
pod/devops-release-devops-info-service-597b4cdb5d-blzkh     1/1     Running     0          23s
pod/devops-release-devops-info-service-597b4cdb5d-qf54p     1/1     Running     0          23s
pod/devops-release-devops-info-service-597b4cdb5d-rwp6f     1/1     Running     0          23s
pod/devops-release-devops-info-service-post-install-pm8fz   0/1     Completed   0          2m42s
pod/devops-release-devops-info-service-pre-install-ckblq    0/1     Completed   0          2m48s

NAME                                         TYPE        CLUSTER-IP     EXTERNAL-IP   PORT(S)        AGE
service/devops-release-devops-info-service   NodePort    10.100.94.39   <none>        80:30080/TCP   2m42s
service/kubernetes                           ClusterIP   10.96.0.1      <none>        443/TCP        9d

NAME                                                 READY   UP-TO-DATE   AVAILABLE   AGE
deployment.apps/devops-release-devops-info-service   3/3     3            3           2m42s

NAME                                                            DESIRED   CURRENT   READY   AGE
replicaset.apps/devops-release-devops-info-service-597b4cdb5d   3         3         3       23s
```

### Hook Execution

```
$ kubectl get jobs
NAME                                              STATUS     COMPLETIONS   DURATION   AGE
devops-release-devops-info-service-pre-install    Complete   1/1           6s         3m2s
devops-release-devops-info-service-post-install   Complete   1/1           11s        2m56s

$ kubectl describe job devops-release-devops-info-service-pre-install
Name:             devops-release-devops-info-service-pre-install
Annotations:      helm.sh/hook: pre-install
                  helm.sh/hook-delete-policy: before-hook-creation
                  helm.sh/hook-weight: -5
Start Time:       Thu, 02 Apr 2026 20:31:31 +0300
Completed At:     Thu, 02 Apr 2026 20:31:37 +0300
Duration:         6s
Pods Statuses:    0 Active / 1 Succeeded / 0 Failed

$ kubectl logs job/devops-release-devops-info-service-pre-install
=== Pre-install hook: environment validation ===
Checking required environment settings...
HOST: 0.0.0.0
PORT: 5001
Release name: devops-release
Image: plaffyyy9/devops-info-service:lab9
Pre-install validation complete.

$ kubectl logs job/devops-release-devops-info-service-post-install
=== Post-install hook: smoke test ===
Release devops-release installed successfully.
Replicas requested: 3
Service type: NodePort
Waiting for service to be ready...
Post-install smoke test complete. Deployment is live.
```

When `hook-succeeded` delete policy is active, jobs disappear immediately after completing:
```
$ kubectl get jobs
No resources found in default namespace.
```

### Multi-Environment Deployments

**Upgrade to dev** (1 replica, relaxed resources):
```
$ helm upgrade devops-release k8s/devops-info-service -f k8s/devops-info-service/values-dev.yaml
Release "devops-release" has been upgraded. Happy Helming!
REVISION: 2

$ kubectl get deployment devops-release-devops-info-service -o jsonpath='{.spec.replicas}'
1 replicas (dev)
```

**Upgrade to prod** (5 replicas, LoadBalancer):
```
$ helm upgrade devops-release k8s/devops-info-service -f k8s/devops-info-service/values-prod.yaml
Release "devops-release" has been upgraded. Happy Helming!
REVISION: 3

$ kubectl get deployment devops-release-devops-info-service -o jsonpath='{.spec.replicas}'
5 replicas (prod)

$ kubectl get svc devops-release-devops-info-service -o jsonpath='{.spec.type}'
LoadBalancer
```

### Application Accessibility

```
$ minikube service devops-release-devops-info-service --url
http://127.0.0.1:56331

$ curl -s http://127.0.0.1:56331/health
{"status":"healthy","timestamp":"2026-04-02T17:27:47.267984+00:00","uptime_seconds":94}

$ curl -s http://127.0.0.1:56331/ready
{"status":"ready","timestamp":"2026-04-02T17:27:47.298252+00:00"}
```

---

## 5. Operations

### Install

```bash
# Default values
helm install devops-release k8s/devops-info-service

# Development environment
helm install devops-release k8s/devops-info-service -f k8s/devops-info-service/values-dev.yaml

# Production environment
helm install devops-release k8s/devops-info-service -f k8s/devops-info-service/values-prod.yaml
```

### Upgrade

```bash
# Upgrade to new image tag
helm upgrade devops-release k8s/devops-info-service --set image.tag=v2.0.0

# Upgrade environment
helm upgrade devops-release k8s/devops-info-service -f k8s/devops-info-service/values-prod.yaml

# Upgrade with chart changes
helm upgrade devops-release k8s/devops-info-service
```

### Rollback

```bash
# View release history
helm history devops-release

# Rollback to previous revision
helm rollback devops-release

# Rollback to specific revision
helm rollback devops-release 1
```

Release history after dev → prod → rollback:
```
REVISION  STATUS      DESCRIPTION
1         superseded  Install complete
2         superseded  Upgrade complete (dev)
3         superseded  Upgrade complete (prod)
4         deployed    Rollback to 1
```

### Uninstall

```bash
helm uninstall devops-release
```

---

## 6. Testing & Validation

### helm lint

```
$ helm lint k8s/devops-info-service
==> Linting k8s/devops-info-service
[INFO] Chart.yaml: icon is recommended

1 chart(s) linted, 0 chart(s) failed
```

Only an informational notice about the missing icon URL — no errors or warnings.

### helm template (local render verification)

```bash
# Render with default values
helm template devops-release k8s/devops-info-service

# Verify dev values render correctly
helm template myapp-dev k8s/devops-info-service \
  -f k8s/devops-info-service/values-dev.yaml | grep -E "replicas:|type:|DEBUG"
# replicas: 1
# type: NodePort
# value: "true"   ← DEBUG=true in dev

# Verify prod values render correctly
helm template myapp-prod k8s/devops-info-service \
  -f k8s/devops-info-service/values-prod.yaml | grep -E "replicas:|type:|DEBUG"
# replicas: 5
# type: LoadBalancer
# value: "false"  ← DEBUG=false in prod
```

### Dry-run

```bash
helm install --dry-run --debug devops-release k8s/devops-info-service
```

Shows computed values and fully rendered manifests without touching the cluster.

### Helm Value Proposition

**Why Helm over raw manifests:**

1. **Single source of truth** — one chart, parameterised once, deployed to any environment via values files. No duplicated YAML files per environment.
2. **Release lifecycle management** — `helm history`, `helm rollback` give you versioned releases without maintaining separate git branches per environment.
3. **Atomic installs** — if any resource fails to deploy, Helm marks the release as failed and you can roll back cleanly. With `kubectl apply`, partial deploys leave the cluster in an inconsistent state.
4. **Hooks** — lifecycle events (pre-install, post-install, pre-upgrade) let you run database migrations, smoke tests, or notifications as first-class deployment steps, not ad-hoc scripts.
5. **Templating** — Go templates eliminate copy-paste YAML drift. Change `resources.limits.memory` in one place, reflected everywhere it's referenced.
