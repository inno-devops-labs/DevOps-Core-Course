# Lab 13 - GitOps with ArgoCD

This document describes the ArgoCD setup and GitOps workflow for the
`devops-info-chart` Helm chart.

Repository:

- `repoURL`: `https://github.com/Vlad1mirZhidkov/DevOps-Core-Course.git`
- `targetRevision`: `lab12`
- Helm chart path: `k8s/devops-info-chart`

## 1. ArgoCD Setup

### Install ArgoCD with Helm

```bash
helm repo add argo https://argoproj.github.io/argo-helm
helm repo update

kubectl create namespace argocd
helm upgrade --install argocd argo/argo-cd --namespace argocd

kubectl wait --for=condition=ready pod \
  -l app.kubernetes.io/name=argocd-server \
  -n argocd \
  --timeout=180s
```

Verification:

```bash
kubectl get pods -n argocd
kubectl get svc -n argocd
```

Expected result: all ArgoCD pods are `Running` or `Completed`, and the
`argocd-server` service exists.

Actual verification on Docker Desktop Kubernetes:

```text
argocd-application-controller-0                     1/1 Running
argocd-applicationset-controller-5bb68dc46f-c78xm   1/1 Running
argocd-dex-server-667448759-rjdwn                   1/1 Running
argocd-notifications-controller-76b4b47f6c-stdvj    1/1 Running
argocd-redis-cdf845b8c-dwcmg                        1/1 Running
argocd-repo-server-67488b9779-k2c5r                 1/1 Running
argocd-server-84fb76fbd9-8nmd7                      1/1 Running
```

### UI Access

Run port-forward in a separate terminal:

```bash
kubectl port-forward svc/argocd-server -n argocd 8080:443
```

Get the initial admin password:

```bash
kubectl -n argocd get secret argocd-initial-admin-secret \
  -o jsonpath="{.data.password}" | base64 -d
```

Open `https://localhost:8080` and log in with:

- username: `admin`
- password: the value from the command above

### CLI Access

Install the ArgoCD CLI for the local platform, then log in:

```bash
argocd login localhost:8080 --insecure
argocd version --client
argocd app list
```

Expected result: the CLI can connect to the local ArgoCD server through the
port-forward.

Note: in this environment, GitHub binary download for `argocd.exe` was blocked
by Windows SChannel. Application sync operations were executed through the
ArgoCD `Application` Kubernetes API instead.

## 2. Application Configuration

ArgoCD manifests are stored in `k8s/argocd/`.

| File | Purpose |
| --- | --- |
| `application.yaml` | Single default manual-sync Application |
| `application-dev.yaml` | Dev Application with automated sync, prune, and self-heal |
| `application-prod.yaml` | Prod Application with manual sync |
| `applicationset.yaml` | Bonus ApplicationSet that generates dev and prod Applications |

The default Application uses:

- name: `devops-info`
- namespace: `default`
- values file: `values.yaml`
- sync mode: manual

Deploy it:

```bash
kubectl apply -f k8s/argocd/application.yaml
argocd app get devops-info
argocd app sync devops-info
argocd app wait devops-info --health --sync --timeout 180
```

Verify Kubernetes resources:

```bash
kubectl get all -n default -l app.kubernetes.io/instance=devops-info
```

## 3. Multi-Environment Deployment

The lab uses namespace separation:

- `dev` for automated delivery
- `prod` for controlled manual delivery

Namespaces can be created manually or by ArgoCD with `CreateNamespace=true`:

```bash
kubectl create namespace dev
kubectl create namespace prod
```

Apply both environment Applications:

```bash
kubectl apply -f k8s/argocd/application-dev.yaml
kubectl apply -f k8s/argocd/application-prod.yaml
```

Dev sync policy:

```yaml
automated:
  prune: true
  selfHeal: true
```

Prod sync policy:

- no `automated` block
- sync is triggered manually

Sync and verify:

```bash
argocd app get devops-info-dev
argocd app get devops-info-prod

argocd app sync devops-info-prod
argocd app wait devops-info-dev --health --sync --timeout 180
argocd app wait devops-info-prod --health --sync --timeout 180

kubectl get deploy,svc,pod,pvc,cm,secret -n dev \
  -l app.kubernetes.io/instance=devops-info-dev
kubectl get deploy,svc,pod,pvc,cm,secret -n prod \
  -l app.kubernetes.io/instance=devops-info-prod
```

Actual ArgoCD status:

```text
NAME               SYNC STATUS   HEALTH STATUS   REVISION                                   PROJECT
devops-info-dev    Synced        Healthy         91e3089adfa28aaf327afd36cecabef6c3a3911c   default
devops-info-prod   Synced        Healthy         91e3089adfa28aaf327afd36cecabef6c3a3911c   default
```

Actual Kubernetes status:

```text
dev namespace:
deployment.apps/devops-info-dev-devops-info-chart   1/1
service/devops-info-dev-devops-info-chart           NodePort 80:30080/TCP
pod/devops-info-dev-devops-info-chart-...           1/1 Running

prod namespace:
deployment.apps/devops-info-prod-devops-info-chart  5/5
service/devops-info-prod-devops-info-chart          LoadBalancer localhost:80
pod/devops-info-prod-devops-info-chart-...          1/1 Running
```

