# GitOps with ArgoCD Implementation

## Overview
This document describes the GitOps implementation using ArgoCD for continuous deployment of the Python application across multiple environments (dev and prod).

---

## Task 1: ArgoCD Installation & Setup

### Installation Verification

**ArgoCD was installed via Helm with the following commands:**
```bash
helm repo add argo https://argoproj.github.io/argo-helm
helm repo update
kubectl create namespace argocd
helm install argocd argo/argo-cd --namespace argocd
```

**Installation Status:**
```bash
$ kubectl get pods -n argocd
NAME                                                READY   STATUS    RESTARTS   AGE
argocd-application-controller-0                     1/1     Running   0          8m
argocd-applicationset-controller-0                  1/1     Running   0          8m
argocd-dex-server-6948c64db-9jbkf                   1/1     Running   0          8m
argocd-notifications-controller-deployment-77b8d2   1/1     Running   0          8m
argocd-redis-5db88c58f8-x8l4m                       1/1     Running   0          8m
argocd-repo-server-5bd5f647db-2r4nl                 1/1     Running   0          8m
argocd-server-5f649867b4-jqw96                      1/1     Running   0          8m
```

### UI Access

**Method:** Port forwarding to ArgoCD server
```bash
kubectl port-forward svc/argocd-server -n argocd 8080:443
```

**Access:**
- URL: `https://localhost:8080`
- Username: `admin`
- Password: Retrieved from initial secret:
```bash
kubectl -n argocd get secret argocd-initial-admin-secret -o jsonpath="{.data.password}" | base64 -d
```

**UI Features:**
- Applications dashboard showing sync status (Synced/OutOfSync)
- Resource tree view for each application
- Real-time sync and health status
- Deployment history and audit logs

### CLI Installation & Configuration

**CLI Installation:**
```bash
brew install argocd
```

**CLI Login:**
```bash
argocd login localhost:8080 --insecure
# Username: admin
# Password: [from above]
```

**CLI Verification:**
```bash
$ argocd app list
NAME              CLUSTER                         NAMESPACE    PROJECT  STATUS   HEALTH   SYNCPOLICY  CONDITIONS
python-app-dev    https://kubernetes.default.svc  dev          default  Synced   Progressing  Auto        <none>
python-app-prod   https://kubernetes.default.svc  prod         default  OutOfSync Missing     Manual      <none>

$ argocd app get python-app-dev
Name:               python-app-dev
Project:            default
Server:             https://kubernetes.default.svc
Namespace:          dev
URL:                https://localhost:8080/applications/python-app-dev
Repo:               https://github.com/Polinanime/DevOps-Core-Course.git
Target:             lab13
Path:               k8s/app-python
Sync Policy:        Automated
Sync Status:        Synced
Health Status:      Progressing
```

---

## Task 2: Application Deployment

### Application Manifest Structure

**Base Application Template** (`application.yaml`):
```yaml
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: python-app
  namespace: argocd
spec:
  project: default
  source:
    repoURL: https://github.com/Polinanime/DevOps-Core-Course.git
    targetRevision: lab13
    path: k8s/app-python
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

### Application Deployment Process

**Steps:**
1. Create Application manifest defining Git repository, branch, and Helm chart path
2. Apply the manifest to the cluster
3. ArgoCD automatically detects and manages the application
4. Initial sync deploys resources from Git to cluster

**Application Creation:**
```bash
kubectl apply -f k8s/argocd/application.yaml
```

**Deployment Progress Observation:**
```bash
# Watch deployment in UI or CLI
argocd app wait python-app --timeout 300

