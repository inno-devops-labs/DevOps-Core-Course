# Lab 10 — Helm Package Manager

## Chart Overview

The Lab 9 static Kubernetes manifests were converted into a reusable Helm chart located in:

```text
k8s/devops-info-service/
├── Chart.yaml
├── values.yaml
├── values-dev.yaml
├── values-prod.yaml
└── templates/
    ├── _helpers.tpl
    ├── deployment.yaml
    ├── service.yaml
    ├── NOTES.txt
    └── hooks/
        ├── pre-install-job.yaml
        └── post-install-job.yaml
```

### Key chart files

- `Chart.yaml` — chart metadata, version, description.
- `values.yaml` — default configuration shared across environments.
- `values-dev.yaml` — lightweight development overrides.
- `values-prod.yaml` — production-style overrides.
- `templates/deployment.yaml` — templated Deployment.
- `templates/service.yaml` — templated Service.
- `templates/_helpers.tpl` — reusable naming and label helpers.
- `templates/hooks/*.yaml` — Helm lifecycle hook Jobs.
- `templates/NOTES.txt` — post-install usage hints.

### Values organization strategy

The values are grouped by concern:
- `image.*` for repository, tag, and pull policy
- `service.*` for service type and ports
- `resources.*` for CPU and memory requests/limits
- `livenessProbe.*`, `readinessProbe.*`, `startupProbe.*` for health checks
- `hookJobs.*` for lifecycle hooks

This keeps the chart reusable and prevents hardcoded deployment settings.

## Configuration Guide

### Important values and their purpose

| Value | Purpose |
|---|---|
| `replicaCount` | Controls the number of Pod replicas |
| `image.repository` | Selects the container image repository |
| `image.tag` | Selects the application image version |
| `image.pullPolicy` | Controls image pulling behavior |
| `service.type` | Defines whether the Service is `NodePort` or `LoadBalancer` |
| `service.port` | External Service port |
| `service.targetPort` | Container port exposed through the Service |
| `service.nodePort` | Fixed NodePort for local minikube testing |
| `container.port` | Container HTTP port used in the Deployment |
| `resources.requests` / `resources.limits` | CPU and memory requests and limits |
| `livenessProbe.*` | Detects whether the application is still healthy |
| `readinessProbe.*` | Controls whether the Pod receives traffic |
| `startupProbe.*` | Protects slower-starting containers from early restarts |
| `hookJobs.*` | Controls pre-install and post-install hook jobs |

### Environment customization strategy

The chart uses one default file and two environment-specific override files:

- **Default values (`values.yaml`)**: local minikube-oriented defaults, `NodePort` service, 3 replicas, modest resources, and hook jobs enabled.
- **Development values (`values-dev.yaml`)**: 1 replica, lower CPU and memory settings, `NodePort`, and startup probe enabled to tolerate slower local startup.
- **Production values (`values-prod.yaml`)**: 3 replicas, `LoadBalancer` service, increased CPU and memory, image tag `1.0.0`, and more conservative probe timing.

### Example installations

#### Development deployment

```bash
helm install dev-release k8s/devops-info-service -f k8s/devops-info-service/values-dev.yaml
```

#### Production-style deployment

```bash
helm install prod-release k8s/devops-info-service -f k8s/devops-info-service/values-prod.yaml
```

#### Upgrade an existing release with production values

```bash
helm upgrade dev-release k8s/devops-info-service -f k8s/devops-info-service/values-prod.yaml
```

#### Override a single value during install or upgrade

```bash
helm upgrade --install hooks-release k8s/devops-info-service \
  -f k8s/devops-info-service/values-dev.yaml \
  --set service.nodePort=30082
```

## Hook Implementation

Two Helm lifecycle hooks were implemented.

### Implemented hooks

1. **Pre-install hook**
   - File: `templates/hooks/pre-install-job.yaml`
   - Hook type: `pre-install`
   - Purpose: run a lightweight validation step and print release metadata before the main resources are installed.

2. **Post-install hook**
   - File: `templates/hooks/post-install-job.yaml`
   - Hook type: `post-install`
   - Purpose: run a lightweight smoke-test placeholder after the release is installed.

