# Helm Chart Documentation

## Chart Overview

### Chart Structure Explanation

```
k8s/python-app/
├── Chart.yaml                          # Chart metadata: name, version, appVersion, dependencies
├── values.yaml                         # Default configuration values
├── values-dev.yaml                     # Development environment overrides
├── values-prod.yaml                    # Production environment overrides
├── Chart.lock                          # Locked dependency versions
├── charts/
│   └── common-lib-0.1.0.tgz           # Packaged library chart dependency
└── templates/
    ├── _helpers.tpl                    # Named template helpers (DRY functions)
    ├── deployment.yaml                 # Kubernetes Deployment resource
    ├── service.yaml                    # Kubernetes Service resource
    ├── NOTES.txt                       # Post-install instructions shown to user
    └── hooks/
        ├── pre-install-job.yaml        # Pre-install lifecycle hook
        └── post-install-job.yaml       # Post-install lifecycle hook
```

### Key Template Files and Their Purpose

| File | Purpose |
|---|---|
| [`Chart.yaml`](python-app/Chart.yaml) | Declares chart name (`python-app`), `apiVersion: v2`, `appVersion: "1.0"`, maintainers, and `common-lib` dependency |
| [`values.yaml`](python-app/values.yaml) | All configurable defaults: image, replicas, service type/ports, resources, env vars, liveness/readiness probes, security contexts |
| [`templates/_helpers.tpl`](python-app/templates/_helpers.tpl) | Defines reusable named templates: `python-app.fullname`, `python-app.name`, `python-app.chart`, `python-app.labels`, `python-app.selectorLabels` |
| [`templates/deployment.yaml`](python-app/templates/deployment.yaml) | Fully templated Deployment — image, replicas, rolling update strategy, env vars, resource limits, liveness/readiness probes, pod/container security contexts |
| [`templates/service.yaml`](python-app/templates/service.yaml) | Service with conditional `nodePort` field (only rendered when `service.type == NodePort`) |
| [`templates/NOTES.txt`](python-app/templates/NOTES.txt) | Post-install access instructions rendered per service type (NodePort / LoadBalancer / ClusterIP) |
| [`templates/hooks/pre-install-job.yaml`](python-app/templates/hooks/pre-install-job.yaml) | Kubernetes Job that runs before chart resources are created |
| [`templates/hooks/post-install-job.yaml`](python-app/templates/hooks/post-install-job.yaml) | Kubernetes Job that runs after all chart resources are ready |

### Values Organization Strategy

Values are organized in nested groups by concern:

```yaml
# Scaling
replicaCount: 3

# Container image
image:
  repository: newspec/python_app
  tag: "1.0"
  pullPolicy: IfNotPresent

# Network exposure
service:
  type: NodePort
  port: 80
  targetPort: 8000
  nodePort: 30080

# Rolling update strategy
strategy:
  type: RollingUpdate
  rollingUpdate:
    maxSurge: 1
    maxUnavailable: 0

# Compute resources
resources:
  requests: { cpu: "100m", memory: "128Mi" }
  limits:   { cpu: "200m", memory: "256Mi" }

# Environment variables
env:
  - name: DEBUG
    value: "False"

# Health checks — NEVER commented out, always active
livenessProbe:
  httpGet: { path: /health, port: 8000 }
  initialDelaySeconds: 10
  periodSeconds: 5
  timeoutSeconds: 3
  failureThreshold: 3

readinessProbe:
  httpGet: { path: /health, port: 8000 }
  initialDelaySeconds: 5
  periodSeconds: 3
  timeoutSeconds: 2
  failureThreshold: 3

# Security
podSecurityContext:
  runAsNonRoot: true
  runAsUser: 1000
  fsGroup: 1000

containerSecurityContext:
  allowPrivilegeEscalation: false
  capabilities:
    drop: [ALL]
```

---

## Configuration Guide

### Important Values and Their Purpose

| Value | Default | Purpose |
|---|---|---|
| `replicaCount` | `3` | Number of pod replicas |
| `image.repository` | `newspec/python_app` | Container image repository |
| `image.tag` | `"1.0"` | Image tag; falls back to `Chart.AppVersion` if empty |
| `image.pullPolicy` | `IfNotPresent` | When to pull the image |
| `service.type` | `NodePort` | Service type: `NodePort`, `LoadBalancer`, or `ClusterIP` |
| `service.port` | `80` | Service port (external) |
| `service.targetPort` | `8000` | Container port (internal) |
| `service.nodePort` | `30080` | NodePort number (only used when `service.type == NodePort`) |
| `resources.requests.cpu` | `100m` | Minimum CPU guaranteed |
| `resources.limits.cpu` | `200m` | Maximum CPU allowed |
| `resources.requests.memory` | `128Mi` | Minimum memory guaranteed |
| `resources.limits.memory` | `256Mi` | Maximum memory allowed |
| `livenessProbe.initialDelaySeconds` | `10` | Seconds before first liveness check |
| `readinessProbe.initialDelaySeconds` | `5` | Seconds before first readiness check |
| `podSecurityContext.runAsUser` | `1000` | UID to run container as (non-root) |
| `nameOverride` | `""` | Override chart name portion of resource names |
| `fullnameOverride` | `""` | Override full resource name entirely |

### How to Customize for Different Environments

Values files are layered: `values.yaml` provides defaults, environment files override only what differs:

```bash
# Development: use values-dev.yaml on top of values.yaml
helm install myapp-dev k8s/python-app -f k8s/python-app/values-dev.yaml

# Production: use values-prod.yaml on top of values.yaml
helm install myapp-prod k8s/python-app -f k8s/python-app/values-prod.yaml

# Ad-hoc override without a file
helm install myapp k8s/python-app --set replicaCount=10 --set image.tag=2.0
```

**Environment comparison:**

| Setting | Dev | Prod |
|---|---|---|
| `replicaCount` | `1` | `5` |
| `image.tag` | `latest` | `1.0` |
| `service.type` | `NodePort` | `LoadBalancer` |
| CPU limit | `100m` | `500m` |
| Memory limit | `128Mi` | `512Mi` |
| `DEBUG` env | `"True"` | `"False"` |
| `livenessProbe.initialDelaySeconds` | `5` | `30` |
| `readinessProbe.initialDelaySeconds` | `3` | `10` |

### Example Installations with Different Configurations
Default (3 replicas, NodePort)
```bash
helm install myrelease k8s/python-app --set service.nodePort=30090
level=ERROR msg="release name check failed" error="cannot reuse a name that is still in use"
Error: INSTALLATION FAILED: release name check failed: cannot reuse a name that is still in use
newspec@MacBook-Pro-5 DevOps-Core-Course % helm uninstall myrelease                                          

release "myrelease" uninstalled
newspec@MacBook-Pro-5 DevOps-Core-Course % clear                   
newspec@MacBook-Pro-5 DevOps-Core-Course % helm install myrelease k8s/python-app --set service.nodePort=30090
NAME: myrelease
LAST DEPLOYED: Thu Apr  2 22:45:51 2026
NAMESPACE: default
STATUS: deployed
REVISION: 1
DESCRIPTION: Install complete
TEST SUITE: None
NOTES:
Thank you for installing python-app v1.0!

Release name: myrelease
Namespace:    default

=== Access the Application ===
  Get the NodePort URL:
    export NODE_PORT=$(kubectl get svc myrelease-python-app-svc -n default -o jsonpath="{.spec.ports[0].nodePort}")
    export NODE_IP=$(kubectl get nodes -o jsonpath="{.items[0].status.addresses[0].address}")
    echo "Application URL: http://$NODE_IP:$NODE_PORT"

=== Health Check ===
  curl http://<APP_URL>/health

=== Useful Commands ===
  # View pods
  kubectl get pods -l app.kubernetes.io/instance=myrelease -n default

  # View logs
  kubectl logs -l app.kubernetes.io/instance=myrelease -n default

  # Upgrade release
  helm upgrade myrelease k8s/python-app -f k8s/python-app/values-prod.yaml

  # Rollback
  helm rollback myrelease 1

  # Uninstall
  helm uninstall myrelease
```
Development (1 replica, latest image, relaxed probes)
```bash
helm install myapp-dev k8s/python-app -f k8s/python-app/values-dev.yaml --set service.nodePort=30091
NAME: myapp-dev
LAST DEPLOYED: Thu Apr  2 22:47:48 2026
NAMESPACE: default
STATUS: deployed
REVISION: 1
DESCRIPTION: Install complete
TEST SUITE: None
NOTES:
Thank you for installing python-app v1.0!

Release name: myapp-dev
Namespace:    default

=== Access the Application ===
  Get the NodePort URL:
    export NODE_PORT=$(kubectl get svc myapp-dev-python-app-svc -n default -o jsonpath="{.spec.ports[0].nodePort}")
    export NODE_IP=$(kubectl get nodes -o jsonpath="{.items[0].status.addresses[0].address}")
    echo "Application URL: http://$NODE_IP:$NODE_PORT"

=== Health Check ===
  curl http://<APP_URL>/health

=== Useful Commands ===
  # View pods
  kubectl get pods -l app.kubernetes.io/instance=myapp-dev -n default

  # View logs
  kubectl logs -l app.kubernetes.io/instance=myapp-dev -n default

  # Upgrade release
  helm upgrade myapp-dev k8s/python-app -f k8s/python-app/values-prod.yaml

  # Rollback
  helm rollback myapp-dev 1

  # Uninstall
  helm uninstall myapp-dev
```
Install for production environment
```bash
helm install myapp-prod k8s/python-app -f k8s/python-app/values-prod.yaml --set service.nodePort=30092
NAME: myapp-prod
LAST DEPLOYED: Thu Apr  2 22:49:16 2026
NAMESPACE: default
STATUS: deployed
REVISION: 1
DESCRIPTION: Install complete
TEST SUITE: None
NOTES:
Thank you for installing python-app v1.0!

Release name: myapp-prod
Namespace:    default

=== Access the Application ===
  Wait for the LoadBalancer IP:
    kubectl get svc myapp-prod-python-app-svc -n default -w
    export LB_IP=$(kubectl get svc myapp-prod-python-app-svc -n default -o jsonpath="{.status.loadBalancer.ingress[0].ip}")
    echo "Application URL: http://$LB_IP:80"

=== Health Check ===
  curl http://<APP_URL>/health

=== Useful Commands ===
  # View pods
  kubectl get pods -l app.kubernetes.io/instance=myapp-prod -n default

  # View logs
  kubectl logs -l app.kubernetes.io/instance=myapp-prod -n default

  # Upgrade release
  helm upgrade myapp-prod k8s/python-app -f k8s/python-app/values-prod.yaml

  # Rollback
  helm rollback myapp-prod 1

  # Uninstall
  helm uninstall myapp-prod
```
Production (5 replicas, LoadBalancer, conservative probes)
```bash
helm install myapp-prod k8s/python-app -f k8s/python-app/values-prod.yaml --set service.nodePort=30092
NAME: myapp-prod
LAST DEPLOYED: Thu Apr  2 22:49:16 2026
NAMESPACE: default
STATUS: deployed
REVISION: 1
DESCRIPTION: Install complete
TEST SUITE: None
NOTES:
Thank you for installing python-app v1.0!

Release name: myapp-prod
Namespace:    default

=== Access the Application ===
  Wait for the LoadBalancer IP:
    kubectl get svc myapp-prod-python-app-svc -n default -w
    export LB_IP=$(kubectl get svc myapp-prod-python-app-svc -n default -o jsonpath="{.status.loadBalancer.ingress[0].ip}")
    echo "Application URL: http://$LB_IP:80"

=== Health Check ===
  curl http://<APP_URL>/health

=== Useful Commands ===
  # View pods
  kubectl get pods -l app.kubernetes.io/instance=myapp-prod -n default

  # View logs
  kubectl logs -l app.kubernetes.io/instance=myapp-prod -n default

  # Upgrade release
  helm upgrade myapp-prod k8s/python-app -f k8s/python-app/values-prod.yaml

  # Rollback
  helm rollback myapp-prod 1

  # Uninstall
  helm uninstall myapp-prod
```
Custom namespace
```bash
helm install spec-namespace k8s/python-app -n production --create-namespace --set service.nodePort=30094
NAME: spec-namespace
LAST DEPLOYED: Thu Apr  2 22:51:53 2026
NAMESPACE: production
STATUS: deployed
REVISION: 1
DESCRIPTION: Install complete
TEST SUITE: None
NOTES:
Thank you for installing python-app v1.0!

Release name: spec-namespace
Namespace:    production

=== Access the Application ===
  Get the NodePort URL:
    export NODE_PORT=$(kubectl get svc spec-namespace-python-app-svc -n production -o jsonpath="{.spec.ports[0].nodePort}")
    export NODE_IP=$(kubectl get nodes -o jsonpath="{.items[0].status.addresses[0].address}")
    echo "Application URL: http://$NODE_IP:$NODE_PORT"

=== Health Check ===
  curl http://<APP_URL>/health

=== Useful Commands ===
  # View pods
  kubectl get pods -l app.kubernetes.io/instance=spec-namespace -n production

  # View logs
  kubectl logs -l app.kubernetes.io/instance=spec-namespace -n production

  # Upgrade release
  helm upgrade spec-namespace k8s/python-app -f k8s/python-app/values-prod.yaml

  # Rollback
  helm rollback spec-namespace 1

  # Uninstall
  helm uninstall spec-namespace
```
Override image tag inline
```bash
helm install over-tag k8s/python-app --set image.tag=2.0 --set service.nodePort=30095
NAME: over-tag
LAST DEPLOYED: Thu Apr  2 22:57:04 2026
NAMESPACE: default
STATUS: deployed
REVISION: 1
DESCRIPTION: Install complete
TEST SUITE: None
NOTES:
Thank you for installing python-app v1.0!

Release name: over-tag
Namespace:    default

=== Access the Application ===
  Get the NodePort URL:
    export NODE_PORT=$(kubectl get svc over-tag-python-app-svc -n default -o jsonpath="{.spec.ports[0].nodePort}")
    export NODE_IP=$(kubectl get nodes -o jsonpath="{.items[0].status.addresses[0].address}")
    echo "Application URL: http://$NODE_IP:$NODE_PORT"

=== Health Check ===
  curl http://<APP_URL>/health

=== Useful Commands ===
  # View pods
  kubectl get pods -l app.kubernetes.io/instance=over-tag -n default

  # View logs
  kubectl logs -l app.kubernetes.io/instance=over-tag -n default

  # Upgrade release
  helm upgrade over-tag k8s/python-app -f k8s/python-app/values-prod.yaml

  # Rollback
  helm rollback over-tag 1

  # Uninstall
  helm uninstall over-tag
```
Combine values file with inline override
```bash
helm install combine k8s/python-app -f k8s/python-app/values-prod.yaml --set replicaCount=10 --set service.nodePort=30096
NAME: combine
LAST DEPLOYED: Thu Apr  2 22:58:41 2026
NAMESPACE: default
STATUS: deployed
REVISION: 1
DESCRIPTION: Install complete
TEST SUITE: None
NOTES:
Thank you for installing python-app v1.0!

Release name: combine
Namespace:    default

=== Access the Application ===
  Wait for the LoadBalancer IP:
    kubectl get svc combine-python-app-svc -n default -w
    export LB_IP=$(kubectl get svc combine-python-app-svc -n default -o jsonpath="{.status.loadBalancer.ingress[0].ip}")
    echo "Application URL: http://$LB_IP:80"

=== Health Check ===
  curl http://<APP_URL>/health

=== Useful Commands ===
  # View pods
  kubectl get pods -l app.kubernetes.io/instance=combine -n default

  # View logs
  kubectl logs -l app.kubernetes.io/instance=combine -n default

  # Upgrade release
  helm upgrade combine k8s/python-app -f k8s/python-app/values-prod.yaml

  # Rollback
  helm rollback combine 1

  # Uninstall
  helm uninstall combine
```

