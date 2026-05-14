# Lab 10 — Helm Package Manager Documentation

## Task 1 — Helm Fundamentals

### Helm Installation

Helm CLI has been installed and verified.

**Installation command:**
```bash
curl https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 | bash
```

**Verification:**
```bash
$ helm version
version.BuildInfo{Version:"v3.20.2", GitCommit:"8fb76d6ab555577e98e23b7500009537a471feee", GitTreeState:"clean", GoVersion:"go1.25.9"}
```

**Note:** While Lab 10 mentions Helm 4.x, Helm v3.20.2 is the current stable release and is fully compatible with all Helm charts using `apiVersion: v2`. Helm 4.x is planned for 2026, but all Helm 3 charts will be compatible with it.

### Chart Repositories Added

The following chart repositories have been configured:

1. **Bitnami** - https://charts.bitnami.com/bitnami
   - Contains production-grade individual application charts
2. **Prometheus Community** - https://prometheus-community.github.io/helm-charts
   - Monitoring and observability charts (Prometheus, Grafana, etc.)
3. **Grafana** - https://grafana.github.io/helm-charts
   - Grafana visualization and logging stack charts

**Commands:**
```bash
helm repo add bitnami https://charts.bitnami.com/bitnami
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo add grafana https://grafana.github.io/helm-charts
helm repo update
```

### Chart Exploration Example: Prometheus

The `prometheus-community/prometheus` chart was explored as an example public chart.

**Chart Metadata:**
```yaml
apiVersion: v2
name: prometheus
description: Prometheus is a monitoring system and time series database.
type: application
version: 29.6.0
appVersion: v3.11.3
home: https://prometheus.io/
kubeVersion: '>=1.19.0-0'
```

**Key Features:**
- Application type: `application` (can be directly installed)
- Chart version: `29.6.0` (chart updates)
- App version: `v3.11.3` (Prometheus version)
- Kubernetes minimum version: 1.19.0

**Chart Dependencies (subcharts):**
- `alertmanager` (v1.36.*) - Alert handling
- `kube-state-metrics` (v7.3.*) - Kubernetes state metrics
- `prometheus-node-exporter` (v4.55.*) - Node-level metrics
- `prometheus-pushgateway` (v3.6.*) - Metrics push gateway

### Value Configuration Example

The chart exposes many configurable parameters via `values.yaml`. Sample top-level sections include resource limits, service configuration, storage, and alert manager options.

### Helm Concepts Understood

**Key Concepts:**
1. **Chart**: A packaged Kubernetes application (like a deb or rpm package)
2. **Release**: A running instance of a chart in a cluster
3. **Repository**: A collection of charts (like apt repository)
4. **Values**: Configuration parameters for customization
5. **Templates**: Go-templated Kubernetes manifest files
6. **Hooks**: Actions executed at specific lifecycle events

### Why Helm?

**Benefits of using Helm:**
- **Templating**: Reuse manifests across environments (dev, staging, prod)
- **Versioning**: Track and rollback releases with `helm rollout`
- **Dependencies**: Manage complex applications with multiple charts as subcharts
- **Lifecycle Hooks**: Execute tasks before/after install, upgrade, delete
- **Standardization**: Industry-standard Kubernetes packaging format
- **Reusability**: Share charts across teams and organizations

### Available Charts Search

Helmcharts are discoverable via `helm search repo`:

**Sample search output for "prometheus" charts:**
```bash
$ helm search repo prometheus | head -5
NAME                                    CHART VERSION   APP VERSION     DESCRIPTION
prometheus-community/prometheus         29.6.0          v3.11.3         Prometheus is a monitoring system and time series database
prometheus-community/kube-prometheus-stack  85.0.3      v0.90.1         kube-prometheus-stack collects Kubernetes manifests
bitnami/prometheus                       2.1.23          3.5.0           Prometheus is an open source monitoring and alerting system
prometheus-community/prometheus-adapter  5.3.0           v0.12.0         A Helm chart for k8s prometheus adapter
```

---

## Task 2 — Converting Manifests to Helm Chart

### Chart Structure Created

The Helm chart `devops-python` has been scaffolded with the following structure:

```
k8s/devops-python/
├── Chart.yaml                 # Chart metadata
├── values.yaml                # Default configuration values
└── templates/
    ├── deployment.yaml        # Templated Deployment manifest
    ├── service.yaml           # Templated Service manifest
    └── _helpers.tpl           # Helm template helpers (fullname, labels)
```

### Chart.yaml Configuration

