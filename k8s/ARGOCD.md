# Lab 13 - GitOps with ArgoCD

## 1. Overview

This lab deploys the existing Helm chart in [`k8s/devops-info-service`](./devops-info-service/Chart.yaml) through ArgoCD instead of running `helm install` manually.

Files added for this lab:

```text
k8s/argocd/
├── application.yaml
├── application-dev.yaml
├── application-prod.yaml
├── install-values.yaml
├── namespaces.yaml
└── bonus/
    └── applicationset.yaml
```

Design choices for this repository:

- the single-app manifest in `k8s/argocd/application.yaml` stays on manual sync for the initial GitOps walkthrough
- the `dev` app uses auto-sync with `prune` and `selfHeal`
- the `prod` app stays manual to preserve a review gate
- Helm hooks are disabled in ArgoCD-managed apps to keep syncs idempotent because ArgoCD maps Helm hooks into its own sync phases instead of running a native Helm install lifecycle
- the chart still references the local Minikube image `devops-info-service:lab09`, so the image must exist in the cluster before syncing

## 2. Prerequisites

Start Minikube and ensure the application image is available locally:

```bash
minikube start --driver=docker
docker build -t devops-info-service:lab09 ./app_python
minikube image load devops-info-service:lab09
```

Push the `lab13` branch so ArgoCD can read the manifests from Git:

```bash
git push -u origin lab13
```

## 3. ArgoCD Installation

Create the namespaces used in this lab:

```bash
kubectl apply -f k8s/argocd/namespaces.yaml
```

Install ArgoCD from the Helm chart:

```bash
helm repo add argo https://argoproj.github.io/argo-helm
helm repo update
helm install argocd argo/argo-cd \
  --namespace argocd \
  -f k8s/argocd/install-values.yaml \
  --wait
```

Verify the installation:

```bash
kubectl get pods -n argocd
kubectl get svc -n argocd
```

Access the UI and retrieve the initial admin password:

```bash
kubectl port-forward svc/argocd-server -n argocd 8080:443
kubectl -n argocd get secret argocd-initial-admin-secret \
  -o jsonpath="{.data.password}" | base64 -d && echo
```

Log in with the CLI:

```bash
argocd login localhost:8080 --insecure
argocd app list
```

## 4. Application Configuration

### Base Manual Application

[`k8s/argocd/application.yaml`](./argocd/application.yaml) deploys one manual-sync application to the `lab13-base` namespace.

Important fields:

- `repoURL`: `https://github.com/nonamecorn/DevOps-Core-Course.git`
- `targetRevision`: `lab13`
- `path`: `k8s/devops-info-service`
- `valueFiles`: `values.yaml`
- `destination.namespace`: `lab13-base`
- manual sync only

The base app overrides `service.type=ClusterIP` so it can coexist with the dev app, which already uses a fixed `NodePort`.

Apply it and trigger the first sync:

```bash
kubectl apply -f k8s/argocd/application.yaml
argocd app get devops-info-service-base
argocd app sync devops-info-service-base
argocd app wait devops-info-service-base --health --sync
kubectl get all -n lab13-base
```

## 5. Multi-Environment Deployment

### Dev

[`k8s/argocd/application-dev.yaml`](./argocd/application-dev.yaml) deploys the chart with `values-dev.yaml` into the `dev` namespace.

Characteristics:

- `replicaCount: 1`
- smaller CPU and memory requests/limits
- `NodePort` service on `30081`
- automated sync enabled
- `prune: true`
- `selfHeal: true`

Deploy:

```bash
kubectl apply -f k8s/argocd/application-dev.yaml
argocd app wait devops-info-service-dev --health
kubectl get all -n dev
```

### Prod

[`k8s/argocd/application-prod.yaml`](./argocd/application-prod.yaml) deploys the chart with `values-prod.yaml` into the `prod` namespace.

Characteristics:

- `replicaCount: 3`
- higher CPU and memory requests/limits
- `LoadBalancer` service
- manual sync

Deploy:

```bash
kubectl apply -f k8s/argocd/application-prod.yaml
argocd app sync devops-info-service-prod
argocd app wait devops-info-service-prod --health --sync
kubectl get all -n prod
```