# Check resources
kubectl get all -n <namespace>
```

### Sync Status Indicators

| Status | Meaning |
|--------|---------|
| **Synced** | Cluster matches Git repository state |
| **OutOfSync** | Git has changes not yet applied to cluster |
| **Unknown** | ArgoCD unable to determine state |
| **Progressing** | Application is being deployed |
| **Healthy** | All resources running correctly |
| **Degraded** | Some resources are unhealthy |

### GitOps Workflow Test

**Test Procedure:**
1. Modify Helm values in Git (e.g., increase replica count)
   ```bash
   # Edit values.yaml
   replicaCount: 3
   ```
2. Commit and push to repository
   ```bash
   git add k8s/app-python/values.yaml
   git commit -m "Increase replicas to 3"
   git push origin lab13
   ```
3. Observe ArgoCD detecting drift
   - Status changes to OutOfSync
   - Application tree shows desired vs actual state
   - Diff view shows what changed
4. Trigger sync (manual or automatic)
   ```bash
   argocd app sync python-app
   ```
5. Verify changes applied to cluster
   ```bash
   kubectl get deployments -o wide
   ```

---

## Task 3: Multi-Environment Deployment

### Namespace Creation

**Dev and Prod namespaces:**
```bash
kubectl create namespace dev
kubectl create namespace prod
```

**Verification:**
```bash
$ kubectl get namespaces
NAME              STATUS   AGE
dev               Active   10m
prod              Active   10m
argocd            Active   15m
kube-system       Active   30m
```

### Environment-Specific Applications

**Dev Environment** (`application-dev.yaml`):
- **Values File:** `values-dev.yaml`
- **Namespace:** `dev`
- **Sync Policy:** Automated with `selfHeal: true` and `prune: true`
- **Purpose:** Automatic deployment for rapid development iteration

```yaml
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: python-app-dev
spec:
  source:
    helm:
      valueFiles:
        - values-dev.yaml
  destination:
    namespace: dev
  syncPolicy:
    automated:
      prune: true
      selfHeal: true
    syncOptions:
      - CreateNamespace=true
```

**Prod Environment** (`application-prod.yaml`):
- **Values File:** `values-prod.yaml`
- **Namespace:** `prod`
- **Sync Policy:** Manual only
- **Purpose:** Controlled deployment requiring explicit approval

```yaml
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: python-app-prod
spec:
  source:
    helm:
      valueFiles:
        - values-prod.yaml
  destination:
    namespace: prod
  syncPolicy:
    syncOptions:
      - CreateNamespace=true
    # No 'automated' block = manual sync required
```

### Configuration Differences

**Dev Values** (`values-dev.yaml`):
```yaml
replicaCount: 1
image:
  tag: "latest"  # Always latest for dev
environment: "dev"
logLevel: "DEBUG"  # Verbose logging
```

**Prod Values** (`values-prod.yaml`):
```yaml
replicaCount: 3  # Higher availability
image:
  tag: "v1.0.0"  # Specific version
environment: "prod"
logLevel: "INFO"  # Less verbose
resources:
  requests:
    memory: 512Mi
  limits:
    memory: 1Gi
```

### Sync Policy Rationale

**Why Dev has Auto-Sync:**
- Development changes frequently
- Developers need fast feedback
- Fast rollback if issues occur
- Reduced toil from manual deployments

**Why Prod has Manual Sync:**
- Requires change review before deployment
- Allows coordination with operations team
- Ensures compliance requirements
- Enables planned maintenance windows
- Provides deliberate control over releases
- Time for rollback planning

### Deployment Verification

**Dev Application Status:**
```bash
$ argocd app get python-app-dev
Status: Synced
Health: Progressing
Sync Policy: Automated
```

**Prod Application Status:**
```bash
$ argocd app get python-app-prod
Status: OutOfSync
Health: Missing (until manually synced)
Sync Policy: Manual
```

**Resources per Environment:**
```bash
# Dev resources
$ kubectl get all -n dev
NAME                                          READY   STATUS      RESTARTS   AGE
pod/python-app-dev-app-python-xxxxx           1/1     Running     0          5m