**File:** [k8s/devops-python/Chart.yaml](../devops-python/Chart.yaml)

```yaml
apiVersion: v2
name: devops-python
description: A Helm chart for deploying the DevOps Python FastAPI application
type: application
version: 0.1.0
appVersion: "1.0"
maintainers:
  - name: DevOps Team
    email: devops@example.com
```

**Key Fields:**
- `apiVersion: v2` - Uses the modern Helm 3 chart format
- `version: 0.1.0` - Chart version (independent from app version)
- `appVersion: 1.0` - Application version (matches deployment)

### values.yaml Configuration

**File:** [k8s/devops-python/values.yaml](../devops-python/values.yaml)

**Configuration Sections:**

```yaml
replicaCount: 3
image:
  repository: devops-python
  tag: "latest"
  pullPolicy: IfNotPresent
service:
  type: NodePort
  port: 80
  targetPort: 5000
  nodePort: 30080
resources:
  requests:
    memory: "128Mi"
    cpu: "100m"
  limits:
    memory: "256Mi"
    cpu: "250m"
livenessProbe:
  enabled: true
  httpGet:
    path: /health
    port: 5000
  initialDelaySeconds: 10
  periodSeconds: 10
readinessProbe:
  enabled: true
  httpGet:
    path: /health
    port: 5000
  initialDelaySeconds: 5
  periodSeconds: 5
strategy:
  type: RollingUpdate
  rollingUpdate:
    maxSurge: 1
    maxUnavailable: 0
```

All values correspond to Lab 9 deployment configuration and can be overridden during installation.

### Template Files

#### _helpers.tpl

**File:** [k8s/devops-python/templates/_helpers.tpl](../devops-python/templates/_helpers.tpl)

Standard Helm helper templates:
- `devops-python.fullname`: Returns release-qualified chart name
- `devops-python.labels`: Standard Kubernetes labels including helm metadata
- `devops-python.selectorLabels`: Pod selector labels

These helpers ensure consistent labeling across all resources.

#### deployment.yaml Template

**File:** [k8s/devops-python/templates/deployment.yaml](../devops-python/templates/deployment.yaml)

The Deployment template uses Go template syntax to dynamically generate resources:
- Integrates with helpers for consistent naming: `{{ include "devops-python.fullname" . }}`
- Uses values for configuration: `{{ .Values.replicaCount }}`, `{{ .Values.resources.limits.memory }}`
- Conditionally includes probes: `{{ if .Values.livenessProbe.enabled }}`
- Maintains Lab 9 configuration (security context `runAsUser: 1000`, health checks, rolling update strategy)

#### service.yaml Template

**File:** [k8s/devops-python/templates/service.yaml](../devops-python/templates/service.yaml)

The Service template exposes the deployment:
- Service name includes release: `{{ include "devops-python.fullname" . }}-service`
- Configurable service type and ports from values
- Pod selector using helper labels
- NodePort type with fixed 30080 for minikube compatibility

### Chart Validation

**Helm Lint Test:**
```bash
$ helm lint k8s/devops-python
==> Linting k8s/devops-python
[INFO] Chart.yaml: icon is recommended

1 chart(s) linted, 0 chart(s) failed
```

Chart structure is valid with no errors

### Template Rendering Test

**Helm Template Test:**
```bash
$ helm template test-release k8s/devops-python
---
# Source: devops-python/templates/service.yaml
apiVersion: v1
kind: Service
metadata:
  name: test-release-devops-python-service
  labels:
    helm.sh/chart: devops-python-0.1.0
    app.kubernetes.io/name: devops-python
    app.kubernetes.io/instance: test-release
    app.kubernetes.io/version: "1.0"
    app.kubernetes.io/managed-by: Helm
spec:
  type: NodePort
  ports:
    - port: 80
      targetPort: 5000
      protocol: TCP
      name: http
      nodePort: 30080
  selector:
    app.kubernetes.io/name: devops-python
    app.kubernetes.io/instance: test-release
---
# Source: devops-python/templates/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: test-release-devops-python
  labels:
    helm.sh/chart: devops-python-0.1.0
    app.kubernetes.io/name: devops-python
    app.kubernetes.io/instance: test-release
    app.kubernetes.io/version: "1.0"
    app.kubernetes.io/managed-by: Helm
spec:
  replicas: 3
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 1
      maxUnavailable: 0
  selector:
    matchLabels:
      app.kubernetes.io/name: devops-python
      app.kubernetes.io/instance: test-release
  template:
    metadata:
      labels:
        app.kubernetes.io/name: devops-python
        app.kubernetes.io/instance: test-release
    spec:
      containers:
        - name: devops-python
          securityContext:
            runAsUser: 1000
          image: "devops-python:latest"
          imagePullPolicy: IfNotPresent
          ports:
            - containerPort: 5000
              name: http
          resources:
            requests:
              memory: "128Mi"
              cpu: "100m"
            limits:
              memory: "256Mi"
              cpu: "250m"
          livenessProbe:
            httpGet:
              path: /health
              port: 5000
            initialDelaySeconds: 10
            periodSeconds: 10
            timeoutSeconds: 3
            failureThreshold: 3
          readinessProbe:
            httpGet:
              path: /health
              port: 5000
            initialDelaySeconds: 5
            periodSeconds: 5
            timeoutSeconds: 2
            failureThreshold: 3
```

