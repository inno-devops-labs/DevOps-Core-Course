# Lab 13 — GitOps with ArgoCD

## Task 1 — ArgoCD Installation & Setup

### 1.1 Install ArgoCD via Helm

1. Add the ArgoCD Helm repository:
   ![Screenshot: Add Helm repo](/docs_lab13/screenshots/helm_repo_add_argo.png)

2. Create dedicated namespace and install ArgoCD:
   ![Screenshot: Create namespace](/docs_lab13/screenshots/kubectl_create_namespace_argocd.png)

3. Verify all pods are ready:
   All components should show `Running` status.

### 1.2 Access ArgoCD UI

1. Set up port forwarding to access the web interface:
   ![Screenshot: Port forwarding](/docs_lab13/screenshots/task2_port_forward_1.png)

2. Retrieve the initial admin password:
   ![Screenshot: Get password](/docs_lab13/screenshots/task2_get_pswrd.png)

3. Access ArgoCD at `https://localhost:8080` in your browser:
   ![Screenshot: UI login page](/docs_lab13/screenshots/task2_app_test_ui.png)

4. Log in with credentials:
   - Username: `admin`
   - Password: `pfZ3jJ3qkuw5l5qo`
   ![Screenshot: After login](/docs_lab13/screenshots/task2_after_login.png)

### 1.3 Install ArgoCD CLI

1. Download the CLI for your platform (Windows):
   ```PowerShell
   Invoke-WebRequest -Uri "https://github.com/argoproj/argo-cd/releases/latest/download/argocd-windows-amd64.exe" -OutFile "argocd.exe"
   ```

2. Log in via CLI:
   ![0](/docs_lab13/screenshots/login_via_cl.png)

3. Verify CLI connection:
   ![1](/docs_lab13/screenshots/agrocd_version.png)
   ![2](/docs_lab13/screenshots/agrocd_user.png)


## Task 2 — Application Deployment

### 2.1 ArgoCD Application Manifests

All application manifests are stored in `k8s/argocd/`:

- **`application.yaml`** - Basic application in default namespace (for testing)
- **`application-dev.yaml`** - Dev environment with auto-sync enabled
- **`application-prod.yaml`** - Prod environment with manual sync only
- **`applicationset.yaml`** - ApplicationSet for automated generation of dev/prod apps (bonus)

### 2.2 Application Manifest Example

```yaml
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: python-app
  namespace: argocd
spec:
  project: default
  source:
    repoURL: https://github.com/Daniil20xx/DevOps-Core-Course.git
    targetRevision: lab12
    path: k8s/mychart
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

### 2.3 Deploy the Application

Apply the application manifest:
![1](/docs_lab13/screenshots/task2_k8s_apply.png)

Monitor the deployment:
![2](/docs_lab13/screenshots/task2_lifecheck.png)

### 2.5 Perform Initial Sync

Trigger manual sync via CLI:
![sync_after_change_2](/docs_lab13/screenshots/to_1-sync_after_change_2.png)

Verify resources are created:
![task2_heakth_check](/docs_lab13/screenshots/task2_heakth_check.png)

Verify that 1 replica:
![after_change_2_to_1](/docs_lab13/screenshots/after_change_2_to_1.png)


## Task 3 — Multi-environment deployment (dev/prod)

### 3.1 Create namespaces

![apply_namespace](/docs_lab13/screenshots/apply_namespace.png)

### 3.2 Create ArgoCD Applications for dev/prod

```bash
kubectl apply -f k8s/argocd/applicationset.yaml
```

App list:
![app_list](/docs_lab13/screenshots/app_list.png)

Sync prod:
```bash
argocd app sync devops-info-service-prod
```

![task3_verify_deplay](/docs_lab13/screenshots/task3_verify_deplay.png)
![task3_verify_prod](/docs_lab13/screenshots/task3_verify_prod.png)

*If apps show `OutOfSync` + `Missing`, it only means resources are not created yet.*

### 3.3 Dev vs Prod differences
### 3.4 Why prod stays manual

## Task 4 — Self-healing & drift tests (dev)

### 4.1 Self-healing test: manual scale

![task4_scale_deployment](/docs_lab13/screenshots/task4_scale_deployment.png)
![task4_diff](/docs_lab13/screenshots/task4_diff.png)

- Manually scaled deployment to new count of replicas.
- ArgoCD detected configuration drift

### 4.2 Pod deletion test (Kubernetes behavior)
![task4_diff](/docs_lab13/screenshots/task4_diff.png)
![task4_pod_deletion](/docs_lab13/screenshots/task4_pod_deletion.png)

- I manually deleted the pod using `kubectl delete pod`
- Kubernetes automatically recreated the pod via the ReplicaSet
- This is Kubernetes built-in self-healing capability, not ArgoCD


### 4.3 Configuration drift test (ArgoCD behavior)

```bash
kubectl annotate deploy -n dev python-app-dev-mychart drift-ts="$(date +%s)" --overwrite
# deployment.apps/python-app-dev-mychart annotated

# Observation: in this cluster/ArgoCD setup, changing top-level Deployment metadata annotations
# did not immediately flip the app to OutOfSync (depends on tracking method), and behavior may vary:

kubectl get deploy -n dev python-app-dev-mychart \
  -o jsonpath='{.metadata.annotations.drift-ts}{"\n"}'
# 1777066438

argocd app get python-app-dev --refresh | grep -E "Sync Status|Health Status" || true
# Sync Status: Synced ...
# Health Status: Healthy

sleep 8

kubectl get deploy -n dev python-app-dev-mychart \
  -o jsonpath='{.metadata.annotations.drift-ts}{"\n"}' || true
# 1777066438


# Reliable drift for evidence (replicas change):
kubectl patch deployment python-app-dev-mychart -n dev \
  --type merge -p '{"spec":{"replicas":5}}'

# Immediately after patch (before self-heal):
kubectl get deploy -n dev python-app-dev-mychart \
  -o jsonpath='{.spec.replicas}{"\n"}'
# 5

# ArgoCD detects drift and (with self-heal enabled OR during next reconciliation loop) reverts it:
argocd app diff python-app-dev || true

sleep 10

argocd app get python-app-dev --refresh | grep -E "Sync Status|Health Status" || true
# Sync Status: Synced ...
# Health Status: Healthy

kubectl get deploy -n dev python-app-dev-mychart \
  -o jsonpath='{.spec.replicas}{"\n"}'
# 1
```

### 4.4 When does ArgoCD sync and how often it checks Git?
