# ArgoCD — Lab 13 (GitOps)

Documentation for ArgoCD installation, Application manifests, and self-healing tests for the `k8s/app-python` Helm chart. Step-by-step commands: [labs/lab13.md](../labs/lab13.md).

---

## 1. ArgoCD setup

**Post-installation checks (Helm)**

- `argocd` namespace created; release (e.g. `argocd`) installed from the `argo/argo-cd` chart.
- All pods **Ready**, including with label `app.kubernetes.io/name=argocd-server` (see the lab for `kubectl wait`).

**UI access**

- Port-forward to `argocd-server` in `argocd` (HTTPS to a local port, e.g. 8080).
- Login: user `admin`, password from secret `argocd-initial-admin-secret`.

**CLI**

- `argocd` binary installed; `argocd login` to the same host/port (use `insecure` for self-signed certs, per the lab).
- Check: `argocd version`, `argocd app list`.

---

## 2. Application configuration

Manifests live in [k8s/argocd/](argocd/).

| File | Application | Values | Destination namespace | Sync |
|------|-------------|--------|-------------------------|------|
| [application.yaml](argocd/application.yaml) | `python-app` | `values.yaml` | `default` | Manual (no `automated` block) |
| [application-dev.yaml](argocd/application-dev.yaml) | `python-app-dev` | `values-dev.yaml` | `dev` | Auto: `prune`, `selfHeal` |
| [application-prod.yaml](argocd/application-prod.yaml) | `python-app-prod` | `values-prod.yaml` | `prod` | Manual |

**Source (shared)**

- `repoURL`: `https://github.com/4hellboy4/DevOps-Core-Course.git` (should match `git remote get-url origin`).
- `targetRevision`: branch on GitHub with the chart and `k8s/argocd` (in manifests: `lab13` — the branch must be **pushed**: `git push -u origin lab13`).
- `path`: `k8s/app-python` — Helm chart root in the repo.
- `helm.valueFiles`: files **relative to** the chart directory (`values.yaml`, `values-dev.yaml`, `values-prod.yaml`).

**Destination**

- `destination.server`: `https://kubernetes.default.svc` — in-cluster API.
- `syncOptions: CreateNamespace=true` — ArgoCD creates the destination namespace on first sync if missing (usually `default` already exists).

Apply: `kubectl apply -f k8s/argocd/<manifest>.yaml`. First sync for applications without auto-sync: UI or `argocd app sync <name>`.

**Chart change → Git → ArgoCD (Task 2, Git workflow):** edit `k8s/app-python/` (e.g. `replicaCount` or `image.tag`), `git add` / `commit` / `push` to the `targetRevision` branch, then **Refresh** in the Argo UI (or wait ~3 min), then **OutOfSync** and **Sync** (manual for `python-app` / `python-app-prod`; for `python-app-dev` with `automated` policy it may sync on its own).

---

## 3. Multi-environment

| | Dev (`python-app-dev`) | Prod (`python-app-prod`) |
|---|------------------------|---------------------------|
| Kubernetes namespace | `dev` | `prod` |
| Values | [values-dev.yaml](app-python/values-dev.yaml) | [values-prod.yaml](app-python/values-prod.yaml) |
| Replicas | `2` (persistence off; see comment in values) | `1` (persistence merged from base [values.yaml](app-python/values.yaml)) |
| Resources | Smaller requests/limits | Higher limits than dev |
| Service | NodePort `30084` (values-dev) | NodePort `30081` |
| ArgoCD sync | Automated with `prune` and `selfHeal` | Manual only |

**Why prod stays manual**

- Change review and approval before rollout.
- Control when the release goes live (maintenance windows, monitoring).
- Compliance/audit: cluster changes should follow an explicit action after review in Git.

Create `dev` and `prod` in advance (`kubectl create namespace dev|prod`) or rely on `CreateNamespace=true`.

---

## 4. Self-healing evidence

For chart `app-python`, full resource name pattern is `{Release.Name}-{Chart.Name}`. In ArgoCD, the default Helm **release** name matches the **Application** name.

| Application | Example Deployment name |
|-------------|----------------------------|
| `python-app` | `python-app-app-python` |
| `python-app-dev` | `python-app-dev-app-python` |
| `python-app-prod` | `python-app-prod-app-python` |

