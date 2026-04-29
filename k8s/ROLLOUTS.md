# Lab 14 — Progressive Delivery with Argo Rollouts

## 1. Argo Rollouts Setup

### Installation

```bash
kubectl create namespace argo-rollouts
kubectl apply -n argo-rollouts -f https://github.com/argoproj/argo-rollouts/releases/latest/download/install.yaml
kubectl apply -n argo-rollouts -f https://github.com/argoproj/argo-rollouts/releases/latest/download/dashboard-install.yaml
brew install argoproj/tap/kubectl-argo-rollouts
```

### Verification

```
$ kubectl argo rollouts version
kubectl-argo-rollouts: v1.8.3+49fa151

$ kubectl get pods -n argo-rollouts
NAME                                READY   STATUS
argo-rollouts-5f64f8d68-rhxmk       1/1     Running
argo-rollouts-dashboard-xxx         1/1     Running
```

### Dashboard access

```bash
kubectl port-forward svc/argo-rollouts-dashboard -n argo-rollouts 3100:3100
# Open http://localhost:3100
```

### Rollout vs Deployment

| | Deployment | Rollout |
|---|---|---|
| API | `apps/v1` | `argoproj.io/v1alpha1` |
| Strategy | RollingUpdate / Recreate | Canary / BlueGreen |
| Traffic control | None | Weighted traffic splitting |
| Pause/Promote | No | Yes |
| Analysis | No | AnalysisTemplate integration |
| Rollback | Manual | Automatic on abort |

---

## 2. Canary Deployment

### Strategy configuration

```yaml
strategy:
  canary:
    steps:
      - setWeight: 20
      - pause: {}          # Manual promotion required
      - setWeight: 40
      - pause: { duration: 30s }
      - setWeight: 60
      - pause: { duration: 30s }
      - setWeight: 80
      - pause: { duration: 30s }
      - setWeight: 100
```

### Rollout progression

```
# Initial state
Status: ✔ Healthy  Step: 9/9  SetWeight: 100  (stable)

# After helm upgrade (new env var)
Status: ◌ Progressing  Step: 0/9  SetWeight: 20  (1 canary pod)

# Reached manual pause
Status: ॥ Paused  Step: 1/9  SetWeight: 20  ActualWeight: 25

# After promote
Status: ॥ Paused  Step: 3/9  SetWeight: 40  (auto-progressing)

# Abort test
Status: ✖ Degraded  RolloutAborted  SetWeight: 0  (traffic back to stable)

# After retry + full promote
Status: ✔ Healthy  Step: 9/9  SetWeight: 100  (revision 2 = stable)
```

### CLI commands used

```bash
# Watch status
kubectl argo rollouts get rollout devops-canary-devops-info-service

# Promote past manual pause
kubectl argo rollouts promote devops-canary-devops-info-service

# Abort (rollback to stable)
kubectl argo rollouts abort devops-canary-devops-info-service

# Retry after abort
kubectl argo rollouts retry rollout devops-canary-devops-info-service

# Full promote (skip all steps)
kubectl argo rollouts promote devops-canary-devops-info-service --full
```

---

## 3. Blue-Green Deployment

### Strategy configuration

```yaml
strategy:
  blueGreen:
    activeService: devops-bluegreen-devops-info-service
    previewService: devops-bluegreen-devops-info-service-preview
    autoPromotionEnabled: false  # Manual promotion
```

Two services:
- **active** — production traffic (blue)
- **preview** — new version for testing (green)

### Blue-Green flow

```
# Initial state (blue = active)
Status: ✔ Healthy  revision:1  stable,active

# After patch (green deployed as preview)
Status: ॥ Paused  BlueGreenPause
  revision:3  preview    (3 new pods ready)
  revision:1  stable,active  (3 old pods serving traffic)

# After promote (instant switch)
Status: ✔ Healthy
  revision:3  stable,active  (green is now active)
  revision:1  ScaledDown     (blue scaled down)
```

### Instant rollback

Blue-green rollback is instant — Rollouts controller just switches the service selector back to the previous ReplicaSet. No pod creation needed.

---

## 4. Strategy Comparison

| | Canary | Blue-Green |
|---|---|---|
| Traffic shift | Gradual (20→40→60→80→100%) | Instant (0% or 100%) |
| Resources | ~1 extra pod during rollout | 2x pods during deployment |
| Rollback speed | Gradual (abort → scale down) | Instant (selector switch) |
| Testing | % of real traffic | Separate preview service |
| Risk | Low (small blast radius) | Medium (all-or-nothing) |
| Best for | High-traffic, risk-averse | Fast iteration, preview testing |

**Recommendation:**
- Use **canary** for production services with real user traffic — gradual exposure limits blast radius
- Use **blue-green** when you need to test the new version with real data before switching, or when instant rollback is critical (e.g., payment services)

---

## Bonus — Automated Analysis

### AnalysisTemplate

```yaml
apiVersion: argoproj.io/v1alpha1
kind: AnalysisTemplate
metadata:
  name: devops-info-service-health-check
spec:
  metrics:
    - name: health-check
      provider:
        web:
          url: "http://devops-info-service.default.svc/health"
          jsonPath: "{$.status}"
      successCondition: result == "healthy"
      interval: 10s
      count: 3
      failureLimit: 1
```

Integrates with canary steps:
```yaml
steps:
  - setWeight: 20
  - analysis:
      templates:
        - templateName: devops-info-service-health-check
  - setWeight: 50
  - pause: { duration: 30s }
```

If health check fails 1+ times → rollout automatically aborted → traffic returns to stable.
