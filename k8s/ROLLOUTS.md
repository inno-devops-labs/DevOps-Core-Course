# Lab 14 - Progressive Delivery with Argo Rollouts

## Implementation Summary

The Helm chart from Labs 10-13 was converted from a regular Kubernetes `Deployment` to an Argo Rollouts `Rollout`. The default Lab 14 deployment now uses progressive delivery, while the previous Deployment behavior is still available with `--set rollout.enabled=false`.

Implemented files:

- [`devops-info-service/templates/rollout.yaml`](devops-info-service/templates/rollout.yaml)
- [`devops-info-service/templates/analysis-template.yaml`](devops-info-service/templates/analysis-template.yaml)
- [`devops-info-service/templates/preview-service.yaml`](devops-info-service/templates/preview-service.yaml)
- [`devops-info-service/values.yaml`](devops-info-service/values.yaml)
- [`devops-info-service/values-canary.yaml`](devops-info-service/values-canary.yaml)
- [`devops-info-service/values-bluegreen.yaml`](devops-info-service/values-bluegreen.yaml)
- [`argocd/application-rollouts-canary.yaml`](argocd/application-rollouts-canary.yaml)
- [`argocd/application-rollouts-bluegreen.yaml`](argocd/application-rollouts-bluegreen.yaml)

The ArgoCD applications were updated to track `targetRevision: lab14`, so the GitOps deployment reconciles the Lab 14 version of the chart.

## Argo Rollouts Setup

The Argo Rollouts namespace was created and the controller was installed from the official release manifest.

```bash
kubectl create namespace argo-rollouts
kubectl apply -n argo-rollouts -f https://github.com/argoproj/argo-rollouts/releases/latest/download/install.yaml
```

Result:

- Namespace `argo-rollouts` was created.
- The Argo Rollouts controller Deployment, ServiceAccount, RBAC resources, and CRDs were applied.
- The `rollouts.argoproj.io` and `analysisruns.argoproj.io` resources became available through the Kubernetes API.

Controller verification:

```bash
kubectl get pods -n argo-rollouts
kubectl wait --for=condition=ready pod -l app.kubernetes.io/name=argo-rollouts -n argo-rollouts --timeout=120s
kubectl argo rollouts version
```

Result:

- The controller pod reached `Running` and `Ready`.
- `kubectl argo rollouts version` returned the installed controller and CLI versions.
- The cluster accepted `Rollout` and `AnalysisTemplate` manifests from the Helm chart.

The dashboard was installed and exposed locally:

```bash
kubectl apply -n argo-rollouts -f https://github.com/argoproj/argo-rollouts/releases/latest/download/dashboard-install.yaml
kubectl port-forward svc/argo-rollouts-dashboard -n argo-rollouts 3100:3100
```

Result:

- The dashboard service became available on `http://localhost:3100`.
- The canary and blue-green rollouts were visible in the dashboard after deployment.

## Rollout vs Deployment

The original chart rendered a Kubernetes `Deployment` with a `RollingUpdate` strategy:

```yaml
strategy:
  type: RollingUpdate
  rollingUpdate:
    maxSurge: 1
    maxUnavailable: 0
```

The Lab 14 chart renders an Argo Rollouts `Rollout`:

```yaml
apiVersion: argoproj.io/v1alpha1
kind: Rollout
```

The pod template, labels, probes, resources, volumes, ConfigMaps, Secrets, PVC, and ServiceAccount stayed the same. The important difference is the strategy section. Argo Rollouts adds canary steps, manual pauses, blue-green service switching, analysis runs, promotion, abort, and undo operations.

The chart can still render the old Deployment path:

```bash
helm template devops-info k8s/devops-info-service --set rollout.enabled=false
```

Result:

- The rendered manifest contained `kind: Deployment`.
- No `Rollout`, `AnalysisTemplate`, or preview service was rendered.

## Canary Deployment

The canary deployment was configured in [`values-canary.yaml`](devops-info-service/values-canary.yaml). It uses five replicas and a ClusterIP service so it can run beside the blue-green demo without a NodePort conflict.

Local render check:

```bash
helm template devops-info-canary k8s/devops-info-service \
  --namespace rollouts-canary \
  -f k8s/devops-info-service/values-canary.yaml
```

Result:

- The chart rendered one active Service.
- The chart rendered one `AnalysisTemplate` named `success-rate`.
- The chart rendered one `Rollout` named `devops-info-canary-devops-info-service`.
- No Kubernetes `Deployment` was rendered for the canary release.

Cluster deployment:

```bash
helm upgrade --install devops-info-canary k8s/devops-info-service \
  --namespace rollouts-canary \
  --create-namespace \
  -f k8s/devops-info-service/values-canary.yaml
```

Result:

- Release `devops-info-canary` was installed in namespace `rollouts-canary`.
- The rollout created the initial stable ReplicaSet.
- The service selected the stable pods.
- The Argo Rollouts dashboard showed the rollout as healthy after the initial deployment.

Configured canary steps:

```yaml
steps:
  - setWeight: 20
  - pause: {}
  - analysis:
      templates:
        - templateName: success-rate
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

A new revision was triggered with a configuration change:

```bash
helm upgrade devops-info-canary k8s/devops-info-service \
  --namespace rollouts-canary \
  -f k8s/devops-info-service/values-canary.yaml \
  --set config.logLevel=DEBUG
```

Rollout watch:

```bash
kubectl argo rollouts get rollout devops-info-canary-devops-info-service -n rollouts-canary -w
```

Result:

- A new ReplicaSet was created for the updated pod template.
- The rollout moved to 20% canary traffic.
- The rollout paused at the manual promotion step.
- The dashboard showed both stable and canary ReplicaSets.

Manual promotion:

```bash
kubectl argo rollouts promote devops-info-canary-devops-info-service -n rollouts-canary
```

Result:

- The rollout continued past the manual pause.
- The `success-rate` analysis ran against the `/health` endpoint.
- After the analysis succeeded, the rollout advanced through 40%, 60%, 80%, and 100%.
- The new ReplicaSet became stable.

Abort test:

```bash
kubectl argo rollouts abort devops-info-canary-devops-info-service -n rollouts-canary
kubectl argo rollouts get rollout devops-info-canary-devops-info-service -n rollouts-canary
```

Result:

- The in-progress canary was aborted.
- Traffic returned to the stable ReplicaSet.
- The dashboard showed the rollout as aborted until it was retried or superseded by a new revision.

## Blue-Green Deployment

The blue-green deployment was configured in [`values-bluegreen.yaml`](devops-info-service/values-bluegreen.yaml). It uses a separate active service and preview service.

Local render check:

```bash
helm template devops-info-bluegreen k8s/devops-info-service \
  --namespace rollouts-bluegreen \
  -f k8s/devops-info-service/values-bluegreen.yaml
```

Result:

- The chart rendered an active Service named `devops-info-bluegreen-devops-info-service`.
- The chart rendered a preview Service named `devops-info-bluegreen-devops-info-service-preview`.
- The chart rendered one `Rollout` named `devops-info-bluegreen-devops-info-service`.
- No `AnalysisTemplate` was rendered for blue-green because this strategy uses manual preview and promotion.

Cluster deployment:

```bash
helm upgrade --install devops-info-bluegreen k8s/devops-info-service \
  --namespace rollouts-bluegreen \
  --create-namespace \
  -f k8s/devops-info-service/values-bluegreen.yaml
```

Result:

- Release `devops-info-bluegreen` was installed in namespace `rollouts-bluegreen`.
- The active service routed traffic to the stable ReplicaSet.
- The preview service was available for testing new revisions before promotion.

Configured blue-green strategy:

```yaml
blueGreen:
  activeService: devops-info-bluegreen-devops-info-service
  previewService: devops-info-bluegreen-devops-info-service-preview
  autoPromotionEnabled: false
  scaleDownDelaySeconds: 30
```

Preview and active services were tested with port-forwarding:

```bash
kubectl port-forward svc/devops-info-bluegreen-devops-info-service -n rollouts-bluegreen 8080:80
kubectl port-forward svc/devops-info-bluegreen-devops-info-service-preview -n rollouts-bluegreen 8081:80
```

Health checks:

```bash
curl http://127.0.0.1:8080/health
curl http://127.0.0.1:8081/health
```

Result:

- The active service returned a healthy response from the stable version.
- The preview service returned a healthy response from the new version.
- The two services allowed the new version to be tested before production traffic was switched.

Promotion:

```bash
kubectl argo rollouts promote devops-info-bluegreen-devops-info-service -n rollouts-bluegreen
```

Result:

- The green ReplicaSet was promoted.
- The active service selector switched to the new ReplicaSet.
- The previous ReplicaSet remained available briefly according to `scaleDownDelaySeconds`.

Rollback:

```bash
kubectl argo rollouts undo devops-info-bluegreen-devops-info-service -n rollouts-bluegreen
kubectl argo rollouts get rollout devops-info-bluegreen-devops-info-service -n rollouts-bluegreen
```

Result:

- Traffic switched back to the previous ReplicaSet.
- Rollback was faster than the canary rollback path because blue-green changes service routing directly instead of moving through percentage-based steps.

## Automated Analysis

The canary rollout includes a web-based `AnalysisTemplate` named `success-rate`. This does not require Prometheus, so it works before the Lab 16 monitoring stack is installed.

Rendered analysis template:

```yaml
apiVersion: argoproj.io/v1alpha1
kind: AnalysisTemplate
metadata:
  name: success-rate
spec:
  metrics:
    - name: webcheck
      interval: 10s
      count: 3
      failureLimit: 1
      successCondition: "result == \"healthy\""
      provider:
        web:
          url: http://<release-fullname>.<namespace>.svc/health
          jsonPath: "{$.status}"
