# Lab 14 — Progressive Delivery with Argo Rollouts

![difficulty](https://img.shields.io/badge/difficulty-intermediate-yellow)
![topic](https://img.shields.io/badge/topic-Progressive%20Delivery-blue)
![points](https://img.shields.io/badge/points-10%2B2.5-orange)
![tech](https://img.shields.io/badge/tech-Argo%20Rollouts-informational)

> Implement canary and blue-green deployment strategies for safe, automated releases with traffic shifting and automatic rollback.

## Overview

Progressive delivery extends continuous delivery by gradually rolling out changes to a subset of users before full deployment. Argo Rollouts provides advanced deployment capabilities including canary releases, blue-green deployments, and automated rollbacks based on metrics.

**What You'll Learn:**
- Canary deployment strategy with traffic shifting
- Blue-green deployment with instant rollback
- Argo Rollouts Dashboard for visualization
- Metrics-based automated promotion/rollback
- Integration with existing Kubernetes services

**Building On:** Your Helm chart from Lab 13 (ArgoCD) with Deployment will be converted to Rollout.

**Tech Stack:** Argo Rollouts 1.7+ | Kubernetes | Prometheus (optional for analysis)

---

## Tasks

### Task 1 — Argo Rollouts Fundamentals (2 pts)

**Objective:** Install Argo Rollouts and understand the Rollout CRD.

**Requirements:**

1. **Install Argo Rollouts Controller**
   - Install via kubectl or Helm
   - Verify controller is running
   - Install kubectl plugin for CLI management

2. **Install Argo Rollouts Dashboard**
   - Deploy the dashboard for visualization
   - Access via port-forward
   - Explore the UI

3. **Understand Rollout vs Deployment**
   - Compare Rollout CRD with Deployment
   - Identify additional fields for progressive delivery
   - Document key differences

<details>
<summary>💡 Hints</summary>

**Installation:**
```bash
# Install controller
kubectl create namespace argo-rollouts
kubectl apply -n argo-rollouts -f https://github.com/argoproj/argo-rollouts/releases/latest/download/install.yaml

# Install kubectl plugin
# macOS
brew install argoproj/tap/kubectl-argo-rollouts

# Linux
curl -LO https://github.com/argoproj/argo-rollouts/releases/latest/download/kubectl-argo-rollouts-linux-amd64
chmod +x kubectl-argo-rollouts-linux-amd64
sudo mv kubectl-argo-rollouts-linux-amd64 /usr/local/bin/kubectl-argo-rollouts

# Verify
kubectl argo rollouts version
```

**Dashboard:**
```bash
# Install dashboard
kubectl apply -n argo-rollouts -f https://github.com/argoproj/argo-rollouts/releases/latest/download/dashboard-install.yaml

# Access
kubectl port-forward svc/argo-rollouts-dashboard -n argo-rollouts 3100:3100
# Open http://localhost:3100
```

**Rollout vs Deployment:**
- Rollout has `strategy` field with `canary` or `blueGreen` options
- Supports traffic management, analysis, and automated rollback
- Otherwise identical structure to Deployment

**Resources:**
- [Argo Rollouts Installation](https://argoproj.github.io/argo-rollouts/installation/)
- [Rollout Specification](https://argoproj.github.io/argo-rollouts/features/specification/)

</details>

---

### Task 2 — Canary Deployment (3 pts)

**Objective:** Implement canary deployment strategy with gradual traffic shifting.

**Requirements:**

1. **Convert Deployment to Rollout**
   - Create `templates/rollout.yaml` in your Helm chart
   - Change `kind: Deployment` to `kind: Rollout`
   - Add canary strategy configuration

2. **Configure Canary Steps**
   - Implement progressive traffic shifting:
     - 20% → pause (manual promotion)
     - 40% → pause 30 seconds
     - 60% → pause 30 seconds
     - 80% → pause 30 seconds
     - 100%

3. **Deploy and Test**
   - Install the Rollout
   - Make a change (e.g., update image tag or env var)
   - Watch traffic shifting in dashboard
   - Manually promote through first step
   - Observe automatic progression

4. **Test Rollback**
   - During a rollout, abort it
   - Observe traffic shifting back to stable version
   - Verify instant rollback capability

<details>
<summary>💡 Hints</summary>

**Rollout with Canary Strategy:**
```yaml
apiVersion: argoproj.io/v1alpha1
kind: Rollout
metadata:
  name: {{ include "mychart.fullname" . }}
spec:
  replicas: {{ .Values.replicaCount }}
  selector:
    matchLabels:
      {{- include "mychart.selectorLabels" . | nindent 6 }}
  template:
    # Same as Deployment pod template
    metadata:
      labels:
        {{- include "mychart.selectorLabels" . | nindent 8 }}
    spec:
      containers:
        - name: {{ .Chart.Name }}
          image: "{{ .Values.image.repository }}:{{ .Values.image.tag }}"
          # ... rest of container spec
  strategy:
    canary:
      steps:
        - setWeight: 20
        - pause: {}  # Manual promotion required
        - setWeight: 40
        - pause: { duration: 30s }
        - setWeight: 60
        - pause: { duration: 30s }
        - setWeight: 80
        - pause: { duration: 30s }
        - setWeight: 100
```

**CLI Commands:**
```bash
# Watch rollout status
kubectl argo rollouts get rollout <name> -w

# Promote to next step
kubectl argo rollouts promote <name>

# Abort rollout
kubectl argo rollouts abort <name>

# Retry aborted rollout
kubectl argo rollouts retry rollout <name>
```

**Important:** Your existing Service still works - it automatically routes to the correct pods based on Rollout's traffic management.

</details>

---

### Task 3 — Blue-Green Deployment (3 pts)

**Objective:** Implement blue-green deployment with preview environment.

**Requirements:**

1. **Create Blue-Green Rollout**
   - Create a separate values file or modify existing
   - Configure `blueGreen` strategy instead of `canary`
   - Set up active and preview services

2. **Configure Services**
   - Active service: serves production traffic
   - Preview service: serves new version for testing
   - Understand `autoPromotionEnabled` setting

3. **Test Blue-Green Flow**
   - Deploy initial version (blue)
   - Update image/config (triggers green deployment)
   - Access preview service to test new version
   - Promote green to active
   - Verify instant switch

4. **Test Instant Rollback**
   - After promotion, trigger rollback
   - Observe instant traffic switch back
   - Document the speed difference vs canary

<details>
<summary>💡 Hints</summary>

**Blue-Green Strategy:**
```yaml
spec:
  strategy:
    blueGreen:
      activeService: {{ include "mychart.fullname" . }}
      previewService: {{ include "mychart.fullname" . }}-preview
      autoPromotionEnabled: false  # Manual promotion
      # autoPromotionSeconds: 30  # Or auto-promote after 30s
```

**Preview Service:**
```yaml
apiVersion: v1
kind: Service
metadata:
  name: {{ include "mychart.fullname" . }}-preview
spec:
  selector:
    {{- include "mychart.selectorLabels" . | nindent 4 }}
  ports:
    - port: {{ .Values.service.port }}
      targetPort: {{ .Values.service.targetPort }}
```

**Testing:**
```bash
# Access active (production)
kubectl port-forward svc/myapp 8080:80

# Access preview (new version)
kubectl port-forward svc/myapp-preview 8081:80

# Compare both, then promote
kubectl argo rollouts promote myapp
```

**Blue-Green vs Canary:**
- Blue-Green: Instant switch, all-or-nothing
- Canary: Gradual traffic shift, percentage-based
- Blue-Green: Need 2x resources during deployment
- Canary: Shared resources, mixed traffic

</details>

---

### Task 4 — Documentation (2 pts)

**Objective:** Document your progressive delivery implementation.

**Create `k8s/ROLLOUTS.md` with:**

1. **Argo Rollouts Setup**
   - Installation verification
   - Dashboard access

2. **Canary Deployment**
   - Strategy configuration explained
   - Step-by-step rollout progression (screenshots from dashboard)
   - Promotion and abort demonstration

3. **Blue-Green Deployment**
   - Strategy configuration explained
   - Preview vs active service
   - Promotion process

4. **Strategy Comparison**
   - When to use canary vs blue-green
   - Pros and cons of each
   - Your recommendation for different scenarios

5. **CLI Commands Reference**
   - Useful commands you used
   - Monitoring and troubleshooting

---

## Bonus Task — Automated Analysis (2.5 pts)

**Objective:** Integrate metrics-based analysis for automated promotion/rollback.

**Requirements:**

1. **Create AnalysisTemplate**
   - Define success criteria based on metrics
   - Use Prometheus or web analysis provider
   - Set failure thresholds

2. **Integrate with Canary**
   - Add analysis step to canary strategy
   - Configure automatic rollback on failure
   - Test with intentional failure

3. **Document Analysis**
   - AnalysisTemplate configuration
   - How metrics determine success/failure
   - Demonstration of auto-rollback

<details>
<summary>💡 Hints</summary>

**Simple Web Analysis (no Prometheus):**
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
          url: http://{{ include "mychart.fullname" . }}.default.svc/health
          jsonPath: "{$.status}"
      successCondition: result == "ok"
      interval: 10s
      count: 3
      failureLimit: 1
```

**Canary with Analysis:**
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

**Prometheus Analysis (if Lab 16 monitoring is set up):**
```yaml
metrics:
  - name: error-rate
    provider:
      prometheus:
        address: http://prometheus.monitoring:9090
        query: |
          sum(rate(http_requests_total{status=~"5.*"}[1m])) /
          sum(rate(http_requests_total[1m]))
    successCondition: result[0] < 0.05
    interval: 30s
```

**Resources:**
- [Analysis & Progressive Delivery](https://argoproj.github.io/argo-rollouts/features/analysis/)
- [AnalysisTemplate Specification](https://argoproj.github.io/argo-rollouts/analysis/overview/)

</details>

---

## Checklist

### Task 1 — Argo Rollouts Fundamentals (2 pts)
- [ ] Controller installed and running
- [ ] kubectl plugin installed
- [ ] Dashboard accessible
- [ ] Rollout vs Deployment differences documented

### Task 2 — Canary Deployment (3 pts)
- [ ] Deployment converted to Rollout
- [ ] Canary steps configured
- [ ] Traffic shifting observed in dashboard
- [ ] Manual promotion tested
- [ ] Rollback tested

### Task 3 — Blue-Green Deployment (3 pts)
- [ ] Blue-green strategy configured
- [ ] Preview service created
- [ ] Preview environment tested
- [ ] Promotion to active tested
- [ ] Instant rollback verified

### Task 4 — Documentation (2 pts)
- [ ] `k8s/ROLLOUTS.md` complete
- [ ] Both strategies documented
- [ ] Screenshots included
- [ ] Comparison analysis provided

### Bonus — Automated Analysis (2.5 pts)
- [ ] AnalysisTemplate created
- [ ] Integrated with canary strategy
- [ ] Auto-rollback demonstrated
- [ ] Documentation complete

---

## Rubric

| Criteria | Points | Description |
|----------|--------|-------------|
| **Fundamentals** | 2 pts | Installation, dashboard, concepts |
| **Canary** | 3 pts | Working canary with traffic shifting |
| **Blue-Green** | 3 pts | Working blue-green with preview |
| **Documentation** | 2 pts | Complete ROLLOUTS.md |
| **Bonus** | 2.5 pts | Automated analysis integration |
| **Total** | 12.5 pts | 10 pts required + 2.5 pts bonus |

---

## Resources

<details>
<summary>📚 Official Documentation</summary>

- [Argo Rollouts Documentation](https://argoproj.github.io/argo-rollouts/)
- [Canary Strategy](https://argoproj.github.io/argo-rollouts/features/canary/)
- [Blue-Green Strategy](https://argoproj.github.io/argo-rollouts/features/bluegreen/)
- [Analysis & Progressive Delivery](https://argoproj.github.io/argo-rollouts/features/analysis/)

</details>

<details>
<summary>🎓 Tutorials</summary>

- [Getting Started Guide](https://argoproj.github.io/argo-rollouts/getting-started/)
- [Canary with Traffic Management](https://argoproj.github.io/argo-rollouts/getting-started/nginx/)

</details>

---

## Looking Ahead

- **Lab 15:** StatefulSets for stateful applications (different use case than Rollouts)
- **Lab 16:** Monitoring your rollouts with Prometheus/Grafana

---

**Good luck!** 🚀

> **Remember:** Rollouts replace Deployments when you need progressive delivery. For stateful applications (Lab 15), you'll still use StatefulSets - they serve different purposes.