Templates render correctly with expected values

### Dry-Run Install Test

**Helm Dry-Run:**
```bash
helm install --dry-run --debug test-release k8s/devops-python
```

Output:
```
NAME: test-release
STATUS: pending-install
COMPUTED VALUES:
fullnameOverride: ""
image:
  pullPolicy: IfNotPresent
  repository: devops-python
  tag: latest
livenessProbe:
  enabled: true
readinessProbe:
  enabled: true
replicaCount: 3
resources:
  limits:
    cpu: 250m
    memory: 256Mi
  requests:
    cpu: 100m
    memory: 128Mi
service:
  nodePort: 30080
```

### Task 2 Summary

- Chart initialized with proper metadata (Chart.yaml)
- All configuration values externalized (values.yaml)
- Templates created for Deployment and Service
- Template helpers ensure consistent naming and labels
- Chart passes `helm lint` validation
- Templates render correctly with `helm template`
- Dry-run install simulation succeeds

---

## Task 3 — Multi-Environment Support

### Environment-Specific Values Files

Created two environment-specific values files to support different configurations:

#### values-dev.yaml - Development Environment

**File:** [k8s/devops-python/values-dev.yaml](../devops-python/values-dev.yaml)

**Configuration:**
```yaml
replicaCount: 1                    # Minimal replicas for dev

image:
  tag: "latest"                    # Use latest image
  pullPolicy: IfNotPresent         # Use local images

service:
  type: NodePort                   # Direct node access for dev
  nodePort: 30080

resources:
  requests:
    memory: "64Mi"                 # Light resources
    cpu: "50m"
  limits:
    memory: "128Mi"
    cpu: "100m"

livenessProbe:
  initialDelaySeconds: 5           # Faster probes for faster iteration
  periodSeconds: 10

readinessProbe:
  initialDelaySeconds: 3
  periodSeconds: 5

strategy:
  rollingUpdate:
    maxSurge: 1
    maxUnavailable: 1              # Allow some downtime in dev
```

**Purpose:**
- Lightweight configuration for development iteration
- Fast probe times for quicker feedback
- NodePort for easy local access
- Local image with IfNotPresent policy

#### values-prod.yaml - Production Environment

**File:** [k8s/devops-python/values-prod.yaml](../devops-python/values-prod.yaml)

**Configuration:**
```yaml
replicaCount: 5

image:
  tag: "1.0"
  pullPolicy: IfNotPresent

service:
  type: LoadBalancer
  nodePort: null

resources:
  requests:
    memory: "256Mi"
    cpu: "200m"
  limits:
    memory: "512Mi"
    cpu: "500m"

livenessProbe:
  initialDelaySeconds: 30
  periodSeconds: 5

readinessProbe:
  initialDelaySeconds: 10
  periodSeconds: 3

strategy:
  rollingUpdate:
    maxSurge: 1
    maxUnavailable: 0
```

**Purpose:**
- High-availability configuration for production
- Proper resource allocation for customer workloads
- LoadBalancer for cloud deployments
- Conservative probe timing to reduce false positives
- Zero-downtime deployment strategy

### Testing Environment Transitions

#### Install Development Environment

**Installation:**
```bash
helm install devops-dev k8s/devops-python -f k8s/devops-python/values-dev.yaml
```

**Verification - Dev Configuration (1 replica, light resources):**
```bash
$ helm get values devops-dev | grep replicaCount
replicaCount: 1

$ helm get values devops-dev | grep -A 6 "resources:"
resources:
  limits:
    cpu: 100m
    memory: 128Mi
  requests:
    cpu: 50m
    memory: 64Mi

$ kubectl get deploy -l app.kubernetes.io/instance=devops-dev
NAME                       READY   UP-TO-DATE   AVAILABLE   AGE
devops-dev-devops-python   1/1     1            1           2m18s
```