```

The application `/health` endpoint returns:

```json
{
  "status": "healthy"
}
```

Analysis verification:

```bash
kubectl get analysistemplates,analysisruns -n rollouts-canary
kubectl describe analysisrun -n rollouts-canary
```

Result:

- `AnalysisTemplate/success-rate` was created.
- An `AnalysisRun` was created during the canary rollout.
- The analysis completed successfully when `/health` returned `status: healthy`.

Failure test:

```bash
helm upgrade devops-info-canary k8s/devops-info-service \
  --namespace rollouts-canary \
  -f k8s/devops-info-service/values-canary.yaml \
  --set rollout.canary.analysis.path=/missing \
  --set podLabels.analysis-test=fail
```

Result:

- The analysis queried a missing path.
- The web metric failed.
- The rollout stopped instead of promoting the bad revision.

Recovery:

```bash
helm upgrade devops-info-canary k8s/devops-info-service \
  --namespace rollouts-canary \
  -f k8s/devops-info-service/values-canary.yaml \
  --set rollout.canary.analysis.path=/health \
  --set podLabels.analysis-test=ok
```

Result:

- The health check path was restored.
- A new revision was created.
- The analysis succeeded again and the rollout was able to continue.

## ArgoCD Flow

The Lab 14 namespaces and ArgoCD applications were applied:

```bash
kubectl apply -f k8s/argocd/namespaces.yaml
kubectl apply -f k8s/argocd/application-rollouts-canary.yaml
kubectl apply -f k8s/argocd/application-rollouts-bluegreen.yaml
```

Result:

- Namespaces `rollouts-canary` and `rollouts-bluegreen` were created.
- ArgoCD applications `devops-info-service-rollouts-canary` and `devops-info-service-rollouts-bluegreen` were created.
- Both applications pointed to `targetRevision: lab14`.

Manual sync:

```bash
argocd app sync devops-info-service-rollouts-canary
argocd app sync devops-info-service-rollouts-bluegreen
```

Result:

- The canary application synced the Helm chart with `values-canary.yaml`.
- The blue-green application synced the Helm chart with `values-bluegreen.yaml`.
- ArgoCD showed both applications as `Synced` and `Healthy` after reconciliation.

Status checks:

```bash
argocd app get devops-info-service-rollouts-canary
argocd app get devops-info-service-rollouts-bluegreen
kubectl get rollouts -A
```

Result:

- The cluster contained both Rollout resources.
- The canary rollout used the `canary` strategy.
- The blue-green rollout used the `blueGreen` strategy with active and preview services.

## Local Validation

The chart was validated locally after implementation.

```bash
helm lint k8s/devops-info-service
```

Result:

```text
==> Linting k8s/devops-info-service
[INFO] Chart.yaml: icon is recommended

1 chart(s) linted, 0 chart(s) failed
```

Rendered manifest checks:

```bash
helm template devops-info-canary k8s/devops-info-service --namespace rollouts-canary -f k8s/devops-info-service/values-canary.yaml
helm template devops-info-bluegreen k8s/devops-info-service --namespace rollouts-bluegreen -f k8s/devops-info-service/values-bluegreen.yaml
helm template devops-info k8s/devops-info-service --set rollout.enabled=false
```

Result:

- Canary rendering produced `Service`, `AnalysisTemplate`, and `Rollout`.
- Blue-green rendering produced active `Service`, preview `Service`, and `Rollout`.
- Legacy rendering produced `Deployment`.
- `git diff --check` returned no whitespace errors.

## Strategy Comparison

Canary is a good fit when a release should be exposed gradually and monitored before full promotion. It is safer for API and backend changes because traffic can move from 20% to 100% in controlled steps. The main drawback is that old and new versions may serve traffic at the same time.

Blue-green is a good fit when the new version should be tested separately before an instant switch. It is easier to reason about because production traffic goes to only one version at a time. The main drawback is higher resource usage because both versions can run during the release.

Recommendation:

- Use canary for production API changes with health or metrics checks.
- Use blue-green when manual preview is important.
- Use blue-green when rollback speed is the highest priority.
- Use standard Deployment only for simple workloads that do not need progressive delivery.

## CLI Reference

```bash
kubectl argo rollouts list rollouts -A
kubectl argo rollouts get rollout <name> -n <namespace> -w
kubectl argo rollouts promote <name> -n <namespace>
kubectl argo rollouts abort <name> -n <namespace>
kubectl argo rollouts retry rollout <name> -n <namespace>
kubectl argo rollouts undo <name> -n <namespace>
kubectl argo rollouts history <name> -n <namespace>
kubectl describe rollout <name> -n <namespace>
kubectl get rs,pods,svc,analysisruns -n <namespace>
```

## Dashboard Evidence

The dashboard was used to inspect the rollout state during each strategy test.

Observed states:

- Canary rollout paused at 20% before manual promotion.
- Canary rollout continued after `kubectl argo rollouts promote`.
- Canary analysis run completed successfully against `/health`.
- Canary abort returned traffic to the stable ReplicaSet.
- Blue-green preview service exposed the new ReplicaSet before promotion.
- Blue-green promotion switched active traffic to the green ReplicaSet.
