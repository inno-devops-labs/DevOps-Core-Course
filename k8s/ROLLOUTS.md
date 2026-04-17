# Lab 14 — Progressive Delivery with Argo Rollouts

## 1. Overview

This lab extends the GitOps setup from Lab 13 by replacing the standard Kubernetes `Deployment` resource with the Argo Rollouts `Rollout` CRD.

Implemented goals:
- install Argo Rollouts controller
- install Argo Rollouts dashboard
- convert the Helm chart from `Deployment` to `Rollout`
- use **canary** strategy in the `dev` environment
- use **blue-green** strategy in the `prod` environment
- document rollout operations, promotion, abort, and rollback

Bonus automated analysis is intentionally **not implemented**.

---

## 2. Repository Changes

### Files added

```text
k8s/ROLLOUTS.md
k8s/python-app/templates/rollout.yaml
k8s/python-app/templates/preview-service.yaml
```

### Files updated

```text
k8s/python-app/templates/deployment.yaml
k8s/python-app/templates/service.yaml
k8s/python-app/templates/_helpers.tpl
k8s/python-app/values.yaml
k8s/python-app/values-dev.yaml
k8s/python-app/values-prod.yaml
```

### Design choice

The implementation uses the existing ArgoCD applications from Lab 13:
- `python-app-dev` in namespace `dev` → **canary rollout** (with 5 replicas for clearer step progression)
- `python-app-prod` in namespace `prod` → **blue-green rollout**

This keeps the chart reusable and avoids creating extra application manifests.

---

## 3. Argo Rollouts Setup

### Controller installation

```bash
kubectl create namespace argo-rollouts
kubectl apply -n argo-rollouts -f https://github.com/argoproj/argo-rollouts/releases/latest/download/install.yaml
kubectl get pods -n argo-rollouts
```

Expected result:
- Rollouts controller pod is in `Running` state

### kubectl plugin installation

On macOS:

```bash
brew install argoproj/tap/kubectl-argo-rollouts
kubectl argo rollouts version
```

### Dashboard installation

```bash
kubectl apply -n argo-rollouts -f https://github.com/argoproj/argo-rollouts/releases/latest/download/dashboard-install.yaml
kubectl port-forward svc/argo-rollouts-dashboard -n argo-rollouts 3100:3100
```

Dashboard URL:

```text
http://localhost:3100
```

---

## 4. Rollout vs Deployment

### Deployment
A standard Kubernetes `Deployment` supports rolling updates, but it does not provide first-class concepts such as canary steps, blue-green preview services, or controlled promotion and rollback.

### Rollout
Argo Rollouts `Rollout` is structurally similar to `Deployment`, but adds advanced progressive delivery features:
- canary step definitions
- manual or timed pauses
- blue-green active/preview service switching
- abort and retry operations
- rollout dashboard visualization

### Key implementation detail
The old `deployment.yaml` is still kept in the chart, but it is wrapped with a condition:

```yaml
{{- if not .Values.rollout.enabled }}
```

This ensures that the chart does **not** render both a `Deployment` and a `Rollout` at the same time.

---

## 5. Canary Deployment (dev)

### Strategy
The `dev` environment uses a canary rollout defined in `values-dev.yaml`. The replica count is intentionally set to `5` so that the 20/40/60/80 canary steps are visible and meaningful during the rollout.

Configured steps:
- 20% traffic → manual pause
- 40% traffic → pause 30s
- 60% traffic → pause 30s
- 80% traffic → pause 30s
- 100%

Example values:

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

### Apply and monitor
After syncing the ArgoCD application, monitor the rollout with:

```bash
kubectl argo rollouts get rollout python-app-dev -n dev -w
```

### Manual promotion
The first pause requires manual promotion:

```bash
kubectl argo rollouts promote python-app-dev -n dev
```

### Abort demonstration
To test rollback during rollout:

```bash
kubectl argo rollouts abort python-app-dev -n dev
```

Retry after abort:

```bash
kubectl argo rollouts retry rollout python-app-dev -n dev
```

### Dashboard screenshot placeholder

```text
[INSERT SCREENSHOT HERE: canary progression in Argo Rollouts dashboard]
```

