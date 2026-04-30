# LAB14 — Terminal Commands & Evidence Collection Guide

## Prerequisites — Install Argo Rollouts (Run in WSL/Bash)

### Step 1: Install Argo Rollouts Controller

```bash
# Create namespace
kubectl create namespace argo-rollouts

# Install controller
kubectl apply -n argo-rollouts -f \
  https://github.com/argoproj/argo-rollouts/releases/latest/download/install.yaml

# Wait for controller to be ready
kubectl wait --for=condition=available --timeout=300s \
  deployment/argo-rollouts -n argo-rollouts
```

**Expected output:**

- argo-rollouts pod running in argo-rollouts namespace

---

### Step 2: Install Argo Rollouts Dashboard (Run in WSL/Bash)

```bash
# Install dashboard
kubectl apply -n argo-rollouts -f \
  https://github.com/argoproj/argo-rollouts/releases/latest/download/dashboard-install.yaml

# Wait for dashboard to be ready
kubectl wait --for=condition=available --timeout=300s \
  deployment/argo-rollouts-dashboard -n argo-rollouts

# Verify installation
kubectl argo rollouts version
```

**Expected output:**

- kubectl argo rollouts version shows current version

---

### Step 3: Start Dashboard Port-Forward (Run in separate WSL terminal)

```bash
# In a NEW separate terminal, keep running:
kubectl port-forward svc/argo-rollouts-dashboard -n argo-rollouts 3100:3100

# Keep this terminal open for dashboard access
# Open browser: http://localhost:3100
```

**Keep this terminal running for the entire lab.**

---

## TASK 1 — Argo Rollouts Fundamentals — Evidence Collection

### Evidence 1a: Controller Installation Verification (Run in WSL/Bash)

```bash
# Check if controller pods are running
kubectl get pods -n argo-rollouts
```

**Screenshot requirement:** Capture output showing argo-rollouts-controller and argo-rollouts-dashboard pods running

---

### Evidence 1b: kubectl Plugin Verification (Run in WSL/Bash)

```bash
# Verify plugin is installed and working
kubectl argo rollouts version
```

**Screenshot requirement:** Show plugin version output

---

### Evidence 1c: Dashboard Access (Browser)

1. Open browser: http://localhost:3100
2. Dashboard should show empty state (no rollouts yet)

**Screenshot requirement:** Dashboard homepage showing "No rollouts found"

---

## TASK 2 — Canary Deployment — Evidence Collection

Use a dedicated namespace for this lab so Helm does not clash with older releases in `default`.

```bash
kubectl create namespace lab14
```

### Evidence 2a: Deploy Canary Rollout (Run in WSL/Bash)

```bash
# Navigate to project directory
cd /c/Users/nov-o/DevOps-course/DevOps-Core-Course

# Deploy with canary enabled
helm upgrade --install lab14-canary ./k8s/devops-info-python \
  -n lab14 \
  -f k8s/devops-info-python/values.yaml \
  --set rollout.canary.enabled=true \
  --set rollout.blueGreen.enabled=false

# Verify rollout created
kubectl get rollouts
kubectl argo rollouts get rollout devops-info-python
```

**Screenshot requirement:** Show rollout in stable state (fully deployed)

---

### Evidence 2b: Verify Canary Service Created (Run in WSL/Bash)

```bash
# Check services
kubectl get svc | grep devops-info-python
kubectl get svc devops-info-python-canary -o yaml
```

**Screenshot requirement:** Show canary service exists

---

### Evidence 2c: Trigger Canary Rollout (Run in WSL/Bash)

```bash
# Start watching rollout progress
kubectl argo rollouts get rollout devops-info-python -w

# In another terminal, trigger update by changing image tag
# Wait 5 seconds then run:
kubectl set image rollout/devops-info-python \
  devops-info-python=olesianov/devops-info-python:lab03 \
  -n lab14
```

**Expected:** Watch window shows traffic at 20% canary (paused)

**Screenshot requirement:** Show rollout status with "Canary: 20%" in dashboard or CLI

---

### Evidence 2d: Manual Promotion (Run in WSL/Bash)

```bash
# Promote to next step
kubectl argo rollouts promote devops-info-python

# Watch progression
kubectl argo rollouts get rollout devops-info-python -w
```

**Expected:** Traffic progresses: 20% → 40% (auto after 30s) → 60% (auto after 30s) → 80% (auto after 30s) → 100%

**Screenshot requirement:** Capture dashboard showing 40%, 60%, 80%, and 100% steps

---

### Evidence 2e: Dashboard Visualization (Browser)

1. Open http://localhost:3100
2. Select namespace: lab14
3. Select rollout: devops-info-python
4. Watch real-time traffic distribution

