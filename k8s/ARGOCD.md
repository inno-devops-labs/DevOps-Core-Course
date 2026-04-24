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