# Lab 13 — GitOps with ArgoCD

## 1. ArgoCD Setup

### 1.1 Installation via Helm

```bash
helm repo add argo https://argoproj.github.io/argo-helm
helm repo update
kubectl create namespace argocd
helm upgrade --install argocd argo/argo-cd -n argocd
kubectl get pods -n argocd
kubectl wait --for=condition=ready pod -l app.kubernetes.io/name=argocd-server -n argocd --timeout=180s
```

Installation output:

```bash
PS C:\Users\zagur\DevOps\DevOps-Core-Course> kubectl create namespace argocd
namespace/argocd created
PS C:\Users\zagur\DevOps\DevOps-Core-Course> helm upgrade --install argocd argo/argo-cd -n argocd
Release "argocd" does not exist. Installing it now.
NAME: argocd
LAST DEPLOYED: Thu Apr 16 18:23:29 2026
NAMESPACE: argocd
STATUS: deployed
REVISION: 1
DESCRIPTION: Install complete
TEST SUITE: None
NOTES:
In order to access the server UI you have the following options:

1. kubectl port-forward service/argocd-server -n argocd 8080:443

    and then open the browser on http://localhost:8080 and accept the certificate

2. enable ingress in the values file `server.ingress.enabled` and either
      - Add the annotation for ssl passthrough: https://argo-cd.readthedocs.io/en/stable/operator-manual/ingress/#option-1-ssl-passthrough
      - Set the `configs.params."server.insecure"` in the values file and terminate SSL at your ingress: https://argo-cd.readthedocs.io/en/stable/operator-manual/ingress/#option-2-multiple-ingress-objects-and-hosts


After reaching the UI the first time you can login with username: admin and the random password generated during the installation. You can find the password by running:

kubectl -n argocd get secret argocd-initial-admin-secret -o jsonpath="{.data.password}" | base64 -d

(You should delete the initial secret afterwards as suggested by the Getting Started Guide: https://argo-cd.readthedocs.io/en/stable/getting_started/#4-login-using-the-cli)
PS C:\Users\zagur\DevOps\DevOps-Core-Course> kubectl get pods -n argocd                              
NAME                                               READY   STATUS              RESTARTS   AGE
argocd-application-controller-0                    0/1     Running             0          13s
argocd-applicationset-controller-9f85b7f7d-xpxbr   1/1     Running             0          13s
argocd-dex-server-64766d9569-zp5zt                 0/1     PodInitializing     0          13s
argocd-notifications-controller-cdf598886-qw8jg    1/1     Running             0          13s
argocd-redis-7476bcff9b-svm5v                      0/1     ContainerCreating   0          13s
argocd-redis-secret-init-qfbp6                     0/1     Completed           0          42s
argocd-repo-server-76c5f678c7-jg4bt                0/1     Running             0          13s
argocd-server-66c66bcc9f-vnhwt                     0/1     Running             0          13s
PS C:\Users\zagur\DevOps\DevOps-Core-Course> kubectl wait --for=condition=ready pod -l app.kubernetes.io/name=argocd-server -n argocd --timeout=180s
pod/argocd-server-66c66bcc9f-vnhwt condition met
```

Result:
- ArgoCD was installed in the dedicated `argocd` namespace.
- Core components started successfully.
- The ArgoCD server became ready and accessible.

### 1.2 Accessing the UI

```bash
kubectl port-forward svc/argocd-server -n argocd 8080:443
```

ArgoCD UI URL:

```text
https://localhost:8080
```

Username:

```text
admin
```

Initial password retrieval:

```bash
PS C:\Users\zagur\DevOps\DevOps-Core-Course> kubectl -n argocd get secret argocd-initial-admin-secret -o jsonpath="{.data.password}" | ForEach-Object { [System.Text.Encoding]::UTF8.GetString([System.Convert]::FromBase64String($_)) }
PASSWORD
```

Port-forward output:

```bash
PS C:\Users\zagur\DevOps\DevOps-Core-Course> kubectl port-forward svc/argocd-server -n argocd 8080:443
Forwarding from 127.0.0.1:8080 -> 8080
Forwarding from [::1]:8080 -> 8080
Handling connection for 8080
Handling connection for 8080
Handling connection for 8080
Handling connection for 8080
Handling connection for 8080
Handling connection for 8080
```

