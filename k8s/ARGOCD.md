# Lab 13 — GitOps with ArgoCD

This document contains the implementation artifacts and verification flow for Lab 13.

**Evidence note:** CLI snippets below were captured **2026-04-30** on **minikube** profile **`lab09`** (`kubectl config current-context: lab09`). Replica names, ages, NodePorts, and Git revision hashes will change on your cluster; rerun the commands to refresh.

## 1. ArgoCD setup

### 1.1 Install ArgoCD via Helm

```bash
helm repo add argo https://argoproj.github.io/argo-helm
helm repo update

kubectl create namespace argocd --dry-run=client -o yaml | kubectl apply -f -
helm upgrade --install argocd argo/argo-cd --namespace argocd --wait --timeout 10m

kubectl wait --for=condition=ready pod -l app.kubernetes.io/name=argocd-server -n argocd --timeout=180s
kubectl get pods -n argocd -l app.kubernetes.io/name=argocd-server
helm list -n argocd
```

Installation / upgrade output (same cluster):

```text
NAME  	NAMESPACE	REVISION	UPDATED                             	STATUS  	CHART        	APP VERSION
argocd	argocd   	2       	2026-04-30 11:59:26.092297 +0300 MSK	deployed	argo-cd-9.5.9	v3.3.8
```

```text
NAME                             READY   STATUS    RESTARTS   AGE
argocd-server-6869cd6b4d-7gcgw   1/1     Running   0          23m
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
kubectl port-forward svc/argocd-server -n argocd 8080:443
argocd login localhost:8080 --insecure
argocd app list
```

CLI login output (representative):

```text
'admin:login' logged in successfully
Context 'localhost:8080' updated
```

Equivalent view without logging in via `kubectl` (same cluster):

```bash
kubectl get application -n argocd -o wide
```

```text
NAME               SYNC STATUS   HEALTH STATUS   REVISION                                   PROJECT
devops-info        Synced        Healthy         5884a3a6eb7e777937ef532a889d24e8ea95e212   default
devops-info-dev    Synced        Healthy         5884a3a6eb7e777937ef532a889d24e8ea95e212   default
devops-info-prod   Synced        Healthy         5884a3a6eb7e777937ef532a889d24e8ea95e212   default
```

## 2. Application configuration

All manifests are in `k8s/argocd/`:

- `application.yaml`: single app deployment (manual sync) using `values.yaml`
- `application-dev.yaml`: dev deployment with auto-sync (`prune` + `selfHeal`) using `values-dev.yaml`
- `application-prod.yaml`: prod deployment with manual sync using `values-prod.yaml`
- `applicationset.yaml`: bonus ApplicationSet (list generator)

### 2.1 Source configuration

- `repoURL`: `https://github.com/ilyalinhnguyen/DevOps-Core-Course.git`
- `targetRevision`: `lab14`
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
kubectl create namespace dev --dry-run=client -o yaml | kubectl apply -f -
kubectl create namespace prod --dry-run=client -o yaml | kubectl apply -f -
kubectl get namespace dev prod
```

Output:

```text
NAME   STATUS   AGE
dev    Active   18m
prod   Active   9d
```

### 3.2 Apply ArgoCD Application manifests

```bash
kubectl apply -f k8s/argocd/application.yaml
kubectl apply -f k8s/argocd/application-dev.yaml
kubectl apply -f k8s/argocd/application-prod.yaml
```

Output (representative):

```text
application.argoproj.io/devops-info created
application.argoproj.io/devops-info-dev configured
application.argoproj.io/devops-info-prod configured
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

Workloads now use **`Rollout`** (Lab 14), not `Deployment`.

```bash
kubectl get application -n argocd -o custom-columns='NAME:.metadata.name,SYNC:.status.sync.status,HEALTH:.status.health.status,REVISION:.status.sync.revision'
kubectl get rollout -A
kubectl get pods -n default -l app.kubernetes.io/instance=devops-info
kubectl get pods -n dev -l app.kubernetes.io/instance=devops-info-dev
kubectl get pods -n prod -l app.kubernetes.io/instance=devops-info-prod
kubectl get svc -n default devops-info
kubectl get svc -n dev devops-info-dev
kubectl get svc -n prod devops-info-prod
```

