# Lab 13 — GitOps with ArgoCD

## 1. Goal

In this lab the Helm chart from Labs 10-12 is managed by ArgoCD in a GitOps workflow.
Git becomes the source of truth, while ArgoCD continuously compares the desired state from the repository with the live state in the Kubernetes cluster.

This lab includes:
- ArgoCD installation via Helm
- access to UI and CLI
- declarative `Application` manifests
- separate dev/prod environments
- automatic sync and self-healing for dev
- manual sync for prod
- bonus `ApplicationSet`

---

## 2. Repository Structure

Added files:

```text
k8s/
├── ARGOCD.md
└── argocd/
    ├── application.yaml
    ├── application-dev.yaml
    ├── application-prod.yaml
    ├── applicationset.yaml
    └── namespaces.yaml
```

Notes:
- `application.yaml` is the single-application manifest for Task 2
- `application-dev.yaml` and `application-prod.yaml` are for Task 3
- `applicationset.yaml` is the bonus solution
- do not apply `applicationset.yaml` together with the individual dev/prod Application manifests

---

## 3. Prerequisites

Required locally:
- Docker Desktop
- Minikube
- kubectl
- Helm
- Homebrew

Recommended checks:

```bash
kubectl config current-context
kubectl get nodes
helm version
minikube status
```

Your application image must already exist inside Minikube, because the chart uses local image settings:

```yaml
image:
  repository: python-app
  tag: "latest"
  pullPolicy: Never
```

If needed, rebuild and load the image again:

```bash
docker build -t python-app:latest ./app_python
minikube image load python-app:latest
```

---

## 4. Install ArgoCD

### 4.1 Add Helm repository

```bash
helm repo add argo https://argoproj.github.io/argo-helm
helm repo update
```

### 4.2 Create namespace

```bash
kubectl create namespace argocd
```

If it already exists:

```bash
kubectl get ns argocd
```

### 4.3 Install ArgoCD from Helm chart

```bash
helm upgrade --install argocd argo/argo-cd -n argocd
```

### 4.4 Verify installation

```bash
kubectl get pods -n argocd
kubectl get svc -n argocd
kubectl wait --for=condition=ready pod -l app.kubernetes.io/part-of=argocd -n argocd --timeout=180s
```

Expected result:
- ArgoCD components are in `Running` or `Completed`
- `argocd-server`, `argocd-repo-server`, `argocd-application-controller`, `argocd-applicationset-controller` are present

---

## 5. Access ArgoCD UI and CLI

### 5.1 Port-forward the ArgoCD server

Check the actual service name first:

```bash
kubectl get svc -n argocd
```

Typical command:

```bash
kubectl port-forward svc/argocd-server -n argocd 8080:443
```

If Helm rendered another service name, use that name instead.

Open in browser:

```text
https://localhost:8080
```

### 5.2 Get initial admin password

```bash
kubectl -n argocd get secret argocd-initial-admin-secret \
  -o jsonpath="{.data.password}" | base64 -d && echo
```

Login credentials:
- username: `admin`
- password: output from the command above

### 5.3 Install ArgoCD CLI on macOS Apple Silicon

```bash
brew install argocd
argocd version --client
```

### 5.4 Login via CLI

```bash
argocd login localhost:8080 --insecure
```

Useful checks:

```bash
argocd account get-user-info
argocd app list
```

---

## 6. Task 2 — Single Application Deployment

### 6.1 Prepare the manifest

File:

```text
k8s/argocd/application.yaml
```

Before applying it, replace placeholders:
- `<YOUR_GITHUB_REPO_URL>`
- `<YOUR_GIT_BRANCH>`

Example:

```yaml
source:
  repoURL: https://github.com/your-user/your-repo.git
  targetRevision: main
  path: k8s/python-app
```

Important:
- the repository must contain the latest Helm chart files
- if the repository is private, add it to ArgoCD first via UI or CLI

### 6.2 Apply the Application manifest

```bash
kubectl apply -f k8s/argocd/application.yaml
argocd app list
argocd app get python-app
```

Expected initial state:
- application exists in ArgoCD
- sync status is likely `OutOfSync`
- health may be `Missing` or `Progressing` before first sync