**Screenshot requirement:** Dashboard showing canary traffic percentage and pod distribution

---

### Evidence 2f: Canary Rollback Testing (Run in WSL/Bash)

```bash
# First, trigger another update
kubectl set image rollout/devops-info-python \
  devops-info-python=olesianov/devops-info-python:lab03 \
  -n lab14

# Wait for it to reach 20% pause
# Then abort
kubectl argo rollouts abort rollout/devops-info-python

# Check status
kubectl argo rollouts get rollout devops-info-python -w
```

**Expected:** Rollout status changes to "Degraded" then cleans up

**Screenshot requirement:** Show rollout after abort - traffic back to stable

---

## TASK 3 — Blue-Green Deployment — Evidence Collection

### Evidence 3a: Deploy Blue-Green Rollout (Run in WSL/Bash)

```bash
# Deploy with blue-green enabled
helm upgrade --install lab14-bg ./k8s/devops-info-python \
  -n lab14 \
  --set fullnameOverride=devops-info-python-bg \
  --set rollout.blueGreen.enabled=true \
  --set rollout.canary.enabled=false \
  --set rollout.blueGreen.autoPromotionEnabled=false

# Verify rollout created
kubectl get rollouts
kubectl argo rollouts get rollout devops-info-python-bg
```

**Screenshot requirement:** Show blue-green rollout in dashboard

---

### Evidence 3b: Verify Services Created (Run in WSL/Bash)

```bash
# Check active and preview services
kubectl get svc | grep devops-info-python
kubectl get svc devops-info-python-bg
kubectl get svc devops-info-python-bg-preview
```

**Screenshot requirement:** Show both services exist

---

### Evidence 3c: Access Active Service (Blue) (Run in WSL/Bash)

```bash
# In one terminal, port-forward to active service
kubectl port-forward svc/devops-info-python-bg 8080:80

# In browser: http://localhost:8080
# Record current version shown in response
```

**Screenshot requirement:** Browser showing active service response

---

### Evidence 3d: Access Preview Service (Green) (Run in NEW WSL/Bash terminal)

```bash
# Open NEW terminal for preview port-forward
kubectl port-forward svc/devops-info-python-bg-preview 8081:80

# Wait a moment then in browser: http://localhost:8081
# Should see same version initially
```

**Screenshot requirement:** Browser showing preview service (same as active initially)

---

### Evidence 3e: Trigger Green Deployment (Run in WSL/Bash)

```bash
# Trigger update to test new version deployment
kubectl set image rollout/devops-info-python-bg \
  devops-info-python=olesianov/devops-info-python:lab03 \
  -n lab14

# Wait for green deployment to complete
kubectl argo rollouts get rollout devops-info-python-bg -w
```

**Expected:** New ReplicaSet created for green version

**Screenshot requirement:** Show dashboard with Blue ready, Green ready (waiting promotion)

---

### Evidence 3f: Compare Blue and Green (Browser)

1. Active service (Blue) at http://localhost:8080
2. Preview service (Green) at http://localhost:8081
3. Both should show app is healthy

**Screenshot requirement:** Both endpoints accessible, versions match

---

### Evidence 3g: Promote Green to Active (Run in WSL/Bash)

```bash
# Promote green to become new active service
kubectl argo rollouts promote rollout/devops-info-python-bg

# Check status
kubectl argo rollouts get rollout devops-info-python-bg -w
```

**Expected:** Traffic instantly switches to green

**Screenshot requirement:** Dashboard showing promotion complete

---

### Evidence 3h: Verify Instant Switch (Browser)

1. Keep both ports forwarded
2. After promotion, refresh both endpoints
3. Both should show same (green) version

**Screenshot requirement:** Both endpoints now show promoted version

---

### Evidence 3i: Blue-Green Instant Rollback (Run in WSL/Bash)

```bash
# Test instant rollback capability
kubectl argo rollouts abort rollout/devops-info-python-bg

# Check status
kubectl argo rollouts get rollout devops-info-python-bg -w
```

**Expected:** Traffic instantly reverts to previous (blue) version

**Screenshot requirement:** Dashboard showing rollback status, both endpoints should match old version

---

## TASK 4 — Documentation

Documentation is provided in: `k8s/ROLLOUTS.md`

**Checklist:**

- [x] Argo Rollouts Setup documented
- [x] Canary Deployment documented with strategy details
- [x] Blue-Green Deployment documented with strategy details
- [x] Strategy Comparison table provided
- [x] CLI Commands Reference included
- [x] When-to-use guidance provided

---

## BONUS — Automated Analysis

### Bonus 1a: Create AnalysisTemplate (Run in WSL/Bash)

