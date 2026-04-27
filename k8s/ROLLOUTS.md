# Lab 14 — Progressive Delivery with Argo Rollouts


## Task 1 — Argo Rollouts fundamentals

### 1.1 Install controller + kubectl plugin

```bash
kubectl create namespace argo-rollouts
kubectl apply -n argo-rollouts -f https://github.com/argoproj/argo-rollouts/releases/latest/download/install.yaml

# macOS plugin
brew install argoproj/tap/kubectl-argo-rollouts

# verify
kubectl argo rollouts version
kubectl get pods -n argo-rollouts
```

**My run (evidence):**

```bash
kubectl config current-context
# minikube

kubectl cluster-info
# Kubernetes control plane is running at https://127.0.0.1:54074

kubectl create namespace argo-rollouts
# namespace/argo-rollouts created

kubectl apply -n argo-rollouts -f https://github.com/argoproj/argo-rollouts/releases/latest/download/install.yaml
# (CRDs + controller resources created)

kubectl apply -n argo-rollouts -f https://github.com/argoproj/argo-rollouts/releases/latest/download/dashboard-install.yaml
# (dashboard resources created)

brew install argoproj/tap/kubectl-argo-rollouts

kubectl argo rollouts version
# kubectl-argo-rollouts: v1.8.3

kubectl get pods -n argo-rollouts
# argo-rollouts-...            Running
# argo-rollouts-dashboard-...   Running
```

### 1.2 Install dashboard + access

```bash
kubectl apply -n argo-rollouts -f https://github.com/argoproj/argo-rollouts/releases/latest/download/dashboard-install.yaml
kubectl port-forward svc/argo-rollouts-dashboard -n argo-rollouts 3100:3100
# open http://localhost:3100
```

**My run (evidence):**

```bash
kubectl port-forward svc/argo-rollouts-dashboard -n argo-rollouts 3100:3100
# Forwarding from 127.0.0.1:3100 -> 3100
```


### 1.3 Rollout vs Deployment (key differences)

- **API/Kind**: `apps/v1 Deployment` → `argoproj.io/v1alpha1 Rollout`
- **Progressive strategies**: Rollout supports `strategy.canary` and `strategy.blueGreen`
- **Controls**: promotion, abort, retry, rollback via `kubectl argo rollouts ...`
- **Traffic shifting**: canary weight-based steps (replica-based without ingress; traffic routing optional)

---

## Task 2 — Canary deployment (dev)

### 2.1 Helm chart changes

- Added `templates/rollout.yaml` (kind `Rollout`)
- Guarded `templates/deployment.yaml` to render only when rollouts disabled
- Canary strategy is enabled in `values-dev.yaml`:
  - 20% → pause (manual promote)
  - 40% → pause 30s
  - 60% → pause 30s
  - 80% → pause 30s
  - 100%

### 2.2 Observe rollout progression

Watch:

```bash
kubectl argo rollouts get rollout devops-info-service -n dev -w
```

Trigger a new rollout (example):

```bash
# Example: change image tag or add env var in values-dev.yaml, then push via ArgoCD
# After sync, rollout starts and stops at 20% pause
```
**My run (evidence: dashboard progression):**
- `k8s/rollouts/screenshots/canary-dev-stepss.png` (steps list)
- `k8s/rollouts/screenshots/canary-dev-20-paused.png` (20% + Paused)
- `k8s/rollouts/screenshots/canary-dev-40.png` (40%)
- `k8s/rollouts/screenshots/canary-dev-60.png` (60%)
- `k8s/rollouts/screenshots/canary-dev-100.png` (100%)

Promote first step manually:

```bash
kubectl argo rollouts promote devops-info-service -n dev
```

**My run (evidence):**

```bash
kubectl argo rollouts promote devops-info-service -n dev
# rollout 'devops-info-service' promoted
```

### 2.3 Abort / rollback test

During a rollout:

```bash
kubectl argo rollouts abort devops-info-service -n dev
kubectl argo rollouts get rollout devops-info-service -n dev
```

**My run (evidence):**

```bash
kubectl argo rollouts abort devops-info-service -n dev
# rollout 'devops-info-service' aborted

kubectl argo rollouts get rollout devops-info-service -n dev
# Status: ✔ Healthy
# Strategy: Canary
```

---

## Task 3 — Blue-green deployment (prod)

### 3.1 Helm chart changes

- Blue-green enabled in `values-prod.yaml`
- Preview service is created by `templates/service-preview.yaml`
- Rollout uses:
  - `activeService: devops-info-service`
  - `previewService: devops-info-service-preview`
  - `autoPromotionEnabled: false` (manual promotion)

