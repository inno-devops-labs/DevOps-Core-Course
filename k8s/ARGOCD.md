# Lab 13 — GitOps with ArgoCD

## 1. ArgoCD Setup

### Installation

ArgoCD was installed via Helm in a dedicated namespace:

```bash
helm repo add argo https://argoproj.github.io/argo-helm
helm repo update
kubectl create namespace argocd
helm install argocd argo/argo-cd --namespace argocd
```

### Installation verification

All core ArgoCD components were running in the `argocd` namespace:

- `argocd-application-controller-0`
- `argocd-applicationset-controller-...`
- `argocd-dex-server-...`
- `argocd-notifications-controller-...`
- `argocd-redis-...`
- `argocd-repo-server-...`
- `argocd-server-...`

### UI access

The ArgoCD UI was accessed using port forwarding:

```bash
kubectl port-forward svc/argocd-server -n argocd 8080:443
```

Then the UI was opened at:

```text
https://localhost:8080
```

Initial admin password was retrieved with:

```bash
kubectl -n argocd get secret argocd-initial-admin-secret -o jsonpath="{.data.password}" | base64 -d
```

### CLI installation

The ArgoCD CLI was installed on macOS with:

```bash
brew install argocd
```

### CLI login

The CLI was configured with:

```bash
argocd login localhost:8080 --insecure
```

This allowed querying and syncing applications directly from the terminal.

---

## 2. Application Configuration

### Main ArgoCD application

A base application named `app-python` was created in ArgoCD UI with the following source settings:

- **Repository URL:** `https://github.com/ostxxp/DevOps-Core-Course`
- **Target revision:** `lab13`
- **Path:** `app-python-chart`

### Destination

- **Cluster:** `https://kubernetes.default.svc`
- **Namespace:** `default`

### Sync policy

The main application was configured with:
- **Automatic sync**

### Final status

ArgoCD CLI output confirmed:

- `Sync Status: Synced`
- `Health Status: Healthy`

Relevant output:

```text
Name:               argocd/app-python
Project:            default
Server:             https://kubernetes.default.svc
Namespace:          default
Source:
- Repo:             https://github.com/ostxxp/DevOps-Core-Course
  Target:           lab13
  Path:             app-python-chart
Sync Policy:        Automated
Sync Status:        Synced to lab13 (ecf381a)
Health Status:      Healthy
```

### Initial issues and fixes

The first deployment attempt failed because `nodePort: 30007` was already occupied by a previous release.  
The fix was to update the Helm chart to use a different NodePort (`30008`) and switch the ArgoCD application source revision from `lab12` to `lab13`.

A second issue occurred because Vault dev-mode had lost its Kubernetes auth configuration.  
This was fixed by:
- re-enabling Kubernetes auth in Vault
- re-creating the Vault policy and role
- re-writing the secret path
- restarting the affected deployment

After this, the ArgoCD-managed application became healthy.

---

## 3. Multi-Environment Deployment

### Namespaces

Separate namespaces were created for development and production:

```bash
kubectl create namespace dev
kubectl create namespace prod
```

### Environment-specific values files

Two Helm values files were added:

- `app-python-chart/values-dev.yaml`
- `app-python-chart/values-prod.yaml`

#### Development configuration

```yaml
replicaCount: 1

service:
  type: NodePort
  port: 80
  targetPort: 5000
  nodePort: 30009

resources:
  limits:
    cpu: 150m
    memory: 192Mi
  requests:
    cpu: 50m
    memory: 64Mi
```

#### Production configuration

```yaml
replicaCount: 3

service:
  type: NodePort
  port: 80
  targetPort: 5000
  nodePort: 30010

resources:
  limits:
    cpu: 300m
    memory: 384Mi
  requests:
    cpu: 150m
    memory: 128Mi
```

### ArgoCD Application manifests

Two declarative Application manifests were created in:

```text
k8s/argocd/
```

Files:
- `application-dev.yaml`
- `application-prod.yaml`

### Dev application

The dev application uses:
- namespace: `dev`
- Helm values: `values.yaml`, `values-dev.yaml`
- **automatic sync**
- `prune: true`
- `selfHeal: true`

### Prod application

The prod application uses:
- namespace: `prod`
- Helm values: `values.yaml`, `values-prod.yaml`
- **manual sync**

### Why dev is automatic and prod is manual

This separation reflects a common GitOps best practice:

- **dev** should update quickly for testing and rapid iteration
- **prod** should remain controlled and require an explicit sync operation before changes go live

This reduces production risk and supports review/approval workflows.

### Final environment verification

#### Dev namespace

```text
deployment.apps/app-python-dev-app-python-chart   1/1     1            1           17m
pod/app-python-dev-app-python-chart-7778f9bf74-d24ft   2/2     Running   0          5m54s
service/app-python-dev-app-python-chart   NodePort   10.105.209.219   <none>   80:30009/TCP   17m
persistentvolumeclaim/app-python-dev-app-python-chart-data   Bound   pvc-e4c4166d-f525-4630-a965-650b751ecab2   100Mi   RWO   standard
```

#### Prod namespace

