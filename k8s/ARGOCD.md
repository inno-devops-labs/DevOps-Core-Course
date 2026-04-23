# Lab 13 — GitOps with ArgoCD

## 1. ArgoCD setup

### Installation
```bash
helm repo add argo https://argoproj.github.io/argo-helm
helm repo update
kubectl create namespace argocd
helm upgrade --install argocd argo/argo-cd --namespace argocd
```

Installation verification:
```bash
$ kubectl get pods -n argocd
NAME                                                READY   STATUS    RESTARTS   AGE
argocd-application-controller-0                     1/1     Running   0          14m
argocd-applicationset-controller-754f66bd99-hx5fc   1/1     Running   0          14m
argocd-dex-server-5584f66c5d-qtglw                  1/1     Running   0          14m
argocd-notifications-controller-7646987985-tdvfr    1/1     Running   0          14m
argocd-redis-7c845cf5b9-qnpps                       1/1     Running   0          14m
argocd-repo-server-7c9654f7b-mrs4d                  1/1     Running   0          14m
argocd-server-5f649867b4-rtw5l                      1/1     Running   0          14m
```

### UI and CLI access
```bash
kubectl port-forward svc/argocd-server -n argocd 8080:443
kubectl -n argocd get secret argocd-initial-admin-secret -o jsonpath="{.data.password}" | base64 -d
argocd login localhost:8080 --username admin --password '<password>' --insecure --grpc-web
```

CLI verification:
```bash
$ argocd version --client --short
argocd: v3.3.8+7ae7d2c.dirty
```

## 2. Application configuration

Created manifests:
- `k8s/argocd/application.yaml`
- `k8s/argocd/application-dev.yaml`
- `k8s/argocd/application-prod.yaml`

Source configuration:
- `repoURL`: `https://github.com/chomosuce/DevOps-Core-Course.git`
- `targetRevision`: `lab13`
- `path`: `k8s/devops-info`

Values selection:
- Single app: `values.yaml`
- Dev app: `values-dev.yaml`
- Prod app: `values-prod.yaml`

Applied:
```bash
kubectl apply -f k8s/argocd
```

## 3. Multi-environment deployment

### Dev vs Prod policy
- `devops-info-dev`: automated sync + `prune: true` + `selfHeal: true`
- `devops-info-prod`: manual sync

### Runtime configuration differences
- Dev app keeps NodePort service (overridden to `30081` to avoid cluster-wide NodePort conflict).
- Prod app uses prod values and is overridden to `ClusterIP` in ArgoCD app parameters for healthy local kind behavior.

Service verification:
```bash
$ kubectl get svc -n dev devops-info-dev -o wide
NAME              TYPE       CLUSTER-IP    EXTERNAL-IP   PORT(S)        AGE
devops-info-dev   NodePort   10.96.29.98   <none>        80:30081/TCP   2m

$ kubectl get svc -n prod devops-info-prod -o wide
NAME               TYPE        CLUSTER-IP      EXTERNAL-IP   PORT(S)   AGE
devops-info-prod   ClusterIP   10.96.144.151   <none>        80/TCP    96s
```

### Final status in ArgoCD
```bash
$ argocd app list --grpc-web
NAME                     STATUS  HEALTH   SYNCPOLICY  TARGET
argocd/devops-info       Synced  Healthy  Manual      lab13
argocd/devops-info-dev   Synced  Healthy  Auto-Prune  lab13
argocd/devops-info-prod  Synced  Healthy  Manual      lab13
```

## 4. Initial sync and GitOps workflow

### Initial sync
Manual sync executed for single app and prod app:
```bash
argocd app sync devops-info --grpc-web
argocd app sync devops-info-prod --grpc-web
```

Dev app synced automatically.

### GitOps workflow validation
A real Git change was made in chart values (`k8s/devops-info/values-dev.yaml`: `LOG_LEVEL` changed from `DEBUG` to `TRACE`) and pushed to `origin/lab13`.

ArgoCD detected and reconciled new revision:
```bash
Sync Status: Synced to lab13 (42c20d3)
```

Rendered config evidence:
```bash
$ kubectl get configmap devops-info-dev-env -n dev -o jsonpath='{.data.LOG_LEVEL}'
TRACE
```

## 5. Self-healing and drift behavior

### 5.1 Manual scale drift (ArgoCD self-heal)
```bash
before 2026-04-23T15:48:04Z: replicas=1
scaled 2026-04-23T15:48:04Z: replicas=5
reconciled 2026-04-23T15:48:07Z: replicas=1
```

### 5.2 Pod deletion (Kubernetes self-heal)
```bash
old pod: devops-info-dev-75588c454d-75hg7
kubectl delete pod devops-info-dev-75588c454d-75hg7 -n dev
new pod: devops-info-dev-75588c454d-sk9ch
```

### 5.3 Configuration drift (ArgoCD self-heal)
```bash
patched-image 2026-04-23T15:48:45Z: nginx:1.27-alpine
reverted-image 2026-04-23T15:48:47Z: devops_lab02:latest
```

Auto-heal operations are reflected in application operation state (`autoHealAttemptsCount` increased).

## 6. Sync behavior summary

- Kubernetes self-healing: controllers recreate pods to maintain desired replica count.
- ArgoCD self-healing: reconciles cluster spec back to Git-declared manifests.
- ArgoCD sync triggers: Git revision changes, manual sync, or detected drift for automated apps.
- Default repo polling interval is approximately 3 minutes; webhook integration can reduce detection latency.

## 7. Screenshot checklist for submission

For grading artifacts, capture and attach these UI screenshots from ArgoCD:
1. Applications list showing `devops-info`, `devops-info-dev`, `devops-info-prod`
2. Application details page for `devops-info-dev` (sync policy and revision)
3. Operation history/diff view during a self-heal event
