# Lab 14 — Progressive Delivery with Argo Rollouts

![difficulty](https://img.shields.io/badge/difficulty-intermediate-yellow)
![topic](https://img.shields.io/badge/topic-Progressive%20Delivery-blue)
![points](https://img.shields.io/badge/points-10%2B2-orange)
![tech](https://img.shields.io/badge/tech-Argo%20Rollouts%201.8-informational)

> Replace `kind: Deployment` with `kind: Rollout`. Ship a **canary** with step-based traffic shifting, a **blue-green** strategy with a preview service, and an **`AnalysisTemplate`** that lets Prometheus auto-abort a bad release — so "deployed" finally means "released".

## Overview

Through Lab 9 you ran rolling updates with a vanilla `Deployment`: pods swap 25% at a time and K8s stops measuring the moment a readiness probe flips green. The 5xx spike that only fires on 5% of requests still ships to 100% of users. **Progressive delivery** closes that loop — shape traffic in steps, gate each step behind metrics, and let the controller roll back without a human watching Grafana on a Friday.

In this lab you convert your Lab 13 Helm chart's `Deployment` into an **Argo Rollouts** `Rollout`, then exercise both major strategies and wire metric-driven analysis.

**What You'll Learn:**
- The Rollout CRD as a drop-in replacement for Deployment (same pod template, plus a `strategy:` block)
- Canary strategy: step-based weights, timed pauses, and manual promotion gates
- Blue-green strategy: `activeService` + `previewService`, instant cutover, instant rollback
- `AnalysisTemplate`: a Prometheus query + success condition that auto-aborts on regression
- The `kubectl argo rollouts` survival toolkit: `get --watch`, `promote`, `abort`, `retry`, `undo`

**Building On:** Your Helm chart from **Lab 13** (ArgoCD-managed) deploys `app-python` (your code, port 5000, `/health`) plus the course plumbing `echo` (`ghcr.io/inno-devops-labs/echo:v1`, port 8081, `/healthz`) and `health` (`ghcr.io/inno-devops-labs/health:v1`, port 8082, `/healthz` + `/metrics`). You will convert **`app-python`** to a Rollout. The `health` service's `/metrics` endpoint is a convenient target for the bonus AnalysisTemplate.

**Tech Stack:** Argo Rollouts **1.8.4** | Kubernetes **1.36 "Haru"** | Helm **4.1** | Prometheus **3.x** (3.11.3 or the 3.5 LTS line, the same Prometheus you stood up in Lab 8) | ArgoCD **3.4.x**

---

## Tasks

### Task 1 — Argo Rollouts Fundamentals (2 pts)

**Objective:** Install Argo Rollouts **1.8.4**, the kubectl plugin, and the dashboard. Understand how a `Rollout` differs from a `Deployment`.

**Requirements:**

1. **Install the controller (pinned to v1.8.4)**
   - Create the `argo-rollouts` namespace and apply the **v1.8.4** install manifest (not `latest`).
   - Verify the controller pod is `Running`.

2. **Install the `kubectl argo rollouts` plugin**
   - Install the v1.8.4 plugin binary and confirm `kubectl argo rollouts version` prints `v1.8.4`.

3. **Install the dashboard**
   - Apply the dashboard install manifest, port-forward, and open the UI.

4. **Document Rollout vs Deployment**
   - In your own words, list **three** fields/behaviours a `Rollout` adds over a `Deployment` (e.g. `strategy.canary`, `strategy.blueGreen`, `analysis`, traffic weights).
   - Note that the `template:`, `selector:`, and `replicas:` are otherwise identical.

<details>
<summary>💡 Hints</summary>

```bash
# Controller — pin v1.8.4 (do NOT use /latest/)
kubectl create namespace argo-rollouts
kubectl apply -n argo-rollouts \
  -f https://github.com/argoproj/argo-rollouts/releases/download/v1.8.4/install.yaml
kubectl -n argo-rollouts rollout status deploy/argo-rollouts

# kubectl plugin (Linux amd64) — pin v1.8.4
curl -fSL -o kubectl-argo-rollouts \
  https://github.com/argoproj/argo-rollouts/releases/download/v1.8.4/kubectl-argo-rollouts-linux-amd64
chmod +x kubectl-argo-rollouts
sudo mv kubectl-argo-rollouts /usr/local/bin/kubectl-argo-rollouts
kubectl argo rollouts version          # expect: v1.8.4

# macOS via Homebrew (tracks latest tap; verify it prints 1.8.x)
# brew install argoproj/tap/kubectl-argo-rollouts

# Dashboard
kubectl apply -n argo-rollouts \
  -f https://github.com/argoproj/argo-rollouts/releases/download/v1.8.4/dashboard-install.yaml
kubectl argo rollouts dashboard        # http://localhost:3100
```

Output examples in this lab are **illustrative** — your pod names, hashes, and timings will differ. Verify against your own cluster.

**Quality-of-life:** `alias kr='kubectl argo rollouts'`.

**Resources:**
- [Argo Rollouts Installation](https://argoproj.github.io/argo-rollouts/installation/)
- [Rollout Specification](https://argoproj.github.io/argo-rollouts/features/specification/)
- [Argo Rollouts releases (pin v1.8.4)](https://github.com/argoproj/argo-rollouts/releases)

</details>

---

### Task 2 — Canary Deployment (3 pts)

**Objective:** Convert `app-python`'s `Deployment` to a `Rollout` and ship a step-based canary.

**Requirements:**

1. **Convert Deployment → Rollout**
   - Create `templates/rollout.yaml` in your `app-python` chart (or rename `deployment.yaml`).
   - Change `apiVersion`/`kind` to the Rollout CRD; keep `selector`, `template`, `replicas` identical to your Deployment.
   - Your existing `Service` keeps working — it selects the same pod labels.

2. **Configure a 5-step canary**
   - Steps: **20 → 40 → 60 → 80 → 100**.
   - Insert a **manual gate** (`pause: {}`) immediately after the first step (20%).
   - Use timed `pause: {duration: 30s}` between the remaining steps.

3. **Trigger and drive a rollout**
   - Bump `image.tag` (or change an env var) to create a new revision.
   - Watch the rollout with `kubectl argo rollouts get rollout app-python --watch`.
   - `promote` past the manual gate, then observe the timed steps progress to 100%.

4. **Test abort**
   - Start another rollout, then `abort` it mid-flight.
   - Confirm traffic returns to the stable ReplicaSet and the rollout shows `Degraded`.
   - `retry` it and let it complete.

> Note: without a traffic router, Argo Rollouts approximates each `setWeight` by the **replica-count ratio** (e.g. 20% of 5 replicas ≈ 1 canary pod). That is expected and fine for this lab. Exact HTTP weights require a traffic router — see the bonus.

<details>
<summary>💡 Rollout skeleton (canary) — fill the YOUR-TASK markers</summary>

```yaml
apiVersion: argoproj.io/v1alpha1
kind: Rollout
metadata:
  name: {{ include "app-python.fullname" . }}
  labels:
    {{- include "app-python.labels" . | nindent 4 }}
spec:
  replicas: {{ .Values.replicaCount }}
  selector:
    matchLabels:
      {{- include "app-python.selectorLabels" . | nindent 6 }}
  template:
    # ⬇️ IDENTICAL to your Lab 13 Deployment pod template
    metadata:
      labels:
        {{- include "app-python.selectorLabels" . | nindent 8 }}
    spec:
      containers:
        - name: {{ .Chart.Name }}
          image: "{{ .Values.image.repository }}:{{ .Values.image.tag }}"
          ports:
            - containerPort: {{ .Values.service.targetPort }}   # 5000
          readinessProbe:
            httpGet:
              path: YOUR-TASK        # /health
              port: YOUR-TASK        # 5000
  strategy:
    canary:
      steps:
        - setWeight: 20
        - pause: {}                  # YOUR-TASK: manual gate — promote to continue
        - setWeight: 40
        - pause: { duration: YOUR-TASK }   # 30s
        - setWeight: 60
        - pause: { duration: YOUR-TASK }   # 30s
        - setWeight: 80
        - pause: { duration: YOUR-TASK }   # 30s
        - setWeight: 100
```
</details>

<details>
<summary>💡 Driving the rollout (commands runnable with Argo Rollouts 1.8 + K8s 1.36)</summary>

```bash
# Live, self-refreshing status (weight, pods, step, analysis)
kubectl argo rollouts get rollout app-python --watch

# Trigger a new revision (example: bump the tag your chart renders)
helm upgrade app-python ./charts/app-python --set image.tag=v2

# Move past a manual pause: {}
kubectl argo rollouts promote app-python

# Skip ALL remaining steps to 100% (use sparingly)
kubectl argo rollouts promote app-python --full

# Abort the in-progress rollout — traffic flips back to stable
kubectl argo rollouts abort app-python

# Retry a Degraded/aborted rollout from step 0
kubectl argo rollouts retry rollout app-python
```

The `Service` is unchanged — Argo Rollouts injects a `rollouts-pod-template-hash` label and shifts pods between stable and canary ReplicaSets behind your existing selector.

</details>

---

### Task 3 — Blue-Green Deployment (3 pts)

**Objective:** Add a blue-green strategy with an active service for production and a preview service for pre-promotion testing.

**Requirements:**

1. **Add a preview Service**
   - Create `templates/service-preview.yaml` — same selector intent as your active service, named `<fullname>-preview`.

2. **Configure the blue-green strategy**
   - Use `blueGreen` with `activeService` (your existing Service) and `previewService` (the new one).
   - Set `autoPromotionEnabled: false` (manual promotion) and `scaleDownDelaySeconds` so old pods survive a few minutes for instant rollback.
   - Keep this as a **second values file** (`values-bluegreen.yaml`) or a toggled block so you can demo both strategies from the same chart.

3. **Test the blue-green flow**
   - Deploy v1 (blue) and confirm the active service serves it.
   - Bump the image to v2 (green) — the controller spins up the new ReplicaSet behind the **preview** service.
   - Port-forward the **preview** service and validate v2 in isolation.
   - `promote` and confirm the active service flips to v2 instantly.

4. **Test instant rollback**
   - After promotion, run `kubectl argo rollouts undo app-python` **before** `scaleDownDelaySeconds` expires.
   - Confirm the active service flips back to v1 with no new pod scheduling.
   - Document the speed difference vs the canary abort in Task 2.

<details>
<summary>💡 Blue-green skeleton — fill the YOUR-TASK markers</summary>

```yaml
# in spec.strategy of your Rollout (values-bluegreen.yaml path)
strategy:
  blueGreen:
    activeService: {{ include "app-python.fullname" . }}
    previewService: {{ include "app-python.fullname" . }}-preview
    autoPromotionEnabled: false          # require manual promote
    scaleDownDelaySeconds: YOUR-TASK      # e.g. 300 — keep old pods 5 min for fast undo
    # prePromotionAnalysis:               # optional: gate promotion on smoke tests
    #   templates: [{ templateName: smoke-tests }]
```

```yaml
# templates/service-preview.yaml
apiVersion: v1
kind: Service
metadata:
  name: {{ include "app-python.fullname" . }}-preview
  labels:
    {{- include "app-python.labels" . | nindent 4 }}
spec:
  selector:
    {{- include "app-python.selectorLabels" . | nindent 4 }}
  ports:
    - port: {{ .Values.service.port }}
      targetPort: YOUR-TASK     # 5000
```
</details>

<details>
<summary>💡 Driving blue-green</summary>

```bash
helm upgrade app-python ./charts/app-python -f values-bluegreen.yaml --set image.tag=v1
# ... bump to v2 to trigger the green ReplicaSet:
helm upgrade app-python ./charts/app-python -f values-bluegreen.yaml --set image.tag=v2

# Validate v2 via the PREVIEW service (production still on v1)
kubectl port-forward svc/app-python-preview 8081:5000
curl -s localhost:8081/health

# Promote green → active (instant cutover)
kubectl argo rollouts promote app-python

# Instant rollback (before scaleDownDelaySeconds expires)
kubectl argo rollouts undo app-python
```

**Trade-off to note in your docs:** during cutover you run ~2x the pods (active + preview) — 2x cost for that window. Canary shares resources but mixes versions; blue-green isolates versions but doubles cost.

</details>

---

### Task 4 — Documentation (2 pts)

**Objective:** Document your progressive-delivery implementation in `k8s/ROLLOUTS.md`.

**Include:**

1. **Setup** — controller/plugin/dashboard install proof (`kubectl argo rollouts version` showing **v1.8.4**), dashboard screenshot.
2. **Canary** — your `strategy.canary` block explained, the 20→40→60→80→100 progression with the manual gate, plus a promote and an abort demonstrated with screenshots/CLI output.
3. **Blue-Green** — your `strategy.blueGreen` block, preview-vs-active explained, the promote and the instant `undo`.
4. **Strategy comparison** — when to use canary vs blue-green (reference the schema-migration case from the lecture), pros/cons, and your recommendation for `app-python`.
5. **CLI reference** — the `kubectl argo rollouts` commands you actually used and what each does.

---

## Bonus Task — Metric-Driven Auto-Abort (2 pts)

**Objective:** Add an `AnalysisTemplate` so a regressing release **auto-aborts** without human intervention, then prove it by shipping a deliberately broken image. For full marks, go beyond the minimum with a genuinely harder extension.

**Requirements:**

1. **Write an `AnalysisTemplate`**
   - Define a metric, a `successCondition`, an `interval`, a `count`, and a `failureLimit`.
   - Use a **Prometheus** provider against the Lab 8 Prometheus (e.g. a 5xx error-rate query against `app-python`'s `/metrics`, or the `health` plumbing's `/metrics`).
   - A `web` provider against `/health` is acceptable as a fallback, but Prometheus is the intended path.

2. **Wire it into the canary**
   - Add an `analysis` step after the first `setWeight`, **and** configure spec-level `backgroundAnalysis` so a mid-step regression aborts immediately (not just at the next gate).

3. **Demonstrate auto-rollback**
   - Deploy an image that returns 500s (or a query you can force to fail).
   - Capture the rollout going `Degraded` and traffic resetting to stable — **no manual abort**.

4. **Go further (required for the full 2 pts) — pick ONE:**
   - **(a) Multiple AnalysisTemplates:** combine two templates in one step (e.g. error-rate **and** p95 latency), so *either* failing aborts the rollout; document how the two interact.
   - **(b) Real HTTP traffic routing:** install the **NGINX Ingress** canary integration (or the **Gateway API** plugin), so `setWeight` programs exact HTTP weights instead of the replica-count approximation. Show the weighted Ingress/HTTPRoute the controller writes.

<details>
<summary>💡 AnalysisTemplate skeleton (Prometheus) — fill the YOUR-TASK markers</summary>

```yaml
apiVersion: argoproj.io/v1alpha1
kind: AnalysisTemplate
metadata:
  name: success-rate
spec:
  args:
    - name: service-name
  metrics:
    - name: success-rate
      interval: YOUR-TASK          # e.g. 30s — query cadence
      count: YOUR-TASK             # e.g. 5 — number of samples
      successCondition: YOUR-TASK  # e.g. result[0] >= 0.99
      failureLimit: YOUR-TASK      # e.g. 2 — failures tolerated before abort
      provider:
        prometheus:
          address: http://prometheus.monitoring:9090   # your Lab 8 Prometheus
          query: |
            sum(rate(http_requests_total{
              service="{{args.service-name}}", status!~"5.."
            }[2m]))
            /
            sum(rate(http_requests_total{
              service="{{args.service-name}}"
            }[2m]))
```
</details>

<details>
<summary>💡 Hooking analysis into the canary + background analysis</summary>

```yaml
strategy:
  canary:
    # background analysis runs in parallel from the start — aborts mid-step
    analysis:
      templates: [{ templateName: success-rate }]
      args:
        - { name: service-name, value: app-python-canary }
    steps:
      - setWeight: 20
      - analysis:                       # inline gate after the first step
          templates: [{ templateName: success-rate }]
          args:
            - { name: service-name, value: app-python-canary }
      - setWeight: 60
      - pause: { duration: 30s }
      - setWeight: 100
```

| Analysis result | Rollout action |
|-----------------|----------------|
| ✅ `Successful` | move to next step |
| ❌ `Failed` | auto-abort, scale canary down, reset traffic to stable |
| ⚠️ `Inconclusive` | pause; resume manually with `promote` |

**Forcing a failure:** deploy an image whose handler returns 500, or temporarily point the query at a label that has no good traffic so `successCondition` can't be met. The third failed sample (`failureLimit: 2`) flips the rollout `Degraded`.

**NGINX traffic-routing extension (option b):**
```yaml
strategy:
  canary:
    canaryService: app-python-canary
    stableService: app-python-stable
    trafficRouting:
      nginx:
        stableIngress: app-python-ingress
    steps:
      - setWeight: 20
      - pause: {}
      - setWeight: 100
```

**Resources:**
- [Analysis & Progressive Delivery](https://argoproj.github.io/argo-rollouts/features/analysis/)
- [AnalysisTemplate Specification](https://argoproj.github.io/argo-rollouts/analysis/overview/)
- [NGINX traffic routing](https://argoproj.github.io/argo-rollouts/features/traffic-management/nginx/)
- [Gateway API plugin](https://github.com/argoproj-labs/rollouts-plugin-trafficrouter-gatewayapi)

</details>

---

## How to Submit

1. **Create Branch:**
   ```bash
   git checkout -b lab14
   ```

2. **Commit Work:**
   ```bash
   git add charts/ k8s/
   git commit -m "feat: lab14 progressive delivery with Argo Rollouts 1.8.4 (canary + blue-green)"
   git push -u origin lab14
   ```

3. **Create Pull Requests:**
   - **PR #1:** `your-fork:lab14` → `course-repo:master`
   - **PR #2:** `your-fork:lab14` → `your-fork:master`

4. **Verify:** Rollout manifests present, `ROLLOUTS.md` complete, screenshots included.

---

## Acceptance Criteria

### Main Tasks (10 points)

**Fundamentals (2 pts):**
- [ ] Controller installed and `Running`, pinned to **v1.8.4** (not `latest`)
- [ ] `kubectl argo rollouts version` prints **v1.8.4**
- [ ] Dashboard accessible (screenshot)
- [ ] Three Rollout-vs-Deployment differences documented

**Canary (3 pts):**
- [ ] `Deployment` converted to `Rollout` (same pod template, existing Service still works)
- [ ] 5-step canary **20 → 40 → 60 → 80 → 100** with a manual gate after step 1
- [ ] Rollout triggered, promoted through the gate, progressed to 100%
- [ ] Abort tested — traffic returns to stable, then `retry` completes

**Blue-Green (3 pts):**
- [ ] `blueGreen` strategy with `activeService` + `previewService`
- [ ] Preview service validated in isolation while prod stays on v1
- [ ] Promotion flips active to v2 instantly
- [ ] `undo` rollback tested before `scaleDownDelaySeconds` expires

**Documentation (2 pts):**
- [ ] `k8s/ROLLOUTS.md` covers setup, canary, blue-green, comparison, CLI reference
- [ ] Screenshots from the dashboard / CLI included for both strategies

### Bonus Task (2 points)

- [ ] `AnalysisTemplate` created (Prometheus provider against Lab 8 Prometheus)
- [ ] Wired into the canary as an inline step **and** as `backgroundAnalysis`
- [ ] Auto-rollback demonstrated with a deliberately broken image (no manual abort)
- [ ] Extension completed: **either** multiple AnalysisTemplates **or** real HTTP traffic routing (NGINX / Gateway API)

---

## Rubric

| Criteria | Points | Description |
|----------|--------|-------------|
| **Fundamentals** | 2 pts | v1.8.4 controller + plugin + dashboard; Rollout vs Deployment understood |
| **Canary** | 3 pts | Working 5-step canary with manual gate, promote, and abort |
| **Blue-Green** | 3 pts | Working active/preview cutover with instant `undo` rollback |
| **Documentation** | 2 pts | Complete `ROLLOUTS.md` with screenshots and strategy comparison |
| **Bonus** | 2 pts | Metric-driven auto-abort + a genuinely harder extension |
| **Total** | 12 pts | 10 pts required + 2 pts bonus |

**Grading Scale:**
- **10/10:** Both strategies work end-to-end, excellent documentation
- **8-9/10:** All works, good docs, minor gaps
- **6-7/10:** Canary or blue-green working, basic documentation
- **<6/10:** Missing a core strategy or documentation, needs revision

---

## Resources

<details>
<summary>📚 Official Documentation</summary>

- [Argo Rollouts Documentation](https://argoproj.github.io/argo-rollouts/)
- [Canary Strategy](https://argoproj.github.io/argo-rollouts/features/canary/)
- [Blue-Green Strategy](https://argoproj.github.io/argo-rollouts/features/bluegreen/)
- [Analysis & Progressive Delivery](https://argoproj.github.io/argo-rollouts/features/analysis/)
- [Argo Rollouts releases (pin v1.8.4)](https://github.com/argoproj/argo-rollouts/releases)

</details>

<details>
<summary>🎓 Tutorials & Background</summary>

- [Getting Started Guide](https://argoproj.github.io/argo-rollouts/getting-started/)
- [Canary with NGINX traffic management](https://argoproj.github.io/argo-rollouts/getting-started/nginx/)
- [Gateway API plugin (mesh-agnostic routing)](https://github.com/argoproj-labs/rollouts-plugin-trafficrouter-gatewayapi)
- [Kayenta — automated canary analysis (Netflix)](https://netflixtechblog.com/automated-canary-analysis-at-netflix-with-kayenta-3260bc7acc69)

</details>

---

## Looking Ahead

- **Lab 15:** StatefulSets for stateful workloads — different update model than Rollouts (ordered, per-pod PVCs, `OnDelete` vs `RollingUpdate`).
- **Lab 16:** Monitoring with Prometheus/Grafana — the `AnalysisTemplate` you wrote here is exactly what closes the *observe → react* loop.

---

**Good luck!** 🚀

> **Remember:** a Rollout is a Deployment **plus a strategy** — same pod template, vastly safer release. Without metric gates you've only slowed down a bad deploy; with them, you've automated the rollback.
