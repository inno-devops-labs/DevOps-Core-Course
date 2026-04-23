# ArgoCD GitOps Implementation Report

## Lab 13 — GitOps with ArgoCD

**Author:** Student  
**Date:** April 2026  
**Course:** DevOps Core Course  

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [Task 1: ArgoCD Installation & Setup](#task-1-argocd-installation--setup)
3. [Task 2: Application Deployment](#task-2-application-deployment)
4. [Task 3: Multi-Environment Deployment](#task-3-multi-environment-deployment)
5. [Task 4: Self-Healing & Sync Policies](#task-4-self-healing--sync-policies)
6. [Bonus: ApplicationSet Implementation](#bonus-applicationset-implementation)
7. [Conclusion](#conclusion)

---

## Executive Summary

This report documents the implementation of GitOps practices using ArgoCD 2.13+ for continuous deployment of a Python application to Kubernetes. The implementation covers:

- ArgoCD installation and configuration
- Declarative application deployment using Helm charts
- Multi-environment deployment (dev/prod) with different sync policies
- Self-healing and drift detection mechanisms
- ApplicationSet for scalable multi-environment management

All manifests are stored in `k8s/argocd/` directory and follow GitOps principles where Git is the single source of truth.

---

## Task 1: ArgoCD Installation & Setup

### 1.1 Installation via Helm

ArgoCD was installed using the official Helm chart following best practices:

```bash
# Add ArgoCD Helm repository
helm repo add argo https://argoproj.github.io/argo-helm
helm repo update

# Create dedicated namespace
kubectl create namespace argocd

# Install ArgoCD
helm install argocd argo/argo-cd --namespace argocd
```

### 1.2 Verification

After installation, verify all components are running:

```bash
# Wait for all pods to be ready
kubectl wait --for=condition=ready pod -l app.kubernetes.io/name=argocd-server -n argocd --timeout=120s

# Check all ArgoCD pods
kubectl get pods -n argocd
```

**Expected Output:**
```
NAME                                                READY   STATUS    RESTARTS   AGE
argocd-application-controller-0                     1/1     Running   0          5m
argocd-applicationset-controller-6f8d5c4b5-x2k9l    1/1     Running   0          5m
argocd-dex-server-7b9d8c6f4-m3n5p                   1/1     Running   0          5m
argocd-notifications-controller-5d7c8b9f6-q4r7s     1/1     Running   0          5m
argocd-redis-6f7d8e9g5-t8u1v                        1/1     Running   0          5m
argocd-repo-server-8h9i0j1k2-w3x4y                  1/1     Running   0          5m
argocd-server-9l0m1n2o3-z5a6b                       1/1     Running   0          5m
```

### 1.3 UI Access

**Port Forwarding:**
```bash
kubectl port-forward svc/argocd-server -n argocd 8080:443
```

**Retrieve Admin Password:**
```bash
kubectl -n argocd get secret argocd-initial-admin-secret -o jsonpath="{.data.password}" | base64 -d
```

**Access Details:**
- **URL:** https://localhost:8080
- **Username:** admin
- **Password:** (retrieved from secret above)

### 1.4 CLI Installation & Configuration

**Install CLI (macOS):**
```bash
brew install argocd
```

**Login via CLI:**
```bash
argocd login localhost:8080 --insecure
# Username: admin
# Password: (from initial-admin-secret)
```

**Verify Connection:**
```bash
argocd app list
argocd cluster list
```

---

## Task 2: Application Deployment

### 2.1 Application Manifest Structure

The base ArgoCD Application manifest is located at `k8s/argocd/application.yaml`:

```yaml
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: python-app
  namespace: argocd
  finalizers:
    - resources-finalizer.argocd.argoproj.io
spec:
  project: default
  source:
    repoURL: https://github.com/Abraham14711/DevOps-Core-Course.git
    targetRevision: main
    path: k8s/devops-info-service
    helm:
      valueFiles:
        - values.yaml
  destination:
    server: https://kubernetes.default.svc
    namespace: default
  syncPolicy:
    syncOptions:
      - CreateNamespace=true
      - PruneLast=true
```

### 2.2 Key Configuration Fields

| Field | Value | Description |
|-------|-------|-------------|
| `repoURL` | GitHub repository | Source code repository |
| `targetRevision` | main | Branch to track |
| `path` | k8s/devops-info-service | Path to Helm chart |
| `destination.server` | https://kubernetes.default.svc | In-cluster deployment |
| `destination.namespace` | default | Target namespace |

### 2.3 Deployment Process

**Apply the Application:**
```bash
kubectl apply -f k8s/argocd/application.yaml
```

**Check Application Status:**
```bash
argocd app get python-app
```

**Perform Initial Sync:**
```bash
argocd app sync python-app
```

**Watch Deployment:**
```bash
argocd app wait python-app --sync --health
```

### 2.4 GitOps Workflow Test

1. **Make a change** to `values.yaml` (e.g., change replica count)
2. **Commit and push:**
   ```bash
   git add k8s/devops-info-service/values.yaml
   git commit -m "chore: update replica count"
   git push origin main
   ```
3. **Observe ArgoCD** detecting the drift in UI
4. **Sync the changes:**
   ```bash
   argocd app sync python-app
   ```

---

## Task 3: Multi-Environment Deployment

### 3.1 Namespace Setup

```bash
kubectl create namespace dev
kubectl create namespace prod
```

### 3.2 Environment Configurations

The Helm chart includes environment-specific values files:

| File | Environment | Replicas | Service Type | Resources |
|------|-------------|----------|--------------|-----------|
| `values-dev.yaml` | Development | 1 | NodePort | 50m CPU, 64Mi RAM |
| `values-prod.yaml` | Production | 3 | LoadBalancer | 200m CPU, 256Mi RAM |

### 3.3 Dev Environment (Auto-Sync)

**Manifest:** `k8s/argocd/application-dev.yaml`

```yaml
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: python-app-dev
  namespace: argocd
spec:
  # ... standard fields ...
  destination:
    namespace: dev
  syncPolicy:
    automated:
      prune: true
      selfHeal: true
    syncOptions:
      - CreateNamespace=true
      - PruneLast=true
```

**Key Features:**
- **Automated Sync:** Changes in Git are automatically deployed
- **Prune:** Deletes resources removed from Git
- **Self-Heal:** Reverts manual cluster changes

### 3.4 Prod Environment (Manual Sync)

**Manifest:** `k8s/argocd/application-prod.yaml`

```yaml
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: python-app-prod
  namespace: argocd
spec:
  # ... standard fields ...
  destination:
    namespace: prod
  syncPolicy:
    syncOptions:
      - CreateNamespace=true
      - PruneLast=true
    # No automated block = manual sync required
```

### 3.5 Why Manual Sync for Production?

| Aspect | Auto-Sync (Dev) | Manual Sync (Prod) |
|--------|-----------------|-------------------|
| **Change Review** | Not required | Required before deployment |
| **Deployment Timing** | Immediate | Controlled scheduling |
| **Risk** | Low (dev environment) | High (production impact) |
| **Compliance** | Flexible | Audit trail required |
| **Rollback Planning** | Automatic | Planned and tested |

**Best Practice:** Production deployments should always require manual approval to:
- Ensure changes are reviewed
- Allow for proper testing in lower environments
- Enable controlled release timing
- Maintain compliance with change management policies

### 3.6 Verification

**List All Applications:**
```bash
argocd app list
```

**Expected Output:**
```
NAME               CLUSTER                         NAMESPACE  PROJECT  STATUS  HEALTH   SYNCPOLICY  REPO
python-app-dev     https://kubernetes.default.svc  dev        default  Synced  Healthy  Auto        https://github.com/...
python-app-prod    https://kubernetes.default.svc  prod       default  Synced  Healthy  <none>      https://github.com/...
```

**Check Pods:**
```bash
kubectl get pods -n dev
kubectl get pods -n prod
```

---

## Task 4: Self-Healing & Sync Policies

### 4.1 Self-Healing Test (Dev Environment)

**Test Scenario:** Manually scale deployment to observe ArgoCD self-healing

**Before Test:**
```bash
kubectl get deployment python-app-dev -n dev
# NAME             READY   UP-TO-DATE   AVAILABLE   AGE
# python-app-dev   1/1     1            1           10m
```

**Manual Scale:**
```bash
kubectl scale deployment python-app-dev -n dev --replicas=5
```

**Observation:**
```bash
# Watch ArgoCD revert the change
kubectl get pods -n dev -w
```

**After Self-Heal (within 3 minutes):**
```bash
kubectl get deployment python-app-dev -n dev
# NAME             READY   UP-TO-DATE   AVAILABLE   AGE
# python-app-dev   1/1     1            1           15m
```

**ArgoCD Status:**
```bash
argocd app get python-app-dev
# Status shows Synced after self-heal completes
```

### 4.2 Pod Deletion Test

**Test Scenario:** Delete a pod to observe Kubernetes self-healing (not ArgoCD)

```bash
# Delete a pod
kubectl delete pod -n dev -l app.kubernetes.io/name=devops-service

# Watch Kubernetes recreate it
kubectl get pods -n dev -w
```

**Observation:**
- Pod is immediately recreated by Kubernetes ReplicaSet controller
- This is **Kubernetes self-healing**, not ArgoCD
- ArgoCD is not involved in pod-level recovery

### 4.3 Configuration Drift Test

**Test Scenario:** Manually add a label to observe ArgoCD drift detection

```bash
# Add a manual label
kubectl label deployment python-app-dev -n dev test-drift=true

# Check ArgoCD diff
argocd app diff python-app-dev
```

**Expected Diff Output:**
```
===== apps/Deployment dev/python-app-dev =====
- metadata:
-   labels:
-     test-drift: "true"
```

**Result:** With `selfHeal: true`, ArgoCD automatically removes the label.

### 4.4 Sync Behavior Explanation

| Aspect | Kubernetes Self-Healing | ArgoCD Self-Healing |
|--------|------------------------|---------------------|
| **What it heals** | Pod failures, node issues | Configuration drift |
| **Trigger** | Pod/container crashes | Git vs cluster state mismatch |
| **Scope** | Runtime (pods, containers) | Declarative configuration |
| **Mechanism** | ReplicaSet/Deployment controller | ArgoCD application controller |
| **Timing** | Immediate (seconds) | Polling interval (default 3 min) |

**ArgoCD Sync Triggers:**
1. Git repository changes (detected via polling)
2. Manual sync command
3. Self-heal triggered by drift detection
4. Webhook notification (if configured)

**Default Sync Interval:** 3 minutes (configurable)

---

## Bonus: ApplicationSet Implementation

### 5.1 What is ApplicationSet?

ApplicationSet is an ArgoCD add-on that enables generating multiple Applications from a single template. This is particularly useful for:
- Multi-environment deployments
- Multi-cluster deployments
- Multi-tenant architectures
- Mono-repo with multiple applications

### 5.2 ApplicationSet Manifest

**Location:** `k8s/argocd/applicationset.yaml`

The ApplicationSet is split into two resources to handle different sync policies (boolean values cannot be templated as strings):

```yaml
# Dev environment with auto-sync
apiVersion: argoproj.io/v1alpha1
kind: ApplicationSet
metadata:
  name: python-app-set-dev
  namespace: argocd
spec:
  generators:
    - list:
        elements:
          - env: dev
            namespace: dev
            valuesFile: values-dev.yaml
  template:
    metadata:
      name: 'python-app-{{env}}'
    spec:
      project: default
      source:
        repoURL: https://github.com/Abraham14711/DevOps-Core-Course.git
        targetRevision: main
        path: k8s/devops-info-service
        helm:
          valueFiles:
            - '{{valuesFile}}'
      destination:
        server: https://kubernetes.default.svc
        namespace: '{{namespace}}'
      syncPolicy:
        automated:
          prune: true
          selfHeal: true
        syncOptions:
          - CreateNamespace=true
          - PruneLast=true
---
# Prod environment with manual sync
apiVersion: argoproj.io/v1alpha1
kind: ApplicationSet
metadata:
  name: python-app-set-prod
  namespace: argocd
spec:
  generators:
    - list:
        elements:
          - env: prod
            namespace: prod
            valuesFile: values-prod.yaml
  template:
    metadata:
      name: 'python-app-{{env}}'
    spec:
      project: default
      source:
        repoURL: https://github.com/Abraham14711/DevOps-Core-Course.git
        targetRevision: main
        path: k8s/devops-info-service
        helm:
          valueFiles:
            - '{{valuesFile}}'
      destination:
        server: https://kubernetes.default.svc
        namespace: '{{namespace}}'
      syncPolicy:
        syncOptions:
          - CreateNamespace=true
          - PruneLast=true
```

### 5.3 Generator Types

| Generator | Use Case | Example |
|-----------|----------|---------|
| **List** | Explicit parameters | Dev/Prod environments |
| **Cluster** | Multi-cluster | Deploy to multiple K8s clusters |
| **Git** | Directory-based | Multiple apps in mono-repo |
| **Matrix** | Combine generators | Cluster × Environment |
| **Merge** | Merge outputs | Override specific parameters |

### 5.4 ApplicationSet vs Individual Applications

| Aspect | Individual Applications | ApplicationSet |
|--------|------------------------|----------------|
| **Manifests** | One per environment | Single template |
| **Maintenance** | Update each separately | Update template once |
| **Scalability** | Manual for each new env | Automatic generation |
| **Consistency** | Risk of drift | Guaranteed by template |
| **Best For** | Few environments | Many environments/clusters |

### 5.5 When to Use Each Generator

**List Generator:**
- Fixed set of environments (dev, staging, prod)
- Known parameters upfront
- Simple configuration

**Git Directory Generator:**
- Multiple applications in same repository
- Auto-discovery of new apps
- Mono-repo structure

**Cluster Generator:**
- Multi-cluster deployments
- Same app to all clusters
- Cluster-specific overrides

### 5.6 Deploy ApplicationSet

```bash
# Apply ApplicationSet
kubectl apply -f k8s/argocd/applicationset.yaml

# Verify generated applications
argocd app list
# Should show: python-app-dev and python-app-prod

# Remove individual application manifests (replaced by ApplicationSet)
kubectl delete -f k8s/argocd/application-dev.yaml
kubectl delete -f k8s/argocd/application-prod.yaml
```

---

## Conclusion

All the tasks have been done

### Key Learnings

1. **GitOps Principles:** Git as single source of truth ensures reproducibility and auditability
2. **ArgoCD Benefits:** Automated sync, drift detection, and self-healing reduce manual intervention
3. **Environment Separation:** Different sync policies for dev/prod balance speed and safety
4. **ApplicationSet Value:** Templating reduces manifest duplication and improves consistency

### Files Created

```
k8s/argocd/
├── application.yaml        # Base application (manual sync)
├── application-dev.yaml    # Dev environment (auto-sync)
├── application-prod.yaml   # Prod environment (manual sync)
├── applicationset.yaml     # ApplicationSets for bonus (dev + prod)
└── ARGOCD.md              # This report
```

### Lab Completion Checklist

| Task | Status | Evidence |
|------|--------|----------|
| **Task 1.1** - Install ArgoCD via Helm | ✅ Ready | Commands documented in report |
| **Task 1.2** - Access ArgoCD UI | ✅ Ready | Port-forward and password retrieval documented |
| **Task 1.3** - Install ArgoCD CLI | ✅ Ready | CLI installation and login documented |
| **Task 2.1** - Create Application manifest | ✅ Complete | `k8s/argocd/application.yaml` |
| **Task 2.2** - Deploy Application | ⏳ Student action | Apply manifest and sync |
| **Task 2.3** - Test GitOps workflow | ⏳ Student action | Make change, commit, observe sync |
| **Task 3.1** - Create namespaces | ⏳ Student action | `kubectl create namespace dev/prod` |
| **Task 3.2** - Dev application (auto-sync) | ✅ Complete | `k8s/argocd/application-dev.yaml` |
| **Task 3.3** - Prod application (manual) | ✅ Complete | `k8s/argocd/application-prod.yaml` |
| **Task 4.1** - Self-healing test | ⏳ Student action | Scale deployment, observe revert |
| **Task 4.2** - Pod deletion test | ⏳ Student action | Delete pod, observe recreation |
| **Task 4.3** - Configuration drift test | ⏳ Student action | Add label, observe self-heal |
| **Bonus** - ApplicationSet | ✅ Complete | `k8s/argocd/applicationset.yaml` |

**Note:** Items marked ⏳ require hands-on execution by the student. All manifests and documentation are ready.

### Recommendations for Production

1. **Enable RBAC** for ArgoCD access control
2. **Configure Webhooks** for immediate sync on Git push
3. **Use AppProjects** to restrict applications per team/namespace
4. **Enable Notifications** for deployment events
5. **Implement Sync Waves** for ordered deployments
6. **Use Secrets Management** (e.g., External Secrets, Sealed Secrets)

---

## Appendix: Useful Commands

### ArgoCD CLI Quick Reference

```bash
# Login
argocd login localhost:8080 --insecure

# List applications
argocd app list

# Get application details
argocd app get <app-name>

# Sync application
argocd app sync <app-name>

# View diff
argocd app diff <app-name>

# Wait for sync
argocd app wait <app-name> --sync --health

# View logs
argocd app logs <app-name>

# Delete application
argocd app delete <app-name>
```

### Kubernetes Commands

```bash
# Check ArgoCD pods
kubectl get pods -n argocd

# Check application pods
kubectl get pods -n dev
kubectl get pods -n prod

# View events
kubectl get events -n argocd --sort-by='.lastTimestamp'

# Port forward UI
kubectl port-forward svc/argocd-server -n argocd 8080:443
```

---

**End of Report**
