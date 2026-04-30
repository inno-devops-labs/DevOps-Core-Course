# Lab 14 - Progressive Delivery with Argo Rollouts

Validated locally on April 30, 2026 against the `kind-devops-lab9` cluster.

## Argo Rollouts Setup

Controller and dashboard were installed in the dedicated namespace:

```bash
kubectl get deploy,pods,svc -n argo-rollouts
kubectl get crd rollouts.argoproj.io analysistemplates.argoproj.io analysisruns.argoproj.io
/tmp/kubectl-argo-rollouts version
```

Observed state:

- controller: `quay.io/argoproj/argo-rollouts:v1.9.0`, `1/1` available
- dashboard: `quay.io/argoproj/kubectl-argo-rollouts:v1.9.0`, `1/1` available
- CLI plugin: `kubectl-argo-rollouts v1.9.0`, downloaded to `/tmp/kubectl-argo-rollouts`
- dashboard access: `kubectl port-forward svc/argo-rollouts-dashboard -n argo-rollouts 3100:3100`
- dashboard HTTP check: `curl -sI http://127.0.0.1:3100/` returned `302 Found` to `/rollouts/`
- dashboard screenshots:
  - `k8s/docs/screenshots/lab14-dashboard-canary.png`
  - `k8s/docs/screenshots/lab14-dashboard-bluegreen.png`
  - `k8s/docs/screenshots/lab14-dashboard-rollouts.png`

## Rollout vs Deployment

The Python Helm chart keeps the legacy `Deployment` path for earlier labs, but Lab 14 profiles enable Argo Rollouts:

- legacy deployment: `rollout.enabled=false` renders `templates/deployment.yaml`
- progressive delivery: `rollout.enabled=true` renders `templates/rollout.yaml`
- canary analysis: `templates/analysis-template.yaml`
- blue-green preview service: `templates/preview-service.yaml`

Key differences from `apps/v1 Deployment`:

- `apiVersion: argoproj.io/v1alpha1`, `kind: Rollout`
- `spec.strategy.canary.steps` supports weights, pauses, and analysis gates
- `spec.strategy.blueGreen` manages active and preview services
- `AnalysisTemplate` can block or fail a rollout based on live checks
- rollback is controlled through Argo Rollouts commands, not only `kubectl rollout`

## Canary Deployment

Canary profile:

```bash
helm upgrade --install lab14-canary k8s/devops-info-python \
  --namespace lab14-rollouts \
  --create-namespace \
  -f k8s/devops-info-python/values-rollout-canary.yaml \
  --wait \
  --timeout 5m
```

The canary profile uses 5 replicas and disables the Lab 12 single-writer PVC so traffic splitting is visible and safe:

- 20% canary, then manual pause
- web analysis gate against `/health`
- 40%, pause 30s
- 60%, pause 30s
- 80%, pause 30s
- 100%
- active service type: `ClusterIP`; use `kubectl port-forward` for local access to avoid NodePort collisions in shared lab clusters

Trigger a canary update:

```bash
helm upgrade lab14-canary k8s/devops-info-python \
  --namespace lab14-rollouts \
  --reuse-values \
  --set config.logLevel=DEBUG

/tmp/kubectl-argo-rollouts get rollout lab14-canary-devops-info-python -n lab14-rollouts
```

Observed evidence:

- manual gate reached `Step: 1/10`, `SetWeight: 20`, `ActualWeight: 20`
- canary ReplicaSet had 1 pod, stable ReplicaSet had 4 pods
- promotion command: `/tmp/kubectl-argo-rollouts promote lab14-canary-devops-info-python -n lab14-rollouts`
- `AnalysisRun lab14-canary-devops-info-python-7fddff446b-2-2` completed `Successful` with 3 checks
- rollout advanced to 40% and paused at the timed pause

Rollback test:

```bash
/tmp/kubectl-argo-rollouts abort lab14-canary-devops-info-python -n lab14-rollouts
```

Observed rollback state:

- rollout moved to `Degraded` with `RolloutAborted`
- `SetWeight: 0`, `ActualWeight: 0`
- stable ReplicaSet returned to 5/5
- canary ReplicaSet scaled down to 0

## Blue-Green Deployment

Blue-green profile:

```bash
helm upgrade --install lab14-bluegreen k8s/devops-info-python \
  --namespace lab14-rollouts \
  -f k8s/devops-info-python/values-rollout-bluegreen.yaml \
  --wait \
  --timeout 5m
```

Strategy configuration:

- `activeService`: `lab14-bluegreen-devops-info-python`
- `previewService`: `lab14-bluegreen-devops-info-python-preview`
- `autoPromotionEnabled: false`
- `previewReplicaCount: 1`
- pre-promotion analysis checks the preview service `/health`
- active and preview services use `ClusterIP`; local access is via `kubectl port-forward`

The active service serves production traffic. The preview service is internal-only and points at the new ReplicaSet before promotion. Argo Rollouts owns the service selectors after installation by adding `rollouts-pod-template-hash`.

Helm 4 note: because Helm uses server-side apply, the chart preserves live blue-green service selectors with `lookup` on upgrades. Without that, Helm conflicts with the `rollouts-controller` field manager for `.spec.selector`.
If a previous manual `kubectl argo rollouts` operation owns fields in managedFields, rerun the Helm upgrade with `--force-conflicts` after checking the rendered manifest.

Trigger a blue-green update:

