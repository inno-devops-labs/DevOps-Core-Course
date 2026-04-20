# Lab 13 - GitOps with ArgoCD

This lab wires the Helm chart from Labs 11-12 into ArgoCD so the cluster is driven from Git.

## 1. ArgoCD Installation & Setup

### Install via Helm

```bash
helm repo add argo https://argoproj.github.io/argo-helm
helm repo update
kubectl apply -f k8s/argocd/namespaces.yaml
helm install argocd argo/argo-cd --namespace argocd
```

### Wait for readiness

```bash
kubectl wait --for=condition=ready pod -l app.kubernetes.io/name=argocd-server -n argocd --timeout=120s
kubectl get pods -n argocd
```

### Access the UI

```bash
kubectl port-forward svc/argocd-server -n argocd 8080:443
kubectl -n argocd get secret argocd-initial-admin-secret -o jsonpath="{.data.password}" | base64 -d
```

Open:

- `https://localhost:8080`
- Username: `admin`
- Password: output from the secret above

### Install the CLI

Windows:

- Download `argocd.exe` from the official GitHub releases and add it to `PATH`

Linux/macOS examples:

```bash
brew install argocd
```

```bash
argocd login localhost:8080 --insecure
argocd app list
```

## 2. Application Deployment

### Manifests

All ArgoCD manifests are stored in `k8s/argocd/`:

- `application.yaml` for the base app
- `application-dev.yaml` for development
- `application-prod.yaml` for production
- `namespaces.yaml` for `argocd`, `dev`, and `prod`

### Source of truth

- Repository: `https://github.com/AliyaSag/DevOps-Core-Course.git`
- Branch: `lab13`
- Helm chart path: `k8s/python-app`

### Sync strategy

- Base app: manual sync
- Dev app: auto-sync with `prune` and `selfHeal`
- Prod app: manual sync

### Apply the Applications

```bash
kubectl apply -f k8s/argocd/application.yaml
kubectl apply -f k8s/argocd/application-dev.yaml
kubectl apply -f k8s/argocd/application-prod.yaml
```

### Initial sync

```bash
argocd app sync python-app
argocd app sync python-app-dev
argocd app sync python-app-prod
argocd app get python-app-dev
```

## 3. Multi-Environment Deployment

### Environment differences

| Environment | Namespace | Values file | Sync policy | Replica count |
|---|---|---|---|---|
| Base | `default` | `values.yaml` | Manual | 3 |
| Dev | `dev` | `values-dev.yaml` | Auto-sync + self-heal | 1 |
| Prod | `prod` | `values-prod.yaml` | Manual | 5 |

### Why dev is automated and prod is manual

- Dev should converge automatically so configuration mistakes are fixed quickly
- Prod should be promoted intentionally after review
- Manual sync in prod provides a release gate and reduces surprise deploys

### Verify deployed resources

```bash
kubectl get pods -n dev
kubectl get pods -n prod
kubectl get svc -n dev
kubectl get svc -n prod
argocd app list
```

## 4. Self-Healing & Sync Policies

### Kubernetes pod recreation

Deleting a pod is normal Kubernetes behavior. The Deployment/ReplicaSet restores it automatically.

```bash
kubectl delete pod -n dev -l app.kubernetes.io/name=python-app
kubectl get pods -n dev -w
```

### ArgoCD drift correction

Manual changes to a resource in `dev` should be reverted by ArgoCD because auto-sync and `selfHeal` are enabled.

```bash
kubectl scale deployment python-app-dev -n dev --replicas=5
argocd app diff python-app-dev
argocd app get python-app-dev
```

Expected behavior:

- ArgoCD marks the app `OutOfSync`
- It restores the replica count back to the Git value
- The pod count returns to the configured value from `values-dev.yaml`

### Sync timing

- ArgoCD continuously watches for state drift
- Git polling is typically around 3 minutes by default
- Webhooks or manual sync can speed up reconciliation

## 5. Verification Evidence To Capture

Collect these outputs in your cluster:

```bash
kubectl get pods -n argocd
kubectl get applications -n argocd
argocd app list
argocd app get python-app-dev
argocd app diff python-app-dev
kubectl get pods -n dev
kubectl get pods -n prod
```

Also capture screenshots of:

- ArgoCD UI application list
- Application details page
- Sync status before and after a change

