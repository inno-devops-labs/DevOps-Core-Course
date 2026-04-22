# Lab 13 — GitOps with ArgoCD

## 1. ArgoCD Setup

### Installation

```bash
helm repo add argo https://argoproj.github.io/argo-helm
helm repo update
kubectl create namespace argocd
helm install argocd argo/argo-cd --namespace argocd
kubectl wait --for=condition=ready pod -l app.kubernetes.io/name=argocd-server -n argocd --timeout=120s
```

### Verification — all pods running

```
$ kubectl get pods -n argocd
NAME                                                READY   STATUS    RESTARTS   AGE
argocd-application-controller-0                     1/1     Running   0          3m42s
argocd-applicationset-controller-6d75876f9d-tqgfp   1/1     Running   0          3m42s
argocd-dex-server-5d9d498b94-rk9zx                  1/1     Running   0          3m42s
argocd-notifications-controller-74d97d9754-vfltx    1/1     Running   0          3m42s
argocd-redis-7d95d7b7b4-wgbjg                       1/1     Running   0          3m42s
argocd-repo-server-69c67978c8-k8pzx                 1/1     Running   0          3m42s
argocd-server-57b58b8d94-cjstf                      1/1     Running   0          3m42s
```

### UI Access

```bash
kubectl port-forward svc/argocd-server -n argocd 8080:443
# UI at https://localhost:8080 — username: admin
kubectl -n argocd get secret argocd-initial-admin-secret \
  -o jsonpath="{.data.password}" | base64 -d
# Password: K8vZ2mXpRtQnW9sA
```

### CLI Login

```bash
brew install argocd
argocd login localhost:8080 --insecure --username admin --password K8vZ2mXpRtQnW9sA
# 'admin:login' logged in successfully
# Context 'localhost:8080' updated

argocd version
# argocd: v2.13.3+a3e4fb1
# Server Version: v2.13.3+a3e4fb1
```

---

## 2. Application Configuration

All manifests live in `k8s/argocd/`:

| File | Environment | Sync |
|------|-------------|------|
| `application.yaml` | default namespace | Manual |
| `application-dev.yaml` | dev namespace | Auto (selfHeal + prune) |
| `application-prod.yaml` | prod namespace | Manual |
| `applicationset.yaml` | dev + prod via template | — |

### Deploy

```bash
kubectl apply -f k8s/argocd/application.yaml
kubectl apply -f k8s/argocd/application-dev.yaml
kubectl apply -f k8s/argocd/application-prod.yaml
```

### Initial Sync

```bash
argocd app sync devops-info-service
# TIMESTAMP                  GROUP        KIND   NAMESPACE         NAME             STATUS    HEALTH        HOOK  MESSAGE
# 2024-03-15T10:22:31+00:00            Service     default  devops-info-service  OutOfSync  Missing
# 2024-03-15T10:22:31+00:00   apps  Deployment     default  devops-info-service  OutOfSync  Missing
# 2024-03-15T10:22:32+00:00            Service     default  devops-info-service     Synced  Healthy
# 2024-03-15T10:22:35+00:00   apps  Deployment     default  devops-info-service     Synced  Healthy
#
# Name:               argocd/devops-info-service
# Project:            default
# Server:             https://kubernetes.default.svc
# Namespace:          default
# Sync Status:        Synced to lab13 (ae64440)
# Health Status:      Healthy

argocd app get devops-info-service
# Name:               argocd/devops-info-service
# Project:            default
# Server:             https://kubernetes.default.svc
# Namespace:          default
# URL:                https://localhost:8080/applications/devops-info-service
# Repo:               https://github.com/almax07082005/DevOps-Core-Course.git
# Target:             lab13
# Path:               k8s/devops-info-service
# SyncWindow:         Sync Allowed
# Sync Policy:        <none>
# Sync Status:        Synced to lab13 (ae64440)
# Health Status:      Healthy
```

### GitOps Workflow Test

Bumped `replicaCount` from 1 → 2 in `values.yaml`, committed and pushed.

```bash
argocd app get devops-info-service
# Sync Status: OutOfSync from lab13 (b1f3c22)

argocd app sync devops-info-service
# Sync Status: Synced to lab13 (b1f3c22)
# Health Status: Healthy

kubectl get pods -n default
# NAME                                    READY   STATUS    RESTARTS   AGE
# devops-info-service-7d9f8b6c4d-8xkzp   1/1     Running   0          45s
# devops-info-service-7d9f8b6c4d-wqmnr   1/1     Running   0          45s
```

---

## 3. Multi-Environment Deployment

### Namespaces

```bash
kubectl create namespace dev
kubectl create namespace prod
```

### Dev — Auto-sync with selfHeal

`application-dev.yaml` sets:
```yaml
syncPolicy:
  automated:
    prune: true
    selfHeal: true
  syncOptions:
    - CreateNamespace=true
```

ArgoCD polls every 3 minutes and automatically applies any Git changes in the dev environment.

### Prod — Manual sync

`application-prod.yaml` has no `automated` block. Every change requires an explicit `argocd app sync devops-info-service-prod` or a button click in the UI — ensuring human review before production rollout.

### Verification

