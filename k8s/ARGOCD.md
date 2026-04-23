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
```bash
.\argocd.exe app sync python-app --insecure
```

Expected status progression:
- `OutOfSync` → `Syncing` → `Synced`
- Health: `Progressing` → `Healthy`

Verify resources are created:
```bash
kubectl get deployments
kubectl get services
kubectl get configmaps
```

### 2.6 Test GitOps Workflow

GitOps principle: **Git is the single source of truth**

Test the workflow:

1. **Make a change in the Helm chart**:
   ```bash
   # Edit values.yaml - change replica count
   sed -i 's/replicaCount: 1/replicaCount: 2/' k8s/mychart/values.yaml
   ```

2. **Commit and push to repository**:
   ```bash
   git add k8s/mychart/values.yaml
   git commit -m "Increase replica count to 2"
   git push origin lab12
   ```

3. **Observe ArgoCD detecting drift**:
   - ArgoCD polls Git every ~3 minutes by default
   - Status changes to `OutOfSync`
   - Application shows the difference in `argocd app diff python-app`

4. **Trigger sync** (automatic for dev, manual for prod):
   ```bash
   .\argocd.exe app sync python-app --insecure
   ```

5. **Verify changes are applied**:
   ```bash
   kubectl get replicas deployment python-app
   ```

This demonstrates the GitOps principle: cluster state follows Git repository state.


## Task 3 — Multi-Environment Deployment

### 3.1 Create Namespaces

Create separate namespaces for each environment declaratively:

```bash
kubectl apply -f k8s/argocd/namespaces.yaml
```

**File content** (`k8s/argocd/namespaces.yaml`):
```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: dev
---
apiVersion: v1
kind: Namespace
metadata:
  name: prod
```

Verify namespaces are created:
```bash
kubectl get namespaces
```

### 3.2 Environment-Specific Applications

#### 3.2.1 Dev Application with Auto-Sync

**File**: `k8s/argocd/application-dev.yaml`

Configuration details:
- **Namespace**: `dev`
- **Values file**: `values-dev.yaml`
- **Sync policy**: `Automated` with `prune: true` and `selfHeal: true`
- **Replica count**: 1 (from values-dev.yaml)
- **Resource limits**: Low (dev/testing)

Deploy:
```bash
kubectl apply -f k8s/argocd/application-dev.yaml
```

Monitor:
```bash
.\argocd.exe app get python-app-dev
kubectl get pods -n dev
```

#### 3.2.2 Prod Application with Manual Sync

**File**: `k8s/argocd/application-prod.yaml`

Configuration details:
- **Namespace**: `prod`
- **Values file**: `values-prod.yaml`
- **Sync policy**: Manual only (no automatic sync)
- **Replica count**: 3 (from values-prod.yaml)
- **Resource limits**: Higher (production)

Deploy:
```bash
kubectl apply -f k8s/argocd/application-prod.yaml
```

Monitor:
```bash
.\argocd.exe app get python-app-prod
kubectl get pods -n prod
```

### 3.3 Sync Policy Differences

| Aspect | Dev | Prod |
|--------|-----|------|
| **Sync Type** | Automatic | Manual |
| **Prune** | Enabled | N/A |
| **Self-Heal** | Enabled | N/A |
| **Git Polling** | Auto-sync on Git changes | Manual trigger required |
| **Rollback** | Automatic | Explicit sync required |
| **Use Case** | Rapid iteration, testing | Controlled releases, compliance |

### 3.4 Why This Pattern?

**Dev Environment (Auto-Sync + Self-Heal)**:
- Enables rapid testing and feedback
- Automatic drift correction maintains consistency
- Prune removes unmanaged resources
- Low risk (non-critical environment)

**Prod Environment (Manual Sync)**:
- Requires human review before deployment
- Provides change control and audit trail
- Allows staged rollout planning
- Enables careful rollback strategy
- Critical for compliance and SLAs

### 3.5 Verification

Check both environments are deployed correctly:

```bash
# List all applications
.\argocd.exe app list

# Check dev application
.\argocd.exe app get python-app-dev

# Check prod application  
.\argocd.exe app get python-app-prod

# Verify namespaces and pods
kubectl get pods -n dev
kubectl get pods -n prod

# Check resource configurations
kubectl get deployment -n dev python-app-dev-mychart -o yaml | grep -A 5 "replicas:"
kubectl get deployment -n prod python-app-prod-mychart -o yaml | grep -A 5 "replicas:"
```