Screenshot:

![](/k8s/screenshots/argo_ui.png)

### 1.3 CLI Installation and Login

Windows PowerShell installation:

```powershell
$version = (Invoke-RestMethod https://api.github.com/repos/argoproj/argo-cd/releases/latest).tag_name
$url = "https://github.com/argoproj/argo-cd/releases/download/" + $version + "/argocd-windows-amd64.exe"
Invoke-WebRequest -Uri $url -OutFile argocd.exe
```

Login and verification:

```bash
argocd login localhost:8080 --insecure
argocd app list
```

CLI verification output:

```bash
PS C:\Users\zagur\DevOps\DevOps-Core-Course> .\argocd app list
NAME                             CLUSTER                         NAMESPACE  PROJECT  STATUS  HEALTH   SYNCPOLICY  CONDITIONS  REPO                                                PATH                     TARGET
argocd/devops-info-service       https://kubernetes.default.svc  default    default  Synced  Healthy  Manual      <none>      https://github.com/wkwtfigo/DevOps-Core-Course.git  k8s/devops-info-service  master
argocd/devops-info-service-dev   https://kubernetes.default.svc  dev        default  Synced  Healthy  Auto-Prune  <none>      https://github.com/wkwtfigo/DevOps-Core-Course.git  k8s/devops-info-service  master
argocd/devops-info-service-prod  https://kubernetes.default.svc  prod       default  Synced  Healthy  Manual      <none>      https://github.com/wkwtfigo/DevOps-Core-Course.git  k8s/devops-info-service  master
```

Result:
- The CLI connected successfully to the ArgoCD server.
- All three applications were visible from the command line.

---

## 2. Application Configuration

This lab uses ArgoCD `Application` manifests stored in `k8s/argocd/`.

### 2.1 Manual Application for Initial Deployment

File: `k8s/argocd/application.yaml`

```yaml
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: devops-info-service
  namespace: argocd
spec:
  project: default
  source:
    repoURL: https://github.com/wkwtfigo/DevOps-Core-Course.git
    targetRevision: master
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
```

Apply it and sync:

```bash
kubectl apply -f k8s/argocd/application.yaml
argocd app get devops-info-service
argocd app sync devops-info-service
kubectl get all -n default
```

Observed state:

```bash
PS C:\Users\zagur\DevOps\DevOps-Core-Course> .\argocd app get devops-info-service
Name:               argocd/devops-info-service
Project:            default
Server:             https://kubernetes.default.svc
Namespace:          default
URL:                https://argocd.example.com/applications/devops-info-service
Source:
- Repo:             https://github.com/wkwtfigo/DevOps-Core-Course.git
  Target:           master
  Path:             k8s/devops-info-service
  Helm Values:      values.yaml
SyncWindow:         Sync Allowed
Sync Policy:        Manual
Sync Status:        Synced to master (742a8e9)
Health Status:      Healthy

GROUP  KIND                   NAMESPACE  NAME                                                  STATUS     HEALTH   HOOK      MESSAGE
batch  Job                    default    devops-info-service-devops-info-service-pre-install   Succeeded           PreSync   Reached expected number of succeeded pods
       ServiceAccount         default    devops-info-service-devops-info-service               Synced                        serviceaccount/devops-info-service-devops-info-service unchanged
       Secret                 default    devops-info-service-devops-info-service-secret        Synced                        secret/devops-info-service-devops-info-service-secret configured
       ConfigMap              default    devops-info-service-devops-info-service-config        Synced                        configmap/devops-info-service-devops-info-service-config unchanged
       ConfigMap              default    devops-info-service-devops-info-service-env           Synced                        configmap/devops-info-service-devops-info-service-env unchanged
       PersistentVolumeClaim  default    devops-info-service-devops-info-service-data          Synced     Healthy            persistentvolumeclaim/devops-info-service-devops-info-service-data unchanged
       Service                default    devops-info-service-devops-info-service               Synced     Healthy            service/devops-info-service-devops-info-service unchanged
apps   Deployment             default    devops-info-service-devops-info-service               Synced     Healthy            deployment.apps/devops-info-service-devops-info-service configured
batch  Job                    default    devops-info-service-devops-info-service-post-install  Succeeded           PostSync  Reached expected number of succeeded pods
```