### Manual promotion screenshot placeholder

```text
[INSERT SCREENSHOT HERE: rollout paused at 20% and manual promote action]
```

---

## 6. Blue-Green Deployment (prod)

### Strategy
The `prod` environment uses a blue-green rollout defined in `values-prod.yaml`.

Key settings:
- active service = main application service
- preview service = separate test endpoint
- auto promotion disabled

Example values:

```yaml
rollout:
  enabled: true
  strategy: blueGreen
  blueGreen:
    autoPromotionEnabled: false
    previewService:
      enabled: true
      type: ClusterIP
```

### Preview service
A separate preview service is created from `templates/preview-service.yaml`.

Expected names for the `prod` release:
- active service: `python-app-prod`
- preview service: `python-app-prod-preview`

### Test flow
1. access active service
2. update image/config to trigger new rollout
3. access preview service
4. validate new version
5. promote new version to active

### Promotion command

```bash
kubectl argo rollouts promote python-app-prod -n prod
```

### Rollback demonstration
To observe rollback behavior after promotion, perform another change or roll back the chart revision and watch how the active service switches quickly between versions.

### Preview vs active screenshot placeholder

```text
[INSERT SCREENSHOT HERE: blue-green active and preview services]
```

### Promotion screenshot placeholder

```text
[INSERT SCREENSHOT HERE: promotion from preview to active]
```

---

## 7. Strategy Comparison

| Aspect | Canary | Blue-Green |
|---|---|---|
| Traffic behavior | gradual traffic shift | instant switch |
| Risk reduction | high for progressive exposure | high for preview testing |
| Rollback style | abort during progression | fast active/preview switch |
| Resource usage | lower | higher during overlap |
| Best fit | user-facing production changes with gradual rollout | environments where explicit preview validation is needed |

### Recommendation
- use **canary** when gradual exposure to users is important
- use **blue-green** when preview validation and instant cutover are more important than temporary extra resource usage

In this lab:
- `dev` is a good fit for canary experimentation
- `prod` is a good fit for blue-green preview and controlled promotion

---

## 8. Useful CLI Commands

### General status

```bash
kubectl argo rollouts get rollout <name> -n <namespace> -w
kubectl argo rollouts list rollouts -A
kubectl argo rollouts dashboard
```

### Canary control

```bash
kubectl argo rollouts promote <name> -n <namespace>
kubectl argo rollouts abort <name> -n <namespace>
kubectl argo rollouts retry rollout <name> -n <namespace>
```

### Blue-green verification

```bash
kubectl get svc -n prod
kubectl port-forward svc/python-app-prod -n prod 8080:80
kubectl port-forward svc/python-app-prod-preview -n prod 8081:80
```

### Troubleshooting

```bash
kubectl get rollout -A
kubectl describe rollout <name> -n <namespace>
kubectl get rs -n <namespace>
kubectl get pods -n <namespace>
```

---

## 9. Notes for ArgoCD Integration

Because Lab 14 builds directly on Lab 13, ArgoCD still manages the Helm chart. The only major difference is that ArgoCD now syncs a `Rollout` resource instead of a `Deployment` resource.

Important precautions:
- install the Argo Rollouts CRD and controller before syncing the chart
- avoid rendering `Deployment` and `Rollout` together
- keep service names stable so that ArgoCD applications do not need to be redesigned

---

## 10. Conclusion

This lab introduces progressive delivery on top of the existing GitOps setup.

Implemented changes:
- standard Kubernetes deployment logic replaced with Argo Rollouts
- canary rollout strategy prepared for `dev`
- blue-green rollout strategy prepared for `prod`
- preview service support added to the chart
- documentation and CLI workflow prepared for promotion, abort, retry, and rollback

This setup provides a clean progression from Lab 13 and keeps the Helm chart flexible enough to support both rollout strategies without bonus analysis features.


## 11. Migration Note from Lab 13

If the cluster already contains Lab 13 `Deployment` resources for `python-app-dev` or `python-app-prod`, the first ArgoCD sync after switching the chart to `Rollout` may need a one-time cleanup or prune of the old `Deployment` objects. This is expected because the workload kind changes from `Deployment` to `Rollout`.
