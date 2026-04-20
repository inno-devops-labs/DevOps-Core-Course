# Lab 14 — Progressive Delivery with Argo Rollouts

## 1. Argo Rollouts Setup

### 1.1 Controller Installation

```bash
kubectl create namespace argo-rollouts
kubectl apply -n argo-rollouts -f https://github.com/argoproj/argo-rollouts/releases/latest/download/install.yaml
kubectl get pods -n argo-rollouts
```

Installation output:

```bash
PS C:\Users\zagur\DevOps\DevOps-Core-Course> kubectl get pods -n argo-rollouts
NAME                             READY   STATUS    RESTARTS   AGE
argo-rollouts-79b89d8856-tvttj   1/1     Running   0          147m
```

### 1.2 Kubectl Plugin

```powershell
$version = (Invoke-RestMethod https://api.github.com/repos/argoproj/argo-rollouts/releases/latest).tag_name
$url = "https://github.com/argoproj/argo-rollouts/releases/download/" + $version + "/kubectl-argo-rollouts-windows-amd64"
Invoke-WebRequest -Uri $url -OutFile kubectl-argo-rollouts.exe
```

```bash
PS C:\Users\zagur\DevOps\DevOps-Core-Course> kubectl argo rollouts version
kubectl-argo-rollouts: v1.9.0+838d4e7
  BuildDate: 2026-03-20T21:15:27Z
  GitCommit: 838d4e792be666ec11bd0c80331e0c5511b5010e
  GitTreeState: clean
  GoVersion: go1.24.13
  Compiler: gc
  Platform: windows/amd64
```

### 1.3 Dashboard Access

```bash
kubectl argo rollouts dashboard -n dev
```

Open:

```text
http://localhost:3100/rollouts
```

### 1.4 Rollout vs Deployment

A Rollout replaces a standard Deployment when progressive delivery is needed. The pod template, selectors, probes, resources, and container spec remain almost identical, but the resource kind changes from `Deployment` to `Rollout`, and the `strategy` section gains advanced rollout options such as `canary` or `blueGreen`, manual promotion, abort, preview service handling, and controlled rollback.

## 2. Canary Deployment

### 2.1 Helm Changes

Files changed:
- `templates/deployment.yaml` wrapped with `if not .Values.rollout.enabled`
- `templates/rollout.yaml` added
- `templates/service-canary.yaml` added
- `values.yaml` / `values-dev.yaml` updated

### 2.2 Canary Strategy

Dev environment uses canary rollout:

```yaml
strategy:
  canary:
    maxSurge: 1
    maxUnavailable: 0
    stableService: devops-info-service-dev-devops-info-service
    canaryService: devops-info-service-dev-devops-info-service-canary
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

### 2.3 Deploy Canary Version

```bash
helm lint k8s/devops-info-service
helm template devops-info-service-dev k8s/devops-info-service -f k8s/devops-info-service/values-dev.yaml
```

Pushed Helm changes to Git, then synced the ArgoCD dev app:

```bash
argocd app sync devops-info-service-dev --prune
kubectl get rollout -n dev
kubectl argo rollouts get rollout devops-info-service-dev-devops-info-service -n dev -w
```

Output:

```bash
NAME                                                                     KIND        STATUS        AGE    INFO
⟳ devops-info-service-dev-devops-info-service                            Rollout     ✔ Healthy     137m   
├──# revision:2                                                                                           
│  └──⧉ devops-info-service-dev-devops-info-service-76c8fcb6d8           ReplicaSet  ✔ Healthy     90m    stable
│     └──□ devops-info-service-dev-devops-info-service-76c8fcb6d8-q8m2f  Pod         ✔ Running     4m17s  ready:2/2
└──# revision:1                                                                                           
   └──⧉ devops-info-service-dev-devops-info-service-7c5f5d96df           ReplicaSet  • ScaledDown  137m   
Name:            devops-info-service-dev-devops-info-service
Namespace:       dev
Status:          ✔ Healthy
Strategy:        Canary
  Step:          9/9
  SetWeight:     100
  ActualWeight:  100
Images:          devops-info-service:dev_canary (stable)
Replicas:
  Desired:       1
  Current:       1
  Updated:       1
  Ready:         1
  Available:     1

NAME                                                                     KIND        STATUS        AGE    INFO
⟳ devops-info-service-dev-devops-info-service                            Rollout     ✔ Healthy     137m   
├──# revision:2                                                                                           
│  └──⧉ devops-info-service-dev-devops-info-service-76c8fcb6d8           ReplicaSet  ✔ Healthy     90m    stable
│     └──□ devops-info-service-dev-devops-info-service-76c8fcb6d8-q8m2f  Pod         ✔ Running     4m18s  ready:2/2
└──# revision:1                                                                                           
   └──⧉ devops-info-service-dev-devops-info-service-7c5f5d96df           ReplicaSet  • ScaledDown  137m   
PS C:\Users\zagur\DevOps\DevOps-Core-Course> 
```

### 2.4 Trigger a Canary Update

Change the pod template, for example by updating `image.tag` in `values-dev.yaml` or modifying an env var in the chart, commit and push it, then sync again.

```bash
git add .
git commit -m "lab14: trigger canary rollout"
git push
argocd app sync devops-info-service-dev --prune
kubectl argo rollouts get rollout devops-info-service-dev-devops-info-service -n dev -w
```

```bash
NAME                                                                     KIND        STATUS        AGE    INFO
⟳ devops-info-service-dev-devops-info-service                            Rollout     ✔ Healthy     137m   
├──# revision:2                                                                                           
│  └──⧉ devops-info-service-dev-devops-info-service-76c8fcb6d8           ReplicaSet  ✔ Healthy     90m    stable
│     └──□ devops-info-service-dev-devops-info-service-76c8fcb6d8-q8m2f  Pod         ✔ Running     4m17s  ready:2/2
└──# revision:1                                                                                           
   └──⧉ devops-info-service-dev-devops-info-service-7c5f5d96df           ReplicaSet  • ScaledDown  137m   
