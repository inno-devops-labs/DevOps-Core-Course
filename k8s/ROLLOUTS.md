# Lab 14 — Progressive Delivery with Argo Rollouts

## 1. Argo Rollouts Setup

### Installation

```bash
kubectl create namespace argo-rollouts
kubectl apply -n argo-rollouts -f https://github.com/argoproj/argo-rollouts/releases/latest/download/install.yaml
kubectl apply -n argo-rollouts -f https://github.com/argoproj/argo-rollouts/releases/latest/download/dashboard-install.yaml
brew install argoproj/tap/kubectl-argo-rollouts
```

See [`rollouts/evidence/00-setup.txt`](./rollouts/evidence/00-setup.txt).

### Dashboard Access

```bash
kubectl port-forward svc/argo-rollouts-dashboard -n argo-rollouts 3100:3100
# Open http://localhost:3100
```

### CLI Version: v1.8.3

### Rollout vs Deployment

| Field | Deployment | Rollout |
|-------|-----------|---------|
| `apiVersion` | `apps/v1` | `argoproj.io/v1alpha1` |
| `kind` | `Deployment` | `Rollout` |
| `spec.strategy` | RollingUpdate / Recreate | canary / blueGreen |
| Traffic shifting | Not supported | Step-based weight control |
| Analysis | Not supported | AnalysisRun integration |
| Pause/Promote | Not supported | Manual gates in steps |

Key differences: Rollout adds `strategy.canary` or `strategy.blueGreen` blocks, supports `pause` steps, weight-based traffic shifting, and automated analysis via `AnalysisTemplate`.

---

## 2. Canary Deployment

### Strategy Configuration

`values-canary.yaml`:
```yaml
rollout:
  enabled: true
  strategy: "canary"
  analysis:
    enabled: true
```

`templates/rollout.yaml` canary strategy block:
```yaml
strategy:
  canary:
    steps:
      - setWeight: 20
      - pause: {}          # manual promotion required
      - setWeight: 40
      - pause:
          duration: 30s
      - setWeight: 60
      - pause:
          duration: 30s
      - setWeight: 80
      - pause:
          duration: 30s
    analysis:
      templates:
        - templateName: devops-info-canary-health-check
      startingStep: 1
```

### Rollout Progression

Deploy:
```bash
helm upgrade --install devops-info-canary k8s/helm/devops-info -n rollout-test \
  -f k8s/helm/devops-info/values-canary.yaml --set image.tag=v2
```

After upgrade, rollout paused at step 1 (20% weight). AnalysisRun started automatically. See [`rollouts/evidence/01-canary-paused.txt`](./rollouts/evidence/01-canary-paused.txt).

Promote through steps:
```bash
kubectl argo rollouts promote devops-info-canary -n rollout-test
# Auto-advances through timed 40% → 60% → 80% → 100%
```

After full promotion, v2 becomes stable. See [`rollouts/evidence/02-canary-60pct.txt`](./rollouts/evidence/02-canary-60pct.txt).

### Abort / Rollback

```bash
kubectl argo rollouts abort devops-info-canary -n rollout-test
```

Traffic shifted immediately back to stable (v2). Canary ReplicaSet scaled to 0. See [`rollouts/evidence/03-canary-abort.txt`](./rollouts/evidence/03-canary-abort.txt).

```bash
# Retry after abort
kubectl argo rollouts retry rollout devops-info-canary -n rollout-test
```

---

## 3. Blue-Green Deployment

### Strategy Configuration

`values-bluegreen.yaml`:
```yaml
rollout:
  enabled: true
  strategy: "blueGreen"
  analysis:
    enabled: false
```

`templates/rollout.yaml` blue-green strategy block:
```yaml
strategy:
  blueGreen:
    activeService: devops-info-bg        # production traffic
    previewService: devops-info-bg-preview  # new version for testing
    autoPromotionEnabled: false          # manual promotion
```

