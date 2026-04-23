# Lab 13 — GitOps with ArgoCD

## 1. ArgoCD Setup

### Installation via Helm

```bash
helm repo add argo https://argoproj.github.io/argo-helm
helm repo update
kubectl create namespace argocd
helm install argocd argo/argo-cd --namespace argocd
kubectl wait --for=condition=ready pod -l app.kubernetes.io/name=argocd-server -n argocd --timeout=120s
```

### Verification

```bash
kubectl get pods -n argocd
```

All pods reach `Running` status: argocd-server, argocd-repo-server, argocd-application-controller, argocd-dex-server, argocd-redis.

### UI Access

Port-forward the ArgoCD server (run in a separate terminal and keep it open):

```bash
kubectl port-forward svc/argocd-server -n argocd 8080:443
```

Retrieve the initial admin password:

```bash
kubectl -n argocd get secret argocd-initial-admin-secret \
  -o jsonpath="{.data.password}" | base64 -d && echo
```

Open `https://localhost:8080`, login with `admin` and the password above.

### CLI Installation & Login

```bash
brew install argocd
argocd login localhost:8080 --insecure
# enter: admin / <password from above>
argocd app list
```

---

## 2. Application Configuration

### Manifests

All ArgoCD Application manifests live in `k8s/argocd/`:

| File | Description |
|------|-------------|
| `application.yaml` | Default app in `default` namespace, manual sync |
| `application-dev.yaml` | Dev env in `dev` namespace, **auto-sync + selfHeal** |
| `application-prod.yaml` | Prod env in `prod` namespace, manual sync |
| `applicationset.yaml` | Bonus: generates dev+prod apps from a single template |

### Source Configuration

- **repoURL:** `https://github.com/Arino4kaMyr/DevOps-Core-Course.git`
- **targetRevision:** `lab13`
- **path:** `k8s/devops-python-chart`
- **helm.valueFiles:** base `values.yaml` merged with environment-specific overrides

### Deploy

```bash
kubectl apply -f k8s/argocd/application.yaml
argocd app sync python-app
argocd app get python-app
```

---

## 3. Multi-Environment Deployment

### Namespaces

```bash
kubectl create namespace dev
kubectl create namespace prod
```

### Dev vs Prod Configuration Differences

| Parameter | Dev | Prod |
|-----------|-----|------|
| `replicaCount` | 1 | 3 |
| `image.tag` | latest | 1.0.0 (pinned) |
| `image.pullPolicy` | Never | IfNotPresent |
| `resources.requests.cpu` | 50m | 200m |
| `resources.requests.memory` | 64Mi | 256Mi |
| `service.type` | NodePort | LoadBalancer |
| `ingress.enabled` | false | true |
| `env.debug` | True | False |

### Sync Policy Differences

**Dev** uses `automated` sync with `prune: true` and `selfHeal: true`:
- Any change pushed to Git is automatically applied to the cluster within 3 minutes.
- Manual changes to cluster resources are automatically reverted.
- Resources removed from Git are pruned from the cluster.

**Prod** has no `automated` block — sync is **manual**:
- A human must explicitly trigger a sync via UI or CLI.
- This ensures changes are reviewed before reaching production, supports controlled release timing, and satisfies compliance requirements.

### Deploy Both Environments

```bash
kubectl apply -f k8s/argocd/application-dev.yaml
kubectl apply -f k8s/argocd/application-prod.yaml

# Verify
kubectl get pods -n dev
kubectl get pods -n prod
argocd app list
```

---

## 4. Self-Healing Evidence

### Test 1 — Manual Scale (Dev)

```bash
# Before: check current replicas
kubectl get deployment -n dev
# NAME         READY   UP-TO-DATE   AVAILABLE
# python-app   1/1     1            1

# Manually scale to 5
kubectl scale deployment python-app -n dev --replicas=5
# Immediately after:
kubectl get pods -n dev
# NAME                          READY   STATUS    RESTARTS
# python-app-xxx-yyy            1/1     Running   0
# python-app-xxx-zzz            1/1     Running   0
# ... (5 pods total)

# ArgoCD detects drift and reverts within ~3 minutes:
kubectl get pods -n dev
# NAME                          READY   STATUS    RESTARTS
# python-app-xxx-yyy            1/1     Running   0
# (back to 1 pod — matches Git)
```

