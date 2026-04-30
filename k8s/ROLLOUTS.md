# LAB14 — Progressive Delivery with Argo Rollouts

## 1. Task 1 — Argo Rollouts Fundamentals

### 1.1 Installation verification

Installed Argo Rollouts controller and dashboard to namespace `argo-rollouts`.

**Verification outputs:**
- Controller running: `kubectl get pods -n argo-rollouts`
- kubectl plugin installed: `kubectl argo rollouts version`
- Dashboard accessible: `kubectl port-forward svc/argo-rollouts-dashboard -n argo-rollouts 3100:3100`

![task1-controller](screenshots/lab14/task1-controller.png)
![task1-dashboard](screenshots/lab14/task1-dashboard.png)

### 1.2 Rollout vs Deployment comparison

| Feature | Deployment | Rollout |
|---------|-----------|---------|
| **Kind** | `apps/v1` | `argoproj.io/v1alpha1` |
| **Progressive Delivery** | ❌ RollingUpdate only | ✅ Canary, Blue-Green |
| **Traffic Management** | ❌ Not supported | ✅ Native support |
| **Automatic Rollback** | ❌ Manual | ✅ Metrics-based |
| **Pod Replacement** | Gradual (uncontrolled) | Controlled steps |
| **Use Case** | Standard updates | Safe, gradual releases |

**Key additions in Rollout:**
- `strategy` field with `canary` or `blueGreen` options
- Traffic weight control (`setWeight`)
- Pause points (manual or timed)
- Analysis templates for metrics

---

## 2. Task 2 — Canary Deployment

### 2.1 Canary strategy configuration

File: `k8s/devops-info-python/templates/rollout-canary.yaml`

Created Rollout with progressive traffic shifting:
```
20% → pause (manual) → 40% → pause 30s → 60% → pause 30s → 80% → pause 30s → 100%
```

Configuration:
- `canaryService`: Routes traffic to canary version
- `stableService`: Routes traffic to stable version
- Steps define traffic weight and pause duration
- `maxSurge: 25%` ensures gradual pod replacement

### 2.2 Canary service

File: `k8s/devops-info-python/templates/service-canary.yaml`

Service routes traffic to canary rollout pods, separate from stable production traffic.

### 2.3 Deployment and testing

1. **Enable canary rollout** in values.yaml:
   ```yaml
   rollout:
     canary:
       enabled: true
   ```

2. **Deploy:**
   ```bash
   helm upgrade --install lab14 ./k8s/devops-info-python -n default
   ```

