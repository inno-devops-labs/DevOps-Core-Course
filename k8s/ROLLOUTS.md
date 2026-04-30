# Argo Rollouts

## 1) Argo Rollouts Setup

### Install controller

```bash
kubectl create namespace argo-rollouts
kubectl apply -n argo-rollouts -f https://github.com/argoproj/argo-rollouts/releases/latest/download/install.yaml
kubectl get pods -n argo-rollouts
```

Expected result: controller pods in `Running` state.

### Install kubectl plugin

Linux:

```bash
curl -LO https://github.com/argoproj/argo-rollouts/releases/latest/download/kubectl-argo-rollouts-linux-amd64
chmod +x kubectl-argo-rollouts-linux-amd64
sudo mv kubectl-argo-rollouts-linux-amd64 /usr/local/bin/kubectl-argo-rollouts
kubectl argo rollouts version
```

macOS:

```bash
brew install argoproj/tap/kubectl-argo-rollouts
kubectl argo rollouts version
```

### Install dashboard

```bash
kubectl apply -n argo-rollouts -f https://github.com/argoproj/argo-rollouts/releases/latest/download/dashboard-install.yaml
kubectl port-forward svc/argo-rollouts-dashboard -n argo-rollouts 3100:3100
```

Open [http://localhost:3100](http://localhost:3100). If the UI stays on loading, first verify the dashboard pod and logs:

```bash
kubectl get pods -n argo-rollouts
kubectl logs -n argo-rollouts deploy/argo-rollouts-dashboard
```

The dashboard root should load before navigating to `/rollouts/`. If the root page is blank, the port-forward or dashboard pod is not healthy.

> If you are using the Argo Rollouts plugin, `kubectl argo rollouts dashboard` is a recommended alternative to direct port-forwarding.

### Rollout vs Deployment

`Rollout` is compatible with the deployment template model, but adds progressive delivery fields:

- `spec.strategy.canary` (weights, pauses, promotions)
- `spec.strategy.blueGreen` (active/preview services, promotion behavior)
- native rollout lifecycle controls (promote, abort, retry, undo)
- deeper rollout status and history for phased release workflows

## 2) Canary Deployment

### Implementation in chart

Main rollout resource is in `k8s/devops-app/templates/rollout.yaml`:

- `kind: Rollout`
- default strategy is canary (`values.yaml`)
- steps are configured as:
  - `20% -> analysis check`
  - `pause` (manual promotion)
  - `40% -> pause 30s`
  - `60% -> pause 30s`
  - `80% -> pause 30s`
  - `100%`

A release-scoped `AnalysisTemplate` is included in `k8s/devops-app/templates/analysistemplate.yaml` (name: `<release>-health-check`) to validate the health endpoint and trigger automatic rollback if the new release fails.

### Deploy canary rollout

```bash
helm upgrade --install devops-app ./k8s/devops-app -n dev --create-namespace
kubectl argo rollouts get rollout devops-app -n dev
```

### Trigger rollout and observe progression

Change image tag or env/config value:

```bash
helm upgrade --install devops-app ./k8s/devops-app -n dev --set image.tag=lab04
kubectl argo rollouts get rollout devops-app -n dev --watch
```

If you want to access the app locally, use the generated service name and port-forwarding:

```bash
kubectl port-forward svc/devops-app -n dev 8080:80
curl http://localhost:8080/health
```

If the app is installed with a different release name, replace `devops-app` with the actual service name from `kubectl get svc -n dev`.

Manual first promotion:

```bash
kubectl argo rollouts promote devops-app -n dev
```

Then rollout continues automatically on timed pauses.

### Abort and rollback test

During progression:

```bash
kubectl argo rollouts abort devops-app -n dev
kubectl argo rollouts get rollout devops-app -n dev
```

Expected behavior: traffic is shifted back to stable revision quickly.

## 3) Blue-Green Deployment

### Implementation in chart

Blue-green profile is provided via `k8s/devops-app/values-bluegreen.yaml`:

- `rollout.strategy: blueGreen`
- `activeService` and `previewService`
- `autoPromotionEnabled: false` (manual approval gate)

Services are templated in `k8s/devops-app/templates/service.yaml`:

- active service (production traffic)
- preview service (new version testing)

### Deploy blue-green rollout

```bash
helm upgrade --install devops-app-bg ./k8s/devops-app -n dev -f ./k8s/devops-app/values-bluegreen.yaml
kubectl argo rollouts get rollout devops-app-bg -n dev
```

### Blue-green flow

1. Deploy baseline version (blue).
2. Push update (new image/config) -> preview (green) comes up behind preview service.
3. Test preview service endpoint:
   ```bash
   kubectl port-forward svc/devops-app-preview -n dev 8081:80
   curl http://localhost:8081/health
   ```
   and verify active service stays stable:
   ```bash
   kubectl port-forward svc/devops-app-active -n dev 8080:80
   curl http://localhost:8080/health
   ```
4. Promote green to active.
5. Verify instant traffic switch.

Promote command:

```bash
kubectl argo rollouts promote devops-app-bg -n dev
```

Rollback after promotion:

```bash
kubectl argo rollouts undo devops-app-bg -n dev
```

Blue-green rollback is typically faster than canary because it switches service selectors immediately instead of stepping through weighted traffic phases.

## Bonus) Automated Analysis

### AnalysisTemplate and thresholds

Canary rollout includes an analysis step with:

- `interval: 10s`
- `count: 3`
- `failureLimit: 1`
- `successCondition: result == "healthy"`

The check uses `web` provider and requests:

`http://<release>.<namespace>.svc.cluster.local{{ .Values.rollout.analysis.path }}`

Default path is configured in `values.yaml`:

```yaml
rollout:
  analysis:
    path: /health
```

### Intentional failure test (auto-rollback demo)

Trigger a rollout with a broken analysis endpoint:

```bash
helm upgrade --install devops-app ./k8s/devops-app -n dev --set rollout.analysis.path=/broken-health
kubectl argo rollouts get rollout devops-app -n dev --watch
kubectl argo rollouts get analysisrun -n dev
```

Expected result:

- analysis metric fails
- rollout is marked `Degraded`
- traffic shifts back to stable ReplicaSet automatically

## 4) Strategy Comparison

### Canary

Pros:
- low blast radius with gradual exposure
- good for risk-sensitive changes
- can combine with analysis gates

Cons:
- slower release process
- more operational steps and monitoring

### Blue-Green

Pros:
- very fast cutover
- very fast rollback
- easy pre-production validation using preview environment

Cons:
- usually higher resource usage (two environments)
- less granular risk control than canary percentages

### Recommendation

- Use **canary** for high-risk releases and when you need controlled progressive exposure.
- Use **blue-green** for low-latency cutover requirements and fast operational rollback.

## 5) CLI Commands Reference

```bash
# List rollouts
kubectl argo rollouts list rollouts -n dev

# Watch rollout status
kubectl argo rollouts get rollout <name> -n dev --watch

# Promote rollout (manual gate)
kubectl argo rollouts promote <name> -n dev

# Abort active rollout
kubectl argo rollouts abort <name> -n dev

# Retry failed rollout
kubectl argo rollouts retry <name> -n dev

# Roll back to previous revision
kubectl argo rollouts undo <name> -n dev

# Rollout dashboard (plugin)
kubectl argo rollouts dashboard
```

## 6) Monitoring and Troubleshooting

- `kubectl argo rollouts get rollout <name> -n <ns> --watch`
- `kubectl describe rollout <name> -n <ns>`
- `kubectl get rs,pods -n <ns> -l app=devops-app`
- `kubectl logs -n argo-rollouts deploy/argo-rollouts`

For report evidence, add dashboard screenshots to `k8s/screenshots` and reference them in this file.

## 7) Submission Checklist Status

- [x] Controller install steps, plugin install, dashboard access documented
- [x] Rollout vs Deployment differences documented
- [x] Deployment converted to Rollout with required canary steps (`20 -> pause manual -> 40/60/80 pauses -> 100`)
- [x] Abort and rollback commands documented
- [x] Blue-green strategy, active/preview services, and promotion flow documented
- [x] Canary vs blue-green comparison included
- [x] AnalysisTemplate and canary integration documented
- [x] Intentional analysis failure scenario documented
- [ ] Add actual dashboard screenshots (progression, promote, abort, preview/active) into `k8s/screenshots`
- [ ] Attach real run evidence from your cluster in this file (optional command output snippets)
