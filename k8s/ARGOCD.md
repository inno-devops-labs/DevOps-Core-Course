# ArgoCD GitOps Deployment (Lab 13)

This document covers the non-bonus Lab 13 scope:
- ArgoCD install and access
- ArgoCD Application manifests
- Multi-environment setup (dev/prod)
- Self-healing and drift tests

## 1. ArgoCD Setup

### 1.1 Install ArgoCD with Helm

```bash
helm repo add argo https://argoproj.github.io/argo-helm
helm repo update

kubectl create namespace argocd
helm install argocd argo/argo-cd --namespace argocd

kubectl get pods -n argocd
kubectl wait --for=condition=ready pod -l app.kubernetes.io/name=argocd-server -n argocd --timeout=180s
```

### 1.2 Access ArgoCD UI

```bash
kubectl port-forward svc/argocd-server -n argocd 8080:443
```

Open: `https://localhost:8080`

Initial credentials:
- Username: `admin`
- Password command:

```bash
kubectl -n argocd get secret argocd-initial-admin-secret \
  -o jsonpath="{.data.password}" | base64 -d && echo
```

### 1.3 Install and Configure ArgoCD CLI

```bash
# macOS
brew install argocd

# Login
argocd login localhost:8080 --insecure --username admin --password '<INITIAL_PASSWORD>'

# Verification
argocd account get-user-info
argocd app list
```

## 2. Application Configuration

Manifests are in `k8s/argocd/`:

- `application.yaml` - base app deployment (manual sync, default namespace)
- `application-dev.yaml` - dev environment (`values-dev.yaml`, auto-sync + self-heal + prune)
- `application-prod.yaml` - prod environment (`values-prod.yaml`, manual sync)
- `namespaces.yaml` - `dev` and `prod` namespaces

Source and destination used in all applications:
- `repoURL`: `https://github.com/plaffyyy/DevOps-Core-Course.git`
- `targetRevision`: `labs/lab12`
- `path`: `k8s/devops-info-service`
- `destination.server`: `https://kubernetes.default.svc`

## 3. Deployment Workflow

### 3.1 Apply Namespaces and Applications

```bash
kubectl apply -f k8s/argocd/namespaces.yaml
kubectl apply -f k8s/argocd/application.yaml
kubectl apply -f k8s/argocd/application-dev.yaml
kubectl apply -f k8s/argocd/application-prod.yaml
```

### 3.2 Initial Sync

```bash
argocd app sync devops-info-service
argocd app get devops-info-service
```

### 3.3 Multi-Environment Verification

```bash
argocd app list
kubectl get pods -n dev
kubectl get pods -n prod
```

Expected:
- `devops-info-service-dev` is auto-synced and self-healing
- `devops-info-service-prod` is manual sync only
- Different configuration is applied via `values-dev.yaml` and `values-prod.yaml`

## 4. Dev vs Prod Strategy

| Area | Dev | Prod |
|------|-----|------|
| Namespace | `dev` | `prod` |
| Values file | `values-dev.yaml` | `values-prod.yaml` |
| Sync mode | Automated | Manual |
| `selfHeal` | Enabled | Disabled |
| `prune` | Enabled | Disabled |
| Why | Fast feedback, automatic reconciliation | Controlled releases and review gate |

Rationale for manual prod sync:
- explicit release control
- safer change windows
- review/compliance-friendly workflow

## 5. Self-Healing and Drift Tests

Use `devops-info-service-dev` for all drift tests.

### 5.1 Test A - Manual Scale Drift (ArgoCD self-healing)

```bash
# get deployment name in dev namespace
kubectl get deploy -n dev

# scale manually to cause drift
kubectl scale deployment <DEPLOYMENT_NAME> -n dev --replicas=5

# observe ArgoCD status and reconciliation
argocd app get devops-info-service-dev
kubectl get deploy <DEPLOYMENT_NAME> -n dev -w
```

Expected behavior:
- App becomes `OutOfSync`
- ArgoCD auto-sync restores replica count from Git state

### 5.2 Test B - Pod Deletion (Kubernetes healing)

```bash
kubectl get pods -n dev
kubectl delete pod -n dev <POD_NAME>
kubectl get pods -n dev -w
```

Expected behavior:
- ReplicaSet recreates pod immediately
- This is Kubernetes controller behavior, not ArgoCD sync

### 5.3 Test C - Configuration Drift

```bash
kubectl label deployment <DEPLOYMENT_NAME> -n dev drift-test=true --overwrite
argocd app diff devops-info-service-dev
argocd app get devops-info-service-dev
```

Expected behavior:
- ArgoCD detects live-vs-git diff
- Auto-sync with self-heal removes manual drift

### 5.4 Sync Trigger and Interval

- ArgoCD sync/reconcile is triggered by:
  - Git change detection
  - live state drift (when `selfHeal` is enabled)
  - manual sync command/UI action
- Default polling interval is approximately 3 minutes (or faster with webhooks/manual sync)

## 6. Screenshots to Include in PR

Capture and attach the following:

1. ArgoCD UI with both applications (`devops-info-service-dev`, `devops-info-service-prod`)
2. Sync status overview (Synced / OutOfSync transitions)
3. Application details page for dev app showing automated policy
4. Diff view during configuration drift test

## 7. Notes

- Bonus task (ApplicationSet) is intentionally excluded.
- GitOps rule: apply configuration changes in Git first; ArgoCD reconciles cluster state from repository state.