Two services are managed:
- **Active service** → stable (blue) ReplicaSet
- **Preview service** → new (green) ReplicaSet

### Test Flow

Initial deploy (blue):
```bash
helm upgrade --install devops-info-bg k8s/helm/devops-info -n rollout-test \
  -f k8s/helm/devops-info/values-bluegreen.yaml --set image.tag=latest \
  --set service.type=ClusterIP
```

Trigger green deployment:
```bash
kubectl argo rollouts set image devops-info-bg devops-info=merkulovlr05/devops-info:v2 -n rollout-test
```

Rollout pauses. Green (v2) is fully ready but only reachable via preview service. See [`rollouts/evidence/05-bluegreen-paused.txt`](./rollouts/evidence/05-bluegreen-paused.txt).

Test preview:
```bash
kubectl port-forward svc/devops-info-bg-preview -n rollout-test 8081:80
curl localhost:8081/health
```

Promote (instant traffic switch):
```bash
kubectl argo rollouts promote devops-info-bg -n rollout-test
```

Active service now points to green (v2). Old blue ReplicaSet kept for scaleDownDelay, then removed. See [`rollouts/evidence/06-bluegreen-promoted.txt`](./rollouts/evidence/06-bluegreen-promoted.txt).

---

## 4. Strategy Comparison

| Aspect | Canary | Blue-Green |
|--------|--------|------------|
| Traffic shift | Gradual (percentage steps) | Instant switch |
| Resource usage | ~1 extra replica during rollout | 2× replicas during rollout |
| Rollback speed | Immediate (set weight 0) | Instant |
| Risk exposure | Small % of users get new version | Nobody until promotion |
| Testing in prod | Yes, on subset of traffic | No, preview is isolated |
| Complexity | Higher (weights, analysis) | Lower |

**When to use canary:**
- High-traffic services where you want progressive exposure
- Metrics-based automated rollback (error rate, latency)
- You need real production traffic to validate the change

**When to use blue-green:**
- Database migrations or breaking API changes (instant cut-over)
- Lower-traffic services where canary percentages are statistically meaningless
- Need full environment testing before any production exposure

**Recommendation:** Canary for stateless microservices with Prometheus metrics; blue-green for services with schema changes or strict SLA requirements.

---

## 5. Bonus — Automated Analysis

### AnalysisTemplate

`templates/analysis-template.yaml`:
```yaml
apiVersion: argoproj.io/v1alpha1
kind: AnalysisTemplate
metadata:
  name: devops-info-canary-health-check
spec:
  metrics:
    - name: health-check
      provider:
        web:
          url: "http://devops-info-canary.rollout-test.svc/health"
          jsonPath: "{$.status}"
      successCondition: result == "healthy"
      interval: 10s
      count: 3
      failureLimit: 1
```

AnalysisRun fires after the canary reaches 20% weight (`startingStep: 1`). It performs 3 HTTP checks every 10 seconds. If any response returns `status != "healthy"` the AnalysisRun fails, and Argo Rollouts automatically aborts the canary — rolling all traffic back to stable.

During the canary rollout above, the AnalysisRun completed as **Successful** (✔ 3 checks passed), allowing progression to continue.

---

## 6. CLI Reference

```bash
# Watch rollout
kubectl argo rollouts get rollout <name> -n <ns> -w

# Promote to next step (canary) or to active (blue-green)
kubectl argo rollouts promote <name> -n <ns>

# Abort rollout (traffic back to stable)
kubectl argo rollouts abort <name> -n <ns>

# Retry after abort
kubectl argo rollouts retry rollout <name> -n <ns>

# Set image (triggers new rollout)
kubectl argo rollouts set image <name> <container>=<image>:<tag> -n <ns>

# List all rollouts
kubectl argo rollouts list rollouts -n <ns>

# Dashboard
kubectl port-forward svc/argo-rollouts-dashboard -n argo-rollouts 3100:3100
```
