# Argo Rollouts — Progressive Delivery (Lab 14)

This document describes the implementation of **canary** and **blue-green** strategies for the Helm chart `k8s/devops-info-service`, excluding the bonus task.

## 1. Argo Rollouts Setup

### 1.1 Installation and verification

```bash
kubectl create namespace argo-rollouts
kubectl apply -n argo-rollouts -f https://github.com/argoproj/argo-rollouts/releases/latest/download/install.yaml
kubectl apply -n argo-rollouts -f https://github.com/argoproj/argo-rollouts/releases/latest/download/dashboard-install.yaml

brew install argoproj/tap/kubectl-argo-rollouts
kubectl argo rollouts version
kubectl -n argo-rollouts rollout status deploy/argo-rollouts
kubectl get pods -n argo-rollouts
```

Cluster verification:
- `kubectl-argo-rollouts: v1.8.3+49fa151`
- `deployment "argo-rollouts" successfully rolled out`
- `argo-rollouts` and `argo-rollouts-dashboard` are in `Running` status

### 1.2 Dashboard access

```bash
kubectl port-forward svc/argo-rollouts-dashboard -n argo-rollouts 3100:3100
```

URL: `http://localhost:3100`  
HTTP check: `HTTP/1.1 302 Found` (dashboard is reachable).

### 1.3 Rollout vs Deployment

| Object | Deployment | Rollout |
|---|---|---|
| API | `apps/v1` | `argoproj.io/v1alpha1` |
| Strategies | `RollingUpdate`, `Recreate` | `canary`, `blueGreen` |
| Step-by-step rollout | No | Yes (`steps`, `pause`, `setWeight`) |
| Promote/abort | No | Yes (`promote`, `abort`, `undo`) |
| Preview service | No | Yes (blue-green) |
| Fast traffic rollback | Limited | Yes, built-in |

## 2. Canary Deployment

### 2.1 Configuration

The chart includes `templates/rollout.yaml` and the `values-canary.yaml` profile.

Key strategy:

```yaml
rollout:
  enabled: true
  strategyType: canary
  canary:
    steps:
      - setWeight: 20
      - pause: {}
      - setWeight: 40
      - pause: { duration: 30s }
      - setWeight: 60
      - pause: { duration: 30s }
      - setWeight: 80
      - pause: { duration: 30s }
      - setWeight: 100
```

### 2.2 Rollout execution and progression

```bash
helm upgrade --install devops-rollouts k8s/devops-info-service -n lab14 -f k8s/devops-info-service/values-canary.yaml
kubectl argo rollouts get rollout devops-rollouts-devops-info-service -n lab14
```

Change test:

```bash
helm upgrade devops-rollouts k8s/devops-info-service -n lab14 -f k8s/devops-info-service/values-canary.yaml --set env.DEBUG=true
kubectl argo rollouts get rollout devops-rollouts-devops-info-service -n lab14
kubectl argo rollouts promote devops-rollouts-devops-info-service -n lab14
kubectl argo rollouts status devops-rollouts-devops-info-service -n lab14 --timeout 300s
```

Observations:
- At the first step, rollout pauses at `CanaryPauseStep` (manual gate)
- After `promote`, it continues through automatic `30s` pauses
- Final status: `Healthy`, `Step: 9/9`, `SetWeight: 100`

### 2.3 Abort/rollback demonstration

```bash
helm upgrade devops-rollouts k8s/devops-info-service -n lab14 -f k8s/devops-info-service/values-canary.yaml --set env.DEBUG=false
kubectl argo rollouts abort devops-rollouts-devops-info-service -n lab14
kubectl argo rollouts get rollout devops-rollouts-devops-info-service -n lab14
```

Observation:
- After `abort`, status becomes `RolloutAborted`
- The canary RS scales down, and the stable revision keeps serving traffic

### 2.4 Dashboard screenshots (what to attach)

1. Rollout in `CanaryPauseStep` at 20%  
2. Rollout after `promote` (progressing through 40/60/80 steps)  
3. Rollout after `abort` with rollback to stable

## 3. Blue-Green Deployment

### 3.1 Configuration

The `values-bluegreen.yaml` profile and preview service support were added via `templates/service.yaml`.

Key strategy:

```yaml
rollout:
  strategyType: blueGreen
  blueGreen:
    autoPromotionEnabled: false
    scaleDownDelaySeconds: 30
    previewService:
      enabled: true
```

### 3.2 Active vs Preview service

```bash
helm upgrade devops-rollouts k8s/devops-info-service -n lab14 -f k8s/devops-info-service/values-bluegreen.yaml --set env.DEBUG=true
kubectl argo rollouts get rollout devops-rollouts-devops-info-service -n lab14
kubectl get svc devops-rollouts-devops-info-service -n lab14 -o jsonpath='{.spec.selector.rollouts-pod-template-hash}'
kubectl get svc devops-rollouts-devops-info-service-preview -n lab14 -o jsonpath='{.spec.selector.rollouts-pod-template-hash}'
```

Test observation:
- `active` selector hash: `c669c8679`
- `preview` selector hash: `75f4cd86`
- This confirms active and preview point to different ReplicaSets.

### 3.3 Promotion

```bash
kubectl argo rollouts promote devops-rollouts-devops-info-service -n lab14
kubectl argo rollouts status devops-rollouts-devops-info-service -n lab14
```

With `autoPromotionEnabled: false`, manual promotion is required.

### 3.4 Instant rollback

```bash
kubectl argo rollouts undo devops-rollouts-devops-info-service -n lab14
kubectl argo rollouts status devops-rollouts-devops-info-service -n lab14
```

Observation:
- Rollback is performed by switching service selectors to the previous stable revision
- Traffic switching is noticeably faster than step-based canary rollback

### 3.5 Dashboard screenshots (what to attach)

1. `preview` state before promote  
2. Active service switch after promote  
3. Fast rollback after `undo`

## 4. Strategy Comparison

| Criterion | Canary | Blue-Green |
|---|---|---|
| Traffic switching | Gradual (percent-based) | Instant (all-or-nothing) |
| Risk | Lower during rollout | Lower during rollback |
| Resources | More efficient | Requires 2 environments during deployment |
| Control | Fine-grained step control | Simple manual gate |
| Best use case | High-traffic production, sensitive releases | Critical releases requiring instant rollback |

Recommendations:
- **Canary**: when gradual validation under real traffic is important.
- **Blue-Green**: when rollback speed and strict old/new separation are critical.

## 5. CLI Commands Reference

Main commands:

```bash
# Rollout visibility
kubectl argo rollouts get rollout <name> -n <ns>
kubectl argo rollouts status <name> -n <ns>
kubectl argo rollouts history <name> -n <ns>

# Rollout control
kubectl argo rollouts promote <name> -n <ns>
kubectl argo rollouts abort <name> -n <ns>
kubectl argo rollouts undo <name> -n <ns>
kubectl argo rollouts retry rollout <name> -n <ns>

# Dashboard
kubectl port-forward svc/argo-rollouts-dashboard -n argo-rollouts 3100:3100

# Blue-green service checks
kubectl get svc <active-service> -n <ns> -o yaml
kubectl get svc <preview-service> -n <ns> -o yaml
```

Troubleshooting:
- `Paused`: expected for manual gates (`pause: {}` or `autoPromotionEnabled: false`).
- `RolloutAborted`: expected after `abort`; resume with `retry rollout`.
- Blue-green Service selector conflicts are avoided by letting the Rollouts controller manage selectors instead of Helm templates.
