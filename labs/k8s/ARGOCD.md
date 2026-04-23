# Lab 13

## 1. ArgoCD Setup

### Installation Verification
- ArgoCD installed via `install.yaml` (manifest) in namespace `argocd`.

```bash
$ kubectl get pods -n argocd

NAME                                               READY   STATUS    RESTARTS      AGE
argocd-application-controller-0                    1/1     Running   1 (17h ago)   21h
argocd-applicationset-controller-668f9c6d4-ntnxg   1/1     Running   1 (17h ago)   21h
argocd-dex-server-7549479499-smzx7                 1/1     Running   1 (17h ago)   21h
argocd-notifications-controller-55968c55-vmnnl     1/1     Running   1 (17h ago)   21h
argocd-redis-85b4855b6b-g4jfl                      1/1     Running   1 (17h ago)   21h
argocd-repo-server-6757d647d5-hs92t                1/1     Running   1 (17h ago)   21h
argocd-server-67f8c8fb87-x87ww                     1/1     Running   1 (17h ago)   21h
```

### UI Access
- Port‑forward started:
```bash
kubectl port-forward svc/argocd-server -n argocd 8080:443
```

```bash
kubectl -n argocd get secret argocd-initial-admin-secret -o jsonpath="{.data.password}" | base64 -d
```

### CLI config
```bash
argocd login localhost:8080 --insecure --username admin --password <password>
'admin:login' logged in successfully
```

## 2. Application Configuration

`application.yaml`:

```bash
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: python-app
  namespace: argocd
spec:
  project: default
  source:
    repoURL: https://github.com/TheVex/DevOps-Core-Course.git
    targetRevision: lab13
    path: labs/k8s/simple-app-chart
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

## 3. Multi-Environment

### Differences
- Dev has less resources
- Dev has 1 replica, while prod has 5
- Dev is automated sync while prod is manual

### Sync policy
Dev (auto‑sync): Fast feedback, immediate deployment of changes.
Prod (manual): Controlled releases, human approval, compliance.

### Namespace separation

```bash
kubectl get pods -n dev
kubectl get pods -n prod
NAME                                         READY   STATUS    RESTARTS   AGE
python-app-dev-simple-app-867bc498f7-wqbq8   1/1     Running   0          79m
NAME                                          READY   STATUS    RESTARTS   AGE
python-app-prod-simple-app-59db9d558d-29nfk   1/1     Running   0          48m
python-app-prod-simple-app-59db9d558d-8tjwc   1/1     Running   0          49m
python-app-prod-simple-app-59db9d558d-krgs7   1/1     Running   0          48m
python-app-prod-simple-app-59db9d558d-vtnpz   1/1     Running   0          49m
python-app-prod-simple-app-59db9d558d-zbsv2   1/1     Running   0          49m

```

## Self-Healing Evidence

### Scale test

```bash
$ kubectl scale deployment python-app-dev-simple-app  -n dev --replicas=3

deployment.apps/python-app-dev-simple-app scaled

$ kubectl get pods -n dev -w

NAME                                           READY   STATUS      RESTARTS   AGE
python-app-dev-simple-app-867bc498f7-wqbq8     1/1     Running     0          81m
python-app-dev-simple-app-post-install-jqh8j   1/1     Running     0          5s
python-app-dev-simple-app-pre-install-wfslp    0/1     Completed   0          21s
python-app-dev-simple-app-post-install-jqh8j   0/1     Completed   0          12s
python-app-dev-simple-app-post-install-jqh8j   0/1     Completed   0          13s
python-app-dev-simple-app-post-install-jqh8j   0/1     Completed   0          14s
python-app-dev-simple-app-post-install-jqh8j   0/1     Completed   0          14s
python-app-dev-simple-app-pre-install-wfslp    0/1     Completed   0          30s
python-app-dev-simple-app-post-install-jqh8j   0/1     Completed   0          14s
python-app-dev-simple-app-pre-install-wfslp    0/1     Completed   0          30s

$ kubectl get pods -n dev -w
NAME                                         READY   STATUS    RESTARTS   AGE
python-app-dev-simple-app-867bc498f7-wqbq8   1/1     Running   0          81m
```

### Pod deletion test

```bash
$ kubectl delete pod -n dev -l app.kubernetes.io/name=simple-app

pod "python-app-dev-simple-app-867bc498f7-wqbq8" deleted from dev namespace

$ kubectl get pods -n dev -w

NAME                                         READY   STATUS    RESTARTS   AGE
python-app-dev-simple-app-867bc498f7-jt4k8   1/1     Running   0          12s
```
### Drift test

```bash
$ kubectl label service simple-app-service -n dev test=drift
service/simple-app-service labeled

$ kubectl get pods -n dev -w
NAME                                         READY   STATUS    RESTARTS   AGE
python-app-dev-simple-app-867bc498f7-jt4k8   1/1     Running   0          2m34s
```
### Explanation

Kubernetes self‑healing: Manages pod lifecycle (count, health) via controllers.

ArgoCD self‑healing: Reverts any manual change in cluster resources to match the Git state (when selfHeal is enabled).

### Screenshots

![Not synced](/labs/k8s/outofsync.png)
![Sync](/labs/k8s/all_sync.png)
![View](/labs/k8s/detail_view.png)