Verification output:

```text
NAME               SYNC     HEALTH    REVISION
devops-info        Synced   Healthy   5884a3a6eb7e777937ef532a889d24e8ea95e212
devops-info-dev    Synced   Healthy   5884a3a6eb7e777937ef532a889d24e8ea95e212
devops-info-prod   Synced   Healthy   5884a3a6eb7e777937ef532a889d24e8ea95e212
```

```text
NAMESPACE   NAME               DESIRED   CURRENT   UP-TO-DATE   AVAILABLE   AGE
default     devops-info        3         3         3            3           12m
dev         devops-info-dev    1         1         1            1           15m
prod        devops-info-prod   3         3         3            3           13m
```

```text
NAME                          READY   STATUS    RESTARTS   AGE
devops-info-c45cbbfb8-42lmn   1/1     Running   0          2m51s
devops-info-c45cbbfb8-59m29   1/1     Running   0          2m51s
devops-info-c45cbbfb8-q5smb   1/1     Running   0          2m51s
```

```text
NAME                               READY   STATUS    RESTARTS   AGE
devops-info-dev-749d6d7987-ssg4t   1/1     Running   0          15m
```

```text
NAME                               READY   STATUS    RESTARTS   AGE
devops-info-prod-57bf997bc-lkx6c   1/1     Running   0          13m
devops-info-prod-57bf997bc-pfl2w   1/1     Running   0          13m
devops-info-prod-57bf997bc-vx55v   1/1     Running   0          13m
```

```text
NAME          TYPE       CLUSTER-IP   EXTERNAL-IP   PORT(S)        AGE
devops-info   NodePort   10.97.14.9   <none>        80:31793/TCP   13m
```

```text
NAME              TYPE       CLUSTER-IP      EXTERNAL-IP   PORT(S)        AGE
devops-info-dev   NodePort   10.106.211.98   <none>        80:30198/TCP   17m
```

```text
NAME               TYPE       CLUSTER-IP       EXTERNAL-IP   PORT(S)        AGE
devops-info-prod   NodePort   10.111.241.242   <none>        80:32316/TCP   9d
```

## 4. Self-healing and sync behavior

### 4.1 Manual scale drift test (ArgoCD self-healing)

1. Confirm desired replica count is from `values-dev.yaml`.
2. Scale the Rollout manually:

```bash
kubectl scale rollout devops-info-dev -n dev --replicas=5
kubectl argo rollouts get rollout devops-info-dev -n dev --watch
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
kubectl label rollout devops-info-dev -n dev drift-test=true --overwrite
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
# 1) Install or upgrade ArgoCD
helm repo add argo https://argoproj.github.io/argo-helm
helm repo update
kubectl create namespace argocd --dry-run=client -o yaml | kubectl apply -f -
helm upgrade --install argocd argo/argo-cd --namespace argocd --wait --timeout 10m

# 2) Login
kubectl port-forward svc/argocd-server -n argocd 8080:443
argocd login localhost:8080 --insecure

# 3) Namespaces + apps (includes default `devops-info` from application.yaml)
kubectl create namespace dev --dry-run=client -o yaml | kubectl apply -f -
kubectl create namespace prod --dry-run=client -o yaml | kubectl apply -f -
kubectl apply -f k8s/argocd/application.yaml
kubectl apply -f k8s/argocd/application-dev.yaml
kubectl apply -f k8s/argocd/application-prod.yaml

# 4) Verify
kubectl get application -n argocd -o wide
kubectl get rollout -A
kubectl get pods -n default -l app.kubernetes.io/instance=devops-info
kubectl get pods -n dev -l app.kubernetes.io/instance=devops-info-dev
kubectl get pods -n prod -l app.kubernetes.io/instance=devops-info-prod
```

## 7. Screenshot checklist

![alt](/k8s/assets/Screenshot%202026-04-20%20at%2020.20.14.png)
![alt](/k8s/assets/Screenshot%202026-04-20%20at%2020.22.53.png)
![alt](/k8s/assets/Screenshot%202026-04-20%20at%2020.23.06.png)