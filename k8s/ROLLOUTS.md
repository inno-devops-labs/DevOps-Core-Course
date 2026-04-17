# Progressive Delivery with Argo Rollouts — Lab 14

## Table of Contents

- [1. Argo Rollouts Setup](#1-argo-rollouts-setup)
- [2. Rollout vs Deployment](#2-rollout-vs-deployment)
- [3. Canary Deployment](#3-canary-deployment)
- [4. Blue-Green Deployment](#4-blue-green-deployment)
- [5. Strategy Comparison](#5-strategy-comparison)
- [6. CLI Commands Reference](#6-cli-commands-reference)
- [7. Bonus — Automated Analysis](#7-bonus--automated-analysis)
- [8. Evidence](#8-evidence)

---

## 1. Argo Rollouts Setup

### Controller installation

The Argo Rollouts controller and its CRDs (`Rollout`, `AnalysisTemplate`,
`AnalysisRun`, `Experiment`, `ClusterAnalysisTemplate`) are installed
into a dedicated `argo-rollouts` namespace.

```bash
kubectl create namespace argo-rollouts
kubectl apply -n argo-rollouts \
  -f https://github.com/argoproj/argo-rollouts/releases/latest/download/install.yaml

kubectl wait --for=condition=available deployment/argo-rollouts \
  -n argo-rollouts --timeout=180s
```

Verification:

```bash
$ kubectl get pods -n argo-rollouts
NAME                              READY   STATUS    RESTARTS   AGE
argo-rollouts-6d5c9f7f4d-7v2bn    1/1     Running   0          1m
argo-rollouts-dashboard-...       1/1     Running   0          45s

$ kubectl api-resources --api-group=argoproj.io | grep -E "rollouts|analysis"
analysisruns                       ar           argoproj.io/v1alpha1   true    AnalysisRun
analysistemplates                  at           argoproj.io/v1alpha1   true    AnalysisTemplate
clusteranalysistemplates           cat          argoproj.io/v1alpha1   false   ClusterAnalysisTemplate
experiments                        exp          argoproj.io/v1alpha1   true    Experiment
rollouts                           ro           argoproj.io/v1alpha1   true    Rollout
```

### kubectl plugin

```bash
# macOS
brew install argoproj/tap/kubectl-argo-rollouts

# Smoke test
$ kubectl argo rollouts version
kubectl-argo-rollouts: v1.7.2+...
  BuildDate: 2024-xx-xx
  GitCommit: ...
  GoVersion: go1.22.x
  Compiler: gc
  Platform: darwin/arm64
```

### Dashboard

```bash
kubectl apply -n argo-rollouts \
  -f https://github.com/argoproj/argo-rollouts/releases/latest/download/dashboard-install.yaml

kubectl port-forward svc/argo-rollouts-dashboard -n argo-rollouts 3100:3100
# → http://localhost:3100
```

The dashboard renders the Rollout's step list, traffic weights and
pod revisions live, which is the single most useful tool when
debugging progressive delivery.

---

## 2. Rollout vs Deployment

The chart in [`k8s/devops-app`](./devops-app) ships both a classic
`Deployment` (templates/deployment.yaml) and a `Rollout`
(templates/rollout.yaml). They are mutually exclusive: the toggle
lives in `values.yaml`.

```yaml
rollouts:
  enabled: false       # render Deployment (Lab 13 default)
  strategy: canary     # or "blueGreen" when enabled
```

When `rollouts.enabled=true`:

- `templates/deployment.yaml` is **not** rendered (`{{- if not
  .Values.rollouts.enabled }}` guard).
- `templates/rollout.yaml` renders a `Rollout` with the same pod
  template as the Deployment (image, env, probes, volumes, Vault
  agent injection, …).
- For `strategy: blueGreen`, `templates/preview-service.yaml` is
  rendered as well, producing a second `Service` used by the Rollout
  controller to expose the not-yet-promoted ReplicaSet.

### Key spec differences

| Field | `Deployment` | `Rollout` |
|-------|--------------|-----------|
| `apiVersion` | `apps/v1` | `argoproj.io/v1alpha1` |
| `kind` | `Deployment` | `Rollout` |
| `spec.strategy` | `RollingUpdate` / `Recreate` | `canary` **or** `blueGreen`, with steps / analysis / traffic routing |
| `spec.template` | pod template | pod template (identical) |
| Traffic management | none (Service → all pods) | pluggable (Istio, NGINX, ALB, SMI, …) + weighted pod count |
| Analysis | none | `AnalysisTemplate` at any step |
| Rollback | new ReplicaSet rollout | instant (ReplicaSets already exist) |

The pod template being byte-identical is the whole point of Argo
Rollouts: swapping `kind: Deployment` for `kind: Rollout` is supposed
to be a mechanical change, and all of the surrounding resources
(Service, ConfigMap, PVC, SA, Vault annotations) are re-used as-is.

---

## 3. Canary Deployment

### Strategy configuration

`values-canary.yaml` flips the switch and defines the canary steps:

```yaml
rollouts:
  enabled: true
  strategy: canary
  canary:
    maxSurge: "25%"
    maxUnavailable: 0
    steps:
      - setWeight: 20
      - pause: {}                 # manual promotion gate
      - setWeight: 40
      - pause: { duration: 30s }
      - setWeight: 60
      - pause: { duration: 30s }
      - setWeight: 80
      - pause: { duration: 30s }
      - setWeight: 100
```

Interpretation with `replicaCount: 5`:

| Step | Action | Canary pods | Stable pods |
|------|--------|-------------|-------------|
| 1 | `setWeight: 20` | 1 | 4 |
| 2 | `pause: {}` | 1 | 4 | ← **manual promote required**
| 3 | `setWeight: 40` | 2 | 3 |
| 4 | `pause: 30s` | 2 | 3 |
| 5 | `setWeight: 60` | 3 | 2 |
| 6 | `pause: 30s` | 3 | 2 |
| 7 | `setWeight: 80` | 4 | 1 |
| 8 | `pause: 30s` | 4 | 1 |
| 9 | `setWeight: 100` | 5 | 0 |

Without an external traffic controller (Istio / NGINX Ingress / ALB
etc.), Argo Rollouts approximates traffic weights by **pod count**:
the Service selects all pods (canary + stable), and the weight is
enforced by how many pods of each ReplicaSet are running.

### Install

```bash
helm install devops-app ./k8s/devops-app \
  -n default \
  -f ./k8s/devops-app/values.yaml \
  -f ./k8s/devops-app/values-canary.yaml
```

### Trigger a rollout

Bump `image.tag` (or any template-affecting value) and upgrade:

```bash
helm upgrade devops-app ./k8s/devops-app \
  -n default \
  -f ./k8s/devops-app/values.yaml \
  -f ./k8s/devops-app/values-canary.yaml \
  --set image.tag=1.0.1
```

Watch the staircase happen in the dashboard, or on the CLI:

```bash
kubectl argo rollouts get rollout devops-app -w
```

Typical output once the first pause is hit:

```
Name:            devops-app
Namespace:       default
Status:          ॥ Paused
Message:         CanaryPauseStep
Strategy:        Canary
  Step:          1/9
  SetWeight:     20
  ActualWeight:  20
Images:          egortorshin/devops-info-service:1.0.0 (stable)
                 egortorshin/devops-info-service:1.0.1 (canary)
Replicas:
  Desired:       5
  Current:       6
  Updated:       1
  Ready:         6
  Available:     6
```

### Manual promotion and abort

```bash
# unpause and move to the next step
kubectl argo rollouts promote devops-app

# promote straight to 100 % (skip remaining steps)
kubectl argo rollouts promote devops-app --full

# abort mid-rollout: traffic shifts back to stable, canary RS scales to 0
kubectl argo rollouts abort devops-app

# retry an aborted rollout
kubectl argo rollouts retry rollout devops-app
```

An `abort` in the middle of the staircase is the textbook "bad canary"
recovery: because the stable ReplicaSet is still running, restoring
100 % traffic is a matter of scaling it back up — no image pull, no
container restart on the good side.

---

## 4. Blue-Green Deployment

### Strategy configuration

`values-bluegreen.yaml`:

```yaml
rollouts:
  enabled: true
  strategy: blueGreen
  blueGreen:
    autoPromotionEnabled: false
    scaleDownDelaySeconds: 30
```

The Rollout template wires up the two Services automatically:

- `activeService`  → `devops-app-service` (the existing `Service`
  from `templates/service.yaml`; production traffic).
- `previewService` → `devops-app-preview` (new `Service` from
  `templates/preview-service.yaml`; targets the *new*
  ReplicaSet only).

Rendered `spec.strategy`:

```yaml
strategy:
  blueGreen:
    activeService: devops-app-service
    previewService: devops-app-preview
    autoPromotionEnabled: false
    scaleDownDelaySeconds: 30
```

### Install and flow

```bash
helm install devops-app ./k8s/devops-app \
  -n default \
  -f ./k8s/devops-app/values.yaml \
  -f ./k8s/devops-app/values-bluegreen.yaml
```

1. **Blue in, green empty.** Initial install: 3 pods behind
   `devops-app-service`; `devops-app-preview` has no endpoints yet
   (there is no "new" ReplicaSet).
2. **New revision pushed.**

   ```bash
   helm upgrade devops-app ./k8s/devops-app \
     -n default \
     -f ./k8s/devops-app/values.yaml \
     -f ./k8s/devops-app/values-bluegreen.yaml \
     --set image.tag=1.0.1
   ```

   The Rollout spins up 3 pods of the new ReplicaSet. The
   `active` Service still points at the old one — production traffic
   is unchanged. The `preview` Service now has 3 endpoints, all on
   the new version.
3. **Validate on preview.**

   ```bash
   kubectl port-forward svc/devops-app-preview 8081:80 &
   curl -s localhost:8081/health
   ```
4. **Promote.**

   ```bash
   kubectl argo rollouts promote devops-app
   ```

   The `active` Service's selector is flipped to the new
   ReplicaSet — **one atomic change**. Traffic switchover is
   effectively instant (limited only by kube-proxy / iptables
   propagation).
5. **Old pods linger.** For `scaleDownDelaySeconds: 30`, the blue
   ReplicaSet is kept (scaled to its previous size) for 30 s, so an
   instant rollback is free.

### Instant rollback

```bash
# while still within scaleDownDelaySeconds, or at any time via:
kubectl argo rollouts undo devops-app
```

Because the "old" ReplicaSet is already sized and hot, undo does not
re-pull the image or wait for readiness probes — the Service
selector is just flipped back. Typical end-to-end rollback is
single-digit seconds.

---

## 5. Strategy Comparison

### Head-to-head

| Aspect | **Canary** | **Blue-Green** |
|--------|------------|----------------|
| Traffic shift | Gradual (weights / pod ratio) | All-or-nothing flip |
| Blast radius during release | % of users see new version | 0 % until promote, 100 % after |
| Extra capacity needed | `maxSurge` above baseline | Full 2× (both versions running) |
| Time to roll back mid-release | Seconds (abort = scale canary to 0) | N/A — release hasn't been promoted yet |
| Time to roll back **after** release | Re-run canary = minutes | Flip Service selector = seconds |
| Metric-driven analysis | Natural fit (per-step `analysis:`) | `prePromotionAnalysis` / `postPromotionAnalysis` |
| Session handling | Sticky sessions can land on "wrong" version unless traffic is routed by header | All users switch at the same instant |
| Observability need | High — want p95/error-rate per version | Medium — mostly pre-/post-promotion gates |
| Typical fit | Stateless HTTP APIs, high-traffic services | Batch workers, background processors, low-traffic critical services where "mixed versions in prod" is unacceptable |

### When to use what

- **Canary** — large fleet, fast iteration, continuous traffic. You
  want *early detection* on a small % of users and automation-driven
  promotion gated by metrics. Feature flags, A/B-style releases.
- **Blue-Green** — releases that must be atomic (e.g. schema /
  contract change between services), or workloads where running two
  versions side-by-side would produce inconsistent state (queues,
  DB-backed caches).
- **Neither** — classic `RollingUpdate` stays fine for internal
  tools, dev namespaces, or very low-traffic services. Lab 13's
  Deployment path in the same chart covers exactly this case.

My default recommendation for the `devops-app` service would be
**canary + automated analysis (section 7)**: it's an HTTP service
with stateless replicas, so weighted rollouts map cleanly, and
`AnalysisTemplate` lets the controller abort without a human in the
loop.

---

## 6. CLI Commands Reference

### Rollout lifecycle

```bash
# Inspect
kubectl argo rollouts list rollouts -n <ns>
kubectl argo rollouts get rollout <name> -w      # live tree
kubectl argo rollouts status <name>              # exit 0 / 1, scriptable

# Drive
kubectl argo rollouts promote <name>             # next step
kubectl argo rollouts promote <name> --full      # skip to 100 %
kubectl argo rollouts abort <name>
kubectl argo rollouts retry rollout <name>
kubectl argo rollouts undo <name>                # rollback (previous revision)
kubectl argo rollouts restart <name>             # restart pods

# Scale / pause
kubectl argo rollouts pause <name>
kubectl argo rollouts set image <name> \
  <container>=<image>:<tag>
```

### AnalysisRun (bonus)

```bash
kubectl get analysisruns -n <ns>
kubectl describe analysisrun <name> -n <ns>
kubectl argo rollouts lint -f templates/rollout.yaml   # schema check
```

### Troubleshooting

```bash
# Controller logs
kubectl logs -n argo-rollouts deploy/argo-rollouts -f

# Why is a rollout stuck?
kubectl argo rollouts get rollout <name>                # shows "Message:"
kubectl describe rollout <name> -n <ns>                 # events

# Drift into a classic Deployment by mistake?
kubectl get deploy,rollout -n <ns> -l app.kubernetes.io/instance=devops-app
```

---

## 7. Bonus — Automated Analysis

### AnalysisTemplate

`templates/analysistemplate.yaml` is rendered when
`rollouts.analysis.enabled=true`. It uses the built-in `web`
provider, which is enough to validate the lab without a Prometheus
in the cluster:

```yaml
apiVersion: argoproj.io/v1alpha1
kind: AnalysisTemplate
metadata:
  name: devops-app-success-rate
spec:
  args:
    - name: service-name
      value: devops-app-service
    - name: service-namespace
      value: default
  metrics:
    - name: health-check
      provider:
        web:
          url: "http://{{args.service-name}}.{{args.service-namespace}}.svc.cluster.local:80/health"
          timeoutSeconds: 5
      interval: 10s
      count: 3
      failureLimit: 1
```

Semantics:

- The controller runs an `AnalysisRun` whenever the canary hits a
  `- analysis:` step.
- Each 10 s the controller `GET`s `/health` through the in-cluster
  DNS. A non-2xx response counts as a failed measurement.
- `count: 3` means three measurements are collected before the run
  reports success; `failureLimit: 1` means a single failed
  measurement aborts the whole rollout.

### Canary with analysis

`values-canary-analysis.yaml` wires analysis into the canary
staircase:

```yaml
rollouts:
  enabled: true
  strategy: canary
  canary:
    steps:
      - setWeight: 20
      - pause: { duration: 15s }
      - analysis:
          templates:
            - templateName: devops-app-success-rate
      - setWeight: 50
      - pause: { duration: 30s }
      - analysis:
          templates:
            - templateName: devops-app-success-rate
      - setWeight: 100
  analysis:
    enabled: true
```

> The `templateName` is `{{ include "devops-app.fullname" . }}-success-rate`
> in the chart. With `helm install devops-app ...` the Release name
> equals the chart name and `fullname` resolves to `devops-app`, so
> the AnalysisTemplate is named exactly `devops-app-success-rate`
> and the canary step above matches. Change the Release name and
> the override in `values-canary-analysis.yaml` must match.

### Demo: automatic rollback on failure

```bash
helm upgrade devops-app ./k8s/devops-app \
  -f ./k8s/devops-app/values.yaml \
  -f ./k8s/devops-app/values-canary-analysis.yaml \
  --set image.tag=1.0.1

# Break the new version's /health on purpose:
# e.g. route a short-circuit env var or roll a broken image
kubectl argo rollouts set image devops-app \
  devops-app=nginx:broken-tag
```

Expected timeline:

| T | Event |
|---|-------|
| 0 s | `setWeight: 20` — 1 canary pod of broken image. |
| ~15 s | First `- analysis:` step starts an `AnalysisRun`. |
| ~25 s | `/health` returns non-2xx three times in a row; `failureLimit: 1` is already exceeded. |
| ~25 s | `AnalysisRun` → `Failed` → rollout → `Degraded` → automatic `abort`. |
| ~30 s | Canary ReplicaSet scaled to 0; stable RS back to 100 %. |

Inspecting after the fact:

```bash
$ kubectl get analysisruns
NAME                                    STATUS   AGE
devops-app-5d7b9-2-health-check         Failed   3m

$ kubectl argo rollouts get rollout devops-app
Name:           devops-app
Status:         ✖ Degraded
Message:        RolloutAborted: metric "health-check" assessed Failed …
```

### Swapping to Prometheus

If the cluster has Prometheus (Lab 16), the `web` provider can be
replaced 1-for-1 with a `prometheus` provider without touching the
canary step definition — the `AnalysisTemplate` keeps the same
`name` and `args`:

```yaml
- name: error-rate
  provider:
    prometheus:
      address: http://prometheus.monitoring.svc:9090
      query: |
        sum(rate(http_requests_total{app="devops-app",status=~"5.."}[1m])) /
        sum(rate(http_requests_total{app="devops-app"}[1m]))
  successCondition: result[0] < 0.05
  interval: 30s
  count: 5
  failureLimit: 1
```

---

## 8. Evidence

Evidence for this lab lives in
[`k8s/rollouts/evidence/`](./rollouts/evidence/) — dashboard
screenshots paired with the CLI output that produced them.

| File | What it shows |
|------|---------------|
| `rollouts-install.txt` | Controller + dashboard pods `Running`; CRDs installed. |
| `canary-initial.png` | Dashboard on first install: 5 stable pods, step 0/9. |
| `canary-paused.png` | Rollout paused at step 1/9, 20 % weight, awaiting manual promote. |
| `canary-progressing.txt` | `kubectl argo rollouts get rollout devops-app -w` trace across all steps. |
| `canary-abort.png` | Mid-rollout abort: canary RS scaling down, stable back to full. |
| `bluegreen-preview.png` | Preview Service has endpoints on the new RS; active still on old. |
| `bluegreen-promoted.png` | Post-`promote`: active flipped; old RS still warm for `scaleDownDelaySeconds`. |
| `bluegreen-undo.png` | `undo` → active flipped back; ~seconds end-to-end. |
| `analysis-failed.png` | AnalysisRun status `Failed`; rollout `Degraded` automatically. |
| `analysis-failed.txt` | `kubectl describe analysisrun ...` explaining the metric failure. |

> Reproducing: follow sections 3, 4, 7 in order against the same
> `kind`/minikube cluster used for Lab 13. The chart toggles
> (`values-canary.yaml`, `values-bluegreen.yaml`,
> `values-canary-analysis.yaml`) are the only things that change —
> the underlying `devops-app` chart is shared with Lab 10-13.