Pod selectors (see [templates/_helpers.tpl](app-python/templates/_helpers.tpl)):

- `app.kubernetes.io/name=app-python` (chart name, not `python-app`).
- `app.kubernetes.io/instance=<Application name>` (e.g. `python-app-dev`).

Below: **run log** (minikube, `4hellboy4` repo, `python-app-dev` in `dev`). Times in **MSK**; **UTC** in parentheses (MSK = UTC+3).

### 4.1 Manual scale (dev, revert to Git)

| Step | Time | Command / observation |
|------|------|-------------------------|
| Before | — | [values-dev.yaml](app-python/values-dev.yaml): `replicaCount: 2` → `kubectl get deploy` **2/2**; `argocd app get` — **Synced**, **Healthy**. |
| Manual scale | — | `kubectl scale deployment python-app-dev-app-python -n dev --replicas=5` → **5/5**; in Argo **OutOfSync** (cluster ≠ Git). |
| Sync to desired | 2026-04-23 **21:57:29** MSK (**18:57** UTC) | `argocd app sync python-app-dev` — op **Succeeded** (~21s, “successfully synced”). |
| After | 2026-04-23 **~21:58** MSK | `kubectl get deploy` → **2/2**; `argocd app get` — **Synced to lab13** (0c9148a), **Healthy**. |

### 4.2 Pod delete (Kubernetes behaviour)

| Step | Time | Observation |
|------|------|-------------|
| Delete | — | `kubectl delete pod -n dev -l app.kubernetes.io/instance=python-app-dev` — two app pods removed. |
| After | — | ReplicaSet/Deployment **created new** pods, desired **2**; that is the **controller-manager**, not an ArgoCD content sync. |

### 4.3 Manual label and `argocd app diff`

| Step | Time | Command / observation |
|------|------|-------------------------|
| Label | — | `kubectl label deploy python-app-dev-app-python -n dev argocd-test=1 --overwrite` |
| State | — | `kubectl get deploy --show-labels` — `argocd-test=1`; in some checks `argocd app get` still shows **Synced/Healthy** for the Deployment. |
| `argocd app diff` | — | **Empty** — Argo/Helm often **do not** surface ad-hoc `metadata.labels` in CLI diff and **do not** clear the label via self-heal, unlike **replica change (§4.1)**. |
| Clean-up (optional) | — | `kubectl label deploy python-app-dev-app-python -n dev argocd-test-` |

**Takeaway:** self-heal for **replicas (§4.1)** is enforced by `sync`; **pod (§4.2)** is Kubernetes; **label (§4.3)** documents actual **diff/label** behaviour.

---

## 5. When ArgoCD syncs vs when Kubernetes “heals”

**ArgoCD sync**

- Git polling (default about **3 minutes**; exact value depends on `timeout.reconciliation` and controller config).
- Immediately on manual **Sync** in the UI or CLI.
- A **webhook** can trigger sync without waiting for the poll.

**Kubernetes self-healing (without ArgoCD)**

- Deployment/ReplicaSet keeps the desired number of pods; if a pod is deleted or fails, a new pod is created with the same spec until the Deployment is changed.

**ArgoCD self-heal (with `selfHeal` on)**

- The live object is driven toward what is computed from Git (including fields changed with `kubectl patch/edit`), within the sync policy.

Summary: **pod delete** shows replica recovery on the **Kubernetes** side; **scale** and manifest drift show **reconciliation toward Git** on the **ArgoCD** side (for dev with auto-sync and self-heal).

---

## 6. Screenshots (ArgoCD UI)

Images are in the `k8s/` directory next to this file. Inline preview below (app list, status, details per lab requirements).

1. **App list / overview** (2026-04-23, 19:57 MSK)

![ArgoCD — application list](./Screenshot%202026-04-23%20at%2019.57.44.png)

2. **Status / details** (2026-04-23, 21:48 MSK)

![ArgoCD — apps, sync, health, resource tree](./Screenshot%202026-04-23%20at%2021.48.21.png)

For submission outside the repo, copy the same PNGs into a separate PDF or document if the course requires it.
