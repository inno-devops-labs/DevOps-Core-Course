# Lab 13 — GitOps with ArgoCD

## 1. ArgoCD Setup

ArgoCD was installed in the Kubernetes cluster using Helm.

### Installation commands

```bash
helm repo add argo https://argoproj.github.io/argo-helm
helm repo update
kubectl create namespace argocd
helm upgrade --install argocd argo/argo-cd -n argocd
kubectl get pods -n argocd
```

### Installation result

ArgoCD installation completed successfully:

```text
namespace/argocd created
Release "argocd" does not exist. Installing it now.
NAME: argocd
LAST DEPLOYED: Fri Apr 17 20:25:15 2026
NAMESPACE: argocd
STATUS: deployed
REVISION: 1
DESCRIPTION: Install complete
```

All core ArgoCD components reached the `Running` state:

```text
NAME                                                READY   STATUS    RESTARTS   AGE
argocd-application-controller-0                     1/1     Running   0          6m9s
argocd-applicationset-controller-59f6b7dd64-pq2db   1/1     Running   0          6m9s
argocd-dex-server-7b9588c494-g6gcr                  1/1     Running   0          6m9s
argocd-notifications-controller-8f6855454-7zm2q     1/1     Running   0          6m9s
argocd-redis-dc6b586fc-47ml7                        1/1     Running   0          6m9s
argocd-repo-server-5f4d44d9f8-4f9qh                 1/1     Running   0          6m9s
argocd-server-5f777b877f-n7z2t                      1/1     Running   0          6m9s
```

### UI access

ArgoCD UI was accessed through port-forwarding:

```bash
kubectl port-forward service/argocd-server -n argocd 8080:443
```

The initial admin password was retrieved with:

```bash
kubectl -n argocd get secret argocd-initial-admin-secret -o jsonpath="{.data.password}" | base64 -d && echo
```

### CLI access

The ArgoCD CLI was installed on macOS and used to log in to the server:

```bash
brew install argocd
argocd login localhost:8080 --insecure
argocd app list
```

This confirmed that the CLI was working and connected to the ArgoCD server.

---

## 2. Application Configuration

### Repository and chart source

The ArgoCD applications were configured to use the Git repository as the source of truth:

```text
Repo:   https://github.com/Darriyano/DevOps-Core-Course.git
Target: lab13
Path:   k8s/python-app
```

The Helm chart from previous labs was reused without changing the overall GitOps idea.

### Application manifests

The following manifests were created:

```text
k8s/argocd/application.yaml
k8s/argocd/application-dev.yaml
k8s/argocd/application-prod.yaml
k8s/argocd/namespaces.yaml
k8s/ARGOCD.md
```

### Task 2 — single application deployment

A single ArgoCD application named `python-app` was created first in the `default` namespace with manual sync.

Observed ArgoCD application state:

```text
Name:               argocd/python-app
Project:            default
Server:             https://kubernetes.default.svc
Namespace:          default
Source:
- Repo:             https://github.com/Darriyano/DevOps-Core-Course.git
  Target:           lab13
  Path:             k8s/python-app
  Helm Values:      values.yaml
Sync Policy:        Manual
Sync Status:        Synced to lab13
Health Status:      Healthy
```

Relevant synced resources:

```text
ConfigMap              default    python-app-config       Synced
ConfigMap              default    python-app-env          Synced
PersistentVolumeClaim  default    python-app-data         Synced   Healthy
Secret                 default    python-app-secret       Synced
Service                default    python-app              Synced   Healthy
ServiceAccount         default    python-app              Synced
Deployment             default    python-app              Synced   Healthy
```

### Single application verification

The application was reachable through the NodePort service and returned healthy responses:

```bash
curl http://127.0.0.1:54872/health
curl http://127.0.0.1:54872/visits
```

Observed output:

```text
{"status":"healthy","timestamp":"2026-04-17T16:23:06.151418+00:00","uptime_seconds":680}
{"visits":0,"file":"/data/visits"}
```

This confirmed that the initial ArgoCD-managed deployment worked correctly.

---

## 3. Multi-Environment Deployment

### Namespace separation

Separate namespaces for development and production were created:

```bash
kubectl apply -f k8s/argocd/namespaces.yaml
kubectl get ns dev prod
```

Observed output:

```text
namespace/dev created
namespace/prod created
NAME   STATUS   AGE
dev    Active   0s
prod   Active   0s
```

### Dev application

The `python-app-dev` application was configured with:
- destination namespace `dev`
- `values-dev.yaml`
- automated sync
- `prune: true`
- `selfHeal: true`

Observed state:

```text
Name:               argocd/python-app-dev
Namespace:          dev
Helm Values:        values-dev.yaml
Sync Policy:        Automated (Prune)
Sync Status:        Synced to lab13
Health Status:      Healthy
```

Observed dev resources:

```text
pod/python-app-dev-78f6bb67f5-bqptz   1/1   Running
service/python-app-dev                NodePort   80:30081/TCP
deployment.apps/python-app-dev        1/1   1   1
configmap/python-app-dev-config
configmap/python-app-dev-env
secret/python-app-dev-secret
persistentvolumeclaim/python-app-dev-data   Bound
serviceaccount/python-app-dev
```

### Prod application

The `python-app-prod` application was configured with:
- destination namespace `prod`
- `values-prod.yaml`
- manual sync only

