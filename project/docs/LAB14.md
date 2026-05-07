# Lab 14 — Progressive Delivery with Argo Rollouts

This document covers the progressive-delivery extension of the `devops-info-service` Helm chart using **Argo Rollouts 1.7+**. The full operator runbook (install, demos, troubleshooting, screenshot anchors) lives in **[`k8s/ROLLOUTS.md`](../k8s/ROLLOUTS.md)**; this report summarises decisions and points to the evidence.

Course lab spec: [`labs/lab14.md`](../../labs/lab14.md) (repository root).

---

## Objectives

- Install the Argo Rollouts controller, kubectl plugin, and dashboard.
- Convert the Lab 13 `Deployment` into a `Rollout` while keeping the chart's existing Service, ConfigMaps, Secret, PVC, hooks, and probes intact.
- Implement a **canary** strategy with a manual gate followed by auto-progressing 30s pauses.
- Implement a **blue-green** strategy with an active + preview Service pair and instant rollback.
- (Bonus) Add an `AnalysisTemplate` (web provider against `/health`) and wire automated rollback on failure.

---

## Chart changes

```
k8s/devops-info-service/
├── values.yaml                          # +rollout.* block (default rollout.enabled: false)
├── values-rollout-canary.yaml           # canary overlay (4 replicas, persistence off)
├── values-rollout-bluegreen.yaml        # blueGreen overlay (2 replicas, persistence off)
└── templates/
    ├── deployment.yaml                  # wrapped in {{- if not .Values.rollout.enabled }}
    ├── rollout.yaml                     # NEW — argoproj.io/v1alpha1 Rollout
    ├── preview-service.yaml             # NEW — only renders for blueGreen
    └── analysistemplate.yaml            # NEW — only renders when bonus enabled
```

### Key design decisions

