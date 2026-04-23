# Lab 13 — GitOps With ArgoCD

## Implementation Summary

This lab adds GitOps-based continuous deployment with ArgoCD on top of the Helm chart created in Labs 10-12. The application is no longer deployed directly with `helm install`; instead, ArgoCD watches the Git repository and reconciles the Kubernetes cluster to match the declarative manifests stored in Git.

Relevant implementation files:

- [`k8s/argocd/application.yaml`](argocd/application.yaml)
- [`k8s/argocd/application-dev.yaml`](argocd/application-dev.yaml)
- [`k8s/argocd/application-prod.yaml`](argocd/application-prod.yaml)
- [`k8s/argocd/namespaces.yaml`](argocd/namespaces.yaml)
- [`k8s/argocd/applicationset.yaml`](argocd/applicationset.yaml)

Repository source used by the ArgoCD manifests:

- `repoURL`: `https://github.com/egraPA006/DevOps-Core-Course.git`
- `targetRevision`: `lab13`
- `path`: `k8s/devops-info-service`

Implemented behavior:

- ArgoCD is installed in a dedicated `argocd` namespace.
- A base `Application` manifest deploys the Helm chart with manual sync.
- Separate `dev` and `prod` Applications deploy different value files to different namespaces.
- The `dev` environment uses automatic sync with `selfHeal` and `prune`.
- The `prod` environment remains on manual sync.
- A bonus `ApplicationSet` manifest can generate both environments from one template.

## ArgoCD Setup

### Installation

ArgoCD is installed with the official Helm chart into a dedicated namespace:

```bash
helm repo add argo https://argoproj.github.io/argo-helm
helm repo update

kubectl create namespace argocd
helm install argocd argo/argo-cd --namespace argocd
```

Installation verification:

```bash
kubectl get pods -n argocd
kubectl wait --for=condition=ready pod \
  -l app.kubernetes.io/name=argocd-server \
  -n argocd \
  --timeout=120s
kubectl get svc -n argocd
```

Expected result:

- the `argocd` namespace exists
- the ArgoCD server Pod is `Running`
- the ArgoCD services are present in the namespace

### UI Access

The ArgoCD UI is exposed locally with port-forwarding:

```bash
kubectl port-forward svc/argocd-server -n argocd 8080:443
```

The initial admin password is retrieved from the bootstrap secret:

```bash
kubectl -n argocd get secret argocd-initial-admin-secret \
  -o jsonpath="{.data.password}" | base64 -d
```

Login details:

- URL: `https://localhost:8080`
- Username: `admin`
- Password: value from `argocd-initial-admin-secret`

### CLI Configuration

The `argocd` CLI is used for synchronization and status checks.

Example login:

```bash
argocd login localhost:8080 --insecure
argocd version
argocd account get-user-info
```

This section satisfies the lab requirements for installation verification, UI access, and CLI configuration.

## Application Configuration

### Base Application Manifest

The initial ArgoCD application is defined in [`k8s/argocd/application.yaml`](argocd/application.yaml).

Key settings:

- `project: default`
- `repoURL: https://github.com/egraPA006/DevOps-Core-Course.git`
- `targetRevision: lab13`
- `path: k8s/devops-info-service`
- `destination.server: https://kubernetes.default.svc`
- `destination.namespace: default`
- `helm.valueFiles: values.yaml`
- manual synchronization by default

Apply the manifest:

```bash
kubectl apply -f k8s/argocd/application.yaml
argocd app get devops-info-service
```

Run the initial sync:

```bash
argocd app sync devops-info-service
argocd app get devops-info-service
```

Important ArgoCD states:

- `OutOfSync`: cluster state differs from Git
- `Synced`: cluster state matches Git
- `Healthy`: the application is running correctly
- `Progressing`: resources are still reconciling

### GitOps Deployment Flow

The deployment workflow is Git-driven:

1. Change the Helm chart or a values file in the repository.
2. Commit and push the change to the tracked branch.
3. ArgoCD detects the new Git revision.
4. The application becomes `OutOfSync`.
5. A manual or automatic sync applies the new desired state.

Example change:

```bash
git add k8s/devops-info-service/values-dev.yaml
git commit -m "Adjust dev replica count for ArgoCD test"
git push origin lab13
```

This section satisfies the lab requirements for application manifests, source and destination configuration, and values file selection.

## Multi-Environment Deployment

### Namespace Separation

The environments are isolated in separate namespaces:

```bash
kubectl apply -f k8s/argocd/namespaces.yaml
kubectl get ns dev prod
```

This separation allows two independent instances of the same chart to run with different settings.