### Hook execution order and weights

The chart uses hook weights to control execution order:

- `pre-install`: weight **`-5`**
- `post-install`: weight **`5`**

This ensures that the pre-install job runs before the main install phase and the post-install job runs afterward.

### Deletion policies

Both hooks use:

```yaml
helm.sh/hook-delete-policy: before-hook-creation,hook-succeeded
```

This means:

- **`hook-succeeded`** removes successful hook jobs after they complete.
- **`before-hook-creation`** removes an older hook resource with the same name before creating a new one during a later install or upgrade.

This behavior was visible during testing: after a successful hook run, `kubectl describe job` could return `NotFound` because the completed job had already been deleted according to policy.

## Installation Evidence

`helm list`:

```bash
PS C:\Users\zagur\DevOps\DevOps-Core-Course> helm list
NAME            NAMESPACE       REVISION        UPDATED                                 STATUS          CHART                        APP VERSION
hooks-release   default         3               2026-03-28 14:19:58.9007113 +0300 MSK   deployed        devops-info-service-0.1.0    1.0.0
prod-release    default         1               2026-03-28 16:41:30.6451874 +0300 MSK   deployed        devops-info-service-0.1.0    1.0.0
```

`kubectl get all`:

```bash
PS C:\Users\zagur\DevOps\DevOps-Core-Course> kubectl get all
NAME                                                     READY   STATUS    RESTARTS   AGE
pod/hooks-release-devops-info-service-755c9854f4-qcz82   1/1     Running   0          143m
pod/prod-release-devops-info-service-7954c7c954-4nxbp    1/1     Running   0          41s
pod/prod-release-devops-info-service-7954c7c954-6tq2v    1/1     Running   0          41s
pod/prod-release-devops-info-service-7954c7c954-w249x    1/1     Running   0          41s

NAME                                        TYPE           CLUSTER-IP      EXTERNAL-IP   PORT(S)        AGE
service/hooks-release-devops-info-service   NodePort       10.102.63.1     <none>        80:30082/TCP   142m
service/kubernetes                          ClusterIP      10.96.0.1       <none>        443/TCP        8d
service/prod-release-devops-info-service    LoadBalancer   10.100.49.155   <pending>     80:31027/TCP   41s

NAME                                                READY   UP-TO-DATE   AVAILABLE   AGE
deployment.apps/hooks-release-devops-info-service   1/1     1            1           143m
deployment.apps/prod-release-devops-info-service    3/3     3            3           41s

NAME                                                           DESIRED   CURRENT   READY   AGE
replicaset.apps/hooks-release-devops-info-service-755c9854f4   1         1         1       143m
replicaset.apps/prod-release-devops-info-service-7954c7c954    3         3         3       41s
PS C:\Users\zagur\DevOps\DevOps-Core-Course> 
```

`kubectl get jobs` and `kubectl describe jobs`:

```bash
PS C:\Users\zagur\DevOps\DevOps-Core-Course> kubectl get jobs
No resources found in default namespace.
```

Hook was deleted very fast because of `hook succeeded`, so this is an output from `kubectl lget events`:

```bash
149m        Normal    SuccessfulCreate    job/hooks-release-devops-info-service-pre-install         Created pod: hooks-release-devops-info-service-pre-install-99sft
149m        Normal    Completed           job/hooks-release-devops-info-service-pre-install         Job completed
``` 
is a part of
```bash
6m16s       Normal    Scheduled           pod/prod-release-devops-info-service-post-install-28xfr   Successfully assigned default/prod-release-devops-info-service-post-install-28xfr to minikube
6m14s       Normal    Pulling             pod/prod-release-devops-info-service-post-install-28xfr   Pulling image "busybox"
6m12s       Normal    Pulled              pod/prod-release-devops-info-service-post-install-28xfr   Successfully pulled image "busybox" in 1.97s (1.97s including waiting). Image size: 4421262 bytes.
6m11s       Normal    Created             pod/prod-release-devops-info-service-post-install-28xfr   Created container: post-install-check
6m10s       Normal    Started             pod/prod-release-devops-info-service-post-install-28xfr   Started container post-install-check
6m16s       Normal    SuccessfulCreate    job/prod-release-devops-info-service-post-install         Created pod: prod-release-devops-info-service-post-install-28xfr
6m3s        Normal    Completed           job/prod-release-devops-info-service-post-install         Job completed
6m27s       Normal    Scheduled           pod/prod-release-devops-info-service-pre-install-4jtcg    Successfully assigned default/prod-release-devops-info-service-pre-install-4jtcg to minikube
6m26s       Normal    Pulling             pod/prod-release-devops-info-service-pre-install-4jtcg    Pulling image "busybox"
6m24s       Normal    Pulled              pod/prod-release-devops-info-service-pre-install-4jtcg    Successfully pulled image "busybox" in 2.1s (2.1s including waiting). Image size: 4421262 bytes.
6m24s       Normal    Created             pod/prod-release-devops-info-service-pre-install-4jtcg    Created container: pre-install-check
6m24s       Normal    Started             pod/prod-release-devops-info-service-pre-install-4jtcg    Started container pre-install-check
6m27s       Normal    SuccessfulCreate    job/prod-release-devops-info-service-pre-install          Created pod: prod-release-devops-info-service-pre-install-4jtcg
6m17s       Normal    Completed           job/prod-release-devops-info-service-pre-install          Job completed
6m16s       Normal    ScalingReplicaSet   deployment/prod-release-devops-info-service               Scaled up replica set prod-release-devops-info-service-7954c7c954 from 0 to 3
```

Different deployments `kubectl get depliyments`:

```bash
PS C:\Users\zagur\DevOps\DevOps-Core-Course> kubectl get deployments
NAME                                READY   UP-TO-DATE   AVAILABLE   AGE
hooks-release-devops-info-service   1/1     1            1           150m
prod-release-devops-info-service    3/3     3            3           7m40s
PS C:\Users\zagur\DevOps\DevOps-Core-Course> 
```

## Operations

### Installation commands used

```bash
# Build a local image for minikube
minikube image build -t devops-info-service:dev .

# Install development release
helm install dev-release k8s/devops-info-service -f k8s/devops-info-service/values-dev.yaml

# Install production-style release
helm install prod-release k8s/devops-info-service -f k8s/devops-info-service/values-prod.yaml
```

### Upgrade a release

```bash
helm upgrade dev-release k8s/devops-info-service -f k8s/devops-info-service/values-prod.yaml
```

### Rollback a release

```bash
helm history dev-release
helm rollback dev-release 1
```

### Uninstall a release

```bash
helm uninstall dev-release
```

### Example of resolving a NodePort conflict

During testing, `hooks-release` could not be installed with the same fixed `nodePort` because the port was already in use. The release was upgraded with an explicit override instead:

```bash
helm upgrade hooks-release k8s/devops-info-service \
  -f k8s/devops-info-service/values-dev.yaml \
  --set service.nodePort=30082
```

## Testing & Validation

### Linting

The chart is intended to be checked with:

```bash
helm lint k8s/devops-info-service
```
with output:

```bash
PS C:\Users\zagur\DevOps\DevOps-Core-Course> helm lint k8s/devops-info-service
==> Linting k8s/devops-info-service

1 chart(s) linted, 0 chart(s) failed
```

### Template rendering verification

The chart can be rendered locally without applying resources:

```bash
helm template dev-release k8s/devops-info-service -f k8s/devops-info-service/values-dev.yaml
```
with output:
```bash
PS C:\Users\zagur\DevOps\DevOps-Core-Course> helm template dev-release k8s/devops-info-service -f k8s/devops-info-service/values-dev.yaml
---
# Source: devops-info-service/templates/service.yml
apiVersion: v1
kind: Service
metadata:
  name: dev-release-devops-info-service
  labels:
    helm.sh/chart: devops-info-service-0.1.0
    app.kubernetes.io/name: devops-info-service
    app.kubernetes.io/instance: dev-release
    app.kubernetes.io/version: "1.0.0"
    app.kubernetes.io/managed-by: Helm
spec:
  type: NodePort
  selector:
    app.kubernetes.io/name: devops-info-service
    app.kubernetes.io/instance: dev-release
  ports:
    - name: http
      port: 80
      targetPort: 5000
      protocol: TCP
      nodePort: 30081
---
...
```