### 3.2 Test preview vs active and promote

```bash
# Active service
kubectl port-forward -n prod svc/devops-info-service 8080:80

# Preview service
kubectl port-forward -n prod svc/devops-info-service-preview 8081:80
```

**Task 3.3 — Access preview service to test new version (evidence to capture):**

- Run both port-forwards (two terminals or background one of them).
- Verify both endpoints respond (example using `/health`):

```bash
curl -sS localhost:8080/health
curl -sS localhost:8081/health
```

- Capture evidence (pick one):
  - screenshot with both port-forwards + the two `curl` results, or
  - paste terminal output of the two `curl` commands into this report.

**My run (evidence):**

```bash
curl -sS localhost:8080/health
# {"status":"healthy","timestamp":"2026-04-27T13:35:34.147849+00:00","uptime_seconds":37}

curl -sS localhost:8081/health
# {"status":"healthy","timestamp":"2026-04-27T13:35:34.163709+00:00","uptime_seconds":37}
```

Promote green to active:

```bash
kubectl argo rollouts promote devops-info-service -n prod
```

**My run (dashboard screenshots):**
- `k8s/rollouts/screenshots/bluegreen-prod-cutover-pending.png` (prod: rollout started, active service cutover pending)
- `k8s/rollouts/screenshots/bluegreen-prod-paused-promote.png` (prod: `BlueGreenPause` / waiting for manual promotion)
- `k8s/rollouts/screenshots/bluegreen-prod-promoted.png` (prod: after promote, new revision becomes `stable,active`)

**My run (evidence: current prod state):**

```bash
kubectl argo rollouts get rollout devops-info-service -n prod
# Status: ✔ Healthy
# Strategy: BlueGreen
# Images: ... (stable, active)
```

### 3.2a Failed preview + instant rollback (undo)

To demonstrate instant rollback, I intentionally used a non-existent image tag for the preview ReplicaSet.  
This caused `ErrImagePull/ImagePullBackOff` and the rollout became `Degraded`, while stable stayed serving traffic.

**My run (evidence):**

```bash
kubectl argo rollouts get rollout devops-info-service -n prod
# Status: ✖ Degraded
# Message: ProgressDeadlineExceeded ...
# preview pods: ErrImagePull / ImagePullBackOff

kubectl argo rollouts undo devops-info-service -n prod
# rollout 'devops-info-service' undo

kubectl argo rollouts get rollout devops-info-service -n prod
# Status: ✔ Healthy
# stable,active ReplicaSet stays Running
```

**Important (prod uses ArgoCD manual sync):**

When I change `values-prod.yaml` in Git, I apply it to `prod` with:

```bash
# ArgoCD server port-forward must be running:
kubectl port-forward svc/argocd-server -n argocd 8080:443

argocd login localhost:8080 --insecure
argocd app sync devops-info-service-prod
```

If sync fails with `another operation is already in progress`, wait and retry:

```bash
argocd app wait devops-info-service-prod --timeout 300
argocd app sync devops-info-service-prod
```

Sync (manual, because `prod` is not auto-sync):

```bash
argocd app sync devops-info-service-prod
```

If after sync you still see `OutOfSync` with a message like `resources require pruning`, run a manual sync with prune:

```bash
argocd app sync devops-info-service-prod --prune
```

### 3.3 Instant rollback

```bash
kubectl argo rollouts undo devops-info-service -n prod
```

**My run (dashboard screenshot):**
- `k8s/rollouts/screenshots/bluegreen-prod-after-undo.png` (prod: after undo / rollback)

### 3.4 Successful promotion (prod)

After restoring a valid image tag and syncing via ArgoCD, promotion succeeds:

```bash
argocd app sync devops-info-service-prod
# Sync Status: Synced to lab14 (...)
# Health Status: Healthy

kubectl argo rollouts promote devops-info-service -n prod
# rollout 'devops-info-service' promoted
```

## Task 4 — Documentation requirements checklist

- **Setup**: controller + dashboard installed, CLI plugin works
- **Canary**: steps, manual promote, abort demonstrated (screenshots from dashboard recommended)
- **Blue-green**: preview/active services, promotion, undo
- **Comparison**:
  - Canary: gradual, mixed traffic, slower but safer
  - Blue-green: instant switch, needs double capacity, easy rollback
- **Recommendation**:
  - Canary: use when you need gradual exposure / higher confidence
  - Blue-green: use when you want instant cutover and fast rollback
- **Commands reference**: see sections above
