# ArgoCD GitOps Workflow

This document completes Lab 13 by defining a reproducible ArgoCD-based GitOps workflow for the existing Helm chart in `k8s/devops-info-python`.

## 1. Scope

- ArgoCD is installed into the dedicated `argocd` namespace by Helm.
- A baseline manual `Application` is provided in `k8s/argocd/application.yaml`.
- Separate `dev` and `prod` `Application` resources are provided for multi-environment deployment.
- A bonus `ApplicationSet` is provided in `k8s/argocd/applicationset.yaml`.
- `dev` is auto-sync with `prune` and `selfHeal`.
- `prod` stays manual for controlled promotion.

Repository source used by the manifests:

- `repoURL`: `https://github.com/pepegx/DevOps-Core-Course.git`
- `targetRevision`: `lab13`
- `path`: `k8s/devops-info-python`

If you push Lab 13 to a different branch before creating the PR, update `targetRevision` in the ArgoCD manifests to match that branch.

## 2. Environment-Specific Configuration

The chart already supports environment overrides. Lab 13 adds the missing separation needed for GitOps:

- `values.yaml`: shared defaults
- `values-dev.yaml`: debug-friendly dev profile, `NodePort 30091`, 1 replica
- `values-prod.yaml`: production profile, stronger resource limits, 2 replicas, internal `ClusterIP` exposure, persistence disabled to avoid `ReadWriteOnce` multi-attach conflicts
- the ArgoCD `Application` manifests also carry small inline Helm overrides so the manifests can be validated locally before the Git branch is pushed

This fixes two practical issues:

- `dev` no longer collides with the already occupied `NodePort 30081` in the local cluster.
- `prod` now has a different replica count, which satisfies the lab requirement for environment-specific deployment differences.
- `prod` no longer combines a multi-replica Deployment with the Lab 12 single-writer `ReadWriteOnce` PVC pattern.
- the standalone Task 2 application uses `NodePort 30093` to avoid colliding with the pre-existing default-namespace service on `30080`

Important GitOps note:

- ArgoCD can only sync a `targetRevision` that already exists in the remote Git repository.
- With `targetRevision: lab13`, full end-to-end sync starts working only after `lab13` is pushed to `origin`.
- Before that push, you can still validate the Helm chart, the ArgoCD manifests, and the live cluster behavior with dry-runs or with an older remote branch already available in Git.

## 3. Install ArgoCD

### 3.1 Install the Helm repository

```bash
helm repo add argo https://argoproj.github.io/argo-helm
helm repo update
```

### 3.2 Install ArgoCD into its own namespace

```bash
kubectl create namespace argocd --dry-run=client -o yaml | kubectl apply -f -

helm upgrade --install argocd argo/argo-cd \
  --namespace argocd \
  -f k8s/argocd/install-values.yaml
```

### 3.3 Wait for core components

```bash
kubectl wait --for=condition=available deployment/argocd-server -n argocd --timeout=180s
kubectl wait --for=condition=available deployment/argocd-repo-server -n argocd --timeout=180s
kubectl wait --for=condition=available deployment/argocd-applicationset-controller -n argocd --timeout=180s
kubectl wait --for=condition=ready pod -l app.kubernetes.io/name=argocd-application-controller -n argocd --timeout=180s
kubectl get pods -n argocd
```

Expected result:

- all ArgoCD pods are `Running`
- `argocd-server`, `argocd-repo-server`, and `argocd-applicationset-controller` are available
- the `argocd-application-controller` pod is ready

## 4. Access UI and CLI

### 4.1 Port-forward the UI

```bash
kubectl port-forward svc/argocd-server -n argocd 8080:443
```

Open `https://localhost:8080`.

If your browser warns about the certificate, accept it for the local lab session and continue.

### 4.2 Retrieve the initial admin password

```bash
kubectl -n argocd get secret argocd-initial-admin-secret \
  -o jsonpath="{.data.password}" | base64 -d && echo
```

Login:

- username: `admin`
- password: output of the command above

### 4.3 Install and login with the CLI

```bash
brew install argocd
argocd login localhost:8080 --username admin --insecure
argocd account get-user-info
argocd app list
```

## 5. Task 2: Single Application Deployment

Apply the baseline manual app:

