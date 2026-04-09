# Helm Chart Documentation — devops-info-service

## 1. Chart Overview

### Chart Structure

```
k8s/
├── devops-info-service/          # Main Python app chart
│   ├── Chart.yaml                # Chart metadata + dependency on common-lib
│   ├── values.yaml               # Default configuration values
│   ├── values-dev.yaml           # Development overrides
│   ├── values-prod.yaml          # Production overrides
│   ├── charts/                   # Bundled dependencies (common-lib)
│   └── templates/
│       ├── _helpers.tpl          # Template helpers (name, fullname, labels)
│       ├── deployment.yaml       # Deployment manifest template
│       ├── service.yaml          # Service manifest template
│       ├── NOTES.txt             # Post-install usage notes
│       └── hooks/
│           ├── pre-install-job.yaml   # Pre-install validation hook
│           └── post-install-job.yaml  # Post-install smoke test hook
├── go-app/                       # Go app chart (uses common-lib)
│   ├── Chart.yaml
│   ├── values.yaml
│   ├── charts/
│   └── templates/
│       ├── _helpers.tpl
│       ├── deployment.yaml
│       ├── service.yaml
│       └── NOTES.txt
└── common-lib/                   # Library chart (shared templates)
    ├── Chart.yaml                # type: library
    └── templates/
        └── _helpers.tpl          # Common labels, selectors, naming
```

### Key Template Files

| File | Purpose |
|------|---------|
| `_helpers.tpl` | Defines reusable template functions (name, fullname, chart, labels, selectorLabels) |
| `deployment.yaml` | Templated Deployment with configurable replicas, image, resources, probes, securityContext |
| `service.yaml` | Templated Service with configurable type and ports |
| `hooks/pre-install-job.yaml` | Pre-install/pre-upgrade validation Job |
| `hooks/post-install-job.yaml` | Post-install/post-upgrade smoke test Job |

### Values Organization

Values are organized into logical groups:
- **`replicaCount`** — number of pod replicas
- **`image.*`** — container image settings (repository, tag, pullPolicy)
- **`service.*`** — service type and port configuration
- **`resources.*`** — CPU/memory requests and limits
- **`securityContext.*`** — pod security settings
- **`startupProbe/livenessProbe/readinessProbe`** — health check configuration
- **`strategy.*`** — rolling update parameters

---

## 2. Configuration Guide

### Important Values

| Value | Default | Description |
|-------|---------|-------------|
| `replicaCount` | 3 | Number of pod replicas |
| `image.repository` | devops-info-service | Container image repository |
| `image.tag` | lab10 | Image tag |
| `image.pullPolicy` | IfNotPresent | Image pull policy |
| `service.type` | NodePort | Kubernetes Service type |
| `service.port` | 80 | Service port |
| `service.targetPort` | 5000 | Container port |
| `resources.requests.cpu` | 100m | CPU request |
| `resources.requests.memory` | 128Mi | Memory request |
| `resources.limits.cpu` | 500m | CPU limit |
| `resources.limits.memory` | 256Mi | Memory limit |

### Environment Customization

**Development** (`values-dev.yaml`):
- 1 replica for minimal resource usage
- Relaxed resources (50m CPU, 64Mi memory)
- NodePort service type
- Shorter probe delays

**Production** (`values-prod.yaml`):
- 5 replicas for high availability
- Higher resources (200m CPU, 256Mi memory)
- LoadBalancer service type
- Longer initial delays for stable startup

### Example Installations

```bash
# Dev environment
helm install myapp-dev k8s/devops-info-service -f k8s/devops-info-service/values-dev.yaml

# Production environment
helm install myapp-prod k8s/devops-info-service -f k8s/devops-info-service/values-prod.yaml

# Custom override
helm install myapp k8s/devops-info-service --set replicaCount=10 --set service.type=ClusterIP
```

---

## 3. Hook Implementation

### Pre-install Hook (`pre-install-job.yaml`)

- **Type:** `pre-install`, `pre-upgrade`
- **Weight:** `-5` (runs first)
- **Purpose:** Validates deployment parameters before resources are created
- **Deletion Policy:** `hook-succeeded` — cleaned up after successful execution

### Post-install Hook (`post-install-job.yaml`)

- **Type:** `post-install`, `post-upgrade`
- **Weight:** `5` (runs after pre-install)
- **Purpose:** Smoke test that checks the service health endpoint
- **Deletion Policy:** `hook-succeeded` — cleaned up after successful execution

### Execution Order

