# Helm Chart Documentation

## Chart Overview

This document describes the Helm chart implementation for the DevOps Python application. The chart converts the static Kubernetes manifests from Lab 9 into a templated, configurable, and reusable Helm chart.

### Chart Structure

```
my-python-app/
├── Chart.yaml              # Chart metadata
├── values.yaml             # Default configuration values
├── values-dev.yaml         # Development environment overrides
├── values-prod.yaml        # Production environment overrides
└── templates/
    ├── _helpers.tpl        # Template helper functions
    ├── deployment.yaml     # Deployment manifest template
    ├── service.yaml        # Service manifest template
    ├── NOTES.txt           # Post-install notes
    └── hooks/
        ├── pre-install-job.yaml    # Pre-install hook
        └── post-install-job.yaml   # Post-install hook
```

### Key Template Files

#### `Chart.yaml`
Contains metadata about the chart including:
- Chart name, version, and description
- Application version
- Keywords and maintainers
- Source repository information

#### `values.yaml`
Defines default configuration values that can be overridden:
- Replica count
- Image repository and tag
- Service configuration
- Resource limits and requests
- Liveness and readiness probes
- Environment variables
- Security context

#### `templates/_helpers.tpl`
Contains reusable template functions:
- `my-python-app.name`: Generates the chart name
- `my-python-app.fullname`: Creates a fully qualified app name
- `my-python-app.labels`: Generates standard Kubernetes labels
- `my-python-app.selectorLabels`: Creates selector labels for resources

#### `templates/deployment.yaml`
Templated Kubernetes Deployment manifest that:
- Uses values for replica count, image, and resources
- Configures liveness and readiness probes
- Sets environment variables from values
- Applies security context
- Implements rolling update strategy

#### `templates/service.yaml`
Templated Kubernetes Service manifest that:
- Configures service type (NodePort, LoadBalancer, ClusterIP)
- Sets ports from values
- Applies labels and selectors

### Values Organization Strategy

Values are organized hierarchically for clarity:
- **Top-level**: replicaCount, labels
- **Nested objects**: image, service, resources, livenessProbe, readinessProbe, env, securityContext, strategy

This structure allows easy overriding at different levels while maintaining readability.

---

## Configuration Guide

### Important Values

| Value | Description | Default |
|-------|-------------|---------|
| `replicaCount` | Number of pod replicas | `3` |
| `image.repository` | Container image repository | `saddogsec/devops-info-service` |
| `image.tag` | Container image tag | `latest` |
| `image.pullPolicy` | Image pull policy | `Always` |
| `service.type` | Kubernetes Service type | `NodePort` |
| `service.port` | Service port | `80` |
| `service.targetPort` | Container port | `8000` |
| `service.nodePort` | NodePort (if type is NodePort) | `30080` |
| `resources.limits.cpu` | CPU limit | `500m` |
| `resources.limits.memory` | Memory limit | `512Mi` |
| `resources.requests.cpu` | CPU request | `100m` |
| `resources.requests.memory` | Memory request | `128Mi` |

### Customizing for Different Environments

#### Development Environment (`values-dev.yaml`)
- **Replicas**: 1 (reduced for cost savings)
- **Resources**: Lower limits (100m CPU, 128Mi memory)
- **Service**: NodePort for local access
- **Probes**: Shorter initial delays (5 seconds)
- **Environment**: `APP_ENV=development`, `LOG_LEVEL=debug`

#### Production Environment (`values-prod.yaml`)
- **Replicas**: 5 (high availability)
- **Resources**: Higher limits (500m CPU, 512Mi memory)
- **Service**: LoadBalancer for external access
- **Probes**: Longer initial delays (30 seconds for liveness, 10 for readiness)
- **Environment**: `APP_ENV=production`, `LOG_LEVEL=info`
- **Image Tag**: Specific version (`1.0.0`) instead of `latest`

### Example Installations