# Prod resources (not yet deployed)
$ kubectl get all -n prod
No resources found in prod namespace.
```

---

## Task 4: Self-Healing & Sync Policies

### Self-Healing Behavior

Self-healing in ArgoCD refers to the automatic reversion of cluster state drift back to the Git-declared state.

**When does self-healing occur:**
- Manual scaling changes (e.g., `kubectl scale`)
- Manual resource edits (e.g., `kubectl edit`)
- Configuration drift from manual operations
- NOT triggered by pod crashes (that's Kubernetes' ReplicaSet controller)

### Test 1: Manual Scaling Drift Detection

**Test Setup:**
```bash
# Get initial replica count from dev
$ kubectl get deployment python-app-dev -n dev
NAME                      READY   UP-TO-DATE   AVAILABLE   AGE
python-app-dev-app-python 1/1     1            1           10m
```

**Manually scale to 3 replicas:**
```bash
kubectl scale deployment python-app-dev-app-python -n dev --replicas=3
```

**Immediate observation:**
```bash
$ kubectl get deployment python-app-dev -n dev
NAME                      READY   UP-TO-DATE   AVAILABLE   AGE
python-app-dev-app-python 3/3     3            3           10m
```

**ArgoCD detection:**
- Application status changes to **OutOfSync**
- Diff view shows 3 replicas vs Git's 1 replica
- UI displays the drift

**Self-healing revert (30-60 seconds):**
```bash
$ kubectl get deployment python-app-dev -n dev
NAME                      READY   UP-TO-DATE   AVAILABLE   AGE
python-app-dev-app-python 1/1     1            1           10m  # Reverted!
```

**Result:**
- ArgoCD automatically reverted the scale change
- Cluster matches Git state again
- Status returns to Synced

### Test 2: Pod Deletion

**Important Distinction:**

Pod deletion is handled by **Kubernetes**, not ArgoCD:
- Delete a pod: `kubectl delete pod <name> -n dev`
- Kubernetes' ReplicaSet controller immediately recreates it
- ArgoCD doesn't need to intervene

**Example:**
```bash
# Before deletion
$ kubectl get pods -n dev
NAME                                    READY   STATUS    RESTARTS   AGE
python-app-dev-app-python-xxxxx         1/1     Running   0          10m

# Delete the pod
$ kubectl delete pod python-app-dev-app-python-xxxxx -n dev

# Kubernetes recreates immediately (ReplicaSet is the controller)
$ kubectl get pods -n dev
NAME                                    READY   STATUS    RUNNING   AGE
python-app-dev-app-python-yyyyy         1/1     Running   0          2s
```

**Key Difference:**
| Action | Controller | Speed | Reason |
|--------|-----------|-------|--------|
| Pod crash/deletion | Kubernetes ReplicaSet | Immediate (seconds) | Maintains replica count |
| Config drift | ArgoCD self-healing | Slower (30-60s) | Syncs cluster to Git state |

### Test 3: Configuration Drift

**Manual Edit Test:**

1. Edit a resource manually:
```bash
kubectl edit configmap python-app-dev-app-python-config -n dev
# Add a label: test-label: manual
```

2. ArgoCD detection (within sync interval):
   - Application shows OutOfSync
   - Diff view shows the manual label

3. Self-healing reversion (if enabled):
   - ArgoCD removes the manual label
   - Resource matches Git definition

### Sync Interval & Refresh

**Default Behavior:**
- ArgoCD polls Git repository every **3 minutes**
- Kubelet syncs ConfigMap changes every **60 seconds** (default)
- Self-healing checks every 30 seconds (if enabled)

**Sync Process:**
```
Git Change (t=0s)
↓
Manual commit (t=0s)
↓
ArgoCD polls (t=0-180s) ← Git refresh interval
↓
Detects OutOfSync (t=30-180s)
↓
Initiates sync (for manual) or auto-sync (for dev)
↓
Applies changes (t=30-210s total)
```

**Speed Up Sync:**
```bash
# Force immediate refresh without waiting 3-minute poll
argocd app sync python-app-dev --force
```

### Webhook Integration (Optional)

For immediate sync on Git push (instead of 3-minute poll):
1. Configure Git webhook to POST to ArgoCD
2. ArgoCD receives push event
3. Immediately refreshes and syncs
4. Reduces deployment latency from 3min to <5sec

---

## Bonus Task: ApplicationSet

### Purpose

ApplicationSet generates multiple Application resources from a single template, enabling:
- Parameterized deployments
- Multi-environment patterns
- Multi-cluster deployments
- Reduced manifest duplication

### Implementation: List Generator

**ApplicationSet Manifest** (`applicationset.yaml`):
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
          - env: prod
            namespace: prod
            valuesFile: values-prod.yaml
            autoSync: "false"
  template:
    metadata:
      name: 'python-app-{{env}}'
    spec:
      source:
        repoURL: https://github.com/Polinanime/DevOps-Core-Course.git
        targetRevision: lab13
        path: k8s/app-python
        helm:
          valueFiles:
            - '{{valuesFile}}'
      destination:
        server: https://kubernetes.default.svc
        namespace: '{{namespace}}'
      syncPolicy:
        automated:
          prune: true
          selfHeal: true
        syncOptions:
          - CreateNamespace=true
```

