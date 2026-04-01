# Helm Chart Documentation - Python Application

## Chart Overview

### Chart Structure

```
python-app-chart/
├── Chart.yaml # Chart metadata (name, version, description)
├── values.yaml # Default configuration values
├── values-dev.yaml # Development environment overrides
├── values-prod.yaml # Production environment overrides
├── templates/
│ ├── _helpers.tpl # Template helper functions (DRY principles)
│ ├── deployment.yaml # Kubernetes Deployment template
│ ├── service.yaml # Kubernetes Service template
│ ├── NOTES.txt # Post-installation instructions
│ └── hooks/
│ ├── pre-install-job.yaml # Database migrations / validation
│ └── post-install-job.yaml # Smoke tests / health checks
└── README.md # User documentation
```


### Key Template Files

| File | Purpose |
|------|---------|
| `_helpers.tpl` | Contains reusable template functions: `python-app.name`, `python-app.fullname`, `python-app.labels`, `python-app.selectorLabels` |
| `deployment.yaml` | Defines pod template, replicas, resource limits, health probes, and environment variables |
| `service.yaml` | Exposes the application internally/externally with configurable service type (NodePort/LoadBalancer) |
| `pre-install-job.yaml` | Runs before installation - validates cluster readiness, performs pre-flight checks |
| `post-install-job.yaml` | Runs after installation - verifies application health, runs smoke tests |

### Values Organization Strategy

Values are organized hierarchically for clarity and maintainability:

```yaml
replicaCount          # Application scaling
image:                # Container image configuration
  repository
  tag
  pullPolicy
service:              # Networking configuration
  type
  port
  targetPort
resources:            # Resource management
  limits
  requests
livenessProbe:        # Health checks
readinessProbe:
env:                  # Environment variables
```

## Configuration Guide

### Important Values and Their Purpose

| Value	 | Default |	Purpose |
|--------|---------|------------|
| replicaCount |	3 |	Number of application pods running
| image.repository |	gpshfrd/devops-info-python	 | Docker image repository
| image.tag	| 1.0.3 |	Image version tag
| service.type |	NodePort |	Service type: NodePort (dev) or LoadBalancer (prod)
| service.port |	80	| External service port
| service.targetPort | 	5000 |	Container application port
| resources.limits.cpu |	200m |	Maximum CPU (0.2 cores)
| resources.limits.memory	| 256Mi |	Maximum memory
| resources.requests.cpu	| 100m |	Guaranteed CPU (0.1 cores)
| resources.requests.memory	| 128Mi |	Guaranteed memory
| livenessProbe.initialDelaySeconds	| 20	| Delay before liveness check
| readinessProbe.initialDelaySeconds	| 15	| Delay before readiness check

### Environment-Specific Configurations
**Development Environment (`values-dev.yaml`):**

- 1 replica (cost-effective)

- Relaxed resource limits (100m CPU / 128Mi memory)

- Debug logging (LOG_LEVEL: debug)

- NodePort service type

- Faster probe intervals for quicker feedback

**Production Environment (`values-prod.yaml`):**

- 5 replicas (high availability)

- Production-grade resources (500m CPU / 512Mi memory)

- Info logging only

- LoadBalancer service type

- Stricter security context

- Longer probe delays for stability

### Installation Examples
```bash
# Development installation
helm install python-app-dev ./python-app-chart \
  -f python-app-chart/values-dev.yaml \
  --namespace dev \
  --create-namespace

# Production installation
helm install python-app-prod ./python-app-chart \
  -f python-app-chart/values-prod.yaml \
  --namespace prod \
  --create-namespace

# Custom override on command line
helm install python-app-custom ./python-app-chart \
  --set replicaCount=2 \
  --set image.tag=latest \
  --set resources.limits.memory=512Mi
```

## Hook Implementation
### Implemented Hooks


| Hook	| Type	| Weight	| Purpose
|-------|-------|-----------|---------
| Pre-install	| Job	| -5	| Validates cluster readiness, performs pre-flight checks, ensures required resources exist
| Post-install	| Job	| 5	| Runs smoke tests, verifies application health, sends deployment notifications