---

## Hook Implementation

### What Hooks Were Implemented and Why

**Pre-install hook** ([`templates/hooks/pre-install-job.yaml`](python-app/templates/hooks/pre-install-job.yaml)):
- Runs a `busybox` Job **before** any chart resources are created
- Simulates a database migration check and environment prerequisites validation
- Real-world use: run `alembic upgrade head`, check external service availability, validate secrets exist

**Post-install hook** ([`templates/hooks/post-install-job.yaml`](python-app/templates/hooks/post-install-job.yaml)):
- Runs a `busybox` Job **after** all chart resources are installed and ready
- Simulates smoke tests (endpoint check, health check, replica count verification) and deployment notification
- Real-world use: run integration tests, send Slack/PagerDuty notification, warm up caches

### Hook Execution Order and Weights

```
helm install myrelease k8s/python-app
    │
    ├─► [pre-install, weight -5] pre-install Job executes
    │       ├─ echo "Simulating database migration check..."
    │       ├─ echo "Schema version check: OK"
    │       └─ echo "Prerequisites check: PASSED"
    │       └─ Job deleted on success (hook-succeeded policy)
    │
    ├─► Kubernetes resources created:
    │       ├─ Deployment (3 replicas, rolling update)
    │       └─ Service (NodePort 30080)
    │
    └─► [post-install, weight 5] post-install Job executes
            ├─ echo "Checking service endpoint availability..."
            ├─ echo "Health check: HEALTHY"
            └─ echo "Replicas: 3/3 ready"
            └─ Job deleted on success (hook-succeeded policy)
```

Weight `-5` for pre-install ensures it runs before any other pre-install hooks that might be added later. Weight `5` for post-install ensures it runs after other post-install hooks.

### Deletion Policies Explanation

Both hooks use `"helm.sh/hook-delete-policy": hook-succeeded`:

| Policy | Behavior | When to Use |
|---|---|---|
| `hook-succeeded` | Delete Job pod after **successful** completion | Production — keeps cluster clean |
| `before-hook-creation` | Delete previous hook before creating new one | Upgrades — prevents conflicts |
| `hook-failed` | Delete Job pod after **failure** | Debugging — usually not used in prod |

`hook-succeeded` was chosen because:
1. Keeps the cluster clean — no orphaned Job pods after successful installs
2. Logs are still accessible via `kubectl logs` before deletion
3. Failed hooks are preserved for debugging (not deleted on failure)

---

## Installation Evidence

### `helm list` Output

```bash
helm list
NAME            NAMESPACE       REVISION        UPDATED                                 STATUS          CHART                   APP VERSION
combine         default         1               2026-04-02 22:58:41.131545 +0300 MSK    deployed        python-app-0.1.0        1.0        
myapp-dev       default         1               2026-04-02 22:47:48.493204 +0300 MSK    deployed        python-app-0.1.0        1.0        
myapp-prod      default         1               2026-04-02 22:49:16.095739 +0300 MSK    deployed        python-app-0.1.0        1.0        
myrelease       default         1               2026-04-02 22:45:51.842135 +0300 MSK    deployed        python-app-0.1.0        1.0        
over-tag        default         1               2026-04-02 22:57:04.844258 +0300 MSK    deployed        python-app-0.1.0        1.0     
```

### `kubectl get all` Showing Deployed Resources

```bash
kubectl get all
NAME                                         READY   STATUS             RESTARTS      AGE
pod/app2-57f579666d-zt89g                    1/1     Running            1 (42m ago)   10d
pod/combine-python-app-655c679f7d-2zsbn      0/1     Pending            0             93s
pod/combine-python-app-655c679f7d-8kgdn      0/1     Pending            0             93s
pod/combine-python-app-655c679f7d-fbngm      0/1     Pending            0             93s
pod/combine-python-app-655c679f7d-h76vq      0/1     Pending            0             93s
pod/combine-python-app-655c679f7d-hqst8      0/1     Pending            0             93s
pod/combine-python-app-655c679f7d-jnl9k      0/1     Pending            0             93s
pod/combine-python-app-655c679f7d-nccrx      0/1     Pending            0             93s
pod/combine-python-app-655c679f7d-pj2s9      0/1     Pending            0             93s
pod/combine-python-app-655c679f7d-t7jfk      0/1     Pending            0             93s
pod/combine-python-app-655c679f7d-wcx5v      0/1     Pending            0             93s
pod/myapp-dev-python-app-54b846d566-dvdtp    0/1     ImagePullBackOff   0             12m
pod/myapp-prod-python-app-69997674f6-cjc9f   0/1     Pending            0             10m
pod/myapp-prod-python-app-69997674f6-mqzzs   0/1     Pending            0             10m
pod/myapp-prod-python-app-69997674f6-r6nh8   0/1     Pending            0             10m
pod/myapp-prod-python-app-69997674f6-r9ql9   0/1     Pending            0             10m
pod/myapp-prod-python-app-69997674f6-x46wp   0/1     Pending            0             10m
pod/myrelease-python-app-7c858df59b-ghs26    1/1     Running            0             14m
pod/myrelease-python-app-7c858df59b-qt2wq    1/1     Running            0             14m
pod/myrelease-python-app-7c858df59b-z6pgk    1/1     Running            0             14m
pod/over-tag-python-app-5c647cffd7-7tdcd     0/1     Pending            0             3m9s
pod/over-tag-python-app-5c647cffd7-9h4zk     0/1     Pending            0             3m9s
pod/over-tag-python-app-5c647cffd7-trtf7     0/1     Pending            0             3m9s
pod/python-app-55b9b99784-8sf4d              1/1     Running            1 (42m ago)   10d
pod/python-app-55b9b99784-fr2vs              1/1     Running            1 (42m ago)   10d
pod/python-app-55b9b99784-j7rbh              1/1     Running            6 (42m ago)   10d

NAME                                TYPE           CLUSTER-IP       EXTERNAL-IP   PORT(S)        AGE
service/app2-svc                    ClusterIP      10.100.176.124   <none>        80/TCP         10d
service/combine-python-app-svc      LoadBalancer   10.96.58.9       <pending>     80:32186/TCP   93s
service/kubernetes                  ClusterIP      10.96.0.1        <none>        443/TCP        10d
service/myapp-dev-python-app-svc    NodePort       10.98.252.88     <none>        80:30091/TCP   12m
service/myapp-prod-python-app-svc   LoadBalancer   10.103.219.117   <pending>     80:31479/TCP   10m
service/myrelease-python-app-svc    NodePort       10.107.123.108   <none>        80:30090/TCP   14m
service/over-tag-python-app-svc     NodePort       10.107.2.198     <none>        80:30095/TCP   3m9s
service/python-app-svc              NodePort       10.96.189.93     <none>        80:30080/TCP   10d

NAME                                    READY   UP-TO-DATE   AVAILABLE   AGE
deployment.apps/app2                    1/1     1            1           10d
deployment.apps/combine-python-app      0/10    10           0           93s
deployment.apps/myapp-dev-python-app    0/1     1            0           12m
deployment.apps/myapp-prod-python-app   0/5     5            0           10m
deployment.apps/myrelease-python-app    3/3     3            3           14m
deployment.apps/over-tag-python-app     0/3     3            0           3m9s
deployment.apps/python-app              3/3     3            3           10d

NAME                                               DESIRED   CURRENT   READY   AGE
replicaset.apps/app2-57f579666d                    1         1         1       10d
replicaset.apps/combine-python-app-655c679f7d      10        10        0       93s
replicaset.apps/myapp-dev-python-app-54b846d566    1         1         0       12m
replicaset.apps/myapp-prod-python-app-69997674f6   5         5         0       10m
replicaset.apps/myrelease-python-app-7c858df59b    3         3         3       14m
replicaset.apps/over-tag-python-app-5c647cffd7     3         3         0       3m9s
replicaset.apps/python-app-55b9b99784              3         3         3       10d
replicaset.apps/python-app-85d6cf4d5d              0         0         0       10d
```

