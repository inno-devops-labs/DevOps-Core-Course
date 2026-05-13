# Lab 14 — Progressive Delivery with Argo Rollouts

## 1. Argo Rollouts Installation

Argo Rollouts was installed into a dedicated namespace.

Commands used:

```bash
kubectl create namespace argo-rollouts

kubectl apply -n argo-rollouts \
-f https://github.com/argoproj/argo-rollouts/releases/latest/download/install.yaml
```

Verification:

```bash
kubectl get pods -n argo-rollouts
```

Output:

```text
NAME                             READY   STATUS    RESTARTS   AGE
argo-rollouts-79b89d8856-g48vp   1/1     Running   0          14m
```

## 2. Argo Rollouts CLI Plugin

The kubectl plugin for Argo Rollouts was installed.

Verification:

```bash
kubectl argo rollouts version
```

Output:

```text
kubectl-argo-rollouts: v1.9.0+838d4e7
BuildDate: 2026-03-20T21:08:11Z
GitCommit: 838d4e792be666ec11bd0c80331e0c5511b5010e
Platform: linux/amd64
```

## 3. Argo Rollouts Dashboard

The dashboard was installed:

```bash
kubectl apply -n argo-rollouts \
-f https://github.com/argoproj/argo-rollouts/releases/latest/download/dashboard-install.yaml
```

Access:

```bash
kubectl port-forward svc/argo-rollouts-dashboard -n argo-rollouts 3100:3100
```

Dashboard URL:

```text
http://localhost:3100
```

The dashboard was used to observe rollout progression, canary pauses, promotions, and rollback behavior.

---

# 4. Rollout vs Deployment

The original Kubernetes Deployment was replaced with an Argo Rollout resource.

Changes made:

- `kind: Deployment` → `kind: Rollout`
- `apiVersion: apps/v1` → `apiVersion: argoproj.io/v1alpha1`
- Added progressive delivery strategies
- Added canary traffic shifting
- Added blue-green deployment support

Unlike Deployments, Rollouts support:

- Canary releases
- Blue-green deployments
- Manual promotion
- Rollback control
- Traffic shifting
- Preview environments

---

# 5. Canary Deployment Strategy

## Rollout Configuration

The Helm chart was updated with a canary strategy:

```yaml
strategy:
  canary:
    steps:
      - setWeight: 20
      - pause: {}
      - setWeight: 40
      - pause:
          duration: 30s
      - setWeight: 60
      - pause:
          duration: 30s
      - setWeight: 80
      - pause:
          duration: 30s
      - setWeight: 100
```

This configuration performs gradual rollout progression with pauses between stages.

---

## Deploying the Canary Rollout

Namespace creation:

```bash
kubectl create namespace canary
```

Deployment:

```bash
helm upgrade --install canary-app \
labs/lab12/k8s/devops-info-service \
-n canary
```

Verification:

```bash
kubectl get rollouts -n canary
```

Output:

```text
NAME                             DESIRED   CURRENT   UP-TO-DATE   AVAILABLE   AGE
canary-app-devops-info-service   3         3         3                        10s
```

---

# 6. Canary Rollout Progression

A new rollout revision was triggered:

```bash
kubectl patch rollout canary-app-devops-info-service -n canary --type merge \
-p '{"spec":{"template":{"metadata":{"annotations":{"rollout-test":"v2"}}}}}'
```

The rollout paused at 20% traffic:

```text
Status:          ॥ Paused
Message:         CanaryPauseStep
Strategy:        Canary
Step:            1/9
SetWeight:       20
ActualWeight:    25
```

The canary version received partial traffic while the stable version remained active.

Manual promotion:

```bash
kubectl argo rollouts promote canary-app-devops-info-service -n canary
```

After promotion, the rollout automatically progressed through:

- 40%
- 60%
- 80%
- 100%

---

# 7. Canary Rollback / Abort Test

A second rollout revision was created:

```bash
kubectl patch rollout canary-app-devops-info-service -n canary --type merge \
-p '{"spec":{"template":{"metadata":{"annotations":{"rollout-test":"v3"}}}}}'
```