### 6.3 Perform the initial sync

```bash
argocd app sync python-app
argocd app get python-app
```

### 6.4 Verify resources

```bash
kubectl get all -n default
kubectl get configmap,secret,pvc -n default
```

### 6.5 Access the application

The base `values.yaml` uses NodePort `30080`.

Check service:

```bash
kubectl get svc -n default
minikube service python-app -n default --url
```

Then test:

```bash
curl http://127.0.0.1:<PORT>/health
curl http://127.0.0.1:<PORT>/
curl http://127.0.0.1:<PORT>/visits
```

### 6.6 Test GitOps flow

Make a small change in Git, for example:
- change `replicaCount` in `k8s/python-app/values.yaml`
- or update `app.version`

Then:

```bash
git add .
git commit -m "Lab 13: change values for ArgoCD test"
git push
```

Observe:

```bash
argocd app get python-app
argocd app diff python-app
```

Manual sync again:

```bash
argocd app sync python-app
```

### 6.7 Clean up before Task 3

To avoid having an extra copy of the application in the `default` namespace, remove the Task 2 application before creating dev/prod apps:

```bash
argocd app delete python-app --cascade
kubectl delete -f k8s/argocd/application.yaml
```

---

## 7. Task 3 — Multi-Environment Deployment

### 7.1 Create namespaces

```bash
kubectl apply -f k8s/argocd/namespaces.yaml
kubectl get ns dev prod
```

### 7.2 Apply environment-specific Applications

Before applying, replace placeholders in both files:
- `k8s/argocd/application-dev.yaml`
- `k8s/argocd/application-prod.yaml`

Apply:

```bash
kubectl apply -f k8s/argocd/application-dev.yaml
kubectl apply -f k8s/argocd/application-prod.yaml
```

Check:

```bash
argocd app list
argocd app get python-app-dev
argocd app get python-app-prod
```

### 7.3 Sync behavior

#### Dev
`python-app-dev` uses:
- `values-dev.yaml`
- destination namespace `dev`
- automated sync enabled
- `prune: true`
- `selfHeal: true`

#### Prod
`python-app-prod` uses:
- `values-prod.yaml`
- destination namespace `prod`
- manual sync only

### 7.4 Verify both environments

```bash
kubectl get all -n dev
kubectl get configmap,secret,pvc -n dev
kubectl get all -n prod
kubectl get configmap,secret,pvc -n prod
```

Check important differences:
- replica count
- resources requests/limits
- app version
- service type / port exposure
- namespace separation

### 7.5 Access the environments

#### Dev
`values-dev.yaml` uses NodePort `30081`.

```bash
minikube service python-app-dev -n dev --url
curl http://127.0.0.1:<DEV_PORT>/health
curl http://127.0.0.1:<DEV_PORT>/visits
```

#### Prod
`values-prod.yaml` currently uses `LoadBalancer`.
For local Minikube verification, one of the following is convenient:

```bash
kubectl port-forward -n prod svc/python-app-prod 8082:80
curl http://127.0.0.1:8082/health
curl http://127.0.0.1:8082/visits
```

or:

```bash
minikube service python-app-prod -n prod --url
```

### 7.6 Why prod stays manual

Manual sync for production is a good practice because it gives:
- review before rollout
- controlled release timing
- safer change management
- simpler rollback planning
- reduced risk of pushing unreviewed changes directly to production

---

## 8. Task 4 — Self-Healing Tests

These tests should be done on `python-app-dev`, because auto-sync and self-heal are enabled there.

### 8.1 Scale drift test

Check current state:

```bash
kubectl get deploy -n dev
argocd app get python-app-dev
```

Scale the deployment manually:

```bash
kubectl scale deployment python-app-dev -n dev --replicas=5
```

Watch the recovery:

```bash
kubectl get pods -n dev -w
argocd app diff python-app-dev
argocd app get python-app-dev
```

Expected behavior:
- deployment becomes drifted relative to Git
- ArgoCD detects `OutOfSync`
- ArgoCD automatically returns replicas to the Git-defined value from `values-dev.yaml`

Document with timestamps in your report, for example:

```text
19:11:03 — deployment manually scaled to 5 replicas
19:11:20 — ArgoCD shows OutOfSync
19:12:05 — ArgoCD reconciles the application
19:12:20 — replicas return to 1, status becomes Synced/Healthy
```

### 8.2 Pod deletion test

Delete one pod:

```bash
kubectl delete pod -n dev -l app.kubernetes.io/name=python-app
kubectl get pods -n dev -w
```

Expected behavior:
- Kubernetes recreates the pod through Deployment/ReplicaSet
- this is Kubernetes self-healing, not ArgoCD self-healing

### 8.3 Configuration drift test

Patch the deployment with an extra label:

```bash
kubectl patch deployment python-app-dev -n dev \
  --type merge \
  -p '{"metadata":{"labels":{"manual-change":"true"}}}'
```

Observe the diff and recovery:

```bash
argocd app diff python-app-dev
argocd app get python-app-dev
kubectl get deployment python-app-dev -n dev --show-labels
```

Expected behavior:
- ArgoCD detects configuration drift
- self-heal removes the manual label and restores Git-defined state

---

## 9. ArgoCD Sync Behavior

### Kubernetes self-healing
Kubernetes restores failed or deleted pods to satisfy the Deployment/ReplicaSet desired state.

Example:
- pod was deleted
- Deployment controller creates a replacement pod

### ArgoCD self-healing
ArgoCD restores the cluster configuration to the state described in Git.

Example:
- replicas manually changed from 1 to 5
- manual label added to Deployment
- ArgoCD detects drift and re-applies the desired manifest

### What triggers ArgoCD sync
- manual sync from UI or CLI
- automatic sync for apps with `automated` policy
- drift detection after repository polling
- drift detection when live cluster state no longer matches desired manifests

### Sync interval
By default, ArgoCD checks the tracked repository roughly every 3 minutes.
It is effectively controlled by `timeout.reconciliation` with additional jitter.

---

## 10. Screenshots to Include

Recommended screenshots for submission:
- ArgoCD Applications page showing `python-app-dev` and `python-app-prod`
- one application details page with sync and health status
- diff or OutOfSync state during drift test
- recovered Synced/Healthy state after self-heal

---

## 11. Bonus — ApplicationSet

File:

```text
k8s/argocd/applicationset.yaml
```

This manifest uses:
- `List` generator
- parameters for `dev` and `prod`
- `goTemplate: true`
- `templatePatch` to enable auto-sync only for dev

### Apply bonus solution

First remove individual Application manifests if they are already applied:

```bash
kubectl delete -f k8s/argocd/application-dev.yaml
kubectl delete -f k8s/argocd/application-prod.yaml
```

Then apply the ApplicationSet:

```bash
kubectl apply -f k8s/argocd/applicationset.yaml
kubectl get applicationset -n argocd
argocd app list
```

Expected result:
- `python-app-dev` is generated automatically
- `python-app-prod` is generated automatically
- the dev app has automated sync
- the prod app remains manual

### Why ApplicationSet is useful

Benefits over separate Application manifests:
- less duplication
- one template for many environments
- easier scaling to more namespaces/clusters/apps
- consistent naming and policy patterns

When to use:
- **List generator**: small fixed set of environments
- **Git generator**: discover apps or folders from repository structure
- **Cluster generator**: deploy to many clusters
- **Matrix generator**: combine environments with clusters or app lists

---

## 12. Suggested Verification Commands Summary

```bash
kubectl get pods -n argocd
kubectl get svc -n argocd
argocd app list
argocd app get python-app-dev
argocd app get python-app-prod
kubectl get all -n dev
kubectl get all -n prod
kubectl get configmap,secret,pvc -n dev
kubectl get configmap,secret,pvc -n prod
argocd app diff python-app-dev
```

---

## 13. Conclusion

Implemented in this lab:
- ArgoCD installed via Helm
- UI and CLI access configured
- Git repository used as the source of truth
- application deployed through ArgoCD `Application` manifests
- separate dev/prod environments created
- auto-sync and self-healing enabled for dev
- manual sync preserved for prod
- bonus `ApplicationSet` prepared for templated multi-environment deployment