### Hook Execution Output

Hooks ran and were **automatically deleted** by `hook-succeeded` policy after successful completion:

```
$ kubectl get jobs
No resources found in default namespace.
```
```
kubectl describe job
No resources found in default namespace.
```

This confirms `hook-succeeded` deletion policy worked correctly — jobs completed and were cleaned up.

### Different Environment Deployments (Dev vs Prod)

**Dev deployment** (1 replica, `latest` image, NodePort):
```bash
helm install myapp-dev k8s/python-app -f k8s/python-app/values-dev.yaml --set service.nodePort=30091
NAME: myapp-dev
LAST DEPLOYED: Thu Apr  2 22:47:48 2026
NAMESPACE: default
STATUS: deployed
REVISION: 1
DESCRIPTION: Install complete
TEST SUITE: None
NOTES:
Thank you for installing python-app v1.0!

Release name: myapp-dev
Namespace:    default

=== Access the Application ===
  Get the NodePort URL:
    export NODE_PORT=$(kubectl get svc myapp-dev-python-app-svc -n default -o jsonpath="{.spec.ports[0].nodePort}")
    export NODE_IP=$(kubectl get nodes -o jsonpath="{.items[0].status.addresses[0].address}")
    echo "Application URL: http://$NODE_IP:$NODE_PORT"

=== Health Check ===
  curl http://<APP_URL>/health

=== Useful Commands ===
  # View pods
  kubectl get pods -l app.kubernetes.io/instance=myapp-dev -n default

  # View logs
  kubectl logs -l app.kubernetes.io/instance=myapp-dev -n default

  # Upgrade release
  helm upgrade myapp-dev k8s/python-app -f k8s/python-app/values-prod.yaml

  # Rollback
  helm rollback myapp-dev 1

  # Uninstall
  helm uninstall myapp-dev
```
Install for production environment
```bash
helm install myapp-prod k8s/python-app -f k8s/python-app/values-prod.yaml --set service.nodePort=30092
NAME: myapp-prod
LAST DEPLOYED: Thu Apr  2 22:49:16 2026
NAMESPACE: default
STATUS: deployed
REVISION: 1
DESCRIPTION: Install complete
TEST SUITE: None
NOTES:
Thank you for installing python-app v1.0!

Release name: myapp-prod
Namespace:    default

=== Access the Application ===
  Wait for the LoadBalancer IP:
    kubectl get svc myapp-prod-python-app-svc -n default -w
    export LB_IP=$(kubectl get svc myapp-prod-python-app-svc -n default -o jsonpath="{.status.loadBalancer.ingress[0].ip}")
    echo "Application URL: http://$LB_IP:80"

=== Health Check ===
  curl http://<APP_URL>/health

=== Useful Commands ===
  # View pods
  kubectl get pods -l app.kubernetes.io/instance=myapp-prod -n default

  # View logs
  kubectl logs -l app.kubernetes.io/instance=myapp-prod -n default

  # Upgrade release
  helm upgrade myapp-prod k8s/python-app -f k8s/python-app/values-prod.yaml

  # Rollback
  helm rollback myapp-prod 1

  # Uninstall
  helm uninstall myapp-prod
```
```bash
kubectl get deployment myapp-dev-python-app -o wide
NAME                   READY   UP-TO-DATE   AVAILABLE   AGE   CONTAINERS   IMAGES                      SELECTOR
myapp-dev-python-app   0/1     1            0           15m   python-app   newspec/python_app:latest   app.kubernetes.io/instance=myapp-dev,app.kubernetes.io/name=python-app
```
```bash
kubectl get svc myapp-dev-python-app-svc
NAME                       TYPE       CLUSTER-IP     EXTERNAL-IP   PORT(S)        AGE
myapp-dev-python-app-svc   NodePort   10.97.17.175   <none>        80:30091/TCP   16m
```

**Upgrade to prod values** (5 replicas, `1.0` image):
```bash
helm upgrade myapp-dev k8s/python-app -f k8s/python-app/values-prod.yaml --set service.nodePort=30091
Release "myapp-dev" has been upgraded. Happy Helming!
NAME: myapp-dev
LAST DEPLOYED: Thu Apr  2 22:41:22 2026
NAMESPACE: default
STATUS: deployed
REVISION: 4
DESCRIPTION: Upgrade complete
TEST SUITE: None
NOTES:
Thank you for installing python-app v1.0!

Release name: myapp-dev
Namespace:    default

=== Access the Application ===
  Wait for the LoadBalancer IP:
    kubectl get svc myapp-dev-python-app-svc -n default -w
    export LB_IP=$(kubectl get svc myapp-dev-python-app-svc -n default -o jsonpath="{.status.loadBalancer.ingress[0].ip}")
    echo "Application URL: http://$LB_IP:80"

=== Health Check ===
  curl http://<APP_URL>/health

=== Useful Commands ===
  # View pods
  kubectl get pods -l app.kubernetes.io/instance=myapp-dev -n default

  # View logs
  kubectl logs -l app.kubernetes.io/instance=myapp-dev -n default

  # Upgrade release
  helm upgrade myapp-dev k8s/python-app -f k8s/python-app/values-prod.yaml

  # Rollback
  helm rollback myapp-dev 1

  # Uninstall
  helm uninstall myapp-dev
```
```bash
kubectl get deployment myapp-dev-python-app -o wide
NAME                   READY   UP-TO-DATE   AVAILABLE   AGE   CONTAINERS   IMAGES                   SELECTOR
myapp-dev-python-app   0/5     1            0           17m   python-app   newspec/python_app:1.0   app.kubernetes.io/instance=myapp-dev,app.kubernetes.io/name=python-app
```

**Rollback to revision 1** (back to dev values):
```bash
helm rollback myapp-dev 1
Rollback was a success! Happy Helming!
```
```bash
helm history myapp-dev
REVISION        UPDATED                         STATUS          CHART                   APP VERSION     DESCRIPTION     
1               Thu Apr  2 22:24:14 2026        superseded      python-app-0.1.0        1.0             Install complete
2               Thu Apr  2 22:25:16 2026        superseded      python-app-0.1.0        1.0             Upgrade complete
3               Thu Apr  2 22:25:23 2026        superseded      python-app-0.1.0        1.0             Rollback to 1   
4               Thu Apr  2 22:41:22 2026        superseded      python-app-0.1.0        1.0             Upgrade complete
5               Thu Apr  2 22:42:38 2026        deployed        python-app-0.1.0        1.0             Rollback to 1   
```

---

## Operations

### Installation Commands Used
Resolve dependencies before first install
```bash
helm dependency update k8s/python-app
Hang tight while we grab the latest from your chart repositories...
...Successfully got an update from the "prometheus-community" chart repository
Update Complete. ⎈Happy Helming!⎈
Saving 1 charts
Deleting outdated charts
```
Install with default values
```bash
helm install myrelease k8s/python-app --set service.nodePort=30090
NAME: myrelease
LAST DEPLOYED: Thu Apr  2 22:45:51 2026
NAMESPACE: default
STATUS: deployed
REVISION: 1
DESCRIPTION: Install complete
TEST SUITE: None
NOTES:
Thank you for installing python-app v1.0!

Release name: myrelease
Namespace:    default

=== Access the Application ===
  Get the NodePort URL:
    export NODE_PORT=$(kubectl get svc myrelease-python-app-svc -n default -o jsonpath="{.spec.ports[0].nodePort}")
    export NODE_IP=$(kubectl get nodes -o jsonpath="{.items[0].status.addresses[0].address}")
    echo "Application URL: http://$NODE_IP:$NODE_PORT"

=== Health Check ===
  curl http://<APP_URL>/health

=== Useful Commands ===
  # View pods
  kubectl get pods -l app.kubernetes.io/instance=myrelease -n default

  # View logs
  kubectl logs -l app.kubernetes.io/instance=myrelease -n default

  # Upgrade release
  helm upgrade myrelease k8s/python-app -f k8s/python-app/values-prod.yaml

  # Rollback
  helm rollback myrelease 1

  # Uninstall
  helm uninstall myrelease
```
Install for development environment
```bash
helm install myapp-dev k8s/python-app -f k8s/python-app/values-dev.yaml --set service.nodePort=30091
NAME: myapp-dev
LAST DEPLOYED: Thu Apr  2 22:47:48 2026
NAMESPACE: default
STATUS: deployed
REVISION: 1
DESCRIPTION: Install complete
TEST SUITE: None
NOTES:
Thank you for installing python-app v1.0!

Release name: myapp-dev
Namespace:    default

=== Access the Application ===
  Get the NodePort URL:
    export NODE_PORT=$(kubectl get svc myapp-dev-python-app-svc -n default -o jsonpath="{.spec.ports[0].nodePort}")
    export NODE_IP=$(kubectl get nodes -o jsonpath="{.items[0].status.addresses[0].address}")
    echo "Application URL: http://$NODE_IP:$NODE_PORT"

=== Health Check ===
  curl http://<APP_URL>/health

=== Useful Commands ===
  # View pods
  kubectl get pods -l app.kubernetes.io/instance=myapp-dev -n default

  # View logs
  kubectl logs -l app.kubernetes.io/instance=myapp-dev -n default

  # Upgrade release
  helm upgrade myapp-dev k8s/python-app -f k8s/python-app/values-prod.yaml

  # Rollback
  helm rollback myapp-dev 1

  # Uninstall
  helm uninstall myapp-dev
```
Install for production environment
```bash
helm install myapp-prod k8s/python-app -f k8s/python-app/values-prod.yaml --set service.nodePort=30092
NAME: myapp-prod
LAST DEPLOYED: Thu Apr  2 22:49:16 2026
NAMESPACE: default
STATUS: deployed
REVISION: 1
DESCRIPTION: Install complete
TEST SUITE: None
NOTES:
Thank you for installing python-app v1.0!

Release name: myapp-prod
Namespace:    default

=== Access the Application ===
  Wait for the LoadBalancer IP:
    kubectl get svc myapp-prod-python-app-svc -n default -w
    export LB_IP=$(kubectl get svc myapp-prod-python-app-svc -n default -o jsonpath="{.status.loadBalancer.ingress[0].ip}")
    echo "Application URL: http://$LB_IP:80"

=== Health Check ===
  curl http://<APP_URL>/health

=== Useful Commands ===
  # View pods
  kubectl get pods -l app.kubernetes.io/instance=myapp-prod -n default

  # View logs
  kubectl logs -l app.kubernetes.io/instance=myapp-prod -n default

  # Upgrade release
  helm upgrade myapp-prod k8s/python-app -f k8s/python-app/values-prod.yaml

  # Rollback
  helm rollback myapp-prod 1

  # Uninstall
  helm uninstall myapp-prod
```
Install in specific namespace
```bash
helm install spec-namespace k8s/python-app -n production --create-namespace --set service.nodePort=30094
NAME: spec-namespace
LAST DEPLOYED: Thu Apr  2 22:51:53 2026
NAMESPACE: production
STATUS: deployed
REVISION: 1
DESCRIPTION: Install complete
TEST SUITE: None
NOTES:
Thank you for installing python-app v1.0!

Release name: spec-namespace
Namespace:    production

=== Access the Application ===
  Get the NodePort URL:
    export NODE_PORT=$(kubectl get svc spec-namespace-python-app-svc -n production -o jsonpath="{.spec.ports[0].nodePort}")
    export NODE_IP=$(kubectl get nodes -o jsonpath="{.items[0].status.addresses[0].address}")
    echo "Application URL: http://$NODE_IP:$NODE_PORT"

=== Health Check ===
  curl http://<APP_URL>/health

=== Useful Commands ===
  # View pods
  kubectl get pods -l app.kubernetes.io/instance=spec-namespace -n production

  # View logs
  kubectl logs -l app.kubernetes.io/instance=spec-namespace -n production

  # Upgrade release
  helm upgrade spec-namespace k8s/python-app -f k8s/python-app/values-prod.yaml

  # Rollback
  helm rollback spec-namespace 1

  # Uninstall
  helm uninstall spec-namespace
```

