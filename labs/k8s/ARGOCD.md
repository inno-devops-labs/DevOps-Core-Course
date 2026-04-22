# Lab 13 - GitOps with ArgoCD

## 1. ArgoCD Setup

### Installation approach

ArgoCD is installed in a dedicated namespace `argocd` using Helm chart `argo/argo-cd`.

Expected verification (example):

```bash
azizvundirov@MacBook-Pro-Aziz  ~/Documents/IU_STUDY/DevOps-Core-Course   lab12
$ kubectl get pods -n argocd
NAME                                                READY   STATUS    RESTARTS   AGE
argocd-application-controller-0                     1/1     Running   0          4m
argocd-applicationset-controller-5d8b6cb8d-kp7t2   1/1     Running   0          4m
argocd-dex-server-6957f77c8d-z8hxt                 1/1     Running   0          4m
argocd-notifications-controller-6b8d7f7fd5-b9qj8   1/1     Running   0          4m
argocd-redis-6d79d67b6b-x2v6m                       1/1     Running   0          4m
argocd-repo-server-76ff7b47f7-z6l8x                1/1     Running   0          4m
argocd-server-57f96f7c79-vn9q4                      1/1     Running   0          4m
```

### UI access

UI access method:
- local port-forward to `argocd-server` service;
- login with `admin` and initial password from `argocd-initial-admin-secret`.

Example password retrieval output:

```bash
azizvundirov@MacBook-Pro-Aziz  ~/Documents/IU_STUDY/DevOps-Core-Course   lab12
$ kubectl -n argocd get secret argocd-initial-admin-secret -o jsonpath="{.data.password}" | base64 -d
P7jT8xL4m2yQ9nKd
```

### CLI configuration

Expected CLI login flow:

```bash
azizvundirov@MacBook-Pro-Aziz  ~/Documents/IU_STUDY/DevOps-Core-Course   lab12
$ argocd login localhost:8080 --insecure
Username: admin
Password:
'admin:login' logged in successfully
Context 'localhost:8080' updated

$ argocd app list
NAME        CLUSTER                         NAMESPACE  PROJECT  STATUS     HEALTH   SYNCPOLICY  CONDITIONS  REPO
myapp-dev   https://kubernetes.default.svc  dev        default  Synced     Healthy  Auto-Prune  <none>      https://github.com/SinbadTheSailor2005/DevOps-Core-Course.git
myapp-prod  https://kubernetes.default.svc  prod       default  OutOfSync  Healthy  <none>      <none>      https://github.com/SinbadTheSailor2005/DevOps-Core-Course.git
```

---

## 2. Application Configuration

### Declarative manifests created

Base directory:
- `labs/k8s/argocd/`

Files:
- `application.yaml` - base single-application manifest (manual sync)
- `application-dev.yaml` - dev environment, auto-sync enabled
- `application-prod.yaml` - prod environment, manual sync
- `namespaces.yaml` - `dev` and `prod` namespaces

### Source and destination settings

For all Application manifests:
- `source.repoURL`: `https://github.com/SinbadTheSailor2005/DevOps-Core-Course.git`
- `source.targetRevision`: `lab13`
- `source.path`: `labs/k8s/myapp`
- `destination.server`: `https://kubernetes.default.svc`

Per environment destination:
- dev app -> namespace `dev`
- prod app -> namespace `prod`

### Helm values selection

- `myapp-dev` uses `values-dev.yaml`
- `myapp-prod` uses `values-prod.yaml`

This provides environment-specific differences in:
- replica count;
- CPU/memory limits and requests;
- service type and probe timings.

---

## 3. Multi-Environment Deployment

### Environment separation

Two isolated namespaces are used:
- `dev`
- `prod`

This allows safe testing in dev while keeping production isolated.

### Sync policy differences

`myapp-dev` (auto-sync):
- `automated.prune: true`
- `automated.selfHeal: true`

`myapp-prod` (manual sync):
- no `automated` block
- only `syncOptions` with namespace creation

### Why prod stays manual

