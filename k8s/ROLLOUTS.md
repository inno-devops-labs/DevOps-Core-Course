# Lab 14 — Progressive Delivery with Argo Rollouts

## 1. Argo Rollouts setup

### Controller + CRDs
```bash
kubectl create namespace argo-rollouts
kubectl apply -n argo-rollouts -f https://github.com/argoproj/argo-rollouts/releases/latest/download/install.yaml
```

Installed resources include CRDs:
- `rollouts.argoproj.io`
- `analysisruns.argoproj.io`
- `analysistemplates.argoproj.io`
- `experiments.argoproj.io`

### Dashboard
```bash
kubectl apply -n argo-rollouts -f https://github.com/argoproj/argo-rollouts/releases/latest/download/dashboard-install.yaml
kubectl port-forward svc/argo-rollouts-dashboard -n argo-rollouts 3100:3100
```

### CLI plugin
```bash
brew install argoproj/tap/kubectl-argo-rollouts
kubectl argo rollouts version
```

Result:
```bash
kubectl-argo-rollouts: v1.8.3+49fa151
```

### Rollout vs Deployment (key differences)
- `kind: Rollout` instead of `kind: Deployment`.
- `spec.strategy` supports `canary` and `blueGreen` with explicit progressive steps.
- Rollout tracks stable/canary/preview ReplicaSets and can `promote`, `abort`, `undo`.
- Deployment only supports standard rolling update without progressive traffic control semantics.

## 2. Helm chart changes

Implemented in chart `k8s/devops-info`:
- Added `templates/rollout.yaml` (canary and blue-green strategies).
- Added `templates/service-preview.yaml` for blue-green preview traffic.
- Added strategy controls in `values.yaml` under `workload` and `rollout`.
- Added scenario files:
  - `values-canary.yaml`
  - `values-bluegreen.yaml`
- Kept `templates/deployment.yaml` under conditional rendering (`workload.type: deployment`) for compatibility.

## 3. Canary deployment

### Canary strategy configured
In `values.yaml` (default canary steps):
- `20%` -> `pause: {}` (manual)
- `40%` -> `pause: 30s`
- `60%` -> `pause: 30s`
- `80%` -> `pause: 30s`
- `100%`

### Install and update
```bash
helm upgrade --install rollouts-demo k8s/devops-info \
  -n rollouts-demo -f k8s/devops-info/values-canary.yaml \
  --set service.nodePort=30090

helm upgrade rollouts-demo k8s/devops-info \
  -n rollouts-demo -f k8s/devops-info/values-canary.yaml \
  --set service.nodePort=30090 --set image.tag=latest
```

Observed during rollout:
```bash
Status: ◌ Progressing
Step: 0/9
SetWeight: 20
Images: devops_lab02:cilc (stable), devops_lab02:latest (canary)
```

Manual promotion test:
```bash
kubectl argo rollouts promote rollouts-demo-devops-info -n rollouts-demo
```

After promote:
```bash
Status: ॥ Paused
Step: 3/9
SetWeight: 40
ActualWeight: 33
```

Auto progression snapshot (timed pauses):
```bash
Status: ॥ Paused
Step: 7/9
SetWeight: 80
ActualWeight: 75
```

### Abort test (rollback)
Triggered new revision and aborted:
```bash
helm upgrade rollouts-demo ... --set image.tag=v1.0.0
kubectl argo rollouts abort rollouts-demo-devops-info -n rollouts-demo
```

Result:
```bash
Status: ✖ Degraded
Message: RolloutAborted: Rollout aborted update to revision 3
```

Stable ReplicaSet remained active (traffic rolled back to stable).

## 4. Blue-green deployment

### Strategy
`values-bluegreen.yaml` uses:
- `rollout.strategy: blueGreen`
- `autoPromotionEnabled: false`
- preview service enabled (`<release>-devops-info-preview`)

### Deploy and trigger green revision
```bash
helm upgrade --install rollouts-bg k8s/devops-info \
  -n rollouts-bg -f k8s/devops-info/values-bluegreen.yaml

helm upgrade rollouts-bg k8s/devops-info \
  -n rollouts-bg -f k8s/devops-info/values-bluegreen.yaml \
  --set image.tag=latest --server-side=false
```

Note: on Helm v4, `--server-side=false` is needed here to avoid SSA conflicts on Service selectors managed by Rollouts controller.

State before promotion:
```bash
Status: ॥ Paused
Message: BlueGreenPause
Images: devops_lab02:cilc (stable, active), devops_lab02:latest (preview)
```

Service selector proof before promotion:
```bash
active hash:  b899b5bdf
preview hash: 575d44bd7f
```

### Promote green -> active
```bash
kubectl argo rollouts promote rollouts-bg-devops-info -n rollouts-bg
```

After promotion:
```bash
Status: ✔ Healthy
Images: devops_lab02:latest (stable, active)
```

Service selector proof after promotion:
```bash
active hash:  575d44bd7f
preview hash: 575d44bd7f
```

### Instant rollback test
```bash
kubectl argo rollouts undo rollouts-bg-devops-info -n rollouts-bg
```

After undo:
```bash
Status: ✔ Healthy
Images: devops_lab02:cilc (stable, active)
```

Rollback is effectively instant traffic switching between active ReplicaSets (blue-green behavior).

## 5. Strategy comparison

### Canary
Pros:
- Gradual exposure to reduce blast radius.
- Easy to pause for manual verification.
- Better fit when partial traffic progression is needed.

Cons:
- Slower release path.
- More operational steps and states to observe.

### Blue-green
Pros:
- Very fast cutover and rollback.
- Clear separation of active vs preview revision.

Cons:
- Requires extra capacity (two full stacks during switch).
- Less granular than canary.

### Recommendation
- Use canary for risky/high-impact changes requiring staged verification.
- Use blue-green for fast reversible releases where extra capacity is acceptable.

## 6. Useful CLI commands

```bash
# Observe rollout
kubectl argo rollouts get rollout <name> -n <ns>

# Watch live status
kubectl argo rollouts get rollout <name> -n <ns> -w

# Manual promotion
kubectl argo rollouts promote <name> -n <ns>

# Abort current rollout
kubectl argo rollouts abort <name> -n <ns>

# Roll back to previous revision
kubectl argo rollouts undo <name> -n <ns>

# Dashboard
kubectl argo rollouts dashboard
```