Observed state before manual sync:

```text
Name:               argocd/python-app-prod
Namespace:          prod
Helm Values:        values-prod.yaml
Sync Policy:        Manual
Sync Status:        OutOfSync
Health Status:      Missing
```

After manual synchronization, the production application became available and responded correctly through port-forwarding.

### Environment access verification

#### Dev

The dev environment was accessed through the NodePort service:

```bash
curl http://127.0.0.1:54872/health
curl http://127.0.0.1:54872/visits
```

Observed output:

```text
{"status":"healthy","timestamp":"2026-04-17T16:23:06.151418+00:00","uptime_seconds":680}
{"visits":0,"file":"/data/visits"}
```

#### Prod

The prod environment was accessed through port-forwarding to the service:

```bash
curl http://127.0.0.1:8082/health
curl http://127.0.0.1:8082/visits
```

Observed output:

```text
{"status":"healthy","timestamp":"2026-04-17T16:23:26.692630+00:00","uptime_seconds":240}
{"visits":0,"file":"/data/visits"}
```

### Dev vs Prod differences

| Property | Dev | Prod |
|---|---|---|
| Namespace | `dev` | `prod` |
| Values file | `values-dev.yaml` | `values-prod.yaml` |
| Sync policy | Automatic | Manual |
| Purpose | fast iteration and self-healing | controlled deployment |

### Why prod was kept manual

Production was intentionally left on manual sync because it provides:
- controlled rollout timing
- explicit review before deployment
- safer operational behavior
- clearer separation between development and production workflows

---

## 4. Self-Healing and Drift Detection

All self-healing tests were performed on `python-app-dev`, because automated sync and self-heal were enabled only in the development environment.

### 4.1 Manual scale drift test

Initial state before modification:

```text
NAME             READY   UP-TO-DATE   AVAILABLE   AGE
python-app-dev   1/1     1            1           13m

Sync Policy:     Automated (Prune)
Sync Status:     Synced
Health Status:   Healthy
```

Manual scale command:

```bash
kubectl scale deployment python-app-dev -n dev --replicas=5
```

Observed result:

```text
deployment.apps/python-app-dev scaled
```

Observed pod behavior:

```text
python-app-dev-78f6bb67f5-2s59n   1/1   Terminating
python-app-dev-78f6bb67f5-9cncm   1/1   Terminating
python-app-dev-78f6bb67f5-bqptz   1/1   Running
python-app-dev-78f6bb67f5-dvn9q   0/1   Terminating
python-app-dev-78f6bb67f5-xdbm9   1/1   Terminating
```

After reconciliation, ArgoCD again reported:

```text
Sync Status:     Synced
Health Status:   Healthy
```

**Explanation:** the number of replicas was changed manually in the live cluster, but ArgoCD detected the drift and restored the deployment to the state described in Git (`replicaCount: 1` in `values-dev.yaml`).

### 4.2 Pod deletion test

Manual deletion command:

```bash
kubectl delete pod -n dev -l app.kubernetes.io/name=python-app
kubectl get pods -n dev -w
```

Observed output:

```text
pod "python-app-dev-78f6bb67f5-bqptz" deleted from dev namespace
python-app-dev-78f6bb67f5-wjcnk   0/1   Running   0   2s
```

**Explanation:** this is Kubernetes self-healing, not ArgoCD self-healing. The Deployment/ReplicaSet controller recreated the deleted pod automatically.

### 4.3 Configuration drift test

A manual patch was applied to replace the deployment image:

```bash
kubectl patch deployment python-app-dev -n dev --type='json' -p='[{"op":"replace","path":"/spec/template/spec/containers/0/image","value":"nginx:latest"}]'
```

Observed result:

```text
deployment.apps/python-app-dev patched
```

Immediately after that, the live deployment again reported the desired image from Git:

```bash
kubectl get deployment python-app-dev -n dev -o jsonpath='{.spec.template.spec.containers[0].image}'; echo
```

Observed output:

```text
python-app:latest
```

ArgoCD status remained:

```text
Sync Status:     Synced
Health Status:   Healthy
```

**Explanation:** ArgoCD detected that the live deployment image had been changed manually and restored it to the Git-defined value (`python-app:latest`). This demonstrates configuration drift correction.

### Sync behavior summary

- **Kubernetes self-healing:** recreates missing pods to satisfy Deployment/ReplicaSet requirements.
- **ArgoCD self-healing:** restores cluster configuration so that it matches the desired state stored in Git.

---

## 5. Screenshots

### Screenshot 1 — single application view

![alt text](image.png)

### Screenshot 2 — multi-environment view

![alt text](image-1.png)

## 6. Conclusion

In this lab, GitOps continuous deployment was implemented with ArgoCD for the existing Helm-based application.

Completed results:
- ArgoCD was installed successfully with Helm
- UI and CLI access were configured
- a single manual-synced application was deployed from Git
- separate `dev` and `prod` environments were created
- automatic sync and self-healing were enabled for `dev`
- manual sync was preserved for `prod`
- application health was verified in both environments
- drift recovery was demonstrated for scaling changes and configuration changes
- the difference between Kubernetes self-healing and ArgoCD self-healing was validated

The lab therefore demonstrates a working GitOps workflow where Git is the source of truth and ArgoCD continuously enforces the desired cluster state.