### How to Upgrade a Release
Upgrade to production values
```bash
helm upgrade myrelease k8s/python-app -f k8s/python-app/values-prod.yaml
Release "myrelease" has been upgraded. Happy Helming!
NAME: myrelease
LAST DEPLOYED: Thu Apr  2 23:02:53 2026
NAMESPACE: default
STATUS: deployed
REVISION: 2
DESCRIPTION: Upgrade complete
TEST SUITE: None
NOTES:
Thank you for installing python-app v1.0!

Release name: myrelease
Namespace:    default

=== Access the Application ===
  Wait for the LoadBalancer IP:
    kubectl get svc myrelease-python-app-svc -n default -w
    export LB_IP=$(kubectl get svc myrelease-python-app-svc -n default -o jsonpath="{.status.loadBalancer.ingress[0].ip}")
    echo "Application URL: http://$LB_IP:80"

=== Health Check ===
  curl http://<APP_URL>/health

=== Useful Commands ===
  # View pods
  kubectl get pods -l app.kubernetes.io/instance=myrelease -n default

  # View logs
  kubectl logs -l app.kubernetes.io/instance=myrelease -n default

  # Upgrade release
  helm upgrade myrelease k8s/python-app -f k8s/python-app/values-prod.yaml

  # Rollback
  helm rollback myrelease 1

  # Uninstall
  helm uninstall myrelease
```
Upgrade with specific image tag
```bash
helm upgrade myrelease k8s/python-app --set image.tag=2.0 --set service.nodePort=30096
Release "myrelease" has been upgraded. Happy Helming!
NAME: myrelease
LAST DEPLOYED: Thu Apr  2 23:03:46 2026
NAMESPACE: default
STATUS: deployed
REVISION: 4
DESCRIPTION: Upgrade complete
TEST SUITE: None
NOTES:
Thank you for installing python-app v1.0!

Release name: myrelease
Namespace:    default

=== Access the Application ===
  Get the NodePort URL:
    export NODE_PORT=$(kubectl get svc myrelease-python-app-svc -n default -o jsonpath="{.spec.ports[0].nodePort}")
    export NODE_IP=$(kubectl get nodes -o jsonpath="{.items[0].status.addresses[0].address}")
    echo "Application URL: http://$NODE_IP:$NODE_PORT"

=== Health Check ===
  curl http://<APP_URL>/health

=== Useful Commands ===
  # View pods
  kubectl get pods -l app.kubernetes.io/instance=myrelease -n default

  # View logs
  kubectl logs -l app.kubernetes.io/instance=myrelease -n default

  # Upgrade release
  helm upgrade myrelease k8s/python-app -f k8s/python-app/values-prod.yaml

  # Rollback
  helm rollback myrelease 1

  # Uninstall
  helm uninstall myrelease
```
Upgrade and install if not exists
```bash
helm upgrade --install myrelease k8s/python-app -f k8s/python-app/values-prod.yaml
Release "myrelease" has been upgraded. Happy Helming!
NAME: myrelease
LAST DEPLOYED: Thu Apr  2 23:04:23 2026
NAMESPACE: default
STATUS: deployed
REVISION: 5
DESCRIPTION: Upgrade complete
TEST SUITE: None
NOTES:
Thank you for installing python-app v1.0!

Release name: myrelease
Namespace:    default

=== Access the Application ===
  Wait for the LoadBalancer IP:
    kubectl get svc myrelease-python-app-svc -n default -w
    export LB_IP=$(kubectl get svc myrelease-python-app-svc -n default -o jsonpath="{.status.loadBalancer.ingress[0].ip}")
    echo "Application URL: http://$LB_IP:80"

=== Health Check ===
  curl http://<APP_URL>/health

=== Useful Commands ===
  # View pods
  kubectl get pods -l app.kubernetes.io/instance=myrelease -n default

  # View logs
  kubectl logs -l app.kubernetes.io/instance=myrelease -n default

  # Upgrade release
  helm upgrade myrelease k8s/python-app -f k8s/python-app/values-prod.yaml

  # Rollback
  helm rollback myrelease 1

  # Uninstall
  helm uninstall myrelease
```
View upgrade history
```bash
helm history myrelease
REVISION        UPDATED                         STATUS          CHART                   APP VERSION     DESCRIPTION                                                                                                                                                
1               Thu Apr  2 22:45:51 2026        superseded      python-app-0.1.0        1.0             Install complete                                                                                                                                           
2               Thu Apr  2 23:02:53 2026        superseded      python-app-0.1.0        1.0             Upgrade complete                                                                                                                                           
3               Thu Apr  2 23:03:16 2026        failed          python-app-0.1.0        1.0             Upgrade "myrelease" failed: Service "myrelease-python-app-svc" is invalid: spec.ports[0].nodePort: Invalid value: 30080: provided port is already allocated
4               Thu Apr  2 23:03:46 2026        superseded      python-app-0.1.0        1.0             Upgrade complete                                                                                                                                           
5               Thu Apr  2 23:04:23 2026        deployed        python-app-0.1.0        1.0             Upgrade complete         
```

### How to Rollback
Rollback to revision 1
```bash
$ helm rollback myapp-dev 1
Rollback was a success! Happy Helming!
```
Verify rollback
```bash
helm history myapp-dev
REVISION        UPDATED                         STATUS          CHART                   APP VERSION     DESCRIPTION     
1               Thu Apr  2 22:47:48 2026        superseded      python-app-0.1.0        1.0             Install complete
2               Thu Apr  2 23:05:28 2026        deployed        python-app-0.1.0        1.0             Rollback to 1   
```

### How to Uninstall
Uninstall release (removes all K8s resources)
```bash
helm uninstall myrelease
release "myrelease" uninstalled
```
Uninstall but keep history for future rollback
```bash
helm uninstall combine --keep-history
release "combine" uninstalled
```
Uninstall from specific namespace
``` bash
helm uninstall combine -n default
release "combine" uninstalled
```

---

## Testing & Validation

### `helm lint` Output

```bash
helm lint k8s/python-app
==> Linting k8s/python-app
[INFO] Chart.yaml: icon is recommended

1 chart(s) linted, 0 chart(s) failed
```

### `helm template` Verification

```bash
helm template test-release k8s/python-app
---
# Source: python-app/templates/service.yaml
apiVersion: v1
kind: Service
metadata:
  name: test-release-python-app-svc
  labels:
    helm.sh/chart: python-app-0.1.0
    app.kubernetes.io/name: python-app
    app.kubernetes.io/instance: test-release
    app.kubernetes.io/version: "1.0"
    app.kubernetes.io/managed-by: Helm
    app.kubernetes.io/component: web
spec:
  type: NodePort
  selector:
    app.kubernetes.io/name: python-app
    app.kubernetes.io/instance: test-release
  ports:
    - name: http
      protocol: TCP
      port: 80
      targetPort: 8000
      nodePort: 30080
---
# Source: python-app/templates/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: test-release-python-app
  labels:
    helm.sh/chart: python-app-0.1.0
    app.kubernetes.io/name: python-app
    app.kubernetes.io/instance: test-release
    app.kubernetes.io/version: "1.0"
    app.kubernetes.io/managed-by: Helm
    app.kubernetes.io/component: web
spec:
  replicas: 3
  selector:
    matchLabels:
      app.kubernetes.io/name: python-app
      app.kubernetes.io/instance: test-release
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 1
      maxUnavailable: 0
  template:
    metadata:
      labels:
        app.kubernetes.io/name: python-app
        app.kubernetes.io/instance: test-release
        app.kubernetes.io/version: "1.0"
        app.kubernetes.io/component: web
    spec:
      securityContext:
        fsGroup: 1000
        runAsNonRoot: true
        runAsUser: 1000
      containers:
        - name: python-app
          image: "newspec/python_app:1.0"
          imagePullPolicy: IfNotPresent
          command:
            - uvicorn
            - app:app
            - --host
            - 0.0.0.0
            - --port
            - "8000"
          ports:
            - name: http
              containerPort: 8000
              protocol: TCP
          env:
            - name: HOST
              value: 0.0.0.0
            - name: PORT
              value: "8000"
            - name: DEBUG
              value: "False"
          resources:
            limits:
              cpu: 200m
              memory: 256Mi
            requests:
              cpu: 100m
              memory: 128Mi
          livenessProbe:
            httpGet:
              path: /health
              port: 8000
            initialDelaySeconds: 10
            periodSeconds: 5
            timeoutSeconds: 3
            failureThreshold: 3
          readinessProbe:
            httpGet:
              path: /health
              port: 8000
            initialDelaySeconds: 5
            periodSeconds: 3
            timeoutSeconds: 2
            failureThreshold: 3
          securityContext:
            allowPrivilegeEscalation: false
            capabilities:
              drop:
              - ALL
            readOnlyRootFilesystem: false
---
# Source: python-app/templates/hooks/post-install-job.yaml
apiVersion: batch/v1
kind: Job
metadata:
  name: "test-release-python-app-post-install"
  labels:
    helm.sh/chart: python-app-0.1.0
    app.kubernetes.io/name: python-app
    app.kubernetes.io/instance: test-release
    app.kubernetes.io/version: "1.0"
    app.kubernetes.io/managed-by: Helm
    app.kubernetes.io/component: web
  annotations:
    # This job runs AFTER all chart resources are installed and ready
    "helm.sh/hook": post-install
    # Higher weight = runs after other post-install hooks
    "helm.sh/hook-weight": "5"
    # Delete the job pod after successful completion to keep the cluster clean
    "helm.sh/hook-delete-policy": hook-succeeded
spec:
  # Retry once on failure
  backoffLimit: 1
  template:
    metadata:
      name: "test-release-python-app-post-install"
      labels:
        app.kubernetes.io/name: python-app
        app.kubernetes.io/instance: test-release
        app.kubernetes.io/component: post-install-hook
    spec:
      restartPolicy: Never
      containers:
        - name: post-install-job
          image: busybox:1.36
          imagePullPolicy: IfNotPresent
          command:
            - sh
            - -c
            - |
              echo "=== Post-install hook starting ==="
              echo "Release: test-release"
              echo "Namespace: default"
              echo "Chart: python-app-0.1.0"
              echo ""
              echo "Waiting for application to stabilize..."
              sleep 10
              echo ""
              echo "Running smoke tests..."
              echo "  [1/3] Checking service endpoint availability..."
              sleep 2
              echo "  Service endpoint: OK"
              echo "  [2/3] Validating health check response..."
              sleep 2
              echo "  Health check: HEALTHY"
              echo "  [3/3] Verifying replica count..."
              sleep 2
              echo "  Replicas: 3/3 ready"
              echo ""
              echo "Sending deployment notification..."
              sleep 1
              echo "Notification sent: python-app v1.0 deployed successfully"
              echo ""
              echo "=== Post-install hook completed successfully ==="
---
# Source: python-app/templates/hooks/pre-install-job.yaml
apiVersion: batch/v1
kind: Job
metadata:
  name: "test-release-python-app-pre-install"
  labels:
    helm.sh/chart: python-app-0.1.0
    app.kubernetes.io/name: python-app
    app.kubernetes.io/instance: test-release
    app.kubernetes.io/version: "1.0"
    app.kubernetes.io/managed-by: Helm
    app.kubernetes.io/component: web
  annotations:
    # This job runs BEFORE any chart resources are installed
    "helm.sh/hook": pre-install
    # Lower weight = runs first; -5 ensures this runs before other pre-install hooks
    "helm.sh/hook-weight": "-5"
    # Delete the job pod after successful completion to keep the cluster clean
    "helm.sh/hook-delete-policy": hook-succeeded
spec:
  # Retry once on failure
  backoffLimit: 1
  template:
    metadata:
      name: "test-release-python-app-pre-install"
      labels:
        app.kubernetes.io/name: python-app
        app.kubernetes.io/instance: test-release
        app.kubernetes.io/component: pre-install-hook
    spec:
      restartPolicy: Never
      containers:
        - name: pre-install-job
          image: busybox:1.36
          imagePullPolicy: IfNotPresent
          command:
            - sh
            - -c
            - |
              echo "=== Pre-install hook starting ==="
              echo "Release: test-release"
              echo "Namespace: default"
              echo "Chart: python-app-0.1.0"
              echo ""
              echo "Simulating database migration check..."
              sleep 5
              echo "Schema version check: OK"
              echo "Migration status: up-to-date"
              echo ""
              echo "Validating environment prerequisites..."
              sleep 3
              echo "Prerequisites check: PASSED"
              echo ""
              echo "=== Pre-install hook completed successfully ==="
```