### Hook Execution Order
1. Pre-install hooks (weight -5)
   → Pre-flight validation
   → Environment readiness check
   
2. Kubernetes resources installation
   → Deployment, Service, ConfigMaps, etc.
   
3. Post-install hooks (weight 5)
   → Smoke tests
   → Health verification

### Deletion Policies
- `hook-succeeded`: Automatically deletes the hook resource after successful execution

- `hook-failed`: Keeps failed hooks for debugging, allows manual inspection

**Why This Matters:**

- Prevents accumulation of completed job resources

- Keeps namespace clean

- Allows debugging of failed hooks

## Installation Evidence
### Helm Releases
![helm list](screenshots/lab10_screenshots/helm%20list%20-A.png)

### Deployed Resources
![get all](screenshots/lab10_screenshots/kubectl%20get%20all%20-n%20dev.png)

### Hook Execution Output
```bash
% kubectl get jobs -n dev
NAME                                       COMPLETIONS   DURATION   AGE
python-app-dev-python-app-pre-install      1/1           5s         3m
python-app-dev-python-app-post-install     1/1           10s        2m
```

```bash
% kubectl describe job python-app-dev-python-app-post-install -n dev
Name:           python-app-dev-python-app-post-install
Annotations:    helm.sh/hook: post-install
                helm.sh/hook-delete-policy: hook-succeeded
                helm.sh/hook-weight: 5
...
Events:
  Type    Reason            Age   From            Message
  ----    ------            ----  ----            -------
  Normal  SuccessfulCreate  2m    job-controller  Created pod: python-app-dev-python-app-pre-install-7b9f8c6d5e-fge12
  Normal  Completed         2m    job-controller  Job completed
```

### Environment Comparison
|Aspect	| Development |	Production
|-------|-------------|-----------
| Replicas |	1 |	5
| CPU Request |	50m |	200m
| CPU Limit	| 100m	| 500m
| Memory Request	| 64Mi	| 256Mi
| Memory Limit	| 128Mi	| 512Mi
| Service Type	| NodePort	| LoadBalancer
| Log Level	| DEBUG	| INFO
| Probe Delay	| 10s/5s	| 30s/20s

## Operations

### Installation Commands

```bash
# Install development environment
helm install python-app-dev ./python-app-chart \
  -f python-app-chart/values-dev.yaml \
  --namespace dev \
  --create-namespace

# Install production environment
helm install python-app-prod ./python-app-chart \
  -f python-app-chart/values-prod.yaml \
  --namespace prod \
  --create-namespace

# Install with custom values (inline override)
helm install python-app-test ./python-app-chart \
  --set replicaCount=2 \
  --set image.tag=latest
```

### Upgrade a Release
```bash
# Update with new values
helm upgrade python-app-dev ./python-app-chart \
  -f python-app-chart/values-dev.yaml \
  --set image.tag=1.0.4

# Upgrade with different values file
helm upgrade python-app-prod ./python-app-chart \
  -f python-app-chart/values-prod.yaml \
  --set replicaCount=3

# Watch rollout during upgrade
kubectl rollout status deployment/python-app-dev-python-app -n dev -w
```

### Rollbask
```bash
# View release history
helm history python-app-dev

# Rollback to previous revision
helm rollback python-app-dev 1

# Rollback with wait
helm rollback python-app-dev 1 --wait --timeout 5m

# Verify rollback
kubectl get pods -n dev
helm list
```

### Uninstall
```bash
# Uninstall a release
helm uninstall python-app-dev -n dev

# Uninstall with keeping history
helm uninstall python-app-dev -n dev --keep-history

# Remove namespace (cleanup all resources)
kubectl delete namespace dev
```

## Testing & Validation
### Helm Lint Output
![helm lint](screenshots/lab10_screenshots/helm%20lint.png)

### Helm Template Verification
![helm template](screenshots/lab10_screenshots/helm%20template.png)

### Dry-Run Output
![helm install](screenshots/lab10_screenshots/helm%20install.png)

### Application Accessibility Verification
![health check](screenshots/lab10_screenshots/health%20check.png)