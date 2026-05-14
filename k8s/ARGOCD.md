# ArgoCD GitOps Implementation

## 1. ArgoCD Setup

### Installation via Helm

```bash
# Add ArgoCD Helm repository
helm repo add argo https://argoproj.github.io/argo-helm
helm repo update

# Create dedicated namespace
kubectl create namespace argocd

# Install ArgoCD
helm install argocd argo/argo-cd --namespace argocd

# Wait for all pods to be ready
kubectl wait --for=condition=ready pod -l app.kubernetes.io/name=argocd-server \
  -n argocd --timeout=120s
```

### Installation Verification

```bash
kubectl get pods -n argocd
```

Expected output:
```
NAME                                                READY   STATUS    RESTARTS   AGE
argocd-application-controller-0                     1/1     Running   0          2m
argocd-applicationset-controller-xxx                1/1     Running   0          2m
argocd-dex-server-xxx                               1/1     Running   0          2m
argocd-notifications-controller-xxx                 1/1     Running   0          2m
argocd-redis-xxx                                    1/1     Running   0          2m
argocd-repo-server-xxx                              1/1     Running   0          2m
argocd-server-xxx                                   1/1     Running   0          2m
```

### UI Access via Port-Forward

```bash
# Start port forwarding (keep this terminal open)
kubectl port-forward svc/argocd-server -n argocd 8080:443

# Retrieve initial admin password
kubectl -n argocd get secret argocd-initial-admin-secret \
  -o jsonpath="{.data.password}" | base64 -d && echo

# Access UI at: https://localhost:8080
# Username: admin
# Password: (retrieved above)
```

### CLI Installation & Login

```bash
# Install ArgoCD CLI (Linux)
curl -sSL -o argocd-linux-amd64 \
  https://github.com/argoproj/argo-cd/releases/latest/download/argocd-linux-amd64
install -m 555 argocd-linux-amd64 /usr/local/bin/argocd

# Login via CLI
argocd login localhost:8080 --insecure
# Username: admin
# Password: (retrieved above)

# Verify connection
argocd version
argocd app list
```

---

## 2. Application Configuration

### Application Manifests

All ArgoCD Application manifests are located in `k8s/argocd/`:

| File | Environment | Namespace | Sync Policy |
|------|-------------|-----------|-------------|
| `application.yaml` | default | default | Manual |
| `application-dev.yaml` | dev | dev | Auto (selfHeal + prune) |
| `application-prod.yaml` | prod | prod | Manual |
| `applicationset.yaml` | both | dev/prod | ApplicationSet |

### Source Configuration

- **Repository:** `https://github.com/Thi1ef/DevOps-Core-Course.git`
- **Branch:** `lab13`
- **Helm chart path:** `k8s/devops-info-service`

### Destination Configuration

- **Cluster:** `https://kubernetes.default.svc` (in-cluster)
- **Namespace:** per environment (default / dev / prod)

### Deploying Applications

```bash
# Apply the default application manifest
kubectl apply -f k8s/argocd/application.yaml

# Trigger initial sync via CLI
argocd app sync python-app

# Check sync status
argocd app get python-app
```

### Values File Selection

Each application specifies which values files Helm should use:

- **Default:** `values.yaml` only
- **Dev:** `values.yaml` + `values-dev.yaml` (overrides)
- **Prod:** `values.yaml` + `values-prod.yaml` (overrides)

---

## 3. Multi-Environment Deployment

### Create Namespaces

```bash
kubectl create namespace dev
kubectl create namespace prod
```

### Apply Environment Applications

```bash
kubectl apply -f k8s/argocd/application-dev.yaml
kubectl apply -f k8s/argocd/application-prod.yaml
```

### Dev vs Prod Configuration Differences

| Parameter | Dev | Prod |
|-----------|-----|------|
| `replicaCount` | 1 | 5 |
| `image.tag` | latest | 1.0.0 |
| `service.type` | NodePort | LoadBalancer |
| `resources.limits.cpu` | 100m | 500m |
| `resources.limits.memory` | 128Mi | 512Mi |

### Sync Policy Differences

**Dev — Auto-Sync:**
```yaml
syncPolicy:
  automated:
    prune: true      # Delete resources removed from Git
    selfHeal: true   # Revert manual cluster changes to match Git
  syncOptions:
    - CreateNamespace=true
```

**Prod — Manual Sync:**
```yaml
syncPolicy:
  syncOptions:
    - CreateNamespace=true
  # No automated block = requires manual sync trigger
```

