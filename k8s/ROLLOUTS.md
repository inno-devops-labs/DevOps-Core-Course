# Lab 14 Report: Progressive Delivery with Argo Rollouts

## Environment and Setup

Local tools:

```bash
helm version --short
# v4.1.3+gc94d381

kubectl version --client=true
# Client Version: v1.32.2
# Kustomize Version: v5.5.0

kubectl argo rollouts version
# kubectl-argo-rollouts: v1.8.3+49fa151
```

The implementation was validated with Helm rendering for both rollout strategies. The commands below document the setup, deployment flow, promotion, abort, and rollback operations used for this lab.

## Argo Rollouts Setup

Install the controller:

```bash
kubectl create namespace argo-rollouts
kubectl apply -n argo-rollouts \
  -f https://github.com/argoproj/argo-rollouts/releases/latest/download/install.yaml
kubectl get pods -n argo-rollouts
```

Install and access the dashboard:

```bash
kubectl apply -n argo-rollouts \
  -f https://github.com/argoproj/argo-rollouts/releases/latest/download/dashboard-install.yaml
kubectl port-forward svc/argo-rollouts-dashboard -n argo-rollouts 3100:3100
```

Dashboard URL:

```text
http://localhost:3100
```

## Rollout vs Deployment

`Deployment` supports rolling updates with `maxSurge` and `maxUnavailable`, but it does not model release stages, manual pauses, preview services, or abort/promotion operations.

`Rollout` keeps the familiar `replicas`, `selector`, and pod `template` fields, and adds progressive delivery under `spec.strategy`. In this lab the chart supports:

- `strategy.canary.steps` for staged rollout weights and pauses.
- `strategy.blueGreen.activeService` for production traffic.
- `strategy.blueGreen.previewService` for testing the new ReplicaSet before promotion.
- CLI operations such as `promote`, `abort`, `retry`, and `undo`.

## Chart Changes

Implemented files:

- `k8s/devops-info/templates/rollout.yaml`
- `k8s/devops-info/templates/service-preview.yaml`
- `k8s/devops-info/values-canary.yaml`
- `k8s/devops-info/values-bluegreen.yaml`

Updated files:

- `k8s/devops-info/templates/deployment.yaml`
- `k8s/devops-info/templates/_helpers.tpl`
- `k8s/devops-info/values.yaml`

The default chart now deploys an Argo Rollout. The legacy Deployment is kept as an explicit fallback and renders only when:

```yaml
deployment:
  enabled: true
rollout:
  enabled: false
```

## Canary Deployment

The canary strategy is configured in `values.yaml` and repeated in `values-canary.yaml`:

```yaml
rollout:
  enabled: true
  strategy: canary
  canary:
    steps:
      - setWeight: 20
      - pause: {}
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

Install canary rollout:

```bash
helm upgrade --install devops-info ./k8s/devops-info \
  -f ./k8s/devops-info/values-canary.yaml
```

Trigger a new rollout:

```bash
helm upgrade devops-info ./k8s/devops-info \
  -f ./k8s/devops-info/values-canary.yaml \
  --set image.tag=v1.0.1
```

Observe and promote:

```bash
kubectl argo rollouts get rollout devops-info -w
kubectl argo rollouts promote devops-info
```

Abort and rollback:

```bash
kubectl argo rollouts abort devops-info
kubectl argo rollouts get rollout devops-info
```

Expected progression:

1. New ReplicaSet receives 20% canary weight.
2. Rollout pauses until manual promotion.
3. After promotion it proceeds to 40%, 60%, and 80%, pausing 30 seconds at each stage.
4. At 100%, the new ReplicaSet becomes stable.
5. If aborted during rollout, Argo Rollouts returns traffic/replicas to the stable ReplicaSet.

The dashboard shows the same progression visually: a stable ReplicaSet, a canary ReplicaSet, the active step, and the current pause or promotion state. Screenshots are omitted from this report.

## Blue-Green Deployment

Blue-green strategy is configured in `values-bluegreen.yaml`:

```yaml
rollout:
  enabled: true
  strategy: blueGreen
  blueGreen:
    autoPromotionEnabled: false
    autoPromotionSeconds: null
    previewService:
      enabled: true
      type: ClusterIP
```

The active service is the existing service:

```text
devops-info
```

The preview service is:

```text
devops-info-preview
```

Install blue-green rollout:

```bash
helm upgrade --install devops-info ./k8s/devops-info \
  -f ./k8s/devops-info/values-bluegreen.yaml
```

Trigger green version:

```bash
helm upgrade devops-info ./k8s/devops-info \
  -f ./k8s/devops-info/values-bluegreen.yaml \
  --set image.tag=v1.0.2
```

Access active and preview services:

```bash
kubectl port-forward svc/devops-info 8080:80
kubectl port-forward svc/devops-info-preview 8081:80
```

Promote green to active:

```bash
kubectl argo rollouts promote devops-info
kubectl argo rollouts get rollout devops-info
```

Rollback after promotion:

```bash
kubectl argo rollouts undo devops-info
```

Expected behavior:

- Active service continues serving the stable ReplicaSet.
- Preview service points to the new ReplicaSet.
- Manual promotion switches active traffic to the new ReplicaSet almost instantly.
- Rollback is faster than canary because it is a service selector switch rather than staged progression.

## Strategy Comparison

| Strategy | Best for | Pros | Cons |
| --- | --- | --- | --- |
| Canary | User-facing services where gradual exposure reduces risk | Limits blast radius, supports staged observation, good for high-traffic services | Slower rollout, users may hit mixed versions, percentage traffic is approximate without an ingress/service-mesh traffic router |
| Blue-green | Releases that need full pre-production validation and instant switch | Simple mental model, preview environment, fast promotion and rollback | Needs extra capacity for both versions, all-or-nothing after promotion |

Recommendation:

- Use canary for normal application releases where risk should be reduced gradually.
- Use blue-green for database-compatible releases, demos, critical cutovers, or releases that must be tested through a preview endpoint before exposure.
- For this Flask service, canary is the default because it is resource-efficient and gives controlled exposure. Blue-green is useful when validating the exact new version through `devops-info-preview` before switching all traffic.

## CLI Reference

Controller and dashboard:

```bash
kubectl get pods -n argo-rollouts
kubectl port-forward svc/argo-rollouts-dashboard -n argo-rollouts 3100:3100
```

Rollout monitoring:

```bash
kubectl argo rollouts list rollouts
kubectl argo rollouts get rollout devops-info
kubectl argo rollouts get rollout devops-info -w
kubectl describe rollout devops-info
```

Promotion, abort, retry, rollback:

```bash
kubectl argo rollouts promote devops-info
kubectl argo rollouts abort devops-info
kubectl argo rollouts retry rollout devops-info
kubectl argo rollouts undo devops-info
```

Helm validation used in this lab:

```bash
helm lint k8s/devops-info
helm template devops-info k8s/devops-info -f k8s/devops-info/values-canary.yaml
helm template devops-info k8s/devops-info -f k8s/devops-info/values-bluegreen.yaml
```

Validation result:

```text
helm lint: 1 chart(s) linted, 0 chart(s) failed
canary render: Rollout rendered with 20/40/60/80/100 canary steps
blue-green render: Rollout rendered with active service devops-info and preview service devops-info-preview
```
