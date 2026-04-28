# Argo Rollouts Implementation

## Argo Rollouts Setup

### Installation Verification

Argo Rollouts controller and dashboard have been installed in the `argo-rollouts` namespace:

```bash
kubectl get pods -n argo-rollouts
```

Output:
```
NAME                                       READY   STATUS    RESTARTS   AGE
argo-rollouts-79b89d8856-dftnn             1/1     Running   0          16m
argo-rollouts-dashboard-7b7bf46775-kpvkn   1/1     Running   0          16m
```

### kubectl Plugin Installation

The kubectl plugin has been installed and verified:

```bash
kubectl argo rollouts version
```

Output:
```
kubectl-argo-rollouts: v1.9.0+838d4e7
```

### Dashboard Access

The Argo Rollouts dashboard is accessible via port-forward:

```bash
kubectl port-forward svc/argo-rollouts-dashboard -n argo-rollouts 3100:3100
```

Access at: http://localhost:3100

## Canary Deployment

### Strategy Configuration

The canary deployment strategy has been implemented with the following configuration:

- **Rollout File**: `templates/rollout.yaml`
- **Analysis Rollout**: `devops-info-analysis` using `templates/rollout-with-analysis.yaml`
- **Traffic Steps**:
  - 20% traffic → analysis step (manual promotion required)
  - 40% traffic → pause 30s
  - 60% traffic → pause 30s
  - 80% traffic → pause 30s
  - 100% traffic

### Step-by-Step Rollout Progression

1. **Initial Deployment**: Deploy the rollout with canary strategy
2. **20% Traffic**: Rollout pauses after 20% traffic shift to run analysis; manual promotion is required to continue.
3. **Manual Promotion**: Use `kubectl argo rollouts promote <rollout-name>` to proceed from the manual pause.
4. **Progression and Pauses**: Rollout advances to 40%, 60%, and 80% with short pauses (30s) at each step for verification.
5. **Full Traffic**: Final step moves to 100% traffic for the new version.

### Promotion and Abort Demonstration

**Promote to next step:**
```bash
kubectl argo rollouts promote devops-info-analysis -n devops-lab13
```

**Abort rollout:**
```bash
kubectl argo rollouts abort devops-info-analysis -n devops-lab13
```

**Watch rollout status:**
```bash
kubectl argo rollouts get rollout devops-info-analysis -n devops-lab13 -w
```

## Blue-Green Deployment

### Strategy Configuration

The blue-green deployment strategy has been implemented with:

- **Rollout File**: `templates/rollout-bluegreen.yaml`
- **Values File**: `values-bluegreen.yaml`
- **Services**:
  - Active service: `devops-info` (production traffic)
  - Preview service: `devops-info-preview` (new version testing)

### Preview vs Active Service

- **Active Service**: Serves production traffic, points to stable version
- **Preview Service**: Serves new version for testing before promotion
- **Auto Promotion**: Disabled (manual promotion required)

### Promotion Process

1. **Deploy New Version**: Update image tag, rollout creates preview environment
2. **Test Preview**: Access preview service to test new version
3. **Promote**: Switch preview to active service instantly
4. **Rollback**: Switch back to previous version instantly

**Access services:**
```bash
# Active (production)
kubectl port-forward svc/devops-info-lab13 8080:80

# Preview (new version)
kubectl port-forward svc/devops-info-lab13-preview 8081:80
```

## Strategy Comparison

### When to Use Canary vs Blue-Green

| Strategy | Use Case | Pros | Cons |
|----------|----------|------|------|
| **Canary** | Gradual rollout, A/B testing, feature flags | Gradual traffic shift, reduced risk, metrics collection | Slower rollout, mixed traffic, resource efficient |
| **Blue-Green** | Major releases, breaking changes, instant rollback needed | Instant switch, zero downtime, easy rollback | 2x resources, all-or-nothing, no gradual testing |

### Recommendations

- **Use Canary** for:
  - API changes with backward compatibility
  - Performance testing with real traffic
  - Gradual feature rollout
  - When you want to collect metrics during rollout

- **Use Blue-Green** for:
  - Database schema changes
  - Breaking API changes
  - Major version upgrades
  - When instant rollback is critical

## CLI Commands Reference

### Rollout Management
```bash
# Get rollout status
kubectl argo rollouts get rollout <name>

# Watch rollout status
kubectl argo rollouts get rollout <name> -w

# Promote to next step
kubectl argo rollouts promote <name>

# Abort rollout
kubectl argo rollouts abort <name>

# Retry aborted rollout
kubectl argo rollouts retry rollout <name>
```

### Dashboard Access
```bash
# Port forward dashboard
kubectl port-forward svc/argo-rollouts-dashboard -n argo-rollouts 3100:3100
```

### Troubleshooting
```bash
# Get rollout details
kubectl argo rollouts get rollout <name> --details

# Get rollout revisions
kubectl argo rollouts get rollout <name> --revisions

# Get rollout analysis runs
kubectl argo rollouts get analysisrun
```

## Automated Analysis (Bonus)

### AnalysisTemplate Configuration

Created `templates/analysis-template.yaml` with web health check and namespace-aware service DNS:

```yaml
apiVersion: argoproj.io/v1alpha1
kind: AnalysisTemplate
metadata:
  name: success-rate
spec:
  metrics:
    - name: webcheck
      provider:
        web:
          url: http://{{ include "devops-info.fullname" . }}.{{ .Release.Namespace }}.svc/health
          jsonPath: "{$.status}"
      successCondition: result == "healthy"
      interval: 10s
      count: 3
      failureLimit: 1
```

### Integration with Canary Strategy

Modified canary steps in `templates/rollout-with-analysis.yaml`:

```yaml
strategy:
  canary:
    steps:
      - setWeight: 20
      - analysis:
          templates:
            - templateName: success-rate
      - setWeight: 50
      - pause: { duration: 30s }
      - setWeight: 100
```

### Auto-Rollback Demonstration

1. **Deploy with Analysis**: Rollout pauses at 20% for analysis
2. **Health Check**: Analysis runs web checks every 10 seconds for 3 times
3. **Success Condition**: Analysis expects the health endpoint to return JSON like `{"status": "healthy"}` (matches `successCondition: result == "healthy"` in the template)
4. **Failure Condition**: If the analysis fails its checks (per `failureLimit`), the rollout will automatically abort/rollback
5. **Manual Retry**: Use `kubectl argo rollouts retry rollout <name>` to retry

## Screenshots Required

1. **Argo Rollouts Dashboard** — main rollout list view
   - file: `k8s/screenshots/rollouts.png`
2. **Blue-Green Rollout Details** — rollout details for `devops-info-lab13`
   - file: `k8s/screenshots/bluegreen.png`
3. **Canary Progress / Promotion** — canary rollout with weight steps visible
   - file: `k8s/screenshots/canary.png`
4. **Abort / Rollback** — rollout abort state and traffic rollback
   - file: `k8s/screenshots/abort.png`
5. **Analysis Run** — analysis run status and result details
   - file: `k8s/screenshots/analysis.png`

## Files Created/Modified

- `templates/rollout.yaml` - Canary rollout configuration
- `templates/rollout-bluegreen.yaml` - Blue-green rollout configuration
- `templates/rollout-with-analysis.yaml` - Canary with automated analysis
- `templates/preview-service.yaml` - Preview service for blue-green
- `templates/analysis-template.yaml` - Health check analysis template
- `values-bluegreen.yaml` - Values file for blue-green deployment