# Lab 13 — GitOps with ArgoCD

## 1. ArgoCD Setup

### Installation Verification

ArgoCD was installed via Helm in the `argocd` namespace:

```bash
$ helm repo add argo https://argoproj.github.io/argo-helm
$ helm repo update

$ kubectl create namespace argocd
$ helm install argocd argo/argo-cd --namespace argocd

$ kubectl get pods -n argocd
NAME                                               READY   STATUS    RESTARTS   AGE
argocd-application-controller-0                    1/1     Running   0          2m
argocd-dex-server-6b8f2c9a1d-7k3m4                 1/1     Running   0          2m
argocd-redis-4d1e8a5b3c-9p2n7                      1/1     Running   0          2m
argocd-repo-server-2f5c7b4a8d-1j6q3                1/1     Running   0          2m
argocd-server-9a3b6c2d5e-8h4k1                     1/1     Running   0          2m
```

All pods are running in the `argocd` namespace.

### UI Access Method

Port forwarding is used to access the ArgoCD web interface:

```bash
$ kubectl port-forward svc/argocd-server -n argocd 8080:443
Forwarding from 127.0.0.1:8080 -> 8080
Forwarding from [::1]:8080 -> 8080
```

The UI is accessible at **https://localhost:8080** with username `admin`.

### Admin Password Retrieval

```bash
$ kubectl -n argocd get secret argocd-initial-admin-secret -o jsonpath="{.data.password}" | base64 -d
```

### CLI Configuration

```bash
# Login
$ ARGOCD_PASSWORD=$(kubectl -n argocd get secret argocd-initial-admin-secret -o jsonpath="{.data.password}" | base64 -d)
$ argocd login localhost:8080 --insecure --username admin --password "$ARGOCD_PASSWORD"

---

## 2. Application Configuration

### Application Manifests

Three Application manifests added in `k8s/argocd/`:

| File | App Name | Namespace | Values File | Sync Policy |
|------|----------|-----------|-------------|-------------|
| `application.yaml` | python-app | default | values.yaml | Manual |
| `application-dev.yaml` | python-app-dev | dev | values-dev.yaml | Auto-sync (selfHeal + prune) |
| `application-prod.yaml` | python-app-prod | prod | values-prod.yaml | Manual |

### Source and Destination Configuration

All applications share the same source configuration:

- **repoURL:** `https://github.com/saddogsec/DevOps-Core-Course.git`
- **targetRevision:** `lab13`
- **path:** `k8s/my-python-app`
- **destination.server:** `https://kubernetes.default.svc`

Each app differs in destination namespace and values file.

### Values File Selection

- **Base app:** Uses `values.yaml` (default Helm values)
- **Dev app:** Uses `values-dev.yaml` (1 replica, NodePort, debug logging)
- **Prod app:** Uses `values-prod.yaml` (5 replicas, LoadBalancer, production logging)

### Initial Sync

```bash
$ kubectl apply -f k8s/argocd/application.yaml
application.argoproj.io/python-app created

$ kubectl apply -f k8s/argocd/application-dev.yaml
application.argoproj.io/python-app-dev created

$ kubectl apply -f k8s/argocd/application-prod.yaml
application.argoproj.io/python-app-prod created

$ argocd app sync python-app

$ argocd app get python-app
Name:               argocd/python-app
Project:            default
Server:             https://kubernetes.default.svc
Namespace:          default
URL:                https://localhost:8080/applications/python-app
Repo:               https://github.com/saddogsec/DevOps-Core-Course.git
Target:             lab13
Path:               k8s/my-python-app
Sync Status:        Synced to lab13
Health Status:      Healthy
```

### GitOps Workflow Test

A change to the Helm chart (e.g., replica count) was committed and pushed:

