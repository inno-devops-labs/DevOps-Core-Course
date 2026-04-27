# LAB14 - Progressive Delivery with Argo Rollouts

Cluster: `minikube`  
Controller namespace: `argo-rollouts`

## 1. Argo Rollouts Setup

### 1.1 Controller and CRDs installation

Commands used:

```bash
kubectl create namespace argo-rollouts
kubectl apply -n argo-rollouts -f /tmp/argo-rollouts-install.yaml
kubectl apply -n argo-rollouts -f /tmp/argo-rollouts-dashboard-install.yaml
```

Verification:

```text
deployment.apps/argo-rollouts             1/1 available
deployment.apps/argo-rollouts-dashboard   1/1 available
service/argo-rollouts-dashboard           ClusterIP 3100/TCP
service/argo-rollouts-metrics             ClusterIP 8090/TCP
```

Installed CRDs:

```text
rollouts.argoproj.io
analysisruns.argoproj.io
analysistemplates.argoproj.io
experiments.argoproj.io
```

### 1.2 kubectl plugin

Installed binary:

```bash
~/.local/bin/kubectl-argo-rollouts
```

Verification:

```text
kubectl-argo-rollouts: v1.9.0+838d4e7
```

### 1.3 Dashboard access

Command:

```bash
kubectl port-forward svc/argo-rollouts-dashboard -n argo-rollouts 3100:3100
```

Observed:

```text
Forwarding from 127.0.0.1:3100 -> 3100
```

URL: `http://localhost:3100`

## 2. Rollout vs Deployment

`Rollout` keeps Deployment-like structure (`replicas`, `selector`, `template`) and adds progressive-delivery strategy fields:

- `spec.strategy.canary.steps` for staged traffic shifts and pauses
- `spec.strategy.blueGreen.activeService` / `previewService`
- promotion/abort/undo workflow via Argo Rollouts controller and CLI

In this chart:

- Added `k8s/devops-info/templates/rollout.yaml` (`kind: Rollout`)
- Kept `deployment.yaml` as fallback only when `rollout.enabled=false`
- Added `service-preview.yaml` for blue-green preview traffic

## 3. Canary Deployment

### 3.1 Canary configuration

Chart values:

```yaml
rollout:
  enabled: true
  strategy: canary
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

Canary test values file: `k8s/devops-info/values-rollout-canary.yaml`

### 3.2 Deploy and progression test

Commands:

```bash
kubectl create namespace rollouts-canary
helm upgrade --install canary-lab k8s/devops-info -n rollouts-canary -f k8s/devops-info/values-rollout-canary.yaml
helm upgrade canary-lab k8s/devops-info -n rollouts-canary -f k8s/devops-info/values-rollout-canary.yaml --set env.RELEASE_VERSION=canary-v2
kubectl argo rollouts get rollout canary-lab-devops-info -n rollouts-canary
kubectl argo rollouts promote canary-lab-devops-info -n rollouts-canary
kubectl argo rollouts status canary-lab-devops-info -n rollouts-canary --timeout 300s
```

Observed rollout pause at first manual step:

```text
Status: Paused
Message: CanaryPauseStep
Step: 1/9
SetWeight: 20
ActualWeight: 25
```

Note: with 3 replicas, 20% maps to nearest practical pod split (1/4 ~= 25%) during surge.

After manual promote, rollout continued through timed pauses and finished Healthy at step `9/9`.

### 3.3 Abort / rollback test

Commands:

```bash
helm upgrade canary-lab k8s/devops-info -n rollouts-canary -f k8s/devops-info/values-rollout-canary.yaml --set env.RELEASE_VERSION=canary-v3
kubectl argo rollouts abort canary-lab-devops-info -n rollouts-canary
kubectl argo rollouts get rollout canary-lab-devops-info -n rollouts-canary
```

Observed:

```text
Status: Degraded
Message: RolloutAborted: Rollout aborted update to revision 3
SetWeight: 0
ActualWeight: 0
```

This confirms traffic returned to stable revision immediately on abort.

Final cleanup back to healthy stable state:

```bash
kubectl argo rollouts undo canary-lab-devops-info -n rollouts-canary
```

## 4. Blue-Green Deployment

### 4.1 Blue-green configuration

Values (`k8s/devops-info/values-rollout-bluegreen.yaml`):

```yaml
rollout:
  enabled: true
  strategy: blueGreen
  blueGreen:
    autoPromotionEnabled: false