Name:            devops-info-service-dev-devops-info-service
Namespace:       dev
Status:          ✔ Healthy
Strategy:        Canary
  Step:          9/9
  SetWeight:     100
  ActualWeight:  100
Images:          devops-info-service:dev_canary (stable)
Replicas:
  Desired:       1
  Current:       1
  Updated:       1
  Ready:         1
  Available:     1

NAME                                                                     KIND        STATUS        AGE    INFO
⟳ devops-info-service-dev-devops-info-service                            Rollout     ✔ Healthy     137m   
├──# revision:2                                                                                           
│  └──⧉ devops-info-service-dev-devops-info-service-76c8fcb6d8           ReplicaSet  ✔ Healthy     90m    stable
│     └──□ devops-info-service-dev-devops-info-service-76c8fcb6d8-q8m2f  Pod         ✔ Running     4m18s  ready:2/2
└──# revision:1                                                                                           
   └──⧉ devops-info-service-dev-devops-info-service-7c5f5d96df           ReplicaSet  • ScaledDown  137m   
PS C:\Users\zagur\DevOps\DevOps-Core-Course> 
```

### 2.5 Manual Promotion and Automatic Progression

```bash
kubectl argo rollouts promote devops-info-service-dev-devops-info-service -n dev
kubectl argo rollouts get rollout devops-info-service-dev-devops-info-service -n dev -w
```

```bash
PS C:\Users\zagur\DevOps\DevOps-Core-Course> kubectl argo rollouts promote devops-info-service-dev-devops-info-service -n dev
rollout 'devops-info-service-dev-devops-info-service' promoted
```

![](/k8s/screenshots/revision2.png)

Expected behavior:
- first pause at 20% requires manual promotion;
- next pauses at 40%, 60%, and 80% continue automatically after 30 seconds each;
- rollout ends at 100%.

### 2.6 Abort / Rollback Test

During the rollout, abort it:

```bash
kubectl argo rollouts abort devops-info-service-dev-devops-info-service -n dev
kubectl argo rollouts get rollout devops-info-service-dev-devops-info-service -n dev -w
```

Optional retry:

```bash
kubectl argo rollouts retry rollout devops-info-service-dev-devops-info-service -n dev
```

![](/k8s/screenshots/after_abort.png)

## 3. Blue-Green Deployment

### 3.1 Helm Changes

Prod environment uses blue-green rollout:
- active service: existing main service
- preview service: `templates/service-preview.yaml`
- strategy defined in `values-prod.yaml`

### 3.2 Blue-Green Strategy

```yaml
strategy:
  blueGreen:
    activeService: devops-info-service-prod-devops-info-service
    previewService: devops-info-service-prod-devops-info-service-preview
    autoPromotionEnabled: false
    previewReplicaCount: 1
    scaleDownDelaySeconds: 30
```

### 3.3 Deploy Blue-Green Version

```bash
helm template devops-info-service-prod k8s/devops-info-service -f k8s/devops-info-service/values-prod.yaml
argocd app sync devops-info-service-prod --prune
kubectl get rollout,svc -n prod
kubectl argo rollouts get rollout devops-info-service-prod-devops-info-service -n prod -w
```

### 3.4 Test Preview vs Active

Port-forward both services:

```bash
kubectl port-forward svc/devops-info-service-prod-devops-info-service -n prod 8080:80
kubectl port-forward svc/devops-info-service-prod-devops-info-service-preview -n prod 8081:80
```

Then compare:

```bash
curl http://localhost:8080/
curl http://localhost:8081/
```

### 3.5 Promote Green to Active

```bash
kubectl argo rollouts promote devops-info-service-prod-devops-info-service -n prod
kubectl argo rollouts get rollout devops-info-service-prod-devops-info-service -n prod -w
```

### 3.6 Instant Rollback

After promotion, trigger another update and abort it, or use undo:

```bash
kubectl argo rollouts undo devops-info-service-prod-devops-info-service -n prod
kubectl argo rollouts get rollout devops-info-service-prod-devops-info-service -n prod -w
```

## 4. Strategy Comparison

### Canary

Pros:
- gradual exposure to risk
- safer for customer-facing changes
- easier to observe behavior step by step

Cons:
- slower rollout process
- more operational steps
- without a traffic router, percentages are approximated through pod counts

### Blue-Green

Pros:
- instant switch between versions
- easy preview testing before promotion
- rollback is very fast

Cons:
- requires extra resources during preview
- all traffic switches at once on promotion

### Recommendation

- Use **canary** for risky application changes and staged validation.
- Use **blue-green** when preview testing is important and instant rollback is desired.
- For this project, dev is a good fit for canary experimentation, while prod is a good fit for blue-green validation and controlled promotion.

## 5. CLI Commands Reference

```bash
kubectl argo rollouts version
kubectl argo rollouts dashboard -n dev
kubectl argo rollouts list rollouts -n dev
kubectl argo rollouts get rollout <name> -n <namespace> -w
kubectl argo rollouts promote <name> -n <namespace>
kubectl argo rollouts abort <name> -n <namespace>
kubectl argo rollouts retry rollout <name> -n <namespace>
kubectl argo rollouts undo <name> -n <namespace>
```

## 6. Screenshots to Include

- Argo Rollouts dashboard main page
- Canary rollout paused at 20%
- Canary rollout after manual promotion
- Abort result in canary rollout
- Blue-green rollout with preview service
- Blue-green rollout after promotion