**Rationale for manual prod sync:**
- Requires explicit human approval before any change reaches production
- Allows change review and rollback planning
- Enables controlled release timing aligned with business windows
- Satisfies compliance requirements that mandate change management approval

### Namespace Separation

Each environment runs in its own Kubernetes namespace (`dev`, `prod`), providing:
- Resource isolation and independent resource quotas
- Separate RBAC permissions per environment
- Independent scaling and lifecycle management

---

## 4. Self-Healing Evidence

### Test 1: Manual Scale (Configuration Drift)

```bash
# Scale deployment manually — this creates drift vs Git state
kubectl scale deployment python-app-dev -n dev --replicas=5

# ArgoCD detects drift (within ~30s with selfHeal)
argocd app get python-app-dev
# STATUS: OutOfSync → Syncing → Synced

# Watch pods revert to Git-defined count (1 replica for dev)
kubectl get pods -n dev -w
```

**Result:** ArgoCD reverts replicas from 5 back to 1 automatically because `selfHeal: true` detects the drift from Git state and re-applies the Helm chart.

### Test 2: Pod Deletion

```bash
# Delete a pod in dev namespace
kubectl delete pod -n dev -l app.kubernetes.io/name=devops-info-service

# Watch Kubernetes recreate it immediately
kubectl get pods -n dev -w
```

**Result:** The pod is recreated by the Kubernetes ReplicaSet controller — this is **Kubernetes self-healing**, not ArgoCD. The ReplicaSet ensures the desired pod count is maintained regardless of ArgoCD.

**Key Distinction:**
- **Kubernetes self-healing:** ReplicaSet/Deployment ensures desired pod count (handles node failures, pod crashes)
- **ArgoCD self-healing:** Reverts cluster resources to match the declared Git state (handles manual `kubectl` changes, configuration drift)

### Test 3: Configuration Drift (Label Edit)

```bash
# Manually add a label to the deployment
kubectl label deployment python-app-dev -n dev test-label=manual

# Check ArgoCD diff view
argocd app diff python-app-dev

# ArgoCD detects and reverts the label within ~3 minutes
argocd app get python-app-dev
```

**Result:** ArgoCD removes the manually added label because it is not present in Git, restoring the exact state defined in the Helm chart.

### Sync Behavior Summary

| Trigger | Who handles it | Mechanism |
|---------|---------------|-----------|
| Pod crash / node failure | Kubernetes | ReplicaSet controller |
| Manual `kubectl` change (scale, label) | ArgoCD | selfHeal polls every 3 minutes |
| Git commit with new config | ArgoCD | Auto-sync on Git poll or webhook |
| Manual sync request | ArgoCD | `argocd app sync <name>` |

**ArgoCD sync interval:** By default, ArgoCD polls Git repositories every **3 minutes**. For faster response, configure a Git webhook to trigger immediate sync on push.

---

## 5. Bonus: ApplicationSet

The `k8s/argocd/applicationset.yaml` replaces the two separate Application manifests with a single template that generates both dev and prod apps.

### List Generator

```yaml
generators:
  - list:
      elements:
        - env: dev
          namespace: dev
          valuesFile: values-dev.yaml
        - env: prod
          namespace: prod
          valuesFile: values-prod.yaml
```

The List generator iterates over the explicit list of elements, substituting `{{env}}`, `{{namespace}}`, and `{{valuesFile}}` into the template for each entry.

### Apply ApplicationSet

```bash
kubectl apply -f k8s/argocd/applicationset.yaml

# Verify generated applications
argocd app list
# NAME              CLUSTER    NAMESPACE  PROJECT  STATUS  HEALTH
# python-app-dev    in-cluster dev        default  Synced  Healthy
# python-app-prod   in-cluster prod       default  Synced  Healthy
```

### ApplicationSet vs Individual Applications

| Aspect | Individual Applications | ApplicationSet |
|--------|------------------------|----------------|
| Source of truth | Multiple YAML files | Single template |
| Adding an environment | Create new YAML file | Add one list element |
| Consistency | Manual, error-prone | Guaranteed by template |
| Scalability | Grows linearly with envs | Single manifest |
| Best for | 1-2 static environments | Many envs, multi-cluster |

### When to Use Which Generator

| Generator | Use Case |
|-----------|----------|
| **List** | Fixed set of environments/clusters with known parameters |
| **Cluster** | Deploy same app to all registered ArgoCD clusters |
| **Git** | Auto-discover apps from directory structure in repo |
| **Matrix** | Combine two generators (e.g., all apps × all clusters) |
| **Merge** | Override generator values with per-element customization |
