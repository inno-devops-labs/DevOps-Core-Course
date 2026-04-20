# Lab 13 — GitOps with ArgoCD

This document contains the implementation artifacts and verification flow for Lab 13.

## 1. ArgoCD setup

### 1.1 Install ArgoCD via Helm

```bash
helm repo add argo https://argoproj.github.io/argo-helm
helm repo update

kubectl create namespace argocd
helm install argocd argo/argo-cd --namespace argocd

kubectl wait --for=condition=ready pod -l app.kubernetes.io/name=argocd-server -n argocd --timeout=180s
kubectl get pods -n argocd
```

Installation output:

```text
"argo" has been added to your repositories
...Successfully got an update from the "argo" chart repository
namespace/argocd created
Release "argocd" does not exist. Installing it now.
NAME: argocd
NAMESPACE: argocd
STATUS: deployed
REVISION: 1
pod/argocd-server-5f777b877f-vtrqr condition met
```

### 1.2 Access ArgoCD UI

```bash
kubectl port-forward svc/argocd-server -n argocd 8080:443
```

Open: `https://localhost:8080`  
Username: `admin`

Retrieve initial password:

```bash
kubectl -n argocd get secret argocd-initial-admin-secret -o jsonpath="{.data.password}" | base64 -d && echo
```

![alt](/k8s/assets/Screenshot%202026-04-20%20at%2020.20.14.png)

### 1.3 ArgoCD CLI login

```bash
brew install argocd
argocd login localhost:8080 --insecure
argocd app list
```

CLI output:

```text
'admin:login' logged in successfully
Context 'localhost:8080' updated
```

## 2. Application configuration

All manifests are in `k8s/argocd/`:

- `application.yaml`: single app deployment (manual sync) using `values.yaml`
- `application-dev.yaml`: dev deployment with auto-sync (`prune` + `selfHeal`) using `values-dev.yaml`
- `application-prod.yaml`: prod deployment with manual sync using `values-prod.yaml`
- `applicationset.yaml`: bonus ApplicationSet (list generator)

### 2.1 Source configuration

- `repoURL`: `https://github.com/ilyalinhnguyen/DevOps-Core-Course.git`
- `targetRevision`: `lab13`
- `path`: `k8s/devops-info`
- Helm values:
  - `values-dev.yaml` for dev
  - `values-prod.yaml` for prod

### 2.2 Destination configuration

- Cluster: `https://kubernetes.default.svc`
- Namespaces: `dev` and `prod`
- `CreateNamespace=true` is enabled in sync options

## 3. Multi-environment deployment

### 3.1 Create namespaces

```bash
kubectl create namespace dev
kubectl create namespace prod
```

Output:

```text
namespace/dev created
namespace/prod created
```

### 3.2 Apply ArgoCD Application manifests

```bash
kubectl apply -f k8s/argocd/application-dev.yaml
kubectl apply -f k8s/argocd/application-prod.yaml
```

Output:

```text
application.argoproj.io/devops-info-dev created
application.argoproj.io/devops-info-prod created
```

### 3.3 Sync policy differences

- **Dev (`devops-info-dev`)**
  - Auto-sync enabled
  - `selfHeal: true`: reverts manual drift
  - `prune: true`: removes resources deleted from Git
- **Prod (`devops-info-prod`)**
  - Manual sync only (no `automated` block)
  - Best for controlled releases and change review

### 3.4 Verify both environments

```bash
argocd app list
kubectl get pods -n dev
kubectl get pods -n prod
```

Current verification output:

```text
NAME                     CLUSTER                         NAMESPACE  PROJECT  STATUS  HEALTH       SYNCPOLICY  CONDITIONS  REPO                                                      PATH             TARGET
argocd/devops-info-dev   https://kubernetes.default.svc  dev        default  Synced  Healthy      Auto-Prune  <none>      https://github.com/ilyalinhnguyen/DevOps-Core-Course.git  k8s/devops-info  lab13
argocd/devops-info-prod  https://kubernetes.default.svc  prod       default  Synced  Healthy      Manual      <none>      https://github.com/ilyalinhnguyen/DevOps-Core-Course.git  k8s/devops-info  lab13
```

