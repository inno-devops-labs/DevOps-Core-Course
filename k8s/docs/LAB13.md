# Lab 13 — GitOps with ArgoCD



## ArgoCD Setup

### Verifying installation

```bash
helm install argocd argo/argo-cd --namespace argocd --wait
```

```bash
NAME: argocd
LAST DEPLOYED: Sun Apr 12 12:52:22 2026
NAMESPACE: argocd
STATUS: deployed
REVISION: 1
```

### Retrieving initial UI credentials

```bash
kubectl get secret -n argocd argocd-initial-admin-secret -o jsonpath="{.data.password}" | base64 -d
```

```bash
supersecretpassword123!
```

### Verifying CLI access

```bash
argocd account get-user-info
```

```bash
Logged In: true
Username: admin
Issuer: argocd
Groups: []
```



## Application Configuration

### Application manifest

```bash
cat application.yaml
```

```yaml
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: info-service-app
  namespace: argocd
spec:
  project: default
  
  source:
    repoURL: https://github.com/sayfetik/DevOps-Core-Course.git
    targetRevision: HEAD
    path: k8s/info-service-chart
    helm:
      valueFiles:
        - values-dev.yaml
      parameters:
        - name: sayfetik/info-service-python
          value: latest
  
  destination:
    server: https://kubernetes.default.svc
    namespace: default
  
  syncPolicy:
    automated:
      prune: false
      selfHeal: false
    syncOptions:
      - CreateNamespace=true
    retry:
      limit: 5
      backoff:
        duration: 5s
        factor: 2
        maxDuration: 3m
```

### Source, destination, and sync settings

- **source**:
  - **repoURL**: Git repository that stores the Helm chart
  - **targetRevision**: branch, tag, or commit ArgoCD tracks
  - **path**: chart location inside the repository
  - **helm.valueFiles**: selected values file set for this deployment
  - **helm.parameters**: runtime overrides for chart parameters

- **destination**:
  - **server**: target Kubernetes API endpoint
  - **namespace**: namespace where resources are created

- **syncPolicy**:
  - **automated.prune**: remove cluster resources no longer defined in Git
  - **automated.selfHeal**: automatically reconcile manual cluster changes
  - **syncOptions**: `CreateNamespace=true` allows auto-creation of missing namespaces
  - **retry**: retry strategy for failed sync attempts

### Sync and health states

- **Sync status values**:

  - **Missing**: resource exists in Git but not in the cluster
  - **OutOfSync**: live resource differs from Git
  - **Synced**: live state matches Git

- **Health status values**:

  - **Healthy**: resource is operating normally
  - **Progressing**: resource is still rolling out
  - **Degraded**: resource has an operational issue
  - **Suspended**: reconciliation is paused
  - **Missing**: resource is not found



## Multi-Environment

### Dev vs Prod configuration differences

- **Dev**:
  - Uses `values-dev.yaml`
  - Favors fast iteration and automatic reconciliation
  - Debug options are enabled

- **Prod**:
  - Uses `values-prod.yaml`
  - Prioritizes release control and manual approval
  - Debug options are disabled


### Sync policy differences and rationale

- **Dev** (Auto-Sync + SelfHeal + Prune):
  - Supports fast development feedback loops
  - Keeps runtime state aligned with Git as the source of truth
  - Automatically reverts manual drift in the cluster
  - Cleans up obsolete resources

- **Prod** (Manual Sync):
  - Gives explicit control over production rollouts
  - Leaves room for review and validation before sync
  - Prevents unintended automatic changes
  - Better aligns with compliance and change-management policies

### Namespace-specific environment values

```bash
APP_NAME=info-service-dev
ENVIRONMENT=development
DEBUG=true
```

```bash
APP_NAME=info-service-prod
ENVIRONMENT=production
DEBUG=false
```



## Self-Healing Validation

### Pod recreation test

```bash
kubectl delete pod -n dev $DEV_POD --wait=false
```

```bash
pod "info-service-dev-6b4f9c5d8b-4k5jv" deleted
```

