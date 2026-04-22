# Lab 13 - GitOps with ArgoCD

This document describes the ArgoCD setup and deployment workflow for `devops-app`.

## 1. ArgoCD Installation and Setup

### 1.1 Install ArgoCD with Helm

```bash
helm repo add argo https://argoproj.github.io/argo-helm
helm repo update
kubectl create namespace argocd
helm install argocd argo/argo-cd -n argocd
kubectl get pods -n argocd -w
```

Verification:

```bash
kubectl get pods -n argocd
kubectl get svc -n argocd
```

All ArgoCD pods in `argocd` should be `Running` or `Completed`.

### 1.2 Access ArgoCD UI

```bash
kubectl port-forward svc/argocd-server -n argocd 8080:443
```

UI URL: `https://localhost:8080`

### 1.3 Retrieve Initial Admin Password

Linux/macOS:

```bash
kubectl -n argocd get secret argocd-initial-admin-secret -o jsonpath="{.data.password}" | base64 -d
```

PowerShell:

```powershell
[System.Text.Encoding]::UTF8.GetString([System.Convert]::FromBase64String((kubectl -n argocd get secret argocd-initial-admin-secret -o jsonpath="{.data.password}")))
```

### 1.4 ArgoCD CLI

Install CLI:

- Windows (Chocolatey): `choco install argocd-cli`
- Windows (Scoop): `scoop install argocd`

Login and verify:

```bash
argocd login localhost:8080 --username admin --password <PASSWORD> --insecure
argocd account get-user-info
argocd version
```

## 2. Application Deployment (Single Application)

Manifest used for Task 2: `k8s/argocd/application.yaml`.

Configuration:

- source: `repoURL`, `targetRevision`, `path: k8s/devops-app`
- destination: `https://kubernetes.default.svc`, namespace `dev`
- sync policy: manual (no `automated` block)

Apply and inspect:

```bash
kubectl apply -f k8s/argocd/application.yaml
argocd app list
argocd app get devops-app
```

Initial manual sync:

```bash
argocd app sync devops-app
argocd app wait devops-app --health --sync
```

Resource verification:

```bash
kubectl get all -n dev
```

## 3. Multi-Environment Deployment (Dev and Prod)

Manifests:

- `k8s/argocd/application-dev.yaml`
- `k8s/argocd/application-prod.yaml`

Apply:

```bash
kubectl create namespace dev
kubectl create namespace prod
kubectl apply -f k8s/argocd/application-dev.yaml
kubectl apply -f k8s/argocd/application-prod.yaml
kubectl get applications -n argocd
```

### 3.1 Dev vs Prod Differences

| Parameter | Dev | Prod |
| --- | --- | --- |
| Namespace | `dev` | `prod` |
| Values file | `values-dev.yaml` | `values-prod.yaml` |
| Replica count | `1` | `3` |
| Log level | `DEBUG` | `INFO` |
| Sync policy | auto-sync (`prune + selfHeal`) | manual sync |

### 3.2 Why Prod Stays Manual

Production uses manual sync to keep a human approval step before rollout, reducing risk from unreviewed or unexpected changes.

## 4. Self-Healing and Drift Tests

Use timestamps from:

```bash
kubectl get events -n dev --sort-by=.metadata.creationTimestamp
```

### 4.1 Scale Drift (ArgoCD Self-Heal)

```bash
kubectl scale deployment devops-app -n dev --replicas=5
kubectl get deploy -n dev -w
```

Expected behavior: ArgoCD marks the app `OutOfSync` and returns replicas to the Git value.

### 4.2 Pod Deletion (Kubernetes Self-Heal)

```bash
kubectl delete pod -n dev --all
kubectl get pods -n dev -w
```

Expected behavior: Kubernetes recreates pods via Deployment/ReplicaSet, independent of ArgoCD sync.

### 4.3 Manual Resource Drift

```bash
kubectl label deployment devops-app -n dev drift-test=true --overwrite
kubectl get deploy -n dev --show-labels
```

Expected behavior: ArgoCD detects diff and removes the manual label during auto-sync.

### 4.4 Sync Behavior Summary

- Manual sync happens when triggered in UI/CLI.
- Auto-sync happens when drift is detected and automated sync is enabled.
- ArgoCD controller reconciliation is periodic (commonly around 3 minutes, configurable).

## 5. GitOps Workflow Validation

Example validation flow:

1. Change `replicaCount` in `k8s/devops-app/values-dev.yaml`.
2. Commit and push.
3. Confirm `OutOfSync` in ArgoCD.
4. Dev auto-syncs to the new desired state.
5. Prod requires explicit manual sync.

## 6. Troubleshooting and Fixes Applied

The following issues were identified and fixed during validation:

- `Sync failed` due to NodePort collision (`30080` already allocated).
- `Degraded` due to Vault auth failure (`namespace not authorized`).
- `ImagePullBackOff` for invalid image tag `latest`.

Fixes:

- Updated Vault Kubernetes role to include `default,dev,prod` namespaces.
- Set dev image tag to `lab03` (`k8s/devops-app/values-dev.yaml`).
- Kept distinct NodePorts per environment (`30081` for dev, `30082` for prod).

Current result:

- `devops-app-dev`: `Synced` / `Healthy`
- `devops-app-prod`: manual sync required by design

## 7. Bonus Task - ApplicationSet

Manifest: `k8s/argocd/applicationset.yaml` (List generator).

Generated applications:

- `devops-app-dev`
- `devops-app-prod`

Design notes:

- Single template for one Helm chart in a mono-repo.
- Environment parameters (`namespace`, `valuesFile`) come from list elements.
- Dev auto-sync can be enabled from template logic; prod remains manual.

Apply:

```bash
kubectl apply -f k8s/argocd/applicationset.yaml
kubectl get applications -n argocd
kubectl get applicationsets -n argocd
```

When to use ApplicationSet:

- Many environments or clusters.
- Repeated application structure with different parameters.
- Reduced duplication and better scaling of GitOps configuration.
