# Lab 14 — Progressive Delivery with Argo Rollouts

## Overview

This lab implements progressive delivery strategies using Argo Rollouts for the `devops-info-service` Helm chart. The existing `Deployment` is replaced by an Argo `Rollout` CRD that supports canary and blue-green deployment strategies with traffic shifting and automated rollback.

---

## Task 1 — Argo Rollouts Setup

### Installation

```bash
# Create namespace
kubectl create namespace argo-rollouts

# Install controller
kubectl apply -n argo-rollouts -f https://github.com/argoproj/argo-rollouts/releases/latest/download/install.yaml

# Install dashboard
kubectl apply -n argo-rollouts -f https://github.com/argoproj/argo-rollouts/releases/latest/download/dashboard-install.yaml

# Verify controller is running
kubectl get pods -n argo-rollouts
# NAME                                 READY   STATUS    RESTARTS   AGE
# argo-rollouts-5d6d8b9b7c-xk9p2       1/1     Running   0          30s
```

### kubectl plugin (Linux)

```bash
curl -LO https://github.com/argoproj/argo-rollouts/releases/latest/download/kubectl-argo-rollouts-linux-amd64
chmod +x kubectl-argo-rollouts-linux-amd64
sudo mv kubectl-argo-rollouts-linux-amd64 /usr/local/bin/kubectl-argo-rollouts

kubectl argo rollouts version
# kubectl-argo-rollouts: v1.7.x
```

### Dashboard Access

```bash
kubectl port-forward svc/argo-rollouts-dashboard -n argo-rollouts 3100:3100
# Open http://localhost:3100
```

### Rollout vs Deployment — Key Differences

| Feature | Deployment | Rollout |
|---------|-----------|---------|
| `apiVersion` | `apps/v1` | `argoproj.io/v1alpha1` |
| `kind` | `Deployment` | `Rollout` |
| Strategy | `RollingUpdate`, `Recreate` | `canary`, `blueGreen` |
| Traffic shifting | Not supported | Percentage-based via `setWeight` |
| Pause/Resume | Not supported | `pause: {}` (manual) or `pause: {duration: Xs}` |
| Analysis | Not supported | `AnalysisTemplate` integration |
| Rollback | kubectl rollout undo | kubectl argo rollouts abort / undo |
| Preview environment | Not supported | Preview service (blue-green) |

Both share the same pod template (`spec.template`) structure — migrating from Deployment to Rollout only requires changing `apiVersion`, `kind`, and replacing `strategy` with the Argo Rollouts strategy block.

---

## Task 2 — Canary Deployment

### Strategy Configuration

The canary strategy progressively shifts traffic from the stable (current) version to the canary (new) version through defined steps:

```yaml
# values-canary.yaml
rollout:
  enabled: true
  strategy: canary
  canary:
    steps:
      - setWeight: 20    # 20% to canary
      - pause: {}        # Manual promotion required
      - setWeight: 40    # 40% to canary (auto after promotion)
      - pause:
          duration: "30s"
      - setWeight: 60
      - pause:
          duration: "30s"
      - setWeight: 80
      - pause:
          duration: "30s"
      # 100% — rollout complete
```

### Deployment and Testing

```bash
# Deploy with canary strategy
helm upgrade --install devops-info-service ./k8s/devops-info-service \
  -f ./k8s/devops-info-service/values.yaml \
  -f ./k8s/devops-info-service/values-canary.yaml

# Watch rollout status
kubectl argo rollouts get rollout devops-info-service-devops-info-service -w

# Trigger a new rollout (change image tag)
kubectl argo rollouts set image devops-info-service-devops-info-service \
  devops-info-service=th1ef/devops-info-service:v2
```

### Rollout Progression

After triggering a new deployment, the rollout pauses at the first step (20% canary traffic):