```bash
helm upgrade lab14-bluegreen k8s/devops-info-python \
  --namespace lab14-rollouts \
  -f k8s/devops-info-python/values-rollout-bluegreen.yaml \
  --set config.logLevel=DEBUG
```

Preview and active service checks:

```bash
kubectl run preview-check -n lab14-rollouts --rm -i --restart=Never \
  --image=busybox:1.36.1 -- \
  wget -qO- http://lab14-bluegreen-devops-info-python-preview/health

kubectl run active-check -n lab14-rollouts --rm -i --restart=Never \
  --image=busybox:1.36.1 -- \
  wget -qO- http://lab14-bluegreen-devops-info-python/health
```

Observed evidence:

- preview and active services both returned `{"status":"healthy"}`
- active and preview responses had different uptimes, proving they reached different ReplicaSets
- `AnalysisRun lab14-bluegreen-devops-info-python-6bdb967c78-3-pre` completed `Successful`
- rollout paused at `BlueGreenPause` until manual promotion

Promotion:

```bash
/tmp/kubectl-argo-rollouts promote lab14-bluegreen-devops-info-python -n lab14-rollouts
```

After promotion, the active service selector switched to the new hash:

```text
rollouts-pod-template-hash=6bdb967c78
```

Rollback:

```bash
/tmp/kubectl-argo-rollouts undo lab14-bluegreen-devops-info-python -n lab14-rollouts
/tmp/kubectl-argo-rollouts promote lab14-bluegreen-devops-info-python -n lab14-rollouts --full
```

Because `autoPromotionEnabled=false`, `undo` creates the rollback candidate as preview first. `promote --full` performs the instant active-service switch back. The active service selector changed to the rollback hash:

```text
rollouts-pod-template-hash=768d967d74
```

## Automated Analysis

The chart defines a reusable web `AnalysisTemplate`:

- provider: `web`
- URL argument: active service for canary, preview service for blue-green
- JSON path: `{$.status}`
- success condition: `result == 'healthy'`
- interval: `10s`
- count: `3`
- failure limit: `1`

Canary integrates this template as an analysis step after the first manual 20% gate. Blue-green integrates it as `prePromotionAnalysis` before the preview ReplicaSet can be promoted.

Intentional failure test:

```bash
helm upgrade lab14-canary k8s/devops-info-python \
  --namespace lab14-rollouts \
  --reuse-values \
  --set analysis.successCondition="result == 'intentional-fail'" \
  --set config.logLevel=TRACE
```

Expected result: the AnalysisRun fails after the failure limit and the rollout is marked degraded; use `abort`, `retry`, or `undo` depending on whether the candidate should be discarded or retried.

Observed evidence:

- `kubectl get analysisruns -n lab14-rollouts` showed a new run for `lab14-canary-devops-info-python` in `Failed` phase
- `/tmp/kubectl-argo-rollouts get rollout lab14-canary-devops-info-python -n lab14-rollouts` showed `Degraded` with failed analysis condition
- `kubectl describe analysisrun -n lab14-rollouts <failed-analysisrun-name>` showed metric evaluations failing the condition `result == 'intentional-fail'` until failure limit was reached

## Strategy Comparison

Use canary when:

- you want gradual exposure and time to observe metrics
- mixed old/new traffic is acceptable
- you can tolerate slower rollout and rollback than blue-green

Canary tradeoffs:

- lower extra capacity than blue-green
- safer incremental blast radius
- rollback still has to shift/scaleback canary pods
- without a traffic router, percentage is approximated by replica counts

Use blue-green when:

- you need a full preview environment before switching users
- rollback speed is more important than gradual exposure
- the app can temporarily run duplicate capacity

Blue-green tradeoffs:

- fast active-service switch
- easy preview validation
- needs extra capacity for active plus preview pods
- all users switch at once after promotion

Recommendation:

- dev/staging: blue-green with manual promotion for clear preview checks
- production web services: canary with automated analysis for lower blast radius
- urgent rollback-sensitive services: blue-green, with enough capacity reserved

## CLI Reference

```bash
# Controller and dashboard
kubectl get deploy,pods,svc -n argo-rollouts
kubectl port-forward svc/argo-rollouts-dashboard -n argo-rollouts 3100:3100

# Render and validate chart
helm lint k8s/devops-info-python
helm template lab14-canary k8s/devops-info-python -f k8s/devops-info-python/values-rollout-canary.yaml
helm template lab14-bluegreen k8s/devops-info-python -f k8s/devops-info-python/values-rollout-bluegreen.yaml

# Rollout status
/tmp/kubectl-argo-rollouts get rollout lab14-canary-devops-info-python -n lab14-rollouts
/tmp/kubectl-argo-rollouts get rollout lab14-bluegreen-devops-info-python -n lab14-rollouts
kubectl get rollout,analysisruns,analysistemplates,rs,pods,svc -n lab14-rollouts

# Promotion and rollback
/tmp/kubectl-argo-rollouts promote lab14-canary-devops-info-python -n lab14-rollouts
/tmp/kubectl-argo-rollouts abort lab14-canary-devops-info-python -n lab14-rollouts
/tmp/kubectl-argo-rollouts promote lab14-bluegreen-devops-info-python -n lab14-rollouts
/tmp/kubectl-argo-rollouts undo lab14-bluegreen-devops-info-python -n lab14-rollouts
/tmp/kubectl-argo-rollouts promote lab14-bluegreen-devops-info-python -n lab14-rollouts --full
```