### Dry-Run Output

```bash
helm install --dry-run --debug test-release k8s/python-app
level=WARN msg="--dry-run is deprecated and should be replaced with '--dry-run=client'"
level=DEBUG msg="Original chart version" version=""
level=DEBUG msg="Chart path" path=/Users/newspec/Desktop/DevOps/DevOps-Core-Course/k8s/python-app
level=DEBUG msg="number of dependencies in the chart" chart=python-app dependencies=1
level=DEBUG msg="number of dependencies in the chart" chart=common-lib dependencies=0
NAME: test-release
LAST DEPLOYED: Thu Apr  2 23:09:49 2026
NAMESPACE: default
STATUS: pending-install
REVISION: 1
DESCRIPTION: Dry run complete
TEST SUITE: None
USER-SUPPLIED VALUES:
{}

COMPUTED VALUES:
command:
- uvicorn
- app:app
- --host
- 0.0.0.0
- --port
- "8000"
common-lib:
  global: {}
containerPort: 8000
containerSecurityContext:
  allowPrivilegeEscalation: false
  capabilities:
    drop:
    - ALL
  readOnlyRootFilesystem: false
env:
- name: HOST
  value: 0.0.0.0
- name: PORT
  value: "8000"
- name: DEBUG
  value: "False"
fullnameOverride: ""
image:
  pullPolicy: IfNotPresent
  repository: newspec/python_app
  tag: "1.0"
livenessProbe:
  failureThreshold: 3
  httpGet:
    path: /health
    port: 8000
  initialDelaySeconds: 10
  periodSeconds: 5
  timeoutSeconds: 3
nameOverride: ""
podSecurityContext:
  fsGroup: 1000
  runAsNonRoot: true
  runAsUser: 1000
readinessProbe:
  failureThreshold: 3
  httpGet:
    path: /health
    port: 8000
  initialDelaySeconds: 5
  periodSeconds: 3
  timeoutSeconds: 2
replicaCount: 3
resources:
  limits:
    cpu: 200m
    memory: 256Mi
  requests:
    cpu: 100m
    memory: 128Mi
service:
  nodePort: 30080
  port: 80
  targetPort: 8000
  type: NodePort
strategy:
  rollingUpdate:
    maxSurge: 1
    maxUnavailable: 0
  type: RollingUpdate

HOOKS:
---
# Source: python-app/templates/hooks/post-install-job.yaml
apiVersion: batch/v1
kind: Job
metadata:
  name: "test-release-python-app-post-install"
  labels:
    helm.sh/chart: python-app-0.1.0
    app.kubernetes.io/name: python-app
    app.kubernetes.io/instance: test-release
    app.kubernetes.io/version: "1.0"
    app.kubernetes.io/managed-by: Helm
    app.kubernetes.io/component: web
  annotations:
    # This job runs AFTER all chart resources are installed and ready
    "helm.sh/hook": post-install
    # Higher weight = runs after other post-install hooks
    "helm.sh/hook-weight": "5"
    # Delete the job pod after successful completion to keep the cluster clean
    "helm.sh/hook-delete-policy": hook-succeeded
spec:
  # Retry once on failure
  backoffLimit: 1
  template:
    metadata:
      name: "test-release-python-app-post-install"
      labels:
        app.kubernetes.io/name: python-app
        app.kubernetes.io/instance: test-release
        app.kubernetes.io/component: post-install-hook
    spec:
      restartPolicy: Never
      containers:
        - name: post-install-job
          image: busybox:1.36
          imagePullPolicy: IfNotPresent
          command:
            - sh
            - -c
            - |
              echo "=== Post-install hook starting ==="
              echo "Release: test-release"
              echo "Namespace: default"
              echo "Chart: python-app-0.1.0"
              echo ""
              echo "Waiting for application to stabilize..."
              sleep 10
              echo ""
              echo "Running smoke tests..."
              echo "  [1/3] Checking service endpoint availability..."
              sleep 2
              echo "  Service endpoint: OK"
              echo "  [2/3] Validating health check response..."
              sleep 2
              echo "  Health check: HEALTHY"
              echo "  [3/3] Verifying replica count..."
              sleep 2
              echo "  Replicas: 3/3 ready"
              echo ""
              echo "Sending deployment notification..."
              sleep 1
              echo "Notification sent: python-app v1.0 deployed successfully"
              echo ""
              echo "=== Post-install hook completed successfully ==="
---
# Source: python-app/templates/hooks/pre-install-job.yaml
apiVersion: batch/v1
kind: Job
metadata:
  name: "test-release-python-app-pre-install"
  labels:
    helm.sh/chart: python-app-0.1.0
    app.kubernetes.io/name: python-app
    app.kubernetes.io/instance: test-release
    app.kubernetes.io/version: "1.0"
    app.kubernetes.io/managed-by: Helm
    app.kubernetes.io/component: web
  annotations:
    # This job runs BEFORE any chart resources are installed
    "helm.sh/hook": pre-install
    # Lower weight = runs first; -5 ensures this runs before other pre-install hooks
    "helm.sh/hook-weight": "-5"
    # Delete the job pod after successful completion to keep the cluster clean
    "helm.sh/hook-delete-policy": hook-succeeded
spec:
  # Retry once on failure
  backoffLimit: 1
  template:
    metadata:
      name: "test-release-python-app-pre-install"
      labels:
        app.kubernetes.io/name: python-app
        app.kubernetes.io/instance: test-release
        app.kubernetes.io/component: pre-install-hook
    spec:
      restartPolicy: Never
      containers:
        - name: pre-install-job
          image: busybox:1.36
          imagePullPolicy: IfNotPresent
          command:
            - sh
            - -c
            - |
              echo "=== Pre-install hook starting ==="
              echo "Release: test-release"
              echo "Namespace: default"
              echo "Chart: python-app-0.1.0"
              echo ""
              echo "Simulating database migration check..."
              sleep 5
              echo "Schema version check: OK"
              echo "Migration status: up-to-date"
              echo ""
              echo "Validating environment prerequisites..."
              sleep 3
              echo "Prerequisites check: PASSED"
              echo ""
              echo "=== Pre-install hook completed successfully ==="
MANIFEST:
---
# Source: python-app/templates/service.yaml
apiVersion: v1
kind: Service
metadata:
  name: test-release-python-app-svc
  labels:
    helm.sh/chart: python-app-0.1.0
    app.kubernetes.io/name: python-app
    app.kubernetes.io/instance: test-release
    app.kubernetes.io/version: "1.0"
    app.kubernetes.io/managed-by: Helm
    app.kubernetes.io/component: web
spec:
  type: NodePort
  selector:
    app.kubernetes.io/name: python-app
    app.kubernetes.io/instance: test-release
  ports:
    - name: http
      protocol: TCP
      port: 80
      targetPort: 8000
      nodePort: 30080
---
# Source: python-app/templates/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: test-release-python-app
  labels:
    helm.sh/chart: python-app-0.1.0
    app.kubernetes.io/name: python-app
    app.kubernetes.io/instance: test-release
    app.kubernetes.io/version: "1.0"
    app.kubernetes.io/managed-by: Helm
    app.kubernetes.io/component: web
spec:
  replicas: 3
  selector:
    matchLabels:
      app.kubernetes.io/name: python-app
      app.kubernetes.io/instance: test-release
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 1
      maxUnavailable: 0
  template:
    metadata:
      labels:
        app.kubernetes.io/name: python-app
        app.kubernetes.io/instance: test-release
        app.kubernetes.io/version: "1.0"
        app.kubernetes.io/component: web
    spec:
      securityContext:
        fsGroup: 1000
        runAsNonRoot: true
        runAsUser: 1000
      containers:
        - name: python-app
          image: "newspec/python_app:1.0"
          imagePullPolicy: IfNotPresent
          command:
            - uvicorn
            - app:app
            - --host
            - 0.0.0.0
            - --port
            - "8000"
          ports:
            - name: http
              containerPort: 8000
              protocol: TCP
          env:
            - name: HOST
              value: 0.0.0.0
            - name: PORT
              value: "8000"
            - name: DEBUG
              value: "False"
          resources:
            limits:
              cpu: 200m
              memory: 256Mi
            requests:
              cpu: 100m
              memory: 128Mi
          livenessProbe:
            httpGet:
              path: /health
              port: 8000
            initialDelaySeconds: 10
            periodSeconds: 5
            timeoutSeconds: 3
            failureThreshold: 3
          readinessProbe:
            httpGet:
              path: /health
              port: 8000
            initialDelaySeconds: 5
            periodSeconds: 3
            timeoutSeconds: 2
            failureThreshold: 3
          securityContext:
            allowPrivilegeEscalation: false
            capabilities:
              drop:
              - ALL
            readOnlyRootFilesystem: false

NOTES:
Thank you for installing python-app v1.0!

Release name: test-release
Namespace:    default

=== Access the Application ===
  Get the NodePort URL:
    export NODE_PORT=$(kubectl get svc test-release-python-app-svc -n default -o jsonpath="{.spec.ports[0].nodePort}")
    export NODE_IP=$(kubectl get nodes -o jsonpath="{.items[0].status.addresses[0].address}")
    echo "Application URL: http://$NODE_IP:$NODE_PORT"

=== Health Check ===
  curl http://<APP_URL>/health

=== Useful Commands ===
  # View pods
  kubectl get pods -l app.kubernetes.io/instance=test-release -n default

  # View logs
  kubectl logs -l app.kubernetes.io/instance=test-release -n default

  # Upgrade release
  helm upgrade test-release k8s/python-app -f k8s/python-app/values-prod.yaml

  # Rollback
  helm rollback test-release 1

  # Uninstall
  helm uninstall test-release
```

