# Lab 13 — GitOps with ArgoCD

## Overview

In this lab, ArgoCD was used to implement GitOps-based continuous deployment. The Kubernetes cluster state is now fully managed from a Git repository, ensuring declarative, version-controlled infrastructure.

## 1. ArgoCD Setup

### Installation Verification

```bash
kubectl get pods -n argocd
```

### UI Access

```bash
kubectl port-forward svc/argocd-server -n argocd 8081:443
```

Access via browser:

```
https://localhost:8081
```

### Retrieve Admin Password

```bash
kubectl -n argocd get secret argocd-initial-admin-secret \
  -o jsonpath="{.data.password}" | base64 -d
```

### CLI Login

```bash
argocd login localhost:8081 --insecure
```

## 2. Application Deployment

### Application Configuration

- Repository:
  `https://github.com/kvassoedik/DevOps-Core-Course.git`

- Branch:
  `lab12`

- Chart path:
  `k8s/devops-chart`

- Values file:
  `values-dev.yaml`

### Sync Result

```bash
argocd app get devops-app
```

```text
Sync Status: Synced
Health Status: Healthy
```

## 3. Multi-Environment Setup

### Namespaces

```bash
kubectl create namespace dev
kubectl create namespace prod
```

### Dev Environment

- Namespace: `dev`
- Sync policy: Automated
- Self-healing enabled

### Prod Environment

- Namespace: `default` or `prod`
- Sync policy: Manual
- No automatic updates

### Rationale

- Dev: fast iteration, automatic updates
- Prod: controlled releases, manual approval

## 4. Self-Healing Tests

### 4.1 Scaling Test

```bash
kubectl get deployment devops-app-dev-devops-chart -n dev
kubectl scale deployment devops-app-dev-devops-chart -n dev --replicas=5
kubectl get deployment devops-app-dev-devops-chart -n dev
```

Output:

```text
deployment.apps/devops-app-dev-devops-chart scaled

NAME                          READY   UP-TO-DATE   AVAILABLE   AGE
devops-app-dev-devops-chart   1/5     5            1           6d22h
```

After ArgoCD self-healing:

```bash
kubectl get deployment devops-app-dev-devops-chart -n dev
```

```text
NAME                          READY   UP-TO-DATE   AVAILABLE   AGE
devops-app-dev-devops-chart   1/1     1            1           6d22h
```

### Explanation

ArgoCD detected drift from Git (replicas=1) and automatically reverted the deployment.

### 4.2 Pod Deletion Test

```bash
kubectl get pods -n dev
kubectl delete pod -n dev devops-app-dev-devops-chart-5d94846fdd-6hjbs
kubectl get pods -n dev
```

Output:

```text
NAME                                           READY   STATUS        RESTARTS   AGE
devops-app-dev-devops-chart-5d94846fdd-6hjbs   1/1     Running       0          2m
```

New pod appears automatically.

### Explanation

This behavior is handled by Kubernetes (ReplicaSet), not ArgoCD.

### 4.3 Configuration Drift Test

```bash
kubectl label deployment devops-app-dev-devops-chart -n dev manual-change=true --overwrite
```

Check:

```bash
kubectl get deployment devops-app-dev-devops-chart -n dev --show-labels
```

```text
manual-change=true
```

After ArgoCD self-healing:

```bash
kubectl get deployment devops-app-dev-devops-chart -n dev --show-labels
```

```text
(no manual-change label present)
```

### Explanation

ArgoCD detected configuration drift and reverted it to match Git.

## 5. Sync Behavior Explanation

### Kubernetes Self-Healing

- Restores pods when deleted
- Managed by ReplicaSet / Deployment

### ArgoCD Self-Healing

- Restores configuration drift
- Ensures cluster matches Git

### Sync Triggers

- Git changes
- Manual sync
- Auto-sync (dev)

### Sync Interval

- Default polling: ~3 minutes

## 6. Summary

This lab demonstrated:

- GitOps deployment with ArgoCD
- Declarative application management via Git
- Multi-environment deployment (dev/prod)
- Automated synchronization
- Self-healing behavior:

  - scaling drift
  - configuration drift
- Difference between Kubernetes and ArgoCD healing mechanisms

## Commands Used

```bash
# ArgoCD
argocd login localhost:8081 --insecure
argocd app get devops-app-dev
argocd app sync devops-app-dev
argocd app diff devops-app-dev

# Kubernetes
kubectl get pods -n dev
kubectl scale deployment devops-app-dev-devops-chart -n dev --replicas=5
kubectl delete pod -n dev <pod-name>
kubectl label deployment devops-app-dev-devops-chart -n dev manual-change=true --overwrite
```

## Conclusion

The GitOps workflow was successfully implemented.
ArgoCD now ensures that the Kubernetes cluster state is always consistent with the Git repository, providing reliable, automated, and auditable deployments.