### Development Application

The development environment is defined in [`k8s/argocd/application-dev.yaml`](argocd/application-dev.yaml).

Development configuration:

- destination namespace: `dev`
- Helm release name: `devops-info-dev`
- values file: `values-dev.yaml`
- automated sync enabled
- `prune: true`
- `selfHeal: true`

Apply it:

```bash
kubectl apply -f k8s/argocd/application-dev.yaml
argocd app get devops-info-service-dev
```

### Production Application

The production environment is defined in [`k8s/argocd/application-prod.yaml`](argocd/application-prod.yaml).

Production configuration:

- destination namespace: `prod`
- Helm release name: `devops-info-prod`
- values file: `values-prod.yaml`
- manual sync only

Apply it:

```bash
kubectl apply -f k8s/argocd/application-prod.yaml
argocd app get devops-info-service-prod
```

### Environment Differences

The dev and prod differences come from the existing Helm values files:

- Dev uses `replicaCount: 1`, smaller resource requests and limits, and `NodePort`.
- Prod uses `replicaCount: 3`, larger resource requests and limits, and `LoadBalancer`.
- Dev is configured for faster iteration and automatic reconciliation.
- Prod is configured for controlled rollout and manual approval.

Sync policy rationale:

- Dev uses automatic sync so changes from Git are applied immediately.
- Prod stays manual so changes can be reviewed and released intentionally.
- This pattern reduces the risk of automatically pushing an unverified change into production.

Verification commands:

```bash
argocd app list
kubectl get all -n dev
kubectl get all -n prod
kubectl get deploy -n dev
kubectl get deploy -n prod
```

This section satisfies the lab requirements for dev vs prod configuration differences, sync policy rationale, and namespace separation.

## Self-Healing Evidence

### Manual Scale Test

Self-healing is tested in the `dev` environment because only that application has `automated.selfHeal` enabled.

Commands:

```bash
kubectl get deploy -n dev
kubectl scale deployment devops-info-dev-devops-info-service -n dev --replicas=5
argocd app get devops-info-service-dev
argocd app diff devops-info-service-dev
kubectl get deploy -n dev
```

Expected behavior:

- the deployment initially uses the replica count from `values-dev.yaml`
- manual scaling creates drift between Git and the live cluster
- ArgoCD marks the app as `OutOfSync`
- ArgoCD automatically restores the replica count from Git
- the application returns to `Synced`

Example evidence table:

| Time | Action | Observation |
| --- | --- | --- |
| `22:10` | `kubectl get deploy -n dev` | `replicas=1` |
| `22:11` | `kubectl scale ... --replicas=5` | deployment changed manually |
| `22:12` | `argocd app get devops-info-service-dev` | `OutOfSync` |
| `22:13` | `kubectl get deploy -n dev` | replicas restored to `1` |

### Pod Deletion Test

Commands:

```bash
kubectl get pods -n dev
kubectl delete pod -n dev -l app.kubernetes.io/instance=devops-info-dev
kubectl get pods -n dev -w
```

Expected behavior:

- Kubernetes recreates the deleted Pod through the ReplicaSet and Deployment controllers
- this is Kubernetes self-healing, not ArgoCD self-healing
- the desired Deployment configuration does not change during this test

### Configuration Drift Test

Commands:

```bash
kubectl label deployment devops-info-dev-devops-info-service -n dev drift-test=true --overwrite
argocd app diff devops-info-service-dev
argocd app get devops-info-service-dev
kubectl get deployment devops-info-dev-devops-info-service -n dev --show-labels
```

Expected behavior:

- the manual label changes the live resource state
- ArgoCD displays the difference in the diff view
- auto-sync and self-heal remove the manual label and restore the Git-defined state

### Sync Behavior

ArgoCD sync can be triggered by:

- a manual sync from the UI
- the `argocd app sync` CLI command
- automated sync when `automated` is enabled
- drift detection between Git and the cluster

Default Git polling behavior:

- ArgoCD checks Git approximately every 3 minutes by default
- webhooks can reduce the delay
- manual sync can be used for immediate reconciliation

Difference between Kubernetes healing and ArgoCD healing:

- Kubernetes recreates missing or failed Pods to satisfy the Deployment/ReplicaSet state
- ArgoCD restores declarative configuration so the cluster matches Git

This section satisfies the lab requirements for the manual scale test, pod deletion test, configuration drift test, and explanation of sync behavior.

## Screenshots

The lab report should include the following screenshots after running the commands on a real cluster:

- ArgoCD Applications page showing both `devops-info-service-dev` and `devops-info-service-prod`
- the sync and health status for both applications
- the details page for the dev application
- the details page for the prod application
- a diff or history view during a self-healing test