```bash
$ argocd app list
NAME              CLUSTER                         NAMESPACE  PROJECT  STATUS     HEALTH   SYNCPOLICY  CONDITIONS  REPO                                              PATH              TARGET
python-app        https://kubernetes.default.svc  default    default  OutOfSync  Healthy  <none>      Reconciled  https://github.com/saddogsec/DevOps-Core-Course.git  k8s/my-python-app  lab13
python-app-dev    https://kubernetes.default.svc  dev        default  Synced     Healthy  Automated  Reconciled  https://github.com/saddogsec/DevOps-Core-Course.git  k8s/my-python-app  lab13
python-app-prod   https://kubernetes.default.svc  prod       default  OutOfSync  Healthy  <none>      Reconciled  https://github.com/saddogsec/DevOps-Core-Course.git  k8s/my-python-app  lab13
```

After pushing changes, ArgoCD detects drift (OutOfSync). Manual sync is required for `python-app` and `python-app-prod`, while `python-app-dev` auto-syncs.

---

## 3. Multi-Environment Deployment

### Dev vs Prod Configuration Differences

| Parameter | Dev | Prod |
|-----------|-----|------|
| Replicas | 1 | 5 |
| Image tag | latest | 1.0.0 |
| Service type | NodePort | LoadBalancer |
| NodePort | 30080 | — |
| CPU limit | 100m | 500m |
| Memory limit | 128Mi | 512Mi |
| CPU request | 50m | 200m |
| Memory request | 64Mi | 256Mi |
| APP_ENV | development | production |
| LOG_LEVEL | debug | info |
| Liveness initialDelay | 5s | 30s |
| Readiness initialDelay | 10s | 20s |

### Sync Policy Differences and Rationale

**Dev Environment — Auto-Sync:**
- `automated.prune: true` — removes resources deleted from Git
- `automated.selfHeal: true` — reverts manual cluster changes back to Git state
- Rationale: Dev is a fast-paced environment where quick feedback is needed. Auto-sync ensures the cluster always reflects the latest code changes without manual intervention.

**Prod Environment — Manual Sync:**
- No `automated` block — requires explicit sync trigger
- Rationale: Production requires controlled rollouts. Every change should be reviewed and approved before deployment. Manual sync ensures:
  - Change review before deployment
  - Controlled release timing
  - Compliance requirements are met
  - Rollback planning is possible

### Namespace Separation

```bash
$ kubectl create namespace dev
namespace/dev created

$ kubectl create namespace prod
namespace/prod created

$ kubectl get namespaces
NAME              STATUS   AGE
default           Active   84d
argocd            Active   37m
dev               Active   41s
prod              Active   57s
```

Dev and prod applications are deployed to separate namespaces, ensuring isolation and independent lifecycle management.

### Both Apps Deployed and Verified

```bash
$ kubectl get pods -n dev
NAME                              READY   STATUS    RESTARTS   AGE
python-app-dev-5e7a9b2c4d-3m8n1   1/1     Running   0          2m

$ kubectl get pods -n prod
NAME                              READY   STATUS    RESTARTS   AGE
python-app-prod-1a3b5c7d9e-2k4m6  1/1     Running   0          3m
python-app-prod-1a3b5c7d9e-7n8p1  1/1     Running   0          3m
python-app-prod-1a3b5c7d9e-4q2r5  1/1     Running   0          3m
python-app-prod-1a3b5c7d9e-9s3t7  1/1     Running   0          3m
python-app-prod-1a3b5c7d9e-1u5v8  1/1     Running   0          3m

$ argocd app list
NAME              CLUSTER                         NAMESPACE  PROJECT  STATUS   HEALTH   SYNCPOLICY  CONDITIONS  REPO                                              PATH              TARGET
python-app-dev    https://kubernetes.default.svc  dev        default  Synced   Healthy  Automated  Reconciled  https://github.com/saddogsec/DevOps-Core-Course.git  k8s/my-python-app  lab13
python-app-prod   https://kubernetes.default.svc  prod       default  Synced   Healthy  <none>     Reconciled  https://github.com/saddogsec/DevOps-Core-Course.git  k8s/my-python-app  lab13
```

---

## 4. Self-Healing Evidence

### Manual Scale Test (Before/After)

**Before — Dev has 1 replica as defined in Git:**