```bash
# Deploy with analysis enabled
helm upgrade --install lab14-analysis ./k8s/devops-info-python \
  -n lab14 \
  --set rollout.canary.enabled=true \
  --set rollout.analysis.enabled=true

# Verify analysis template created
kubectl get analysistemplate
kubectl describe analysistemplate devops-info-python-success-rate
```

**Screenshot requirement:** Show AnalysisTemplate created

---

### Bonus 1b: Check Analysis Running (Run in WSL/Bash)

```bash
# Trigger a rollout and watch analysis
kubectl set image rollout/devops-info-python \
  devops-info-python=olesianov/devops-info-python:lab03 \
  -n lab14

# In another terminal, watch analysis runs
kubectl get analysis -w
kubectl argo rollouts get rollout devops-info-python -w

# View analysis details
kubectl describe analysis <analysis-name>
```

**Expected:** Analysis runs during canary progression

**Screenshot requirement:** Show analysis template running during canary steps

---

### Bonus 1c: View Analysis Metrics (Browser)

In dashboard http://localhost:3100:

1. Select the rollout
2. Expand "Analysis" section
3. View metric checks and results

**Screenshot requirement:** Dashboard showing analysis metrics section

---

### Bonus 1d: Test Auto-Rollback (Optional - Advanced)

```bash
# This requires modifying the app to fail health checks
# Or disable the health endpoint temporarily to simulate failure

# For documentation purposes:
# Auto-rollback would happen if analysis template
# returns failure condition met

# Check analysis failure logs:
kubectl describe analysistemplate devops-info-python-success-rate
```

**Screenshot requirement:** (Optional) Show analysis failure in logs

---

## Summary Commands — Quick Reference

### View Everything (Run in WSL/Bash)

```bash
# Check all Argo Rollouts resources
echo "=== ROLLOUTS ===" && kubectl get rollouts
echo "=== SERVICES ===" && kubectl get svc | grep devops
echo "=== ANALYSIS ===" && kubectl get analysistemplate
echo "=== ANALYSIS RUNS ===" && kubectl get analysis

# Dashboard URL
echo "Dashboard: http://localhost:3100"

# Rollout status
kubectl argo rollouts get rollout devops-info-python
```

### Cleanup (Run in WSL/Bash)

```bash
# Remove lab deployments
helm uninstall lab14-canary
helm uninstall lab14-bg
helm uninstall lab14-analysis

# Keep Argo Rollouts installed for other labs
# kubectl delete namespace argo-rollouts  # Only if removing everything
```

---

## Screenshot Placement Guide

Create `k8s/screenshots/lab14/` directory and place:

- `task1-controller.png` — kubectl get pods -n argo-rollouts
- `task1-dashboard.png` — http://localhost:3100
- `task2-canary-progression.png` — Dashboard during canary steps
- `task2-canary-dashboard.png` — Dashboard showing traffic percentage
- `task2-rollback.png` — Rollout after abort
- `task3-bluegreen-setup.png` — Both active and preview services
- `task3-bluegreen-dashboard.png` — Dashboard after promotion
- `task3-rollback.png` — Dashboard after blue-green rollback
- `bonus-analysis-template.png` — AnalysisTemplate in dashboard
- `bonus-auto-rollback.png` — Analysis failure and auto-rollback

---

## Troubleshooting

### Rollout stuck at pause

```bash
# Check if waiting for promotion
kubectl argo rollouts get rollout devops-info-python

# Manually promote if paused
kubectl argo rollouts promote devops-info-python
```

### Analysis not running

```bash
# Verify analysis template exists
kubectl get analysistemplate

# Check if enabled in values
grep -A 5 "analysis:" k8s/devops-info-python/values.yaml

# Check analysis logs
kubectl logs <analysis-pod>
```

### Dashboard not accessible

```bash
# Verify port-forward is running
kubectl port-forward svc/argo-rollouts-dashboard -n argo-rollouts 3100:3100

# Kill old port-forward if needed
pkill -f "port-forward"
```

### Services not accessible

```bash
# Verify port-forwards are running in separate terminals
# Keep them running throughout the lab

# Test connectivity
kubectl port-forward svc/devops-info-python 8080:80
curl http://localhost:8080/health
```

---

## Important Notes

1. **Keep terminal windows open:**
   - Terminal 1: Dashboard port-forward
   - Terminal 2: Active service port-forward (blue-green testing)
   - Terminal 3: Preview service port-forward (blue-green testing)
   - Terminal 4: Working terminal for kubectl commands

2. **Run in WSL/Git Bash:** Use `/c/Users/...` path format for Windows paths in WSL

3. **Timing:** Allow 30-60 seconds for each pause during canary steps

4. **Screenshot timing:** Take screenshots at each step completion

5. **Documentation:** k8s/ROLLOUTS.md is already created with all required content
