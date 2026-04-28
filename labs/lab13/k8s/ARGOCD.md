# Lab 13 — GitOps with ArgoCD

## 1. ArgoCD Setup

ArgoCD was installed into a dedicated namespace using Helm.

Commands used:

```bash
kubectl create namespace argocd
helm install argocd argo/argo-cd -n argocd \
  --set redis.image.repository=docker.io/library/redis \
  --set redis.image.tag=8.2.3-alpine
```

Verification:

```bash
kubectl get pods -n argocd
```

All ArgoCD components were running, including:

argocd-server
argocd-repo-server
argocd-application-controller
argocd-redis
argocd-applicationset-controller

The UI was accessed using port-forward:

```bash
kubectl port-forward svc/argocd-server -n argocd 8081:443
```

URL:

https://localhost:8081

Username:

admin

The initial password was retrieved with:

```bash
kubectl -n argocd get secret argocd-initial-admin-secret \
  -o jsonpath="{.data.password}" | base64 -d
```

### ArgoCD CLI

The ArgoCD CLI was installed:

```bash
curl -sSL -o argocd \
https://github.com/argoproj/argo-cd/releases/latest/download/argocd-linux-amd64

chmod +x argocd
sudo mv argocd /usr/local/bin/
```

Login via CLI:

argocd login localhost:8083 --insecure

Verification:

argocd app list
argocd app get devops-info-app-dev

## 2. Application Configuration

ArgoCD Application manifests were created in:

labs/lab13/k8s/argocd/

Files:

application.yaml
application-dev.yaml
application-prod.yaml

The application source points to the GitHub repository:

https://github.com/fayz131/DevOps-Core-Course.git

Target revision:

lab13

Helm chart path:

labs/lab12/k8s/devops-info-service

The Application deploys the Helm chart from Git into Kubernetes, following the GitOps model.

## 3. Initial Application Deployment

The base application was applied using:

kubectl apply -f labs/lab13/k8s/argocd/application.yaml

ArgoCD detected the application and synced it to the cluster.

Verification:

kubectl get applications -n argocd

Example output:

NAME                   SYNC STATUS   HEALTH STATUS
devops-info-app        Synced        Healthy

Application resources were created in the default namespace.

## 4. Multi-Environment Deployment

Two additional ArgoCD Applications were created:

devops-info-app-dev
devops-info-app-prod
Dev environment

Namespace:

dev

Values file:

values-dev.yaml

Sync policy:

automated:
  prune: true
  selfHeal: true

This means dev automatically syncs changes from Git and self-heals manual drift.

### Prod environment

Namespace:

prod

Values file:

values-prod.yaml

Sync policy:

manual

Production remains manual to allow controlled releases and review before deployment.

Verification:

```bash
kubectl get pods -n dev
kubectl get pods -n prod
kubectl get applications -n argocd
```


Output:

devops-info-app-dev    Synced   Healthy
devops-info-app-prod   Synced   Progressing

Prod pods were running:

devops-info-app-prod-devops-info-service-...   1/1   Running
devops-info-app-prod-devops-info-service-...   1/1   Running
devops-info-app-prod-devops-info-service-...   1/1   Running

## 5. GitOps Workflow

The Helm chart is stored in Git and ArgoCD reads it from the lab13 branch.

When configuration changes are committed and pushed to Git, ArgoCD detects the difference between:

desired state in Git
actual state in the Kubernetes cluster

If the cluster does not match Git, ArgoCD marks the application as OutOfSync.

Manual sync or auto-sync then applies the Git-defined state to the cluster.

## 6. Self-Healing Evidence

### Manual scale drift test

The dev Deployment was manually scaled to 5 replicas:

```bash
kubectl scale deployment devops-info-app-dev-devops-info-service -n dev --replicas=5
kubectl get deployment -n dev
```


Output immediately after manual change:

NAME                                      READY   UP-TO-DATE   AVAILABLE
devops-info-app-dev-devops-info-service   1/5     1            1

After 30 seconds, ArgoCD self-healing reverted the Deployment back to the Git-defined state:

```bash
kubectl get deployment -n dev
```

Output:

NAME                                      READY   UP-TO-DATE   AVAILABLE
devops-info-app-dev-devops-info-service   1/1     1            1

This proves ArgoCD detected configuration drift and restored the desired Git state.

### Pod deletion test

A pod was manually deleted:

```bash
kubectl delete pod -n dev -l app.kubernetes.io/name=devops-info-service
kubectl get pods -n dev -w
```

Output:

pod "devops-info-app-dev-devops-info-service-6bc8d7dbfc-r5d5h" deleted
devops-info-app-dev-devops-info-service-6bc8d7dbfc-wjlww   0/1   Running
devops-info-app-dev-devops-info-service-6bc8d7dbfc-wjlww   1/1   Running

This demonstrates Kubernetes self-healing. The Deployment controller recreated the deleted pod automatically.

## 7. Kubernetes Self-Healing vs ArgoCD Self-Healing

Kubernetes self-healing:

recreates deleted pods
keeps ReplicaSets and Deployments at their desired replica count
works inside the cluster

ArgoCD self-healing:

compares cluster state with Git state
reverts manual changes that drift from Git
keeps Kubernetes configuration aligned with the repository

In this lab:

pod deletion was fixed by Kubernetes
manual scaling to 5 replicas was reverted by ArgoCD
## 8. Sync Policy Explanation

Dev uses auto-sync because it is suitable for rapid iteration and testing.

Prod uses manual sync because production deployments should be controlled, reviewed, and released intentionally.

This separation is a common GitOps best practice.

## 9. Challenges and Solutions
Redis image pull issue

The default ArgoCD Redis image was pulled from AWS ECR and failed due to network issues.

Solution:

helm upgrade argocd argo/argo-cd -n argocd \
  --set redis.image.repository=docker.io/library/redis \
  --set redis.image.tag=8.2.3-alpine
Application image pull issue

The kind cluster had intermittent network issues when pulling from Docker Hub.

Solution:

loaded the local image into kind
changed image pull policy to IfNotPresent
kind load docker-image fayzullin/devops-info-service:latest --name lab9
NodePort conflict

The Service initially failed because a fixed NodePort was already allocated.

Solution:

made nodePort optional in the Helm template
set nodePort: null in values

## 10. Summary

This lab implemented GitOps continuous delivery using ArgoCD.

Completed:

ArgoCD installed via Helm
UI accessed through port-forward
Applications deployed from Git
Helm chart synced by ArgoCD
dev and prod environments configured
dev auto-sync enabled
prod manual sync configured
self-healing tested
Kubernetes pod recovery tested

Git is now the source of truth for Kubernetes application deployment.

## 11. Screenshots

The following screenshots were captured from ArgoCD UI:

- `labs/lab13/screenshots/argocd-overview.png` — all applications (dev, prod)
- `labs/lab13/screenshots/dev-app.png` — dev application details
- `labs/lab13/screenshots/prod-app.png` — prod application details

These screenshots show:
- Sync status (Synced)
- Health status (Healthy)
- Deployed resources