```
Name:            devops-info-service-devops-info-service
Namespace:       default
Status:          ॥ Paused
Message:         CanaryPauseStep
Strategy:        Canary
  Step:          1/8
  SetWeight:     20
  ActualWeight:  20

Replicas:
  Desired:       3
  Current:       3
  Updated:       1  ← canary replica
  Ready:         3
  Available:     3

NAME                                                     KIND        STATUS     AGE  INFO
⟳ devops-info-service-devops-info-service                Rollout     ॥ Paused   2m
├──# revision:2                                          CanarySet   ✔ Healthy  30s  canary
│  └──□ devops-info-service-devops-info-service-xxx      Pod         ✔ Running  30s  canary
└──# revision:1                                          ReplicaSet  ✔ Healthy  2m   stable
   ├──□ devops-info-service-devops-info-service-yyy      Pod         ✔ Running  2m
   └──□ devops-info-service-devops-info-service-zzz      Pod         ✔ Running  2m
```

### Manual Promotion

```bash
# Promote to next step (20% → 40%)
kubectl argo rollouts promote devops-info-service-devops-info-service

# Subsequent steps auto-advance after 30s pause
# Status: 40% → wait 30s → 60% → wait 30s → 80% → wait 30s → 100%
```

### Abort and Rollback

```bash
# Abort during rollout — traffic instantly returns to stable
kubectl argo rollouts abort devops-info-service-devops-info-service

# Status changes to Degraded — retry to restore healthy state
kubectl argo rollouts retry rollout devops-info-service-devops-info-service
```

After abort, the canary replica set is scaled down and 100% traffic returns to the stable version immediately.

---

## Task 3 — Blue-Green Deployment

### Strategy Configuration

Blue-green maintains two full environments simultaneously — `active` (production) and `preview` (new version):

```yaml
# values-bluegreen.yaml
rollout:
  enabled: true
  strategy: blueGreen
  blueGreen:
    autoPromotionEnabled: false  # Manual promotion required

service:
  type: NodePort
  port: 80
  targetPort: 5000
  nodePort: 30080       # active service
  previewNodePort: 30081  # preview service
```

Two Kubernetes Services are created:
- **`devops-info-service-devops-info-service`** — active service (production traffic)
- **`devops-info-service-devops-info-service-preview`** — preview service (new version testing)

### Deployment and Testing

```bash
# Deploy with blue-green strategy
helm upgrade --install devops-info-service ./k8s/devops-info-service \
  -f ./k8s/devops-info-service/values.yaml \
  -f ./k8s/devops-info-service/values-bluegreen.yaml

# Trigger update
kubectl argo rollouts set image devops-info-service-devops-info-service \
  devops-info-service=th1ef/devops-info-service:v2

# Watch status
kubectl argo rollouts get rollout devops-info-service-devops-info-service -w
```

### Blue-Green Flow

```
Status:          ॥ Paused
Message:         BlueGreenPause
Strategy:        BlueGreen
  ActiveService: devops-info-service-devops-info-service
  PreviewService: devops-info-service-devops-info-service-preview

NAME                                                  KIND        STATUS     INFO
⟳ devops-info-service-devops-info-service             Rollout     ॥ Paused
├──# revision:2                                       ReplicaSet  ✔ Healthy  preview
│  └──□ devops-info-service-xxx (v2)                  Pod         ✔ Running
└──# revision:1                                       ReplicaSet  ✔ Healthy  active
   ├──□ devops-info-service-yyy (v1)                  Pod         ✔ Running
   └──□ devops-info-service-zzz (v1)                  Pod         ✔ Running
```

Access both versions simultaneously:

```bash
# Test new version via preview service
kubectl port-forward svc/devops-info-service-devops-info-service-preview 8081:80
curl http://localhost:8081/

# Production traffic still on v1
kubectl port-forward svc/devops-info-service-devops-info-service 8080:80
curl http://localhost:8080/
```

### Promotion and Instant Rollback

```bash
# Promote preview → active (instant traffic switch)
kubectl argo rollouts promote devops-info-service-devops-info-service

# Rollback — undo restores previous active revision instantly
kubectl argo rollouts undo devops-info-service-devops-info-service
```

The switch from blue to green (or rollback) is **instant** — Argo Rollouts updates the Service selector to point to the new ReplicaSet. No traffic is gradually shifted.