1. Pre-install job runs (weight: -5) — validates parameters
2. Main resources (Deployment, Service) are created
3. Post-install job runs (weight: 5) — smoke tests the service

### Deletion Policies

Both hooks use `hook-succeeded` policy, which means:
- Job is deleted after it completes successfully
- If the hook fails, the Job and Pod remain for debugging
- This keeps the cluster clean during normal operations

---

## 4. Installation Evidence

### Dev Environment Install (1 replica)

```
$ helm install python-app k8s/devops-info-service -f k8s/devops-info-service/values-dev.yaml
NAME: python-app
NAMESPACE: default
STATUS: deployed
REVISION: 1

$ kubectl get all
NAME                                                 READY   STATUS    RESTARTS   AGE
pod/python-app-devops-info-service-87cbcb986-dqqxg   1/1     Running   0          41s

NAME                                     TYPE        CLUSTER-IP     EXTERNAL-IP   PORT(S)        AGE
service/python-app-devops-info-service   NodePort    10.99.206.10   <none>        80:32278/TCP   41s

deployment.apps/python-app-devops-info-service   1/1     1            1           41s
```

### Prod Environment Upgrade (5 replicas)

```
$ helm upgrade python-app k8s/devops-info-service -f k8s/devops-info-service/values-prod.yaml --set image.tag=lab10
Release "python-app" has been upgraded. Happy Helming!
REVISION: 2

$ kubectl get all
deployment.apps/python-app-devops-info-service   5/5     5            5
service/python-app-devops-info-service   LoadBalancer   10.99.206.10   <pending>     80:32278/TCP
```

### Rollback

```
$ helm rollback python-app 1
Rollback was a success! Happy Helming!

$ helm history python-app
REVISION  STATUS      DESCRIPTION
1         superseded  Install complete
2         superseded  Upgrade complete
3         deployed    Rollback to 1
```

### Both Apps Deployed (Bonus — Library Charts)

```
$ helm list
NAME        NAMESPACE  REVISION  STATUS    CHART                      APP VERSION
go-app      default    1         deployed  go-app-0.1.0               1.0.0
python-app  default    3         deployed  devops-info-service-0.1.0  1.0.0

$ kubectl get deployments
deployment.apps/go-app-go-app                    2/2     2            2
deployment.apps/python-app-devops-info-service   1/1     1            1
```

### Health Check Verification

```
$ kubectl run curl-test --image=busybox --restart=Never --rm -i -- wget -q -O- http://python-app-devops-info-service/health
{"status":"healthy","timestamp":"2026-04-02T16:28:27.067293+00:00","uptime_seconds":101}

$ kubectl run curl-test2 --image=busybox --restart=Never --rm -i -- wget -q -O- http://go-app-go-app/health
{"status":"healthy","timestamp":"2026-04-02T16:28:38Z","uptime_seconds":45}
```

### Hook Cleanup Verification

```
$ kubectl get jobs
No resources found in default namespace.
```

Hooks were cleaned up by the `hook-succeeded` deletion policy as expected.

---

## 5. Operations

### Installation

```bash
# Install with default values
helm install <release-name> k8s/devops-info-service

# Install with environment-specific values
helm install <release-name> k8s/devops-info-service -f k8s/devops-info-service/values-dev.yaml
```

### Upgrade

```bash
# Upgrade to new values
helm upgrade <release-name> k8s/devops-info-service -f k8s/devops-info-service/values-prod.yaml

# Upgrade with specific overrides
helm upgrade <release-name> k8s/devops-info-service --set image.tag=v2.0.0
```

### Rollback

```bash
# Rollback to previous revision
helm rollback <release-name> <revision>

# View history
helm history <release-name>
```

### Uninstall

```bash
helm uninstall <release-name>
```

---

## 6. Testing & Validation

### Lint Output

```
$ helm lint k8s/devops-info-service
==> Linting k8s/devops-info-service
[INFO] Chart.yaml: icon is recommended
1 chart(s) linted, 0 chart(s) failed

$ helm lint k8s/go-app
==> Linting k8s/go-app
[INFO] Chart.yaml: icon is recommended
1 chart(s) linted, 0 chart(s) failed
```

### Template Verification

```bash
helm template python-app k8s/devops-info-service
```

Renders correct Deployment, Service, and hook Job resources with proper labels, selectors, and values substitution.

### Dry-Run

```bash
helm install --dry-run --debug test-release k8s/devops-info-service
```

Shows computed values and rendered manifests without creating any resources.
