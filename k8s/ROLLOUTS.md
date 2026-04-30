# Argo Rollouts for DevOps Info Service

This document describes the completed Lab 14 implementation in `k8s/devops-info-service` and the bonus task with automated analysis. The chart was not only rendered locally with Helm, but also verified in a live Kind cluster with the Argo Rollouts controller and dashboard.

## 1. What Was Implemented

The existing Helm chart now supports three modes:

- Base mode: regular Kubernetes `Deployment` when `rollout.enabled: false`
- Production mode: canary `Rollout` with weighted progression and automated analysis
- Development mode: blue-green `Rollout` with preview service and manual promotion

The main chart changes are:

- `templates/rollout.yaml`: renders a `Rollout` instead of a `Deployment` when progressive delivery is enabled
- `templates/analysis-template.yaml`: renders the bonus `AnalysisTemplate` for canary analysis
- `templates/service.yaml`: creates rollout-aware services for canary and blue-green strategies
- `values-prod.yaml`: enables canary rollout
- `values-dev.yaml`: enables blue-green rollout
- `values-analysis-fail.yaml`: forces a failing analysis path for the bonus rollback scenario
- `values-prod-update.yaml` and `values-dev-update.yaml`: provide reproducible application changes that create new revisions during live tests

## 2. Argo Rollouts Setup

### 2.1 Controller

```bash
kubectl create namespace argo-rollouts
kubectl apply -n argo-rollouts -f https://github.com/argoproj/argo-rollouts/releases/latest/download/install.yaml
kubectl get pods -n argo-rollouts
```

### 2.2 kubectl plugin

The `kubectl-argo-rollouts` plugin was installed and used for all rollout operations:

```bash
kubectl argo rollouts version
```

### 2.3 Dashboard

The dashboard was installed and used to inspect rollout state and analysis runs:

```bash
kubectl apply -n argo-rollouts -f https://github.com/argoproj/argo-rollouts/releases/latest/download/dashboard-install.yaml
kubectl port-forward svc/argo-rollouts-dashboard -n argo-rollouts 3100:3100
```

Additional dashboard sessions were also opened via:

```bash
kubectl argo rollouts dashboard -n prod --port 3101
kubectl argo rollouts dashboard -n dev --port 3102
```

## 3. Local Helm Verification

The chart passed static validation:

```bash
helm lint k8s/devops-info-service
helm template lab14-base k8s/devops-info-service -n default
helm template lab14-prod k8s/devops-info-service -n prod -f k8s/devops-info-service/values-prod.yaml
helm template lab14-dev k8s/devops-info-service -n dev -f k8s/devops-info-service/values-dev.yaml
helm template lab14-fail k8s/devops-info-service -n prod -f k8s/devops-info-service/values-prod.yaml -f k8s/devops-info-service/values-analysis-fail.yaml
```

Verified render results:

- Base profile renders a regular `Deployment`
- Production profile renders a `Rollout` and an `AnalysisTemplate`
- Development profile renders a `Rollout` and a preview service
- Failure overlay rewrites the analysis path to `/does-not-exist`

## 4. Canary Rollout in `prod`

### 4.1 Strategy

The production profile uses:

- `replicaCount: 5`
- canary weights `20 -> 40 -> 60 -> 80 -> 100`
- one manual pause at 20%
- timed pauses at the next stages
- automated analysis against the canary-only service

The analysis step is rendered from the chart configuration and inserted through `rollout.analysis.stepIndex`, so it is no longer hard-coded in the template.

### 4.2 Initial deployment

For the live cluster run I used a NodePort override because ports `30090/30091` were already occupied by previous labs:

```bash
helm upgrade --install lab14-prod k8s/devops-info-service \
  -n prod \
  -f k8s/devops-info-service/values-prod.yaml \
  --set service.nodePort=30191 \
  --set hooks.enabled=false
```

Notes:

- `hooks.enabled=false` was used for live verification to isolate Lab 14 rollout behavior from the older post-install Job logic inherited from previous labs
- the chart still contains the hook template, and it was improved to retry its health check instead of failing immediately

### 4.3 Reproducible update

The production update overlay changes the application metadata and release track so that Helm creates a new ReplicaSet:

```bash
helm upgrade lab14-prod k8s/devops-info-service \
  -n prod \
  -f k8s/devops-info-service/values-prod.yaml \
  -f k8s/devops-info-service/values-prod-update.yaml \
  --set service.nodePort=30191 \
  --set hooks.enabled=false
```

`values-prod-update.yaml` changes the service version to `1.1.0` and release track to `prod-canary-v2`.

### 4.4 Successful canary flow

Observed during the live run:

1. The rollout paused at the manual `20%` canary step
2. After manual promotion, the `AnalysisRun` started successfully
3. The analysis completed successfully against the canary service
4. The rollout continued through `40%`, `60%`, `80%`, and `100%`
5. The rollout finished in `Healthy` state

Commands used:

```bash
kubectl argo rollouts get rollout lab14-prod-devops-info-service -n prod -w
kubectl argo rollouts promote lab14-prod-devops-info-service -n prod
```

At the successful point the rollout tree showed:

- a healthy stable revision based on the updated ReplicaSet
- a successful `AnalysisRun`
- full promotion to 100%

### 4.5 Abort scenario

I also verified explicit abort behavior on a live in-progress update:

```bash
kubectl argo rollouts abort lab14-prod-devops-info-service -n prod
```

Observed result:

- the rollout entered `RolloutAborted`
- the previous stable revision remained healthy
- no broken traffic cutover occurred

## 5. Blue-Green Rollout in `dev`

### 5.1 Initial deployment

The development rollout was deployed with another free NodePort:

```bash
helm upgrade --install lab14-dev k8s/devops-info-service \
  -n dev \
  -f k8s/devops-info-service/values-dev.yaml \
  --set service.nodePort=30190 \
  --set hooks.enabled=false
```

### 5.2 Reproducible update

The development update overlay changes the dev version and release track:

```bash
helm upgrade lab14-dev k8s/devops-info-service \
  -n dev \
  -f k8s/devops-info-service/values-dev.yaml \
  -f k8s/devops-info-service/values-dev-update.yaml \
  --set service.nodePort=30190 \
  --set hooks.enabled=false
```

`values-dev-update.yaml` changes the service version to `1.1.0-dev` and release track to `dev-green-v2`.

### 5.3 Preview verification

The blue-green rollout exposed:

- active service: `lab14-dev-devops-info-service`
- preview service: `lab14-dev-devops-info-service-preview`

I verified that the preview service really served the new revision before promotion:

```bash
kubectl port-forward svc/lab14-dev-devops-info-service -n dev 18080:80
kubectl port-forward svc/lab14-dev-devops-info-service-preview -n dev 18081:80
curl -s http://127.0.0.1:18081/ | jq '.service.version, .configuration.data.settings.releaseTrack'
```

Observed preview response:

- `service.version = "1.1.0-dev"`
- `releaseTrack = "dev-green-v2"`

Before promotion, the active service still pointed to the old stable revision.

### 5.4 Promotion and undo

Promotion was verified with:

```bash
kubectl argo rollouts promote lab14-dev-devops-info-service -n dev
```

Observed result:

- the active service switched to the new ReplicaSet
- the preview service matched the active hash after cutover

Rollback behavior was then verified with:

```bash
kubectl argo rollouts undo lab14-dev-devops-info-service -n dev
kubectl argo rollouts promote lab14-dev-devops-info-service -n dev
```

Observed result:

- the previous revision returned as the rollout target
- after promotion, the active service switched back to the old stable revision
- the final active response again matched the old version

Final active response check:

```bash
kubectl port-forward svc/lab14-dev-devops-info-service -n dev 18082:80
curl -s http://127.0.0.1:18082/ | jq '.service.version, .configuration.data.settings.releaseTrack'
```

Observed final active response:

- `service.version = "1.0.0-dev"`
- `releaseTrack = "dev-green-v2"`

## 6. Bonus Task: Automated Analysis Failure and Automatic Rollback

### 6.1 AnalysisTemplate behavior

The bonus task uses a web metric against the canary service:

- service URL pattern: `http://<release>-devops-info-service-canary.<namespace>.svc.cluster.local:80/<path>`
- success condition: `result == "healthy"`
- JSONPath: `{$.status}`
- interval: `10s`
- count: `3`
- failure limit: `1`

### 6.2 Failure overlay

The failure overlay changes the analysis endpoint:

```yaml
rollout:
  analysis:
    path: /does-not-exist
```

### 6.3 Live failure test

To force a new revision and make the analysis fail, I used:

```bash
helm upgrade lab14-prod k8s/devops-info-service \
  -n prod \
  -f k8s/devops-info-service/values-prod.yaml \
  -f k8s/devops-info-service/values-prod-update.yaml \
  --set service.nodePort=30191 \
  --set hooks.enabled=false \
  --set 'env[3].value=1.2.0' \
  --set 'env[5].value=prod-fail-v3' \
  --set rollout.analysis.path=/does-not-exist
```

Then the rollout was promoted through the initial pause:

```bash
kubectl argo rollouts promote lab14-prod-devops-info-service -n prod
```

Observed result:

- the rollout reached the analysis step
- the `AnalysisRun` queried `http://lab14-prod-devops-info-service-canary.prod.svc.cluster.local:80/does-not-exist`
- the metric received repeated `404` responses
- the rollout was automatically aborted
- the previous stable revision remained healthy

Observed analysis status from `kubectl describe analysisrun`:

- message: `received non 2xx response code: 404`
- final rollout message: `RolloutAborted: Rollout aborted update to revision 5`

This confirms the bonus requirement: failed automated analysis stops promotion and protects the stable version.

### 6.4 Post-test restore

After the failure scenario was validated, `prod` was restored to a healthy state:

```bash
helm upgrade lab14-prod k8s/devops-info-service \
  -n prod \
  -f k8s/devops-info-service/values-prod.yaml \
  -f k8s/devops-info-service/values-prod-update.yaml \
  --set service.nodePort=30191 \
  --set hooks.enabled=false
```

Final production rollout status:

```bash
kubectl argo rollouts get rollout lab14-prod-devops-info-service -n prod
```

Final result:

- `prod`: `Healthy`
- `dev`: `Healthy`

## 7. Screenshots

The live dashboard screenshots are saved in:

- `k8s/screenshots/lab14/dashboard-home.png`
- `k8s/screenshots/lab14/dashboard-prod.png`
- `k8s/screenshots/lab14/dashboard-prod-rollout.png`

These capture the dashboard used during validation.

## 8. Helpful Commands

```bash
kubectl argo rollouts get rollout <name> -n <namespace> -w
kubectl argo rollouts promote <name> -n <namespace>
kubectl argo rollouts abort <name> -n <namespace>
kubectl argo rollouts undo <name> -n <namespace>
kubectl argo rollouts retry rollout <name> -n <namespace>
kubectl get rollout -A
kubectl get analysisrun -A
kubectl describe rollout <name> -n <namespace>
kubectl describe analysisrun <name> -n <namespace>
```

## 9. Summary

Lab 14 and the bonus task are fully implemented and verified:

- Helm chart supports plain deployment, canary rollout, and blue-green rollout
- `prod` canary was tested for successful promotion and manual abort
- `dev` blue-green was tested for preview validation, promotion, and undo
- bonus automated analysis failure was reproduced live and caused automatic abort
- the cluster was left in a healthy final state after verification