Expected results:
- Dev: `Synced` status, auto-sync enabled, 1 replica
- Prod: `OutOfSync` (before manual sync), manual sync only, 3 replicas (or configured value)


## Task 4 — Self-Healing & Sync Policies

### 4.1 Understanding Self-Healing vs Kubernetes Self-Healing

**Kubernetes Self-Healing** (ReplicaSet/Deployment Controller):
- Automatically recreates deleted pods
- Maintains desired replica count
- Scope: Pod-level recovery

**ArgoCD Self-Healing** (with `selfHeal: true`):
- Detects configuration drift from Git
- Reverts manual changes to match Git state
- Scope: Application-level state consistency

### 4.2 Manual Scale Test (Drift Detection)

This test demonstrates ArgoCD self-healing by introducing intentional drift.

#### Step 1: Baseline
Check current replica count:
```bash
kubectl get deployment python-app-dev-mychart -n dev
# Expected: 1 replica (from values-dev.yaml)
```
![Screenshot: Initial state](/docs_lab13/screenshots/04_initial_replicas.png)

#### Step 2: Introduce Drift
Manually scale the deployment:
```bash
kubectl scale deployment python-app-dev-mychart -n dev --replicas=5
kubectl get pods -n dev
# Now shows 5 pods instead of 1
```
![Screenshot: Scaled to 5 replicas](/docs_lab13/screenshots/04_scaled_5_replicas.png)

#### Step 3: Check ArgoCD Detection
ArgoCD detects the drift:
```bash
.\argocd.exe app get python-app-dev
# Status should show: OutOfSync
# Health: Progressing or Degraded
```
![Screenshot: ArgoCD detected OutOfSync](/docs_lab13/screenshots/04_argocd_out_of_sync.png)

#### Step 4: Self-Healing (Auto-Revert)
With `selfHeal: true`, ArgoCD automatically reverts the drift:
```bash
# Wait 3-5 minutes for auto-sync trigger
# Or manually trigger:
.\argocd.exe app sync python-app-dev --insecure

# Check result
kubectl get pods -n dev
# Expected: Back to 1 replica
```
![Screenshot: Self-healed back to 1 replica](/docs_lab13/screenshots/04_self_healed.png)

**Evidence of Self-Healing**:
| Timestamp | Action | Replicas | ArgoCD Status |
|-----------|--------|----------|---------------|
| T0 | Baseline | 1 | Synced |
| T1 | Manual scale | 5 | OutOfSync |
| T2 | Self-heal triggered | 1 | Synced |

### 4.3 Pod Deletion Test

This test demonstrates Kubernetes self-healing (replica management).

#### Step 1: Delete a Pod
```bash
kubectl get pods -n dev
# Get one pod name, then delete it

kubectl delete pod python-app-dev-mychart-XXXXX -n dev
```
![Screenshot: Pod deleted](/docs_lab13/screenshots/04_pod_deleted.png)

#### Step 2: Observe Kubernetes Recreation
```bash
kubectl get pods -n dev -w
# Watch as new pod is created automatically within seconds
```
![Screenshot: Pod recreated](/docs_lab13/screenshots/04_pod_recreated.png)

**Observation**: Kubernetes immediately recreates the pod because the Deployment's ReplicaSet controller ensures the desired pod count is maintained.

### 4.4 Configuration Drift Test

This test demonstrates ArgoCD's drift detection for configuration changes.

#### Step 1: Introduce Configuration Drift
Manually add a label to the deployment:
```bash
kubectl label deployment python-app-dev-mychart -n dev drift-test=true --overwrite
```
![Screenshot: Label added](/docs_lab13/screenshots/04_label_added.png)

#### Step 2: View Drift in ArgoCD
```bash
.\argocd.exe app diff python-app-dev
# Shows the added label as a difference
```
![Screenshot: ArgoCD diff view](/docs_lab13/screenshots/04_argocd_diff.png)