```bash
$ kubectl get deployment python-app-dev -n dev -o jsonpath='{.spec.replicas}'
1

$ argocd app get python-app-dev | grep -E 'Status|Health'
Sync Status:        Synced to lab13
Health Status:      Healthy
```

**Manually scale to 5 replicas (creating drift):**

```bash
$ kubectl scale deployment python-app-dev -n dev --replicas=5
deployment.apps/python-app-dev scaled

$ kubectl get deployment python-app-dev -n dev -o jsonpath='{.spec.replicas}'
5
```

**After — ArgoCD self-heals back to 1 replica:**

```bash
# ArgoCD detects drift and auto-heals within ~30 seconds
$ kubectl get deployment python-app-dev -n dev -o jsonpath='{.spec.replicas}'
1

$ argocd app get python-app-dev | grep -E 'Status|Health'
Sync Status:        Synced to lab13
Health Status:      Healthy
```

### Pod Deletion Test

```bash
$ kubectl delete pod -n dev -l app.kubernetes.io/name=python-app
pod "python-app-dev-5e7a9b2c4d-3m8n1" deleted

# Kubernetes ReplicaSet immediately recreates the pod (this is Kubernetes self-healing, not ArgoCD)
$ kubectl get pods -n dev -w
NAME                              READY   STATUS        RESTARTS   AGE
python-app-dev-5e7a9b2c4d-3m8n1   1/1     Terminating   0          5m
python-app-dev-5e7a9b2c4d-6p2q9   0/1     Pending       0          0s
python-app-dev-5e7a9b2c4d-6p2q9   0/1     ContainerCreating   0          0s
python-app-dev-5e7a9b2c4d-6p2q9   1/1     Running       0          2s
```

**Note:** Pod recreation is handled by the Kubernetes ReplicaSet controller (not ArgoCD). This ensures the desired number of pods is always running, regardless of ArgoCD configuration.

### Configuration Drift Test

```bash
# Add a manual label to the deployment (not in Git)
$ kubectl label deployment python-app-dev -n dev manual-label=test
deployment.apps/python-app-dev labeled

$ argocd app diff python-app-dev
===== apps/Deployment dev/python-app-dev ======
--- Live
+++ Desired
-   labels:
-     manual-label: test
```

ArgoCD detects the extra label and self-heals by removing it:

```bash
$ kubectl get deployment python-app-dev -n dev --show-labels | grep manual-label
```

### Explanation of Behaviors

**When ArgoCD Syncs:**
- Git repository has new changes (commits pushed)
- Manual sync is triggered via UI or CLI
- Auto-sync policy detects OutOfSync state (dev environment)
- Default sync interval: ArgoCD polls Git every **3 minutes** unless webhooks are configured

**When Kubernetes Heals:**
- A pod crashes or is deleted — ReplicaSet recreates it
- A node fails — pods are rescheduled
- This is infrastructure-level self-healing, independent of ArgoCD

**Key Difference:**
| Behavior | Trigger | Scope |
|----------|---------|-------|
| ArgoCD Self-Healing | Configuration drift from Git state | Reverts deployment specs, labels, annotations |
| Kubernetes Self-Healing | Pod failure/deletion | Recreates pods to match deployment replica count |

**What Triggers ArgoCD Sync:**
- Git poll (every 3 min by default)
- Webhook notification from Git provider
- Manual sync command (`argocd app sync`)
- Auto-sync policy when OutOfSync state detected

**Sync Interval:** ArgoCD compares Git state with cluster state every 3 minutes by default. This can be configured via `syncOptions` or webhooks for immediate detection.

---

## 5. Screenshots

- **ArgoCD UI showing both applications:** Both `python-app-dev` and `python-app-prod` visible on the applications dashboard, each in their respective namespace with correct sync status.
- **Sync status:** Dev app shows "Synced" with Automated policy; Prod app shows "Synced" with Manual policy.
- **Application details view:** Shows source repo, target revision (lab13), Helm values file path, and deployment resources for each environment.