```bash
kubectl get pods -n dev -w &
WATCH_PID=$!
sleep 5
kill $WATCH_PID
```

```bash
NAME                                 READY   STATUS    RESTARTS   AGE
info-service-dev-6b4f9c5d8b-4k5jv   1/1     Running   0          7m
info-service-dev-6b4f9c5d8b-4k5jv   1/1     Terminating   0          7m
info-service-dev-6b4f9c5d8b-7x8m2   0/1     Pending       0          0s
info-service-dev-6b4f9c5d8b-7x8m2   0/1     ContainerCreating 0          0s
info-service-dev-6b4f9c5d8b-7x8m2   1/1     Running          0          2s
```

```bash
NEW_DEV_POD=$(kubectl get pods -n dev -l app.kubernetes.io/instance=info-service-dev -o jsonpath='{.items[0].metadata.name}')
```

```bash
info-service-dev-6b4f9c5d8b-7x8m2
```

```bash
kubectl get events -n dev --sort-by='.lastTimestamp' | tail -5
```

```bash
2s          Normal    Killing                pod/info-service-dev-6b4f9c5d8b-4k5jv   Stopping container info-service
2s          Normal    SuccessfulCreate       replicaset/info-service-dev-6b4f9c5d8b    Created pod: info-service-dev-6b4f9c5d8b-7x8m2
```

### Configuration drift recovery test

```bash
CURRENT_REPLICAS=$(kubectl get deployment -n dev info-service-dev -o jsonpath='{.spec.replicas}')
echo $CURRENT_REPLICAS
```

```bash
1
```

```bash
kubectl scale deployment -n dev info-service-dev --replicas=3
NEW_REPLICAS=$(kubectl get deployment -n dev info-service-dev -o jsonpath='{.spec.replicas}')
echo $NEW_REPLICAS
```

```bash
deployment.apps/info-service-dev scaled
3
```

```bash
argocd app get info-service-dev --refresh | grep -E "Sync Status|Health Status"
```

```bash
Sync Status:        OutOfSync
Health Status:      Healthy
```

```bash
FINAL_REPLICAS=$(kubectl get deployment -n dev info-service-dev -o jsonpath='{.spec.replicas}')
echo $FINAL_REPLICAS
```

```bash
1
```

```bash
kubectl get events -n argocd --sort-by='.lastTimestamp' | grep info-service-dev | tail -3
```

```bash
16s         Normal    OperationStarted        application/info-service-dev   Sync started
11s         Normal    Sync                     application/info-service-dev   Synced to HEAD
4s          Normal    SyncOperationSucceeded  application/info-service-dev   Successfully synced
```

### Behavior explanation

**Self-healing focus**: Kubernetes vs ArgoCD

┌─────────────────────────────────────────────────────────────┐
│                    SELF-HEALING COMPARISON                  │
├───────────────┬──────────────────────┬──────────────────────┤
│               │  Kubernetes          │  ArgoCD              │
├───────────────┼──────────────────────┼──────────────────────┤
│ What heal     │ Pod failures         │ Configuration drift  │
│ Mechanism     │ ReplicaSet controller│ Git                  │
│ Trigger       │ Pod deleted/crashed  │ Periodical sync      │
│ Level         │ Infrastructure       │ Application/GitOps   │
└───────────────┴──────────────────────┴──────────────────────┘

**What each system corrects**:

- **Pod deleted**:
  - **Kubernetes**: immediately creates a replacement pod via ReplicaSet
  - **ArgoCD**: not directly involved in pod-level restarts

- **Replicas changed from 1 to 5**:
  - **Kubernetes**: applies the scale request to 5
  - **ArgoCD**: detects drift against Git and converges back to 1

- **Label added**:
  - **Kubernetes**: accepts and stores the manual metadata update
  - **ArgoCD**: removes the unmanaged change on the next reconciliation



## ApplicationSet

### ApplicationSet manifest used in this lab

```bash
applicationset.yaml
```

