# Lab 14 - Progressive Delivery with Argo Rollouts

Run date: April 29, 2026

## Review Result

The Lab 14 chart implementation is valid after cleanup:

- the normal chart path still renders a Kubernetes `Deployment`
- the canary profile renders an Argo `Rollout` plus `AnalysisTemplate`
- the blue-green profile renders an Argo `Rollout` plus active and preview services
- rollout-specific values disable the older Helm install hooks, because those hooks can run before Argo Rollout pods are ready and make a valid rollout install look failed

Live Argo Rollouts controller/dashboard actions were not executed in this review environment. The evidence below is based on Helm lint and manifest rendering, with exact commands for a live cluster run.

## Files

Lab 14 resources:

- `k8s/devops-info-service/templates/rollout.yaml`
- `k8s/devops-info-service/templates/preview-service.yaml`
- `k8s/devops-info-service/templates/analysis-template.yaml`
- `k8s/devops-info-service/values-rollout-canary.yaml`
- `k8s/devops-info-service/values-rollout-bluegreen.yaml`

Supporting updates:

- `k8s/devops-info-service/templates/NOTES.txt`
- `k8s/devops-info-service/templates/_helpers.tpl`
- `k8s/devops-info-service/values.yaml`

## Validation

Commands run locally:

```powershell
.\.tools\helm.exe lint .\k8s\devops-info-service
.\.tools\helm.exe template devops-info-service .\k8s\devops-info-service
.\.tools\helm.exe template devops-info-service-canary .\k8s\devops-info-service -f .\k8s\devops-info-service\values-rollout-canary.yaml --namespace canary
.\.tools\helm.exe template devops-info-service-bluegreen .\k8s\devops-info-service -f .\k8s\devops-info-service\values-rollout-bluegreen.yaml --namespace bluegreen
```

Result:

```text
1 chart(s) linted, 0 chart(s) failed
```

The rendered manifests include the expected Lab 14 objects:

- default profile: `Deployment`
- canary profile: `Rollout`, `AnalysisTemplate`, `Service`
- blue-green profile: `Rollout`, active `Service`, preview `Service`

## Argo Rollouts Setup

Install controller and dashboard in a live cluster:

```powershell
kubectl create namespace argo-rollouts
kubectl apply -n argo-rollouts -f https://github.com/argoproj/argo-rollouts/releases/latest/download/install.yaml
kubectl apply -n argo-rollouts -f https://github.com/argoproj/argo-rollouts/releases/latest/download/dashboard-install.yaml
kubectl get pods -n argo-rollouts
kubectl port-forward svc/argo-rollouts-dashboard -n argo-rollouts 3100:3100
```

CLI plugin checks:

```powershell
kubectl argo rollouts version
kubectl argo rollouts get rollout <name> -n <namespace> -w
kubectl argo rollouts promote <name> -n <namespace>
kubectl argo rollouts abort <name> -n <namespace>
kubectl argo rollouts retry rollout <name> -n <namespace>
```

## Rollout vs Deployment

The chart supports both workload modes.

Default mode:

```yaml
rollout:
  enabled: false
```

This renders `apps/v1 Deployment` and preserves behavior from earlier labs.

Lab 14 mode:

```yaml
rollout:
  enabled: true
```

This renders `argoproj.io/v1alpha1 Rollout`, which adds canary steps, blue-green promotion, manual pauses, aborts, retries, and analysis.

The rollout values also set `persistence.enabled: false`. Progressive delivery profiles need multiple replicas, while the earlier lab's default PVC is `ReadWriteOnce`; disabling persistence keeps the rollout examples stateless and schedulable.

## Canary Deployment

Canary values:

```yaml
replicaCount: 5

persistence:
  enabled: false

service:
  type: ClusterIP

hooks:
  enabled: false

rollout:
  enabled: true
  strategy: canary
  analysis:
    enabled: true
```

Rendered strategy:

```yaml
strategy:
  canary:
    maxSurge: "25%"
    maxUnavailable: "0"
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

Live run:

```powershell
.\.tools\helm.exe upgrade --install devops-info-service-canary .\k8s\devops-info-service --namespace canary --create-namespace -f .\k8s\devops-info-service\values-rollout-canary.yaml
kubectl argo rollouts get rollout devops-info-service-canary -n canary -w
kubectl argo rollouts promote devops-info-service-canary -n canary
```

Rollback test:

```powershell
kubectl argo rollouts abort devops-info-service-canary -n canary
kubectl argo rollouts get rollout devops-info-service-canary -n canary -w
kubectl argo rollouts retry rollout devops-info-service-canary -n canary
```

## Blue-Green Deployment

Blue-green values:

```yaml
replicaCount: 4

persistence:
  enabled: false

service:
  type: ClusterIP

hooks:
  enabled: false

rollout:
  enabled: true
  strategy: blueGreen
  blueGreen:
    autoPromotionEnabled: false
```

Rendered strategy:

```yaml
strategy:
  blueGreen:
    activeService: devops-info-service-bluegreen
    previewService: devops-info-service-bluegreen-preview
    autoPromotionEnabled: false
```

Live run:

```powershell
.\.tools\helm.exe upgrade --install devops-info-service-bluegreen .\k8s\devops-info-service --namespace bluegreen --create-namespace -f .\k8s\devops-info-service\values-rollout-bluegreen.yaml
kubectl argo rollouts get rollout devops-info-service-bluegreen -n bluegreen -w
kubectl port-forward svc/devops-info-service-bluegreen 8080:80 -n bluegreen
kubectl port-forward svc/devops-info-service-bluegreen-preview 8081:80 -n bluegreen
kubectl argo rollouts promote devops-info-service-bluegreen -n bluegreen
```

Expected behavior in a live cluster:

- port `8080` serves the active version
- port `8081` serves the preview version before promotion
- promotion switches the active service to the preview ReplicaSet
- rollback is an immediate service selector switch

## Automated Analysis

Canary analysis is enabled in `values-rollout-canary.yaml`.

Rendered template:

```yaml
apiVersion: argoproj.io/v1alpha1
kind: AnalysisTemplate
spec:
  metrics:
    - name: web-healthcheck
      interval: "10s"
      count: 3
      failureLimit: 1
      successCondition: result == "healthy"
      provider:
        web:
          url: http://devops-info-service-canary.canary.svc.cluster.local:80/health
          jsonPath: "{$.status}"
```

The template calls `/health` and expects:

```json
{"status": "healthy"}
```

This demonstrates automated analysis without requiring Prometheus. Prometheus-based analysis can be added later when the monitoring lab stack is running.

## Strategy Comparison

Use canary when:

- risk should be reduced by gradual exposure
- behavior should be observed before full rollout
- metrics or manual gates should control promotion

Use blue-green when:

- a full preview environment is useful
- promotion and rollback must be instant
- temporary double capacity is acceptable

Recommendation:

- canary is the better default for normal application changes
- blue-green fits larger changes where preview validation and fast switching matter more than gradual exposure

## Notes for Screenshots

For final lab evidence in a live cluster, capture:

- controller pods running in `argo-rollouts`
- dashboard at `http://localhost:3100`
- canary paused at 20%
- canary progressing through 40%, 60%, and 80%
- canary abort and retry
- blue-green active and preview services before promotion
- blue-green active service after promotion
