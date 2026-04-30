# Lab 14: Argo Rollouts Progressive Delivery

Helm chart source for this lab: `lab12c/k8s/devops-info`.

This lab replaces a classic `Deployment` with Argo `Rollout` and adds:
- canary traffic shifting with pauses and manual promotion;
- blue-green release flow with preview service;
- automated health analysis for rollback decisions.

## 1) Argo Rollouts setup

### Install controller

```powershell
kubectl create namespace argo-rollouts
kubectl apply -n argo-rollouts -f https://github.com/argoproj/argo-rollouts/releases/latest/download/install.yaml
kubectl get pods -n argo-rollouts
```

Expected: controller pod is `Running`.

### Install kubectl plugin (Windows PowerShell)

```powershell
$version = (Invoke-RestMethod https://api.github.com/repos/argoproj/argo-rollouts/releases/latest).tag_name
Invoke-WebRequest -Uri "https://github.com/argoproj/argo-rollouts/releases/download/$version/kubectl-argo-rollouts-windows-amd64.exe" -OutFile "$env:USERPROFILE\kubectl-argo-rollouts.exe"
[Environment]::SetEnvironmentVariable("Path", $env:Path + ";$env:USERPROFILE", [EnvironmentVariableTarget]::User)
```

Restart terminal and verify:

```powershell
kubectl argo rollouts version
```

### Install dashboard

```powershell
kubectl apply -n argo-rollouts -f https://github.com/argoproj/argo-rollouts/releases/latest/download/dashboard-install.yaml
kubectl port-forward svc/argo-rollouts-dashboard -n argo-rollouts 3100:3100
```

Open: `http://localhost:3100`.

## 2) Rollout vs Deployment (key differences)

- `kind` changes from `Deployment` to `Rollout`.
- `spec.strategy` supports advanced modes (`canary`, `blueGreen`), not only rolling update knobs.
- Rollouts can pause, require manual promotion, and run metric checks (`AnalysisTemplate`).
- Rollouts support explicit abort/retry flow for safer rollback handling.

## 3) Canary deployment implementation

### What was changed

- Added template `templates/rollout.yaml` (enabled by `rollouts.enabled`).
- Kept legacy `templates/deployment.yaml` behind guard `if not .Values.rollouts.enabled`.
- Default strategy in `values.yaml` is `canary`.
- Canary progression:
  - 20% -> manual pause
  - 40% -> pause 30s
  - 60% -> pause 30s
  - 80% -> pause 30s
  - 100%

### Deploy canary

```powershell
helm upgrade --install devops-info .\lab12c\k8s\devops-info -n default --create-namespace
kubectl argo rollouts get rollout devops-info -n default -w
```

Trigger new revision:

```powershell
helm upgrade --install devops-info .\lab12c\k8s\devops-info -n default `
  --set image.tag=lab14-canary-1 `
  --set env.RELEASE_ID=lab14-canary-1
```

Promote first manual pause:

```powershell
kubectl argo rollouts promote devops-info -n default
```

Abort rollout (rollback test):

```powershell
kubectl argo rollouts abort devops-info -n default
kubectl argo rollouts get rollout devops-info -n default
```

Retry aborted rollout:

```powershell
kubectl argo rollouts retry rollout devops-info -n default
```

## 4) Blue-green deployment implementation

### What was changed

- Added preview service template: `templates/service-preview.yaml`.
- Added blue-green values profile: `values-bluegreen.yaml`.
- `values-prod.yaml` also uses `rollouts.strategy=blueGreen`.
- Blue-green config uses:
  - `activeService: <release-name>`
  - `previewService: <release-name>-preview`
  - `autoPromotionEnabled: false` (manual cutover)

### Deploy blue-green

```powershell
helm upgrade --install devops-info-bg .\lab12c\k8s\devops-info -n default `
  -f .\lab12c\k8s\devops-info\values-bluegreen.yaml `
  --set env.RELEASE_ID=lab14-bg-blue
```

Trigger green revision:

```powershell
helm upgrade --install devops-info-bg .\lab12c\k8s\devops-info -n default `
  -f .\lab12c\k8s\devops-info\values-bluegreen.yaml `
  --set image.tag=lab14-bg-green `
  --set env.RELEASE_ID=lab14-bg-green
```

Port-forward active and preview:

```powershell
kubectl port-forward svc/devops-info-bg -n default 8080:80
kubectl port-forward svc/devops-info-bg-preview -n default 8081:80
```

Promote preview to active:

```powershell
kubectl argo rollouts promote devops-info-bg -n default
```

Instant rollback:

```powershell
kubectl argo rollouts undo devops-info-bg -n default
```

## 5) Bonus: automated analysis

### What was changed

- Added `templates/analysis-template.yaml`.
- Analysis is controlled by `rollouts.analysis.*` values and enabled by default.
- Canary steps can include analysis gate via values.
- Health check uses `/health` and expects JSON `{"status":"healthy"}`.

Example canary with analysis gate:

```yaml
rollouts:
  canary:
    steps:
      - setWeight: 20
      - analysis:
          templates:
            - templateName: devops-info-success-rate
      - pause: {}
      - setWeight: 100
```

Watch analysis runs:

```powershell
kubectl get analysisrun -n default
kubectl describe analysisrun -n default <analysisrun-name>
```

If analysis fails (failure limit reached), rollout is automatically aborted and traffic stays on stable ReplicaSet.

## 6) Strategy comparison and recommendations

### Canary

- Best for risky changes, gradual verification on real traffic.
- Lower blast radius due to percentage-based rollout.
- Slower release and rollback compared to hard switching.

Use when:
- new feature logic can fail partially;
- you need progressive exposure and close monitoring.

### Blue-green

- Best for fast cutover and fast rollback.
- Easy A/B validation via separate preview service.
- Requires extra resources because both versions run together.

Use when:
- release must switch instantly;
- preview acceptance tests are mandatory before go-live.

## 7) Useful CLI commands

```powershell
kubectl argo rollouts list rollouts -A
kubectl argo rollouts get rollout <name> -n <ns> -w
kubectl argo rollouts promote <name> -n <ns>
kubectl argo rollouts abort <name> -n <ns>
kubectl argo rollouts retry rollout <name> -n <ns>
kubectl argo rollouts undo <name> -n <ns>
kubectl argo rollouts dashboard
```

## 8) Screenshots checklist (dashboard)

Add screenshots to `lab13c/docs/`:
- canary rollout at 20% paused;
- canary promoted to 40/60/80;
- aborted canary rollback;
- blue-green preview and active before promotion;
- blue-green after promotion.
