# Lab 14 — Progressive Delivery with Argo Rollouts

## 1. Argo Rollouts Setup

### Installation

Installed Argo Rollouts controller and dashboard into the `kind-lab12` cluster:

```bash
kubectl create namespace argo-rollouts
kubectl apply -n argo-rollouts -f https://github.com/argoproj/argo-rollouts/releases/latest/download/install.yaml
kubectl apply -n argo-rollouts -f https://github.com/argoproj/argo-rollouts/releases/latest/download/dashboard-install.yaml
```

kubectl plugin installed to `~/.local/bin/`:

```bash
curl -sLO https://github.com/argoproj/argo-rollouts/releases/latest/download/kubectl-argo-rollouts-linux-amd64
chmod +x kubectl-argo-rollouts-linux-amd64
mv kubectl-argo-rollouts-linux-amd64 ~/.local/bin/kubectl-argo-rollouts
```

### Verification

```
kubectl-argo-rollouts version
kubectl-argo-rollouts: v1.9.0+838d4e7
```

Both controller and dashboard pods running:

```
NAME                                       READY   STATUS    RESTARTS   AGE
argo-rollouts-79b89d8856-xx8bz             1/1     Running   0          5m
argo-rollouts-dashboard-7b7bf46775-hgzlc   1/1     Running   0          5m
```

CRDs created:

```
analysisruns.argoproj.io
analysistemplates.argoproj.io
clusteranalysistemplates.argoproj.io
experiments.argoproj.io
rollouts.argoproj.io
```

### Dashboard Access

```bash
kubectl port-forward svc/argo-rollouts-dashboard -n argo-rollouts 3100:3100
# Open http://localhost:3100
```

---

## 2. Rollout vs Deployment — Key Differences

| Feature | Deployment | Rollout |
|---|---|---|
| API group | `apps/v1` | `argoproj.io/v1alpha1` |
| Strategy | `RollingUpdate` or `Recreate` | `canary` or `blueGreen` |
| Traffic shifting | Not supported | Gradual % shifting |
| Pause steps | No | Yes — manual or timed |
| Automated rollback | No | Yes — based on analysis |
| Preview environment | No | Yes (blue-green) |
| AnalysisRun integration | No | Yes |

The pod template spec inside Rollout is identical to Deployment. Only the `strategy` block is different — Rollout has much richer options there.

---

## 3. Canary Deployment

### Strategy Configuration

The Rollout is in `k8s/devops-info-service/templates/rollout.yaml`. Enable it with `--set rollout.enabled=true --set rollout.strategy=canary`.

Canary steps configured:

```yaml
strategy:
  canary:
    steps:
      - setWeight: 20
      - pause: {}          # manual promotion required
      - setWeight: 40
      - pause: { duration: 30s }
      - setWeight: 60
      - pause: { duration: 30s }
      - setWeight: 80
      - pause: { duration: 30s }
```

This means: start at 20% canary traffic, wait for a human to approve, then automatically shift 40 → 60 → 80 → 100% with 30-second pauses between each step.

### Deploy and Test

Install:

```bash
cd k8s/devops-info-service
helm upgrade --install rollout-test . \
  --set rollout.enabled=true \
  --set rollout.strategy=canary \
  --set replicaCount=2 \
  -n default
```

Trigger a new canary by changing any value:

```bash
helm upgrade rollout-test . --set rollout.enabled=true --set rollout.strategy=canary \
  --set appEnv=canary-test -n default
```

Watch status:

```bash
kubectl-argo-rollouts get rollout rollout-test-devops-info-service -n default
```

Observed output at 20% (paused, waiting for promotion):

```
Status:        Progressing
Strategy:      Canary
  Step:        0/8
  SetWeight:   20
  ActualWeight: 0
Images:        devops-info-service:latest (canary, stable)
```

### Manual Promotion

```bash
kubectl-argo-rollouts promote rollout-test-devops-info-service -n default
```

After promotion — automatically moved to step 3/8 at 40%:

```
Status:       Paused
  Step:       3/8
  SetWeight:  40
  ActualWeight: 33
```

### Rollback Test

```bash
kubectl-argo-rollouts abort rollout-test-devops-info-service -n default
```

After abort — canary scaled down instantly, stable 100% back:

```
Status:       Degraded
Message:      RolloutAborted: Rollout aborted update to revision 2
  SetWeight:  0
  ActualWeight: 0
Images:       devops-info-service:latest (stable)
```

Retry after fixing the issue:

```bash
kubectl-argo-rollouts retry rollout rollout-test-devops-info-service -n default
```

---

## 4. Blue-Green Deployment

### Strategy Configuration

Use `--set rollout.strategy=blueGreen` to switch to blue-green mode. A preview service is automatically created by `templates/preview-service.yaml`.

```yaml
strategy:
  blueGreen:
    activeService: <release-name>-devops-info-service
    previewService: <release-name>-devops-info-service-preview
    autoPromotionEnabled: false
```

### Deploy and Test

```bash
helm upgrade --install bg-test . \
  --set rollout.enabled=true \
  --set rollout.strategy=blueGreen \
  --set rollout.blueGreen.autoPromotionEnabled=false \
  --set replicaCount=2 \
  -n default
```

Initial state — blue (revision 1) is active:

```
Status:   Healthy
Strategy: BlueGreen
Images:   devops-info-service:latest (stable, active)
```

Trigger green deployment:

```bash
helm upgrade bg-test . --set rollout.enabled=true --set rollout.strategy=blueGreen \
  --set appEnv=green-test -n default
```

Two services available:

```
bg-test-devops-info-service           ClusterIP  (active/blue)
bg-test-devops-info-service-preview   ClusterIP  (preview/green)
```

Test the preview service before promoting:

```bash
kubectl port-forward svc/bg-test-devops-info-service-preview 8081:80
curl http://localhost:8081/health
```

### Promotion

```bash
kubectl-argo-rollouts promote bg-test-devops-info-service -n default
```

After promotion — green (revision 2) becomes active instantly:

```
Status:   Healthy
Images:   devops-info-service:latest (active, stable)
# revision:2 is now active
```

### Instant Rollback

```bash
kubectl-argo-rollouts undo bg-test-devops-info-service -n default
```

Rollback is instant — no gradual traffic shifting, just an immediate selector switch back to the blue ReplicaSet.

---

## 5. Strategy Comparison

| | Canary | Blue-Green |
|---|---|---|
| Traffic shift | Gradual (20 → 40 → 60 → 80 → 100%) | Instant (0% or 100%) |
| Resource usage | ~1.5x during rollout | 2x during rollout |
| Rollback speed | Fast (traffic shifted back) | Instant (selector flip) |
| Testing | Real % of users get new version | Isolated preview environment |
| Risk | Lower — gradual exposure | Higher at cutover — but quick undo |

**When to use canary:**
- You want real user traffic to validate the new version gradually
- You have enough replicas that 20% traffic split makes sense
- You want to detect issues before full rollout

**When to use blue-green:**
- You need zero-downtime with instant cutover
- You want to test the new version in a completely isolated environment first
- Database migrations or breaking changes that don't allow mixed traffic

**My recommendation:**
- Use canary for regular application updates where gradual exposure matters
- Use blue-green for major releases or when you need a clean preview environment for QA

---

## 6. CLI Commands Reference

```bash
# Install
kubectl create namespace argo-rollouts
kubectl apply -n argo-rollouts -f https://github.com/argoproj/argo-rollouts/releases/latest/download/install.yaml
kubectl apply -n argo-rollouts -f https://github.com/argoproj/argo-rollouts/releases/latest/download/dashboard-install.yaml

# Watch rollout status
kubectl-argo-rollouts get rollout <name> -n <ns>
kubectl-argo-rollouts get rollout <name> -n <ns> -w  # watch mode

# Promote to next step (canary)
kubectl-argo-rollouts promote <name> -n <ns>

# Promote all steps at once
kubectl-argo-rollouts promote <name> -n <ns> --full

# Abort (triggers rollback)
kubectl-argo-rollouts abort <name> -n <ns>

# Retry after abort
kubectl-argo-rollouts retry rollout <name> -n <ns>

# Undo (blue-green instant rollback)
kubectl-argo-rollouts undo <name> -n <ns>

# Dashboard
kubectl port-forward svc/argo-rollouts-dashboard -n argo-rollouts 3100:3100

# List rollouts
kubectl get rollouts -n <ns>

# List analysis runs
kubectl get analysisrun -n <ns>
```

---

## 7. Bonus — Automated Analysis

### AnalysisTemplate Configuration

The template is in `k8s/devops-info-service/templates/analysis-template.yaml`. Enable with `--set rollout.analysis.enabled=true`.

```yaml
apiVersion: argoproj.io/v1alpha1
kind: AnalysisTemplate
metadata:
  name: <release>-success-rate
spec:
  metrics:
    - name: webcheck
      provider:
        web:
          url: http://<service>.<namespace>.svc/health
          jsonPath: "{$.status}"
      successCondition: result == "healthy"
      interval: 10s
      count: 3
      failureLimit: 1
```

This runs 3 HTTP checks against `/health` every 10 seconds. If more than 1 check fails, the analysis fails and the rollout is automatically rolled back.

### Integration with Canary

The analysis is injected at step 2 (`startingStep: 2`) of the canary — after the 40% weight step. This means Argo checks that the canary is healthy before allowing it to continue to 60%.

```yaml
strategy:
  canary:
    steps:
      - setWeight: 20
      - pause: {}
      - setWeight: 40
      - pause: { duration: 30s }
      ...
    analysis:
      templates:
        - templateName: <release>-success-rate
      startingStep: 2
```

### Auto-Rollback Demonstration

**Test 1 — Intentional failure (wrong success condition `"ok"` instead of `"healthy"`):**

The AnalysisRun failed because the app returns `"healthy"` but the condition checked for `"ok"`. After 2 failures (exceeding `failureLimit: 1`), Argo automatically aborted and rolled back:

```
α AnalysisRun  Failed   ✖ 2
Message: Metric "webcheck" assessed Failed due to failed (2) > failureLimit (1)
# canary ScaledDown, stable serving 100%
```

**Test 2 — Working analysis (correct `"healthy"` condition):**

After fixing the condition, the AnalysisRun passed all 3 checks and the rollout continued normally:

```
α AnalysisRun  Successful   ✔ 3
# canary progressed to 60%, 80%, 100%
```

### How Metrics Determine Success/Failure

1. Argo makes an HTTP GET to the health URL
2. Extracts the `status` field using jsonPath
3. Compares to `successCondition`
4. If the check fails more than `failureLimit` times → AnalysisRun = Failed → rollback triggered automatically
5. If all `count` checks pass → AnalysisRun = Successful → rollout continues
