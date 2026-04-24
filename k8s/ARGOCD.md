# Lab 13 — Argo CD GitOps

This document describes how Argo CD deploys the **`k8s/devops-python`** Helm chart from Git, how dev/prod are separated, and how to verify self-healing. Replace placeholders in manifests before use.

## Prerequisites

- A Kubernetes cluster (e.g. kind, minikube) with `kubectl` and `helm` configured.
- A **Git remote** (GitHub or other) hosting this repository so Argo CD can pull the chart.
- The Argo CD **Application** resources live in the **`argocd`** namespace; workloads deploy to **`dev`**, **`prod`**, or **`default`** as configured.

## 1. Argo CD setup (Task 1)

### Install (Helm)

From the repository root:

```bash
chmod +x k8s/argocd/install-argocd.sh
./k8s/argocd/install-argocd.sh
```

Or manually (as in the lab):

```bash
helm repo add argo https://argoproj.github.io/argo-helm
helm repo update
kubectl create namespace argocd
helm install argocd argo/argo-cd --namespace argocd
kubectl wait --for=condition=ready pod -l app.kubernetes.io/name=argocd-server -n argocd --timeout=180s
```

**Verification:** `kubectl get pods -n argocd` should show all components Running / Completed.

### UI access

```bash
kubectl port-forward svc/argocd-server -n argocd 8080:443
```

Open **https://localhost:8080** (accept the self-signed certificate).  
User: **admin**. Initial password:

```bash
kubectl -n argocd get secret argocd-initial-admin-secret -o jsonpath='{.data.password}' | base64 -d
echo
```

### CLI

