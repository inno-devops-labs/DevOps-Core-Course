# Argo Rollouts – Progressive Delivery Documentation

## 1. Overview

Argo Rollouts is a Kubernetes controller that extends the native Deployment with advanced deployment strategies such as **Canary** and **Blue‑Green**. It enables:

- Gradual traffic shifting (Canary)
- Instant cut‑over with preview environments (Blue‑Green)
- Manual/auto promotion and rollback
- Metrics‑based analysis for automatic decisions

This documentation covers the complete setup and usage of Argo Rollouts for the DevOps Info Service application.

---

## 2. Installation

### 2.1 Install Argo Rollouts Controller

```bash
kubectl create namespace argo-rollouts
kubectl apply -n argo-rollouts -f https://github.com/argoproj/argo-rollouts/releases/latest/download/install.yaml
```

Verify:

```bash
kubectl get pods -n argo-rollouts
# NAME                               READY   STATUS    RESTARTS   AGE
# argo-rollouts-xxxxxxxxxx-xxxxx     1/1     Running   0          30s
```

### 2.2 Install kubectl Plugin

**macOS (Homebrew):**
```bash
brew install argoproj/tap/kubectl-argo-rollouts
```

**Linux:**
```bash
curl -LO https://github.com/argoproj/argo-rollouts/releases/latest/download/kubectl-argo-rollouts-linux-amd64
chmod +x kubectl-argo-rollouts-linux-amd64
sudo mv kubectl-argo-rollouts-linux-amd64 /usr/local/bin/kubectl-argo-rollouts
```

**Verify:**
```bash
kubectl argo rollouts version
```

### 2.3 Install Dashboard

```bash
kubectl apply -n argo-rollouts -f https://github.com/argoproj/argo-rollouts/releases/latest/download/dashboard-install.yaml
kubectl port-forward svc/argo-rollouts-dashboard -n argo-rollouts 3100:3100
```

Access the dashboard: http://localhost:3100

---

## 3. Helm Chart Modifications

The existing Helm chart (`my-python-app`) was extended to support both Canary and Blue‑Green strategies.

### 3.1 Chart Structure (relevant files)

```
my-python-app/
├── Chart.yaml                 # version updated to 0.2.0
├── values.yaml                # added strategy, canary steps, blueGreen settings
├── templates/
│   ├── rollout.yaml           # replaces deployment.yaml (conditional canary/bluegreen)
│   ├── service.yaml           # unchanged
│   ├── preview-service.yaml   # new – only for blue‑green
│   ├── analysis-template.yaml # optional – for automated analysis
│   ├── _helpers.tpl           # unchanged
│   └── NOTES.txt
```

### 3.2 Key Values

```yaml
# values.yaml (excerpt)
strategy: "canary"            # or "bluegreen"

canary:
  steps:
    - setWeight: 20
    - pause: {}               # manual promotion
    - setWeight: 40
    - pause: { duration: 30s }
    - setWeight: 60
    - pause: { duration: 30s }
    - setWeight: 80
    - pause: { duration: 30s }
    - setWeight: 100

blueGreen:
  autoPromotionEnabled: false
  # autoPromotionSeconds: 30   # optional

analysis:
  enabled: false               # set true for bonus
  templateName: webcheck
  successCondition: "healthy"
  interval: 10s
  count: 3
  failureLimit: 1
```

---

## 4. Canary Deployment

### 4.1 Strategy Definition

The Canary strategy shifts traffic gradually:

| Step | Weight | Action                     |
|------|--------|----------------------------|
| 1    | 20%    | Manual promotion required  |
| 2    | 40%    | Auto‑pause 30 seconds      |
| 3    | 60%    | Auto‑pause 30 seconds      |
| 4    | 80%    | Auto‑pause 30 seconds      |
| 5    | 100%   | Full rollout               |

### 4.2 Deploy Canary

```bash
helm upgrade --install myapp ./my-python-app --set strategy=canary
```

### 4.3 Trigger an Update

```bash
helm upgrade myapp ./my-python-app --set image.tag=metrics2 --set strategy=canary
```

### 4.4 Monitor and Promote

```bash
# Watch rollout progress
kubectl argo rollouts get rollout myapp-my-python-app -w

# After the first step (20%), promote manually
kubectl argo rollouts promote myapp-my-python-app
```

The rollout will then proceed automatically through the remaining steps.

### 4.5 Abort / Rollback

```bash
# Abort during rollout (revert to stable version)
kubectl argo rollouts abort myapp-my-python-app

# Retry aborted rollout
kubectl argo rollouts retry myapp-my-python-app
```

---

## 5. Blue‑Green Deployment

### 5.1 Strategy Definition

- **Active Service**: `myapp-my-python-app` (serves production traffic)
- **Preview Service**: `myapp-my-python-app-preview` (exposes new version)

The new version is deployed without affecting production. It is accessible only via the preview service until manually promoted.

### 5.2 Deploy Blue‑Green

```bash
helm upgrade --install myapp ./my-python-app --set strategy=bluegreen
```

