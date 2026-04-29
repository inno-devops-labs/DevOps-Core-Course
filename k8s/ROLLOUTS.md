# Lab 14 - Progressive Delivery with Argo Rollouts

Prepared on `2026-04-29` on branch `lab14`.

This lab converts the `k8s/devops-info` Helm chart from a Kubernetes `Deployment` to an Argo Rollouts `Rollout` and demonstrates canary, blue-green, and analysis-driven rollback flows.

## 1. Implemented Files

Chart changes:

- `k8s/devops-info/templates/rollout.yaml` - default workload when `rollout.enabled=true`
- `k8s/devops-info/templates/deployment.yaml` - fallback only when `rollout.enabled=false`
- `k8s/devops-info/templates/preview-service.yaml` - blue-green preview service
- `k8s/devops-info/templates/analysis-template.yaml` - web AnalysisTemplate for canary checks
- `k8s/devops-info/values.yaml` - canary defaults and analysis settings
- `k8s/devops-info/values-bluegreen.yaml` - blue-green override
- `k8s/devops-info/values-analysis-fail.yaml` - intentional failing analysis override
- `k8s/argocd/application-rollouts-bluegreen.yaml` - optional ArgoCD app for blue-green

ArgoCD manifests were moved from `targetRevision: lab13` to `targetRevision: lab14` so GitOps points at the current branch.

## 2. Argo Rollouts Setup

Controller and dashboard installation:

```bash
kubectl create namespace argo-rollouts
kubectl apply -n argo-rollouts -f https://github.com/argoproj/argo-rollouts/releases/latest/download/install.yaml
kubectl apply -n argo-rollouts -f https://github.com/argoproj/argo-rollouts/releases/latest/download/dashboard-install.yaml
```

Local plugin installation:

```bash
curl -L -o /tmp/kubectl-argo-rollouts \
  https://github.com/argoproj/argo-rollouts/releases/latest/download/kubectl-argo-rollouts-linux-amd64
chmod +x /tmp/kubectl-argo-rollouts
mv /tmp/kubectl-argo-rollouts ~/.local/bin/kubectl-argo-rollouts
```

Verified plugin version:

```text
kubectl-argo-rollouts: v1.9.0+838d4e7
```

Verified controller CRDs:

```text
rollouts.argoproj.io
analysistemplates.argoproj.io
analysisruns.argoproj.io
```

Verified controller and dashboard pods:

```text
argo-rollouts-6c76c49cd8-7tjf8           1/1 Running
argo-rollouts-dashboard-984b9675-n4sj7   1/1 Running
```

Dashboard access:

```bash
kubectl -n argo-rollouts port-forward svc/argo-rollouts-dashboard 3100:3100
```

Open `http://localhost:3100/rollouts/`. In the local headless run, the dashboard service was checked from inside the cluster and returned the Argo Rollouts HTML entrypoint:

```text
<title>Argo Rollouts</title>
```

## 3. Rollout vs Deployment

The pod template, selectors, probes, service account, volumes, security context, resources, and labels are the same as the old Deployment.

The important differences are:

- `apiVersion: argoproj.io/v1alpha1` and `kind: Rollout`
- `spec.strategy.canary` or `spec.strategy.blueGreen` replaces `spec.strategy.rollingUpdate`
- Rollouts create and control ReplicaSets like Deployments, but add pause, promotion, abort, undo, analysis, active service, and preview service controls
- `kubectl rollout` is replaced by `kubectl argo rollouts` for progressive delivery operations

## 4. Canary Deployment

Default canary configuration in `values.yaml`:

```yaml
rollout:
  enabled: true
  strategy: canary
  canary:
    weights: [20, 40, 60, 80, 100]
    pauseDuration: 30s
```

Rendered strategy:

```yaml
strategy:
  canary:
    steps:
      - setWeight: 20
      - pause: {}
      - analysis:
          templates:
            - templateName: devops-info-canary-webcheck
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

Validation commands:

```bash
helm lint k8s/devops-info
helm template devops-info-canary k8s/devops-info \
  -n rollouts-canary \
  -f k8s/devops-info/values.yaml \
  -f k8s/devops-info/values-dev.yaml \
  --set replicaCount=5 \
  --set service.type=ClusterIP \
  --set service.nodePort=null
```

Initial 20 percent pause after updating `SERVICE_VERSION=1.0.1`:

```text
Status:          Paused
Message:         CanaryPauseStep
Step:            1/10
SetWeight:       20
ActualWeight:    20
Updated:         1
Ready:           5
Available:       5
```

Manual promotion:

```bash
kubectl argo rollouts promote devops-info-canary -n rollouts-canary
```

After promotion, the AnalysisRun executed and the rollout automatically advanced through the timed pauses:

```text
AnalysisRun devops-info-canary-55bbc57b55-2-2   Successful
Progressing - waiting for all steps to complete
Healthy
```

Abort test:

```bash
kubectl argo rollouts abort devops-info-canary -n rollouts-canary
```

Observed result:

```text
Status:  Degraded
Message: RolloutAborted: Rollout aborted update to revision 3

