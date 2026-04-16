# Lab 13 — GitOps with ArgoCD

## 1. ArgoCD Setup

### 1.1 Installation via Helm

```bash
helm repo add argo https://argoproj.github.io/argo-helm
helm repo update
kubectl create namespace argocd
helm upgrade --install argocd argo/argo-cd -n argocd
kubectl get pods -n argocd
kubectl wait --for=condition=ready pod -l app.kubernetes.io/name=argocd-server -n argocd --timeout=180s
```

Record the output of `kubectl get pods -n argocd` here.

### 1.2 Accessing the UI

```bash
kubectl port-forward svc/argocd-server -n argocd 8080:443
```

ArgoCD UI URL:

```text
https://localhost:8080
```

Username:

```text
admin
```

Initial password retrieval:

```bash
argocd admin initial-password -n argocd
```

Paste a masked version of the password retrieval output here.

### 1.3 CLI Installation and Login

Windows PowerShell:

```powershell
$version = (Invoke-RestMethod https://api.github.com/repos/argoproj/argo-cd/releases/latest).tag_name
$url = "https://github.com/argoproj/argo-cd/releases/download/" + $version + "/argocd-windows-amd64.exe"
Invoke-WebRequest -Uri $url -OutFile argocd.exe
```

Login:

```bash
argocd login localhost:8080 --insecure
argocd app list
```

Paste the output of `argocd app list` after login here.

## 2. Application Configuration

This lab uses ArgoCD `Application` manifests stored in `k8s/argocd/`.

### 2.1 Manual Application for Initial Deployment

File: `k8s/argocd/application.yaml`

```yaml
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: devops-info-service
  namespace: argocd
spec:
  project: default
  source:
    repoURL: https://github.com/<YOUR_GITHUB_USERNAME>/<YOUR_REPOSITORY>.git
    targetRevision: main
    path: k8s/devops-info-service
    helm:
      valueFiles:
        - values.yaml
  destination:
    server: https://kubernetes.default.svc
    namespace: default
  syncPolicy:
    syncOptions:
      - CreateNamespace=true
```

Apply it:

```bash
kubectl apply -f k8s/argocd/application.yaml
argocd app get devops-info-service
argocd app sync devops-info-service
kubectl get all -n default
```

Explain in the report:
- `repoURL` points to the Git repository that stores the Helm chart.
- `targetRevision` is the Git branch tracked by ArgoCD.
- `path` points to the Helm chart inside the repository.
- `valueFiles` tells ArgoCD which Helm values file to render.
- This first application uses manual sync.

### 2.2 GitOps Workflow Test

Make a small Git change, for example in `values.yaml`:
- change `replicaCount`, or
- change a resource limit, or
- change an environment variable.

Then commit and push:

```bash
git add .
git commit -m "lab13: test GitOps sync"
git push
```

Check the application state:

```bash
argocd app get devops-info-service
argocd app diff devops-info-service
```

If it becomes `OutOfSync`, sync it manually:

```bash
argocd app sync devops-info-service
```

## 3. Multi-Environment Deployment

### 3.1 Namespaces

```bash
kubectl apply -f k8s/argocd/namespaces.yaml
kubectl get ns dev prod
```

### 3.2 Dev Application (Auto-Sync)

File: `k8s/argocd/application-dev.yaml`

```yaml
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: devops-info-service-dev
  namespace: argocd
spec:
  project: default
  source:
    repoURL: https://github.com/<YOUR_GITHUB_USERNAME>/<YOUR_REPOSITORY>.git
    targetRevision: main
    path: k8s/devops-info-service
    helm:
      valueFiles:
        - values-dev.yaml
  destination:
    server: https://kubernetes.default.svc
    namespace: dev
  syncPolicy:
    automated:
      prune: true
      selfHeal: true
    syncOptions:
      - CreateNamespace=true
```

### 3.3 Prod Application (Manual Sync)

File: `k8s/argocd/application-prod.yaml`

```yaml
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: devops-info-service-prod
  namespace: argocd
spec:
  project: default
  source:
    repoURL: https://github.com/<YOUR_GITHUB_USERNAME>/<YOUR_REPOSITORY>.git
    targetRevision: main
    path: k8s/devops-info-service
    helm:
      valueFiles:
        - values-prod.yaml
  destination:
    server: https://kubernetes.default.svc
    namespace: prod
  syncPolicy:
    syncOptions:
      - CreateNamespace=true
```

Apply both:

```bash
kubectl apply -f k8s/argocd/application-dev.yaml
kubectl apply -f k8s/argocd/application-prod.yaml
argocd app list
```

Initial sync:

```bash
argocd app sync devops-info-service-dev
argocd app sync devops-info-service-prod
kubectl get pods -n dev
kubectl get pods -n prod
```

In the report explain:
- `dev` uses `values-dev.yaml` and automatic sync.
- `prod` uses `values-prod.yaml` and manual sync.
- Separate namespaces isolate the environments.
- Manual sync for production is safer because changes are reviewed before rollout.

## 4. Self-Healing Evidence

### 4.1 Manual Scale Test in Dev

Check the current replica count:

```bash
kubectl get deploy -n dev
argocd app get devops-info-service-dev
```

Scale manually to an incorrect value:

```bash
kubectl scale deployment dev-release-devops-info-service -n dev --replicas=5
kubectl get pods -n dev -w
```

Observe ArgoCD reconciling it back to the Git-defined value.

Capture:
- time when you ran the scale command;
- time when ArgoCD returned the deployment to the value from Git;
- `argocd app get devops-info-service-dev` output;
- optional `argocd app diff devops-info-service-dev` output.

### 4.2 Pod Deletion Test

```bash
kubectl delete pod -n dev -l app.kubernetes.io/instance=dev-release
kubectl get pods -n dev -w
```

Explain:
- this is Kubernetes self-healing via ReplicaSet / Deployment;
- this is not ArgoCD self-healing.

### 4.3 Configuration Drift Test

For example, add a label manually to the deployment:

```bash
kubectl label deployment dev-release-devops-info-service -n dev drift-test=manual
argocd app diff devops-info-service-dev
kubectl get deployment dev-release-devops-info-service -n dev --show-labels
```

Wait for ArgoCD to self-heal, then verify the label disappears:

```bash
kubectl get deployment dev-release-devops-info-service -n dev --show-labels
argocd app get devops-info-service-dev
```

### 4.4 Sync Behavior Explanation

Write in the report:
- Kubernetes self-healing restores Pods when controllers detect missing replicas.
- ArgoCD self-healing restores declarative configuration drift against Git.
- ArgoCD checks tracked repositories on a schedule and also reacts to manual syncs or webhooks.
- Auto-sync affects only applications with `automated` enabled.

## 5. Screenshots

Include screenshots of:
- ArgoCD login page or dashboard;
- the Applications list showing `devops-info-service-dev` and `devops-info-service-prod`;
- one application details page;
- a moment when dev is `OutOfSync` and then `Synced` again.

## 6. Conclusion

ArgoCD implements GitOps by treating Git as the source of truth for Kubernetes application manifests. In this lab, the application was deployed from a Helm chart, split into dev and prod environments, and tested for manual sync, automatic sync, and self-healing behavior.
