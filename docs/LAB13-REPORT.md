# Lab 13 – GitOps with ArgoCD Report

## 1. Overview

This lab demonstrates a GitOps workflow using ArgoCD to manage Kubernetes deployments declaratively. The repository acts as the single source of truth, while ArgoCD continuously reconciles cluster state with the configuration stored in Git.

The deployed application is a Helm-based FastAPI service located at:

- Repository: https://github.com/ebortsov/DevOps-Core-Course.git  
- Branch: `lab13`  
- Chart path: `k8s/devops-info`

---

## 2. Repository State

- Active branch: `lab13`  
- Commit: `711d355`

The repository includes:

- Helm chart: `k8s/devops-info`
- ArgoCD manifests:
  - `application.yaml`
  - `application-dev.yaml`
  - `application-prod.yaml`
  - `applicationset.yaml`

---

## 3. Tooling

- Helm version: `v4.1.3`
- Kubernetes client: `v1.35`

All Helm validations and template rendering were executed successfully.

---

## 4. Helm Chart Validation

### Linting

No errors were found. Only a recommendation to include an icon in Chart.yaml.

### Template Rendering

All configurations (base, dev, prod) rendered successfully, confirming correctness of templates and values layering.

---

## 5. ArgoCD Application Design

### Baseline Application

- Name: `devops-info`
- Namespace: `devops-gitops`
- Sync: manual

### Development Environment

- Namespace: `dev`
- Auto-sync enabled
- Self-healing and pruning enabled

### Production Environment

- Namespace: `prod`
- Manual sync

---

## 6. ApplicationSet

Uses a list generator and Go templates to define environments dynamically.

Benefits:
- Reduced duplication
- Easy scalability
- Centralized configuration

---

## 7. GitOps Workflow

1. Modify Helm values in Git
2. Commit and push changes
3. ArgoCD detects drift
4. Dev syncs automatically
5. Prod requires manual sync

---

## 8. Self-Healing

- Kubernetes recreates deleted pods
- ArgoCD restores configuration drift (dev environment)

---

## 9. Conclusion

The lab successfully demonstrates a GitOps workflow using ArgoCD with Helm charts, supporting multiple environments with automated and manual deployment strategies.