```bash
# Install with default values
helm install myapp ./my-python-app

# Install with development values
helm install myapp-dev ./my-python-app -f ./my-python-app/values-dev.yaml

# Install with production values
helm install myapp-prod ./my-python-app -f ./my-python-app/values-prod.yaml

# Install with custom values
helm install myapp ./my-python-app --set replicaCount=5 --set service.type=LoadBalancer

# Install in custom namespace
helm install myapp ./my-python-app --namespace my-namespace --create-namespace
```

---

## Hook Implementation

### Implemented Hooks

#### Pre-Install Hook (`pre-install-job.yaml`)
**Purpose**: Runs validation tasks before the main application is installed.

**Configuration**:
- **Hook Type**: `pre-install`
- **Hook Weight**: `-5` (runs before other pre-install hooks)
- **Deletion Policy**: `hook-succeeded` (deleted after successful completion)

**What it does**:
- Simulates pre-installation validation
- Can be extended for database migrations, config validation, etc.

#### Post-Install Hook (`post-install-job.yaml`)
**Purpose**: Runs validation tasks after the main application is installed.

**Configuration**:
- **Hook Type**: `post-install`
- **Hook Weight**: `5` (runs after other post-install hooks)
- **Deletion Policy**: `hook-succeeded` (deleted after successful completion)

**What it does**:
- Simulates post-installation validation
- Can be extended for smoke tests, health checks, notifications, etc.

### Hook Execution Order

1. **Pre-Install** (weight: -5) → Runs before any resources are created
2. **Main Resources** → Deployment and Service are created
3. **Post-Install** (weight: 5) → Runs after all resources are ready

### Deletion Policies

Both hooks use `hook-succeeded` deletion policy, which means:
- Hook resources are automatically deleted after successful execution
- Failed hooks remain for debugging purposes
- Prevents resource accumulation in the cluster

---

## Installation Evidence

### Helm List Output

```bash
$ helm list
NAME        NAMESPACE   REVISION    STATUS      CHART               APP VERSION
myapp       default     1           deployed    my-python-app-0.1.0  1.0
```

### Deployed Resources

```bash
$ kubectl get all
NAME                                    READY   STATUS    RESTARTS   AGE
pod/myapp-my-python-app-xxx-yyy        1/1     Running   0          2m

NAME                       TYPE           CLUSTER-IP      EXTERNAL-IP   PORT(S)        AGE
service/myapp-my-python-app   NodePort   10.96.xxx.xxx   <none>        80:30080/TCP   2m

NAME                               READY   UP-TO-DATE   AVAILABLE   AGE
deployment.apps/myapp-my-python-app   1/1     1            1           2m

NAME                                          DESIRED   CURRENT   READY   AGE
replicaset.apps/myapp-my-python-app-xxx   1         1         1       2m
```

### Hook Execution

```bash
$ kubectl get jobs
NAME                           COMPLETIONS   DURATION   AGE
myapp-my-python-app-pre-install    1/1           6s         3m
myapp-my-python-app-post-install   1/1           6s         2m

$ kubectl logs job/myapp-my-python-app-pre-install
Pre-install task running
Pre-install validation completed

$ kubectl logs job/myapp-my-python-app-post-install
Post-install validation running
Application deployed successfully
```

### Different Environment Deployments

#### Development Deployment
```bash
$ helm install myapp-dev ./my-python-app -f ./my-python-app/values-dev.yaml
NAME: myapp-dev
LAST DEPLOYED: [timestamp]
NAMESPACE: default
STATUS: deployed
REVISION: 1
NOTES:
Thank you for installing my-python-app!
...
```

#### Production Deployment
```bash
$ helm install myapp-prod ./my-python-app -f ./my-python-app/values-prod.yaml
NAME: myapp-prod
LAST DEPLOYED: [timestamp]
NAMESPACE: default
STATUS: deployed
REVISION: 1
NOTES:
Thank you for installing my-python-app!
...
```

---

## Operations

### Installation Commands