Application access verification:

```text
curl http://localhost:30080/health
{"status":"healthy","timestamp":"2026-04-19T18:42:39.919Z","uptime_seconds":821}

curl http://localhost/health
{"status":"healthy","timestamp":"2026-04-19T18:42:40.065Z","uptime_seconds":1972}
```

Configuration differences:

| Environment | Values file | Replicas | Resources | Sync |
| --- | --- | ---: | --- | --- |
| dev | `values-dev.yaml` | 1 | smaller requests/limits | automated |
| prod | `values-prod.yaml` | 5 | larger requests/limits | manual |

## 4. GitOps Workflow Test

Example change:

1. Change `replicaCount` in `k8s/devops-info-chart/values-dev.yaml`.
2. Commit and push to the branch used by `targetRevision`.
3. Watch ArgoCD detect the change:

```bash
argocd app get devops-info-dev
argocd app history devops-info-dev
```

Expected behavior:

- dev auto-syncs because `automated` is enabled
- prod remains unchanged until a manual sync is started

## 5. Self-Healing and Drift Tests

### Manual Scale Test

Current Git-defined dev replica count is `1`.

```bash
kubectl get deployment -n dev \
  -l app.kubernetes.io/instance=devops-info-dev

kubectl scale deployment -n dev \
  -l app.kubernetes.io/instance=devops-info-dev \
  --replicas=5

kubectl get pods -n dev -w
```

Expected behavior:

- Kubernetes scales the Deployment to 5 replicas.
- ArgoCD detects drift from Git.
- ArgoCD self-heals the Deployment back to 1 replica.

Record timestamps:

| Event | Timestamp |
| --- | --- |
| Manual scale to 5 replicas | 2026-04-19T21:25:17+03:00 |
| ArgoCD detects drift | within 20 seconds |
| ArgoCD self-heals back to 1 replica | within 20 seconds |

Actual result:

```text
after_manual_scale=1/1
status_after_scale=Synced/Healthy
after_self_heal=1/1
status_after_self_heal=Synced/Healthy
```

### Pod Deletion Test

```bash
kubectl delete pod -n dev \
  -l app.kubernetes.io/instance=devops-info-dev

kubectl get pods -n dev -w
```

Expected behavior:

- The ReplicaSet creates a replacement pod.
- This is Kubernetes self-healing, not ArgoCD self-healing.

Actual result:

```text
delete_time=2026-04-19T21:28:42+03:00
deleted_pod=devops-info-dev-devops-info-chart-6bcb466786-r8kxg
replacement_pod=devops-info-dev-devops-info-chart-6bcb466786-6mxr8
replacement_status=1/1 Running
```

### Configuration Drift Test

```bash
kubectl set image deployment/devops-info-dev-devops-info-chart -n dev \
  devops-info-chart=busybox:1.36

argocd app diff devops-info-dev
argocd app get devops-info-dev
```

Expected behavior:

- ArgoCD shows the live resource differs from Git.
- Because dev has `selfHeal: true`, ArgoCD restores the image from Git.

Actual result:

```text
image_drift_start=2026-04-19T21:32:21+03:00
image_after_manual_change=vladimirzhidkov/devops-info-service:latest
status_after_image_change=Synced/Healthy
image_after_self_heal=vladimirzhidkov/devops-info-service:latest
status_after_self_heal=Synced/Healthy
```

### ArgoCD vs Kubernetes Healing

Kubernetes self-healing is controller-level behavior. For example, a
Deployment/ReplicaSet restores missing pods to keep the requested pod count.

ArgoCD self-healing is GitOps reconciliation. It restores Kubernetes resource
configuration to the desired state stored in Git.

By default, ArgoCD checks Git approximately every 3 minutes. Manual sync and
webhooks can trigger reconciliation sooner.

## 6. Screenshots

Save screenshots under `screenshots/lab13/`:

- `01-applications-list.png`: ArgoCD UI with `devops-info-dev` and `devops-info-prod`
- `02-dev-application-details.png`: dev Application synced and healthy
- `03-prod-application-details.png`: prod Application synced and healthy after manual sync
- `04-dev-self-heal.png`: self-healing or diff evidence

Actual screenshots/evidence files:

```text
screenshots/lab13/01-applications-list.png
screenshots/lab13/02-dev-application-details.png
screenshots/lab13/03-prod-application-details.png
screenshots/lab13/04-dev-self-heal.png
```

## 7. Bonus - ApplicationSet

The bonus manifest is `k8s/argocd/applicationset.yaml`.

It uses:

- List generator for `dev` and `prod`
- Go templates for environment-specific values
- `templatePatch` to add auto-sync only for dev

Apply it instead of the individual dev/prod Applications:

```bash
kubectl delete -f k8s/argocd/application-dev.yaml --ignore-not-found
kubectl delete -f k8s/argocd/application-prod.yaml --ignore-not-found
kubectl apply -f k8s/argocd/applicationset.yaml

argocd app list
argocd app get devops-info-dev
argocd app get devops-info-prod
```

ApplicationSet benefits:

- one template for many environments
- less duplication
- easier scaling to more environments or clusters

Use individual Applications for a small number of highly customized
deployments. Use ApplicationSet when multiple Applications share a common
structure and differ mostly by parameters.
