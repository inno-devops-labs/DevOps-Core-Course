# Lab 13 — GitOps with ArgoCD

## 1. ArgoCD setup

### Installation
ArgoCD was installed with Helm into the `argocd` namespace:

```bash
helm repo add argo https://argoproj.github.io/argo-helm
helm repo update
kubectl create namespace argocd
helm upgrade --install argocd argo/argo-cd -n argocd
```

### UI access
The server was exposed locally with port-forwarding:

```bash
kubectl port-forward svc/argocd-server -n argocd 8080:443
```

Initial admin password:

```bash
kubectl -n argocd get secret argocd-initial-admin-secret -o jsonpath="{.data.password}" | base64 -d
```

Login details:
- Username: `admin`
- Password: retrieved from `argocd-initial-admin-secret`

### CLI setup
The `argocd` CLI was installed locally and verified:

```bash
argocd version --client
argocd login localhost:8080 --insecure --username admin --password <password>
```

### Installation status
Current ArgoCD components are running in the `argocd` namespace.

---

## 2. Application deployment

Three ArgoCD Applications were created in [k8s/argocd/](k8s/argocd):

- [application.yaml](k8s/argocd/application.yaml)
- [application-dev.yaml](k8s/argocd/application-dev.yaml)
- [application-prod.yaml](k8s/argocd/application-prod.yaml)

### Shared source
- Git repository: `https://github.com/hololotl/DevOps-Core-Course.git`
- Git branch: `lab13`
- Chart path: `k8s/devops-app`

### Base application
- Name: `lab13-base`
- Namespace: `default`
- Sync policy: manual
- Purpose: baseline GitOps deployment

### Dev application
- Name: `lab13-dev`
- Namespace: `dev`
- Sync policy: automated with `prune: true` and `selfHeal: true`
- Purpose: development environment with auto-sync

### Prod application
- Name: `lab13-prod`
- Namespace: `prod`
- Sync policy: manual
- Purpose: production environment with controlled updates

### Verification
After creation and sync:

```bash
argocd app list
```

Result summary:
- `lab13-base` — Synced, Healthy
- `lab13-dev` — Synced, Healthy
- `lab13-prod` — Synced, Healthy

---

## 3. Multi-environment deployment

Environment-specific values files:

- [values-dev.yaml](k8s/devops-app/values-dev.yaml)
- [values-prod.yaml](k8s/devops-app/values-prod.yaml)

### Dev configuration
- `replicaCount: 1`
- `service.type: ClusterIP`
- `image.tag: 1.0.0`
- `persistence.enabled: false`
- Auto-sync enabled

### Prod configuration
- `replicaCount: 3`
- `service.type: ClusterIP`
- `image.tag: 1.0.0`
- `persistence.enabled: false`
- Manual sync only

### Namespaces
Created namespaces:

```bash
kubectl create namespace dev
kubectl create namespace prod
```

### Why prod stays manual
- safer release control
- easier rollback planning
- prevents accidental live changes

---

## 4. Self-healing and sync policy tests

### Test 1: manual scale drift in dev
The dev deployment was scaled manually to 5 replicas:

```bash
kubectl -n dev scale deployment/lab13-dev-devops-app --replicas=5
```

Observed behavior:
- ArgoCD detected drift
- Auto-sync/self-heal restored the desired state
- Deployment returned to `1 -> 1 ready=1`

Evidence:

```bash
1 -> 1 ready=1
```

### Test 2: pod deletion in dev
A running pod was deleted manually:

```bash
kubectl -n dev delete pod <pod-name>
```

Observed behavior:
- Kubernetes recreated the pod automatically
- This is controller behavior from Deployment/ReplicaSet
- It is separate from ArgoCD self-healing

Evidence:
- Old pod entered `Terminating`
- New pod appeared in `Running` state

### Difference between healing types
- **Kubernetes self-healing**: restores pod count after a pod is deleted
- **ArgoCD self-healing**: restores desired configuration from Git when cluster state drifts

---

## 5. Verification outputs

### ArgoCD application status
Current healthy state:

```bash
argocd app get lab13-base
argocd app get lab13-dev
argocd app get lab13-prod
```

Observed final status:
- `lab13-base` — Synced, Healthy
- `lab13-dev` — Synced, Healthy
- `lab13-prod` — Synced, Healthy

### Pod state

```bash
kubectl get pods -n dev
kubectl get pods -n prod
```

Observed final state:
- `dev` has a running pod
- `prod` has running pods

---

## 6. Screenshots to include

Add screenshots of:
1. ArgoCD UI showing all three applications
2. Application details for `lab13-dev`
3. Sync status after manual scale test
4. Pod recreation after deletion in `dev`

---

## 7. Summary

Completed tasks:
- Task 1 — ArgoCD installation and CLI setup
- Task 2 — Application deployment
- Task 3 — Multi-environment deployment
- Task 4 — Self-healing and sync policies

Bonus task not completed.
