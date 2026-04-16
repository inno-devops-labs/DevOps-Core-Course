# ArgoCD GitOps Deployment

## 1. ArgoCD Setup

### Installation

ArgoCD installed via Helm:

```bash
helm repo add argo https://argoproj.github.io/argo-helm
helm repo update
kubectl create namespace argocd
helm install argocd argo/argo-cd --namespace argocd
kubectl wait --for=condition=ready pod -l app.kubernetes.io/name=argocd-server -n argocd --timeout=120s
```

### Pods Verification

```
$ kubectl get pods -n argocd
NAME                                                READY   STATUS    RESTARTS      AGE
argocd-application-controller-0                     1/1     Running   1 (75m ago)   82m
argocd-applicationset-controller-58c9647667-mn2zw   1/1     Running   1 (75m ago)   82m
argocd-dex-server-d68bfd4b7-qmfnv                   1/1     Running   0             82m
argocd-notifications-controller-58f8fcd889-6qqkh    1/1     Running   1 (75m ago)   82m
argocd-redis-5d5bb8d56b-8bdlb                       1/1     Running   1 (75m ago)   82m
argocd-repo-server-5d5755cbb-6d2gq                  1/1     Running   1 (75m ago)   82m
argocd-server-5964cdf9fb-96tmn                      1/1     Running   1 (75m ago)   82m
```

### UI Access

```bash
kubectl port-forward svc/argocd-server -n argocd 8080:443
# Access at https://localhost:8080, username: admin
```

Password retrieved via:

```bash
kubectl -n argocd get secret argocd-initial-admin-secret -o jsonpath="{.data.password}" | base64 -d
```

### CLI

```bash
brew install argocd
argocd login localhost:8080 --insecure
```

```
$ argocd version --client
argocd: v3.3.6+998fb59.dirty
  BuildDate: 2026-03-27T19:12:28Z
  GitTag: v3.3.6
  GoVersion: go1.26.1
  Platform: darwin/arm64
```

## 2. Application Configuration

### Application Manifest (`k8s/argocd/application.yaml`)

```yaml
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: python-app
  namespace: argocd
spec:
  project: default
  source:
    repoURL: https://github.com/karishka1222/DevOps-Core-Course.git
    targetRevision: lab13
    path: k8s/python-app
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

Key fields:
- **source.repoURL** — GitHub repo containing the Helm chart
- **source.path** — path to chart within repo (`k8s/python-app`)
- **source.helm.valueFiles** — which values file to use
- **destination** — target cluster (`kubernetes.default.svc`) and namespace
- **syncPolicy** — manual sync (no `automated` block)

### Deploy & Sync

```bash
kubectl apply -f k8s/argocd/application.yaml
argocd app sync python-app
argocd app get python-app
```

<!-- PASTE: argocd app get python-app output after successful sync -->

### GitOps Workflow Test

1. Changed `replicaCount` in `values.yaml`
2. Committed and pushed
3. ArgoCD detected OutOfSync status
4. Synced changes via `argocd app sync python-app`

<!-- PASTE: argocd app get python-app showing Synced after the change -->

## 3. Multi-Environment Deployment

### Namespace Setup

```bash
kubectl create namespace dev
kubectl create namespace prod
```

### Dev Environment — Auto-Sync (`application-dev.yaml`)

| Parameter | Value |
|-----------|-------|
| Replicas | 1 |
| Resources | 64Mi/50m request, 128Mi/100m limit |
| Service | NodePort:30080 |
| Image Pull | IfNotPresent |
| Sync | **Automated** (prune + selfHeal) |

`selfHeal: true` reverts manual cluster modifications to match Git.
`prune: true` deletes resources removed from Git.

### Prod Environment — Manual Sync (`application-prod.yaml`)

| Parameter | Value |
|-----------|-------|
| Replicas | 5 |
| Resources | 256Mi/200m request, 512Mi/500m limit |
| Service | LoadBalancer |
| Image Tag | 1.0.0 |
| Sync | **Manual** |

Manual sync for production ensures:
- Changes are reviewed before deployment
- Controlled release timing
- Compliance and rollback planning

### App List

```
$ argocd app list
NAME                    CLUSTER                         NAMESPACE  PROJECT  STATUS   HEALTH   SYNCPOLICY
argocd/python-app       https://kubernetes.default.svc  default    default  Synced   Healthy  Manual
argocd/python-app-dev   https://kubernetes.default.svc  dev        default  Synced   Healthy  Auto-Prune
argocd/python-app-prod  https://kubernetes.default.svc  prod       default  Synced   Healthy  Manual
```

<!-- UPDATE: replace with actual output after push+sync -->

### Verification

```bash
$ kubectl get pods -n dev
```

<!-- PASTE: kubectl get pods -n dev output -->

```bash
$ kubectl get pods -n prod
```

<!-- PASTE: kubectl get pods -n prod output -->

## 4. Self-Healing Evidence

### Test 1: Manual Scale (Dev)

Dev has `selfHeal: true`, so ArgoCD should revert manual scaling.

```bash
# Before: 1 replica (defined in values-dev.yaml)
$ kubectl get pods -n dev

