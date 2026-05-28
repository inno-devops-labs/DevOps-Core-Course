# Lab 14 — Progressive Delivery with Argo Rollouts

![difficulty](https://img.shields.io/badge/difficulty-intermediate-yellow)
![topic](https://img.shields.io/badge/topic-Progressive%20Delivery-blue)
![points](https://img.shields.io/badge/points-10%2B2-orange)
![tech](https://img.shields.io/badge/tech-Argo%20Rollouts%201.8.4-informational)

> **Goal:** Replace `kind: Deployment` with `kind: Rollout`. Write the canary `steps:` list yourself, write the active + preview `Service` manifests yourself, and (bonus) write the PromQL behind a metric gate that auto-aborts a regressing release.
> **Deliverable:** A PR from `lab14` with `charts/app-python/templates/rollout.yaml`, the two blue-green `Service`s, optional `AnalysisTemplate`, and `docs/LAB14.md`.

---

## Overview

Through Lab 9 you ran rolling updates with a vanilla `Deployment`: K8s swaps pods 25% at a time and stops measuring the moment a readiness probe flips green. The 5xx spike that only fires on 5% of requests still ships to 100% of users. **Progressive delivery** closes that loop — shape traffic in steps, gate each step behind metrics, and let the controller roll back without a human watching Grafana on a Friday.

In this lab you will practice:
- The `Rollout` CRD as a drop-in for `Deployment` — same pod template, new `spec.strategy:` block
- **Writing the canary `steps:` list from scratch** — every `setWeight` and every `pause` is yours
- **Writing the active and preview `Service` manifests from scratch** for blue-green
- **Writing the Prometheus query and gate conditions** in an `AnalysisTemplate` for the bonus
- Driving rollouts with `kubectl argo rollouts <verb>` — and learning the verbs by name

> ⚠️ **Scope:** No traffic-router integration in the main path — `setWeight` approximates by replica ratio (lecture 14 slide 12). One traffic-router option lives in the bonus. No mesh, no notifications controller. Stick to the canary + blue-green core and write every line of strategy yourself.

> 🪨 **Pedagogical core.** The headline proof of this lab is a single screen: `kubectl argo rollouts get rollout app-python` showing **`Status: ॥ Paused`**, **`Message: CanaryPauseStep`**, and **`SetWeight: 25, ActualWeight: 25`** at step 1/6 — then, after you run `promote --full`, the same command at **step 6/6 `Healthy`**. A `Rollout` that goes straight to 100% with no visible pause didn't exercise progressive delivery. **Save that capture.**

---

## Project State

**You should have from previous labs:**
- A k3d cluster on Kubernetes **1.36** (Lab 9)
- The Helm chart at `charts/app-python/` from Lab 10 — your `Deployment` template, `Service` template, `_helpers.tpl`, and `values.yaml`
- ArgoCD **3.4** managing that chart through an `ApplicationSet` (Lab 13)
- The `echo` and `health` plumbing services from Labs 9 / 13 — `health` exposes `/metrics` you'll use in the bonus
- A Prometheus instance from **Lab 8** (Docker-Compose) — see Setup for the in-cluster decision

**This lab adds:**
- `charts/app-python/templates/rollout.yaml` — **you write** (Task 2: canary strategy)
- `charts/app-python/templates/service-active.yaml` — **you write** (Task 3: blue-green active)
- `charts/app-python/templates/service-preview.yaml` — **you write** (Task 3: blue-green preview)
- `charts/app-python/templates/analysistemplate.yaml` — **you write** (Bonus)
- `charts/app-python/values-bluegreen.yaml` — toggle for the blue-green flow (Task 3)
- `docs/LAB14.md` — your submission report

Course-repo plumbing for this lab:
- `labs/lab14/prometheus-pointer.md` — what to do if your Lab 8 Prometheus is still a Docker-Compose stack outside the cluster (the bonus needs an in-cluster URL). **Do not edit.**

By **Lab 16** you'll replace the bare in-cluster Prometheus with kube-prometheus-stack + a `ServiceMonitor` — the `AnalysisTemplate` you write here is the consumer end of that pipeline.

---

## Setup

| Component | Version | Notes |
|---|---|---|
| Argo Rollouts controller | **v1.8.4** | Released Feb 13 2026. Do NOT use `latest` |
| `kubectl argo rollouts` plugin | **v1.8.4** | Match the controller |
| Kubernetes (k3s) | `v1.36.1-k3s1` | from Lab 9 |
| Helm | `v4.1.x` | from Lab 10 |
| Prometheus | `3.x` | Lab 8's instance — see in-cluster note below |

```bash
kubectl get nodes                  # 3-node k3d cluster from Lab 9 must be Running
helm version                       # 4.1.x from Lab 10
kubectl argo rollouts version      # not installed yet — that's Task 1
```

> ⚠️ **Prometheus location matters for the bonus.** Lab 8 ran Prometheus in a Docker-Compose stack on your laptop. An `AnalysisTemplate` running **inside** the cluster cannot reach `http://localhost:9090` on your host. Three options, see `labs/lab14/prometheus-pointer.md`:
>
> 1. **Point at the host gateway** — k3d exposes `host.k3d.internal`; works for the bonus today but Lab 16 replaces this with the in-cluster stack anyway.
> 2. **Run a tiny in-cluster Prometheus** in the `monitoring` namespace (manifest pointer in `labs/lab14/`).
> 3. **Skip the bonus.** Main tasks 1–4 don't need Prometheus.

Directory layout you will produce:

```
charts/app-python/
├── templates/
│   ├── rollout.yaml                # YOU write — replaces deployment.yaml (Task 2)
│   ├── service-active.yaml         # YOU write (Task 3)
│   ├── service-preview.yaml        # YOU write (Task 3)
│   └── analysistemplate.yaml       # YOU write (Bonus)
├── values.yaml                     # add a `strategy.type` toggle
└── values-bluegreen.yaml           # YOU write (Task 3) — override `strategy.type`
docs/
└── LAB14.md                        # your submission report
```

---

## Task 1 — Argo Rollouts fundamentals (2 pts)

### 1.1 — Why a separate controller instead of a Deployment

In `docs/LAB14.md` write **3** sentences each on:

1. What signal does a `Deployment` actually use to decide a rollout succeeded — and why is that insufficient when a bug fires on 5% of requests?
2. How does Argo Rollouts shift "traffic" without a traffic router (lecture 14 slide 12) — and what's the accuracy limit at 5 replicas?
3. Which **three** new top-level fields does the `Rollout` CRD add that `Deployment` doesn't have? (Hint: lecture 14 slides 6–11 — `strategy.canary`, `strategy.blueGreen`, `analysis`/`backgroundAnalysis`.)

### 1.2 — Install the controller pinned to v1.8.4

`YOUR TASK`: install the controller into the `argo-rollouts` namespace from the **v1.8.4** release manifest — not `latest`, not `main`. The plumbing release URL pattern is `https://github.com/argoproj/argo-rollouts/releases/download/<version>/install.yaml`.

```bash
kubectl create namespace argo-rollouts
kubectl apply -n argo-rollouts -f ___        # YOUR TASK: the v1.8.4 install.yaml URL
kubectl -n argo-rollouts rollout status deploy/argo-rollouts --timeout=120s
```

> 💡 The reason `latest` is forbidden: a release that breaks `bluegreen` analysis (1.8.0–1.8.3 had exactly this bug — see lecture 14 slide 21) would silently ship through your students' lab. Pin the version your TAs verified.

### 1.3 — Install the matching kubectl plugin

`YOUR TASK`: download the **v1.8.4** plugin binary for your OS/arch, make it executable, and place it on `PATH` as `kubectl-argo-rollouts`. Verify with `kubectl argo rollouts version` — both client and server should report `v1.8.4`.

```bash
# Linux amd64 example — adapt for darwin-arm64 / windows-amd64
curl -fSL -o kubectl-argo-rollouts ___       # YOUR TASK: the v1.8.4 plugin binary URL
chmod +x kubectl-argo-rollouts
sudo mv kubectl-argo-rollouts /usr/local/bin/

kubectl argo rollouts version                # expect: v1.8.4 client + v1.8.4 server
```

> 💡 The plugin is **not** a `kubectl` subcommand — it's a separate binary `kubectl` shells out to. If `kubectl argo rollouts version` says "unknown command", the binary isn't on your `PATH`.

### 1.4 — Install the dashboard (optional but useful)

`YOUR TASK`: apply the v1.8.4 dashboard manifest, port-forward it to `localhost:3100`, and screenshot the empty dashboard (you'll repopulate it once Task 2 produces a rollout).

```bash
kubectl apply -n argo-rollouts -f ___        # YOUR TASK: the v1.8.4 dashboard-install.yaml URL
kubectl argo rollouts ___                    # YOUR TASK: which subcommand opens the local UI on :3100?
                                             #            (one of: dashboard, ui, serve, web)
```

### 1.5 — Proof of work

**Paste into `docs/LAB14.md`:**

- The 3 research answers from §1.1
- `kubectl -n argo-rollouts get pods` — controller pod `Running`
- `kubectl argo rollouts version` — client + server both `v1.8.4`
- A screenshot of the empty dashboard at `http://localhost:3100`

---

## Task 2 — Canary deployment (3 pts) ← **headline task**

### 2.1 — Convert `Deployment` → `Rollout`

Your Lab 10 chart has `templates/deployment.yaml`. **Rename it** to `templates/rollout.yaml` and change the kind. Everything inside `spec.template:` stays identical — same labels, same container, same ports, same probes. The Rollout CRD reuses your `Deployment` pod template byte-for-byte. **Don't change the `Service` selector** — Argo Rollouts injects an extra `rollouts-pod-template-hash` label to distinguish stable from canary pods, but your existing selector (`app.kubernetes.io/name` + `instance`) still matches both.

`YOUR TASK`: write `templates/rollout.yaml`. The skeleton below shows the parts that are **identical to your Deployment** (so you don't reinvent the wheel) and **blanks the canary `steps:` list entirely** — you write each step.

```yaml
# charts/app-python/templates/rollout.yaml
apiVersion: ___                                    # YOUR TASK: which apiGroup/version owns Rollout?
                                                   #            (hint: NOT apps/v1 — see lecture 14 slide 7)
kind: ___                                          # YOUR TASK
metadata:
  name: {{ include "app-python.fullname" . }}
  labels:
    {{- include "app-python.labels" . | nindent 4 }}
spec:
  replicas: {{ .Values.replicaCount }}             # keep your Lab 10 default — needs ≥ 4 for visible 25/50/75 weights
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
          image: "{{ .Values.image.repository }}:{{ .Values.image.tag | default .Chart.AppVersion }}"
          # ⬇️ pod template body is IDENTICAL to your Lab 10 Deployment — copy it verbatim
          # ⬇️ (ports, probes, resources, env). Shown elided here for brevity.
          # See your charts/app-python/templates/deployment.yaml for the body to paste.
  strategy:
    canary:
      # YOUR TASK: write the 7-element step list for a 25 → 50 → 75 → 100 canary
      # with a MANUAL pause between every weight change. Format hints below.
      #
      # Step semantics (lecture 14 slide 7):
      #   - `- setWeight: ___`           shift traffic/replica ratio to the listed percentage
      #   - `- pause: {}`                HARD manual gate — rollout waits for `promote`
      #   - `- pause: { duration: ___ }` timed pause (e.g. "30s", "2m") — rollout resumes itself
      #
      # The headline proof of this lab is a PAUSED canary at SetWeight 25 (the lab14 refs
      # quote `CanaryPauseStep` at Step 1/6). So step 1 must shift to 25% and step 2 must be
      # a MANUAL gate, not a timed pause — otherwise the rollout never sits there long
      # enough for the `kubectl argo rollouts get` capture to show `Paused`.
      #
      # Required progression: 25 → pause → 50 → pause → 75 → pause → 100
      # (the trailing 100 doesn't need a pause; the rollout marks itself Healthy at step 6/6)
      steps:
        - setWeight: ___                            # YOUR TASK
        - pause: ___                                # YOUR TASK: which pause form? (see hint above)
        - setWeight: ___                            # YOUR TASK
        - pause: ___                                # YOUR TASK
        - setWeight: ___                            # YOUR TASK
        - pause: ___                                # YOUR TASK
        - setWeight: ___                            # YOUR TASK
```

**Why each step matters:**
- **`setWeight: 25` at step 1** is what makes `ActualWeight: 25` show up in `kubectl argo rollouts get`. Without it your first weight is 100 and there's no progressive delivery to demo.
- **`pause: {}` (no duration)** sits there until you run `promote`. That's the gate a real team would put metric review behind.
- **`pause: { duration: 30s }`** is the alternative — useful for CI demos that can't wait for a human. Either is acceptable, but **at least step 2 must be `pause: {}`** so the canary visibly sits at 25% for the capture.
- **Trailing 100 with no pause** — the controller marks the rollout `Healthy` automatically; an explicit `setWeight: 100` at the end is fine but a redundant `- pause: {}` after it leaves the rollout stuck.

### 2.2 — Trigger the first rollout and capture the pause

Apply the chart (via ArgoCD sync if you wired Lab 13's ApplicationSet, otherwise `helm upgrade`). The first `Rollout` apply creates the resource; the controller marks it `Healthy` at 100% without going through the steps (steps only run for **subsequent** revisions). Now bump the image to trigger a real canary:

```bash
helm upgrade app-python ./charts/app-python --set image.tag=v2
# or commit values-dev.yaml with the new tag and let ArgoCD sync it
```

Then watch:

```bash
kubectl argo rollouts ___ rollout app-python --watch   # YOUR TASK: which verb shows live status?
                                                       #            (one of: get, describe, status, list)
```

`YOUR TASK`: capture the moment the rollout sits at step 1/6 with `Message: CanaryPauseStep`, `SetWeight: 25`, `ActualWeight: 25`. This is the headline artifact of Lab 14.

### 2.3 — Promote past every gate

```bash
kubectl argo rollouts ___ app-python --full            # YOUR TASK: which verb advances past ALL remaining pauses?
                                                       #            (full = skip the manual gates AND wait for them)
```

Then re-capture `kubectl argo rollouts get rollout app-python` showing **step 6/6, `Status: ✔ Healthy`, `SetWeight: 100`**.

### 2.4 — Abort mid-rollout

`YOUR TASK`: trigger a third rollout (bump the tag to `v3`), wait for it to reach step 1/6 paused at 25%, and then abort it. Confirm traffic returns to the stable ReplicaSet and the rollout reports `Degraded`.

```bash
helm upgrade app-python ./charts/app-python --set image.tag=v3
# wait for the paused 25% step:
kubectl argo rollouts get rollout app-python

kubectl argo rollouts ___ app-python                   # YOUR TASK: which verb cancels the in-progress rollout?
kubectl argo rollouts get rollout app-python           # expect: Status: ✖ Degraded, traffic on stable

# Now resume from step 0 once you've "fixed" the image (e.g. re-bump back to v2):
kubectl argo rollouts ___ rollout app-python           # YOUR TASK: which verb restarts a Degraded rollout?
```

### 2.5 — Proof of work

**Paste into `docs/LAB14.md`:**

- The contents of your `templates/rollout.yaml` `spec.strategy.canary` block (just the `steps:` list — 8–10 lines)
- The **headline capture** from §2.2 — `kubectl argo rollouts get rollout app-python` showing `Paused`, `CanaryPauseStep`, `Step: 1/6`, `SetWeight: 25, ActualWeight: 25`
- The **`promote --full`** capture from §2.3 — same command, now `Step: 6/6, Status: ✔ Healthy, SetWeight: 100`
- The **abort + retry** captures from §2.4 — `Degraded` after abort, then `Healthy` after `retry`
- 2–3 sentences on what you observed in the dashboard during the paused window — was 1 of 4 replicas on the new ReplicaSet? (lecture 14 slide 8)

---

## Task 3 — Blue-green deployment (3 pts)

### 3.1 — Why a second strategy

In `docs/LAB14.md` answer in 2–3 sentences:
- What's the canonical workload type for blue-green over canary? (Hint: lecture 14 slide 5 — schema migrations.)
- During the cutover window, how many copies of your pods are running? Why does that matter for cluster cost?

### 3.2 — Write the two `Service` manifests from scratch

Blue-green needs **two** Services pointing at the same pod label set — Argo Rollouts rewrites their selectors on promotion so `activeService` always points at the live ReplicaSet and `previewService` always points at the staged one. Your Lab 10 chart had **one** Service; you now write **two**.

`YOUR TASK`: write `templates/service-active.yaml` and `templates/service-preview.yaml` from scratch. They must:

- Use the chart's `selectorLabels` helper (so the rollout controller can mutate the selector)
- Differ only in `metadata.name` — one is `<fullname>` (the existing name your callers use), the other is `<fullname>-preview`
- Both expose the same `port` / `targetPort` as your Lab 10 Service

(No skeleton — you've written ~6 Service manifests by now in Labs 9, 10, 13. If you need the API shape, `kubectl explain service.spec` is one shell command away.)

> 💡 **Naming matters.** The `activeService` name in your `Rollout` spec must match an existing `Service` *exactly*. A typo here results in `Rollout` errors like `service "app-python-actv" not found` — and the controller will not heal it. Reference the value via `include "app-python.fullname" .` from the same helper your Service uses.

### 3.3 — Configure the blue-green strategy

`YOUR TASK`: create `values-bluegreen.yaml` that **overrides** your Rollout's `strategy:` block. Use a single boolean toggle in `values.yaml` (e.g. `strategy.type: canary` default; override to `bluegreen` in the new file) and a `{{- if eq .Values.strategy.type "bluegreen" }}` branch in `rollout.yaml`. **Don't** ship both strategies side-by-side — Argo Rollouts rejects a Rollout that declares both `canary` and `blueGreen`.

The blue-green outer shape below is the only part shown; the **four values** that define your cutover behaviour are blanks.

```yaml
# in rollout.yaml, inside spec:
  strategy:
    {{- if eq .Values.strategy.type "bluegreen" }}
    blueGreen:
      activeService: ___                # YOUR TASK: name of the Service production traffic hits
                                        #            (hint: matches your <fullname>)
      previewService: ___               # YOUR TASK: name of the Service QA / smoke tests hit
                                        #            (hint: matches <fullname>-preview)
      autoPromotionEnabled: ___         # YOUR TASK: true or false?
                                        #            (this lab needs manual promote — see lecture 14 slide 9)
      scaleDownDelaySeconds: ___        # YOUR TASK: how many seconds to keep the OLD ReplicaSet
                                        #            alive after promotion, for instant `undo`?
                                        #            (suggested: 300 = 5 min — short enough to not pay
                                        #             for two ReplicaSets all day, long enough that you
                                        #             can `undo` if you spot a bug in the first minute)
      # prePromotionAnalysis:           # optional — covered in the bonus
    {{- else }}
    canary:
      steps:
        # ... your Task 2 step list ...
    {{- end }}
```

### 3.4 — Run the blue-green cutover

```bash
helm upgrade app-python ./charts/app-python -f values-bluegreen.yaml --set image.tag=v1
# Confirm the active Service serves v1:
kubectl port-forward svc/app-python 8080:80 &
curl -s localhost:8080/ | jq .service

# Bump to v2 — the controller spins up the new ReplicaSet behind the PREVIEW Service:
helm upgrade app-python ./charts/app-python -f values-bluegreen.yaml --set image.tag=v2

# In another shell, validate v2 via the preview Service (prod still on v1):
kubectl port-forward svc/app-python-preview 8081:80 &
curl -s localhost:8081/ | jq .service       # YOUR TASK: confirm v2

# Confirm the two Services have DIFFERENT pod IPs in their endpoints right now —
# this is the proof the controller wrote two different selectors:
kubectl get endpoints app-python app-python-preview -o wide

# Promote — the active Service flips to v2 instantly (no new pods scheduled):
kubectl argo rollouts ___ app-python                  # YOUR TASK: same verb as Task 2 manual gate

# Test instant rollback BEFORE scaleDownDelaySeconds expires:
kubectl argo rollouts ___ app-python                  # YOUR TASK: which verb rolls back to the previous ReplicaSet?
kubectl get endpoints app-python                      # active flipped back to v1 pod IPs
```

### 3.5 — Proof of work

**Paste into `docs/LAB14.md`:**

- The two Service manifests in full (one per code block)
- Your `blueGreen:` block with all four values filled in + a one-sentence justification for `scaleDownDelaySeconds`
- The **two `kubectl get endpoints`** captures from §3.4 showing `app-python` and `app-python-preview` pointing at **different pod IPs** during the cutover window — this is the headline blue-green artifact
- The `promote` + `undo` captures showing the active Service IPs flipping
- 2 sentences comparing the speed of blue-green `undo` vs canary `abort` — which is faster, and why

---

## Task 4 — Documentation (2 pts)

`YOUR TASK`: write `docs/LAB14.md` with these sections, in order:

1. **Setup** — Task 1 captures (controller / plugin / dashboard versions, the three Rollout-vs-Deployment differences)
2. **Canary strategy** — your `steps:` list, the §2.5 captures (Paused at 25% → Healthy at 6/6 → Degraded after abort → Healthy after retry), and one paragraph on what the dashboard showed during the paused window
3. **Blue-green strategy** — your two Service manifests, your `blueGreen:` block, the endpoint-IP diff capture, the promote + undo evidence
4. **Strategy comparison** — when do you reach for canary vs blue-green? Reference the lecture 14 slide 5 table; pick `app-python` (your service) and justify which strategy you'd use *in production* for a typical feature release vs a schema migration
5. **CLI reference** — the **five verbs** you ran (`get`, `promote`, `abort`, `retry`, `undo` — plus `version` and `dashboard`), one sentence per verb on what it does
6. **Challenges & learnings** — at least one real one (label selector surprise, scaleDownDelay too short, wrong apiVersion, …) — see Common Pitfalls

---

## Bonus Task — Metric-driven auto-abort (2 pts)

**Objective:** Add an `AnalysisTemplate` that queries Prometheus and **auto-aborts** the canary when the metric regresses — no human intervention.

The lecture (slides 10–11) showed the *shape* of an AnalysisTemplate. You write the actual query, success condition, failure limit, and cadence. Use the metrics you instrumented in **Lab 8** — `app_requests_total{status}` is the canonical RED-error-rate substrate.

### Bonus.1 — Write the AnalysisTemplate

`YOUR TASK`: write `charts/app-python/templates/analysistemplate.yaml`. The kind + outer `spec.metrics:` shape is given; the **query, success condition, failure limit, and interval** are yours.

```yaml
# charts/app-python/templates/analysistemplate.yaml
apiVersion: argoproj.io/v1alpha1
kind: ___                                          # YOUR TASK: which kind? (hint: slide 10)
metadata:
  name: success-rate
spec:
  args:
    - name: service-name
  metrics:
    - name: success-rate
      interval: ___                                # YOUR TASK: how often to sample?
                                                   #   Rule from slide 18: ≥ scrape_interval × 4
                                                   #   so if Prometheus scrapes every 15s, 60s is the floor.
      count: ___                                   # YOUR TASK: how many samples before declaring success?
                                                   #   3–5 is typical — fewer = jittery, more = slow gates.
      successCondition: ___                        # YOUR TASK: a Go expression over `result` (slide 10)
                                                   #   You're computing "fraction of non-5xx requests".
                                                   #   The query below returns a single float in [0, 1].
                                                   #   What threshold makes sense for 99.x% availability?
                                                   #   (NOT 0.95 — that's the slide-16 anti-pattern.)
      failureLimit: ___                            # YOUR TASK: how many failed samples before AUTO-ABORT?
                                                   #   0 = abort on first miss (too jittery)
                                                   #   2 = the lecture's recommendation
      provider:
        prometheus:
          address: ___                             # YOUR TASK: in-cluster Prometheus URL
                                                   #   See labs/lab14/prometheus-pointer.md for the three options.
                                                   #   Format: http://<service-name>.<namespace>:9090
          query: |
            ___                                    # YOUR TASK: PromQL for the
                                                   # "fraction of non-5xx requests" metric over a 2-minute window.
                                                   #
                                                   # Use the Lab 8 metric: app_requests_total{status="..."}
                                                   # The shape is:
                                                   #   sum(rate(<good>[2m])) / sum(rate(<all>[2m]))
                                                   # — see slide 10 for the literal template.
                                                   #
                                                   # IMPORTANT: when the canary pod has just started, no requests
                                                   # have hit it yet → the numerator and denominator are both 0
                                                   # → Prometheus returns an EMPTY VECTOR → AnalysisTemplate
                                                   # crashes on `result[0]` with NaN/index-out-of-range.
                                                   # Fix: append `or on() vector(0)` so the empty case returns 0
                                                   # rather than nothing. (See Common Pitfalls.)
                                                   #
                                                   # The `service-name` arg is yours to use:
                                                   # filter by `service="{{args.service-name}}"` or by the
                                                   # `app.kubernetes.io/name` label your `web` pods carry.
```

### Bonus.2 — Wire it into the canary

`YOUR TASK`: edit your Task 2 canary `steps:` so an `analysis` step fires after the first weight change, **and** add a spec-level continuous analysis so a mid-step regression aborts immediately (not just at the next gate).

```yaml
  strategy:
    canary:
      ___:                                         # YOUR TASK: which spec-level key runs analysis CONTINUOUSLY
                                                   #   (in parallel with steps), so a regression mid-step
                                                   #   aborts immediately? (hint: lecture 14 slide 11 "pro tip")
        templates:
          - templateName: ___                      # YOUR TASK: which AnalysisTemplate name from Bonus.1?
        args:
          - name: service-name
            value: ___                             # YOUR TASK: which service name does the PromQL filter on?
      steps:
        - setWeight: 25
        - ___:                                     # YOUR TASK: which step type runs analysis as a GATE
                                                   #   (i.e. blocks until success/failure)?
            templates:
              - templateName: ___                  # YOUR TASK
            args:
              - name: service-name
                value: ___                         # YOUR TASK
        # … rest of your Task 2 steps …
```

### Bonus.3 — Prove auto-abort

`YOUR TASK`: ship a deliberately broken image (e.g. add an `app.before_request` handler that returns `500` half the time) and trigger a rollout. Without touching the CLI, the rollout must go `Degraded` within `interval × failureLimit + count × interval` seconds. Capture:

- `kubectl argo rollouts get rollout app-python` showing `Degraded` with `Message: RolloutAborted` after analysis failure
- `kubectl get analysisruns -o wide` showing the failed `AnalysisRun` with its `Phase: Failed` and the failed `MeasurementCount`

### Bonus.4 — Go further (required for the full 2 pts) — pick ONE

**Option A — Multiple AnalysisTemplates.** Write a second AnalysisTemplate (e.g. `p95-latency` using `histogram_quantile(0.95, ...)` over your Lab 8 Histogram), reference **both** templates in a single `analysis:` step, and document how `failureLimit` interacts when *either* template fails. (One AnalysisTemplate failing aborts the rollout — the failure is OR'd across templates within a step.)

**Option B — Multiple metrics in one AnalysisTemplate.** Add a second entry to `spec.metrics:` (e.g. error-rate AND p95 latency) inside the same `AnalysisTemplate`. Argo Rollouts evaluates each independently; the rollout aborts when *any* metric exceeds its `failureLimit`. Document the cleaner ergonomics vs Option A.

### Bonus.5 — Proof of work

**Paste into `docs/LAB14.md`:**

- The full `AnalysisTemplate` you wrote — query, interval, count, successCondition, failureLimit, provider URL
- The §Bonus.3 captures (rollout `Degraded` after analysis failure + the `AnalysisRun` showing the Prometheus measurements that triggered it)
- Your Option A or B extension — second template OR second metric, with the file and the captured second `AnalysisRun`
- 2–3 sentences on which extension you picked and why

---

## How to Submit

```bash
git switch -c lab14
git add charts/app-python/templates/rollout.yaml
git add charts/app-python/templates/service-active.yaml charts/app-python/templates/service-preview.yaml
git add charts/app-python/values-bluegreen.yaml
git add charts/app-python/templates/analysistemplate.yaml  # bonus only
git add docs/LAB14.md
git commit -m "feat(lab14): argo rollouts 1.8.4 — canary + blue-green + analysis"
git push -u origin lab14
```

Open **two** PRs:

- `your-fork:lab14` → `course-repo:master` *(reviewed)*
- `your-fork:lab14` → `your-fork:master` *(merges into your own main when done)*

PR checklist:

```text
- [ ] Task 1 — controller + plugin + dashboard pinned to v1.8.4; research answers in LAB14.md
- [ ] Task 2 — Rollout written from scratch; canary 25→pause→50→pause→75→pause→100;
              PAUSED-at-25% capture + Healthy-at-6/6 capture + abort/retry captures
- [ ] Task 3 — two Service manifests written from scratch; blueGreen block with all four values;
              endpoints diff during cutover; promote + undo evidence
- [ ] Task 4 — LAB14.md with all six sections
- [ ] Bonus — AnalysisTemplate written from scratch; auto-abort demonstrated on a broken image;
              Option A or B extension documented
```

---

## Acceptance Criteria

### Task 1 — Fundamentals (2 pts)
- ✅ Controller, plugin, and dashboard **all v1.8.4** (not `latest`)
- ✅ `kubectl argo rollouts version` shows client + server both `v1.8.4`
- ✅ The three Rollout-vs-Deployment differences documented in LAB14.md

### Task 2 — Canary (3 pts)
- ✅ `templates/rollout.yaml` written from scratch — `apiVersion`, `kind`, full `spec.strategy.canary.steps:` list filled in
- ✅ Step list is `25 → pause → 50 → pause → 75 → pause → 100` — **the pause after 25 must be `pause: {}` (manual)**
- ✅ **Headline capture**: `kubectl argo rollouts get rollout app-python` showing `Status: ॥ Paused`, `Message: CanaryPauseStep`, `Step: 1/6`, `SetWeight: 25, ActualWeight: 25`
- ✅ **Promotion capture**: same command after `promote --full` showing `Status: ✔ Healthy`, `Step: 6/6`, `SetWeight: 100`
- ✅ Abort + retry demonstrated — captures show `Degraded` then `Healthy` again

### Task 3 — Blue-Green (3 pts)
- ✅ `templates/service-active.yaml` and `templates/service-preview.yaml` **written from scratch** — no skeleton given in this lab
- ✅ `blueGreen:` block with all four values filled in (`activeService`, `previewService`, `autoPromotionEnabled`, `scaleDownDelaySeconds`)
- ✅ **Endpoints diff capture**: `kubectl get endpoints app-python app-python-preview` shows **different pod IPs** during the cutover window
- ✅ Promote + undo demonstrated — `kubectl get endpoints app-python` shows the active selector flipping back

### Task 4 — Documentation (2 pts)
- ✅ All six sections present in `docs/LAB14.md`
- ✅ CLI reference section names the five verbs (`get`, `promote`, `abort`, `retry`, `undo`) with a sentence each
- ✅ One real challenge documented (not "I had never seen YAML before")

### Bonus — Metric-driven auto-abort (2 pts)
- ✅ `AnalysisTemplate` written from scratch — query, condition, interval, count, failureLimit all yours
- ✅ Query uses the Lab 8 `app_requests_total` metric with `or on() vector(0)` guard
- ✅ Auto-abort demonstrated on a deliberately broken image — captures show `Degraded` with `RolloutAborted` from an analysis failure (no manual `abort`)
- ✅ Option A or B extension shipped — second template OR second metric, with its own `AnalysisRun` evidence

---

## Rubric

| Task | Points | Criteria |
|------|-------:|----------|
| **Task 1** — Fundamentals | **2** | v1.8.4 controller + plugin + dashboard; Rollout-vs-Deployment differences |
| **Task 2** — Canary | **3** | Hand-written steps; paused-at-25% headline capture; promote-to-Healthy; abort + retry |
| **Task 3** — Blue-Green | **3** | Hand-written Services; four-value `blueGreen:` block; endpoint IPs differ during cutover; instant `undo` |
| **Task 4** — Documentation | **2** | Six sections, CLI verbs explained, real challenge |
| **Bonus** — Auto-abort | **2** | Hand-written AnalysisTemplate + Lab 8 PromQL; auto-aborted on broken image; Option A or B extension |
| **Total** | **12** | 10 main + 2 bonus |

**Grading:**
- **10/10:** Both strategies end-to-end, the headline paused-at-25% capture is unambiguous, docs are honest
- **8–9/10:** Both work, minor gaps in evidence (e.g. blue-green endpoint diff missing)
- **6–7/10:** Canary works but blue-green Services not written from scratch, OR endpoint-IP diff missing
- **<6/10:** Step list copy-pasted from the docs without the 25→pause headline, OR Services not written

---

## Resources

<details>
<summary>📚 Argo Rollouts documentation</summary>

- [Argo Rollouts docs](https://argoproj.github.io/argo-rollouts/) — start at *Features*
- [Rollout Specification](https://argoproj.github.io/argo-rollouts/features/specification/) — every field in the CRD
- [Canary Strategy](https://argoproj.github.io/argo-rollouts/features/canary/)
- [Blue-Green Strategy](https://argoproj.github.io/argo-rollouts/features/bluegreen/)
- [Analysis & Progressive Delivery](https://argoproj.github.io/argo-rollouts/features/analysis/)
- [`kubectl argo rollouts` CLI](https://argoproj.github.io/argo-rollouts/generated/kubectl-argo-rollouts/kubectl-argo-rollouts/) — every subcommand
- [Argo Rollouts v1.8.4 release](https://github.com/argoproj/argo-rollouts/releases/tag/v1.8.4) — pin this exact tag

</details>

<details>
<summary>📦 Course plumbing</summary>

- `labs/lab14/prometheus-pointer.md` — three ways to give the in-cluster AnalysisTemplate a reachable Prometheus URL
- `plumbing/health/README.md` — the `/metrics` endpoint you can also point the bonus query at

</details>

<details>
<summary>⚠️ Common Pitfalls (from real dry-runs)</summary>

- **`kubectl rollout restart deployment/app-python` does NOT work on a Rollout.** The core `kubectl rollout` subcommands target `Deployment` / `DaemonSet` / `StatefulSet`. The `Rollout` CRD is owned by Argo Rollouts, not the K8s rollout API. Use `kubectl argo rollouts restart <name>` instead — same verb, different binary. Symptom: `error: deployments.apps "app-python" not found` even though `kubectl get rollouts` shows it.

- **AnalysisTemplate crashes on `result[0]` with NaN when there's no traffic.** When the canary pod has just started, no requests have hit it → `sum(rate(app_requests_total{...}[2m]))` returns an **empty vector**, not 0. The `successCondition` expression `result[0] >= 0.99` then errors out and the AnalysisRun shows `Inconclusive` or `Error` instead of evaluating. Fix: append `or on() vector(0)` to the PromQL — Prometheus then returns `0` for the empty case and the expression evaluates cleanly. This is the single most common bonus-task failure.

- **`scaleDownDelaySeconds` is a foot-gun for traffic-still-on-preview surprises.** Setting it too high (e.g. `3600`) means every blue-green cutover leaves the **old** ReplicaSet running for an hour — burning compute and confusing anyone who sees stale pods. Setting it too low (e.g. `30`) means by the time you notice a v2 bug in production, there's no v1 ReplicaSet left to `undo` to. 300 seconds (5 min) is a sane default; document your choice.

- **`kubectl set image` needs the plugin, not core kubectl.** `kubectl set image rollout/app-python web=ghcr.io/...:v2` errors with `the server doesn't have a resource type "rollout"`. Use `kubectl argo rollouts set image app-python web=ghcr.io/...:v2` instead. Or — better practice — drive image changes through Helm / GitOps and let ArgoCD sync, so the change is in Git.

- **Prometheus not in-cluster → AnalysisTemplate can't reach it.** Lab 8's Prometheus runs in a Docker-Compose stack on your laptop. From inside k3d, `http://localhost:9090` resolves to the **pod's** localhost, not your host's. Three fixes documented in `labs/lab14/prometheus-pointer.md`: (a) `host.k3d.internal:9090` from inside k3d (works today, breaks in Lab 16 when you move on); (b) deploy a minimal Prometheus into the cluster's `monitoring` namespace; (c) wait for Lab 16's kube-prometheus-stack and skip the bonus until then.

- **Selector pollution from the Lab 13 chart.** Argo Rollouts injects `rollouts-pod-template-hash` onto pod labels so it can distinguish stable from canary. If your `selectorLabels` helper from Lab 10 includes anything beyond `name` + `instance` (e.g. `version` — which is the lecture-15 anti-pattern), the controller's mutation fights your helper and the Service ends up selecting *both* ReplicaSets. Keep `selectorLabels` to the two-key minimum (this is the same rule from Lab 10's helpers).

- **Promoting a manual gate before the canary is actually paused.** `kubectl argo rollouts promote app-python` returns immediately if there's no active pause — it does **not** wait for the next step. If you run it too eagerly in a script, the rollout skips your headline-capture moment and runs straight to 100%. Wait until `kubectl argo rollouts get` shows `Paused / CanaryPauseStep` before promoting.

- **`autoPromotionEnabled: true` in blue-green silently skips the manual gate.** The default is `false`, but a lot of tutorials show `true` for CI demos. With `true`, the new ReplicaSet is promoted as soon as it goes Ready — your preview-Service-validation window is **zero seconds**. Always set this to `false` in your lab values; only ever `true` in fully automated pipelines with prePromotionAnalysis.

- **`apiVersion: apps/v1` in the Rollout.** Muscle memory from `Deployment` strikes — Rollout lives in `argoproj.io/v1alpha1`, not `apps/v1`. `kubectl apply` returns `no matches for kind "Rollout" in version "apps/v1"` and the file silently fails to apply if you're using `helm template | kubectl apply -f -`. Always double-check the first two lines.

</details>

<details>
<summary>🛠️ Tools worth knowing</summary>

- `alias kr='kubectl argo rollouts'` — saves you 18 characters every command
- [`argo-rollouts/dashboard`](http://localhost:3100) — the local UI is the cleanest way to grab Task 2 / 3 screenshots
- [`kubectl get analysisruns -A`](https://argoproj.github.io/argo-rollouts/features/analysis/) — every analysis run the controller ever spawned, including the failed ones the rollout aborted on

</details>

---

## Looking Ahead

| Lab | What it adds to this stack |
|---:|---|
| 15 | StatefulSets — stateful workloads don't fit the Rollout model; ordered pod identity + per-pod PVC instead |
| 16 | **kube-prometheus-stack** + `ServiceMonitor` CRDs — replaces your hand-rolled Prometheus URL with a proper in-cluster monitoring stack; your `AnalysisTemplate` from this lab keeps working, just with `address: http://prometheus-operated.monitoring:9090` |

---

**Good luck!** 🚦

> **Remember:** a `Rollout` is a `Deployment` plus a strategy. Without metric gates you've only slowed down a bad deploy; with them, you've automated the rollback. The headline of this lab — `SetWeight: 25, ActualWeight: 25, Message: CanaryPauseStep` — is the moment "deployed" stops meaning "released" and starts meaning "released *if the canary survives the gate*."
