# Lab 13 — GitOps with ArgoCD

## 1. ArgoCD Setup

### Installation verification

```bash
helm repo add argo https://argoproj.github.io/argo-helm
helm repo update
kubectl create namespace argocd
helm upgrade --install argocd argo/argo-cd -n argocd -f k8s/argocd/install-values.yaml
kubectl get pods -n argocd
```

Expected components include:
- `argocd-server`
- `argocd-repo-server`
- `argocd-application-controller`
- `argocd-dex-server`
- `argocd-redis`

### UI access method

```bash
kubectl port-forward svc/argocd-server -n argocd 8080:80
kubectl -n argocd get secret argocd-initial-admin-secret -o jsonpath="{.data.password}" | base64 -d && echo
```

Open:
- `http://localhost:8080`

Credentials:
- username: `admin`
- password: value from `argocd-initial-admin-secret`

### CLI configuration

Install CLI (Linux example):

```bash
curl -sSL -o /tmp/argocd https://github.com/argoproj/argo-cd/releases/latest/download/argocd-linux-amd64
chmod +x /tmp/argocd
sudo mv /tmp/argocd /usr/local/bin/argocd
argocd version --client
```

Login and basic checks:

```bash
argocd login localhost:8080 --insecure
argocd app list
```

---

## 2. Application Configuration

### Application manifests

Files created:
- `k8s/argocd/application.yaml` (single app, manual sync)
- `k8s/argocd/application-dev.yaml` (dev, auto-sync)
- `k8s/argocd/application-prod.yaml` (prod, manual sync)
- `k8s/argocd/namespaces.yaml` (dev/prod namespaces)

### Source and destination configuration

All ArgoCD `Application` manifests use:
- `source.repoURL`: `https://github.com/TheBugYouCantFix/DevOps-Core-Course.git`
- `source.targetRevision`: `lab13`
- `source.path`: `k8s/devops-info-service`
- `destination.server`: `https://kubernetes.default.svc`

Destination namespaces:
- baseline app: `default`
- dev app: `dev`
- prod app: `prod`

### Values file selection

- `application.yaml` uses `values.yaml`
- `application-dev.yaml` uses `values-dev.yaml`
- `application-prod.yaml` uses `values-prod.yaml`

Deployment commands:

```bash
kubectl apply -f k8s/argocd/namespaces.yaml
kubectl apply -f k8s/argocd/application.yaml
kubectl apply -f k8s/argocd/application-dev.yaml
kubectl apply -f k8s/argocd/application-prod.yaml
```

Initial sync:

```bash
argocd app sync devops-info
argocd app sync devops-info-dev
argocd app sync devops-info-prod
argocd app get devops-info-dev
argocd app get devops-info-prod
```

---

## 3. Multi-Environment

### Dev vs Prod configuration differences

From Helm values:
- `values-dev.yaml`: `replicaCount: 1`, smaller resource requests/limits, `NodePort`
- `values-prod.yaml`: `replicaCount: 3`, larger resource requests/limits, `LoadBalancer`

### Sync policy differences and rationale

- **Dev** (`application-dev.yaml`):
  - auto-sync enabled (`automated`)
  - `selfHeal: true`
  - `prune: true`
  - fast feedback, immediate drift correction

- **Prod** (`application-prod.yaml`):
  - manual sync only (no `automated` block)
  - controlled promotion and change review before apply

### Namespace separation

- `dev` namespace hosts dev release
- `prod` namespace hosts prod release
- isolation reduces risk and clarifies ownership/observability

Verification commands:

```bash
kubectl get ns dev prod
kubectl get pods -n dev
kubectl get pods -n prod
argocd app list
```

---

## 4. Self-Healing Evidence

### Manual scale drift test (ArgoCD self-heal)

1. Observe current replicas in `dev`:
```bash
kubectl get deploy -n dev
```

2. Introduce drift:
```bash
kubectl scale deployment devops-info-dev-devops-info-service -n dev --replicas=5
kubectl get deploy devops-info-dev-devops-info-service -n dev
```

3. Watch ArgoCD revert:
```bash
argocd app get devops-info-dev
kubectl get deploy devops-info-dev-devops-info-service -n dev -w
```

Expected behavior:
- deployment temporarily shows 5 replicas
- ArgoCD marks `OutOfSync`
- auto-sync/self-heal restores replicas from Git (`values-dev.yaml`, replicaCount=1)

### Pod deletion test (Kubernetes healing)

```bash
kubectl delete pod -n dev -l app.kubernetes.io/instance=devops-info-dev
kubectl get pods -n dev -w
```

Expected behavior:
- ReplicaSet/Deployment recreates pod
- this is Kubernetes workload controller behavior (not ArgoCD sync)

### Configuration drift test

Add an unmanaged label manually:

```bash
kubectl patch deployment devops-info-dev-devops-info-service -n dev \
  --type='merge' \
  -p '{"metadata":{"labels":{"drift-test":"true"}}}'

argocd app diff devops-info-dev
argocd app get devops-info-dev
```

Expected behavior:
- ArgoCD detects drift (`OutOfSync`)
- with auto-sync + self-heal enabled, ArgoCD removes drift label to match Git

### Sync behavior explanation

- **Kubernetes self-healing**: keeps declared pod replica count for a Deployment/ReplicaSet.
- **ArgoCD self-healing**: reverts resource spec drift to match Git when app is auto-sync + self-heal.

ArgoCD sync triggers:
- Git changes detected by polling (default interval ~3 minutes)
- webhooks (if configured)
- manual sync command/UI action

---

## 5. Screenshots

Capture and attach:

1. ArgoCD UI application list showing both:
   - `devops-info-dev`
   - `devops-info-prod`

2. Sync status view:
   - dev auto-sync behavior (`Synced` / temporary `OutOfSync` during drift test)
   - prod manual sync indicators

3. Application details page:
   - source repo/path/branch
   - destination namespace
   - health + sync status