```

Strategy fields in rollout template:

- `activeService: <release>-devops-info`
- `previewService: <release>-devops-info-preview`
- manual promotion (`autoPromotionEnabled=false`)

### 4.2 Blue-green flow (preview and promote)

Commands:

```bash
kubectl create namespace rollouts-bg
helm upgrade --install bg-lab k8s/devops-info -n rollouts-bg -f k8s/devops-info/values-rollout-bluegreen.yaml
helm upgrade bg-lab k8s/devops-info -n rollouts-bg -f k8s/devops-info/values-rollout-bluegreen.yaml --set env.RELEASE_VERSION=green-v2
kubectl argo rollouts get rollout bg-lab-devops-info -n rollouts-bg
kubectl argo rollouts promote bg-lab-devops-info -n rollouts-bg
```

Before promotion:

```text
Status: Paused
Message: BlueGreenPause
active_hash=797899b8b9
preview_hash=5488c554c9
```

After promotion:

```text
active_hash=5488c554c9
preview_hash=5488c554c9
Status: Healthy
```

### 4.3 Preview vs active validation

Triggered another revision (`green-v3`) and validated service routing:

```text
active_hash=797899b8b9
preview_hash=6489dc4d87
active_endpoints=10.244.0.49 10.244.0.50 10.244.0.52
preview_endpoints=10.244.0.56 10.244.0.57 10.244.0.58
```

Both services were reachable:

```text
active_health={"status":"healthy",...,"uptime_seconds":101}
preview_health={"status":"healthy",...,"uptime_seconds":7}
```

Different uptime confirms traffic to different pod sets (stable vs preview).

### 4.4 Instant rollback behavior

Commands:

```bash
kubectl argo rollouts undo bg-lab-devops-info -n rollouts-bg
kubectl argo rollouts get rollout bg-lab-devops-info -n rollouts-bg
```

Observed immediate selector switch back:

```text
active_hash=797899b8b9
preview_hash=797899b8b9
```

Blue-green rollback is effectively instant service-pointer switch, unlike canary’s staged rollback behavior.

## 5. Strategy Comparison

### 5.1 Canary

Pros:
- gradual exposure and lower blast radius
- better for risky changes and progressive validation

Cons:
- slower rollout/rollback
- more operational complexity (steps, pauses, promotion logic)

Best for:
- high-risk app changes
- user-facing features requiring progressive confidence

### 5.2 Blue-Green

Pros:
- simple operational model
- near-instant promotion and rollback by service switch

Cons:
- requires duplicate capacity during transition
- all-or-nothing traffic switch at promotion time

Best for:
- infrastructure/config changes needing quick fallback
- release windows where fast rollback is critical

### 5.3 Recommendation

- Use **canary** for high-risk incremental rollouts.
- Use **blue-green** for fast cutover and fastest rollback.

## 6. CLI Commands Reference

```bash
# Install checks
kubectl argo rollouts version
kubectl get deploy,pods,svc -n argo-rollouts

# Dashboard
kubectl port-forward svc/argo-rollouts-dashboard -n argo-rollouts 3100:3100

# Inspect rollout
kubectl argo rollouts get rollout <name> -n <ns>
kubectl argo rollouts status <name> -n <ns> --timeout 300s

# Progression controls
kubectl argo rollouts promote <name> -n <ns>
kubectl argo rollouts abort <name> -n <ns>
kubectl argo rollouts undo <name> -n <ns>

# Service/hash checks
kubectl get svc -n <ns> <active-svc> <preview-svc> -o wide
kubectl get endpoints -n <ns> <svc>
```

## 7. Screenshots

3.png
4.png
5.png
6.png



