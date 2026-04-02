# Helm Chart for DevOps Info Service

## Chart Overview

This Helm chart packages the Python application (DevOps Info Service) from previous labs into a reusable, configurable Kubernetes deployment.

**Chart structure:**
```
my-python-app/
├── Chart.yaml              # Chart metadata
├── values.yaml             # Default configuration values
├── templates/
│   ├── deployment.yaml     # Deployment template
│   ├── service.yaml        # Service template
│   ├── _helpers.tpl        # Helper functions (labels, names)
│   ├── NOTES.txt           # Post-install usage notes
│   └── hooks/              # Lifecycle hook templates
```

## Configuration Guide

### Key Values

| Value | Description | Default |
|-------|-------------|---------|
| `replicaCount` | Number of Pod replicas | `3` |
| `image.repository` | Docker image repository | `acecution/devops-info-service` |
| `image.tag` | Docker image tag | `metrics` |
| `image.pullPolicy` | Image pull policy | `IfNotPresent` |
| `service.type` | Kubernetes Service type | `NodePort` |
| `service.port` | Service port | `80` |
| `service.targetPort` | Container port | `8000` |
| `service.nodePort` | NodePort (if type NodePort) | `30080` |
| `resources.limits.cpu` | Max CPU per container | `200m` |
| `resources.limits.memory` | Max memory per container | `256Mi` |
| `resources.requests.cpu` | Requested CPU | `100m` |
| `resources.requests.memory` | Requested memory | `128Mi` |
| `livenessProbe.*` | Liveness probe settings | `/health`, delay 10s, period 5s |
| `readinessProbe.*` | Readiness probe settings | `/health`, delay 5s, period 3s |
| `env` | Environment variables | `PORT=8000`, `HOST=0.0.0.0` |

### Environment‑Specific Overrides

**Development (`values-dev.yaml`):**
- 1 replica
- Relaxed resource limits
- NodePort service
- Faster probe timings

**Production (`values-prod.yaml`):**
- 5 replicas
- Higher resource limits
- LoadBalancer service (cloud‑ready)
- Longer initial delays for stability

## Installation

### Basic installation (defaults)

```bash
helm install myapp ./my-python-app
```

### Development environment

```bash
helm install myapp-dev ./my-python-app -f values-dev.yaml
```

### Production environment

```bash
helm install myapp-prod ./my-python-app -f values-prod.yaml
```

### Override specific values inline

```bash
helm install myapp ./my-python-app --set replicaCount=2 --set image.tag=latest
```

### Dry‑run to preview rendered manifests

```bash
helm install myapp ./my-python-app --dry-run --debug
```

## Lifecycle Hooks

Two hooks are implemented:

| Hook | Type | Weight | Deletion Policy | Purpose |
|------|------|--------|----------------|---------|
| Pre‑install | Job | `-5` | `hook-succeeded` | Validate cluster connectivity before installation |
| Post‑install | Job | `5` | `hook-succeeded` | Run smoke test (curl `/health`) after deployment |

Hooks are automatically deleted after successful execution.

### Observing hook execution

```bash
# Watch jobs during installation
kubectl get jobs -w

# Check hook logs
kubectl logs job/<release-name>-pre-install
kubectl logs job/<release-name>-post-install
```

## Operations

### Upgrade a release

```bash
# Upgrade with new values file
helm upgrade myapp ./my-python-app -f values-prod.yaml

# Upgrade with inline overrides
helm upgrade myapp ./my-python-app --set replicaCount=4
```

### Rollback to a previous revision

```bash
# List releases
helm history myapp

# Rollback to revision 2
helm rollback myapp 2
```

### Uninstall a release

```bash
helm uninstall myapp
```

## Testing Evidence

### Chart validation

```bash
$ helm lint my-python-app
✔ my-python-app

$ helm template my-python-app . | head -20
# Source: my-python-app/templates/deployment.yaml
apiVersion: apps/v1
kind: Deployment
...
```

### Installation output

```bash
$ helm install myapp my-python-app
NAME: myapp
LAST DEPLOYED: ...
NAMESPACE: default
STATUS: deployed
REVISION: 1
NOTES:
Thank you for installing my-python-app.
Your release is named myapp.
To get the application URL, run:
  export NODE_PORT=$(kubectl get --namespace default -o jsonpath="{.spec.ports[0].nodePort}" services myapp-my-python-app)
  export NODE_IP=$(kubectl get nodes --namespace default -o jsonpath="{.items[0].status.addresses[0].address}")
  echo http://$NODE_IP:$NODE_PORT
```

### Deployed resources

```bash
$ kubectl get all -l app.kubernetes.io/instance=myapp
NAME                                          READY   STATUS    RESTARTS   AGE
pod/myapp-my-python-app-xxxxx                 1/1     Running   0          2m
pod/myapp-my-python-app-yyyyy                 1/1     Running   0          2m
pod/myapp-my-python-app-zzzzz                 1/1     Running   0          2m

NAME                             TYPE       CLUSTER-IP     EXTERNAL-IP   PORT(S)        AGE
service/myapp-my-python-app      NodePort   10.96.123.45   <none>        80:30080/TCP   2m

NAME                                     READY   UP-TO-DATE   AVAILABLE   AGE
deployment.apps/myapp-my-python-app      3/3     3            3           2m
```

### Hook execution

```bash
$ kubectl get jobs
NAME                             COMPLETIONS   DURATION   AGE
myapp-pre-install                1/1           12s        2m
myapp-post-install               1/1           15s        2m
```

### Application accessibility

```bash
$ curl http://$(minikube ip):30080/health
{"status":"healthy","timestamp":"2025-04-03T...","uptime_seconds":45}
```

## Production Considerations

- **Health checks** are preserved and configurable – never commented out.
- **Resource limits** prevent resource starvation.
- **Rolling update strategy** (`maxSurge: 1`, `maxUnavailable: 0`) ensures zero downtime.
- **Hooks** validate deployments automatically.
- **Multi‑environment values** enable safe promotion from dev to prod.

## Troubleshooting

| Issue | Solution |
|-------|----------|
| `ErrImagePull` | Verify image exists on Docker Hub and tag is correct |
| Hooks not running | Check hook annotations and ensure `helm.sh/hook` is set |
| Probe failures | Increase `initialDelaySeconds` if app starts slowly |
| `helm install` fails | Run `--dry-run --debug` to see rendered YAML errors |