#### Step 3: Self-Heal Removes the Change
ArgoCD self-healing reverts the unwanted label:
```bash
# Auto-revert if selfHeal=true, or:
.\argocd.exe app sync python-app-dev --insecure

# Verify label is removed
kubectl get deployment python-app-dev-mychart -n dev -o yaml | grep drift-test
# Should return nothing
```
![Screenshot: Label removed by self-heal](/docs_lab13/screenshots/04_label_removed.png)

### 4.5 Sync Interval & Triggers

**Default Behavior**:
- **Polling interval**: ~3 minutes (ArgoCD checks Git)
- **Auto-sync trigger**: Git commit detected
- **Webhook trigger**: Faster detection (can be configured)

**Sync Status Indicators**:
- `Synced` — Cluster matches Git
- `OutOfSync` — Git has unreplicated changes
- `Unknown` — Unable to determine state (repo issues)

**Health Status Indicators**:
- `Healthy` — All resources running correctly
- `Progressing` — Deployment in progress
- `Degraded` — Resources failing or unhealthy
- `Unknown` — Unable to determine health

### 4.6 Key Insights

| Aspect | Kubernetes Self-Heal | ArgoCD Self-Heal |
|--------|---------------------|------------------|
| **What** | Pod recovery | State consistency |
| **Trigger** | Pod deletion | Drift detection |
| **Scope** | Pod/Replica level | Application level |
| **Revert** | Create new pod | Revert to Git state |
| **Enabled** | Always (ReplicaSet) | Only if `selfHeal: true` |

For **production**, this pattern ensures:
- ✅ Automatic recovery from failures
- ✅ Consistency with source control
- ✅ Repeatable, auditable deployments
- ✅ Easy rollback (revert Git, re-sync)


## Bonus Task — ApplicationSet

### 5.1 What is ApplicationSet?

**ApplicationSet** is a Kubernetes CRD that generates multiple ArgoCD Application resources from a single template using generators.

**Benefits**:
- ✅ Eliminates manifest duplication
- ✅ Centralizes environment configuration
- ✅ Scales easily to many environments
- ✅ Supports multiple generation patterns
- ✅ Single source of truth for all applications

**Use Cases**:
- Multi-environment deployments (dev/staging/prod)
- Multi-cluster deployments (west/east regions)
- Multi-tenant SaaS applications
- Monorepo with multiple microservices

### 5.2 Available Generators

| Generator | Use Case | Example |
|-----------|----------|---------|
| **List** | Explicit environment list | dev, staging, prod |
| **Cluster** | Multi-cluster deployments | AWS, GCP, Azure clusters |
| **Git** | Auto-discover apps in repo | Scan directories for Kustomize/Helm |
| **SCM** | GitHub organization scanning | Auto-sync GitHub repos |
| **Matrix** | Combine generators | Multi-region + multi-environment |
| **Merge** | Combine multiple generator outputs | Complex scenarios |

### 5.3 Implementation with List Generator

**File**: `k8s/argocd/applicationset.yaml`

```yaml
apiVersion: argoproj.io/v1alpha1
kind: ApplicationSet
metadata:
  name: python-app-set
  namespace: argocd
spec:
  generators:
    - list:
        elements:
          - env: dev
            namespace: dev
            valuesFile: values-dev.yaml
            autoSync: "true"
            replicas: "1"
          - env: prod
            namespace: prod
            valuesFile: values-prod.yaml
            autoSync: "false"
            replicas: "3"
  template:
    metadata:
      name: 'python-app-{{env}}'
      labels:
        app: python-app
        env: '{{env}}'
    spec:
      project: default
      source:
        repoURL: https://github.com/Daniil20xx/DevOps-Core-Course.git
        targetRevision: lab12
        path: k8s/mychart
        helm:
          valueFiles:
            - '{{valuesFile}}'
      destination:
        server: https://kubernetes.default.svc
        namespace: '{{namespace}}'
      syncPolicy:
        syncOptions:
          - CreateNamespace=true
        automated: '{{autoSync}}'
        prune: true
        selfHeal: true
```

### 5.4 Deploy ApplicationSet

Deploy the ApplicationSet:
```bash
kubectl apply -f k8s/argocd/applicationset.yaml
```

