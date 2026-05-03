# Argo Rollouts — Progressive Delivery

## 1. Setup

### Install controller

```bash
kubectl create namespace argo-rollouts
kubectl apply -n argo-rollouts -f https://github.com/argoproj/argo-rollouts/releases/latest/download/install.yaml

# Verify
kubectl -n argo-rollouts get pods
```

### Install kubectl plugin (Linux)

```bash
curl -LO https://github.com/argoproj/argo-rollouts/releases/latest/download/kubectl-argo-rollouts-linux-amd64
chmod +x kubectl-argo-rollouts-linux-amd64
sudo mv kubectl-argo-rollouts-linux-amd64 /usr/local/bin/kubectl-argo-rollouts

kubectl argo rollouts version
```

### Dashboard

```bash
kubectl apply -n argo-rollouts -f https://github.com/argoproj/argo-rollouts/releases/latest/download/dashboard-install.yaml
kubectl port-forward svc/argo-rollouts-dashboard -n argo-rollouts 3100:3100
# Open http://localhost:3100
```

### Rollout vs Deployment

| Feature | Deployment | Rollout |
|---------|-----------|---------|
| Kind | `apps/v1/Deployment` | `argoproj.io/v1alpha1/Rollout` |
| Strategy | RollingUpdate / Recreate | canary / blueGreen |
| Traffic control | None | Weighted traffic split |
| Analysis | None | AnalysisTemplate integration |
| Rollback | Manual or auto (readiness) | Instant or metric-based |

---

## 2. Canary Deployment

### Strategy

Configured in `templates/rollout.yaml` when `rollout.strategy: canary`.

Steps:
1. Set 20% traffic to canary — **pause** (manual promotion required)
2. Set 40% — pause 30s (auto-continue)
3. Set 60% — pause 30s
4. Set 80% — pause 30s
5. 100% (complete)

### Deploy

```bash
# Enable rollout with canary strategy
helm upgrade --install devops-info k8s/devops-info-chart \
  -f k8s/devops-info-chart/values-canary.yaml

# Watch rollout status
kubectl argo rollouts get rollout devops-info-devops-info-chart -w
```

### Trigger canary (update image)

```bash
helm upgrade devops-info k8s/devops-info-chart \
  -f k8s/devops-info-chart/values-canary.yaml \
  --set image.tag=lab03
```

### Promote through steps

```bash
# After 20% pause — manually promote
kubectl argo rollouts promote devops-info-devops-info-chart

# Subsequent steps progress automatically after 30s pauses
```

### Abort and rollback

```bash
# Abort during rollout — traffic shifts back to stable immediately
kubectl argo rollouts abort devops-info-devops-info-chart

# Retry after fixing the issue
kubectl argo rollouts retry rollout devops-info-devops-info-chart
```

---

## 3. Blue-Green Deployment

### Strategy

Configured with `rollout.strategy: blueGreen`. Requires two services:
- **Active service** (`devops-info-devops-info-chart`) — production traffic
- **Preview service** (`devops-info-devops-info-chart-preview`) — new version for testing

### Deploy

```bash
helm upgrade --install devops-info k8s/devops-info-chart \
  -f k8s/devops-info-chart/values-bluegreen.yaml
```

### Blue-Green flow

```bash
# Trigger green deployment
helm upgrade devops-info k8s/devops-info-chart \
  -f k8s/devops-info-chart/values-bluegreen.yaml \
  --set image.tag=lab03

# Test preview (green) — does not affect production
kubectl port-forward svc/devops-info-devops-info-chart-preview 8081:80

# Test active (blue) — still old version
kubectl port-forward svc/devops-info-devops-info-chart 8080:80

# Promote green to active (instant switch)
kubectl argo rollouts promote devops-info-devops-info-chart
```

### Instant rollback

```bash
# After promotion, rollback is instant
kubectl argo rollouts undo devops-info-devops-info-chart
```

---

## 4. Strategy Comparison

| Aspect | Canary | Blue-Green |
|--------|--------|------------|
| Traffic shift | Gradual (% based) | Instant (all-or-nothing) |
| Rollback speed | Fast (re-weight) | Instant |
| Resource usage | Normal (mixed pods) | 2x during deployment |
| Testing | Real user % see new version | Isolated preview env |
| Risk | Lower (small blast radius) | Higher (full switch) |
| Best for | Stateless APIs, feature flags | DB migrations, breaking changes |

**Recommendation:**
- Use **canary** for regular feature releases where gradual validation matters
- Use **blue-green** when you need a staging environment to test before any users see the change, or when rollback must be instant

---

## 5. CLI Reference

```bash
# Status
kubectl argo rollouts get rollout <name> -w
kubectl argo rollouts list rollouts

# Control
kubectl argo rollouts promote <name>          # next step
kubectl argo rollouts promote --full <name>   # skip all steps
kubectl argo rollouts abort <name>            # rollback
kubectl argo rollouts retry rollout <name>    # retry aborted
kubectl argo rollouts undo <name>             # rollback after promotion

# History
kubectl argo rollouts history rollout <name>

# Dashboard
kubectl port-forward svc/argo-rollouts-dashboard -n argo-rollouts 3100:3100
```

---

## 6. Bonus — Automated Analysis

AnalysisTemplate `success-rate` checks `/health` endpoint during canary rollout.

```bash
# Enable analysis in canary
helm upgrade devops-info k8s/devops-info-chart \
  -f k8s/devops-info-chart/values-canary.yaml \
  --set rollout.analysis.enabled=true \
  --set image.tag=lab03
```

The template polls `/health` 3 times every 10 seconds after the 20% step.
If `{"status": "healthy"}` is not returned, the rollout auto-aborts and traffic returns to stable.

Check analysis run:

```bash
kubectl get analysisrun
kubectl describe analysisrun <name>
```
