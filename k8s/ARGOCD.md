# Lab 13 — GitOps with ArgoCD

## 1. ArgoCD setup

### Installation
```bash
helm repo add argo https://argoproj.github.io/argo-helm
helm repo update
kubectl create namespace argocd
helm install argocd argo/argo-cd --namespace argocd
```

Installation result:
```bash
NAME: argocd
NAMESPACE: argocd
STATUS: deployed
REVISION: 1
```

Cluster readiness:
```bash
$ kubectl get pods -n argocd
NAME                                                READY   STATUS
argocd-application-controller-0                     1/1     Running
argocd-applicationset-controller-754f66bd99-vbz2g   1/1     Running
argocd-dex-server-5584f66c5d-nhx9j                  1/1     Running
argocd-notifications-controller-7646987985-kvw6b    1/1     Running
argocd-redis-7c845cf5b9-6znzk                       1/1     Running
argocd-repo-server-7c9654f7b-slnpc                  1/1     Running
argocd-server-5f649867b4-c92ns                      1/1     Running
```

### UI/CLI access
```bash
kubectl port-forward svc/argocd-server -n argocd 8080:443
kubectl -n argocd get secret argocd-initial-admin-secret -o jsonpath="{.data.password}" | base64 -d
argocd login localhost:8080 --username admin --password '<password>' --insecure --grpc-web
argocd account get-user-info --grpc-web
```

CLI verification:
```bash
Logged In: true
Username: admin
Issuer: argocd
```

## 2. Application configuration

Created manifests:
- `k8s/argocd/application.yaml`
- `k8s/argocd/application-dev.yaml`
- `k8s/argocd/application-prod.yaml`

Key settings used:
- `repoURL`: `https://github.com/chomosuce/DevOps-Core-Course.git`
- `path`: `k8s/devops-info`
- `targetRevision` in manifests: `lab13`
- `dev` values file: `values-dev.yaml`
- `prod` values file: `values-prod.yaml`

Apply:
```bash
kubectl create namespace dev
kubectl create namespace prod
kubectl apply -f k8s/argocd
kubectl get applications.argoproj.io -n argocd -o wide
```

## 3. Multi-environment deployment

### Policy difference
- `dev`: automated sync + `prune: true` + `selfHeal: true`
- `prod`: manual sync only

This split is intentional:
- `dev` auto-sync gives fast feedback and automatic reconciliation.
- `prod` manual sync keeps release timing controlled and reduces accidental impact.

### Runtime note for this repository state
At execution time, remote branch `lab13` was not published yet, so ArgoCD showed:
```bash
ComparisonError: unable to resolve 'lab13' to a commit SHA
```

To complete end-to-end runtime tests, app revision was temporarily switched in ArgoCD runtime to already existing remote branch `lab12`:
```bash
argocd app set devops-info-dev --revision lab12 --grpc-web
argocd app set devops-info-prod --revision lab12 --grpc-web
argocd app sync devops-info-dev --grpc-web
argocd app sync devops-info-prod --grpc-web
```

Current app state:
```bash
$ argocd app list --grpc-web
NAME                     STATUS   HEALTH       SYNCPOLICY
argocd/devops-info       Unknown  Healthy      Manual
argocd/devops-info-dev   Synced   Healthy      Auto-Prune
argocd/devops-info-prod  Synced   Progressing  Manual
```

(`prod` is `Progressing` in kind because `values-prod.yaml` uses `LoadBalancer` service type and external IP is pending in local cluster.)

## 4. Self-healing and drift behavior

### 4.1 Manual scale drift (ArgoCD self-heal)
```bash
before 2026-04-23T10:52:23Z: replicas=1
kubectl scale deployment devops-info-dev -n dev --replicas=5
scaled 2026-04-23T10:52:24Z: replicas=5
reconciled 2026-04-23T10:52:27Z: replicas=1
```

### 4.2 Pod deletion (Kubernetes self-heal)
```bash
old pod: devops-info-dev-75588c454d-5zdx6
kubectl delete pod devops-info-dev-75588c454d-5zdx6 -n dev
new pod: devops-info-dev-75588c454d-g7cjs
```

### 4.3 Config drift (ArgoCD self-heal)
```bash
kubectl set image deployment/devops-info-dev -n dev devops-info=nginx:1.27-alpine
patched-image 2026-04-23T10:57:37Z: nginx:1.27-alpine
reverted-image 2026-04-23T10:57:40Z: devops_lab02:latest
```

### 4.4 Sync behavior summary
- Kubernetes self-heal: recreates failed/deleted pods to satisfy ReplicaSet/Deployment desired pod count.
- ArgoCD self-heal: reverts declarative config drift to match Git state.
- ArgoCD sync triggers: Git revision change, manual sync, or drift reconciliation for automated apps.
- Default ArgoCD repo polling interval: ~3 minutes (webhooks can make it near-real-time).

## 5. UI screenshots requirement

Headless environment was used for execution, so evidence is provided via CLI output above.
For submission screenshots, capture these UI pages while port-forward is active:
1. Applications list with `devops-info-dev` and `devops-info-prod`
2. Application details page (`Sync`, `Health`, `History`)
3. Diff/operation timeline for self-heal event