```bash
kubectl apply -f k8s/argocd/application.yaml
argocd app get devops-info-python
argocd app sync devops-info-python
argocd app wait devops-info-python --health --sync
```

Verification:

```bash
kubectl get all -n lab13
kubectl get pvc -n lab13
kubectl port-forward -n lab13 svc/devops-info-python 30090:80
curl http://127.0.0.1:30090/health
```

Expected result:

- the app status becomes `Synced` and `Healthy`
- the `lab13` namespace is created automatically
- the Flask service responds on `/health`

## 6. Task 3: Multi-Environment Deployment

Apply the explicit per-environment applications:

```bash
kubectl apply -f k8s/argocd/application-dev.yaml
kubectl apply -f k8s/argocd/application-prod.yaml
argocd app list
```

Check both applications:

```bash
argocd app get devops-info-python-dev
argocd app get devops-info-python-prod
kubectl get all -n dev
kubectl get all -n prod
```

Environment behavior:

- `dev`
  - value files: `values.yaml`, `values-dev.yaml`
  - namespace: `dev`
  - release name: `devops-info-python-dev`
  - sync mode: automatic
  - prune: enabled
  - self-heal: enabled
  - service exposure: `NodePort 30091`
- `prod`
  - value files: `values.yaml`, `values-prod.yaml`
  - namespace: `prod`
  - release name: `devops-info-python-prod`
  - sync mode: manual
  - prune: manual
  - self-heal: disabled
  - service exposure: internal `ClusterIP`, verify through `kubectl port-forward`
  - persistence: disabled to keep the multi-replica deployment safe on local `RWO` storage

Access checks:

```bash
kubectl port-forward -n dev svc/devops-info-python-dev 30091:80
curl http://127.0.0.1:30091/health
kubectl port-forward -n prod svc/devops-info-python-prod 30092:80
curl http://127.0.0.1:30092/health
```

If your kind cluster does not expose NodePorts directly to the host, use the `kubectl port-forward` command above for `dev` too.

Why `prod` stays manual:

- change review happens before deployment
- production rollout timing stays controlled
- risky Helm changes are not pushed straight into the cluster

## 7. Task 4: Self-Healing and Drift Tests

### 7.1 Manual scale drift in `dev`

```bash
kubectl scale deployment devops-info-python-dev -n dev --replicas=5
kubectl get deploy devops-info-python-dev -n dev -w
argocd app get devops-info-python-dev
```

Expected behavior:

- ArgoCD detects `OutOfSync`
- because `selfHeal: true`, ArgoCD reconciles back to the Git-defined replica count
- the deployment returns to 1 replica

### 7.2 Pod deletion test

```bash
kubectl delete pod -n dev -l app.kubernetes.io/instance=devops-info-python-dev
kubectl get pods -n dev -w
```

Expected behavior:

- Kubernetes recreates the pod immediately through the ReplicaSet
- this is Kubernetes self-healing, not an ArgoCD sync event

### 7.3 Configuration drift test

```bash
kubectl patch deployment devops-info-python-dev -n dev \
  --type merge \
  -p '{"spec":{"template":{"spec":{"containers":[{"name":"devops-info-python","image":"nginx:1.27"}]}}}}'
kubectl get deployment devops-info-python-dev -n dev \
  -o jsonpath='{.spec.template.spec.containers[?(@.name=="devops-info-python")].image}' && echo
argocd app get devops-info-python-dev --refresh
argocd app diff devops-info-python-dev
```

Expected behavior in this lab:

- the image change is configuration drift in the tracked `spec`, so ArgoCD can detect and revert it
- depending on reconcile timing, `argocd app diff` may show the drift only briefly or may already return clean output
- the reliable signal is that the container image returns to the Git-defined `pepegx/devops-info-service:lab12`

In this setup, a top-level metadata label like `kubectl label deployment ... drift=manual` is not a reliable proof of ArgoCD self-healing because that extra label may stay on the live object without showing up in `argocd app diff`. Use a `spec` change for the lab evidence instead, for example:

```bash
kubectl scale deployment devops-info-python-dev -n dev --replicas=5
argocd app get devops-info-python-dev --refresh
```

That scale change is usually easier to observe in `OutOfSync` state before auto-heal reconciles it.

### 7.4 Sync interval

