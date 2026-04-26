# Lab 14

## 1. Argo Rollouts Setup

```bash
$ kubectl get pods -n argo-rollouts
NAME                                      READY   STATUS    RESTARTS   AGE
argo-rollouts-5f64f8d68-k7d2c             1/1     Running   0          165m
argo-rollouts-dashboard-755bbc64c-ljchj   1/1     Running   0          164m
```

## 2. Canary Development


```bash
strategy:
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

This rolls out the new version gradually: 20% -> manual promotion -> 40% -> ... -> 100%

![](/labs/k8s/promotion.png)
![](/labs/k8s/promotion_progress.png)
![](/labs/k8s/abort_promotion.png)

## 3. Blue-Green Deployment

A separate values file `values-bg.yaml` sets `strategy: bluegreen`. The Rollout template reads this and creates:

```yaml
strategy:
  blueGreen:
    activeService: python-app-bg-simple-app
    previewService: python-app-bg-simple-app-preview
    autoPromotionEnabled: false
```

### Preview vs Active

- Active Service receives production traffic.

- Preview Service points to the new (green) version for testing before promotion.

- Both services use the same selector labels to allow the Rollout controller to switch traffic.

![](/labs/k8s/bg_rollout.png)
![](/labs/k8s/Green%20and%20blue%20versions.png)

## 4. Strategy Comparison

| Criteria         | Canary                               | Blue‑Green                          |
|------------------|--------------------------------------|-------------------------------------|
| Traffic shift    | Gradual (percentage‑based)           | All‑or‑nothing (full switch)        |
| Rollback speed   | Fast revert to stable ReplicaSet     | Instant ‑ active service switches immediately |
| Resource usage   | Same replicas shared between versions| 2x replicas required during transition |
| User exposure    | Real users are partially exposed     | Only testers access green via preview |
| Testing new version | Canary pods receive real traffic | Green is tested in isolation via preview |

