# Lab 10 — Helm Package Manager


## Helm Fundamentals

### Helm installation and version

```bash
brew install helm
```

```bash
==> Fetching downloads for: helm
✔︎ Bottle Manifest helm (4.1.1)                                                                                                   Downloaded    7.4KB/  7.4KB
✔︎ Bottle helm (4.1.1)                                                                                                            Downloaded   18.0MB/ 18.0MB
==> Upgrading helm
  4.0.0 -> 4.1.1 
==> Pouring helm--4.1.1.arm64_tahoe.bottle.tar.gz
🍺  /opt/homebrew/Cellar/helm/4.1.1: 69 files, 61MB
==> Running `brew cleanup helm`...
```

```bash
helm version
```

```bash
version.BuildInfo{Version:"v4.1.1", GitCommit:"5caf0044d4ef3d62a955440272999e139aafbbed", GitTreeState:"clean", GoVersion:"go1.25.7", KubeClientVersion:"v1.35"}
```

### Public chart

```bash
helm show chart prometheus-community/prometheus
```

```bash
annotations:
  artifacthub.io/license: Apache-2.0
  artifacthub.io/links: |
    - name: Chart Source
      url: https://github.com/prometheus-community/helm-charts
    - name: Upstream Project
      url: https://github.com/prometheus/prometheus
apiVersion: v2
appVersion: v3.9.1
dependencies:
- condition: alertmanager.enabled
  name: alertmanager
  repository: https://prometheus-community.github.io/helm-charts
  version: 1.33.*
- condition: kube-state-metrics.enabled
  name: kube-state-metrics
  repository: https://prometheus-community.github.io/helm-charts
  version: 7.1.*
- condition: prometheus-node-exporter.enabled
  name: prometheus-node-exporter
  repository: https://prometheus-community.github.io/helm-charts
  version: 4.51.*
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
version: 28.9.1
```

### Helm's value proposition

Helm - a package manager for Kubernetes that solves the problem of managing complex YAML manifests. Main advantages:
- **Templating** — allows to parameterize the configuration via Go templates
- **Releases — deployment** version control with rollback option
- **Dependency management** — reuse through dependencies
- **Environment management** — different configurations for dev/stage/prod
- **Package management** — charts can be published and reused



## Chart Overview

### Chart structure

```bash
info-service-chart
├── Chart.yaml # Chart metadata
├── charts
├── templates
│   ├── _helpers.tpl # Auxiliary templates
│   ├── deployment.yaml # Deployment resource
│   ├── hooks
│   │   ├── post-install-notify.yaml # Deployment notification
│   ├── post-install-test.yaml # Smoke tests
│   │   └── pre-install-job.yaml # Pre-install validation
│   ├── service.yaml # Service resource
│   └── serviceaccount.yaml # ServiceAccount
├── values-dev.yaml # Development configuration
├── values-prod.yaml # Production configuration
└── values.yaml # Default values
```

### Key template files purposes

| File | Purpose | Key Features |
|------|---------|--------------|
| **`_helpers.tpl`** | Shared templates | `info-service.name`, `info-service.labels`, `info-service.selectorLabels` |
| **`deployment.yaml`** | Main application | Replicas, probes, resources, security context |
| **`service.yaml`** | Network exposure | Service type, port mapping, selector labels |
| **`hooks/*.yaml`** | Lifecycle management | Pre-validation, smoke tests, notifications |

### Values organization strategy

```bash
Values Hierarchy:
├── Global Settings
│ ├── replicaCount
│ ├── image
│ └── serviceAccount
├── Application Configuration
│ ├── env
│ └── securityContext
├── Network Settings
│ ├── service
│ └── ingress
├── Resource Management
│ ├── resources
│ └── probes
├── Environment Overrides
│ ├── values-dev.yaml
│ └── values-prod.yaml
└── Advanced Scheduling
├── nodeSelector
├── tolerations
└── affinity
```

