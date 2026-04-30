# Lab 14 — Argo Rollouts (Canary Deployment)

## 🎯 Objective
Implement and demonstrate canary deployment strategy using Argo Rollouts, including:
- Paused rollout
- Manual promotion
- Abort scenario
- Rollback (undo)

---

## ⚙️ Setup

Argo Rollouts was installed in the cluster:

```bash
kubectl create namespace argo-rollouts  
kubectl apply -n argo-rollouts -f https://github.com/argoproj/argo-rollouts/releases/latest/download/install.yaml
```

Dashboard:
```bash
kubectl apply -n argo-rollouts -f https://github.com/argoproj/argo-rollouts/releases/latest/download/dashboard-install.yaml  
kubectl port-forward svc/argo-rollouts-dashboard -n argo-rollouts 3100:3100
```
---

## 🚀 Rollout Configuration

Canary strategy:

- 20% → pause  
- 40% → pause  
- 60% → pause  
- 80% → pause  
- 100%

Annotation for triggering new versions:

rollout.argoproj.io/version

---

## 📸 Evidence

1. Dashboard  
screenshots/lab14/01-rollouts-dashboard.png
![[01-rollouts-dashboard.png]]

2. Paused  
screenshots/lab14/02-paused.png
![[02-paused.png]]

3. Promote  
screenshots/lab14/03-promote.png
![[03-promote.png]]

4. Abort  
screenshots/lab14/04-abort.png
![[04-abort.png]]

5. Undo  
screenshots/lab14/05-undo.png
![[05-undo.png]]

---

## ✅ Result

Successfully demonstrated:
- Canary deployment
- Manual promotion
- Abort
- Rollback (undo)

Argo Rollouts works correctly.
