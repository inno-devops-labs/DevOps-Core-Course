# LAB13 - GitOps with ArgoCD

Cluster: `minikube`  
ArgoCD namespace: `argocd`

## 1. ArgoCD Setup

### 1.1 Installation (Helm)

Commands used:

```bash
helm repo add argo https://argoproj.github.io/argo-helm
helm repo update
kubectl create namespace argocd
helm upgrade --install argocd argo/argo-cd -n argocd --wait --timeout 15m
kubectl wait --for=condition=Ready pod -l app.kubernetes.io/part-of=argocd -n argocd --timeout=300s
```

Verification:

```text
NAME                                                READY   STATUS    RESTARTS   AGE
argocd-application-controller-0                     1/1     Running   0          ...
argocd-applicationset-controller-754f66bd99-g6jqr   1/1     Running   0          ...
argocd-dex-server-5584f66c5d-x69tr                  1/1     Running   0          ...
argocd-notifications-controller-7646987985-w5zcq    1/1     Running   0          ...
argocd-redis-7c845cf5b9-dzrjt                       1/1     Running   0          ...
argocd-repo-server-7c9654f7b-4dddm                  1/1     Running   0          ...
argocd-server-5f649867b4-597l6                      1/1     Running   0          ...
```

### 1.2 UI Access

Port-forward command:

```bash
kubectl port-forward svc/argocd-server -n argocd 8080:443
```

Observed:

```text
Forwarding from 127.0.0.1:8080 -> 8080
```

Initial admin password retrieval:

```bash
kubectl -n argocd get secret argocd-initial-admin-secret -o jsonpath='{.data.password}' | base64 -d
```

Login:
- URL: `https://localhost:8080`
- Username: `admin`
- Password: value from secret above

### 1.3 ArgoCD CLI

Installed CLI binary:

```bash
curl -4 --connect-timeout 20 --max-time 180 -fL -o /tmp/argocd https://github.com/argoproj/argo-cd/releases/latest/download/argocd-linux-amd64
chmod +x /tmp/argocd
/tmp/argocd version --client
```

Output:

```text
argocd: v3.3.8+7ae7d2c
BuildDate: 2026-04-21T17:45:55Z
Platform: linux/amd64
```

CLI login used:

```bash
PASS=$(kubectl -n argocd get secret argocd-initial-admin-secret -o jsonpath='{.data.password}' | base64 -d)
/tmp/argocd login argocd-server --username admin --password "$PASS" --insecure --grpc-web --port-forward --port-forward-namespace argocd
```

CLI verification:

```text
Logged In: true
Username: admin
Issuer: argocd
```

## 2. Application Configuration

Created manifests:
- `k8s/argocd/application.yaml`
- `k8s/argocd/application-dev.yaml`
- `k8s/argocd/application-prod.yaml`

Source and destination:
- `repoURL`: `https://github.com/Rash1d1/DevOps-Core-Course.git`
- `targetRevision`: `lab12` (this branch contains `k8s/devops-info`)
- `path`: `k8s/devops-info`
- destination server: `https://kubernetes.default.svc`
- namespaces: `default`, `dev`, `prod`

Notes:
- `python-app` is manual sync.
- `python-app-dev` uses auto-sync with `prune: true` and `selfHeal: true`.
- `python-app-prod` remains manual sync.
- For prod, `values-prod.yaml` image tag `1.0.0` was unavailable in registry, so `application-prod.yaml` adds Helm parameter `image.tag=lab02` to keep deployment healthy.
- For local minikube health checks, prod also overrides `service.type=NodePort`.

Apply commands:

```bash
kubectl create namespace dev --dry-run=client -o yaml | kubectl apply -f -
kubectl create namespace prod --dry-run=client -o yaml | kubectl apply -f -
kubectl apply -f k8s/argocd/application.yaml -f k8s/argocd/application-dev.yaml -f k8s/argocd/application-prod.yaml
```

Manual syncs performed:

```bash
/tmp/argocd --port-forward --port-forward-namespace argocd --insecure --grpc-web app sync python-app
/tmp/argocd --port-forward --port-forward-namespace argocd --insecure --grpc-web app sync python-app-prod
```

Application list:

```text
NAME                    STATUS  HEALTH       SYNCPOLICY
argocd/python-app       Synced  Healthy      Manual
argocd/python-app-dev   Synced  Healthy      Auto-Prune
argocd/python-app-prod  Synced  Healthy      Manual
```