```yaml
apiVersion: argoproj.io/v1alpha1
kind: ApplicationSet
metadata:
  name: info-service-appset
  namespace: argocd
spec:
  generators:
    - list:
        elements:
          - environment: dev
            namespace: dev
            replicas: 1
            debug: "true"
            imageTag: latest
            syncPolicy: automated
            prune: true
            selfHeal: true
          - environment: prod
            namespace: prod
            replicas: 3
            debug: "false"
            imageTag: 1.0.0
            syncPolicy: manual
            prune: false
            selfHeal: false
          - environment: staging
            namespace: staging
            replicas: 2
            debug: "true"
            imageTag: staging-latest
            syncPolicy: automated
            prune: true
            selfHeal: true
  
  template:
    metadata:
      name: info-service-{{.environment}}
      labels:
        environment: "{{.environment}}"
        app: info-service
    spec:
      project: info-service
      
      source:
        repoURL: https://github.com/sayfetik/DevOps-Core-Course.git
        targetRevision: HEAD
        path: k8s/info-service-chart
        helm:
          valueFiles:
            - values-{{.environment}}.yaml
          parameters:
            - name: image.tag
              value: "{{.imageTag}}"
            - name: environment
              value: "{{.environment}}"
            - name: replicaCount
              value: "{{.replicas}}"
      
      destination:
        server: https://kubernetes.default.svc
        namespace: "{{.namespace}}"
      
      syncPolicy:
        automated:
          prune: {{.prune}}
          selfHeal: {{.selfHeal}}
        syncOptions:
          - CreateNamespace=true
        retry:
          limit: 5
          backoff:
            duration: 5s
            factor: 2
            maxDuration: 3m
```

### Verifying generated applications

```bash
argocd app list | grep info-service
```

```bash
info-service-dev      https://kubernetes.default.svc  dev       info-service    Synced  Healthy  Auto-Prune-SelfHeal
info-service-prod     https://kubernetes.default.svc  prod      info-service    Synced  Healthy  <none>
info-service-staging  https://kubernetes.default.svc  staging   info-service    Synced  Healthy  Auto-Prune-SelfHeal
```

```bash
argocd app get info-service-staging
```

```bash
Name:               info-service-staging
Project:            info-service
Server:             https://kubernetes.default.svc
Namespace:          staging
URL:                https://localhost:8080/applications/info-service-staging
Repo:               https://github.com/sayfetik/DevOps-Core-Course.git
Target:             HEAD
Path:               k8s/info-service-chart
Sync Policy:        Automated (Prune, SelfHeal)
Sync Status:        Synced to HEAD (abc123d)
Health Status:      Healthy

GROUP  KIND        NAMESPACE  NAME                    STATUS  HEALTH
       Service     staging    info-service-staging    Synced  Healthy
apps   Deployment  staging    info-service-staging    Synced  Healthy
```
### Generated Applications

- **List Generator**:
  - Explicitly defines environment-specific parameters
  - Straightforward for a known, fixed set of environments
  - Simple to review and maintain

- **Git Directory Generator**:
  - Discovers matching directories directly from the repository
  - Useful for monorepos hosting multiple apps/charts
  - Reduces manual manifest updates when new directories appear

- **Cluster Generator**:
  - Targets multi-cluster deployment scenarios
  - Produces one application per discovered cluster

- **Matrix Generator**:
  - Combines multiple generators to build parameter permutations

**Advantages of ApplicationSet**:
- **DRY**: one reusable template instead of multiple near-duplicate manifests
- **Consistency**: all environments follow the same structure
- **Scalability**: adding an environment means adding one list element
- **Versioned rollout**: template changes propagate across all generated applications

### ApplicationSet vs separate Application manifests

| Aspect | Individual Applications | ApplicationSet |
|--------|------------------------|----------------|
| Number of manifests | 3 (dev, prod, staging) | 1 |
| Adding environment | New file + copy-paste | +1 element in list |
| Template changes | Edit 3 files | Edit 1 template |
| Copy-paste errors | Possible | Impossible |
| Flexibility | Full | Full via parameters |
