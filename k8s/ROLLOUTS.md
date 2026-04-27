# Lab 14 — Progressive Delivery with Argo Rollouts


## Task 1 — Argo Rollouts fundamentals

### 1.1 Install controller + kubectl plugin

```bash
kubectl create namespace argo-rollouts
kubectl apply -n argo-rollouts -f https://github.com/argoproj/argo-rollouts/releases/latest/download/install.yaml

# macOS plugin
brew install argoproj/tap/kubectl-argo-rollouts

# verify
kubectl argo rollouts version
kubectl get pods -n argo-rollouts
```

**My run (evidence):**

```bash
kubectl config current-context
# minikube

kubectl cluster-info
# Kubernetes control plane is running at https://127.0.0.1:54074

kubectl create namespace argo-rollouts
# namespace/argo-rollouts created

kubectl apply -n argo-rollouts -f https://github.com/argoproj/argo-rollouts/releases/latest/download/install.yaml
# (CRDs + controller resources created)

kubectl apply -n argo-rollouts -f https://github.com/argoproj/argo-rollouts/releases/latest/download/dashboard-install.yaml
# (dashboard resources created)

brew install argoproj/tap/kubectl-argo-rollouts

kubectl argo rollouts version
# kubectl-argo-rollouts: v1.8.3

kubectl get pods -n argo-rollouts
# argo-rollouts-...            Running
# argo-rollouts-dashboard-...   Running
```

### 1.2 Install dashboard + access

```bash
kubectl apply -n argo-rollouts -f https://github.com/argoproj/argo-rollouts/releases/latest/download/dashboard-install.yaml
kubectl port-forward svc/argo-rollouts-dashboard -n argo-rollouts 3100:3100
# open http://localhost:3100
```

**My run (evidence):**

```bash
kubectl port-forward svc/argo-rollouts-dashboard -n argo-rollouts 3100:3100
# Forwarding from 127.0.0.1:3100 -> 3100
```

### 1.3 Rollout vs Deployment (key differences)

- **API/Kind**: `apps/v1 Deployment` → `argoproj.io/v1alpha1 Rollout`
- **Progressive strategies**: Rollout supports `strategy.canary` and `strategy.blueGreen`
- **Controls**: promotion, abort, retry, rollback via `kubectl argo rollouts ...`
- **Traffic shifting**: canary weight-based steps (replica-based without ingress; traffic routing optional)

---

## Task 2 — Canary deployment (dev)

### 2.1 Helm chart changes

- Added `templates/rollout.yaml` (kind `Rollout`)
- Guarded `templates/deployment.yaml` to render only when rollouts disabled
- Canary strategy is enabled in `values-dev.yaml`:
  - 20% → pause (manual promote)
  - 40% → pause 30s
  - 60% → pause 30s
  - 80% → pause 30s
  - 100%

### 2.2 Observe rollout progression

Watch:

```bash
kubectl argo rollouts get rollout devops-info-service -n dev -w
```

Trigger a new rollout (example):

```bash
# Example: change image tag or add env var in values-dev.yaml, then push via ArgoCD
# After sync, rollout starts and stops at 20% pause
```

Promote first step manually:

```bash
kubectl argo rollouts promote devops-info-service -n dev
```

### 2.3 Abort / rollback test

During a rollout:

```bash
kubectl argo rollouts abort devops-info-service -n dev
kubectl argo rollouts get rollout devops-info-service -n dev
```

---

## Task 3 — Blue-green deployment (prod)

### 3.1 Helm chart changes

- Blue-green enabled in `values-prod.yaml`
- Preview service is created by `templates/service-preview.yaml`
- Rollout uses:
  - `activeService: devops-info-service`
  - `previewService: devops-info-service-preview`
  - `autoPromotionEnabled: false` (manual promotion)

### 3.2 Test preview vs active and promote

```bash
# Active service
kubectl port-forward -n prod svc/devops-info-service 8080:80

# Preview service
kubectl port-forward -n prod svc/devops-info-service-preview 8081:80
```

Promote green to active:

```bash
kubectl argo rollouts promote devops-info-service -n prod
```

### 3.3 Instant rollback

```bash
kubectl argo rollouts undo devops-info-service -n prod
```

---

## Task 4 — Documentation requirements checklist

- **Setup**: controller + dashboard installed, CLI plugin works
- **Canary**: steps, manual promote, abort demonstrated (screenshots from dashboard recommended)
- **Blue-green**: preview/active services, promotion, undo
- **Comparison**:
  - Canary: gradual, mixed traffic, slower but safer
  - Blue-green: instant switch, needs double capacity, easy rollback
- **Commands reference**: see sections above

---

## Useful commands reference

```bash
kubectl argo rollouts get rollout devops-info-service -n dev
kubectl argo rollouts get rollout devops-info-service -n prod
kubectl argo rollouts promote devops-info-service -n dev
kubectl argo rollouts promote devops-info-service -n prod
kubectl argo rollouts abort devops-info-service -n dev
kubectl argo rollouts undo devops-info-service -n prod
```