devops-info-canary-55bbc57b55   desired 5   stable
devops-info-canary-85fcb58d4    desired 0   aborted canary
```

The aborted canary ReplicaSet scaled to zero and traffic returned to the previous stable ReplicaSet. The demo namespace was then restored with:

```bash
kubectl argo rollouts undo devops-info-canary -n rollouts-canary
```

## 5. Blue-Green Deployment

Blue-green is enabled with:

```bash
helm template devops-info-bluegreen k8s/devops-info \
  -n rollouts-bluegreen \
  -f k8s/devops-info/values.yaml \
  -f k8s/devops-info/values-dev.yaml \
  -f k8s/devops-info/values-bluegreen.yaml
```

Rendered strategy:

```yaml
strategy:
  blueGreen:
    activeService: devops-info-bluegreen
    previewService: devops-info-bluegreen-preview
    autoPromotionEnabled: false
    scaleDownDelaySeconds: 30
```

After applying `SERVICE_VERSION=1.0.1`, the rollout paused before active cutover:

```text
Status:   Paused
Message:  BlueGreenPause
```

Service selectors before promotion:

```text
devops-info-bluegreen         rollouts-pod-template-hash=764c4cf6ff
devops-info-bluegreen-preview rollouts-pod-template-hash=78bccdbf9f
```

The preview pod contained the new version while the active pod still served the old version:

```text
preview pod: SERVICE_VERSION=1.0.1, SERVICE_VARIANT=green-preview
active pod:  SERVICE_VERSION=1.0.0, SERVICE_VARIANT=blue-green
```

Promotion:

```bash
kubectl argo rollouts promote devops-info-bluegreen -n rollouts-bluegreen
```

After promotion, the active service switched immediately:

```text
devops-info-bluegreen         rollouts-pod-template-hash=78bccdbf9f
devops-info-bluegreen-preview rollouts-pod-template-hash=78bccdbf9f
Status: Healthy
```

Instant rollback test:

```bash
kubectl argo rollouts undo devops-info-bluegreen -n rollouts-bluegreen
```

After undo, the active service selector switched back:

```text
devops-info-bluegreen         rollouts-pod-template-hash=764c4cf6ff
devops-info-bluegreen-preview rollouts-pod-template-hash=764c4cf6ff
Status: Healthy
```

## 6. Automated Analysis Bonus

The default canary includes a web AnalysisTemplate:

```yaml
provider:
  web:
    url: http://devops-info-canary.rollouts-canary.svc.cluster.local:80/ready
    jsonPath: "{$.status}"
successCondition: result == "ready"
interval: 10s
count: 3
failureLimit: 1
```

Intentional failure was tested by layering `values-analysis-fail.yaml`, which changes the check path to `/missing`.

Observed failed AnalysisRun:

```text
AnalysisRun devops-info-canary-64c7f8bcf8-5-2   Error
Metric "webcheck" assessed Error due to consecutiveErrors (5) > consecutiveErrorLimit (4)
Error Message: received non 2xx response code: 404
```

Observed automatic abort:

```text
Status:  Degraded
Message: RolloutAborted: Rollout aborted update to revision 5:
Step-based analysis phase error/failed
```

The namespace was restored by reapplying the normal `/ready` analysis and verifying:

```text
kubectl argo rollouts status devops-info-canary -n rollouts-canary
Healthy
```

## 7. Strategy Comparison

| Strategy | Strengths | Tradeoffs | Best use |
|---|---|---|---|
| Canary | Gradual exposure, metric checks before full release, low blast radius | Mixed versions run at the same time, rollback is progressive unless aborted early | User-facing APIs where risk should be reduced gradually |
| Blue-green | Active traffic switches instantly, preview can be tested before promotion, rollback is instant | Needs both versions running during release, all traffic moves at once | Releases that need final manual verification and fast rollback |

Recommendation:

- Use canary for normal production API releases because it limits exposure and allows automated analysis.
- Use blue-green for high-confidence releases where preview validation and instant rollback are more important than gradual exposure.
- Keep `autoPromotionEnabled: false` for production unless metrics and smoke tests are mature.

## 8. CLI Reference

```bash
kubectl argo rollouts version --short
kubectl argo rollouts get rollout devops-info-canary -n rollouts-canary
kubectl argo rollouts status devops-info-canary -n rollouts-canary
kubectl argo rollouts promote devops-info-canary -n rollouts-canary
kubectl argo rollouts abort devops-info-canary -n rollouts-canary
kubectl argo rollouts undo devops-info-canary -n rollouts-canary

kubectl get rollout,rs,pods,analysisrun -n rollouts-canary
kubectl get svc -n rollouts-bluegreen -o wide
kubectl describe analysisrun -n rollouts-canary <analysisrun-name>
kubectl port-forward -n argo-rollouts svc/argo-rollouts-dashboard 3100:3100
```

## 9. Local Environment Notes

The existing `kind-lab13` host kubeconfig returned EOF on `https://127.0.0.1:46841`, so live validation used the admin kubeconfig from inside the kind control-plane:

```bash
docker exec lab13-control-plane kubectl --kubeconfig /etc/kubernetes/admin.conf ...
```

The kind node could not pull from GitHub or Quay directly. Controller and dashboard images were pulled on the host, loaded into kind, then patched to local image names with `imagePullPolicy: Never` for this local run. This was an environment workaround; the repository manifests use the standard upstream install method.
