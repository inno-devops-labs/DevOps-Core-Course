# Lab 13 - GitOps with ArgoCD

This document captures the Lab 13 ArgoCD setup, application manifests, multi-environment deployment model, and the self-healing checks required by the assignment.

## Task 1 - ArgoCD Setup

### Installation verification

ArgoCD is installed in the dedicated `argocd` namespace as a Helm release named `argocd`.

Verification commands:

```bash
helm repo add argo https://argoproj.github.io/argo-helm
helm repo update
kubectl create namespace argocd
helm install argocd argo/argo-cd --namespace argocd
kubectl wait --for=condition=ready pod -l app.kubernetes.io/name=argocd-server -n argocd --timeout=120s
kubectl get pods -n argocd
```

Repo manifests related to ArgoCD live in:

- `k8s/argocd/namespaces.yaml`
- `k8s/argocd/application.yaml`
- `k8s/argocd/application-dev.yaml`
- `k8s/argocd/application-prod.yaml`
- `k8s/argocd/applicationset.yaml`

Verified state on `2026-04-19`:

```text
$ helm list -n argocd
NAME    NAMESPACE  REVISION  STATUS    CHART         APP VERSION
argocd  argocd     1         deployed  argo-cd-9.5.2 v3.3.7

$ kubectl get pods -n argocd
argocd-application-controller-0                     1/1 Running
argocd-applicationset-controller-59f6b7dd64-q9xmj   1/1 Running
argocd-dex-server-7b9588c494-hp455                  1/1 Running
argocd-notifications-controller-8f6855454-jk2rg     1/1 Running
argocd-redis-dc6b586fc-4l27k                        1/1 Running
argocd-repo-server-5f4d44d9f8-rx4k9                 1/1 Running
argocd-server-5f777b877f-bt6xk                      1/1 Running
```

### UI access

Port-forward the ArgoCD API/UI service:

```bash
kubectl port-forward svc/argocd-server -n argocd 8080:443
```

Open:

```text
https://127.0.0.1:8080
```

Retrieve the initial admin password:

```bash
kubectl -n argocd get secret argocd-initial-admin-secret \
  -o jsonpath="{.data.password}" | base64 -d
```

Login details:

- Username: `admin`
- Password: value returned by the command above

### CLI setup

Example Linux installation:

```bash
curl -sSL -o /tmp/argocd \
  https://github.com/argoproj/argo-cd/releases/download/v3.3.7/argocd-linux-amd64
chmod +x /tmp/argocd
sudo mv /tmp/argocd /usr/local/bin/argocd
```

Login and verification:

```bash
/tmp/argocd login 127.0.0.1:8080 --insecure --grpc-web
/tmp/argocd app list --grpc-web
/tmp/argocd version --grpc-web
```

Verified CLI version:

```text
argocd: v3.3.7+035e855
argocd-server: v3.3.7
```

## Task 2 - Application Deployment

### Base application manifest

`k8s/argocd/application.yaml` defines the initial manual-sync ArgoCD `Application` for the Helm chart:

- `repoURL`: `https://github.com/setterwars/DevOps-Core-Course.git`
- `targetRevision`: `lab13`
- `path`: `k8s/myapp`
- `destination.namespace`: `default`
- `valueFiles`: `values.yaml`
- Sync mode: manual

Important local verification note:

- The repo manifests intentionally keep `repoURL: https://github.com/setterwars/DevOps-Core-Course.git` and `targetRevision: lab13`.
- The public GitHub remote did not expose a `lab13` branch during this session, so ArgoCD could not resolve that revision directly from GitHub.
- To complete the lab verification without changing the committed manifests, I exposed a temporary local bare Git mirror and patched the live `Application` objects in-cluster to:

```text
git://host.minikube.internal/DevOps-Core-Course.git
```

- Once `lab13` is pushed to GitHub, reapply the repo manifests or patch the live `repoURL` back to GitHub.

Apply it with:

```bash
kubectl apply -f k8s/argocd/application.yaml
```

Manual sync:

```bash
argocd app sync myapp
argocd app get myapp
```

### GitOps workflow

The application manifest points ArgoCD to the Git repository and Helm chart path, so deployment changes are driven by repository updates instead of manual `kubectl apply` changes to workload resources.

For this lab, one safe GitOps change is increasing or decreasing `replicaCount` in the relevant values file, committing the change, pushing it to the tracked branch, and then observing ArgoCD mark the application `OutOfSync` until the change is synced.

Verified ArgoCD application state after deployment:

```text
$ /tmp/argocd app list --grpc-web
argocd/myapp       default  Synced  Healthy      Manual
argocd/myapp-dev   dev      Synced  Healthy      Auto-Prune
argocd/myapp-prod  prod     Synced  Progressing  Manual
```

## Task 3 - Multi-Environment Deployment

### Namespaces

Separate environments are created with `k8s/argocd/namespaces.yaml`:

- `dev`
- `prod`

Apply them with:

```bash
kubectl apply -f k8s/argocd/namespaces.yaml
```

### Environment-specific applications

`k8s/argocd/application-dev.yaml`

- Namespace: `dev`
- Values files: `values.yaml`, `values-dev.yaml`
- Sync mode: automatic
- Auto options: `prune: true`, `selfHeal: true`

`k8s/argocd/application-prod.yaml`

- Namespace: `prod`
- Values files: `values.yaml`, `values-prod.yaml`
- Sync mode: manual

Apply them with:

```bash
kubectl apply -f k8s/argocd/application-dev.yaml
kubectl apply -f k8s/argocd/application-prod.yaml
```

Verified workloads:

```text
$ kubectl get deploy -n default myapp
myapp       2/2 available

$ kubectl get deploy -n dev myapp-dev
myapp-dev   1/1 available

$ kubectl get deploy -n prod myapp-prod
myapp-prod  5/5 available
```

### Configuration differences

| Environment | Namespace | Replicas | Service type | Service exposure | Resource limits | Sync policy |
|---|---|---:|---|---|---|---|
| base | `default` | 2 | `NodePort` | `30083` | `128Mi / 200m` | manual |
| dev | `dev` | 1 | `NodePort` | `30082` | `128Mi / 200m` | auto-sync + self-heal + prune |
| prod | `prod` | 5 | `LoadBalancer` | cluster assigned | `256Mi / 400m` | manual |

Notes:

- Base uses `nodePort: 30083` because the earlier `my-app-service` already owns `30080`.
- Dev uses `nodePort: 30082` so it can coexist with the base application NodePort in `default` and the previous Lab 12 release on `30081`.
- Prod stays manual because production changes should be reviewed and triggered deliberately.
- In local `minikube`, the prod `LoadBalancer` service stays `EXTERNAL-IP <pending>` unless `minikube tunnel` is running, so ArgoCD keeps prod health at `Progressing` even though all 5 pods are ready.

Observed services:

```text
default  my-app-service       NodePort     80:30080/TCP
default  lab12-myapp-service  NodePort     80:30081/TCP
default  myapp-service        NodePort     80:30083/TCP
dev      myapp-dev-service    NodePort     80:30082/TCP
prod     myapp-prod-service   LoadBalancer 80:31157/TCP  EXTERNAL-IP <pending>
```

## Task 4 - Self-Healing and Drift Detection

### Scale drift test

Manual scale drift in dev:

```bash
kubectl scale deployment myapp-dev -n dev --replicas=5
argocd app get myapp-dev
kubectl get deploy myapp-dev -n dev
```

Expected behavior:

- ArgoCD detects the live cluster drift from Git.
- Because `selfHeal: true` is enabled for dev, ArgoCD reconciles the deployment back to the replica count defined in `values-dev.yaml`.

Observed result:

```text
start=2026-04-19T19:47:47+03:00
before=1
after_manual_scale=5
restored=1
end=2026-04-19T19:48:01+03:00
```

ArgoCD restored the desired replica count in 14 seconds.

### Pod deletion test

```bash
kubectl delete pod -n dev -l app.kubernetes.io/instance=myapp-dev
kubectl get pods -n dev -w
```

Behavior:

- Kubernetes recreates the pod through the Deployment/ReplicaSet controller.
- This is Kubernetes self-healing, not ArgoCD drift correction.

Observed result:

```text
start=2026-04-19T19:48:16+03:00
deleted=myapp-dev-58b5ffd5f7-98h6f
recreated=myapp-dev-58b5ffd5f7-k6qgn
ready=true
end=2026-04-19T19:48:32+03:00
```

The replacement pod appeared and became ready in 16 seconds. That was Kubernetes Deployment/ReplicaSet behavior, not ArgoCD.

### Configuration drift test

```bash
kubectl patch service myapp-dev-service -n dev --type=json \
  -p='[{"op":"replace","path":"/spec/ports/0/nodePort","value":30084}]'
kubectl get svc myapp-dev-service -n dev
```

Behavior:

- ArgoCD detects the service spec change as configuration drift.
- Dev auto-sync restores the Git-defined `nodePort: 30082`.

Observed result:

```text
start=2026-04-19T19:50:27+03:00
before=30082
after_patch=30084
restored=30082
end=2026-04-19T19:50:29+03:00
```

This drift reverted in 2 seconds.

### When ArgoCD syncs vs when Kubernetes heals

- Kubernetes self-healing: recreates failed or deleted pods so the live replica count matches the Deployment spec.
- ArgoCD self-healing: restores live Kubernetes objects so they match the manifests stored in Git.

ArgoCD checks Git on a polling interval of roughly 3 minutes by default. Sync can also be triggered manually or accelerated through webhooks.

## Screenshots

Captured UI screenshots:

![](k8s/argocd/screenshots/argocd-login.png)
![](k8s/argocd/screenshots/argocd-apps.png)
![](k8s/argocd/screenshots/argocd-myapp-dev.png)
![](k8s/argocd/screenshots/argocd-myapp-prod.png)

What they show:

- `argocd-login.png`: the ArgoCD login page exposed through the local port-forward
- `argocd-apps.png`: all three applications with their sync/health summaries
- `argocd-myapp-dev.png`: the healthy dev tree view after auto-sync and self-healing
- `argocd-myapp-prod.png`: the prod tree view showing `Synced` but `Progressing` because the `LoadBalancer` service is still waiting for an external IP in minikube

## Bonus - ApplicationSet

`k8s/argocd/applicationset.yaml` contains a List-generator-based `ApplicationSet` for `dev` and `prod`.

Why this pattern helps:

- One template manages multiple similar applications.
- Environment-specific values stay explicit in the generator list.
- Sync behavior can still vary by environment through templating.

How to use it safely:

```bash
kubectl delete application myapp-dev myapp-prod -n argocd
kubectl apply -f k8s/argocd/applicationset.yaml
kubectl get applications -n argocd
```

The generated applications intentionally reuse the same names as the individual manifests, so delete the standalone `Application` objects first to avoid ownership conflicts.