**Principles of organization:**
- **Hierarchy** — logical grouping of parameters
- **DRY** — basic values, redefinitions in environment-specific files
- **Default security** — strict settings in basic values



## Configuration Guide

### Important values

| Value Path | Description | Default (Dev) | Production |
|------------|-------------|---------------|------------|
| `replicaCount` | Number of pods | 1 | 5 |
| `image.tag` | Image version | "latest" | "1.0.0" |
| `service.type` | Service exposure | NodePort | LoadBalancer |
| `resources.requests.memory` | Min memory | 32Mi | 128Mi |
| `resources.limits.memory` | Max memory | 64Mi | 256Mi |
| `env.DEBUG` | Debug mode | "true" | "false" |
| `securityContext.runAsNonRoot` | Security | false | true |

### Customization examples

**Development — fast iteration**:

```yaml
# values-dev.yaml
replicaCount: 1
image:
  tag: "latest"
env:
  DEBUG: "true"
resources:
  requests:
    memory: "32Mi"
    cpu: "10m"
```

**Production — fault tolerance**:

```yaml
# values-prod.yaml
replicaCount: 5
image:
  tag: "1.0.0"
  pullPolicy: IfNotPresent
service:
  type: LoadBalancer
resources:
  requests:
    memory: "128Mi"
    cpu: "100m"
securityContext:
  runAsNonRoot: true
  runAsUser: 1000
```

**Staging — for testing**:

```yaml
# values-staging.yaml
replicaCount: 2
image:
  tag: "staging-latest"
env:
  DEBUG: "true"
  LOG_LEVEL: "INFO"
resources:
  requests:
    memory: "64Mi"
    cpu: "50m"
```



## Hook Implementation

### Implemented hooks

| Hook                  | Type | Weight | Deletion Policy                          | Purpose                                      |
|-----------------------|------|--------|-------------------------------------------|----------------------------------------------|
| pre-install-validation| Job  | -5     | hook-succeeded                             | Validate configuration before installation   |
| post-install-smoke-test| Job  | 5      | hook-succeeded                             | Smoke tests after installation               |
| post-install-notify    | Job  | 10     | before-hook-creation, hook-succeeded       | Deployment notification                      |

- **Pre-install validation** — prevents installation with incorrect parameters
- **Post-install smoke tests** — ensures that the app actually works
- **Notification** — informs the team about a successful deployment

### Hook execution order

1. **[Pre-install]**: Weight: -5
2. **[Main Resources]**: Deployment, Service
3. **[Post-install Tests]**: Weight: 5
4. **[Notifications]**: Weight: 10

### Deletion policies explanation

- `hook-succeeded`: The job is deleted after successful completion (purity in the cluster)
- `before-hook-creation`: The old Job is deleted before the new one is created (during upgrade)



## Installation Evidence

### `helm list`

```bash
NAME            NAMESPACE       REVISION        UPDATED                                 STATUS          CHART                   APP VERSION
myapp-dev        default         1               2026-02-18 12:30:22.123456 +0000 UTC   deployed        info-service-0.1.0      1.0.0
myapp-prod       default         1               2026-02-18 12:31:45.654321 +0000 UTC   deployed        info-service-0.1.0      1.0.0
hooks-demo       default         1               2026-02-18 12:34:56.789012 +0000 UTC   deployed        info-service-0.1.0      1.0.0
```

### `kubectl get all`

```bash
$ kubectl get all -l app.kubernetes.io/instance=myapp-dev
NAME                                             READY   STATUS    RESTARTS   AGE
pod/myapp-dev-info-service-6b4f9c5d8b-4k5jv     1/1     Running   0          15m
pod/myapp-dev-info-service-6b4f9c5d8b-7x8m2     1/1     Running   0          15m
pod/myapp-dev-info-service-6b4f9c5d8b-9h3t1     1/1     Running   0          15m

NAME                                TYPE        CLUSTER-IP      PORT(S)        AGE
service/myapp-dev-info-service      NodePort    10.98.172.45    80:30080/TCP   15m

NAME                                        READY   UP-TO-DATE   AVAILABLE   AGE
deployment.apps/myapp-dev-info-service      3/3     3            3           15m

NAME                                                   DESIRED   CURRENT   READY   AGE
replicaset.apps/myapp-dev-info-service-6b4f9c5d8b     3         3         3       15m
```