Install `argocd` per [Argo CD CLI installation](https://argo-cd.readthedocs.io/en/stable/cli_installation/), then:

```bash
argocd login localhost:8080 --insecure
argocd version
argocd app list
```

---

## 2. Configure Git source in manifests

In **`k8s/argocd/*.yaml`**, set:

| Field | Set to |
|--------|--------|
| `spec.source.repoURL` | Your repository HTTPS URL, e.g. `https://github.com/<you>/<repo>.git` |
| `spec.source.targetRevision` | Branch or tag, e.g. `main` or `lab13` |

Argo CD must be able to reach the Git server. For **private** repositories, create credentials in Argo CD (UI: **Settings → Repositories**, or a Secret with the proper labels) — see [private repos](https://argo-cd.readthedocs.io/en/stable/user-guide/private-repositories/).

---

## 3. Application manifests (Task 2)

| File | Purpose |
|------|---------|
| `k8s/argocd/application.yaml` | Single app, **`default`** namespace, `values.yaml`, **manual** sync (learning / Task 2) |
| `k8s/argocd/application-dev.yaml` | **`dev`** namespace, `values-dev.yaml`, **auto-sync** + **selfHeal** + **prune** |
| `k8s/argocd/application-prod.yaml` | **`prod`** namespace, `values-prod.yaml`, **manual** sync only |

**Helm chart path in Git:** `k8s/devops-python` (path is relative to the repository root).

Apply **either** the Task 2 base app **or** the dev/prod pair — do not duplicate the same environment with two different Application names.

**Example (dev + prod only):**

```bash
kubectl apply -f k8s/argocd/namespaces.yaml   # optional; CreateNamespace also works
kubectl apply -f k8s/argocd/application-dev.yaml
kubectl apply -f k8s/argocd/application-prod.yaml
```

**Sync dev** (or use the “Sync” button in the UI):

```bash
argocd app sync devops-python-dev
```

**Sync prod** (manual policy — required when you want to promote):

```bash
argocd app sync devops-python-prod
argocd app get devops-python-prod
```

**GitOps check:** change a value in the chart (e.g. `replicaCount` in `values-dev.yaml`), commit and push; after the Git poll interval, dev should **outofsync** and then **auto-sync** if automated policy is enabled.

**Default Argo CD Git poll interval** is on the order of **~3 minutes**; use **Refresh** in the UI, **`argocd app sync`**, or a [webhook](https://argo-cd.readthedocs.io/en/stable/operator-manual/webhook/) for faster feedback.

---

## 4. Multi-environment summary (Task 3)

| | **dev** (`devops-python-dev`) | **prod** (`devops-python-prod`) |
|---|------------------------------|----------------------------------|
| Namespace | `dev` | `prod` |
| Values | `values-dev.yaml` | `values-prod.yaml` |
| Replicas (defaults in repo) | 1 | 5 |
| Sync | Automated + prune + selfHeal | Manual only |

**Why manual prod?**  

Production changes are often gated by review, change windows, and rollback plans. **Manual sync** (or a pipeline that runs `argocd app sync` after approval) avoids every Git merge immediately changing live traffic.

---

## 5. Self-healing and drift (Task 4)

### 5.1 Self-heal (dev only)

With **selfHeal: true**, Argo CD reconciles the live cluster back to the **Git-declared** desired state (Helm output after `helm template`), not to ad-hoc `kubectl` edits.

**Example: manual scale (should be reverted on dev)**

```bash
# Names follow Helm fullname: <release>-devops-python
kubectl scale deployment -n dev -l "app.kubernetes.io/name=devops-python" --replicas=5
# Watch: replica count should return to the value from values-dev (e.g. 1) after the next sync/self-heal
kubectl get deploy -n dev -w
argocd app get devops-python-dev
```

Record **time before** the manual scale and **time after** the Deployment spec matches Git again. Exact timing depends on sync interval and controller latency.

**Difference from Kubernetes “self-healing”:**  

- The **Deployment / ReplicaSet** recreates **Pods** when a Pod is deleted (desired replicas unchanged).  
- **Argo CD** corrects **drift in resource specs** (e.g. replica count, labels) to match **Git** when selfHeal is on.

### 5.2 Pod deletion (Kubernetes behavior)

```bash
kubectl delete pod -n dev -l app.kubernetes.io/name=devops-python
kubectl get pods -n dev -w
```

New pods are created by the **ReplicaSet**; this does not require an Argo CD sync.

### 5.3 Configuration drift (label edit)

```bash
kubectl label deployment -n dev -l app.kubernetes.io/name=devops-python argo-test=manual --overwrite
argocd app diff devops-python-dev
```

With self-heal, the label may be removed when Argo CD reconciles. **Prod** without auto-sync stays out of sync until you run a **Sync** and choose whether to apply.

### 5.4 When does Argo CD sync?

- **Auto-sync (dev):** on detected Git changes (after poll) and periodic reconciliation, plus self-heal correcting drift.  
- **Manual (prod):** only when a user (or automation) runs sync / CI triggers `argocd app sync`.  
- **Kubernetes** keeps Pod count and restarts per **Controller** logic independent of Argo CD.

---

## 6. Optional screenshots (submission)

Place evidence under e.g. **`k8s/evidence/`** (your course’s convention) or attach to the lab report:

- Argo CD **Applications** list showing **dev** and **prod**.
- **Application details** for one app: sync status, health, revision.
- **Resource tree** or **Sync** result after a change.

*Example* `kubectl` output to capture:

```bash
kubectl get applications -n argocd
kubectl get pods -n dev
kubectl get pods -n prod
```

---

## 7. Bonus — ApplicationSet

`k8s/argocd/applicationset.yaml` uses a **List** generator and **goTemplate** to emit two **Applications** (`devops-python-dev` and `devops-python-prod`) with **automated** sync only for **dev**.

**Do not** apply this **and** `application-dev.yaml` / `application-prod.yaml` for the same names.

**Apply ApplicationSet only:**

```bash
kubectl apply -f k8s/argocd/applicationset.yaml
```

**Benefits:** one manifest for N environments, shared `repoURL` / `path`, parameters per list row. For more environments or clusters, consider **Matrix**, **Cluster**, or **Git** generators — see [ApplicationSet](https://argo-cd.readthedocs.io/en/stable/operator-manual/applicationset/).

---

## 8. References

- [Argo CD — Getting started](https://argo-cd.readthedocs.io/en/stable/getting_started/)  
- [Application spec](https://argo-cd.readthedocs.io/en/stable/operator-manual/declarative-setup/)  
- [Automated sync policy](https://argo-cd.readthedocs.io/en/stable/user-guide/auto_sync/)  
- [Helm chart: argo/argo-cd](https://github.com/argoproj/argo-helm/tree/main/charts/argo-cd)  