### 5.3 Trigger an Update

```bash
helm upgrade myapp ./my-python-app --set image.tag=metrics2 --set strategy=bluegreen
```

Argo Rollouts creates a new ReplicaSet (green) and makes it available behind the preview service.

### 5.4 Test Preview

```bash
kubectl port-forward svc/myapp-my-python-app-preview 8081:80
```

Open http://localhost:8081 – you should see the new version.

### 5.5 Promote to Active

```bash
kubectl argo rollouts promote myapp-my-python-app
```

The active service is instantly switched to the green version.

### 5.6 Instant Rollback

```bash
kubectl argo rollouts undo myapp-my-python-app
```

Rollback is immediate – the active service points back to the previous stable version.

---

## 6. Automated Analysis (Bonus)

With analysis, the rollout can automatically promote or roll back based on metrics (e.g., health endpoint, error rate).

### 6.1 Enable Analysis

Set in `values.yaml`:

```yaml
analysis:
  enabled: true
  templateName: webcheck
  successCondition: "healthy"
  interval: 10s
  count: 3
  failureLimit: 1
```

### 6.2 AnalysisTemplate

The chart creates an `AnalysisTemplate` that performs HTTP checks against the application's `/health` endpoint:

```yaml
apiVersion: argoproj.io/v1alpha1
kind: AnalysisTemplate
metadata:
  name: webcheck
spec:
  metrics:
    - name: web-check
      provider:
        web:
          url: http://myapp-my-python-app.default.svc/health
          jsonPath: "{$.status}"
      successCondition: result == "healthy"
      interval: 10s
      count: 3
      failureLimit: 1
```

### 6.3 Integration with Canary

If analysis is enabled, an analysis step is added after the 20% weight step. If any check fails, the rollout automatically rolls back.

---

## 7. Useful CLI Commands

| Command | Description |
|---------|-------------|
| `kubectl argo rollouts get rollout <name> -w` | Watch rollout progress |
| `kubectl argo rollouts promote <name>` | Promote to next step / promote green to active |
| `kubectl argo rollouts abort <name>` | Abort ongoing rollout |
| `kubectl argo rollouts retry <name>` | Retry aborted rollout |
| `kubectl argo rollouts undo <name>` | Rollback to previous stable version |
| `kubectl argo rollouts set image <name> <container>=<image>` | Update image imperatively |
| `kubectl argo rollouts get experiments` | List analysis experiments |

---

## 8. Testing Evidence

### 8.1 Canary Test

```bash
$ helm upgrade myapp ./my-python-app --set image.tag=metrics2
$ kubectl argo rollouts get rollout myapp-my-python-app
Name:            myapp-my-python-app
Namespace:       default
Status:          ✔ Healthy
Strategy:        Canary
  Step:          4/5 (setWeight: 80)
  SetWeight:     80
  ActualWeight:  80
...
```

Dashboard screenshot shows traffic pie chart with 80% new version, 20% old.

### 8.2 Blue‑Green Test

After update, preview service accessible on port 8081. After promotion:

```bash
$ kubectl argo rollouts promote myapp-my-python-app
rollout "myapp-my-python-app" promoted

$ kubectl get svc
NAME                         TYPE        CLUSTER-IP      PORT(S)        AGE
myapp-my-python-app          NodePort    10.96.xxx.xxx   80:30080/TCP   5m
myapp-my-python-app-preview  NodePort    10.96.yyy.yyy   80:30234/TCP   5m
```

Active service now points to green version.

### 8.3 Analysis Test

Intentionally break the new version’s health endpoint. The analysis fails and the rollout is automatically rolled back:

```bash
$ kubectl argo rollouts get rollout myapp-my-python-app
Status:          ✘ Degraded
Message:         Rollback completed
```

---

## 9. Strategy Comparison

| Aspect | Canary | Blue‑Green |
|--------|--------|------------|
| Traffic shift | Gradual (percentage‑based) | Instant (all‑or‑nothing) |
| Resource usage | 1x (during shift) | 2x (during deployment) |
| Rollback speed | Gradual (abort stops new traffic) | Instant (switch active service) |
| Risk exposure | Low (small initial %) | Higher (full new version exposed) |
| Good for | Baseline testing, A/B tests | Critical cuts, zero‑downtime |
| Service requirements | Single service | Two services (active + preview) |

**Recommendation:** Use Canary when you want to validate with real traffic gradually. Use Blue‑Green when you want an instant cut‑over and can afford 2x resources temporarily.

---

## 10. Troubleshooting

| Issue | Solution |
|-------|----------|
| Rollout stuck at `pause: {}` | Run `kubectl argo rollouts promote` |
| Analysis fails | Check AnalysisTemplate URL and ensure app responds correctly |
| Preview service not accessible | Verify service exists: `kubectl get svc | grep preview` |
| `unknown field "setWeight"` | Ensure Argo Rollouts controller is installed and Rollout CRD exists |
| Rollout and Deployment conflict | Remove `deployment.yaml` from Helm chart |