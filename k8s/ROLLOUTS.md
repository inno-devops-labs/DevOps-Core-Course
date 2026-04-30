# Lab 14 — Progressive delivery with Argo Rollouts

This document describes how Argo Rollouts is set up for the `devops-info` Helm chart, how canary and blue-green strategies work, and how to operate them from the CLI and Argo CD.

**Evidence note:** CLI output in §1.4 was captured **2026-04-30** on minikube **`lab09`**, alongside the Argo CD evidence in `ARGOCD.md`.

## 1. Argo Rollouts setup

### 1.1 Install the controller

```bash
kubectl create namespace argo-rollouts
kubectl apply -n argo-rollouts -f https://github.com/argoproj/argo-rollouts/releases/latest/download/install.yaml
kubectl wait --for=condition=available deployment/argo-rollouts -n argo-rollouts --timeout=120s
kubectl get pods -n argo-rollouts
```

### 1.2 Install the kubectl plugin

- **macOS:** `brew install argoproj/tap/kubectl-argo-rollouts`
- **Verify:** `kubectl argo rollouts version`

### 1.3 Rollouts dashboard (optional UI)

```bash
kubectl apply -n argo-rollouts -f https://github.com/argoproj/argo-rollouts/releases/latest/download/dashboard-install.yaml
kubectl port-forward svc/argo-rollouts-dashboard -n argo-rollouts 3100:3100
```