### 2.1 GitOps workflow check

During setup, source revision was first set to `master`, where `k8s/devops-info` is absent in remote repo, so ArgoCD reported:

```text
ComparisonError: k8s/devops-info: app path does not exist
```

After updating manifests to `targetRevision: lab12` and reapplying, apps moved to `OutOfSync`, then to `Synced` after reconciliation/sync.  
This validates ArgoCD drift detection and reconciliation based on Git source revision/path.

## 3. Multi-Environment Deployment

### 3.1 Environment split

- `dev` app:
  - values file: `values-dev.yaml`
  - sync policy: auto (`prune`, `selfHeal`)
  - expected replicas: 1
- `prod` app:
  - values file: `values-prod.yaml` (+ image tag override to `lab02`)
  - sync policy: manual
  - expected replicas: 3

### 3.2 Verification

```text
dev replicas=1 ready=1 image=j0cos/devops-info-service:lab02
prod replicas=3 ready=3 image=j0cos/devops-info-service:lab02
default replicas=3 ready=3 image=j0cos/devops-info-service:lab02
```

Sync policy verification:

```text
syncPolicy automated.prune=true automated.selfHeal=true
prod has automated=
```

### 3.3 Why prod is manual

- Explicit review/approval gate before production rollout
- Better control of release timing
- Safer incident handling and rollback decisions

## 4. Self-Healing and Drift Tests

### 4.1 Manual scale drift (ArgoCD self-healing)

Commands:

```bash
kubectl scale deployment -n dev python-app-dev-devops-info --replicas=5
```

Observed timeline:

```text
before 2026-04-23T17:57:26+03:00 spec=1 ready=1 sync=Synced
2026-04-23T17:57:26+03:00 spec=5 ready=1 sync=Synced health=Healthy
2026-04-23T17:57:32+03:00 spec=1 ready=1 sync=Synced health=Healthy
```

Result: deployment spec was auto-reverted from 5 to Git-defined 1 in ~6 seconds.

### 4.2 Pod deletion test (Kubernetes self-healing)

Commands:

```bash
kubectl delete pod -n dev <pod-name>
```

Observed:

```text
before 2026-04-23T17:57:44+03:00 pod=python-app-dev-devops-info-6fcc8b7c5d-5x5pj
pod "...-5x5pj" deleted
2026-04-23T17:58:15+03:00 pods=python-app-dev-devops-info-6fcc8b7c5d-bqgq8:Running
```

Result: ReplicaSet recreated a new pod automatically. This is Kubernetes controller behavior, not ArgoCD sync.

### 4.3 Configuration drift test

Tested by forcing runtime image change:

```bash
kubectl set image deployment/python-app-dev-devops-info -n dev app=nginx:1.27.1
```

Observed:

```text
before 2026-04-23T18:02:01+03:00 image=j0cos/devops-info-service:lab02 sync=Synced
deployment.apps/python-app-dev-devops-info image updated
after_patch 2026-04-23T18:02:03+03:00 image=j0cos/devops-info-service:lab02 sync=Synced
image_reverted_at=2026-04-23T18:02:04+03:00
```

Result: self-heal reverted deployment image back to Git state almost immediately.

ArgoCD event evidence for automated reconciliation:

```text
OperationStarted     application/python-app-dev  Initiated automated sync to '32e96c4...'
OperationCompleted   application/python-app-dev  Partial sync operation to 32e96c4... succeeded
```

## 5. Sync Behavior Summary

### 5.1 What triggers ArgoCD sync

- Manual sync (`argocd app sync ...`)
- Automated sync for apps with `spec.syncPolicy.automated`
- Live-state drift reconciliation when `selfHeal: true` is enabled
- Git polling cycle

### 5.2 ArgoCD vs Kubernetes healing

- Kubernetes healing: restores pod count/pods from Deployment/ReplicaSet desired state.
- ArgoCD healing: restores Kubernetes object spec to Git-defined manifest values.

### 5.3 Sync interval in this installation

From `argocd-cm`:

```text
timeout.reconciliation: 120s
timeout.reconciliation.jitter: 60s
```

So repo reconciliation is roughly every 2-3 minutes (unless sync is triggered manually or by live drift/self-heal).

## 6. Screenshots

1.png
2.png

