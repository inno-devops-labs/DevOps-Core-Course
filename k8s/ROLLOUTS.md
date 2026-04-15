# Lab 14 - Progressive Delivery with Argo Rollouts

Run date: April 15, 2026

Resource-saving note:
I did not install Argo Rollouts into a live cluster or open the dashboard in this session. Instead, I extended the Helm chart with a switchable Rollout path, rendered the chart in default, canary, and blue-green modes, and documented the exact commands required for a live run.

## Files Added

- `k8s/devops-info-service/templates/rollout.yaml`
- `k8s/devops-info-service/templates/preview-service.yaml`
- `k8s/devops-info-service/templates/analysis-template.yaml`
- `k8s/devops-info-service/values-rollout-canary.yaml`
- `k8s/devops-info-service/values-rollout-bluegreen.yaml`
- `k8s/ROLLOUTS.md`

Files updated:

- `k8s/devops-info-service/templates/deployment.yaml`
- `k8s/devops-info-service/templates/NOTES.txt`
- `k8s/devops-info-service/templates/_helpers.tpl`
- `k8s/devops-info-service/values.yaml`
- `k8s/argocd/application.yaml`
- `k8s/argocd/application-dev.yaml`
- `k8s/argocd/application-prod.yaml`
- `k8s/argocd/applicationset.yaml`

## Validation Summary

The chart still renders in default Deployment mode:

```text
.\.tools\helm.exe lint .\k8s\devops-info-service
1 chart(s) linted, 0 chart(s) failed

.\.tools\helm.exe template devops-info-service .\k8s\devops-info-service
```

Canary and blue-green rollout profiles also render successfully:

```text
.\.tools\helm.exe template devops-info-service-canary .\k8s\devops-info-service -f .\k8s\devops-info-service\values-rollout-canary.yaml --namespace canary
.\.tools\helm.exe template devops-info-service-bluegreen .\k8s\devops-info-service -f .\k8s\devops-info-service\values-rollout-bluegreen.yaml --namespace bluegreen
```

This means:

- previous labs keep working because rollout support is opt-in
- the chart can now emit `Rollout`, `Preview Service`, and `AnalysisTemplate` resources without breaking the existing Deployment path

## Argo Rollouts Setup

Prepared live install commands:

```powershell
kubectl create namespace argo-rollouts
kubectl apply -n argo-rollouts -f https://github.com/argoproj/argo-rollouts/releases/latest/download/install.yaml
kubectl apply -n argo-rollouts -f https://github.com/argoproj/argo-rollouts/releases/latest/download/dashboard-install.yaml
kubectl get pods -n argo-rollouts
kubectl port-forward svc/argo-rollouts-dashboard -n argo-rollouts 3100:3100
```

Prepared CLI commands:

```powershell
kubectl argo rollouts version
kubectl argo rollouts get rollout <name> -n <namespace> -w
kubectl argo rollouts promote <name> -n <namespace>
kubectl argo rollouts abort <name> -n <namespace>
kubectl argo rollouts retry rollout <name> -n <namespace>
```

These were not executed in this run because the cluster and plugin were not installed to conserve resources.

## Rollout Design

The chart now supports two workload modes:

- default: Kubernetes `Deployment`
- progressive delivery: Argo `Rollout`

This is controlled by:

```yaml
rollout:
  enabled: false
  strategy: canary
```

Important design choice:

- the Lab 12 chart defaults to persistent storage
- that storage is `ReadWriteOnce`
- weighted canary steps need multiple replicas
- therefore the rollout-specific values disable persistence and treat the service as stateless for progressive delivery

This keeps both labs valid:

- Lab 12 still demonstrates PVC-backed persistence
- Lab 14 demonstrates safe multi-replica rollout strategies

## Canary Deployment

Canary profile:

```yaml
replicaCount: 5

persistence:
  enabled: false

service:
  type: ClusterIP

rollout:
  enabled: true
  strategy: canary
  analysis:
    enabled: true
```

Rendered canary rollout excerpt:

```yaml
kind: Rollout
spec:
  strategy:
    canary:
      steps:
        - setWeight: 20
        - pause: {}
        - analysis:
            templates:
              - templateName: devops-info-service-canary-health
        - setWeight: 40
        - pause:
            duration: 30s
        - setWeight: 60
        - pause:
            duration: 30s
        - setWeight: 80
        - pause:
            duration: 30s
        - setWeight: 100
```

This matches the lab progression:

- 20% with a manual pause
- 40%, 60%, and 80% with timed pauses
- 100% final promotion

Live commands for a real run:

```powershell
.\.tools\helm.exe upgrade --install devops-info-service-canary .\k8s\devops-info-service --namespace canary --create-namespace -f .\k8s\devops-info-service\values-rollout-canary.yaml
kubectl argo rollouts get rollout devops-info-service-canary -n canary -w
kubectl argo rollouts promote devops-info-service-canary -n canary
```

Rollback test prepared for live execution:

```powershell
kubectl argo rollouts abort devops-info-service-canary -n canary
kubectl argo rollouts get rollout devops-info-service-canary -n canary -w
kubectl argo rollouts retry rollout devops-info-service-canary -n canary
```