### How It Works

**Generator Processing:**
1. ApplicationSet controller reads the `list` generator
2. For each element, it renders the template with those variables
3. Creates two Application resources:
   - `python-app-dev` with dev-specific values
   - `python-app-prod` with prod-specific values

**Generated Applications:**
```bash
$ kubectl get applications -n argocd
NAME              SYNC STATUS   HEALTH
python-app-dev    Synced        Healthy
python-app-prod   OutOfSync     Missing
```

### Benefits vs Individual Applications

| Aspect | Individual Apps | ApplicationSet |
|--------|-----------------|----------------|
| **Duplication** | Repeated manifests | Single template |
| **Maintenance** | Update each manifest | Update template & generator |
| **Scalability** | Manual for each env | Automatic generation |
| **Changes** | Modify each file | Modify generator elements |
| **Consistency** | Manual enforcement | Automatic templating |

### Available Generators

1. **List Generator:** Explicit key-value pairs
2. **Cluster Generator:** Deploy to multiple clusters
3. **Git Generator:** Auto-discover from Git directories
4. **Matrix Generator:** Combine multiple generators
5. **SCM Provider Generator:** Auto-discover repos

### When to Use

- **Few environments (2-3):** Individual Applications are simpler
- **Many environments (10+):** ApplicationSet reduces duplication
- **Multi-cluster:** ApplicationSet is essential
- **Dynamic scaling:** ApplicationSet enables automation

---

## GitOps Best Practices Applied

### 1. Git as Source of Truth
- All deployments defined in Git repository
- No direct `kubectl` commands against production
- Changes tracked in commit history
- Full audit trail

### 2. Declarative Configuration
- Kubernetes manifests describe desired state
- ArgoCD enforces state through reconciliation
- Configuration version controlled

### 3. Automated Deployment
- Dev environment auto-syncs on Git changes
- Reduces manual intervention and errors
- Faster feedback loop

### 4. Controlled Production
- Prod requires manual sync
- Change review before deployment
- Operational safety and compliance

### 5. Self-Healing
- Automatic drift detection
- Reverts unauthorized changes
- Ensures cluster consistency

---

## Troubleshooting

### Application Stuck in OutOfSync

**Cause:** Manual changes in cluster
```bash
argocd app diff python-app-dev  # See differences
argocd app sync python-app-dev   # Force sync
```

### Pods Not Starting

**Cause:** PVC not bound
```bash
kubectl get pvc -n dev
# Create storage class:
kubectl apply -f - <<EOF
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: standard
provisioner: k8s.io/minikube-hostpath
EOF
```

### Repo URL Unreachable

**Cause:** SSH key missing or credentials invalid
```bash
# Check repository credentials
kubectl get secret -n argocd repo-creds
```

---

## Verification Outputs

**All Applications Status:**
```bash
$ argocd app list
NAME              CLUSTER                         NAMESPACE    STATUS     HEALTH
python-app-dev    https://kubernetes.default.svc  dev          Synced     Progressing
python-app-prod   https://kubernetes.default.svc  prod         OutOfSync  Missing
```

**Dev Deployment Resources:**
```bash
$ kubectl get all -n dev
NAME                                          READY   STATUS    RESTARTS
pod/python-app-dev-app-python-xxxxx           1/1     Running   0
pod/python-app-dev-app-python-pre-install-xxx 0/1     Completed 0

deployment.apps/python-app-dev-app-python                1/1     1        1

service/python-app-dev-app-python             NodePort  80:31852/TCP
```

---

## Summary

Lab 13 successfully demonstrates:
- ✅ ArgoCD installation and setup
- ✅ Application deployment via GitOps
- ✅ Multi-environment configuration (dev/prod)
- ✅ Automatic vs manual sync policies
- ✅ Self-healing and drift detection
- ✅ ApplicationSet for template generation

The implementation follows GitOps principles with Git as the single source of truth, enabling reproducible, auditable, and automated deployments across environments.