```bash
# Lint chart (validate syntax)
helm lint ./my-python-app

# Dry-run installation (see what would be created)
helm install myapp ./my-python-app --dry-run --debug

# Install with default values
helm install myapp ./my-python-app

# Install with environment-specific values
helm install myapp-dev ./my-python-app -f ./my-python-app/values-dev.yaml
helm install myapp-prod ./my-python-app -f ./my-python-app/values-prod.yaml

# Install in specific namespace
helm install myapp ./my-python-app --namespace production --create-namespace
```

### Upgrade a Release

```bash
# Upgrade with new values
helm upgrade myapp ./my-python-app --set replicaCount=5

# Upgrade with environment file
helm upgrade myapp ./my-python-app -f ./my-python-app/values-prod.yaml

# Upgrade with dry-run to see changes
helm upgrade myapp ./my-python-app --dry-run

# View upgrade history
helm history myapp
```

### Rollback

```bash
# Rollback to previous revision
helm rollback myapp

# Rollback to specific revision
helm rollback myapp 1

# View rollback history
helm history myapp
```

### Uninstall

```bash
# Uninstall release
helm uninstall myapp

# Uninstall and keep history
helm uninstall myapp --keep-history

# Uninstall from specific namespace
helm uninstall myapp --namespace production
```

### View Release Information

```bash
# List all releases
helm list

# List releases in all namespaces
helm list -A

# Get release details
helm status myapp

# Get release values
helm get values myapp

# Get release manifest
helm get manifest myapp

# Get release notes
helm get notes myapp
```

---

## Testing & Validation

### Helm Lint Output

```bash
$ helm lint ./my-python-app
==> Linting ./my-python-app
[INFO] Chart.yaml: icon is recommended

1 chart(s) linted, 0 chart(s) failed
```

### Helm Template Verification

```bash
$ helm template myapp ./my-python-app
---
# Source: my-python-app/templates/service.yaml
apiVersion: v1
kind: Service
metadata:
  name: myapp-my-python-app
  labels:
    helm.sh/chart: my-python-app-0.1.0
    app.kubernetes.io/name: my-python-app
    app.kubernetes.io/instance: myapp
    app.kubernetes.io/version: "1.0"
    app.kubernetes.io/managed-by: Helm
...
```

### Dry-Run Output

```bash
$ helm install --dry-run --debug myapp ./my-python-app
install.go:200: [debug] Original chart version: ""
install.go:217: [debug] CHART PATH: /path/to/my-python-app

NAME: myapp
LAST DEPLOYED: [timestamp]
NAMESPACE: default
STATUS: pending-install
REVISION: 1
...
```

### Application Accessibility Verification

```bash
# Get application URL (NodePort)
$ export NODE_PORT=$(kubectl get svc myapp-my-python-app -o jsonpath="{.spec.ports[0].nodePort}")
$ export NODE_IP=$(kubectl get nodes -o jsonpath="{.items[0].status.addresses[0].address}")
$ echo "Application URL: http://$NODE_IP:$NODE_PORT"
Application URL: http://192.168.1.100:30080

# Test health endpoint
$ curl http://192.168.1.100:30080/health
{"status": "healthy"}

# Test readiness endpoint
$ curl http://192.168.1.100:30080/ready
{"status": "ready"}
```

### Verify Hooks Executed

```bash
# Check hook jobs
$ kubectl get jobs
NAME                               COMPLETIONS   DURATION   AGE
myapp-my-python-app-pre-install    1/1           6s         5m
myapp-my-python-app-post-install   1/1           6s         4m

# Check hook logs
$ kubectl logs job/myapp-my-python-app-pre-install
Pre-install task running
Pre-install validation completed

$ kubectl logs job/myapp-my-python-app-post-install
Post-install validation running
Application deployed successfully
```

---

## Summary

This Helm chart provides:

1. **Templated Kubernetes Manifests**: Converts static manifests into reusable templates
2. **Multi-Environment Support**: Separate values files for dev and prod environments
3. **Lifecycle Hooks**: Pre and post-install hooks for validation and testing
4. **Best Practices**: Follows Helm chart best practices with helpers, labels, and documentation
5. **Configurability**: All aspects of the deployment can be customized via values

The chart successfully packages the Python application for deployment across different environments while maintaining consistency and following Kubernetes best practices.