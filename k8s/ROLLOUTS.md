# Lab 14 - Progressive Delivery with Argo Rollouts

## What I built

The Helm chart from Lab 13 now supports Argo Rollouts for the Python service:

- default canary Rollout with progressive weights `20 -> 40 -> 60 -> 80 -> 100`
- manual pause after the first 20% step
- 30 second timed pauses between later canary steps
- web AnalysisTemplate that checks `/health` during the canary
- blue-green Rollout mode with active and preview services
- compatibility path for the original Kubernetes Deployment with `--set rollout.enabled=false`

The chart renders a Rollout by default because Lab 14 replaces the Lab 13 Deployment when progressive delivery is needed.

## Files

- `k8s/devops-info-service/templates/rollout.yaml`
  Main Argo Rollout resource. It reuses the same labels, pod template, config checksum annotations, Vault annotations, probes, resources, service account, ConfigMaps, Secret, and PVC wiring as the old Deployment.

- `k8s/devops-info-service/templates/analysis-template.yaml`
  Web AnalysisTemplate used by the canary strategy. It calls the service health endpoint and expects `status` to be `healthy`.

- `k8s/devops-info-service/templates/preview-service.yaml`
  Preview service for the blue-green strategy. It is rendered only when `rollout.strategy=blueGreen`.

- `k8s/devops-info-service/templates/deployment.yaml`
  Original Deployment kept as an opt-out path. It renders only when `rollout.enabled=false`.

- `k8s/devops-info-service/values.yaml`
  Default canary rollout configuration.

- `k8s/devops-info-service/values-canary.yaml`
  Explicit canary values file.

- `k8s/devops-info-service/values-bluegreen.yaml`
  Blue-green values file.

## Argo Rollouts setup

Install the controller:

```bash
kubectl create namespace argo-rollouts
kubectl apply -n argo-rollouts -f https://github.com/argoproj/argo-rollouts/releases/latest/download/install.yaml
kubectl rollout status deployment/argo-rollouts -n argo-rollouts --timeout=180s
```

Install the kubectl plugin on macOS:

```bash
brew install argoproj/tap/kubectl-argo-rollouts
kubectl argo rollouts version
```

Install and open the dashboard:

```bash
kubectl apply -n argo-rollouts -f https://github.com/argoproj/argo-rollouts/releases/latest/download/dashboard-install.yaml
kubectl port-forward svc/argo-rollouts-dashboard -n argo-rollouts 3100:3100
```

Dashboard URL:

```text
http://localhost:3100
```

Live verification from the local kind cluster:

```text
$ kubectl get pods,svc -n argo-rollouts -o wide
pod/argo-rollouts-5f64f8d68-lngmk             1/1 Running
pod/argo-rollouts-dashboard-755bbc64c-vbv66   1/1 Running
service/argo-rollouts-dashboard               ClusterIP 3100/TCP
service/argo-rollouts-metrics                 ClusterIP 8090/TCP

$ /tmp/argo-rollouts-plugin/kubectl-argo-rollouts-darwin-arm64 version
kubectl-argo-rollouts: v1.9.0+838d4e7
```

Verification commands:

```bash
kubectl get pods -n argo-rollouts
kubectl get crd rollouts.argoproj.io analysistemplates.argoproj.io
kubectl argo rollouts version
```

## Rollout vs Deployment

Both resources manage ReplicaSets from a pod template, but Rollout adds release strategy controls that a Deployment does not have.

| Capability | Deployment | Rollout |
| --- | --- | --- |
| Rolling update | Yes | Yes |
| Manual promotion gate | No | Yes |
| Canary weights | No | Yes |
| Blue-green active and preview services | No | Yes |
| Metric or web analysis | No | Yes |
| Abort and retry release operation | Limited rollback only | Yes |

Use a Deployment when a normal rolling update is enough. Use a Rollout when the release needs explicit traffic shaping, preview validation, metric gates, or fast abort semantics.

## Canary deployment

Render the default canary chart:

```bash
helm template devops-info-service k8s/devops-info-service --namespace lab14
```

Install it:

```bash
helm upgrade --install devops-info-service k8s/devops-info-service \
  --namespace lab14 \
  --create-namespace \
  -f k8s/devops-info-service/values-canary.yaml \
  --set service.nodePort=30082
```

I used `30082` locally because older lab releases already used `30080` and `30081`.

The canary strategy is:

```yaml
canary:
  steps:
    - setWeight: 20
    - pause: {}
    - analysis:
        templates:
          - templateName: devops-info-service-health-check
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

Trigger a canary rollout by changing an image tag or visible environment value:

```bash
helm upgrade devops-info-service k8s/devops-info-service \
  --namespace lab14 \
  -f k8s/devops-info-service/values-canary.yaml \
  --set env.serviceVersion=1.0.1
```

Watch the rollout:

```bash
kubectl argo rollouts get rollout devops-info-service -n lab14 -w
```

Promote through the manual 20% pause:

```bash
kubectl argo rollouts promote devops-info-service -n lab14
```

Abort a rollout:

```bash
kubectl argo rollouts abort devops-info-service -n lab14
kubectl argo rollouts get rollout devops-info-service -n lab14
```

Retry after an abort:

```bash
kubectl argo rollouts retry rollout devops-info-service -n lab14
```

Observed rollout progression:

```text
Status:          Paused
Message:         CanaryPauseStep
Strategy:        Canary
Step:            1/10
SetWeight:       20
ActualWeight:    25
```

After manual promotion, the web analysis passed:

```text
AnalysisRun  Successful  webcheck: 3 successful measurements
```

The rollout then completed:

```text
Status:          Healthy
Strategy:        Canary
Step:            10/10
SetWeight:       100
ActualWeight:    100
```

Abort test:

```text
rollout 'devops-info-service' aborted
Status:          Degraded
Message:         RolloutAborted: Rollout aborted update to revision 3
SetWeight:       0
ActualWeight:    0
ReplicaSet       revision 3 ScaledDown
ReplicaSet       revision 2 stable
```

## Automated analysis

The canary includes a web AnalysisTemplate:

```yaml
metrics:
  - name: webcheck
    interval: 10s
    count: 3
    failureLimit: 1
    successCondition: result == "healthy"
    provider:
      web:
        url: http://devops-info-service.lab14.svc:80/health
        jsonPath: "{$.status}"
```

The Python service health response contains:

```json
{
  "status": "healthy"
}
```

A successful analysis allows the canary to continue. A failed analysis marks the rollout unhealthy and prevents promotion. To test a failure without changing application code, install with a mismatched expected status:

```bash
helm upgrade devops-info-service k8s/devops-info-service \
  --namespace lab14 \
  -f k8s/devops-info-service/values-canary.yaml \
  --set rollout.canary.analysis.expectedStatus=broken \
  --set env.serviceVersion=1.0.2
```

Then inspect and abort:

```bash
kubectl argo rollouts get rollout devops-info-service -n lab14
kubectl get analysisrun -n lab14
kubectl argo rollouts abort devops-info-service -n lab14
```

Intentional failure evidence from `lab14-analysis`:

```text
Status:          Degraded
Message:         RolloutAborted: Rollout aborted update to revision 2:
                 Step-based analysis phase error/failed:
                 Metric "webcheck" assessed Failed due to failed (2) > failureLimit (1)

AnalysisRun      Failed
Canary ReplicaSet ScaledDown
Stable ReplicaSet Healthy
```

## Blue-green deployment

Render the blue-green chart:

```bash
helm template devops-info-service k8s/devops-info-service \
  --namespace lab14 \
  -f k8s/devops-info-service/values-bluegreen.yaml
```

Install it:

```bash
helm upgrade --install devops-info-service k8s/devops-info-service \
  --namespace lab14 \
  --create-namespace \
  -f k8s/devops-info-service/values-bluegreen.yaml \
  --server-side=false
```

With Helm v4, I used `--server-side=false` for blue-green updates. Argo Rollouts owns and mutates the active and preview Service selectors, and client-side Helm updates avoid fighting the controller over those fields.

The blue-green strategy is:

```yaml
blueGreen:
  activeService: devops-info-service
  previewService: devops-info-service-preview
  autoPromotionEnabled: false
  scaleDownDelaySeconds: 30
```

The active service keeps production traffic:

```bash
kubectl port-forward svc/devops-info-service -n lab14 8080:80
curl -fsS http://127.0.0.1:8080/health
```

The preview service exposes the new ReplicaSet before promotion:

```bash
kubectl port-forward svc/devops-info-service-preview -n lab14 8081:80
curl -fsS http://127.0.0.1:8081/health
```

Trigger a green deployment:

```bash
helm upgrade devops-info-service k8s/devops-info-service \
  --namespace lab14 \
  -f k8s/devops-info-service/values-bluegreen.yaml \
  --set env.serviceVersion=1.0.3 \
  --server-side=false
