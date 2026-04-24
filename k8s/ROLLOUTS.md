# Lab 14 — Argo Rollouts (progressive delivery)

The `k8s/devops-python` Helm chart deploys the app with an Argo **Rollout** instead of a `Deployment`. The chart supports **canary** (default) and **blue-green** strategies.

## Prerequisites

- Kubernetes cluster
- [Argo Rollouts](https://argoproj.github.io/argo-rollouts/) installed in the cluster
- (Recommended) [kubectl argo rollouts](https://argoproj.github.io/argo-rollouts/installation/#kubectl-plugin-installation) plugin

## 1. Install the Rollouts controller and dashboard (Task 1)

```bash
chmod +x k8s/rollouts/install-argo-rollouts.sh
./k8s/rollouts/install-argo-rollouts.sh
```

Or use the [upstream manifests](https://argoproj.github.io/argo-rollouts/installation/) directly.

**Verify:**

```bash
kubectl get pods -n argo-rollouts
kubectl argo rollouts version   # with plugin installed
```

**Dashboard (Task 1):** after the script (or `kubectl apply` of `dashboard-install.yaml`):

```bash
kubectl port-forward svc/argo-rollouts-dashboard -n argo-rollouts 3100:3100
```

Open **http://localhost:3100** and open your namespace / Rollout from the UI.

**Rollout vs Deployment:** a **Rollout** is API-compatible in `spec.template` and `spec.selector` with a Deployment, but `spec.strategy` is replaced with **canary** or **blueGreen** options that support traffic weights, pauses, analysis, and (with ingress/service mesh) fine-grained routing.

## 2. Install the app (Helm)

**Canary (default `values.yaml`):**

```bash
helm upgrade --install myapp ./k8s/devops-python -n <namespace> --create-namespace
```

**Blue-green:**

```bash
helm upgrade --install myapp ./k8s/devops-python -n <namespace> -f k8s/devops-python/values-bluegreen.yaml
```

The main Service (unchanged) is the **active** production Service. When using blue-green, a second **preview** Service is created: `<release>-devops-python-preview` (e.g. for smoke tests on the new stack before `promote`).

## 3. Canary strategy (Task 2)

Configured in `templates/rollout.yaml` and `values.yaml` (`rollout.strategy: canary`).

**Steps (lab spec):**

| Step | Action |
|------|--------|
| 1 | `setWeight: 20` |
| 2 | Optional **analysis** (see bonus) if `rollout.analysis.enabled: true` |
| 3 | `pause: {}` — **manual** promotion (`kubectl argo rollouts promote ...`) |
| 4 | `setWeight: 40` → `pause: 30s` |
| 5 | `setWeight: 60` → `pause: 30s` |
| 6 | `setWeight: 80` → `pause: 30s` |
| 7 | `setWeight: 100` |

**CLI:**

```bash
kubectl argo rollouts get rollout <rollout-name> -n <namespace> -w
kubectl argo rollouts promote <rollout-name> -n <namespace>
kubectl argo rollouts abort <rollout-name> -n <namespace>
kubectl argo rollouts retry rollout <rollout-name> -n <namespace>
```

Trigger an upgrade (e.g. `helm upgrade ... --set image.tag=newtag`), then use the **dashboard** or `kubectl` to watch ReplicaSet weights and follow pauses.

**Replicas:** canary `setWeight` is a **percentage of desired pods** going to the new version. For meaningful steps, use **at least 2** replicas in the target environment (see `values-dev.yaml`).

**Note:** without a service mesh or ingress integration, “traffic split” is approximated by **replica count** of stable vs canary; for exact HTTP splits you would add a traffic router (NGINX, Istio, etc.) per the [Argo Rollouts traffic management](https://argoproj.github.io/argo-rollouts/features/traffic-management/) docs.

**Rollback / abort:** `abort` stops the canary; stable ReplicaSet should serve again while you fix Git/Helm.

## 4. Blue-green (Task 3)

Use `-f k8s/devops-python/values-bluegreen.yaml` or set in your own values file:

- `rollout.strategy: blueGreen`
- `rollout.blueGreen.activeService` / `previewService` are implied in the template as `<fullname>` and `<fullname>-preview` (the chart wires them to the two Services)
- `autoPromotionEnabled: false` for **manual** promotion to production
- `service.previewNodePort: 30081` when `service.type: NodePort` (active uses `30080` by default)

**Flow (conceptual):**

1. Baseline runs as **active** (blue).
2. Change app version → Rollout brings up **green**; **preview** Service targets the new ReplicaSet.
3. Test: `kubectl port-forward svc/<name>-preview ...` and hit `/` or `/health`.
4. **Promote:** `kubectl argo rollouts promote <name> -n <namespace>` — active switches to green; optional delay before scale-down (`scaleDownDelaySeconds`).

**Blue-green vs canary (Task 4):**

| | Canary | Blue-green |
|---|--------|------------|
| Risk | Gradual; mixed version traffic at weights | All-or-nothing cutover when promoted |
| Resources | Often fewer extra pods (weighted mix) | Often **two** full stacks while preview exists |
| Best when | You want % rollout + pauses for metrics | You want full new stack tested behind preview Service |

**Practical pick:** canary for gradual, metric-gated release; blue-green for full UAT of the next stack before a single **promote** event.

## 5. Bonus — automated analysis (optional)

- Set `rollout.analysis.enabled: true` in values (with `rollout.strategy: canary`).

The chart renders an **AnalysisTemplate** (`templates/analysistemplate.yaml`) that performs a **web** check against `http://<service>.<namespace>.svc:<port>/health` and expects JSON `status` to equal `healthy` (see `app_python` `/health`).

**Canary** steps include an `analysis` step after `setWeight: 20` when analysis is enabled. If analysis fails, the Rollout can **abort** the promotion per controller settings.

**Prometheus**-based analysis is possible in larger setups (cluster Prometheus URL + PromQL in `AnalysisTemplate`); this repo uses the **web** provider for a minimal, dependency-free path.

## 6. Further reading

- [Rollout spec](https://argoproj.github.io/argo-rollouts/features/specification/)  
- [Canary](https://argoproj.github.io/argo-rollouts/features/canary/) / [Blue-Green](https://argoproj.github.io/argo-rollouts/features/bluegreen/)  
- [Analysis & progressive delivery](https://argoproj.github.io/argo-rollouts/features/analysis/)  

## 7. Screenshot / evidence checklist (for your report)

- Argo Rollouts **dashboard** showing a Rollout and its steps  
- `kubectl argo rollouts get rollout ...` / `get pods` during a canary  
- (Blue-green) port-forward to **active** vs **preview** and note versions  
- (Bonus) `AnalysisRun` success/failure in the UI or `kubectl get analysisrun`  