Open [http://localhost:3100](http://localhost:3100) and select the namespace where the app is installed (for example `default`, `dev`, or `prod`).

### 1.4 Verification (captured)

```bash
kubectl get pods -n argo-rollouts
kubectl get rollout -A
```

```text
NAME                                      READY   STATUS    RESTARTS   AGE
argo-rollouts-5f64f8d68-xh5pt             1/1     Running   0          23m
argo-rollouts-dashboard-755bbc64c-r7dk5   1/1     Running   0          23m
```

```text
NAMESPACE   NAME               DESIRED   CURRENT   UP-TO-DATE   AVAILABLE   AGE
default     devops-info        3         3         3            3           12m
dev         devops-info-dev    1         1         1            1           15m
prod        devops-info-prod   3         3         3            3           13m
```

### 1.5 Rollout vs Deployment

| Aspect | `Deployment` | `Rollout` |
|--------|----------------|-----------|
| API | `apps/v1` | `argoproj.io/v1alpha1` |
| Progressive strategies | `RollingUpdate` / `Recreate` only | `canary`, `blueGreen`, plus analysis hooks |
| Traffic shift | Not built-in (needs mesh/ingress for %) | Canary steps (`setWeight`, `pause`, `analysis`); blue-green with active/preview Services |
| Rollback | `kubectl rollout undo` | `kubectl argo rollouts abort`, promote/retry, version history on the Rollout object |

The pod template (`spec.template`) stays the same as a normal Deployment; the difference is `spec.strategy` and optional analysis resources.

---

## 2. Helm chart wiring

- **Workload:** `k8s/devops-info/templates/rollout.yaml` — `Rollout` replacing the former `Deployment`.
- **Canary (default):** `rollout.strategy: canary` in `values.yaml` with weighted steps matching the lab (20% manual pause → 40/60/80 with 30s pauses → 100%).
- **Blue-green:** add `values-bluegreen.yaml` (sets `rollout.strategy: blueGreen`).
- **Preview Service:** `k8s/devops-info/templates/service-preview.yaml` renders only when `rollout.strategy` is `blueGreen` (`<fullname>-preview`).
- **Bonus analysis:** merge `values-canary-analysis.yaml` to enable `AnalysisTemplate` and an `analysis` step after the first `setWeight`; see §5.

### 2.1 Argo CD branch

Argo CD Applications under `k8s/argocd/` use `targetRevision: lab14` so Git remains the source of truth after you push this branch. Install or refresh as in `k8s/ARGOCD.md` (`kubectl apply -f k8s/argocd/…`, then Sync in the UI or `argocd app sync …`).

### 2.2 Local Helm (without Argo CD)

```bash
cd k8s/devops-info
helm upgrade --install devops-info . \
  --namespace default \
  --create-namespace \
  -f values.yaml
```

Blue-green example:

```bash
helm upgrade --install devops-info . -n default -f values.yaml -f values-bluegreen.yaml
```

---

## 3. Canary deployment

### 3.1 Strategy (as configured)

Without a service mesh or ingress traffic router, Argo Rollouts approximates percentage weights by scaling canary vs stable ReplicaSets relative to total replicas—adequate for the lab dashboard and CLI observation.

Configured steps (`values.yaml`):

1. `setWeight: 20` → `pause` with no duration (manual promote).
2. `setWeight: 40` → `pause: 30s`.
3. `setWeight: 60` → `pause: 30s`.
4. `setWeight: 80` → `pause: 30s`.
5. `setWeight: 100` (finish).

### 3.2 Run a rollout and promote

Trigger a change (image tag or env in values), sync from Git or upgrade Helm, then watch:

```bash
kubectl argo rollouts get rollout <releasefullname> -n <ns> --watch
# e.g. release name devops-info → often devops-info-dev in dev namespace
kubectl argo rollouts promote <rollout-name> -n <ns>
```

After the first 20% step, promotion is manual once; subsequent pauses are timed.

### 3.3 Abort (rollback behavior)

During an update:

```bash
kubectl argo rollouts abort <rollout-name> -n <ns>
```

Observe stable traffic returning to the previous ReplicaSet revision; then `kubectl argo rollouts get rollout …` shows aborted state (`retry rollout` when you want another attempt).

### 3.4 Dashboard checkpoints

For UI screenshots, capture the Rollouts dashboard at **pause** steps and **healthy** steady state (`kubectl port-forward svc/argo-rollouts-dashboard -n argo-rollouts 3100:3100`). Store PNGs under `k8s/assets/` and link them here. CLI corroboration: `kubectl argo rollouts get rollout <name> -n <ns>` or the cluster snapshot in `ROLLOUTS.md` §1.4 / `ARGOCD.md` §3.4.

---

## 4. Blue-green deployment

### 4.1 Strategy

With `values-bluegreen.yaml`, the Rollout uses:

- **activeService:** existing Service `{{ fullname }}` (production).
- **previewService:** `{{ fullname }}-preview` for the new stack before promotion.
- **autoPromotionEnabled:** `false` (promote explicitly after testing preview).

### 4.2 Test active vs preview

After changing the image (new “green” version):

```bash
kubectl port-forward svc/<fullname> 8080:80 -n <ns>        # active (stable after sync)
kubectl port-forward svc/<fullname>-preview 8081:80 -n <ns> # preview (candidate)
```

Compare responses, then:

```bash
kubectl argo rollouts promote <rollout-name> -n <ns>
```

Traffic on the active Service switches to the new ReplicaSet immediately (all-or-nothing vs gradual canary).

### 4.3 Instant rollback

After promotion, roll back fast with undo or abort depending on rollout phase:

```bash
kubectl argo rollouts undo <rollout-name> -n <ns>
```

Canary rolls back gradually; blue-green swaps all traffic between stable and preview sets in one step—typically faster perceptually for “instant” cutover labs.

---

## 5. Bonus: automated analysis (web health)

Merge `values-canary-analysis.yaml` (sets `rollout.analysis.enabled: true`). The chart renders `AnalysisTemplate` `{{ fullname }}-health` that polls `GET /health` and expects JSON `{"status":"healthy"}` (matches `app_python`).

To simulate failure: temporarily point the probe at a failing path or break the Service so the metric fails three times—the Rollout marks the analysis failed and triggers automatic rollback consistent with Rollouts analysis settings.

Prometheus-backed analysis can replace the web provider once monitoring from Lab 16 is available; see [Argo Rollouts analysis docs](https://argoproj.github.io/argo-rollouts/features/analysis/).

---

## 6. Strategy comparison

| | Canary | Blue-green |
|---|--------|------------|
| **Traffic shape** | Shifts by percentage over time | Full cutover active ↔ preview |
| **Resource use** | Lower extra capacity during rollout | Often 2× workload during overlap |
| **Risk** | Issues surface gradually | Bad release hits everyone after promote |
| **Best for** | Public APIs needing gradual exposure | Internal releases / release gates with human preview QA |

Recommendation: prefer **canary** for gradual exposure and softer failure domains; prefer **blue-green** when operators must certify the candidate on a duplicate Service before flipping production.

---

## 7. CLI reference

```bash
kubectl argo rollouts get rollout NAME -n NS
kubectl argo rollouts get rollout NAME -n NS --watch
kubectl argo rollouts promote NAME -n NS
kubectl argo rollouts abort NAME -n NS
kubectl argo rollouts retry rollout NAME -n NS
kubectl argo rollouts undo NAME -n NS
kubectl get rollout -A
```

Troubleshooting: `kubectl describe rollout NAME -n NS`, controller logs in `argo-rollouts` namespace, and Rollouts dashboard events for step progression.

![alt](/k8s/assets/Screenshot%202026-04-30%20at%2012.30.30.png)
![alt](/k8s/assets/Screenshot%202026-04-30%20at%2012.30.21.png)