# Scale manually
$ kubectl scale deployment <deployment-name> -n dev --replicas=5

# ArgoCD detects drift and reverts within ~3 min
$ kubectl get pods -n dev -w
```

<!-- PASTE: before/after output showing ArgoCD reverting to 1 replica -->

### Test 2: Pod Deletion

This tests **Kubernetes** self-healing (ReplicaSet controller), not ArgoCD.

```bash
$ kubectl delete pod -n dev -l app.kubernetes.io/name=python-app
$ kubectl get pods -n dev -w
```

<!-- PASTE: output showing pod recreation by Kubernetes -->

The ReplicaSet controller immediately creates a replacement pod.

### Test 3: Configuration Drift

Manually add a label, ArgoCD reverts it:

```bash
$ kubectl label deployment <deployment-name> -n dev test-label=manual
$ argocd app diff python-app-dev
```

<!-- PASTE: argocd diff output, then revert evidence -->

### Kubernetes vs ArgoCD Self-Healing

| Aspect | Kubernetes | ArgoCD |
|--------|-----------|--------|
| What heals | Pod count / health | Full resource spec |
| Trigger | Pod crash or deletion | Config drift from Git |
| Mechanism | ReplicaSet controller | Periodic Git comparison |
| Speed | Immediate | ~3 min default polling |
| Example | Pod dies → new pod | Replicas manually changed → reverted |

### Sync Triggers

- **Automatic**: ArgoCD polls Git every **3 minutes** by default
- **Manual**: `argocd app sync <name>` or UI button
- **Webhook**: GitHub webhook for instant sync (optional)

## 5. Screenshots

<!-- INSERT: ArgoCD UI showing all applications (python-app, python-app-dev, python-app-prod) -->

<!-- INSERT: Sync status view -->

<!-- INSERT: Application details view for python-app-dev -->

## 6. Bonus: ApplicationSet

### Manifest (`k8s/argocd/applicationset.yaml`)

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
          - env: prod
            namespace: prod
            valuesFile: values-prod.yaml
  template:
    metadata:
      name: 'python-app-{{env}}'
    spec:
      project: default
      source:
        repoURL: https://github.com/karishka1222/DevOps-Core-Course.git
        targetRevision: lab13
        path: k8s/python-app
        helm:
          valueFiles:
            - '{{valuesFile}}'
      destination:
        server: https://kubernetes.default.svc
        namespace: '{{namespace}}'
      syncPolicy:
        syncOptions:
          - CreateNamespace=true
```

### How It Works

The **List generator** iterates over `elements`, producing one `Application` per entry. Placeholders `{{env}}`, `{{namespace}}`, `{{valuesFile}}` are substituted per element.

### Benefits over Individual Applications

| Aspect | Individual Apps | ApplicationSet |
|--------|----------------|---------------|
| Maintenance | Edit each file | Single template |
| Scaling | Linear file growth | Add list element |
| Consistency | Manual structure sync | Guaranteed by template |
| Adding env | New YAML file | New list entry |

### Available Generator Types

- **List** — explicit parameter sets (used here)
- **Git** — auto-discover from repo directories/files
- **Cluster** — multi-cluster deployments
- **Matrix** — combine multiple generators
- **Merge** — merge generator outputs

### Deployment

```bash
# First delete individual apps to avoid conflicts
kubectl delete -f k8s/argocd/application-dev.yaml
kubectl delete -f k8s/argocd/application-prod.yaml

# Apply ApplicationSet
kubectl apply -f k8s/argocd/applicationset.yaml
argocd app list
```

<!-- PASTE: argocd app list showing ApplicationSet-generated apps -->

<!-- INSERT: Screenshot of ArgoCD UI with ApplicationSet-generated apps -->