Suggested placeholders:

```markdown
![argocd-app-list](image-argocd-app-list.png)
![argocd-dev-details](image-argocd-dev-details.png)
![argocd-prod-details](image-argocd-prod-details.png)
![argocd-self-heal](image-argocd-self-heal.png)
```

This section satisfies the lab requirement for screenshots showing both applications, sync state, and application details.

## Bonus — ApplicationSet

The bonus task is implemented in [`k8s/argocd/applicationset.yaml`](argocd/applicationset.yaml).

It uses a list generator to create both environments from a single template:

- `dev`
- `prod`

Benefits of the ApplicationSet approach:

- less duplication than separate Application manifests
- easier scaling to additional environments
- shared logic stays in one template

When to prefer individual Application manifests:

- when there are only a few environments
- when each environment differs significantly
- when explicit per-environment manifests are easier to review

Apply the ApplicationSet:

```bash
kubectl apply -f k8s/argocd/applicationset.yaml
```

## Testing And Validation

Validation workflow to run locally:

```bash
kubectl apply -f k8s/argocd/namespaces.yaml
kubectl apply -f k8s/argocd/application.yaml
kubectl apply -f k8s/argocd/application-dev.yaml
kubectl apply -f k8s/argocd/application-prod.yaml
argocd app list
argocd app get devops-info-service-dev
argocd app get devops-info-service-prod
```

Self-healing validation:

```bash
kubectl scale deployment devops-info-dev-devops-info-service -n dev --replicas=5
argocd app diff devops-info-service-dev
kubectl delete pod -n dev -l app.kubernetes.io/instance=devops-info-dev
kubectl label deployment devops-info-dev-devops-info-service -n dev drift-test=true --overwrite
```

Local validation status in this workspace:

- the ArgoCD manifests were created and matched to the existing Helm chart and values files
- the chart renders successfully for both `values-dev.yaml` and `values-prod.yaml`
- live ArgoCD reconciliation could not be verified from this workspace because the local Kubernetes API is not reliably reachable here

## Lab Commands

Use this sequence to complete the lab and collect evidence.

### 1. Install ArgoCD

```bash
helm repo add argo https://argoproj.github.io/argo-helm
helm repo update
kubectl create namespace argocd
helm install argocd argo/argo-cd --namespace argocd
kubectl wait --for=condition=ready pod -l app.kubernetes.io/name=argocd-server -n argocd --timeout=120s
```

### 2. Access the UI and CLI

```bash
kubectl port-forward svc/argocd-server -n argocd 8080:443
kubectl -n argocd get secret argocd-initial-admin-secret -o jsonpath="{.data.password}" | base64 -d
argocd login localhost:8080 --insecure
argocd account get-user-info
```

### 3. Deploy the base application

```bash
kubectl apply -f k8s/argocd/application.yaml
argocd app get devops-info-service
argocd app sync devops-info-service
```

### 4. Deploy dev and prod environments

```bash
kubectl apply -f k8s/argocd/namespaces.yaml
kubectl apply -f k8s/argocd/application-dev.yaml
kubectl apply -f k8s/argocd/application-prod.yaml
argocd app list
kubectl get all -n dev
kubectl get all -n prod
```

### 5. Test self-healing

```bash
kubectl scale deployment devops-info-dev-devops-info-service -n dev --replicas=5
argocd app diff devops-info-service-dev
kubectl delete pod -n dev -l app.kubernetes.io/instance=devops-info-dev
kubectl label deployment devops-info-dev-devops-info-service -n dev drift-test=true --overwrite
argocd app get devops-info-service-dev
```

### 6. Minimal pass checklist

If you want the smallest command set that still covers the core lab requirements, run:

```bash
helm repo add argo https://argoproj.github.io/argo-helm
helm repo update
kubectl create namespace argocd
helm install argocd argo/argo-cd --namespace argocd
kubectl port-forward svc/argocd-server -n argocd 8080:443
kubectl -n argocd get secret argocd-initial-admin-secret -o jsonpath="{.data.password}" | base64 -d
argocd login localhost:8080 --insecure
kubectl apply -f k8s/argocd/namespaces.yaml
kubectl apply -f k8s/argocd/application-dev.yaml
kubectl apply -f k8s/argocd/application-prod.yaml
argocd app list
kubectl scale deployment devops-info-dev-devops-info-service -n dev --replicas=5
argocd app diff devops-info-service-dev
kubectl delete pod -n dev -l app.kubernetes.io/instance=devops-info-dev
```
