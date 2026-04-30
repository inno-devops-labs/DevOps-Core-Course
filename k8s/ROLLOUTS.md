# Lab 14 — Progressive Delivery with Argo Rollouts

## Argo Rollouts Fundamentals

Argo Rollouts controller and dashboard were successfully installed:
```bash
$ kubectl argo rollouts version

kubectl-argo-rollouts: v1.9.0+838d4e7
  BuildDate: 2026-03-20T21:08:11Z
  GitCommit: 838d4e792be666ec11bd0c80331e0c5511b5010e
  GitTreeState: clean
  GoVersion: go1.24.13
  Compiler: gc
  Platform: linux/amd64
```

And rollouts pods are running:
```bash
$ kubectl get pods -n argocd-rollouts

NAME                                      READY   STATUS    RESTARTS   AGE
argo-rollouts-921a1aaa3-74fd6             1/1     Running   0          45s
argo-rollouts-dashboard-971adf19-k3nop    1/1     Running   0          45s
```

And web version:

![alt text](./img/rollouts.png)


### Deployment VS rollout

Key Differences:

| Feature | Deployment | Rollout (CRD) |
|---------|------------|----------------|
| **Update strategy** | RollingUpdate / Recreate | Blue-Green, Canary, RollingUpdate |
| **Traffic shaping** |  Not supported |  Istio, NGINX, ALB, SMI integration |
| **Analysis & metrics** |  No |  Prometheus, Datadog, webhooks |
| **Automated rollback** | Manual or based on pod health |  Based on metrics/analysis |
| **Pause/resume** | No |  Manual or automated |
| **Step-wise progression** |  No |  Yes (setWeight, pause, analysis) |


Main Takeaways:
- Deployments are simple rolling updates, pod-level health only
- Rollout is progressive delivery (canary/blue green), traffic control, metric-based analysis

## Canary Deployment

I converted Helm‑managed `Deployment` into `Rollout`. So I created `rollout.yaml` with those canary steps:
```yaml
kind: Rollout
...
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