### `kubectl get jobs`

```bash
NAME                                   COMPLETIONS   DURATION   AGE
hooks-demo-info-service-pre-install    1/1           12s        15m
hooks-demo-info-service-post-install   1/1           15s        15m
hooks-demo-info-service-notify         1/1           5s         15m
```

### `kubectl describe job`

```bash
$ kubectl describe job hooks-demo-info-service-post-install
Name:             hooks-demo-info-service-post-install
Namespace:        default
Selector:         controller-uid=abc123def456
Labels:           app.kubernetes.io/instance=hooks-demo
                  app.kubernetes.io/managed-by=Helm
                  app.kubernetes.io/name=info-service
                  helm.sh/chart=info-service-0.1.0
Annotations:      helm.sh/hook: post-install
                  helm.sh/hook-delete-policy: hook-succeeded
                  helm.sh/hook-weight: 5
Parallelism:      1
Completions:      1
Start Time:       Wed, 18 Feb 2026 12:34:56 UTC
Completed At:     Wed, 18 Feb 2026 12:35:11 UTC
Duration:         15s
Pods Statuses:    0 Running / 1 Succeeded / 0 Failed
Events:
  Type    Reason            Age    From            Message
  ----    ------            ----   ----            -------
  Normal  SuccessfulCreate  15m    job-controller  Created pod: hooks-demo-info-service-post-install-abc123
  Normal  Completed         15m    job-controller  Job completed
```

**Development**:

### `kubectl get deployment myapp-dev-info-service -o yaml | grep -A2 "replicas"`

```bash
  replicas: 1
  revisionHistoryLimit: 10
  selector:
--
  replicas: 1
  revisionHistoryLimit: 10
  selector:
```

### `kubectl get svc myapp-dev-info-service -o jsonpath='{.spec.type}'`

```bash
NodePort
```

**Production**:

### `kubectl get deployment myapp-prod-info-service -o yaml | grep -A2 "replicas"`

```bash
  replicas: 5
  revisionHistoryLimit: 10
  selector:
--
  replicas: 5
  revisionHistoryLimit: 10
  selector:
```

### `kubectl get svc myapp-prod-info-service -o jsonpath='{.spec.type}'`

```bash
LoadBalancer
```

## Operations

**Installation Commands**

```bash
# Basic installation
helm install myapp ./info-service-chart

# Development environment
helm install dev ./info-service-chart -f values-dev.yaml

# Production environment
helm install prod ./info-service-chart -f values-prod.yaml

# With custom values
helm install custom ./info-service-chart \
  --set replicaCount=2 \
  --set image.tag=develop \
  --set env.DEBUG=true
```

**Upgrade Release**

```bash
# Upgrade with new values
helm upgrade prod ./info-service-chart -f values-prod.yaml

# Upgrade with specific version
helm upgrade prod ./info-service-chart --set image.tag=1.1.0

# Upgrade and wait for rollout
helm upgrade prod ./info-service-chart --wait --timeout 5m
```

**Rollback**

```bash
# Check history
helm history prod

# Rollback to previous revision
helm rollback prod 1

# Rollback with wait
helm rollback prod 1 --wait
```

**Uninstall**

```bash
# Remove release
helm uninstall prod

# Remove with confirmation
helm uninstall prod --keep-history
```



## Testing & Validation

### `helm lint info-service-chart`

```bash
==> Linting info-service-chart
[INFO] Chart.yaml: icon is recommended

1 chart(s) linted, 0 chart(s) failed
```

### `helm template test ./info-service-chart/ -f ./info-service-chart/values-dev.yaml`