**What happens**:
1. ApplicationSet controller reads the spec
2. List generator produces 2 elements (dev, prod)
3. Template is rendered for each element
4. Two Application resources are generated:
   - `python-app-dev` (in dev namespace, auto-sync)
   - `python-app-prod` (in prod namespace, manual sync)

### 5.5 Verify Generated Applications

View generated applications:
```bash
kubectl get applications -n argocd
# Should show:
# NAME                SYNC STATUS  HEALTH STATUS
# python-app-dev      Synced       Healthy
# python-app-prod     OutOfSync    Missing
```

View ApplicationSet status:
```bash
.\argocd.exe app list | grep python-app
# Shows both generated applications
```

View ApplicationSet details:
```bash
kubectl get applicationset -n argocd python-app-set -o yaml
```

### 5.6 Advantages Over Individual Applications

**With Individual Applications**:
```
application-dev.yaml   (~50 lines of YAML)
application-prod.yaml  (~50 lines of YAML)
---
Total: ~100 lines, significant duplication
```

**With ApplicationSet**:
```
applicationset.yaml    (~60 lines of YAML)
---
Total: ~60 lines, single source of truth
```

**Scaling to 5 environments**:
- Individual: ~250 lines of repetitive YAML
- ApplicationSet: ~80 lines (add environment to list)

### 5.7 Key Features

**Template Variables** (`{{ }}` syntax):
- `{{env}}` — Environment name
- `{{namespace}}` — Target namespace
- `{{valuesFile}}` — Helm values file
- `{{autoSync}}` — Auto-sync setting
- Any custom parameter in generator elements

**Conditional Settings**:
- Sync policy can vary per environment
- Resource limits per environment
- Helm values per environment
- Destination namespace per environment

### 5.8 Scaling Patterns

**Example: Adding Staging**:
```yaml
- env: staging
  namespace: staging
  valuesFile: values-staging.yaml
  autoSync: "false"
  replicas: "2"
```
Just add one more element, no new files needed!

**Example: Adding Region** (with Matrix generator):
```yaml
generators:
  - matrix:
      generators:
        - list:
            elements:
              - env: dev
              - env: prod
        - list:
            elements:
              - region: us-east
              - region: eu-west
```
Automatically generates 4 applications (dev-us-east, dev-eu-west, prod-us-east, prod-eu-west)

### 5.9 Best Practices

✅ **Do**:
- Use ApplicationSet for 3+ environments
- Keep template parameterized for flexibility
- Use list generators for simple cases
- Document parameter meanings

❌ **Don't**:
- Override values in ApplicationSet (use values files)
- Duplicate templates across ApplicationSets
- Use for single-app deployments (use Application directly)
- Hardcode cluster-specific settings


## Deployment & Verification

### 6.1 Quick Start Commands

Deploy all resources in order:

```bash
# Create namespaces
kubectl apply -f k8s/argocd/namespaces.yaml

# Deploy basic application (testing)
kubectl apply -f k8s/argocd/application.yaml

# Deploy environment-specific applications
kubectl apply -f k8s/argocd/application-dev.yaml
kubectl apply -f k8s/argocd/application-prod.yaml

# Alternative: Deploy ApplicationSet instead (generates both)
# kubectl apply -f k8s/argocd/applicationset.yaml
```

### 6.2 Verification Checklist

```bash
# Check ArgoCD pods
kubectl get pods -n argocd

# Check all applications
.\argocd.exe app list

# Check individual application status
.\argocd.exe app get python-app-dev
.\argocd.exe app get python-app-prod

# Check deployed resources in dev
kubectl get all -n dev
kubectl get pods -n dev -w

# Check deployed resources in prod
kubectl get all -n prod
kubectl get pods -n prod -w

# Check sync status
.\argocd.exe app status python-app-dev
.\argocd.exe app status python-app-prod
```

### 6.3 Port Forwarding for UI Access

Keep this running in a separate terminal:
```bash
kubectl port-forward svc/argocd-server -n argocd 8080:443
```

Then access at: `https://localhost:8080`

### 6.4 Testing GitOps Workflow

1. **Make a Git change**:
   ```bash
   # Modify values-dev.yaml
   sed -i 's/replicaCount: 1/replicaCount: 2/' k8s/mychart/values-dev.yaml
   
   # Commit and push
   git add k8s/mychart/values-dev.yaml
   git commit -m "Test: Increase dev replicas"
   git push origin lab12
   ```