Interpretation:
- The initial application used manual sync.
- ArgoCD successfully rendered and deployed the Helm chart from Git.
- The application reached `Synced` and `Healthy` states.

### 2.2 Source and Destination Configuration

The initial ArgoCD Application was configured with:
- **Repository:** `https://github.com/wkwtfigo/DevOps-Core-Course.git`
- **Branch:** `master`
- **Chart path:** `k8s/devops-info-service`
- **Values file:** `values.yaml`
- **Target namespace:** `default`

This means Git is the source of truth, while ArgoCD continuously compares the cluster state with the manifests produced from the Helm chart in the repository.

### 2.3 GitOps Workflow Test

A Git change was committed and pushed to the repository. ArgoCD then compared the live cluster state with the updated Git state.

![](/k8s/screenshots/commit.png)

Commands used:

```bash
argocd app get devops-info-service
argocd app diff devops-info-service
```

```bash
PS C:\Users\zagur\DevOps\DevOps-Core-Course> .\argocd app get devops-info-service
Name:               argocd/devops-info-service
Project:            default
Server:             https://kubernetes.default.svc
Namespace:          default
URL:                https://argocd.example.com/applications/devops-info-service
Source:
- Repo:             https://github.com/wkwtfigo/DevOps-Core-Course.git
  Target:           master
  Path:             k8s/devops-info-service
  Helm Values:      values.yaml
SyncWindow:         Sync Allowed
Sync Policy:        Manual
Sync Status:        Synced to master (742a8e9)
Health Status:      Healthy

GROUP  KIND                   NAMESPACE  NAME                                                  STATUS     HEALTH   HOOK      MESSAGE
batch  Job                    default    devops-info-service-devops-info-service-pre-install   Succeeded           PreSync   Reached expected number of succeeded pods
       ServiceAccount         default    devops-info-service-devops-info-service               Synced                        serviceaccount/devops-info-service-devops-info-service unchanged
       Secret                 default    devops-info-service-devops-info-service-secret        Synced                        secret/devops-info-service-devops-info-service-secret configured
       ConfigMap              default    devops-info-service-devops-info-service-config        Synced                        configmap/devops-info-service-devops-info-service-config unchanged
       ConfigMap              default    devops-info-service-devops-info-service-env           Synced                        configmap/devops-info-service-devops-info-service-env unchanged
       PersistentVolumeClaim  default    devops-info-service-devops-info-service-data          Synced     Healthy            persistentvolumeclaim/devops-info-service-devops-info-service-data unchanged
       Service                default    devops-info-service-devops-info-service               Synced     Healthy            service/devops-info-service-devops-info-service unchanged
apps   Deployment             default    devops-info-service-devops-info-service               Synced     Healthy            deployment.apps/devops-info-service-devops-info-service configured
batch  Job                    default    devops-info-service-devops-info-service-post-install  Succeeded           PostSync  Reached expected number of succeeded pods
PS C:\Users\zagur\DevOps\DevOps-Core-Course> .\argocd app diff devops-info-service
PS C:\Users\zagur\DevOps\DevOps-Core-Course> 
```

Observed result:
- The application remained in `Synced` state after the tested change was applied and reconciled.
- `argocd app diff` returned no output after synchronization, which means the live cluster matched the manifests stored in Git.

---

## 3. Multi-Environment Deployment

### 3.1 Namespaces

```bash
kubectl apply -f k8s/argocd/namespaces.yaml
kubectl get ns dev prod
```

Output:

```bash
PS C:\Users\zagur\DevOps\DevOps-Core-Course> kubectl get ns dev prod            
NAME   STATUS   AGE
dev    Active   5s
prod   Active   5s
```

This separation isolates the environments and allows different sync policies and Helm values to be applied independently.

### 3.2 Dev Application (Auto-Sync)

File: `k8s/argocd/application-dev.yaml`