```text
NAME                               READY   STATUS    RESTARTS   AGE
devops-info-dev-7b4d65489f-md5g7   1/1     Running   0          48m
```

```text
NAME                                 READY   STATUS      RESTARTS   AGE
devops-info-prod-7f4cdd5dc5-5chzx    1/1     Running     0          14m
devops-info-prod-7f4cdd5dc5-78nnx    1/1     Running     0          14m
devops-info-prod-7f4cdd5dc5-bkb6q    1/1     Running     0          14m
```

```text
NAME               TYPE       CLUSTER-IP       EXTERNAL-IP   PORT(S)        AGE
devops-info-prod   NodePort   10.111.241.242   <none>        80:32316/TCP   14m
```

## 4. Self-healing and sync behavior

### 4.1 Manual scale drift test (ArgoCD self-healing)

1. Confirm desired replica count is from `values-dev.yaml`.
2. Scale deployment manually:

```bash
kubectl scale deployment devops-info-dev -n dev --replicas=5
kubectl get deploy -n dev devops-info-dev -w
```

3. Observe ArgoCD mark app `OutOfSync`, then auto-reconcile back to Git value.

### 4.2 Pod deletion test (Kubernetes self-healing)

```bash
kubectl delete pod -n dev -l app.kubernetes.io/instance=devops-info-dev
kubectl get pods -n dev -w
```

Expected result: ReplicaSet recreates deleted pod immediately.  
This behavior is native Kubernetes reconciliation, not ArgoCD sync.

### 4.3 Configuration drift test (ArgoCD self-healing)

```bash
kubectl label deployment devops-info-dev -n dev drift-test=true --overwrite
argocd app diff devops-info-dev
argocd app get devops-info-dev
```

Expected result: ArgoCD detects drift and removes non-declarative label when self-heal runs.

### 4.4 ArgoCD sync behavior summary

- ArgoCD compares live state with Git-defined desired state.
- Automatic sync happens when:
  - Git changes are detected, and/or
  - live state drifts while `selfHeal` is enabled.
- Default reconciliation polling interval is about 3 minutes.
- Webhooks can make sync nearly immediate after `git push`.

## 5. Bonus: ApplicationSet

The file `k8s/argocd/applicationset.yaml` demonstrates a List generator that defines dev/prod environment parameters in one object and generates two Application resources.

### Why use ApplicationSet

- Single template for many environments/apps
- Less duplication than separate Application manifests
- Easier scaling for mono-repo and multi-cluster patterns

### When individual Applications are still useful

- Small number of environments
- Different sync policies or lifecycle controls per env
- Need explicit, independently managed manifests

## 6. Useful command sequence

```bash
# 1) Install ArgoCD
helm repo add argo https://argoproj.github.io/argo-helm
helm repo update
kubectl create namespace argocd
helm install argocd argo/argo-cd --namespace argocd

# 2) Login
kubectl port-forward svc/argocd-server -n argocd 8080:443
argocd login localhost:8080 --insecure

# 3) Deploy dev/prod apps
kubectl create namespace dev
kubectl create namespace prod
kubectl apply -f k8s/argocd/application-dev.yaml
kubectl apply -f k8s/argocd/application-prod.yaml

# 4) Verify
argocd app list
kubectl get all -n dev
kubectl get all -n prod
```

## 7. Screenshot checklist

![alt](/k8s/assets/Screenshot%202026-04-20%20at%2020.20.14.png)
![alt](/k8s/assets/Screenshot%202026-04-20%20at%2020.22.53.png)
![alt](/k8s/assets/Screenshot%202026-04-20%20at%2020.23.06.png)