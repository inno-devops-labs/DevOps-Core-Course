## 1. ArgoCD Setup

### Installation via Helm

ArgoCD was installed using Argo Helm repository:

```bash
# Add ArgoCD Helm repository
helm repo add argo https://argoproj.github.io/argo-helm
helm repo update

# Create dedicated namespace and install
kubectl create namespace argocd
helm install argocd argo/argo-cd --namespace argocd
```

And then:
```bash
# Wait for pods
kubectl wait --for=condition=ready pod -l app.kubernetes.io/name=argocd-server -n argocd --timeout=120s
```

EVidence that pods are running successfully in argocd namespace:

```bash
NAME                                                READY   STATUS
argocd-application-controller-0                     1/1     Running
argocd-applicationset-controller-7f8c9d44c7-lm2pz   1/1     Running
argocd-dex-server-6b7f9cddc4-wkz8n                  1/1     Running
argocd-notifications-controller-5dcbf768c9-hq4tm    1/1     Running
argocd-redis-7fbc896fbd-rp9vk                       1/1     Running
argocd-repo-server-6f977dcb5b-qx7ls                 1/1     Running
argocd-server-6dfb8d4657-jr2hx                      1/1     Running
```

### ArgoCD UI

Evidence passw redacted:
```bash
kubectl -n argocd get secret argocd-initial-admin-secret -o jsonpath="{.data.password}" | base64 -d && echo
xxx
```

### Login via ArgoCD CLI

Login:
```bash
argocd login localhost:8080 --insecure
'admin:login' logged in successfully

argocd version
v3.3.8
```

Verify Connection:
```
argocd app list
argocd cluster list
```

## 2. App Config

All configs stored in `k8s/argocd`

**Manifests Key Fields:**
- `repoURL`: https://github.com/CacucoH/DevOps-Core-Course
- `targetRevision`: `lab13`
- `path`: `k8s/app-python`
- `destination.namespace`: default/dev/prod


### Notes:
`python-app` is configured with manual sync.
`python-app-dev` uses automated sync with prune: `true` and `selfHeal`: true to ensure continuous reconciliation.
`python-app-prod` remains on manual sync to provide controlled production releases.
For local Minikube testing, `python-app-prod` overrides `service.type=NodePort` to allow external access.

### Deployment Process

Apply app:
```bash
kubectl create namespace dev --dry-run=client -o yaml | kubectl apply -f -
kubectl create namespace prod --dry-run=client -o yaml | kubectl apply -f -
kubectl apply -f k8s/argocd/application.yaml -f k8s/argocd/application-dev.yaml -f k8s/argocd/application-prod.yaml
```

Check app status:
```bash
argocd app get python-app
```

Perform init Sync:
```bash
argocd app sync python-app
```

Deployment:
```bash
argocd app wait python-app --sync --health
```

Final result:
```bash
NAME                    STATUS  HEALTH       SYNCPOLICY
argocd/python-app       Synced  Healthy      Manual
argocd/python-app-dev   Synced  Healthy      Auto-Prune
argocd/python-app-prod  Synced  Healthy      Manual
```