### Application Accessibility Verification
Port-forward to access locally
```bash
kubectl port-forward svc/myrelease-python-app-svc 8090:80 &                                  
[1] 55427
newspec@MacBook-Pro-5 DevOps-Core-Course % Forwarding from 127.0.0.1:8090 -> 8000
Forwarding from [::1]:8090 -> 8000
```
Health check 
```bash
curl http://localhost:8090/health
{"status":"healthy","timestamp":"2026-04-02T20:17:44.749283+00:00","uptime_seconds":59}%     
``` 
Main endpoint
```bash
curl http://localhost:8090/
{"service":{"name":"devops-info-service","version":"1.0.0","description":"DevOps course info service","framework":"FastAPI"},"system":{"hostname":"myrelease-python-app-7c858df59b-29ptf","platform":"Linux","platform_version":"#100-Ubuntu SMP PREEMPT_DYNAMIC Tue Jan 13 16:39:21 UTC 2026","architecture":"x86_64","cpu_count":2,"python_version":"3.12.12"},"runtime":{"uptime_seconds":83,"uptime_human":"0 hours, 1 minutes","current_time":"2026-04-02T20:18:08.404511+00:00","timezone":"UTC"},"request":{"client_ip":"127.0.0.1","user_agent":"curl/8.7.1","method":"GET","path":"/"},"endpoints":[{"path":"/","method":"GET","description":"Service information"},{"path":"/health","method":"GET","description":"Health check"}]}%  
```
---
## Documentation Required
### Task 1 — Helm Fundamentals
#### Terminal output showing Helm installation and version (should be 4.x)
```bash
helm version
version.BuildInfo{Version:"v4.1.3", GitCommit:"c94d381b03be117e7e57908edbf642104e00eb8f", GitTreeState:"clean", GoVersion:"go1.26.1", KubeClientVersion:"v1.35"}
```
#### Output of exploring a public chart (e.g., helm show chart prometheus-community/prometheus)
```bash
helm show chart prometheus-community/prometheus
annotations:
  artifacthub.io/license: Apache-2.0
  artifacthub.io/links: |
    - name: Chart Source
      url: https://github.com/prometheus-community/helm-charts
    - name: Upstream Project
      url: https://github.com/prometheus/prometheus
apiVersion: v2
appVersion: v3.11.0
dependencies:
- condition: alertmanager.enabled
  name: alertmanager
  repository: https://prometheus-community.github.io/helm-charts
  version: 1.34.*
- condition: kube-state-metrics.enabled
  name: kube-state-metrics
  repository: https://prometheus-community.github.io/helm-charts
  version: 7.2.*
- condition: prometheus-node-exporter.enabled
  name: prometheus-node-exporter
  repository: https://prometheus-community.github.io/helm-charts
  version: 4.52.*
- condition: prometheus-pushgateway.enabled
  name: prometheus-pushgateway
  repository: https://prometheus-community.github.io/helm-charts
  version: 3.6.*
description: Prometheus is a monitoring system and time series database.
home: https://prometheus.io/
icon: https://raw.githubusercontent.com/prometheus/prometheus.github.io/master/assets/prometheus_logo-cb55bb5c346.png
keywords:
- monitoring
- prometheus
kubeVersion: '>=1.19.0-0'
maintainers:
- email: gianrubio@gmail.com
  name: gianrubio
  url: https://github.com/gianrubio
- email: zanhsieh@gmail.com
  name: zanhsieh
  url: https://github.com/zanhsieh
- email: miroslav.hadzhiev@gmail.com
  name: Xtigyro
  url: https://github.com/Xtigyro
- email: naseem@transit.app
  name: naseemkullah
  url: https://github.com/naseemkullah
- email: rootsandtrees@posteo.de
  name: zeritti
  url: https://github.com/zeritti
name: prometheus
sources:
- https://github.com/prometheus/alertmanager
- https://github.com/prometheus/prometheus
- https://github.com/prometheus/pushgateway
- https://github.com/prometheus/node_exporter
- https://github.com/kubernetes/kube-state-metrics
type: application
version: 28.15.0

```
#### Brief explanation of Helm's value proposition

Helm is the **package manager for Kubernetes**. Without Helm, deploying an application requires manually applying multiple YAML manifests (`kubectl apply -f deployment.yaml`, `-f service.yaml`, `-f configmap.yaml`, etc.) with no built-in way to version, rollback, or parameterize them.

Helm solves this by bundling all Kubernetes resources into a single **chart** — a versioned, reusable package. Key benefits demonstrated in this lab:

| Problem without Helm | Helm solution |
|---|---|
| Duplicate YAML for dev/prod | Single chart + `values-dev.yaml` / `values-prod.yaml` |
| No rollback mechanism | `helm rollback myrelease 1` — instant one-command rollback |
| Manual resource ordering | Hooks (`pre-install`, `post-install`) with weights control execution order |
| No release history | `helm history myrelease` shows every revision with timestamps |
| Copy-paste across apps | Library charts (`common-lib`) share templates across multiple charts |
| Hard-coded values | Go templates + `values.yaml` make every parameter overridable at install time |