2. **Observe ArgoCD detecting drift**:
   ```bash
   # After ~3 minutes or immediate if webhook configured
   .\argocd.exe app get python-app-dev
   # Status should be: OutOfSync
   ```

3. **ArgoCD auto-syncs** (dev) **or manual sync** (prod):
   ```bash
   # For dev - should auto-sync
   # For prod - manual sync required
   .\argocd.exe app sync python-app-prod --insecure
   ```

4. **Verify changes applied**:
   ```bash
   kubectl get deployment python-app-dev-mychart -n dev -o yaml | grep replicas:
   kubectl get pods -n dev
   ```

### 6.5 Troubleshooting

**Issue**: `ComparisonError: Failed to load target state` / `connection refused`
- **Root Cause**: repo-server pod is not responding to requests
- **Solution**:
  ```bash
  # Check repo-server status
  kubectl get pods -n argocd | grep repo-server
  
  # If CrashLoopBackOff or not Running, restart it
  kubectl delete pod -l app.kubernetes.io/name=argocd-repo-server -n argocd
  
  # Wait for new pod to start (check logs)
  kubectl logs -f deployment/argocd-repo-server -n argocd
  
  # Retry the operation
  .\argocd.exe app get python-app-dev
  ```

**Issue**: Application shows `ComparisonError` with specific Git errors
- **Root Cause**: Invalid repository URL, branch, or authentication
- **Solution**: 
  ```bash
  # Verify repository configuration
  git remote -v
  git branch -a
  
  # Check repo-server can access Git
  kubectl exec -it deployment/argocd-repo-server -n argocd -- \
    git ls-remote https://github.com/Daniil20xx/DevOps-Core-Course.git
  ```

**Issue**: Pods in `ImagePullBackOff`
- **Root Cause**: Container image doesn't exist or registry not accessible
- **Solution**:
  ```bash
  # Check pull errors
  kubectl describe pod POD_NAME -n dev
  
  # Option 1: Use existing image (e.g., nginx)
  kubectl set image deployment/python-app-dev-mychart \
    mychart=nginx:latest -n dev
  
  # Option 2: Build and push custom image
  docker build -t myapp:v1.0 .
  docker push myapp:v1.0
  
  # Update values-dev.yaml with new image
  # Push to Git, ArgoCD will auto-sync
  ```

**Issue**: Application syncs but pods stay in `Pending`
- **Root Cause**: Insufficient cluster resources or PVC issues
- **Solution**:
  ```bash
  # Check pod events
  kubectl describe pod POD_NAME -n dev
  
  # Check available resources
  kubectl top nodes
  kubectl describe nodes
  
  # Check PVC status
  kubectl get pvc -n dev
  kubectl describe pvc -n dev
  ```

**Issue**: Manual sync keeps failing with "another operation in progress"
- **Root Cause**: Previous sync operation hasn't finished
- **Solution**:
  ```bash
  # Wait 2-3 minutes for previous operation to complete
  # Or view operation status
  .\argocd.exe app get python-app-dev
  
  # Check if ArgoCD server is responsive
  .\argocd.exe account get-user-info
  ```

---

## Lab Report Requirements

### 7.1 What to Document

Your report must include evidence for each task:

#### Task 1 — ArgoCD Installation (2 pts)
- [ ] Screenshot: `kubectl get pods -n argocd` showing all Running
- [ ] Screenshot: ArgoCD UI login page
- [ ] Screenshot: ArgoCD dashboard after login
- [ ] Evidence: CLI login with `.\argocd.exe version` output

#### Task 2 — Application Deployment (3 pts)
- [ ] Manifest files present: `application.yaml`, `application-dev.yaml`, `application-prod.yaml`
- [ ] Screenshot: `argocd app list` showing all applications
- [ ] Screenshot: `argocd app get python-app` with Synced status
- [ ] Evidence: Application resources created (pods, services, configmaps)
- [ ] Test: GitOps workflow with Git commit → ArgoCD sync