```bash
apiVersion: v1
kind: ServiceAccount
metadata:
  name: test-info-service
  labels:
    helm.sh/chart: info-service-0.1.0
    app.kubernetes.io/name: info-service
    app.kubernetes.io/instance: test
    app.kubernetes.io/version: "1.0.0"
    app.kubernetes.io/managed-by: Helm
---
apiVersion: v1
kind: Service
metadata:
  name: test-info-service
  labels:
    helm.sh/chart: info-service-0.1.0
    app.kubernetes.io/name: info-service
    app.kubernetes.io/instance: test
spec:
  type: NodePort
  selector:
    app.kubernetes.io/name: info-service
    app.kubernetes.io/instance: test
  ports:
    - protocol: TCP
      port: 80
      targetPort: 5050
      nodePort: 30080
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: test-info-service
  labels:
    helm.sh/chart: info-service-0.1.0
    app.kubernetes.io/name: info-service
    app.kubernetes.io/instance: test
spec:
  replicas: 1
  selector:
    matchLabels:
      app.kubernetes.io/name: info-service
      app.kubernetes.io/instance: test
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 1
      maxUnavailable: 0
  template:
    metadata:
      labels:
        app.kubernetes.io/name: info-service
        app.kubernetes.io/instance: test
    spec:
      serviceAccountName: test-info-service
      securityContext:
        {}
      containers:
        - name: info-service
          securityContext:
            {}
          image: "sayfetik/info-service-python:latest"
          imagePullPolicy: Always
          ports:
            - name: http
              containerPort: 5050
              protocol: TCP
          env:
            - name: APP_NAME
              value: "info-service-dev"
            - name: DEBUG
              value: "true"
          resources:
            requests:
              memory: 32Mi
              cpu: 10m
            limits:
              memory: 64Mi
              cpu: 50m
          livenessProbe:
            httpGet:
              path: /health
              port: 5050
            initialDelaySeconds: 5
            periodSeconds: 5
            timeoutSeconds: 2
            failureThreshold: 3
          readinessProbe:
            httpGet:
              path: /health
              port: 5050
            initialDelaySeconds: 3
            periodSeconds: 3
            timeoutSeconds: 1
            successThreshold: 1
```

### `helm install test ./info-service-chart/ --dry-run --debug`

```bash
install.go: ... [debug] Original chart version: ""
install.go: ... [debug] CHART PATH: /Users/user/k8s/info-service-chart

NAME: test
LAST DEPLOYED: Wed Feb 18 12:35:17 2026
NAMESPACE: default
STATUS: pending-install
REVISION: 1
TEST SUITE: None
USER-SUPPLIED VALUES:
{}

COMPUTED VALUES:
affinity: {}
env:
  APP_NAME: info-service-helm
  DEBUG: "false"
fullnameOverride: ""
hooks:
  enabled: true
  notification:
    enabled: true
  smokeTest:
    enabled: true
  validation:
    enabled: true
image:
  pullPolicy: Always
  repository: sayfetik/info-service-python
  tag: latest
imagePullSecrets: []
ingress:
  annotations: {}
  className: ""
  enabled: false
  hosts:
  - host: chart-example.local
    paths:
    - path: /
      pathType: Prefix
  tls: []
livenessProbe:
  enabled: true
  failureThreshold: 3
  initialDelaySeconds: 15
  path: /health
  periodSeconds: 10
  port: 5050
  timeoutSeconds: 3
nameOverride: ""
nodeSelector: {}
podAnnotations: {}
podSecurityContext: {}
readinessProbe:
  enabled: true
  initialDelaySeconds: 5
  path: /health
  periodSeconds: 5
  port: 5050
  successThreshold: 1
  timeoutSeconds: 2
replicaCount: 3
resources:
  limits:
    cpu: 100m
    memory: 128Mi
  requests:
    cpu: 50m
    memory: 64Mi
securityContext:
  allowPrivilegeEscalation: false
  capabilities:
    drop:
    - ALL
  runAsNonRoot: true
  runAsUser: 1000
service:
  nodePort: 30080
  port: 80
  targetPort: 5050
  type: NodePort
serviceAccount:
  annotations: {}
  create: true
  name: ""
tolerations: []
```