```yaml
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: devops-info-service-dev
  namespace: argocd
spec:
  project: default
  source:
    repoURL: https://github.com/wkwtfigo/DevOps-Core-Course.git
    targetRevision: master
    path: k8s/devops-info-service
    helm:
      valueFiles:
        - values-dev.yaml
  destination:
    server: https://kubernetes.default.svc
    namespace: dev
  syncPolicy:
    automated:
      prune: true
      selfHeal: true
    syncOptions:
      - CreateNamespace=true
```

### 3.3 Prod Application (Manual Sync)

File: `k8s/argocd/application-prod.yaml`

```yaml
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: devops-info-service-prod
  namespace: argocd
spec:
  project: default
  source:
    repoURL: https://github.com/wkwtfigo/DevOps-Core-Course.git
    targetRevision: master
    path: k8s/devops-info-service
    helm:
      valueFiles:
        - values-prod.yaml
  destination:
    server: https://kubernetes.default.svc
    namespace: prod
  syncPolicy:
    syncOptions:
      - CreateNamespace=true
```

### 3.4 Deploying Both Applications

```bash
kubectl apply -f k8s/argocd/application-dev.yaml
kubectl apply -f k8s/argocd/application-prod.yaml
argocd app list
```

Output:

```bash
PS C:\Users\zagur\DevOps\DevOps-Core-Course> .\argocd app list                                                          
NAME                             CLUSTER                         NAMESPACE  PROJECT  STATUS  HEALTH   SYNCPOLICY  CONDITIONS  REPO                                                PATH                     TARGET
argocd/devops-info-service       https://kubernetes.default.svc  default    default  Synced  Healthy  Manual      <none>      https://github.com/wkwtfigo/DevOps-Core-Course.git  k8s/devops-info-service  master
argocd/devops-info-service-dev   https://kubernetes.default.svc  dev        default  Synced  Healthy  Auto-Prune  <none>      https://github.com/wkwtfigo/DevOps-Core-Course.git  k8s/devops-info-service  master
argocd/devops-info-service-prod  https://kubernetes.default.svc  prod       default  Synced  Healthy  Manual      <none>      https://github.com/wkwtfigo/DevOps-Core-Course.git  k8s/devops-info-service  master
PS C:\Users\zagur\DevOps\DevOps-Core-Course> 
```

Initial sync and verification:

```bash
argocd app sync devops-info-service-dev
argocd app sync devops-info-service-prod
kubectl get pods -n dev
kubectl get pods -n prod
```

Output:

```bash
PS C:\Users\zagur\DevOps\DevOps-Core-Course> kubectl get pods -n dev
NAME                                                          READY   STATUS    RESTARTS   AGE
devops-info-service-dev-devops-info-service-b6588bcfd-vgmc6   2/2     Running   0          26m

PS C:\Users\zagur\DevOps\DevOps-Core-Course> kubectl get pods -n prod
NAME                                                            READY   STATUS    RESTARTS   AGE
devops-info-service-prod-devops-info-service-5888c57f44-654nb   2/2     Running   0          25m
```

![](/k8s/screenshots/argo_ui.png)

### 3.5 Dev vs Prod Differences

**Dev environment**
- Namespace: `dev`
- Helm values file: `values-dev.yaml`
- Sync policy: automated with `prune: true` and `selfHeal: true`
- Purpose: fast feedback and automatic correction of drift

**Prod environment**
- Namespace: `prod`
- Helm values file: `values-prod.yaml`
- Sync policy: manual
- Purpose: controlled deployments with explicit operator approval

### 3.6 Why Auto-Sync in Dev and Manual Sync in Prod

Keeping `dev` automated is useful because the environment is intended for quick iteration and testing. If someone changes a managed resource manually, ArgoCD can restore the Git-defined state automatically.

Keeping `prod` manual is safer because production changes should be deliberate and reviewed. Manual sync reduces the risk of deploying unintended changes immediately after a commit.

---

## 4. Self-Healing Evidence

### 4.1 Manual Scale Test in Dev

The `dev` application had automated sync with self-healing enabled.

Commands used:

```bash
kubectl get deploy -n dev
kubectl scale deployment devops-info-service-dev-devops-info-service -n dev --replicas=5
kubectl get pods -n dev -w
argocd app get devops-info-service-dev --hard-refresh
argocd app diff devops-info-service-dev
```

Observed output:

```bash
PS C:\Users\zagur\DevOps\DevOps-Core-Course> kubectl scale deployment devops-info-service-dev-devops-info-service -n dev --replicas=5
deployment.apps/devops-info-service-dev-devops-info-service scaled

PS C:\Users\zagur\DevOps\DevOps-Core-Course> .\argocd app get devops-info-service-dev --hard-refresh
Name:               argocd/devops-info-service-dev
Project:            default
Server:             https://kubernetes.default.svc
Namespace:          dev
URL:                https://argocd.example.com/applications/devops-info-service-dev
Source:
- Repo:             https://github.com/wkwtfigo/DevOps-Core-Course.git
  Target:           master
  Path:             k8s/devops-info-service
  Helm Values:      values-dev.yaml
SyncWindow:         Sync Allowed
Sync Policy:        Automated (Prune)
Sync Status:        Synced to master (742a8e9)
Health Status:      Healthy
```

Additional deployment events confirmed the rollback to the Git-defined replica count:

```bash
Events:
  Type    Reason             Age                From                   Message
  ----    ------             ----               ----                   -------
  Normal  ScalingReplicaSet  58m (x2 over 64m)  deployment-controller  Scaled up replica set devops-info-service-dev-devops-info-service-b6588bcfd from 1 to 5
  Normal  ScalingReplicaSet  58m (x2 over 64m)  deployment-controller  Scaled down replica set devops-info-service-dev-devops-info-service-b6588bcfd from 5 to 1
```

Interpretation:
- The Deployment was manually scaled to 5 replicas.
- The live state no longer matched the desired state from Git.
- ArgoCD self-healing restored the deployment back to 1 replica.
- This is the strongest demonstration of GitOps reconciliation in this lab.


### 4.2 Pod Deletion Test

Commands used:

```bash
kubectl get pods -n dev
kubectl delete pod -n dev devops-info-service-dev-devops-info-service-b6588bcfd-vgmc6
kubectl get pods -n dev -w
```

Output:

```bash
PS C:\Users\zagur\DevOps\DevOps-Core-Course> kubectl get pods -n dev
NAME                                                          READY   STATUS    RESTARTS   AGE
devops-info-service-dev-devops-info-service-b6588bcfd-vgmc6   2/2     Running   0          60m

PS C:\Users\zagur\DevOps\DevOps-Core-Course> kubectl delete pod -n dev devops-info-service-dev-devops-info-service-b6588bcfd-vgmc6
pod "devops-info-service-dev-devops-info-service-b6588bcfd-vgmc6" deleted from dev namespace

PS C:\Users\zagur\DevOps\DevOps-Core-Course> kubectl get pods -n dev -w
NAME                                                          READY   STATUS    RESTARTS   AGE
devops-info-service-dev-devops-info-service-b6588bcfd-p6x2v   1/2     Running   0          8s
devops-info-service-dev-devops-info-service-b6588bcfd-p6x2v   1/2     Running   0          16s
devops-info-service-dev-devops-info-service-b6588bcfd-p6x2v   2/2     Running   0          16s
```

Interpretation:
- The deleted pod was recreated automatically.
- This behavior was performed by Kubernetes through the Deployment and ReplicaSet controllers.
- This is **Kubernetes self-healing**, not ArgoCD self-healing.


### 4.3 Configuration Drift Test

A manual configuration drift test was attempted on the `dev` deployment.

Attempt 1: add a manual label to the Deployment:

```bash
kubectl label deployment devops-info-service-dev-devops-info-service -n dev drift-test=manual
argocd app diff devops-info-service-dev
kubectl get deployment devops-info-service-dev-devops-info-service -n dev --show-labels
```

Observed output:

```bash
PS C:\Users\zagur\DevOps\DevOps-Core-Course> kubectl label deployment devops-info-service-dev-devops-info-service -n dev drift-test=manual
deployment.apps/devops-info-service-dev-devops-info-service labeled

PS C:\Users\zagur\DevOps\DevOps-Core-Course> .\argocd app diff devops-info-service-dev

PS C:\Users\zagur\DevOps\DevOps-Core-Course> kubectl get deployment devops-info-service-dev-devops-info-service -n dev --show-labels
NAME                                          READY   UP-TO-DATE   AVAILABLE   AGE   LABELS
devops-info-service-dev-devops-info-service   1/1     1            1           67m   app.kubernetes.io/instance=devops-info-service-dev,app.kubernetes.io/managed-by=Helm,app.kubernetes.io/name=devops-info-service,app.kubernetes.io/version=1.0.0,drift-test=manual,helm.sh/chart=devops-info-service-0.1.0
```