```text
deployment.apps/app-python-prod-app-python-chart   3/3     3            3           8m25s
pod/app-python-prod-app-python-chart-6dcc8cdf5f-7zcss   2/2     Running   0   8m25s
pod/app-python-prod-app-python-chart-6dcc8cdf5f-f2g5d   2/2     Running   0   8m25s
pod/app-python-prod-app-python-chart-6dcc8cdf5f-r28k9   2/2     Running   0   8m25s
service/app-python-prod-app-python-chart   NodePort   10.104.175.53   <none>   80:30010/TCP   8m25s
persistentvolumeclaim/app-python-prod-app-python-chart-data   Bound   pvc-5469f938-c464-446e-a41e-56a84b3a345a   100Mi   RWO   standard
```

### Application list verification

```text
NAME                    CLUSTER                         NAMESPACE  PROJECT  STATUS  HEALTH   SYNCPOLICY  CONDITIONS  REPO                                          PATH              TARGET
argocd/app-python       https://kubernetes.default.svc  default    default  Synced  Healthy  Auto        <none>      https://github.com/ostxxp/DevOps-Core-Course  app-python-chart  lab13
argocd/app-python-dev   https://kubernetes.default.svc  dev        default  Synced  Healthy  Auto-Prune  <none>      https://github.com/ostxxp/DevOps-Core-Course  app-python-chart  lab13
argocd/app-python-prod  https://kubernetes.default.svc  prod       default  Synced  Healthy  Manual      <none>      https://github.com/ostxxp/DevOps-Core-Course  app-python-chart  lab13
```

This confirmed:
- all three applications were visible in ArgoCD
- all were healthy
- sync policies differed correctly

---

## 4. Self-Healing Evidence

### Test 1 — Manual scale in dev

The development deployment was manually scaled:

```bash
kubectl scale deployment app-python-dev-app-python-chart -n dev --replicas=5
```

Immediately after scaling, the deployment showed:

```text
app-python-dev-app-python-chart   1/5
```

Kubernetes created additional pods to satisfy the modified deployment state.

However, because ArgoCD self-healing was enabled for dev, ArgoCD detected the configuration drift and automatically reverted the deployment back to the Git-defined state.

After a short delay, the deployment returned to:

```text
app-python-dev-app-python-chart   1/1
```

And ArgoCD reported:

- `Sync Status: Synced`
- `Health Status: Healthy`

This demonstrates **ArgoCD self-healing**.

### Test 2 — Pod deletion in dev

A pod in the dev namespace was manually deleted:

```bash
kubectl delete pod -n dev -l app.kubernetes.io/instance=app-python-dev
```

Kubernetes immediately recreated a replacement pod:

```text
app-python-dev-app-python-chart-7778f9bf74-d24ft   2/2   Running
```

This demonstrates **Kubernetes self-healing**, not ArgoCD self-healing.

#### Key distinction

- **Kubernetes self-healing** restores missing pods to satisfy Deployment/ReplicaSet state
- **ArgoCD self-healing** restores resource definitions back to the desired Git state

### Test 3 — Configuration drift

A manual label change on the deployment did not produce a strong visible drift signal in ArgoCD.  
To produce a clear and reproducible drift event, the deployment replicas were manually changed again:

```bash
kubectl scale deployment app-python-dev-app-python-chart -n dev --replicas=3
```

Immediately after the change:

```text
app-python-dev-app-python-chart   1/3
```

After approximately 15 seconds, ArgoCD automatically reverted the deployment to:

```text
app-python-dev-app-python-chart   1/1
```

This provided a second clear demonstration of Git-driven self-healing.

### Sync behavior explanation

ArgoCD reconciles cluster state against Git. If auto-sync and self-heal are enabled:
- changes pushed to Git are applied automatically
- manual cluster changes that differ from Git are reverted automatically

Kubernetes, on the other hand, only ensures controller-level desired state such as:
- pod count
- pod recreation
- Deployment/ReplicaSet health

### Sync interval

ArgoCD polls Git periodically (commonly around every 3 minutes by default), though sync can also happen:
- immediately via manual sync
- automatically after drift detection
- faster when webhooks are configured

---

## 5. GitOps Workflow Summary

This lab demonstrated the GitOps workflow in practice:

1. Helm chart and ArgoCD Application definitions were stored in Git
2. ArgoCD read the repository and deployed the resources declaratively
3. Dev and prod were separated by namespace and values files
4. Dev used automatic sync and self-healing
5. Prod used manual sync for controlled release behavior
6. Manual drift in dev was automatically corrected back to Git-defined state

This validates the core GitOps principle:

> Git is the source of truth, and the cluster is continuously reconciled to match Git.

---

## 6. Final Result

By the end of the lab, the following were successfully implemented:

- ArgoCD installed via Helm
- UI access configured via port-forward
- CLI installed and authenticated
- base application deployed from Git via ArgoCD
- declarative ArgoCD Application manifests created
- separate dev and prod environments deployed
- different Helm values applied per environment
- automatic sync enabled for dev
- manual sync retained for prod
- self-healing tested and verified
- distinction between Kubernetes healing and ArgoCD healing documented

This lab successfully demonstrated declarative GitOps deployment with ArgoCD, multi-environment delivery, and self-healing behavior.