| Decision | Reason |
|----------|--------|
| Single `rollout.enabled` toggle in `values.yaml` instead of a separate chart | Keeps Lab 13 ArgoCD Applications working unchanged (they don't set `rollout.enabled`). One chart, three render shapes (Deployment / Canary / Blue-Green). |
| `templates/deployment.yaml` is **gated** rather than deleted | A render with default values still produces a Deployment, so the existing `argocd/application*.yaml` continue to deploy the chart byte-identically. |
| `templates/rollout.yaml` re-uses every `_helpers.tpl` include from the Deployment | Pod template is byte-for-byte identical (probes, securityContext, volumes, env). Argo Rollouts only needs a different `kind` + `strategy`. |
| Canary defaults to **4 replicas** in the overlay | The 20/40/60/80/100 weights map cleanly to whole pods; avoids `setWeight` rounding surprises. |
| Both overlays disable `persistence` | The chart's PVC is `ReadWriteOnce`; you can't run >1 replica against the same volume on a single-node cluster. |
| Bonus AnalysisTemplate uses **web provider, not Prometheus** | The cluster from Lab 13 has no Prometheus yet (Lab 16). The web provider hits `/health` directly through the in-cluster Service DNS — zero extra infrastructure. |

---

## Argo Rollouts Setup (Task 1)

```bash
kubectl create namespace argo-rollouts
kubectl apply -n argo-rollouts \
  -f https://github.com/argoproj/argo-rollouts/releases/latest/download/install.yaml

brew install argoproj/tap/kubectl-argo-rollouts
kubectl argo rollouts version

kubectl apply -n argo-rollouts \
  -f https://github.com/argoproj/argo-rollouts/releases/latest/download/dashboard-install.yaml
kubectl port-forward svc/argo-rollouts-dashboard -n argo-rollouts 3100:3100
```

| Evidence | Screenshot |
|----------|------------|
| Controller running, plugin version | `screenshots/argo-rollouts-version.png` |
| Dashboard reachable at `http://localhost:3100` | `screenshots/argo-rollouts-dashboard-empty.png` |

---

## Canary Strategy (Task 2)

```yaml
# values-rollout-canary.yaml — overlay over values.yaml
rollout:
  enabled: true
  strategy: canary
replicaCount: 4
persistence:
  enabled: false
```

The canary `steps` (defined in `values.yaml`) progress 20 % → manual pause → 40 / 60 / 80 (each followed by 30 s pause) → 100 %.

```bash
helm upgrade --install app k8s/devops-info-service \
  -f k8s/devops-info-service/values.yaml \
  -f k8s/devops-info-service/values-rollout-canary.yaml -n default

kubectl argo rollouts set image app-devops-info-service \
  devops-info-service=peplxx/devops-info-service:v0.1.7
kubectl argo rollouts get rollout app-devops-info-service -w
kubectl argo rollouts promote app-devops-info-service     # past the manual gate
kubectl argo rollouts abort   app-devops-info-service     # rollback test
```

See runbook §2 for full output and screenshots `argo-rollouts-canary-stepping.png`, `argo-rollouts-canary-cli-get.png`, `argo-rollouts-canary-promote.png`, `argo-rollouts-canary-abort.png`.

---

## Blue-Green Strategy (Task 3)

```yaml
# values-rollout-bluegreen.yaml — overlay over values.yaml
rollout:
  enabled: true
  strategy: blueGreen
  blueGreen:
    autoPromotionEnabled: false
    scaleDownDelaySeconds: 30
replicaCount: 2
persistence:
  enabled: false
```

Two services render: `app-devops-info-service` (active, production) and `app-devops-info-service-preview` (ClusterIP, green pods only).

```bash
helm upgrade --install app k8s/devops-info-service \
  -f k8s/devops-info-service/values.yaml \
  -f k8s/devops-info-service/values-rollout-bluegreen.yaml -n default

kubectl argo rollouts set image app-devops-info-service \
  devops-info-service=peplxx/devops-info-service:v0.1.7

# Verify green via the preview service before promoting
kubectl port-forward svc/app-devops-info-service-preview 8081:80
kubectl argo rollouts promote app-devops-info-service     # instant traffic flip
kubectl argo rollouts undo    app-devops-info-service     # instant rollback (within scaleDownDelaySeconds)
```

See runbook §3, screenshots `argo-rollouts-bluegreen-preview.png`, `argo-rollouts-bluegreen-promote.png`.

---

## Strategy Comparison

| Aspect | Canary | Blue-Green |
|--------|--------|------------|
| Traffic shift | Gradual (weighted) | Instant on promote |
| Resource cost during rollout | ~1 + (max weight / 100) replicas | 2× replicas |
| Rollback | Abort at any step (seconds) | Flip back to previous active (instant, while scaleDownDelaySeconds is open) |
| Mixed-version traffic? | Yes (by design) | No (clients hit one version) |
| Preview environment | None | `previewService` (green only) |
| Best for this service | `dev` — exercises real traffic, cheap | `prod` — schema/contract changes, audit trail |

---

## Bonus — Automated Analysis (2.5 pts)

`templates/analysistemplate.yaml` renders when `rollout.analysis.enabled: true`. The canary's `steps` array gets an `analysis:` step injected immediately after `setWeight: 20` (configurable via `rollout.canary.analysis.atStep`).

**AnalysisTemplate (web provider against `/health`):**

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
          url: http://app-devops-info-service.default.svc:80/health
          jsonPath: "{$.status}"
      successCondition: result == "healthy"
      interval: 10s
      count: 3
      failureLimit: 1
```

Happy path: `setWeight 20 → AnalysisRun (3 × "healthy") → Successful → manual pause → 40/60/80/100 → Healthy`. Forced-failure path (point the URL at a 404): `setWeight 20 → AnalysisRun → Failed → rollout AutoAborted → traffic returns to stable, status Degraded`.

```bash
helm upgrade --install app k8s/devops-info-service \
  -f k8s/devops-info-service/values.yaml \
  -f k8s/devops-info-service/values-rollout-canary.yaml \
  --set rollout.analysis.enabled=true,rollout.canary.analysis.enabled=true \
  -n default
```

See runbook §6 for the full demo (passing + forced-failure rollback) and screenshots `argo-rollouts-analysis-passing.png`, `argo-rollouts-analysis-rollback.png`.

---

## Task mapping

| Lab task | Points | Manifests / commands |
|----------|--------|----------------------|
| Argo Rollouts fundamentals | 2 pts | controller install, plugin install, dashboard install — runbook §1 |
| Canary deployment | 3 pts | `templates/rollout.yaml`, `values-rollout-canary.yaml`, `kubectl argo rollouts promote`/`abort` — runbook §2 |
| Blue-green deployment | 3 pts | `templates/preview-service.yaml`, `values-rollout-bluegreen.yaml` — runbook §3 |
| Documentation | 2 pts | this report + [`k8s/ROLLOUTS.md`](../k8s/ROLLOUTS.md) |
| Bonus — automated analysis | 2.5 pts | `templates/analysistemplate.yaml`, canary step splice — runbook §6 |

---

## Local verification (no cluster)

```bash
cd project/k8s/devops-info-service

helm lint .
helm lint . -f values-rollout-canary.yaml
helm lint . -f values-rollout-bluegreen.yaml

helm template app . | grep -E '^kind:'                                # → Deployment (no Rollout)
helm template app . -f values-rollout-canary.yaml   | grep -E '^kind:' # → Rollout (no Deployment)
helm template app . -f values-rollout-bluegreen.yaml | grep -E '^kind:' # → Rollout + preview Service

helm template app . -f values-rollout-canary.yaml \
  --set rollout.analysis.enabled=true,rollout.canary.analysis.enabled=true \
  | grep -E '^kind: AnalysisTemplate'                                   # → bonus rendered
```

All four assertions pass on `feat/lab14`.

---

## Further reading

- Operator runbook: [`k8s/ROLLOUTS.md`](../k8s/ROLLOUTS.md)
- Lab 13 (GitOps base): [`docs/LAB13.md`](LAB13.md)
- Helm chart: [`k8s/devops-info-service/`](../k8s/devops-info-service/)
- Lecture notes: [`lectures/lec14.md`](../../lectures/lec14.md)
- [Argo Rollouts documentation](https://argoproj.github.io/argo-rollouts/)
- [Canary strategy](https://argoproj.github.io/argo-rollouts/features/canary/)
- [Blue-green strategy](https://argoproj.github.io/argo-rollouts/features/bluegreen/)
- [Analysis & progressive delivery](https://argoproj.github.io/argo-rollouts/features/analysis/)