```

Test the preview service, then promote:

```bash
kubectl argo rollouts get rollout devops-info-service -n lab14 -w
kubectl argo rollouts promote devops-info-service -n lab14
```

Rollback after promotion:

```bash
kubectl argo rollouts undo devops-info-service -n lab14
```

Blue-green rollback is faster than canary rollback because service selection switches between ReplicaSets instead of stepping traffic weights back over time.

Observed blue-green preview evidence from `lab14-bluegreen2`:

```text
Status:          Paused
Message:         BlueGreenPause
Strategy:        BlueGreen

revision 2 ReplicaSet  preview
revision 1 ReplicaSet  stable,active
```

The active and preview services selected different ReplicaSets:

```text
devops-info-service-bg2 selector={"rollouts-pod-template-hash":"76456f9b84"}
devops-info-service-bg2-preview selector={"rollouts-pod-template-hash":"75896ccd87"}
```

Active service before promotion:

```json
{
  "version": "1.0.0",
  "hostname": "devops-info-service-bg2-76456f9b84-4hv8w"
}
```

Preview service before promotion:

```json
{
  "version": "1.0.1",
  "hostname": "devops-info-service-bg2-75896ccd87-7jqm9"
}
```

After promotion, a fresh active connection served the new version:

```json
{
  "version": "1.0.1",
  "hostname": "devops-info-service-bg2-75896ccd87-7jqm9"
}
```

Rollback was staged with `undo` and switched after promotion:

```text
rollout 'devops-info-service-bg2' undo
Status: Paused
revision 3 ReplicaSet preview
revision 2 ReplicaSet stable,active

rollout 'devops-info-service-bg2' promoted
Status: Healthy
revision 3 ReplicaSet stable,active
```

After rollback, the active service served `1.0.0` again:

```json
{
  "version": "1.0.0",
  "hostname": "devops-info-service-bg2-76456f9b84-j42kh"
}
```

## Strategy comparison

| Strategy | Best use | Pros | Cons |
| --- | --- | --- | --- |
| Canary | Risky changes, high traffic services, changes needing live sampling | Limits blast radius, supports analysis gates, gradual confidence | Slower, users can temporarily see mixed versions |
| Blue-green | Releases needing preview validation and instant cutover | Easy preview testing, instant promotion, instant rollback | Needs roughly double capacity during rollout |

My default recommendation is canary for user-facing services when a gradual release is acceptable. I would use blue-green when the release must be tested as a complete environment before traffic moves, or when mixed versions are unsafe.

## Command reference

```bash
kubectl argo rollouts list rollouts -n lab14
kubectl argo rollouts get rollout devops-info-service -n lab14
kubectl argo rollouts get rollout devops-info-service -n lab14 -w
kubectl argo rollouts promote devops-info-service -n lab14
kubectl argo rollouts abort devops-info-service -n lab14
kubectl argo rollouts retry rollout devops-info-service -n lab14
kubectl argo rollouts undo devops-info-service -n lab14
kubectl describe rollout devops-info-service -n lab14
kubectl get replicasets,pods,svc,analysisrun -n lab14
helm lint k8s/devops-info-service
helm template devops-info-service k8s/devops-info-service --namespace lab14
helm template devops-info-service k8s/devops-info-service --namespace lab14 -f k8s/devops-info-service/values-bluegreen.yaml
```

## Local validation

Static validation completed:

```text
$ helm lint k8s/devops-info-service
1 chart(s) linted, 0 chart(s) failed
```

Rendered canary resources include:

```text
kind: AnalysisTemplate
name: devops-info-service-health-check
kind: Rollout
setWeight: 20
templateName: devops-info-service-health-check
setWeight: 40
setWeight: 60
setWeight: 80
setWeight: 100
```

Rendered blue-green resources include:

```text
kind: Service
name: devops-info-service-preview
kind: Rollout
blueGreen:
activeService: devops-info-service
previewService: devops-info-service-preview
autoPromotionEnabled: false
```

Live cluster validation was completed after Docker was started. One Helm-specific caveat remains: `helm --wait` timed out on the Rollout CRD even while the Rollouts controller reported the resource healthy, so rollout readiness was verified with the Argo Rollouts CLI instead.

```text
$ /tmp/argo-rollouts-plugin/kubectl-argo-rollouts-darwin-arm64 get rollout devops-info-service -n lab14
Status: Healthy
```