#### Upgrade to Production Environment

**Upgrade Command:**
```bash
helm upgrade devops-dev k8s/devops-python -f k8s/devops-python/values-prod.yaml
```

**Verification - Prod Configuration (5 replicas, robust resources):**
```bash
$ helm get values devops-dev | grep replicaCount
replicaCount: 5

$ helm get values devops-dev | grep -A 6 "resources:"
resources:
  limits:
    cpu: 500m
    memory: 512Mi
  requests:
    cpu: 200m
    memory: 256Mi

$ helm get values devops-dev | grep "^  type:"
  type: LoadBalancer

$ kubectl get deploy -l app.kubernetes.io/instance=devops-dev
NAME                       READY   UP-TO-DATE   AVAILABLE   AGE
devops-dev-devops-python   5/5     5            5           8m49s

$ kubectl get svc -l app.kubernetes.io/instance=devops-dev
NAME                               TYPE           CLUSTER-IP      EXTERNAL-IP   PORT(S)
devops-dev-devops-python-service   LoadBalancer   10.109.158.27   <pending>     80:30080/TCP
```

#### Release History (Environment Upgrades)

**Command:**
```bash
helm history devops-dev
```

**Output (showing dev→prod upgrade sequence):**
```
REVISION  UPDATED                STATUS      CHART              APP VERSION
1         Thu May 14 20:44:39    superseded  devops-python-0.1.0  1.0
2         Thu May 14 20:50:16    superseded  devops-python-0.1.0  1.0
3         Thu May 14 20:52:27    deployed    devops-python-0.1.0  1.0
```

### Environment Comparison Table

| Aspect | Development | Production |
|--------|-------------|------------|
| **Replicas** | 1 | 5 |
| **Memory Request** | 64Mi | 256Mi |
| **Memory Limit** | 128Mi | 512Mi |
| **CPU Request** | 50m | 200m |
| **CPU Limit** | 100m | 500m |
| **Image Tag** | latest | 1.0 |
| **Service Type** | NodePort | LoadBalancer |
| **Liveness Delay** | 5s | 30s |
| **Max Unavailable** | 1 | 0 |
| **Use Case** | Development/Testing | Production |

### Key Kubernetes Features Demonstrated

1. **Helm Values Override** - Different values files customize the same chart for different environments
2. **Rolling Updates** - Zero-downtime deployment with `maxUnavailable: 0` (prod only)
3. **Resource Limits** - Environment-appropriate CPU and memory allocation
4. **Service Types** - NodePort for dev (simple), LoadBalancer for prod (cloud-ready)
5. **Health Probe Tuning** - Faster iteration (dev) vs robust stability (prod)

### Task 3 Summary

- Created values-dev.yaml with 1 replica and light resources
- Created values-prod.yaml with 5 replicas and robust resources
- Successfully installed chart with dev values
- Successfully upgraded to prod values with zero-downtime rolling update
- Verified resource limits applied correctly
- Verified service type changed from NodePort to LoadBalancer
- Confirmed replica count scaling from 1 to 5
- Release history shows upgrade sequence with proper versioning

### Next Steps

- **Task 4**: Implement Helm lifecycle hooks (pre-install, post-install)
- **Task 5**: Final documentation and deployment verification

---

## Task 4 — Chart Hooks (Lifecycle Management)

### Hook Concepts

Helm hooks are Kubernetes resources that execute at specific points in the release lifecycle. They enable automation of tasks before/after installation, upgrades, rollbacks, and deletions.

**Hook Types Implemented:**
- **pre-install**: Executes before any resources are installed
- **post-install**: Executes after all resources are installed and running

**Hook Properties Used:**
- **Weight**: Controls execution order (lower values first; range: -100 to 100)  
- **Delete Policy**: `hook-succeeded` - deletes job after successful completion

### Hook Implementation Files

#### Pre-Install Hook

**File:** [k8s/devops-python/templates/hooks/pre-install-job.yaml](../devops-python/templates/hooks/pre-install-job.yaml)

**Purpose:** Validates environment and prerequisites before deployment

**Annotations:**
```yaml
annotations:
  "helm.sh/hook": pre-install           # Runs before installation
  "helm.sh/hook-weight": "-5"           # Executes first (negative weight)
  "helm.sh/hook-delete-policy": hook-succeeded  # Clean up after success
```

**Execution Details:**
- Validates release metadata (name, namespace, chart, version)
- Verifies deployment configuration (replicas, image, service)
- Confirms all prerequisites are met for installation