### `curl http://localhost:8080`

```bash
{
  "endpoints": [
    {
      "description": "Service information",
      "method": "GET",
      "path": "/"
    },
    {
      "description": "Health check",
      "method": "GET",
      "path": "/health"
    }
  ],
  "request": {
    "client_ip": "127.0.0.1",
    "method": "GET",
    "path": "/",
    "user_agent": "curl/8.7.1"
  },
  "runtime": {
    "current_time": "2026-02-18T12:53:03.550450+00:00",
    "timezone": "UTC",
    "uptime_human": "0 hour(s), 0 minute(s)",
    "uptime_seconds": 11
  },
  "service": {
    "description": "DevOps course info service",
    "framework": "Flask",
    "name": "devops-info-service",
    "version": "1.0.0"
  },
  "system": {
    "architecture": "arm64",
    "cpu_count": 8,
    "hostname": "Scarff.local",
    "platform": "Darwin",
    "platform_version": "Darwin Kernel Version 25.2.0: Tue Nov 18 21:09:55 PST 2025; root:xnu-12377.61.12~1/RELEASE_ARM64_T8103",
    "python_version": "3.14.0"
  }
}
```

### `curl http://localhost:8080/health`

```bash
{
  "status": "healthy",
  "timestamp": "2026-02-18T12:52:58.123456Z",
  "uptime_seconds": 300
}
```



## BONUS: Library Charts

### Library chart structure

```bash
common-lib
├── Chart.yaml
└── templates
    └── _helpers
        ├── _labels.tpl
        ├── _names.tpl
        ├── _probes.tpl
        ├── _resources.tpl
        └── _security.tpl
```

### Shared library

```bash
helm dependency update info-service-chart
```

```bash
Hang tight while we grab the latest from your chart repositories...
...Successfully got an update from the "grafana" chart repository
...Successfully got an update from the "bitnami" chart repository
...Successfully got an update from the "prometheus-community" chart repository
...Successfully got an update from the "stable" chart repository
Update Complete. ⎈Happy Helming!⎈
Saving 1 charts
Deleting outdated charts
```

```bash
helm dependency update echo-app-chart
```

```bash
Hang tight while we grab the latest from your chart repositories...
...Successfully got an update from the "bitnami" chart repository
...Successfully got an update from the "prometheus-community" chart repository
...Successfully got an update from the "grafana" chart repository
...Successfully got an update from the "stable" chart repository
Update Complete. ⎈Happy Helming!⎈
Saving 1 charts
Deleting outdated charts
```

### Benefits of this approach

- **DRY** — common templates in one place
- **Consistency** — uniform labels and probes in all applications
- **Maintainability** — changes in one place are applied everywhere
- **Versioning** — library chart can be versioned separately
- **Standardization** — all applications follow the same best practices

### Terminal output showing successful deployment of both apps

```bash
helm list
```

```bash
NAME            NAMESPACE       REVISION        UPDATED                                 STATUS          CHART                   APP VERSION
info-release    default         1               2026-02-18 13:48:52 +0000 UTC           deployed        info-service-0.2.0      1.0.0
echo-release    default         1               2026-02-18 13:50:11 +0000 UTC           deployed        echo-app-0.1.0          latest
```

```bash
kubectl get pods
```

```bash
NAME                                         READY   STATUS    RESTARTS   AGE
info-release-info-service-6b4f9c5d8b-4k5jv   1/1     Running   0          5m
info-release-info-service-6b4f9c5d8b-7x8m2   1/1     Running   0          5m
info-release-info-service-6b4f9c5d8b-9h3t1   1/1     Running   0          5m
echo-release-echo-app-7d8f9c6b5c-2xq7p       1/1     Running   0          4m
echo-release-echo-app-7d8f9c6b5c-5rk9n       1/1     Running   0          4m
```