Additional attempts were made by changing pod template annotations, environment variables, and a managed ConfigMap, but in this local setup those changes still did not appear in `argocd app diff` and were not automatically reverted.

Observed application state remained:

```bash
PS C:\Users\zagur\DevOps\DevOps-Core-Course> .\argocd app get devops-info-service-dev
Name:               argocd/devops-info-service-dev
Project:            default
Server:             https://kubernetes.default.svc
Namespace:          dev
URL:                https://argocd.example.com/applications/devops-info-service-dev
Source:
- Repo:             https://github.com/wkwtfigo/DevOps-Core-Course.git
  Target:           master
  Path:             k8s/devops-info-service
  Helm Values:      values-dev.yaml
Sync Policy:        Automated (Prune)
Sync Status:        Synced to master (742a8e9)
Health Status:      Healthy
```

Interpretation:
- A configuration drift experiment was performed as required.
- In this local environment, the tested manual mutations were not surfaced as visible drift by `argocd app diff`.
- Because of that, the scale test in section 4.1 is used as the primary proof of ArgoCD self-healing.
- The attempted drift test is still documented here as an observed result rather than a successful revert.

### 4.4 When ArgoCD Syncs vs When Kubernetes Heals

**Kubernetes self-healing**
- Recreates deleted pods to satisfy the Deployment replica count.
- Operates through native controllers such as Deployment and ReplicaSet.
- Does not compare live state with Git.

**ArgoCD self-healing**
- Reconciles the cluster back to the declarative Git-defined desired state.
- Applies to managed resources of an ArgoCD Application.
- Was demonstrated successfully through the manual scale drift test.

### 4.5 Sync Interval and Reconciliation in This Setup

From the `argocd-cm` configuration in this cluster:

```yaml
timeout.reconciliation: 120s
timeout.reconciliation.jitter: 60s
```

This means ArgoCD periodically reconciles applications on roughly a 2-minute interval with additional jitter. Manual refreshes and manual syncs can also be triggered from the CLI or the UI.

---
## 5. Screenshots

The following screenshots should be included in `k8s/screenshots/` and referenced in the report:

1. `argo_ui.png`
   - ArgoCD UI with all applications visible.
   - Shows `devops-info-service`, `devops-info-service-dev`, and `devops-info-service-prod`.

    ![](/k8s/screenshots/argo_ui.png)

2. `commit.png`
   - Git commit or repository change used for the GitOps workflow demonstration.

    ![](/k8s/screenshots/commit.png)

3. `app_details_dev.png` (recommended)
   - ArgoCD application details page for the `dev` application.
   - Should show sync policy and health information.

    ![](/k8s/screenshots/dev.png)

4. `app_details_prod.png` (recommended)
   - ArgoCD application details page for the `prod` application.
   - Useful to highlight the manual sync policy.

    ![](/k8s/screenshots/prod.png)

---

## 6. Conclusion

In this lab, ArgoCD was installed and configured as a GitOps controller for the existing Helm-based application. The application was deployed declaratively from Git, and separate `dev` and `prod` environments were created using different Application manifests and Helm values files.

The `dev` environment used automated synchronization with pruning and self-healing, while the `prod` environment remained on manual synchronization. This reflects a practical workflow in which development prioritizes speed and automatic reconciliation, while production prioritizes control and review.

The most reliable self-healing evidence in this setup was the manual scale test, where the deployment was changed from 1 replica to 5 replicas and then automatically restored to the Git-defined state. The pod deletion test demonstrated standard Kubernetes self-healing through Deployment and ReplicaSet controllers. Additional manual configuration drift experiments were documented, even though they did not surface as visible ArgoCD diffs in this local environment.

Overall, the lab demonstrated the core GitOps model:
- Git stores the desired state.
- ArgoCD continuously reconciles cluster resources against that desired state.
- Different environments can use different sync strategies while still sharing a single repository and Helm chart.