---

## Task 4 — Strategy Comparison

### Canary vs Blue-Green

| Aspect | Canary | Blue-Green |
|--------|--------|-----------|
| **Traffic model** | Percentage split (20% → 40% → ... → 100%) | Full switch (0% → 100%) |
| **Resources** | Shared — only canary pods are extra | 2× resources during deployment |
| **Rollback speed** | Fast (seconds) | Instant (service selector update) |
| **Risk exposure** | Gradual — only a subset of users see new version | All-or-nothing after promotion |
| **Preview testing** | Traffic sampling | Full isolated preview environment |
| **Rollback complexity** | Scales down canary, redirects traffic | Flip service selector back |
| **Best for** | High-risk changes, A/B testing, gradual validation | Zero-downtime deploys, QA testing before go-live |

### Recommendations

**Use Canary when:**
- Validating a new feature with real user traffic (e.g., 5% of users)
- Monitoring error rates / latency before full rollout
- Incremental rollouts tied to metrics (via AnalysisTemplate)

**Use Blue-Green when:**
- You need a full staging environment before production
- Rollback must be instantaneous (e.g., financial systems)
- Database schema changes are coordinated with app deployment

---

## CLI Commands Reference

```bash
# --- Status and Monitoring ---
kubectl argo rollouts list rollouts
kubectl argo rollouts get rollout <name> -w
kubectl argo rollouts status <name>

# --- Canary Control ---
kubectl argo rollouts promote <name>           # Advance to next step
kubectl argo rollouts promote <name> --full    # Skip all steps, go to 100%
kubectl argo rollouts abort <name>             # Abort, return to stable
kubectl argo rollouts retry rollout <name>     # Retry aborted rollout

# --- Blue-Green Control ---
kubectl argo rollouts promote <name>           # Switch preview → active
kubectl argo rollouts undo <name>              # Rollback to previous revision

# --- Image Update ---
kubectl argo rollouts set image <name> <container>=<image>:<tag>

# --- Dashboard ---
kubectl port-forward svc/argo-rollouts-dashboard -n argo-rollouts 3100:3100
```

---

## Bonus — Automated Analysis

The `AnalysisTemplate` performs automated health checks during a canary rollout. If the health endpoint returns unexpected results, the rollout is automatically aborted.

### AnalysisTemplate

```yaml
# templates/analysis-template.yaml (rendered when analysis.enabled=true)
apiVersion: argoproj.io/v1alpha1
kind: AnalysisTemplate
metadata:
  name: devops-info-service-success-rate
spec:
  metrics:
    - name: health-check
      provider:
        web:
          url: "http://devops-info-service.default.svc/health"
          jsonPath: "{$.status}"
      successCondition: result == "ok"
      interval: 10s
      count: 3
      failureLimit: 1
```

### Canary with Analysis

```yaml
# values-canary-analysis.yaml
rollout:
  enabled: true
  strategy: canary
  canary:
    steps:
      - setWeight: 20
      - pause: {}
      - setWeight: 50
      - pause:
          duration: "30s"
      - setWeight: 100

analysis:
  enabled: true
```

The analysis runs starting from step 1. It polls `/health` every 10 seconds, 3 times. If more than 1 check fails, the rollout is automatically aborted and traffic returns to the stable version.

### Deploy with Analysis

```bash
helm upgrade --install devops-info-service ./k8s/devops-info-service \
  -f ./k8s/devops-info-service/values.yaml \
  -f ./k8s/devops-info-service/values-canary-analysis.yaml

# Watch analysis runs
kubectl get analysisrun
kubectl argo rollouts get rollout devops-info-service-devops-info-service -w
```

### Auto-Rollback on Failure

If the health check fails (e.g., the new image returns 500 or `/health` returns `{"status": "error"}`):

```
Status:     ✖ Degraded
Message:    RolloutAborted: Metric "health-check" assessed Failed due to failed (1) > failureLimit (1)
```

The rollout is automatically aborted and all traffic returns to the stable version — no manual intervention required.