By default, ArgoCD polls Git roughly every 3 minutes. Sync can also happen earlier when:

- you trigger it manually in the UI or CLI
- a webhook notifies ArgoCD about a new commit
- self-heal reacts to live-state drift on an automated application

## 8. Bonus: ApplicationSet

The bonus manifest is `k8s/argocd/applicationset.yaml`.

Switch to it cleanly:

```bash
kubectl delete applicationset devops-info-python-envs -n argocd --ignore-not-found
kubectl delete -f k8s/argocd/application-dev.yaml
kubectl delete -f k8s/argocd/application-prod.yaml
kubectl apply -f k8s/argocd/applicationset.yaml
kubectl get applicationset -n argocd
kubectl get applications -n argocd
```

What it does:

- uses the `list` generator to define `dev` and `prod`
- generates the same ArgoCD application names as the standalone flow: `devops-info-python-dev` and `devops-info-python-prod`
- keeps the same Helm `releaseName` values as the standalone flow, so the existing workloads can be adopted instead of duplicated
- uses `templatePatch` to apply `valueFiles`
- conditionally enables auto-sync only for `dev`

Important:

- this bonus manifest is intended to replace the individual `Application` resources, not run in parallel with them
- delete any previous bonus manifest before reapplying it, especially if it generated alternate names such as `*-set`
- if you leave the regular `application-dev.yaml` and `application-prod.yaml` active, ArgoCD will try to manage the same namespaces and the same service ports twice
- on a real cluster that leads to conflicts such as `NodePort ... already allocated`

Expected result after the switch:

- only one `ApplicationSet` named `devops-info-python-envs` exists in `argocd`
- only two environment applications exist in `argocd`: `devops-info-python-dev` and `devops-info-python-prod`
- there are no extra generated apps such as `devops-info-python-dev-set` or `devops-info-python-prod-set`

Why ApplicationSet is useful:

- one template controls multiple environments consistently
- adding a new environment becomes a data change, not a new full manifest
- drift in application definitions is reduced because shared logic lives in one place

When to prefer it:

- multiple environments of the same app
- mono-repo patterns
- repeated Application definitions that only differ by a few fields

## 9. Validation Commands

Use these commands before final push:

```bash
helm lint k8s/devops-info-python
helm template devops-info-python-dev k8s/devops-info-python \
  -f k8s/devops-info-python/values.yaml \
  -f k8s/devops-info-python/values-dev.yaml >/tmp/devops-info-python-dev.yaml
helm template devops-info-python-prod k8s/devops-info-python \
  -f k8s/devops-info-python/values.yaml \
  -f k8s/devops-info-python/values-prod.yaml >/tmp/devops-info-python-prod.yaml
kubectl apply --dry-run=client -f k8s/argocd/application.yaml
kubectl apply --dry-run=client -f k8s/argocd/application-dev.yaml
kubectl apply --dry-run=client -f k8s/argocd/application-prod.yaml
```

After ArgoCD CRDs are installed, validate server-side too:

```bash
kubectl apply --dry-run=server -f k8s/argocd/application.yaml
kubectl apply --dry-run=server -f k8s/argocd/application-dev.yaml
kubectl apply --dry-run=server -f k8s/argocd/application-prod.yaml
kubectl apply --dry-run=server -f k8s/argocd/applicationset.yaml
```

## 10. Screenshots To Capture For Submission

Take these screenshots after the manifests are synced from Git:

1. ArgoCD main dashboard with `devops-info-python-dev` and `devops-info-python-prod`
2. `devops-info-python-dev` details page showing `Synced` and `Healthy`
3. `devops-info-python-prod` details page before and after manual sync
4. Diff view for a drift test in `dev`
5. Terminal showing the scale drift reverting back to the Git-defined replica count
6. Bonus screenshot with generated `devops-info-python-dev` and `devops-info-python-prod` managed by `ApplicationSet`

## 11. Checklist Mapping

- Task 1: install via Helm, UI access, admin password, CLI login
- Task 2: `k8s/argocd/` created, single `Application` added, sync workflow documented
- Task 3: `dev` and `prod` apps added with different values files and sync policies
- Task 4: self-healing, pod deletion, and drift tests documented in repeatable command form
- Bonus: `ApplicationSet` implemented with a list generator and conditional auto-sync
