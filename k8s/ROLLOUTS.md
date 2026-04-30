# Argo Rollouts — Progressive Delivery

Canary and blue-green deployment strategies for the `app-python` Helm
chart, implemented with Argo Rollouts.

## Contents

1. [Setup](#1-setup)
2. [Rollout vs Deployment](#2-rollout-vs-deployment)
3. [Chart Layout](#3-chart-layout)
4. [Canary Deployment](#4-canary-deployment)
5. [Blue-Green Deployment](#5-blue-green-deployment)
6. [Strategy Comparison](#6-strategy-comparison)
7. [CLI Reference](#7-cli-reference)
8. [Troubleshooting](#8-troubleshooting)

---

## 1. Setup

### Controller and CRDs

```bash
kubectl create namespace argo-rollouts
kubectl apply -n argo-rollouts \
  -f https://github.com/argoproj/argo-rollouts/releases/latest/download/install.yaml
```

### Dashboard

```bash
kubectl apply -n argo-rollouts \
  -f https://github.com/argoproj/argo-rollouts/releases/latest/download/dashboard-install.yaml

kubectl port-forward svc/argo-rollouts-dashboard -n argo-rollouts 3100:3100
```

UI is then available at `http://localhost:3100`.

### kubectl Plugin (macOS arm64)

```bash
mkdir -p ~/bin
curl -fsSL -o ~/bin/kubectl-argo-rollouts \
  https://github.com/argoproj/argo-rollouts/releases/latest/download/kubectl-argo-rollouts-darwin-arm64
chmod +x ~/bin/kubectl-argo-rollouts
export PATH="$HOME/bin:$PATH"
```

### Verification

```bash
kubectl argo rollouts version
kubectl get pods -n argo-rollouts
```

Expected: controller and dashboard pods `Running 1/1`.

---

## 2. Rollout vs Deployment

| Field | Deployment | Rollout |
|-------|------------|---------|
| `apiVersion` | `apps/v1` | `argoproj.io/v1alpha1` |
| `kind` | `Deployment` | `Rollout` |
| `spec.strategy` | `RollingUpdate` / `Recreate` | `canary` / `blueGreen` |
| Traffic shaping | none | step-based weight (canary), service swap (blueGreen) |
| Manual gate | none | `pause: {}` step + `kubectl argo rollouts promote` |
| Rollback | revision-history rollback | `abort` (instant) / `undo` |
| Analysis | external | `AnalysisTemplate` integration |
| Preview env | none | dedicated `previewService` (blueGreen) |

The pod template (`spec.template`) and selector are byte-identical to a
Deployment. Converting an existing Deployment is a one-field change in
`kind` plus the strategy block.

---

## 3. Chart Layout

| File | Purpose |
|------|---------|
| `templates/deployment.yaml` | Rendered when `rollout.enabled: false` |
| `templates/rollout.yaml` | Rendered when `rollout.enabled: true` |
| `templates/service.yaml` | Active service (used by both strategies) |
| `templates/service-preview.yaml` | Preview service, rendered only for `strategy: blueGreen` |
| `values.yaml` | Defaults (rollout disabled) |
| `values-canary.yaml` | Canary release values |
| `values-bluegreen.yaml` | Blue-green release values |

The `deployment.yaml` body is wrapped in `{{- if not .Values.rollout.enabled }}`
so the chart renders either a Deployment or a Rollout, never both. The
existing Service is reused unchanged; the Argo Rollouts controller
manages its `.spec.selector` to route traffic between stable and
canary/preview ReplicaSets.

The `rollout` block in `values.yaml`:

```yaml
rollout:
  enabled: false
  strategy: canary       # canary | blueGreen
  canary:
    steps:
      - setWeight: 20
      - pause: {}
      - setWeight: 40
      - pause: { duration: 30s }
      - setWeight: 60
      - pause: { duration: 30s }
      - setWeight: 80
      - pause: { duration: 30s }
      - setWeight: 100
  blueGreen:
    autoPromotionEnabled: false
    autoPromotionSeconds: 0
    scaleDownDelaySeconds: 30
```

---

## 4. Canary Deployment

### Strategy

Traffic shifts in five weighted steps. The first step pauses for manual
review; subsequent steps auto-advance after a 30-second soak.

| Step | Weight | Pause |
|------|--------|-------|
| 1 | 20% | manual |
| 2 | 40% | 30s |
| 3 | 60% | 30s |
| 4 | 80% | 30s |
| 5 | 100% | — |

With `replicaCount: 4` (set in `values-canary.yaml`), each 20% step maps
to one whole pod, so weights match the pod fleet exactly.

### Install

```bash
kubectl create namespace rollouts-demo
helm install app-python-canary k8s/app-python \
  -f k8s/app-python/values-canary.yaml \
  -n rollouts-demo --no-hooks
```

### Update Flow

1. Trigger an update (image change, env-var change, etc.):

   ```bash
   kubectl argo rollouts set image app-python-canary-app-python \
     -n rollouts-demo app-python=4hellboy4/devops-info-service:<new-tag>
   ```

2. The rollout pauses at step 1 (`SetWeight: 20`). Verify health with
   `kubectl argo rollouts get rollout` or in the dashboard.

3. Promote past the manual gate:

   ```bash
   kubectl argo rollouts promote app-python-canary-app-python -n rollouts-demo
   ```

4. Subsequent steps progress automatically; final state is `Healthy` at
   `Step 9/9, SetWeight: 100`.

### Abort and Rollback

While the rollout is in progress (typically while paused), abort:

```bash
kubectl argo rollouts abort app-python-canary-app-python -n rollouts-demo
```

The canary ReplicaSet scales to zero and the stable ReplicaSet retains
100% of traffic. To re-attempt the same revision, use
`kubectl argo rollouts retry rollout`.

---

## 5. Blue-Green Deployment

### Strategy

Two complete ReplicaSets coexist during a rollout — `active` (current
production) and `preview` (new version). Promotion swaps the active
service selector to the preview ReplicaSet in a single API call.

| Service | Role | Type |
|---------|------|------|
| `<release>-app-python` | Active — production traffic | NodePort |
| `<release>-app-python-preview` | Preview — new version under test | ClusterIP |

`autoPromotionEnabled: false` keeps promotion manual.
`scaleDownDelaySeconds: 30` keeps the previous ReplicaSet warm after
promote, enabling instant rollback.

### Install

```bash
kubectl create namespace bluegreen-demo
helm install app-python-bg k8s/app-python \
  -f k8s/app-python/values-bluegreen.yaml \
  -n bluegreen-demo --no-hooks
```

### Update Flow

1. Trigger an update. The rollouts controller owns the Service
   `.spec.selector`, so a plain `helm upgrade` produces a
   field-manager conflict on both Services. Update the Rollout
   directly:

   ```bash
   kubectl argo rollouts set image app-python-bg-app-python \
     -n bluegreen-demo app-python=4hellboy4/devops-info-service:<new-tag>
   ```

2. The controller spawns a new ReplicaSet labelled `preview`; the
   active ReplicaSet keeps `stable,active`. Status reads
   `active service cutover pending`.

3. Validate the new version against the preview service:

   ```bash
   kubectl port-forward -n bluegreen-demo \
     svc/app-python-bg-app-python-preview 8081:80
   ```

4. Promote — the active service selector flips to the new ReplicaSet
   atomically:

   ```bash
   kubectl argo rollouts promote app-python-bg-app-python -n bluegreen-demo
   ```

### Instant Rollback

```bash
kubectl argo rollouts undo app-python-bg-app-python -n bluegreen-demo
```

Within `scaleDownDelaySeconds`, the previous ReplicaSet is still warm,
so the rollback is a single selector flip with no cold-start cost.

---

## 6. Strategy Comparison

| Aspect | Canary | Blue-Green |
|--------|--------|------------|
| Traffic split | Gradual percentage | All-or-nothing |
| Validation | Real users at low weight | Synthetic tests on preview service |
| Failure blast radius | Bounded by current weight | Zero pre-promote, full post-promote |
| Resource cost during rollout | ~1.0× — extra canary pods only | ~2.0× — full second fleet |
| Rollback speed | Fast — scale canary to zero | Instant — selector flip |
| Best for | User-facing services with measurable SLOs | Releases that can't tolerate traffic mixing (schema-coupled APIs, stateful clients, coordinated client deploys) |
| Worst for | Backward-incompatible releases | Tight resource budgets |

**Recommendation for this project.** Canary is the default for
day-to-day app updates: the four-replica fleet maps cleanly to
20/40/60/80/100% pod weights and the manual gate at 20% gives a
real-user smoke test before committing further traffic. Blue-green is
the right strategy for releases that change the wire protocol or that
must coordinate with a client deploy, where mixed-version traffic would
corrupt user-visible state.

---

## 7. CLI Reference

### Inspection

```bash
kubectl argo rollouts get rollout <name> -n <ns>
kubectl argo rollouts get rollout <name> -n <ns> -w
kubectl argo rollouts list rollouts -n <ns>
kubectl argo rollouts status <name> -n <ns> [--watch]
```

### Triggering Updates

```bash
kubectl argo rollouts set image <name> -n <ns> <container>=<image>:<tag>
```

### Flow Control

```bash
kubectl argo rollouts promote <name> -n <ns>
kubectl argo rollouts promote <name> --full -n <ns>
kubectl argo rollouts abort <name> -n <ns>
kubectl argo rollouts retry rollout <name> -n <ns>
kubectl argo rollouts undo <name> -n <ns>
kubectl argo rollouts restart <name> -n <ns>
kubectl argo rollouts pause <name> -n <ns>
kubectl argo rollouts resume <name> -n <ns>
```

### Dashboard

```bash
kubectl port-forward svc/argo-rollouts-dashboard -n argo-rollouts 3100:3100
```

---

## 8. Troubleshooting

### Controller stuck on "waiting for rollout spec update to be observed"

The controller occasionally misses a spec event (most common after a
control-plane restart). Restart the controller pod:

```bash
kubectl rollout restart deployment/argo-rollouts -n argo-rollouts
kubectl rollout status  deployment/argo-rollouts -n argo-rollouts
```

### `helm upgrade` fails with Service selector conflict

The rollouts controller owns `.spec.selector` on the active and preview
services; `helm upgrade` cannot reclaim those fields. Update the
Rollout directly instead of going through Helm:

```bash
kubectl argo rollouts set image <rollout> -n <ns> <container>=<image>:<tag>
```

Or patch the Rollout pod template:

```bash
kubectl patch rollout <name> -n <ns> --type=json \
  -p='[{"op":"replace","path":"/spec/template/spec/containers/0/env/2/value","value":"<v>"}]'
```

### Switching strategies on an existing release

`canary` ↔ `blueGreen` cannot be hot-swapped on a running Rollout
(the strategy field is mutable but the controller will not migrate
selectors cleanly). Uninstall and reinstall with the target values
file:

```bash
helm uninstall <release> -n <ns>
helm install <release> k8s/app-python -f <values-file>.yaml -n <ns>
```