The rollout was manually aborted:

```bash
kubectl argo rollouts abort canary-app-devops-info-service -n canary
```

Verification:

```bash
kubectl argo rollouts get rollout canary-app-devops-info-service -n canary
```

Output:

```text
Status:          ✖ Degraded
Message:         RolloutAborted: Rollout aborted update to revision 3
```

The stable ReplicaSet was automatically restored:

```text
revision:2 -> stable
revision:3 -> scaledDown
```

This demonstrated instant rollback capability during a canary deployment.

---

# 8. Blue-Green Deployment Strategy

A separate values file was created:

```text
values-bluegreen.yaml
```

Blue-green strategy configuration:

```yaml
strategy:
  blueGreen:
    activeService: bluegreen-app-devops-info-service
    previewService: bluegreen-app-devops-info-service-preview
    autoPromotionEnabled: false
```

---

# 9. Blue-Green Deployment

Namespace creation:

```bash
kubectl create namespace bluegreen
```

Deployment:

```bash
helm upgrade --install bluegreen-app \
labs/lab12/k8s/devops-info-service \
-n bluegreen \
-f labs/lab12/k8s/devops-info-service/values-bluegreen.yaml
```

Verification:

```bash
kubectl get rollout -n bluegreen
kubectl get svc -n bluegreen
```

Output:

```text
bluegreen-app-devops-info-service
bluegreen-app-devops-info-service-preview
```

The deployment created:

- Active production service
- Preview service for the new version

---

# 10. Preview Environment Testing

The active service was exposed:

```bash
kubectl port-forward -n bluegreen \
svc/bluegreen-app-devops-info-service 8084:80
```

The preview service was exposed:

```bash
kubectl port-forward -n bluegreen \
svc/bluegreen-app-devops-info-service-preview 8085:80
```

Testing:

```bash
curl localhost:8084
curl localhost:8085
```

Both services responded successfully.

Different pod hostnames confirmed that active and preview environments were separated.

---

# 11. Blue-Green Promotion

Promotion command:

```bash
kubectl argo rollouts promote bluegreen-app-devops-info-service -n bluegreen
```

Verification:

```bash
kubectl argo rollouts get rollout bluegreen-app-devops-info-service -n bluegreen
```

Output:

```text
Status:          ✔ Healthy
Strategy:        BlueGreen
Images:          fayzullin/devops-info-service:latest (active, stable)
```

The new ReplicaSet became:

```text
stable,active
```

The previous ReplicaSet remained temporarily available for rollback purposes.

---

# 12. Canary vs Blue-Green Comparison

## Canary Deployment

Advantages:

- Gradual rollout
- Reduced risk
- Partial traffic testing
- Safer production releases

Disadvantages:

- More complex rollout process
- Longer deployment duration
- Multiple application versions running simultaneously

Best for:

- Large production systems
- Risk-sensitive deployments
- Incremental releases

---

## Blue-Green Deployment

Advantages:

- Instant switch between versions
- Easy rollback
- Simple release process
- Dedicated preview environment

Disadvantages:

- Requires double infrastructure resources
- Full traffic switch at promotion time

Best for:

- Fast rollback requirements
- Simple release workflows
- Pre-production validation

---

# 13. Useful CLI Commands

Watch rollout:

```bash
kubectl argo rollouts get rollout <name> -w
```

Promote rollout:

```bash
kubectl argo rollouts promote <name>
```

Abort rollout:

```bash
kubectl argo rollouts abort <name>
```

Retry rollout:

```bash
kubectl argo rollouts retry rollout <name>
```

View services:

```bash
kubectl get svc -n <namespace>
```

---

# 14. Summary

This lab implemented progressive delivery using Argo Rollouts.

Completed:

- Argo Rollouts controller installation
- kubectl plugin installation
- Rollouts dashboard setup
- Canary deployment strategy
- Manual promotion
- Canary rollback testing
- Blue-green deployment strategy
- Preview environment testing
- Blue-green promotion
- Traffic shifting validation

Argo Rollouts successfully replaced standard Kubernetes Deployments with advanced progressive delivery capabilities.