This verifies that the templates, values, and helper functions produce valid Kubernetes YAML.

### Dry-run validation

A dry-run installation can be used to inspect hooks and rendered resources:

```bash
helm install --dry-run --debug test-release k8s/devops-info-service -f k8s/devops-info-service/values-dev.yaml
```
with output:
```bash
PS C:\Users\zagur\DevOps\DevOps-Core-Course> helm install --dry-run --debug test-release k8s/devops-info-service -f k8s/devops-info-service/values-dev.yaml
level=WARN msg="--dry-run is deprecated and should be replaced with '--dry-run=client'"
level=DEBUG msg="Original chart version" version=""
level=DEBUG msg="Chart path" path=C:\Users\zagur\DevOps\DevOps-Core-Course\k8s\devops-info-service
level=DEBUG msg="number of dependencies in the chart" chart=devops-info-service dependencies=0
NAME: test-release
LAST DEPLOYED: Sat Mar 28 16:51:37 2026
NAMESPACE: default
STATUS: pending-install
REVISION: 1
DESCRIPTION: Dry run complete
TEST SUITE: None
USER-SUPPLIED VALUES:
image:
  tag: dev
probes:
  liveness:
    initialDelaySeconds: 10
    periodSeconds: 10
  readiness:
    initialDelaySeconds: 3
    periodSeconds: 5
  startup:
    failureThreshold: 30
replicaCount: 1
resources:
  limits:
    cpu: 100m
    memory: 128Mi
  requests:
    cpu: 50m
    memory: 64Mi
service:
  nodePort: 30081
  type: NodePort

COMPUTED VALUES:
containerSecurityContext:
  capabilities:
    drop:
    - ALL
env:
- name: PYTHONUNBUFFERED
  value: "1"
image:
  pullPolicy: IfNotPresent
  repository: devops-info-service
  tag: dev
probes:
  liveness:
    enabled: true
    failureThreshold: 6
    initialDelaySeconds: 10
    path: /health
    periodSeconds: 10
    port: 5000
    timeoutSeconds: 2
  readiness:
    enabled: true
    failureThreshold: 6
    initialDelaySeconds: 3
    path: /health
    periodSeconds: 5
    port: 5000
    timeoutSeconds: 2
  startup:
    enabled: true
    failureThreshold: 30
    initialDelaySeconds: 0
    path: /health
    periodSeconds: 5
    port: 5000
    timeoutSeconds: 2
replicaCount: 1
resources:
  limits:
    cpu: 100m
    memory: 128Mi
  requests:
    cpu: 50m
    memory: 64Mi
securityContext:
  allowPrivilegeEscalation: false
  readOnlyRootFilesystem: false
  runAsGroup: 1000
  runAsNonRoot: true
  runAsUser: 1000
service:
  nodePort: 30081
  port: 80
  targetPort: 5000
  type: NodePort

HOOKS:
---
...
```
### Application accessibility verification

The application was verified indirectly through Kubernetes status:

- the Helm release reached `STATUS: deployed`
- the final rollout showed **three Pods in `1/1 Running` state**
- the Service was created successfully as `LoadBalancer` during the production-style configuration test

For local access in minikube, the following command can be used for a NodePort-based environment:

```bash
minikube service prod-release-devops-info-service --url
```

```bash
PS C:\Users\zagur\DevOps\DevOps-Core-Course> minikube service prod-release-devops-info-service --url
http://127.0.0.1:18293
❗  Because you are using a Docker driver on windows, the terminal needs to be open to run it.
```

![](/past_labs/docs/screenshots/helm.png)

### Testing conclusion

The chart successfully templates the Kubernetes resources, supports multiple environments, preserves configurable health checks, and implements working lifecycle hooks. The deployment evidence also shows that Helm upgrades and value overrides were applied successfully during testing.