Expected behavior:

- abort immediately stops progression
- traffic returns to the stable ReplicaSet
- retry resumes the rollout after the issue is fixed

## Blue-Green Deployment

Blue-green profile:

```yaml
replicaCount: 4

persistence:
  enabled: false

service:
  type: ClusterIP

rollout:
  enabled: true
  strategy: blueGreen
  blueGreen:
    autoPromotionEnabled: false
```

Rendered blue-green excerpt:

```yaml
kind: Service
metadata:
  name: devops-info-service-bluegreen-preview
---
kind: Rollout
spec:
  strategy:
    blueGreen:
      activeService: devops-info-service-bluegreen
      previewService: devops-info-service-bluegreen-preview
      autoPromotionEnabled: false
```

Operational model:

- the existing chart service becomes the active service
- a second preview service exposes the new version
- promotion is manual, which fits the lab requirement

Prepared live flow:

```powershell
.\.tools\helm.exe upgrade --install devops-info-service-bluegreen .\k8s\devops-info-service --namespace bluegreen --create-namespace -f .\k8s\devops-info-service\values-rollout-bluegreen.yaml
kubectl port-forward svc/devops-info-service-bluegreen 8080:80 -n bluegreen
kubectl port-forward svc/devops-info-service-bluegreen-preview 8081:80 -n bluegreen
kubectl argo rollouts get rollout devops-info-service-bluegreen -n bluegreen -w
kubectl argo rollouts promote devops-info-service-bluegreen -n bluegreen
```

Expected behavior:

- `8080` serves the active version
- `8081` serves the preview version
- promotion switches traffic to the preview ReplicaSet instantly
- rollback after promotion is faster than canary because it is an all-at-once service switch

## Bonus - Automated Analysis

The chart now renders an `AnalysisTemplate` when canary analysis is enabled.

Rendered excerpt:

```yaml
successCondition: result == "healthy"
provider:
  web:
    url: http://devops-info-service-canary.canary.svc.cluster.local:80/health
    jsonPath: "{$.status}"
```

How it works:

- the canary rollout performs a web check against the service `/health` endpoint
- it expects the JSON field `status` to equal `healthy`
- failures past `failureLimit` can stop or fail the rollout

Benefits:

- no Prometheus dependency is required for the first analysis lab
- health-driven rollback logic is still demonstrated
- the chart is ready for Prometheus-based analysis later if needed

## Rollout vs Deployment

Why `Rollout` instead of `Deployment` for this lab:

- `Rollout` supports step-based canaries and blue-green promotions
- `Deployment` only supports standard rolling updates
- `Rollout` exposes pause, promote, abort, and analysis primitives

Why the chart keeps both:

- earlier labs and ArgoCD examples still use the Deployment path by default
- rollout behavior is enabled only in rollout-specific values files
- this avoids regressions across labs

## Strategy Comparison

### Canary

Best when:

- you want gradual exposure
- you want to observe behavior before full rollout
- rollback decisions may depend on metrics or analysis

Tradeoffs:

- slower than blue-green
- more operational steps
- percentage-based rollout is harder to reason about when replicas are low

### Blue-Green

Best when:

- you need a fast promotion and rollback
- you want a clean preview environment before switching traffic
- you can afford double capacity during rollout

Tradeoffs:

- requires active and preview capacity at the same time
- traffic switch is immediate rather than incremental

Recommendation:

- use canary for high-risk changes or behavior changes
- use blue-green when validation is strong and rollback speed matters most

## Dashboard and Evidence

The dashboard was not started in this run, so screenshots were not collected. For a live run, capture:

- dashboard view of the canary rollout paused at 20%
- dashboard view during 40% / 60% / 80% progression
- abort state and retry state
- blue-green preview and active services before and after promotion

## Command Reference

Useful commands for the live lab run:

```powershell
kubectl create namespace argo-rollouts
kubectl apply -n argo-rollouts -f https://github.com/argoproj/argo-rollouts/releases/latest/download/install.yaml
kubectl apply -n argo-rollouts -f https://github.com/argoproj/argo-rollouts/releases/latest/download/dashboard-install.yaml
.\.tools\helm.exe upgrade --install devops-info-service-canary .\k8s\devops-info-service --namespace canary --create-namespace -f .\k8s\devops-info-service\values-rollout-canary.yaml
.\.tools\helm.exe upgrade --install devops-info-service-bluegreen .\k8s\devops-info-service --namespace bluegreen --create-namespace -f .\k8s\devops-info-service\values-rollout-bluegreen.yaml
kubectl argo rollouts get rollout devops-info-service-canary -n canary -w
kubectl argo rollouts promote devops-info-service-canary -n canary
kubectl argo rollouts abort devops-info-service-canary -n canary
kubectl argo rollouts retry rollout devops-info-service-canary -n canary
kubectl argo rollouts get rollout devops-info-service-bluegreen -n bluegreen -w
kubectl argo rollouts promote devops-info-service-bluegreen -n bluegreen
```