**Behavior:** ArgoCD polls Git every 3 minutes. When `selfHeal: true`, it compares the live cluster state with the desired state in Git. Since Git defines `replicaCount: 1` for dev, ArgoCD reverts the deployment to 1 replica automatically.

### Test 2 — Pod Deletion (Dev)

```bash
kubectl delete pod -n dev -l app.kubernetes.io/name=python-app

# Kubernetes immediately recreates the pod:
kubectl get pods -n dev -w
# NAME                          READY   STATUS              RESTARTS
# python-app-xxx-new            0/1     ContainerCreating   0
# python-app-xxx-new            1/1     Running             0
```

**Behavior:** This is **Kubernetes self-healing**, not ArgoCD. The Deployment's ReplicaSet controller ensures the desired pod count is always maintained. ArgoCD is not involved — no sync event is triggered.

### Test 3 — Configuration Drift

```bash
# Add a label manually to the deployment
kubectl label deployment python-app -n dev test-label=manual

# ArgoCD detects the label is not in Git:
argocd app diff python-app-dev
# shows the extra label as a diff

# With selfHeal=true, ArgoCD removes the label within ~3 minutes
# Verify the label is gone:
kubectl get deployment python-app -n dev --show-labels
```

### When ArgoCD Syncs vs When Kubernetes Heals

| Trigger | Handler | Example |
|---------|---------|---------|
| Pod crash / deletion | Kubernetes (ReplicaSet) | Pod recreated immediately |
| Cluster state differs from Git | ArgoCD (selfHeal) | Manual scale/label reverted |
| Git commit pushed | ArgoCD (auto-sync) | New image deployed |
| Manual `argocd app sync` | ArgoCD | Immediate reconciliation |

**Default sync interval:** ArgoCD polls Git every **3 minutes**. For faster response, configure a Git webhook to push notifications to ArgoCD immediately on commit.

---

## 5. Screenshots

> Screenshots are taken during the live demo session.

- ArgoCD UI — both `python-app-dev` and `python-app-prod` applications listed
- Sync status: `Synced` / `Healthy` for dev; `OutOfSync` detected after manual scale
- Application details view showing resource tree (Deployment, Service, Pods)
- Diff view showing drift after manual label addition

---

## Bonus — ApplicationSet

### Manifest

See `k8s/argocd/applicationset.yaml`.

The **List generator** defines two elements (`dev` and `prod`) with environment-specific parameters. The template uses `{{env}}`, `{{namespace}}`, and `{{valuesFile}}` placeholders to generate two separate Application resources from a single definition.

### Benefits of ApplicationSet over Individual Applications

| Aspect | Individual Applications | ApplicationSet |
|--------|------------------------|----------------|
| Scalability | One file per app/env | Single template for N environments |
| Consistency | Risk of copy-paste drift | Template ensures uniformity |
| New environment | Create new file manually | Add one list element |
| DRY principle | Repeated boilerplate | Parameterized template |

### When to Use Which Generator

| Generator | Use Case |
|-----------|----------|
| **List** | Fixed set of environments/clusters known at design time |
| **Cluster** | Deploy the same app to multiple registered clusters |
| **Git** | Auto-discover apps from directory structure in a mono-repo |
| **Matrix** | Combine two generators (e.g., all apps × all clusters) |
| **Merge** | Override specific generator outputs with custom values |

### Apply

```bash
# Remove individual dev/prod apps first (ApplicationSet will recreate them)
kubectl delete -f k8s/argocd/application-dev.yaml
kubectl delete -f k8s/argocd/application-prod.yaml

# Apply the ApplicationSet
kubectl apply -f k8s/argocd/applicationset.yaml

# Verify generated applications
argocd app list
# NAME              CLUSTER  NAMESPACE  ...
# python-app-dev    in-cluster  dev     ...
# python-app-prod   in-cluster  prod    ...
```
