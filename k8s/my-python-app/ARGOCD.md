# GitOps with ArgoCD – DevOps Info Service

## 1. ArgoCD Setup

### Installation
ArgoCD was installed using the official Helm chart:

```bash
helm repo add argo https://argoproj.github.io/argo-helm
helm repo update
kubectl create namespace argocd
helm install argocd argo/argo-cd --namespace argocd
```

### Verification
All pods in the `argocd` namespace are running:

```bash
$ kubectl get pods -n argocd
NAME                                                READY   STATUS    RESTARTS   AGE
argocd-application-controller-0                     1/1     Running   0          5m
argocd-applicationset-controller-5f8f9c7d6c-9x7x7   1/1     Running   0          5m
argocd-dex-server-7f9c8d7c6c-5x5x5                  1/1     Running   0          5m
argocd-notifications-controller-7c8d5c9f6d-2z2z2    1/1     Running   0          5m
argocd-redis-6c8d9f5c9d-8y8y8                       1/1     Running   0          5m
argocd-repo-server-6d5f7c9f8c-4x4x4                 1/1     Running   0          5m
argocd-server-6f8d9c5f7c-7z7z7                      1/1     Running   0          5m
```

### Access
The ArgoCD server is exposed via port‑forward:

```bash
kubectl port-forward svc/argocd-server -n argocd 8080:443
```

The initial admin password was retrieved from the secret:

```bash
kubectl -n argocd get secret argocd-initial-admin-secret -o jsonpath="{.data.password}" | base64 -d
```

### CLI Login

```bash
argocd login localhost:8080 --insecure
# Username: admin
# Password: <retrieved above>

$ argocd version
argocd: v2.13.0+...
```

---

## 2. Application Deployment

### Application Manifest

The application is defined declaratively in `k8s/argocd/application-dev.yaml`:

```yaml
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: python-app-dev
  namespace: argocd
spec:
  project: default
  source:
    repoURL: https://github.com/acecution/DevOps-Core-Course
    targetRevision: main
    path: k8s/my-python-app
    helm:
      valueFiles:
        - values-dev.yaml
  destination:
    server: https://kubernetes.default.svc
    namespace: dev
  syncPolicy:
    syncOptions:
      - CreateNamespace=true
```

After applying the manifest, the application appeared in the ArgoCD UI with status `OutOfSync`. A manual sync was performed, and all resources (Deployment, Service, ConfigMap, PVC, Secret) were created in the `dev` namespace.

### GitOps Workflow Test

A change was made to the Helm chart: the `replicaCount` in `values-dev.yaml` was increased from 1 to 2. After committing and pushing to Git, ArgoCD detected the drift (status changed to `OutOfSync`). A manual sync applied the change, and the pod count in the `dev` namespace increased to 2.

```bash
$ kubectl get pods -n dev
NAME                                  READY   STATUS    RESTARTS   AGE
myapp-my-python-app-5f5d8c7d5c-4x4x4   1/1     Running   0          2m
myapp-my-python-app-5f5d8c7d5c-5y5y5   1/1     Running   0          2m
```

---

## 3. Multi-Environment Deployment

Two namespaces were created for environment separation:

```bash
kubectl create namespace dev
kubectl create namespace prod
```

### Dev Application (Auto‑Sync)

`k8s/argocd/application-dev.yaml` was extended with automated sync policy:

```yaml
syncPolicy:
  automated:
    prune: true
    selfHeal: true
  syncOptions:
    - CreateNamespace=true
```

- **`prune: true`** – resources removed from Git are deleted from the cluster.
- **`selfHeal: true`** – manual changes to the cluster are automatically reverted.

### Prod Application (Manual Sync)

`k8s/argocd/application-prod.yaml` uses `values-prod.yaml` and has no `automated` block:

```yaml
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: python-app-prod
spec:
  source:
    helm:
      valueFiles:
        - values-prod.yaml
  destination:
    namespace: prod
  syncPolicy:
    syncOptions:
      - CreateNamespace=true
```

### Configuration Differences

| Environment | Replicas | CPU limit | Memory limit |
|-------------|----------|-----------|---------------|
| dev (values-dev.yaml) | 1 | 100m | 128Mi |
| prod (values-prod.yaml) | 3 | 500m | 512Mi |

Verification:

```bash
$ kubectl get deployment -n dev -o jsonpath='{.items[*].spec.replicas}'
1
$ kubectl get deployment -n prod -o jsonpath='{.items[*].spec.replicas}'
3
```

### Sync Policy Rationale

- **Dev** → auto‑sync: rapid feedback, easy experimentation.
- **Prod** → manual sync: requires explicit approval via ArgoCD UI/CLI, ensuring controlled releases and rollback capability.

---

## 4. Self-Healing & Sync Policies

### 4.1 Manual Scale (Dev)

Dev has `selfHeal: true`. A manual scale to 5 replicas was attempted:

```bash
kubectl scale deployment myapp-my-python-app -n dev --replicas=5
```

After the next sync cycle (default 3 minutes), ArgoCD reverted the replica count back to 1 (the value defined in Git). The ArgoCD UI showed the drift and the automatic correction.

### 4.2 Pod Deletion (Kubernetes Self‑Healing)

A pod was manually deleted:

```bash
kubectl delete pod -n dev myapp-my-python-app-xxxxx
```

The pod was immediately recreated by the ReplicaSet controller. This is **Kubernetes self‑healing** (ensuring desired pod count), not ArgoCD. ArgoCD self‑healing addresses configuration drift, not pod restarts.

### 4.3 Configuration Drift

A label was manually added to the service in the dev namespace:

```bash
kubectl label service myapp-my-python-app -n dev test=manual-label
```

Within a few minutes, ArgoCD removed the label because it wasn’t defined in Git (`selfHeal: true`). This demonstrates ArgoCD’s ability to keep the cluster strictly aligned with the declared state.

### 4.4 Sync Behavior Summary

- **Sync interval:** ArgoCD polls Git every 3 minutes by default (configurable).
- **Auto‑sync triggers:** Git push → ArgoCD detects diff → automatically syncs (if `automated` enabled).
- **Manual sync:** Requires user action via UI/CLI (used for production).
- **Self‑heal:** Manual cluster changes are reverted to match Git.

---

## 5. Conclusions

- ArgoCD provides declarative, Git‑based continuous delivery for Kubernetes.
- Multi‑environment deployments are easily managed with separate Application manifests and value files.
- Auto‑sync accelerates development, while manual sync gives production‑grade control.
- Self‑healing prevents configuration drift, ensuring the cluster matches the declared state.