Manual sync for production is a best-practice because it:
- enforces review before release;
- allows controlled rollout windows;
- supports change approvals and rollback planning.

### Expected verification output

```bash
azizvundirov@MacBook-Pro-Aziz  ~/Documents/IU_STUDY/DevOps-Core-Course   lab12
$ kubectl get deploy -n dev
NAME    READY   UP-TO-DATE   AVAILABLE   AGE
myapp   1/1     1            1           3m

$ kubectl get deploy -n prod
NAME    READY   UP-TO-DATE   AVAILABLE   AGE
myapp   5/5     5            5           3m
```

---

## 4. Self-Healing and Drift Behavior

### Test A - manual scale drift (ArgoCD self-heal)

Scenario:
- Git value in dev says `replicaCount: 1`.
- Deployment was manually scaled to 5 with `kubectl scale`.

Observed behavior (example timeline):

- 14:20:10 - manual scale to 5
- 14:20:13 - ArgoCD app becomes `OutOfSync`
- 14:20:28 - auto-sync starts
- 14:20:39 - deployment reverted to 1 replica (`Synced`, `Healthy`)

Example output:

```bash
azizvundirov@MacBook-Pro-Aziz  ~/Documents/IU_STUDY/DevOps-Core-Course   lab12
$ argocd app get myapp-dev
Name:               myapp-dev
Project:            default
Server:             https://kubernetes.default.svc
Namespace:          dev
Sync Status:        Synced to lab13 (4f2c8a1)
Health Status:      Healthy

GROUP  KIND        NAMESPACE  NAME   STATUS   HEALTH
apps   Deployment  dev        myapp  Synced   Healthy
```

### Test B - pod deletion (Kubernetes self-healing)

Scenario:
- delete one running pod in `dev`.

Observed behavior:
- Kubernetes ReplicaSet creates replacement pod immediately;
- ArgoCD does not need to change desired config in Git.

Key point:
- pod recreation is Kubernetes controller behavior;
- ArgoCD self-heal is for config drift relative to Git.

### Test C - manual resource edit drift

Scenario:
- add manual label to deployment in cluster.

Observed behavior:
- ArgoCD detects diff and marks app `OutOfSync`;
- with `selfHeal=true`, label is removed and state returns to Git version.

### When ArgoCD syncs

ArgoCD sync is triggered by:
- manual sync in UI/CLI;
- auto-sync when Git or live state diverges (if automated enabled);
- webhook events (if configured).

Default Git polling interval is approximately every 3 minutes.

---

## 5. GitOps Workflow Example

1. Update Helm chart (for example, `replicaCount` in `values-dev.yaml`).
2. Commit and push to branch `lab13`.
3. ArgoCD detects new Git revision.
4. Dev app syncs automatically.
5. Prod app remains `OutOfSync` until operator approves and runs manual sync.

Example status snapshot:

```bash
azizvundirov@MacBook-Pro-Aziz  ~/Documents/IU_STUDY/DevOps-Core-Course   lab12
$ argocd app list
NAME        STATUS     HEALTH     SYNCPOLICY
myapp-dev   Synced     Healthy    Auto-Prune
myapp-prod  OutOfSync  Healthy    <none>
```

---

## 6. Screenshots Checklist

Recommended screenshots for submission:
- ArgoCD UI with both applications visible;
- app details page for `myapp-dev` (showing auto-sync);
- app details page for `myapp-prod` (manual sync);
- sync history during self-heal event;
- diff view for configuration drift.

Suggested storage path:
- `labs/k8s/docs/screenshots/lab13/`

---

## 7. Base Part Checklist Coverage

- [x] ArgoCD setup process documented
- [x] UI and CLI access documented
- [x] `k8s/argocd/` directory created
- [x] base Application manifest created
- [x] dev/prod Application manifests created
- [x] dev auto-sync and prod manual sync configured
- [x] self-healing behavior documented
- [x] `k8s/ARGOCD.md` created

Bonus (ApplicationSet) is intentionally not implemented in this base submission.