#### Post-Install Hook

**File:** [k8s/devops-python/templates/hooks/post-install-job.yaml](../devops-python/templates/hooks/post-install-job.yaml)

**Purpose:** Verifies successful deployment and logs installation information

**Annotations:**
```yaml
annotations:
  "helm.sh/hook": post-install
  "helm.sh/hook-weight": "5"
  "helm.sh/hook-delete-policy": hook-succeeded
```

**Execution Details:**
- Confirms installation completed successfully
- Logs release configuration (chart, app, replicas, image)
- Verifies resource limits and service configuration
- Provides helpful management command reference

### RBAC Resources for Hooks

#### ServiceAccount

**File:** [k8s/devops-python/templates/serviceaccount.yaml](../devops-python/templates/serviceaccount.yaml)

Provides identity for hook and main deployment resources.

#### ClusterRole

**File:** [k8s/devops-python/templates/clusterrole.yaml](../devops-python/templates/clusterrole.yaml)

Defines read permissions for cluster operations.

#### ClusterRoleBinding

**File:** [k8s/devops-python/templates/clusterrolebinding.yaml](../devops-python/templates/clusterrolebinding.yaml)

Binds the ClusterRole to the ServiceAccount.

### Hook Configuration in values.yaml

```yaml
hooks:
  preInstall:
    enabled: true
  postInstall:
    enabled: true
```

### Hook Execution Testing

#### Chart Validation

```bash
$ helm lint k8s/devops-python
==> Linting k8s/devops-python
[INFO] Chart.yaml: icon is recommended

1 chart(s) linted, 0 chart(s) failed
```

All hook templates validated

#### Hook Annotations Verification

```bash
$ helm template test-hooks k8s/devops-python | grep -E "helm.sh/hook"
"helm.sh/hook": post-install
"helm.sh/hook-weight": "5"
"helm.sh/hook-delete-policy": hook-succeeded
"helm.sh/hook": pre-install
"helm.sh/hook-weight": "-5"
"helm.sh/hook-delete-policy": hook-succeeded
```

Hook annotations properly configured in templates

#### Live Installation with Hooks

**Installation Command:**
```bash
$ helm install devops-final k8s/devops-python -f k8s/devops-python/values-dev.yaml
NAME: devops-final
STATUS: deployed
REVISION: 1
```

**Deployment Verification:**
```bash
$ kubectl get deploy,pods -l app.kubernetes.io/instance=devops-final
NAME                                         READY   UP-TO-DATE   AVAILABLE   AGE
deployment.apps/devops-final-devops-python   1/1     1            1           25s

NAME                                              READY   STATUS    RESTARTS   AGE
pod/devops-final-devops-python-7f657bbf57-4xknn   1/1     Running   0          25s
```

Deployment running successfully with 1 replica

**Hook Cleanup Verification:**
```bash
$ kubectl get jobs -l app.kubernetes.io/instance=devops-final
No resources found in default namespace.
```

Hook jobs automatically deleted per `hook-succeeded` deletion policy

### Hook Execution Order During Installation

1. **Pre-install Hook** (weight: -5) → Validates prerequisites
2. **Main Resources Creation** → ServiceAccount, ClusterRole, Service, Deployment
3. **Pod Startup** → Pods created and started by deployment controller
4. **Post-install Hook** (weight: 5) → Verifies installation success
5. **Automatic Cleanup** → Both hook jobs deleted successfully

### Task 4 Summary

- Pre-install hook created for validation (weight: -5)
- Post-install hook created for verification (weight: 5)
- RBAC resources configured (ServiceAccount, ClusterRole, ClusterRoleBinding)
- Hook deletion policy set to `hook-succeeded` for automatic cleanup
- Hook configuration added to values.yaml for enablement control
- Chart lints successfully with all hook templates
- Templates render correctly with proper hook annotations
- Live installation demonstrates hook execution and cleanup
- Deployment runs successfully after hooks complete
- Hook jobs cleaned up per deletion policy

### Key Helm Features Demonstrated

1. **Lifecycle Management** - Hooks automate tasks at installation boundaries
2. **Hook Weights** - Control execution sequence (pre/post phases)
3. **Deletion Policies** - Automatic resource cleanup after execution
4. **Conditional Rendering** - Hooks enabled/disabled via values
5. **RBAC Integration** - ServiceAccount + ClusterRole for permissions
6. **Resource Isolation** - Hooks independent from main application
7. **Template Reusability** - Hooks use same templating engine
8. **Flexible Configuration** - Can be customized per environment