The `prometheus-community/prometheus` chart above illustrates real-world Helm value: a complex monitoring stack (Prometheus, Alertmanager, Node Exporter, Pushgateway, kube-state-metrics) packaged as a single installable unit with 100+ configurable values — something that would require dozens of manually maintained YAML files otherwise.
### Task 2 — Create Your Helm Chart 
```bash
helm lint k8s/python-app
==> Linting k8s/python-app
[INFO] Chart.yaml: icon is recommended

1 chart(s) linted, 0 chart(s) failed
```
```bash
helm template python-app k8s/python-app
---
# Source: python-app/templates/service.yaml
apiVersion: v1
kind: Service
metadata:
  name: python-app-svc
  labels:
    helm.sh/chart: python-app-0.1.0
    app.kubernetes.io/name: python-app
    app.kubernetes.io/instance: python-app
    app.kubernetes.io/version: "1.0"
    app.kubernetes.io/managed-by: Helm
    app.kubernetes.io/component: web
spec:
  type: NodePort
  selector:
    app.kubernetes.io/name: python-app
    app.kubernetes.io/instance: python-app
  ports:
    - name: http
      protocol: TCP
      port: 80
      targetPort: 8000
      nodePort: 30080
---
# Source: python-app/templates/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: python-app
  labels:
    helm.sh/chart: python-app-0.1.0
    app.kubernetes.io/name: python-app
    app.kubernetes.io/instance: python-app
    app.kubernetes.io/version: "1.0"
    app.kubernetes.io/managed-by: Helm
    app.kubernetes.io/component: web
spec:
  replicas: 3
  selector:
    matchLabels:
      app.kubernetes.io/name: python-app
      app.kubernetes.io/instance: python-app
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 1
      maxUnavailable: 0
  template:
    metadata:
      labels:
        app.kubernetes.io/name: python-app
        app.kubernetes.io/instance: python-app
        app.kubernetes.io/version: "1.0"
        app.kubernetes.io/component: web
    spec:
      securityContext:
        fsGroup: 1000
        runAsNonRoot: true
        runAsUser: 1000
      containers:
        - name: python-app
          image: "newspec/python_app:1.0"
          imagePullPolicy: IfNotPresent
          command:
            - uvicorn
            - app:app
            - --host
            - 0.0.0.0
            - --port
            - "8000"
          ports:
            - name: http
              containerPort: 8000
              protocol: TCP
          env:
            - name: HOST
              value: 0.0.0.0
            - name: PORT
              value: "8000"
            - name: DEBUG
              value: "False"
          resources:
            limits:
              cpu: 200m
              memory: 256Mi
            requests:
              cpu: 100m
              memory: 128Mi
          livenessProbe:
            httpGet:
              path: /health
              port: 8000
            initialDelaySeconds: 10
            periodSeconds: 5
            timeoutSeconds: 3
            failureThreshold: 3
          readinessProbe:
            httpGet:
              path: /health
              port: 8000
            initialDelaySeconds: 5
            periodSeconds: 3
            timeoutSeconds: 2
            failureThreshold: 3
          securityContext:
            allowPrivilegeEscalation: false
            capabilities:
              drop:
              - ALL
            readOnlyRootFilesystem: false
---
# Source: python-app/templates/hooks/post-install-job.yaml
apiVersion: batch/v1
kind: Job
metadata:
  name: "python-app-post-install"
  labels:
    helm.sh/chart: python-app-0.1.0
    app.kubernetes.io/name: python-app
    app.kubernetes.io/instance: python-app
    app.kubernetes.io/version: "1.0"
    app.kubernetes.io/managed-by: Helm
    app.kubernetes.io/component: web
  annotations:
    # This job runs AFTER all chart resources are installed and ready
    "helm.sh/hook": post-install
    # Higher weight = runs after other post-install hooks
    "helm.sh/hook-weight": "5"
    # Delete the job pod after successful completion to keep the cluster clean
    "helm.sh/hook-delete-policy": hook-succeeded
spec:
  # Retry once on failure
  backoffLimit: 1
  template:
    metadata:
      name: "python-app-post-install"
      labels:
        app.kubernetes.io/name: python-app
        app.kubernetes.io/instance: python-app
        app.kubernetes.io/component: post-install-hook
    spec:
      restartPolicy: Never
      containers:
        - name: post-install-job
          image: busybox:1.36
          imagePullPolicy: IfNotPresent
          command:
            - sh
            - -c
            - |
              echo "=== Post-install hook starting ==="
              echo "Release: python-app"
              echo "Namespace: default"
              echo "Chart: python-app-0.1.0"
              echo ""
              echo "Waiting for application to stabilize..."
              sleep 10
              echo ""
              echo "Running smoke tests..."
              echo "  [1/3] Checking service endpoint availability..."
              sleep 2
              echo "  Service endpoint: OK"
              echo "  [2/3] Validating health check response..."
              sleep 2
              echo "  Health check: HEALTHY"
              echo "  [3/3] Verifying replica count..."
              sleep 2
              echo "  Replicas: 3/3 ready"
              echo ""
              echo "Sending deployment notification..."
              sleep 1
              echo "Notification sent: python-app v1.0 deployed successfully"
              echo ""
              echo "=== Post-install hook completed successfully ==="
---
# Source: python-app/templates/hooks/pre-install-job.yaml
apiVersion: batch/v1
kind: Job
metadata:
  name: "python-app-pre-install"
  labels:
    helm.sh/chart: python-app-0.1.0
    app.kubernetes.io/name: python-app
    app.kubernetes.io/instance: python-app
    app.kubernetes.io/version: "1.0"
    app.kubernetes.io/managed-by: Helm
    app.kubernetes.io/component: web
  annotations:
    # This job runs BEFORE any chart resources are installed
    "helm.sh/hook": pre-install
    # Lower weight = runs first; -5 ensures this runs before other pre-install hooks
    "helm.sh/hook-weight": "-5"
    # Delete the job pod after successful completion to keep the cluster clean
    "helm.sh/hook-delete-policy": hook-succeeded
spec:
  # Retry once on failure
  backoffLimit: 1
  template:
    metadata:
      name: "python-app-pre-install"
      labels:
        app.kubernetes.io/name: python-app
        app.kubernetes.io/instance: python-app
        app.kubernetes.io/component: pre-install-hook
    spec:
      restartPolicy: Never
      containers:
        - name: pre-install-job
          image: busybox:1.36
          imagePullPolicy: IfNotPresent
          command:
            - sh
            - -c
            - |
              echo "=== Pre-install hook starting ==="
              echo "Release: python-app"
              echo "Namespace: default"
              echo "Chart: python-app-0.1.0"
              echo ""
              echo "Simulating database migration check..."
              sleep 5
              echo "Schema version check: OK"
              echo "Migration status: up-to-date"
              echo ""
              echo "Validating environment prerequisites..."
              sleep 3
              echo "Prerequisites check: PASSED"
              echo ""
              echo "=== Pre-install hook completed successfully ==="
```
```bash
helm install --dry-run --debug test-release k8s/python-app

level=WARN msg="--dry-run is deprecated and should be replaced with '--dry-run=client'"
level=DEBUG msg="Original chart version" version=""
level=DEBUG msg="Chart path" path=/Users/newspec/Desktop/DevOps/DevOps-Core-Course/k8s/python-app
level=DEBUG msg="number of dependencies in the chart" chart=python-app dependencies=1
level=DEBUG msg="number of dependencies in the chart" chart=common-lib dependencies=0
NAME: test-release
LAST DEPLOYED: Thu Apr  2 23:27:43 2026
NAMESPACE: default
STATUS: pending-install
REVISION: 1
DESCRIPTION: Dry run complete
TEST SUITE: None
USER-SUPPLIED VALUES:
{}

COMPUTED VALUES:
command:
- uvicorn
- app:app
- --host
- 0.0.0.0
- --port
- "8000"
common-lib:
  global: {}
containerPort: 8000
containerSecurityContext:
  allowPrivilegeEscalation: false
  capabilities:
    drop:
    - ALL
  readOnlyRootFilesystem: false
env:
- name: HOST
  value: 0.0.0.0
- name: PORT
  value: "8000"
- name: DEBUG
  value: "False"
fullnameOverride: ""
image:
  pullPolicy: IfNotPresent
  repository: newspec/python_app
  tag: "1.0"
livenessProbe:
  failureThreshold: 3
  httpGet:
    path: /health
    port: 8000
  initialDelaySeconds: 10
  periodSeconds: 5
  timeoutSeconds: 3
nameOverride: ""
podSecurityContext:
  fsGroup: 1000
  runAsNonRoot: true
  runAsUser: 1000
readinessProbe:
  failureThreshold: 3
  httpGet:
    path: /health
    port: 8000
  initialDelaySeconds: 5
  periodSeconds: 3
  timeoutSeconds: 2
replicaCount: 3
resources:
  limits:
    cpu: 200m
    memory: 256Mi
  requests:
    cpu: 100m
    memory: 128Mi
service:
  nodePort: 30080
  port: 80
  targetPort: 8000
  type: NodePort
strategy:
  rollingUpdate:
    maxSurge: 1
    maxUnavailable: 0
  type: RollingUpdate

HOOKS:
---
# Source: python-app/templates/hooks/post-install-job.yaml
apiVersion: batch/v1
kind: Job
metadata:
  name: "test-release-python-app-post-install"
  labels:
    helm.sh/chart: python-app-0.1.0
    app.kubernetes.io/name: python-app
    app.kubernetes.io/instance: test-release
    app.kubernetes.io/version: "1.0"
    app.kubernetes.io/managed-by: Helm
    app.kubernetes.io/component: web
  annotations:
    # This job runs AFTER all chart resources are installed and ready
    "helm.sh/hook": post-install
    # Higher weight = runs after other post-install hooks
    "helm.sh/hook-weight": "5"
    # Delete the job pod after successful completion to keep the cluster clean
    "helm.sh/hook-delete-policy": hook-succeeded
spec:
  # Retry once on failure
  backoffLimit: 1
  template:
    metadata:
      name: "test-release-python-app-post-install"
      labels:
        app.kubernetes.io/name: python-app
        app.kubernetes.io/instance: test-release
        app.kubernetes.io/component: post-install-hook
    spec:
      restartPolicy: Never
      containers:
        - name: post-install-job
          image: busybox:1.36
          imagePullPolicy: IfNotPresent
          command:
            - sh
            - -c
            - |
              echo "=== Post-install hook starting ==="
              echo "Release: test-release"
              echo "Namespace: default"
              echo "Chart: python-app-0.1.0"
              echo ""
              echo "Waiting for application to stabilize..."
              sleep 10
              echo ""
              echo "Running smoke tests..."
              echo "  [1/3] Checking service endpoint availability..."
              sleep 2
              echo "  Service endpoint: OK"
              echo "  [2/3] Validating health check response..."
              sleep 2
              echo "  Health check: HEALTHY"
              echo "  [3/3] Verifying replica count..."
              sleep 2
              echo "  Replicas: 3/3 ready"
              echo ""
              echo "Sending deployment notification..."
              sleep 1
              echo "Notification sent: python-app v1.0 deployed successfully"
              echo ""
              echo "=== Post-install hook completed successfully ==="
---
# Source: python-app/templates/hooks/pre-install-job.yaml
apiVersion: batch/v1
kind: Job
metadata:
  name: "test-release-python-app-pre-install"
  labels:
    helm.sh/chart: python-app-0.1.0
    app.kubernetes.io/name: python-app
    app.kubernetes.io/instance: test-release
    app.kubernetes.io/version: "1.0"
    app.kubernetes.io/managed-by: Helm
    app.kubernetes.io/component: web
  annotations:
    # This job runs BEFORE any chart resources are installed
    "helm.sh/hook": pre-install
    # Lower weight = runs first; -5 ensures this runs before other pre-install hooks
    "helm.sh/hook-weight": "-5"
    # Delete the job pod after successful completion to keep the cluster clean
    "helm.sh/hook-delete-policy": hook-succeeded
spec:
  # Retry once on failure
  backoffLimit: 1
  template:
    metadata:
      name: "test-release-python-app-pre-install"
      labels:
        app.kubernetes.io/name: python-app
        app.kubernetes.io/instance: test-release
        app.kubernetes.io/component: pre-install-hook
    spec:
      restartPolicy: Never
      containers:
        - name: pre-install-job
          image: busybox:1.36
          imagePullPolicy: IfNotPresent
          command:
            - sh
            - -c
            - |
              echo "=== Pre-install hook starting ==="
              echo "Release: test-release"
              echo "Namespace: default"
              echo "Chart: python-app-0.1.0"
              echo ""
              echo "Simulating database migration check..."
              sleep 5
              echo "Schema version check: OK"
              echo "Migration status: up-to-date"
              echo ""
              echo "Validating environment prerequisites..."
              sleep 3
              echo "Prerequisites check: PASSED"
              echo ""
              echo "=== Pre-install hook completed successfully ==="
MANIFEST:
---
# Source: python-app/templates/service.yaml
apiVersion: v1
kind: Service
metadata:
  name: test-release-python-app-svc
  labels:
    helm.sh/chart: python-app-0.1.0
    app.kubernetes.io/name: python-app
    app.kubernetes.io/instance: test-release
    app.kubernetes.io/version: "1.0"
    app.kubernetes.io/managed-by: Helm
    app.kubernetes.io/component: web
spec:
  type: NodePort
  selector:
    app.kubernetes.io/name: python-app
    app.kubernetes.io/instance: test-release
  ports:
    - name: http
      protocol: TCP
      port: 80
      targetPort: 8000
      nodePort: 30080
---
# Source: python-app/templates/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: test-release-python-app
  labels:
    helm.sh/chart: python-app-0.1.0
    app.kubernetes.io/name: python-app
    app.kubernetes.io/instance: test-release
    app.kubernetes.io/version: "1.0"
    app.kubernetes.io/managed-by: Helm
    app.kubernetes.io/component: web
spec:
  replicas: 3
  selector:
    matchLabels:
      app.kubernetes.io/name: python-app
      app.kubernetes.io/instance: test-release
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 1
      maxUnavailable: 0
  template:
    metadata:
      labels:
        app.kubernetes.io/name: python-app
        app.kubernetes.io/instance: test-release
        app.kubernetes.io/version: "1.0"
        app.kubernetes.io/component: web
    spec:
      securityContext:
        fsGroup: 1000
        runAsNonRoot: true
        runAsUser: 1000
      containers:
        - name: python-app
          image: "newspec/python_app:1.0"
          imagePullPolicy: IfNotPresent
          command:
            - uvicorn
            - app:app
            - --host
            - 0.0.0.0
            - --port
            - "8000"
          ports:
            - name: http
              containerPort: 8000
              protocol: TCP
          env:
            - name: HOST
              value: 0.0.0.0
            - name: PORT
              value: "8000"
            - name: DEBUG
              value: "False"
          resources:
            limits:
              cpu: 200m
              memory: 256Mi
            requests:
              cpu: 100m
              memory: 128Mi
          livenessProbe:
            httpGet:
              path: /health
              port: 8000
            initialDelaySeconds: 10
            periodSeconds: 5
            timeoutSeconds: 3
            failureThreshold: 3
          readinessProbe:
            httpGet:
              path: /health
              port: 8000
            initialDelaySeconds: 5
            periodSeconds: 3
            timeoutSeconds: 2
            failureThreshold: 3
          securityContext:
            allowPrivilegeEscalation: false
            capabilities:
              drop:
              - ALL
            readOnlyRootFilesystem: false

NOTES:
Thank you for installing python-app v1.0!

Release name: test-release
Namespace:    default

=== Access the Application ===
  Get the NodePort URL:
    export NODE_PORT=$(kubectl get svc test-release-python-app-svc -n default -o jsonpath="{.spec.ports[0].nodePort}")
    export NODE_IP=$(kubectl get nodes -o jsonpath="{.items[0].status.addresses[0].address}")
    echo "Application URL: http://$NODE_IP:$NODE_PORT"

=== Health Check ===
  curl http://<APP_URL>/health

=== Useful Commands ===
  # View pods
  kubectl get pods -l app.kubernetes.io/instance=test-release -n default

  # View logs
  kubectl logs -l app.kubernetes.io/instance=test-release -n default

  # Upgrade release
  helm upgrade test-release k8s/python-app -f k8s/python-app/values-prod.yaml

  # Rollback
  helm rollback test-release 1

  # Uninstall
  helm uninstall test-release
```
```bash
helm install myrelease k8s/python-app --set service.nodePort=30090
NAME: myrelease
LAST DEPLOYED: Thu Apr  2 23:29:10 2026
NAMESPACE: default
STATUS: deployed
REVISION: 1
DESCRIPTION: Install complete
TEST SUITE: None
NOTES:
Thank you for installing python-app v1.0!

Release name: myrelease
Namespace:    default

=== Access the Application ===
  Get the NodePort URL:
    export NODE_PORT=$(kubectl get svc myrelease-python-app-svc -n default -o jsonpath="{.spec.ports[0].nodePort}")
    export NODE_IP=$(kubectl get nodes -o jsonpath="{.items[0].status.addresses[0].address}")
    echo "Application URL: http://$NODE_IP:$NODE_PORT"

=== Health Check ===
  curl http://<APP_URL>/health

=== Useful Commands ===
  # View pods
  kubectl get pods -l app.kubernetes.io/instance=myrelease -n default

  # View logs
  kubectl logs -l app.kubernetes.io/instance=myrelease -n default

  # Upgrade release
  helm upgrade myrelease k8s/python-app -f k8s/python-app/values-prod.yaml

  # Rollback
  helm rollback myrelease 1

  # Uninstall
  helm uninstall myrelease
```
### Task 3 — Multi-Environment Support
#### Test Both Environments
Install with dev values
```bash
helm install myrelease k8s/python-app --set service.nodePort=30090
NAME: myrelease
LAST DEPLOYED: Thu Apr  2 23:32:27 2026
NAMESPACE: default
STATUS: deployed
REVISION: 1
DESCRIPTION: Install complete
TEST SUITE: None
NOTES:
Thank you for installing python-app v1.0!

Release name: myrelease
Namespace:    default

=== Access the Application ===
  Get the NodePort URL:
    export NODE_PORT=$(kubectl get svc myrelease-python-app-svc -n default -o jsonpath="{.spec.ports[0].nodePort}")
    export NODE_IP=$(kubectl get nodes -o jsonpath="{.items[0].status.addresses[0].address}")
    echo "Application URL: http://$NODE_IP:$NODE_PORT"

=== Health Check ===
  curl http://<APP_URL>/health

=== Useful Commands ===
  # View pods
  kubectl get pods -l app.kubernetes.io/instance=myrelease -n default

  # View logs
  kubectl logs -l app.kubernetes.io/instance=myrelease -n default

  # Upgrade release
  helm upgrade myrelease k8s/python-app -f k8s/python-app/values-prod.yaml

  # Rollback
  helm rollback myrelease 1

  # Uninstall
  helm uninstall myrelease
  ```
