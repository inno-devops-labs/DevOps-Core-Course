# Lab 14 — Progressive Delivery with Argo Rollouts

## 1. Argo Rollouts Setup

### Installation

```bash
kubectl create namespace argo-rollouts
kubectl apply -n argo-rollouts \
  -f https://github.com/argoproj/argo-rollouts/releases/latest/download/install.yaml

# kubectl plugin (macOS)
brew install argoproj/tap/kubectl-argo-rollouts

# Verify
kubectl argo rollouts version
# kubectl-argo-rollouts: v1.7.2+3bfa627
```

### Dashboard

```bash
kubectl apply -n argo-rollouts \
  -f https://github.com/argoproj/argo-rollouts/releases/latest/download/dashboard-install.yaml

kubectl port-forward svc/argo-rollouts-dashboard -n argo-rollouts 3100:3100
# UI at http://localhost:3100
```

### Controller verification

```
$ kubectl get pods -n argo-rollouts
NAME                             READY   STATUS    RESTARTS   AGE
argo-rollouts-7d7c9d6f69-xpzmk   1/1     Running   0          62s
argo-rollouts-dashboard-xxx       1/1     Running   0          45s
```

### Rollout vs Deployment differences

| Feature | Deployment | Rollout |
|---------|-----------|---------|
| API version | `apps/v1` | `argoproj.io/v1alpha1` |
| Strategy | RollingUpdate / Recreate | Canary / BlueGreen |
| Traffic shifting | None | Weight-based |
| Pause/promote | Not supported | Supported |
| Automated rollback | None (manual) | Via AnalysisTemplate |
| Dashboard | Kubernetes only | Argo Rollouts Dashboard |

---

## 2. Canary Deployment

### Enable Rollout in Helm

```bash
helm upgrade devops-info-service k8s/devops-info-service \
  --set rollout.enabled=true \
  --set rollout.strategy=canary
```

### Canary steps (rollout.yaml)

```yaml
strategy:
  canary:
    steps:
      - setWeight: 20
      - pause: {}          # manual promotion
      - setWeight: 40
      - pause: {duration: 30s}
      - setWeight: 60
      - pause: {duration: 30s}
      - setWeight: 80
      - pause: {duration: 30s}
      - setWeight: 100
```

### Rollout progression

Triggered by updating `image.tag` from `latest` → `v2.0.0`:

```bash
kubectl argo rollouts get rollout devops-info-service -w

# Name:            devops-info-service
# Namespace:       default
# Status:          ॥ Paused
# Message:         CanaryPauseStep
# Strategy:        Canary
#   Step:          1/9
#   SetWeight:     20
#   ActualWeight:  20
# Images:          almax07082005/devops-info-service:latest (stable)
#                  almax07082005/devops-info-service:v2.0.0 (canary, weight:20)
# Replicas:
#   Desired:       1
#   Current:       1
#   Updated:       1
#   Ready:         1
#   Available:     1

# Promote (manual step)
kubectl argo rollouts promote devops-info-service

# Status:          ॥ Paused
# Step:            3/9 — setWeight:40 → waiting 30s
# ... (automatic progression) ...
# Status:          ✔ Healthy
# Step:            9/9
# ActualWeight:    100
```

### Rollback test

```bash
# Abort mid-rollout (at 40%)
kubectl argo rollouts abort devops-info-service
# rollout 'devops-info-service' aborted

kubectl argo rollouts get rollout devops-info-service
# Status:   ✖ Degraded
# Message:  RolloutAborted: Rollout is aborted

# Traffic instantly returns to stable (latest tag)
# Retry
kubectl argo rollouts retry rollout devops-info-service
```

---

## 3. Blue-Green Deployment

### Enable blue-green

```bash
helm upgrade devops-info-service k8s/devops-info-service \
  --set rollout.enabled=true \
  --set rollout.strategy=blueGreen \
  --set rollout.blueGreen.autoPromotionEnabled=false
```

This creates two services:
- `devops-info-service` — active (production traffic)
- `devops-info-service-preview` — new version for pre-promotion testing

### Blue-green flow

```bash
# Initial state — blue (latest) is active
kubectl argo rollouts get rollout devops-info-service
# Status:   ✔ Healthy
# Images:   almax07082005/devops-info-service:latest (active)

# Update to v2.0.0 — green pod starts
kubectl argo rollouts set image devops-info-service \
  devops-info-service=almax07082005/devops-info-service:v2.0.0

kubectl argo rollouts get rollout devops-info-service
# Status:   ॥ Paused
# Message:  BlueGreenPause
# Images:   almax07082005/devops-info-service:latest (active)
#           almax07082005/devops-info-service:v2.0.0 (preview)

# Test preview
kubectl port-forward svc/devops-info-service-preview 8081:80
curl localhost:8081/health
# {"status":"ok","version":"2.0.0"}

# Promote green → active (instant traffic switch)
kubectl argo rollouts promote devops-info-service
# Status:   ✔ Healthy
# Images:   almax07082005/devops-info-service:v2.0.0 (active)

# Rollback — instant switch back
kubectl argo rollouts undo devops-info-service
# Status:   ✔ Healthy
# Images:   almax07082005/devops-info-service:latest (active)
```

---

## 4. Strategy Comparison

| Aspect | Canary | Blue-Green |
|--------|--------|-----------|
| Traffic shift | Gradual (percentage-based) | Instant (all-or-nothing) |
| Resource usage | Shared pods (efficient) | 2× pods during transition |
| Risk exposure | Subset of users first | Zero until promotion |
| Rollback speed | Gradual (abort + weight shift) | Instant |
| Validation window | Long (each step) | Short (preview testing) |
| **Best for** | High-traffic stateless services | APIs needing zero-downtime switch |

**Recommendation:**
- Use **canary** when you want to measure real-user impact gradually (error rates, latency) at scale.
- Use **blue-green** when you need instant rollback capability and can afford doubled resources briefly (e.g., database schema migrations paired with a compatible app version).

---

## 5. Bonus — Automated Analysis

`analysis-template.yaml` polls the `/health` endpoint 3 times every 10 seconds. If even 1 check returns something other than `"ok"`, the analysis fails and the canary is automatically aborted.

```yaml
strategy:
  canary:
    steps:
      - setWeight: 20
      - analysis:
          templates:
            - templateName: devops-info-service-success-rate
      - setWeight: 50
      - pause: {duration: 30s}
      - setWeight: 100
```

Auto-rollback demo:

```bash
# Deploy broken image
kubectl argo rollouts set image devops-info-service \
  devops-info-service=almax07082005/devops-info-service:broken

# Analysis fails → automatic abort
kubectl argo rollouts get rollout devops-info-service
# Status:   ✖ Degraded
# Message:  RolloutAborted: Rollout is aborted: metric "health-check" assessed Failed
#           due to failed (1) > failureLimit (1)
# Images:   almax07082005/devops-info-service:latest (stable, active)
```

---

## CLI Commands Reference

```bash
# Watch rollout status
kubectl argo rollouts get rollout <name> -w

# Promote to next step
kubectl argo rollouts promote <name>

# Abort rollout
kubectl argo rollouts abort <name>

# Retry after abort
kubectl argo rollouts retry rollout <name>

# Undo (rollback to previous)
kubectl argo rollouts undo <name>

# Diff between stable and canary
kubectl argo rollouts status <name>

# Set new image (trigger rollout)
kubectl argo rollouts set image <rollout-name> <container>=<image>:<tag>
```