Why keep prod manual:

- it adds an explicit review point before rollout
- it avoids deploying every commit automatically
- it leaves room for timing changes around maintenance windows or rollback planning

## 6. GitOps Workflow

Make a Git change, commit it, and push it:

```bash
sed -i 's/^replicaCount: 1$/replicaCount: 2/' k8s/devops-info-service/values-dev.yaml
git add k8s/devops-info-service/values-dev.yaml
git commit -m "Tune dev replica count for lab13"
git push
```

Expected behavior:

- ArgoCD marks `devops-info-service-dev` as `OutOfSync`
- the dev app auto-syncs back to `Synced`
- the prod app stays `OutOfSync` until a manual sync is triggered

Useful commands:

```bash
argocd app list
argocd app history devops-info-service-dev
argocd app get devops-info-service-dev
argocd app get devops-info-service-prod
```

## 7. Self-Healing Tests

### Manual Scale Drift

Scale the dev deployment away from Git:

```bash
kubectl scale deployment/devops-info-service-dev -n dev --replicas=5
kubectl get deployment -n dev -w
```

Expected behavior:

- Kubernetes immediately applies the manual scale
- ArgoCD detects the drift on the dev app
- ArgoCD syncs it back to the Git-defined replica count from `values-dev.yaml`

Check the diff:

```bash
argocd app diff devops-info-service-dev
```

### Pod Deletion

Delete one pod in the dev namespace:

```bash
kubectl delete pod -n dev -l app.kubernetes.io/instance=devops-info-service-dev
kubectl get pods -n dev -w
```

Expected behavior:

- the ReplicaSet recreates the pod immediately
- this is Kubernetes self-healing, not ArgoCD self-healing

### Configuration Drift

Patch the deployment with a manual label:

```bash
kubectl label deployment/devops-info-service-dev \
  -n dev drift=manual --overwrite
argocd app diff devops-info-service-dev
```

Expected behavior:

- ArgoCD shows the added label as drift
- because `selfHeal` is enabled, ArgoCD removes the label on the next reconciliation

Difference between the two healing mechanisms:

- Kubernetes healing recreates failed or deleted pods so the workload matches the Deployment spec already stored in the cluster
- ArgoCD healing reconciles the cluster back to the desired state stored in Git

Reconciliation timing:

- Git changes are detected on ArgoCD's reconciliation loop or by webhook/manual refresh
- the default Git polling interval is `120s` plus up to `60s` of jitter, so it is usually observed as about 3 minutes
- live cluster drift on an app with `selfHeal: true` can be corrected without waiting for a new Git commit

## 8. Screenshots To Capture

Add screenshots after running the lab:

1. ArgoCD UI with both `devops-info-service-dev` and `devops-info-service-prod`
2. Application details page for the dev app showing `Auto-Sync`
3. Application details page for the prod app showing manual sync
4. Diff or status view during a drift/self-heal event

Suggested location:

```text
k8s/argocd/screenshots/
```

## 9. Bonus - ApplicationSet

Bonus manifest: [`k8s/argocd/bonus/applicationset.yaml`](./argocd/bonus/applicationset.yaml)

This manifest uses a List generator to create both environment applications from one template.

Why it is useful:

- one template manages naming, repo source, destination, and Helm settings
- adding a new environment becomes a data change instead of a copy-paste change
- it scales better for mono-repos or many clusters

Important note:

- use the ApplicationSet instead of the individual `application-dev.yaml` and `application-prod.yaml` manifests, not together with them

Apply the bonus version:

```bash
kubectl delete -f k8s/argocd/application-dev.yaml -f k8s/argocd/application-prod.yaml
kubectl apply -f k8s/argocd/bonus/applicationset.yaml
kubectl get applications -n argocd
kubectl get applicationsets -n argocd
```

## 10. Validation Checklist

- ArgoCD is installed in the `argocd` namespace
- the base application is created from `k8s/argocd/application.yaml`
- `dev` uses automated sync with pruning and self-healing
- `prod` uses manual sync
- `dev` and `prod` deploy different Helm values files
- self-healing tests are documented and reproducible