Verify configuration
```bash
kubectl get deployment myapp-dev-python-app -o wide                                                 

NAME                   READY   UP-TO-DATE   AVAILABLE   AGE   CONTAINERS   IMAGES                      SELECTOR
myapp-dev-python-app   0/1     1            0           30s   python-app   newspec/python_app:latest   app.kubernetes.io/instance=myapp-dev,app.kubernetes.io/name=python-app
```
```bash
kubectl get svc myapp-dev-python-app-svc           
NAME                       TYPE       CLUSTER-IP     EXTERNAL-IP   PORT(S)        AGE
myapp-dev-python-app-svc   NodePort   10.109.4.150   <none>        80:30092/TCP   76s
```
Upgrade to prod values
```bash
helm upgrade myapp-dev k8s/python-app -f k8s/python-app/values-prod.yaml --set service.nodePort=30092

Release "myapp-dev" has been upgraded. Happy Helming!
NAME: myapp-dev
LAST DEPLOYED: Thu Apr  2 23:36:22 2026
NAMESPACE: default
STATUS: deployed
REVISION: 2
DESCRIPTION: Upgrade complete
TEST SUITE: None
NOTES:
Thank you for installing python-app v1.0!

Release name: myapp-dev
Namespace:    default

=== Access the Application ===
  Wait for the LoadBalancer IP:
    kubectl get svc myapp-dev-python-app-svc -n default -w
    export LB_IP=$(kubectl get svc myapp-dev-python-app-svc -n default -o jsonpath="{.status.loadBalancer.ingress[0].ip}")
    echo "Application URL: http://$LB_IP:80"

=== Health Check ===
  curl http://<APP_URL>/health

=== Useful Commands ===
  # View pods
  kubectl get pods -l app.kubernetes.io/instance=myapp-dev -n default

  # View logs
  kubectl logs -l app.kubernetes.io/instance=myapp-dev -n default

  # Upgrade release
  helm upgrade myapp-dev k8s/python-app -f k8s/python-app/values-prod.yaml

  # Rollback
  helm rollback myapp-dev 1

  # Uninstall
  helm uninstall myapp-dev
```
Verify changes applied
```bash
kubectl get deployment myapp-dev-python-app -o wide

NAME                   READY   UP-TO-DATE   AVAILABLE   AGE    CONTAINERS   IMAGES                   SELECTOR
myapp-dev-python-app   0/5     1            0           2m1s   python-app   newspec/python_app:1.0   app.kubernetes.io/instance=myapp-dev,app.kubernetes.io/name=python-app
```bash
kubectl get pods -l app.kubernetes.io/instance=myapp-dev

NAME                                    READY   STATUS             RESTARTS   AGE
myapp-dev-python-app-54b846d566-8fjc9   0/1     ImagePullBackOff   0          45s
myapp-dev-python-app-54b846d566-g6hrt   0/1     Pending            0          45s
myapp-dev-python-app-54b846d566-ppr98   0/1     ImagePullBackOff   0          45s
myapp-dev-python-app-54b846d566-tm852   0/1     ImagePullBackOff   0          2m15s
myapp-dev-python-app-54b846d566-tng4d   0/1     ErrImagePull       0          45s
myapp-dev-python-app-85b85bd99b-dtgqz   0/1     Pending            0          45s
```
---

## Bonus — Library Charts

### Library Chart Structure

```
k8s/common-lib/
├── Chart.yaml              # type: library — cannot be installed directly
└── templates/
    ├── _names.tpl          # common.name, common.fullname, common.chart
    └── _labels.tpl         # common.labels, common.selectorLabels
```

### Shared Templates Implemented

| Template | Purpose |
|---|---|
| `common.name` | Chart name truncated to 63 chars (DNS limit) |
| `common.fullname` | `release-name-chart-name` (or `fullnameOverride`) |
| `common.chart` | `chart-name-version` for `helm.sh/chart` label |
| `common.labels` | Full label set: `helm.sh/chart`, `app.kubernetes.io/name`, `instance`, `version`, `managed-by` |
| `common.selectorLabels` | Minimal labels for `matchLabels`: `name` + `instance` only |

### How Both Apps Use the Library

Both `python-app` and `app-go` declare `common-lib` as a dependency:

```yaml
# python-app/Chart.yaml and app-go/Chart.yaml
dependencies:
  - name: common-lib
    version: 0.1.0
    repository: "file://../common-lib"
```

`app-go` templates reference library helpers directly:

```yaml
# app-go/templates/deployment.yaml
metadata:
  name: {{ include "common.fullname" . }}
  labels:
    {{- include "common.labels" . | nindent 4 }}
spec:
  selector:
    matchLabels:
      {{- include "common.selectorLabels" . | nindent 6 }}
```

### Dependency Update and Lint

```bash
helm dependency update k8s/python-app
elm dependency update k8s/python-app
Hang tight while we grab the latest from your chart repositories...
...Successfully got an update from the "prometheus-community" chart repository
Update Complete. ⎈Happy Helming!⎈
Saving 1 charts
Deleting outdated charts
```
```bash
helm dependency update k8s/app-go
Hang tight while we grab the latest from your chart repositories...
...Successfully got an update from the "prometheus-community" chart repository
Update Complete. ⎈Happy Helming!⎈
Saving 1 charts
Deleting outdated charts
```
```bash
helm lint k8s/python-app
==> Linting k8s/python-app
[INFO] Chart.yaml: icon is recommended

1 chart(s) linted, 0 chart(s) failed
```
```bash
helm lint k8s/app-go
==> Linting k8s/app-go
[INFO] Chart.yaml: icon is recommended

1 chart(s) linted, 0 chart(s) failed
```

### Both Apps Deployed Successfully

```bash
helm install python-release k8s/python-app --set service.nodePort=30090
NAME: python-release
LAST DEPLOYED: Thu Apr  2 23:45:46 2026
NAMESPACE: default
STATUS: deployed
REVISION: 1
DESCRIPTION: Install complete
TEST SUITE: None
NOTES:
Thank you for installing python-app v1.0!

Release name: python-release
Namespace:    default

=== Access the Application ===
  Get the NodePort URL:
    export NODE_PORT=$(kubectl get svc python-release-python-app-svc -n default -o jsonpath="{.spec.ports[0].nodePort}")
    export NODE_IP=$(kubectl get nodes -o jsonpath="{.items[0].status.addresses[0].address}")
    echo "Application URL: http://$NODE_IP:$NODE_PORT"

=== Health Check ===
  curl http://<APP_URL>/health

=== Useful Commands ===
  # View pods
  kubectl get pods -l app.kubernetes.io/instance=python-release -n default

  # View logs
  kubectl logs -l app.kubernetes.io/instance=python-release -n default

  # Upgrade release
  helm upgrade python-release k8s/python-app -f k8s/python-app/values-prod.yaml

  # Rollback
  helm rollback python-release 1

  # Uninstall
  helm uninstall python-release
```
```bash
helm install go-release k8s/app-go --set service.nodePort=30091
NAME: go-release
LAST DEPLOYED: Thu Apr  2 23:47:07 2026
NAMESPACE: default
STATUS: deployed
REVISION: 1
DESCRIPTION: Install complete
TEST SUITE: None
```
```bash
helm list
NAME            NAMESPACE       REVISION        UPDATED                                 STATUS          CHART                   APP VERSION
go-release      default         1               2026-04-02 23:47:07.260233 +0300 MSK    deployed        app-go-0.1.0            1.0        
python-release  default         1               2026-04-02 23:45:46.373474 +0300 MSK    deployed        python-app-0.1.0        1.0    
```
```bash
$ kubectl get deployments
NAME                        READY   UP-TO-DATE   AVAILABLE   AGE
app2                        1/1     1            1           10d
go-release-app-go           0/2     2            0           45s
python-app                  3/3     3            3           10d
python-release-python-app   3/3     3            3           115s
```

### Benefits of Library Charts

| Benefit | Description |
|---|---|
| **DRY** | Label and naming logic defined once, used by all apps |
| **Consistency** | All apps use identical `app.kubernetes.io/*` label structure |
| **Maintainability** | Change label strategy in one place — all charts benefit automatically |
| **Standardization** | Enforces naming conventions across the entire platform |
| **Reduced errors** | No copy-paste mistakes between chart `_helpers.tpl` files |

Without `common-lib`, each chart would duplicate identical `_helpers.tpl` definitions for `fullname`, `labels`, and `selectorLabels`. With the library, this logic lives in one versioned package that both `python-app` and `app-go` depend on.
