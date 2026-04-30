# Lab 14 — Progressive Delivery with Argo Rollouts

## Overview

In this lab, progressive delivery strategies were implemented using Argo Rollouts:

- Canary deployment (gradual rollout)
- Blue-Green deployment (instant traffic switch)

## Task 1 — Argo Rollouts Fundamentals

### Installation

```bash
kubectl create namespace argo-rollouts
kubectl apply -n argo-rollouts -f https://github.com/argoproj/argo-rollouts/releases/latest/download/install.yaml
```

Verification:

```bash
kubectl get pods -n argo-rollouts
```

### CLI Plugin

```bash
kubectl argo rollouts version
```

### Rollout vs Deployment

| Deployment | Rollout |
| --- | --- |
| Basic updates | Advanced deployment strategies |
| No traffic control | Traffic shifting supported |
| No rollback logic | Automated rollback |
| No steps | Step-based rollout |

## Task 2 — Canary Deployment

### Helm Validation

```bash
helm lint .
```

```text
1 chart(s) linted, 0 chart(s) failed
```

### Template Validation

```bash
helm template devops-app . -f values-canary.yaml | grep -E "kind: Rollout|setWeight|pause"
```

```text
kind: Rollout
        - setWeight: 20
        - pause: {}
        - setWeight: 40
        - pause:
        - setWeight: 60
        - pause:
        - setWeight: 80
        - pause:
        - setWeight: 100
```

### Deployment

```bash
kubectl create namespace rollouts-lab --dry-run=client -o yaml | kubectl apply -f -

helm upgrade --install devops-rollout . \
  -n rollouts-lab \
  -f values-canary.yaml
```

### Rollout Status

```bash
kubectl get rollouts -n rollouts-lab
```

```text
NAME                          DESIRED   CURRENT   UP-TO-DATE
devops-rollout-devops-chart   3         3         3
```

### Detailed Status

```bash
kubectl argo rollouts get rollout devops-rollout-devops-chart -n rollouts-lab
```

```text
Status: ✔ Healthy
Strategy: Canary
SetWeight: 100
Images: aserova/devops-info-service:v3 (stable)

Replicas:
  Desired: 3
  Ready: 3
```

### Abort Rollout

```bash
kubectl argo rollouts abort devops-rollout-devops-chart -n rollouts-lab
```

```text
rollout 'devops-rollout-devops-chart' aborted
```

The rollout remained stable:

```text
Status: ✔ Healthy
```

## Task 3 — Blue-Green Deployment

### Template Validation

```bash
helm template devops-app . -f values-bluegreen.yaml | grep -E "kind: Rollout|blueGreen|previewService|activeService"
```

```text
kind: Rollout
blueGreen:
  activeService: devops-app-devops-chart-service
  previewService: devops-app-devops-chart-preview
```

### Deployment

```bash
helm upgrade --install devops-bluegreen . \
  -n rollouts-lab \
  -f values-bluegreen.yaml
```

### Services

```bash
kubectl get svc -n rollouts-lab
```

```text
devops-bluegreen-devops-chart-preview   NodePort   80:31094
devops-bluegreen-devops-chart-service   NodePort   80:30466
```

### Rollout Status

```bash
kubectl argo rollouts get rollout devops-bluegreen-devops-chart -n rollouts-lab
```

```text
Status: ✔ Healthy
Strategy: BlueGreen
Images: aserova/devops-info-service:v3 (stable, active)

Replicas:
  Desired: 3
  Ready: 3
```

### Update Version

```bash
helm upgrade --install devops-bluegreen . \
  -n rollouts-lab \
  -f values-bluegreen.yaml \
  --set config.logLevel=debug
```

### Promote

```bash
kubectl argo rollouts promote devops-bluegreen-devops-chart -n rollouts-lab
```

```text
rollout 'devops-bluegreen-devops-chart' promoted
```

## Strategy Comparison

| Canary | Blue-Green |
| --- | --- |
| Gradual rollout | Instant switch |
| Lower risk | Fast deployment |
| Takes more time | Requires more resources |
| Partial traffic testing | Full preview environment |

## Conclusion

During this lab:

- Canary deployment was implemented and tested
- Blue-Green deployment was implemented with preview environment
- Rollout operations were tested:

  - deployment
  - promotion
  - abort

Argo Rollouts successfully enabled controlled and safe application updates.

## Result

All tasks completed successfully:

- Canary deployment ✔
- Blue-Green deployment ✔
- Rollout management ✔
