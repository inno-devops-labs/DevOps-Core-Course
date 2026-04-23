# Lab 14 — Progressive Delivery with Argo Rollouts

## 1. Argo Rollouts Setup

### Installation verification

```bash
kubectl create namespace argo-rollouts
kubectl apply -n argo-rollouts -f https://github.com/argoproj/argo-rollouts/releases/latest/download/install.yaml
kubectl get pods -n argo-rollouts
```

Expected:
- `argo-rollouts` controller pod in `Running`

### Dashboard access

```bash
kubectl apply -n argo-rollouts -f https://github.com/argoproj/argo-rollouts/releases/latest/download/dashboard-install.yaml
kubectl port-forward svc/argo-rollouts-dashboard -n argo-rollouts 3100:3100
```

Open:
- `http://localhost:3100`

### kubectl plugin

```bash
# Linux
curl -LO https://github.com/argoproj/argo-rollouts/releases/latest/download/kubectl-argo-rollouts-linux-amd64
chmod +x kubectl-argo-rollouts-linux-amd64
sudo mv kubectl-argo-rollouts-linux-amd64 /usr/local/bin/kubectl-argo-rollouts

kubectl argo rollouts version
```

### Rollout vs Deployment (key differences)

- `Rollout` is a CRD (`apiVersion: argoproj.io/v1alpha1`) with advanced `strategy`.
- `Deployment` supports rolling updates; `Rollout` supports `canary` and `blueGreen` orchestration.
- `Rollout` adds promotion, pause steps, abort, and traffic switch workflows while keeping familiar pod template/selector structure.

---

## 2. Canary Deployment

### Strategy configuration

Implemented in chart:
- Template: `k8s/devops-info-service/templates/rollout.yaml`
- Values profile: `k8s/devops-info-service/values-rollout-canary.yaml`

Canary steps:
- 20% → pause (manual)
- 40% → pause 30s
- 60% → pause 30s
- 80% → pause 30s
- 100%

### Deploy canary rollout

```bash
helm upgrade --install devops-canary k8s/devops-info-service \
  -n dev --create-namespace \
  -f k8s/devops-info-service/values-dev.yaml \
  -f k8s/devops-info-service/values-rollout-canary.yaml
```

### Step-by-step rollout progression

```bash
kubectl argo rollouts get rollout devops-canary-devops-info-service -n dev -w
```

Trigger a new version (example tag bump):

```bash
helm upgrade devops-canary k8s/devops-info-service \
  -n dev \
  -f k8s/devops-info-service/values-dev.yaml \
  -f k8s/devops-info-service/values-rollout-canary.yaml \
  --set image.tag=v1.0.1
```

Promote through first manual pause:

```bash
kubectl argo rollouts promote devops-canary-devops-info-service -n dev
```

Abort demonstration:

```bash
kubectl argo rollouts abort devops-canary-devops-info-service -n dev
kubectl argo rollouts get rollout devops-canary-devops-info-service -n dev
```

Expected behavior:
- rollout transitions to aborted state
- traffic returns to stable replica set

---

## 3. Blue-Green Deployment

### Strategy configuration

Implemented in chart:
- Template: `k8s/devops-info-service/templates/rollout.yaml`
- Preview service template: `k8s/devops-info-service/templates/service-preview.yaml`
- Values profile: `k8s/devops-info-service/values-rollout-bluegreen.yaml`

Blue-green settings:
- `activeService`: `<fullname>`
- `previewService`: `<fullname>-preview`
- `autoPromotionEnabled: false` (manual promotion)

### Deploy blue-green rollout

```bash
helm upgrade --install devops-bg k8s/devops-info-service \
  -n prod --create-namespace \
  -f k8s/devops-info-service/values-prod.yaml \
  -f k8s/devops-info-service/values-rollout-bluegreen.yaml
```

### Preview vs active service

- Active service serves production traffic.
- Preview service exposes the new (green) version for validation before promotion.

Access both (NodePort example):

```bash
kubectl get svc -n prod
kubectl port-forward svc/devops-bg-devops-info-service -n prod 8080:80
kubectl port-forward svc/devops-bg-devops-info-service-preview -n prod 8081:80
```

Promotion:

```bash
kubectl argo rollouts promote devops-bg-devops-info-service -n prod
kubectl argo rollouts get rollout devops-bg-devops-info-service -n prod
```

Rollback (instant switch):

```bash
kubectl argo rollouts undo devops-bg-devops-info-service -n prod
```

---

## 4. Strategy Comparison

### Canary vs Blue-Green

| Aspect | Canary | Blue-Green |
|---|---|---|
| Traffic movement | Gradual, percentage-based | Instant switch between environments |
| Risk reduction | Strong (small blast radius early) | Moderate (all traffic switched at promote) |
| Rollback speed | Fast, but step-based state transitions | Very fast/instant traffic switch |
| Resource overhead | Lower | Higher (two stacks during rollout) |
| Best for | User-facing changes needing progressive validation | Clear staging/preview and instant cutover workflows |

### Recommendation by scenario

- Use **canary** when you want gradual confidence-building and phased risk.
- Use **blue-green** when you need explicit preview validation and instant production cutover/rollback.
- In high-risk production systems, combine canary with strict checks and manual gates.

---

## 5. CLI Commands Reference

### Core commands used

```bash
# Watch rollout status
kubectl argo rollouts get rollout <name> -n <ns> -w

# Promote rollout
kubectl argo rollouts promote <name> -n <ns>

# Abort rollout
kubectl argo rollouts abort <name> -n <ns>

# Retry aborted rollout
kubectl argo rollouts retry rollout <name> -n <ns>

# Undo/rollback
kubectl argo rollouts undo <name> -n <ns>

# Dashboard
kubectl argo rollouts dashboard
```

### Monitoring and troubleshooting

```bash
kubectl get rollout -A
kubectl describe rollout <name> -n <ns>
kubectl get rs -n <ns>
kubectl get svc -n <ns>
kubectl logs -n argo-rollouts deploy/argo-rollouts
```

---

## Manual evidence to collect for submission

1. Argo Rollouts dashboard screenshot showing rollout progression.
2. Canary progression screenshots:
   - paused at 20%
   - promoted
   - later steps at 40/60/80
3. Abort/rollback evidence for canary.
4. Blue-green screenshot with active + preview services.
5. Promotion and rollback evidence for blue-green.