#### Task 3 — Multi-Environment Deployment (3 pts)
- [ ] Screenshot: Both namespaces exist (`dev` and `prod`)
- [ ] Screenshot: `argocd app list` showing dev and prod applications
- [ ] Evidence: Dev app has auto-sync enabled
- [ ] Evidence: Prod app has manual sync only
- [ ] Screenshot: Different configurations (compare `kubectl get deployment -o yaml`)

#### Task 4 — Self-Healing & Sync (2 pts)
- [ ] **Manual Scale Test**:
  - Before: `kubectl get pods -n dev` (1 pod)
  - Action: `kubectl scale ... --replicas=5`
  - After: ArgoCD reverted to 1 (with timestamp)
  - Screenshot: Evidence of reversion

- [ ] **Pod Deletion Test**:
  - Delete pod: `kubectl delete pod ...`
  - Screenshot: Kubernetes recreated it (new pod age)
  - Timestamp: How long recovery took

- [ ] **Configuration Drift Test**:
  - Manual change: `kubectl label ...`
  - Screenshot: `argocd app diff` showing difference
  - Result: Self-heal removed the change

#### Bonus — ApplicationSet (2.5 pts)
- [ ] `applicationset.yaml` file present
- [ ] Screenshot: Generated applications visible (`argocd app list`)
- [ ] Documentation: How many apps generated
- [ ] Explanation: Benefits vs. individual Applications

### 7.2 Screenshot Template for Report

Create a directory `docs_lab13/screenshots/` and include:

```
# Task 1
01_argocd_pods_running.png          # kubectl get pods -n argocd
02_argocd_ui_login.png              # ArgoCD login page
03_argocd_dashboard.png             # After login
04_cli_version.png                  # argocd version output

# Task 2
05_application_created.png          # argocd app get python-app
06_app_synced.png                   # Sync Status: Synced
07_resources_created.png            # kubectl get all -n default
08_gitops_workflow.png              # Git commit → ArgoCD sync

# Task 3
09_namespaces.png                   # kubectl get namespaces
10_dev_vs_prod_apps.png             # argocd app list (both)
11_dev_autosync_config.png          # App config: auto-sync enabled
12_prod_manual_config.png           # App config: manual sync

# Task 4
13_baseline_replicas.png            # Initial state: 1 replica
14_scaled_to_5.png                  # After manual scale
15_self_healed.png                  # After self-heal: back to 1
16_pod_deleted.png                  # Pod deletion moment
17_pod_recreated.png                # Kubernetes recreation
18_configuration_drift.png          # kubectl label + argocd diff
19_drift_removed.png                # After self-heal

# Bonus
20_applicationset_apps.png          # Generated applications
21_applicationset_yaml.png          # ApplicationSet definition
```

### 7.3 Report Content Structure

```markdown
# Lab 13 Report — GitOps with ArgoCD

## Summary
- ArgoCD installed: ✓
- Applications deployed: dev ✓, prod ✓
- Auto-sync working: ✓
- Self-healing verified: ✓

## Task 1 — Setup
[Screenshots + command outputs]

## Task 2 — Deployment
[GitOps workflow demonstration]

## Task 3 — Environments
[Dev vs Prod configuration comparison]

## Task 4 — Self-Healing
[Before/After for each test]
- Manual scale: Reverted in [X] seconds
- Pod deletion: Recreated in [X] seconds
- Configuration drift: Removed in [X] seconds

## Bonus — ApplicationSet
[Generated apps screenshot + explanation]

## Lessons Learned
- ArgoCD ensures cluster consistency with Git
- Self-healing automates drift correction
- Multi-env patterns enable controlled releases
```

### 7.4 Reporting Script (Optional)

Capture evidence automatically:
```bash
#!/bin/bash
mkdir -p docs_lab13/screenshots

# Task 1
kubectl get pods -n argocd > docs_lab13/screenshots/01_pods.txt

# Task 2
argocd app list > docs_lab13/screenshots/02_app_list.txt
argocd app get python-app > docs_lab13/screenshots/02_app_status.txt

# Task 3
argocd app get python-app-dev > docs_lab13/screenshots/03_dev_status.txt
argocd app get python-app-prod > docs_lab13/screenshots/03_prod_status.txt

# Task 4
kubectl get pods -n dev > docs_lab13/screenshots/04_dev_pods.txt
kubectl get pods -n prod > docs_lab13/screenshots/04_prod_pods.txt
```

---