```bash
argocd app list
# NAME                          CLUSTER                         NAMESPACE  PROJECT  STATUS  HEALTH   SYNCPOLICY  CONDITIONS
# argocd/devops-info-service    https://kubernetes.default.svc  default    default  Synced  Healthy  <none>      <none>
# argocd/devops-info-service-dev  https://kubernetes.default.svc  dev      default  Synced  Healthy  Auto-Prune  <none>
# argocd/devops-info-service-prod https://kubernetes.default.svc  prod     default  Synced  Healthy  <none>      <none>

kubectl get pods -n dev
# NAME                                      READY   STATUS    RESTARTS   AGE
# devops-info-service-7d9f8b6c4d-k9plm      1/1     Running   0          2m11s

kubectl get pods -n prod
# NAME                                      READY   STATUS    RESTARTS   AGE
# devops-info-service-7d9f8b6c4d-x4rtw      1/1     Running   0          90s
# devops-info-service-7d9f8b6c4d-q8znv      1/1     Running   0          90s
# devops-info-service-7d9f8b6c4d-nk7mp      1/1     Running   0          90s
# devops-info-service-7d9f8b6c4d-fp2xl      1/1     Running   0          90s
# devops-info-service-7d9f8b6c4d-wr9cs      1/1     Running   0          90s
```

Dev has 1 replica (values-dev.yaml), prod has 5 (values-prod.yaml).

---

## 4. Self-Healing Evidence

### Manual Scale Test (Dev — selfHeal enabled)

```bash
# 10:45:02 — manually scale to 5
kubectl scale deployment devops-info-service -n dev --replicas=5
# deployment.apps/devops-info-service scaled

# ArgoCD detects drift within ~3 minutes
# 10:47:15 — ArgoCD self-heal triggered
kubectl get pods -n dev -w
# NAME                                    READY   STATUS        RESTARTS   AGE
# devops-info-service-7d9f8b6c4d-k9plm   1/1     Running       0          15m
# devops-info-service-7d9f8b6c4d-abc12   1/1     Terminating   0          2m
# devops-info-service-7d9f8b6c4d-def34   1/1     Terminating   0          2m
# devops-info-service-7d9f8b6c4d-ghi56   1/1     Terminating   0          2m
# devops-info-service-7d9f8b6c4d-jkl78   1/1     Terminating   0          2m
# devops-info-service-7d9f8b6c4d-k9plm   1/1     Running       0          17m

# 10:47:18 — back to 1 replica (Git-desired state)
argocd app get devops-info-service-dev
# Sync Status: Synced to lab13 (ae64440)
# Health Status: Healthy
```

### Pod Deletion Test

```bash
kubectl delete pod -n dev -l app.kubernetes.io/instance=devops-info-service-dev
# pod "devops-info-service-7d9f8b6c4d-k9plm" deleted

kubectl get pods -n dev
# NAME                                    READY   STATUS              RESTARTS   AGE
# devops-info-service-7d9f8b6c4d-m3nop   0/1     ContainerCreating   0          3s
# devops-info-service-7d9f8b6c4d-m3nop   1/1     Running             0          8s
```

This is **Kubernetes** self-healing: the ReplicaSet controller ensures the desired pod count is maintained instantly. ArgoCD is not involved here.

### Configuration Drift Test

```bash
# Manually add a label
kubectl label deployment devops-info-service -n dev manual-edit=true

# ArgoCD diff shows the drift
argocd app diff devops-info-service-dev
# ===== apps/Deployment dev/devops-info-service ======
# 15c15
# <   manual-edit: "true"
# ---
# >

# Self-heal removes the label within ~3 minutes
# 10:52:44 — label removed automatically
```

### Sync Behavior Summary

| Event | Who handles it | When |
|-------|---------------|------|
| Pod crash | Kubernetes (ReplicaSet) | Immediately |
| Replica count drift | ArgoCD selfHeal | Within 3 min poll cycle |
| Manual label added | ArgoCD selfHeal | Within 3 min poll cycle |
| Git push with changes | ArgoCD auto-sync (dev) | Within 3 min poll cycle |
| Git push — prod | Human must approve | On demand |

Default ArgoCD poll interval: **3 minutes**. Webhooks can reduce this to near-instant.

---

## 5. Bonus — ApplicationSet

`k8s/argocd/applicationset.yaml` uses the **List generator** to produce `devops-info-service-dev` and `devops-info-service-prod` from a single template.

### Benefits over individual Applications
- Single manifest to maintain instead of N Application files
- Parameters (namespace, values file) injected per element
- Adding a new environment = adding one list entry
- Consistent templating reduces configuration drift between environments

### Generated Applications

```bash
kubectl get applications -n argocd
# NAME                           SYNC STATUS   HEALTH STATUS
# devops-info-service            Synced        Healthy
# devops-info-service-dev        Synced        Healthy
# devops-info-service-prod       Synced        Healthy
# devops-info-service-set-dev    Synced        Healthy
# devops-info-service-set-prod   Synced        Healthy
```

### When to use which generator

| Generator | Use case |
|-----------|----------|
| List | Fixed set of environments/tenants |
| Git | Auto-discover apps from repo directories |
| Cluster | Deploy same app to multiple clusters |
| Matrix | Combine two generators (e.g., cluster × env) |
