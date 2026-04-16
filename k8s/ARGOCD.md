# Lab 13 - GitOps with ArgoCD

## 1. ArgoCD Setup

### 1.1 Install ArgoCD with Helm

```bash
helm repo add argo https://argoproj.github.io/argo-helm
helm repo update
kubectl create namespace argocd
helm upgrade --install argocd argo/argo-cd -n argocd
kubectl get pods -n argocd
```

Expected: server/repo-server/application-controller/dex/redis components are `Running`.

### 1.2 Access UI

```bash
kubectl port-forward svc/argocd-server -n argocd 8080:443
kubectl -n argocd get secret argocd-initial-admin-secret -o jsonpath="{.data.password}" | base64 -d && echo
```

Login:

- URL: `https://localhost:8080`
- Username: `admin`
- Password: decoded value from the secret above

### 1.3 ArgoCD CLI

```bash
argocd version --client
argocd login localhost:8080 --insecure
argocd account get-user-info
```

---

## 2. Application Deployment

### 2.1 Manifests created

- `k8s/argocd/application.yaml` (single app, manual sync)
- `k8s/argocd/application-dev.yaml` (dev app, auto-sync)
- `k8s/argocd/application-prod.yaml` (prod app, manual sync)
- `k8s/argocd/namespaces.yaml` (`dev` and `prod`)
- `k8s/argocd/applicationset.yaml` (bonus)

Note:

- `repoURL` currently points to `https://github.com/mpasgat/DevOps-Core-Course.git`.
- If you are using your fork/branch, update `repoURL` and `targetRevision` in these manifests.

### 2.2 Apply and sync (single app)

```bash
kubectl apply -f k8s/argocd/application.yaml
argocd app list
argocd app get python-app
argocd app sync python-app
argocd app wait python-app --health --sync
```

### 2.3 GitOps drift detection test

1. Change Helm value in Git (example: `replicaCount` in chart values).
2. Commit/push change.
3. Observe app status:

```bash
argocd app get python-app
```

Expected:

- status changes to `OutOfSync` until sync is triggered (manual policy).

---

## 3. Multi-Environment Deployment

### 3.1 Create namespaces

```bash
kubectl apply -f k8s/argocd/namespaces.yaml
kubectl get ns dev prod
```

### 3.2 Apply dev/prod ArgoCD Applications

```bash
kubectl apply -f k8s/argocd/application-dev.yaml
kubectl apply -f k8s/argocd/application-prod.yaml
argocd app list
```

### 3.3 Sync behavior

- `python-app-dev`: automated sync enabled (`prune=true`, `selfHeal=true`).
- `python-app-prod`: manual sync only.

### 3.4 Verify deployments

```bash
argocd app get python-app-dev
argocd app get python-app-prod
kubectl get all -n dev
kubectl get all -n prod
```

Rationale:

- Auto-sync in dev speeds feedback loops.
- Manual sync in prod gives controlled rollout/review.

---

## 4. Self-Healing and Drift Tests

### 4.1 Manual scale drift test (dev)

```bash
kubectl -n dev get deploy
kubectl -n dev scale deployment <deployment-name> --replicas=5
kubectl -n dev get deploy <deployment-name> -w
argocd app get python-app-dev
```

Expected:

- ArgoCD detects drift and reverts replicas to Git value automatically.

### 4.2 Pod deletion test

```bash
kubectl -n dev delete pod -l app.kubernetes.io/instance=python-app-dev
kubectl -n dev get pods -w
```

Expected:

- Pod is recreated by Kubernetes Deployment/ReplicaSet controller.
- This is Kubernetes self-healing, not ArgoCD sync.

### 4.3 Resource edit drift test

```bash
kubectl -n dev patch deployment <deployment-name> --type='merge' -p '{"metadata":{"labels":{"manual-drift":"true"}}}'
argocd app diff python-app-dev
argocd app get python-app-dev
```

Expected:

- Drift detected by ArgoCD and reverted by self-heal.

### 4.4 Sync trigger behavior

- ArgoCD compares desired (Git) vs live state continuously.
- Repo polling is periodic (default around 3 minutes).
- Webhooks can provide near-immediate update detection.
- Manual sync is always available via UI/CLI.

---

## 5. Bonus - ApplicationSet

Implemented:

- `k8s/argocd/applicationset.yaml`
- Generator type: `list`
- Environments generated from one template (`dev` and `prod`)

How it works:

- Shared template defines source/destination/base syncOptions.
- `templatePatch` conditionally adds automated sync only for `dev`.

Apply:

```bash
# Optional cleanup if standalone app manifests already applied
kubectl -n argocd delete application python-app-dev python-app-prod --ignore-not-found

kubectl apply -f k8s/argocd/applicationset.yaml
kubectl -n argocd get applicationsets
kubectl -n argocd get applications
argocd app list
```

Benefits over individual Applications:

- Less duplication.
- Consistent policy/template.
- Scales better when env/app count grows.

When to use:

- `Application`: few apps, explicit control.
- `ApplicationSet`: many similar apps/environments/clusters.

---

## 6. Suggested Evidence Commands for Submission

```bash
kubectl get pods -n argocd
argocd app list
argocd app get python-app-dev
argocd app get python-app-prod
kubectl get all -n dev
kubectl get all -n prod
```

Screenshot checklist:

1. ArgoCD UI with both dev/prod apps.
2. Sync/Health status per app.
3. Application details panel showing source path + values file.
4. Drift/self-heal before/after (dev).