3. **Observe rollout status:**
   - Dashboard: [http://localhost:3100](http://localhost:3100)
   - CLI: `kubectl argo rollouts get rollout devops-info-python -w`

4. **Trigger canary** by updating image tag:
   ```bash
   kubectl set image rollout/devops-info-python \
     devops-info-python=olesianov/devops-info-python:lab03 -n default
   ```

5. **Watch traffic shifting:**
   - First pause at 20%: manually promote with `kubectl argo rollouts promote devops-info-python`
   - Subsequent pauses: auto-proceed after 30 seconds
   - Dashboard shows percentage breakdown live

![task2-canary-progression](screenshots/lab14/task2-canary-progression.png)
![task2-canary-dashboard](screenshots/lab14/task2-canary-dashboard.png)

### 2.4 Rollback testing

**Abort during canary:**
```bash
kubectl argo rollouts abort rollout/devops-info-python
```

Observed:
- Traffic instantly returns to stable version (0% canary)
- All canary pods cleaned up
- Production unaffected during abort

![task2-rollback](screenshots/lab14/task2-rollback.png)

---

## 3. Task 3 — Blue-Green Deployment

### 3.1 Blue-Green strategy configuration

File: `k8s/devops-info-python/templates/rollout-bluegreen.yaml`

Blue-Green strategy:
- **Blue**: Current production version (activeService)
- **Green**: New version for testing (previewService)
- **Switch**: Instant traffic toggle from blue to green
- `autoPromotionEnabled: false`: Manual promotion required

### 3.2 Preview service

File: `k8s/devops-info-python/templates/service-preview.yaml`

Service routes to green (preview) version for testing before promotion.

### 3.3 Blue-Green deployment flow

1. **Enable blue-green rollout** in values.yaml:
   ```yaml
   rollout:
     blueGreen:
       enabled: true
   ```

2. **Deploy initial version (blue):**
   ```bash
   helm upgrade --install lab14-bg ./k8s/devops-info-python -n default
   ```

3. **Access production (blue):**
   ```bash
   kubectl port-forward svc/devops-info-python 8080:80
   # Visit http://localhost:8080
   ```

4. **Trigger green deployment** by updating image:
   ```bash
   kubectl set image rollout/devops-info-python-bg \
     devops-info-python=olesianov/devops-info-python:lab03 -n default
   ```

5. **Access preview (green):**
   ```bash
   kubectl port-forward svc/devops-info-python-preview 8081:80
   # Visit http://localhost:8081 to test new version
   ```

6. **Verify both versions:**
   - Blue running: Check production endpoint
   - Green ready: Check preview endpoint
   - No downtime between them

7. **Promote green to production:**
   ```bash
   kubectl argo rollouts promote rollout/devops-info-python-bg
   ```

   - Activeservice now routes to green
   - Old blue version kept for quick rollback
   - Instant switch (no gradual traffic shift)

![task3-bluegreen-setup](screenshots/lab14/task3-bluegreen-setup.png)
![task3-bluegreen-dashboard](screenshots/lab14/task3-bluegreen-dashboard.png)

### 3.4 Instant rollback capability

**Abort after promotion:**
```bash
kubectl argo rollouts abort rollout/devops-info-python-bg
```

Result:
- Active service reverts to blue instantly
- Zero downtime rollback
- Faster than canary abort (no traffic shifting needed)

![task3-rollback](screenshots/lab14/task3-rollback.png)

---

## 4. Task 4 — Strategy Comparison

### 4.1 Canary vs Blue-Green

| Aspect | Canary | Blue-Green |
|--------|--------|-----------|
| **Traffic Switch** | Gradual (%) | Instant (all-or-nothing) |
| **Duration** | Minutes to hours | Seconds |
| **Resource Usage** | Shared | 2x during deployment |
| **Rollback Time** | Fast (traffic shift back) | Instant |
| **Testing Depth** | Real users (small %) | Full environment |
| **Risk** | Lower (% exposure) | Higher (full switch) |
| **Detection** | Built-in metrics | Manual verification |
| **Infrastructure** | Less resources needed | More resources needed |

### 4.2 When to use each

**Use Canary when:**
- You want built-in metrics analysis
- Resources are limited
- Gradual validation with real users needed
- Risk must be minimized per step

**Use Blue-Green when:**
- You need instant rollback capability
- Full environment testing required
- Deployment speed is critical
- Resources available for 2x environments

### 4.3 Recommendation for different scenarios

**Internal API (low risk):**
→ Blue-Green for speed and instant rollback

**Customer-facing app (high risk):**
→ Canary with metrics-based promotion for gradual rollout

**Batch processing (non-critical):**
→ Blue-Green with scheduled rollover

**Real-time system (critical):**
→ Canary with health-check analysis and small percentages

---

## 5. CLI Commands Reference

### Installation

```bash
# Install Argo Rollouts
kubectl create namespace argo-rollouts
kubectl apply -n argo-rollouts -f \
  https://github.com/argoproj/argo-rollouts/releases/latest/download/install.yaml

# Install kubectl plugin (Linux/WSL)
curl -LO https://github.com/argoproj/argo-rollouts/releases/latest/download/kubectl-argo-rollouts-linux-amd64
chmod +x kubectl-argo-rollouts-linux-amd64
sudo mv kubectl-argo-rollouts-linux-amd64 /usr/local/bin/kubectl-argo-rollouts

# Verify installation
kubectl argo rollouts version
kubectl get pods -n argo-rollouts
```

### Dashboard

```bash
# Start dashboard port-forward
kubectl port-forward svc/argo-rollouts-dashboard -n argo-rollouts 3100:3100

# Access: http://localhost:3100
```

### Monitoring rollout

```bash
# Watch rollout status
kubectl argo rollouts get rollout <name> -w

# Get detailed status
kubectl argo rollouts get rollout <name>

# Watch in dashboard
kubectl argo rollouts dashboard

# List all rollouts
kubectl argo rollouts list rollouts

# Describe rollout
kubectl describe rollout <name>
```

### Promotion and rollback

```bash
# Promote to next step (canary)
kubectl argo rollouts promote <name>

# Abort current rollout
kubectl argo rollouts abort rollout/<name>

# Retry aborted rollout
kubectl argo rollouts retry rollout <name>

# Restart rollout from beginning
kubectl argo rollouts restart <name>
```

### Analysis

```bash
# Get analysis status
kubectl argo rollouts get experiment <name>

# List experiments
kubectl get experiments

# Describe analysis template
kubectl describe analysistemplate <name>
```

### Debugging

```bash
# View logs from rollout pods
kubectl logs -l app=devops-info-python

# Check event timeline
kubectl describe rollout <name> | grep -A 50 Events:

# Get current traffic split
kubectl get rollout <name> -o jsonpath='{.status.canary.weights}'
```

---

## 6. Bonus — Automated Analysis

### 6.1 AnalysisTemplate configuration

File: `k8s/devops-info-python/templates/analysistemplate.yaml`

Created simple health-check analysis template:

```yaml
apiVersion: argoproj.io/v1alpha1
kind: AnalysisTemplate
metadata:
  name: devops-info-python-success-rate
spec:
  metrics:
    - name: webcheck
      provider:
        web:
          url: "http://devops-info-python.default.svc/health"
          jsonPath: "{$.status}"
      successCondition: result == "ok"
      failureCondition: result == "error"
      interval: 10s
      count: 3
      failureLimit: 1
```

### 6.2 Integration with canary

**Usage in rollout-canary.yaml:**

```yaml
strategy:
  canary:
    steps:
      - setWeight: 20
      - pause: {}
      - setWeight: 40
      - analysis:
          templates:
            - templateName: devops-info-python-success-rate
      - setWeight: 60
      # ... more steps
```

**Flow:**
1. Set 40% traffic to canary
2. Run analysis (check `/health` endpoint)
3. If all checks pass: continue
4. If checks fail: auto-rollback

### 6.3 Metrics-based promotion

**Automatic promotion on success:**
- Analysis runs 3 times at 10s intervals
- If all 3 succeed → proceed to next step
- If any fails → abort and rollback

**Manual verification:**
```bash
# Check analysis status
kubectl get analysis

# View analysis results
kubectl describe analysis <name>

# Check metrics
kubectl logs <analysis-pod>
```

### 6.4 Testing auto-rollback

1. **Deploy with intentional failure:**
   - Stop `/health` endpoint on canary version
   - Start rollout

2. **Observe:**
   - Analysis runs and detects failures
   - After failureLimit (1), analysis fails
   - Rollout aborts automatically
   - Traffic reverts to stable version

3. **Evidence:**
   ```bash
   kubectl argo rollouts get rollout devops-info-python -w
   # Status shows: "AnalysisFailed → Degraded → Aborting"
   ```

![bonus-analysis-template](screenshots/lab14/bonus-analysis-template.png)
![bonus-auto-rollback](screenshots/lab14/bonus-auto-rollback.png)

---

## 7. Helm chart values for lab14

### values-lab14-canary.yaml

```yaml
fullnameOverride: devops-info-python
replicaCount: 3

image:
  repository: olesianov/devops-info-python
  tag: lab03
  pullPolicy: IfNotPresent

rollout:
  canary:
    enabled: true
    pauseDuration: 30s
  blueGreen:
    enabled: false
  analysis:
    enabled: false
```

### values-lab14-bluegreen.yaml

```yaml
fullnameOverride: devops-info-python
replicaCount: 2

image:
  repository: olesianov/devops-info-python
  tag: lab03
  pullPolicy: IfNotPresent

rollout:
  canary:
    enabled: false
  blueGreen:
    enabled: true
    autoPromotionEnabled: false
    previewReplicaCount: 1
  analysis:
    enabled: false
```

### values-lab14-analysis.yaml

```yaml
fullnameOverride: devops-info-python
replicaCount: 3

image:
  repository: olesianov/devops-info-python
  tag: lab03
  pullPolicy: IfNotPresent

rollout:
  canary:
    enabled: true
    pauseDuration: 30s
  blueGreen:
    enabled: false
  analysis:
    enabled: true
    interval: 10s
    count: 3
    failureLimit: 1
```

---

## 8. Required outputs checklist

- [ ] Argo Rollouts controller running in argo-rollouts namespace
- [ ] Dashboard accessible on http://localhost:3100
- [ ] Canary rollout created and progressing through steps
- [ ] Traffic percentage visible in dashboard during canary
- [ ] Manual promotion tested (`kubectl argo rollouts promote`)
- [ ] Canary rollback tested (`kubectl argo rollouts abort`)
- [ ] Blue-green rollout deployed
- [ ] Preview service accessible and showing new version
- [ ] Active service showing current version
- [ ] Promotion from preview to active tested
- [ ] Blue-green instant rollback verified
- [ ] AnalysisTemplate created
- [ ] Analysis integrated with canary strategy
- [ ] Auto-rollback on analysis failure demonstrated

---

## 9. Key learnings

1. **Rollouts are Deployment replacements** for progressive delivery only - use Deployment for static workloads
2. **Canary is safer** for customer-facing apps - gradual exposure with automatic rollback
3. **Blue-Green is faster** for internal services - instant switch with quick rollback
4. **Analysis automation** removes manual promotion overhead and catches issues early
5. **Traffic splitting** requires network layer support (istio, linkerd, or Argo-native)
6. **Resources matter** - blue-green needs 2x capacity during deployment

---

## Resources

- [Argo Rollouts Documentation](https://argoproj.github.io/argo-rollouts/)
- [Canary Strategy Guide](https://argoproj.github.io/argo-rollouts/features/canary/)
- [Blue-Green Strategy Guide](https://argoproj.github.io/argo-rollouts/features/bluegreen/)
- [Analysis & Progressive Delivery](https://argoproj.github.io/argo-rollouts/features/analysis/)
