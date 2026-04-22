# Lab 13 - GitOps with ArgoCD

Run date: April 22, 2026

This lab was executed on a live `kind` cluster. ArgoCD was installed, applications were synced from the `lab13` branch, UI screenshots were captured, and drift/self-healing scenarios were verified on the running cluster.

Tested Git revision:

```text
2a641d25c0e0b8a5ec61951c18a36c01d4a0e0be
```

## Files

- `k8s/argocd/install-values.yaml`
- `k8s/argocd/namespaces.yaml`
- `k8s/argocd/application.yaml`
- `k8s/argocd/application-dev.yaml`
- `k8s/argocd/application-prod.yaml`
- `k8s/argocd/applicationset.yaml`
- `k8s/ARGOCD.md`
- `k8s/screenshots/06-argocd-applications.png`
- `k8s/screenshots/07-argocd-dev-details.png`
- `k8s/screenshots/08-argocd-prod-details.png`

## ArgoCD Installation

ArgoCD was installed from the upstream Helm chart into namespace `argocd`.

Installation values:

```yaml
global:
  domain: argocd.local

configs:
  params:
    server.insecure: true

server:
  service:
    type: ClusterIP

redis-ha:
  enabled: false
```

Namespaces were prepared with:

```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: argocd
---
apiVersion: v1
kind: Namespace
metadata:
  name: lab13
---
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

Commands used:

```powershell
kubectl apply -f .\k8s\argocd\namespaces.yaml
.\.tools\helm.exe repo add argo https://argoproj.github.io/argo-helm
.\.tools\helm.exe repo update
.\.tools\helm.exe install argocd argo/argo-cd --namespace argocd -f .\k8s\argocd\install-values.yaml
kubectl get pods -n argocd
kubectl port-forward svc/argocd-server -n argocd 18080:80
```

Verified after install:

- ArgoCD API responded on `http://127.0.0.1:18080/api/version`
- returned version: `v3.3.8`
- `argocd-server` was exposed as `ClusterIP`, which matches the local port-forward access model

## Applications

Three main Application manifests were applied:

- `application.yaml` -> manual sync app in namespace `lab13`
- `application-dev.yaml` -> auto-sync, prune, self-heal in namespace `dev`
- `application-prod.yaml` -> manual sync app in namespace `prod`

Commands used:

```powershell
kubectl apply -f .\k8s\argocd\application.yaml
kubectl apply -f .\k8s\argocd\application-dev.yaml
kubectl apply -f .\k8s\argocd\application-prod.yaml
```

CLI verification was done with ArgoCD core mode against the cluster kubeconfig:

```powershell
$env:KUBECONFIG = ".\k8s\lab13-kubeconfig"
argocd app list --core --kube-context kind-lab13
```

Final application status on the clean cluster:

```text
devops-info-service-dev          Synced  Healthy
devops-info-service-dev-appset   Synced  Healthy
devops-info-service-manual       Synced  Healthy
devops-info-service-prod         Synced  Healthy
devops-info-service-prod-appset  Synced  Healthy
```

Deployment state confirmed with `kubectl get deploy -A`:

- `devops-info-service-manual` -> `1/1` in `lab13`
- `devops-info-service-dev` -> `1/1` in `dev`
- `devops-info-service-prod` -> `3/3` in `prod`
- `devops-info-service-dev-appset` -> `1/1` in `dev-appset`
- `devops-info-service-prod-appset` -> `3/3` in `prod-appset`

## Environment Differences

Both environments deploy the same Helm chart, but with different values files.

### Dev

`values-dev.yaml`:

```yaml
replicaCount: 1

env:
  appEnv: development
  appRegion: lab13-dev
  logLevel: debug

config:
  responseMode: detailed

service:
  type: NodePort
  nodePort: 30080
```

Meaning:

- one replica
- `NodePort` access for easy local testing
- lighter resource requests and limits
- auto-sync with `prune: true` and `selfHeal: true`

### Prod

`values-prod.yaml`:

```yaml
replicaCount: 3
minReadySeconds: 10

env:
  appEnv: production
  appRegion: lab13-prod
  logLevel: info

config:
  responseMode: compact

persistence:
  enabled: false

service:
  type: ClusterIP
```

Meaning:

- three replicas
- `ClusterIP` service, which keeps the app healthy on local `kind`
- stronger CPU and memory limits than dev
- manual sync policy for controlled promotion
- persistence explicitly disabled so the chart remains valid with `replicaCount: 3`

## Self-Healing and Drift Verification

The required GitOps behavior was checked on the running cluster.

### 1. Replica Drift Self-Heal

Command used:

```powershell
kubectl scale deployment devops-info-service-dev -n dev --replicas=5
```

Observed result:

```text
before=2026-04-22T16:59:53.1277507+03:00 replicas=1
scaled=2026-04-22T16:59:53.4730229+03:00 replicas=5
healed=2026-04-22T17:00:03.9428900+03:00 replicas=1
```

Interpretation:

- the deployment was manually changed from `1` to `5` replicas
- ArgoCD detected the drift and restored the Git state
- recovery took about 10 seconds

### 2. Pod Deletion

Command used:

```powershell
kubectl delete pod -n dev -l app.kubernetes.io/instance=devops-info-service-dev
```

Observed result:

```text
deleted_at=2026-04-22T17:04:04.6746238+03:00 old_pod=devops-info-service-dev-555f9fdbd-vhlvf
replacement=devops-info-service-dev-555f9fdbd-ddbgz
```

Interpretation:

- Kubernetes recreated the pod through the Deployment/ReplicaSet controller
- the application stayed healthy after replacement

### 3. Config Drift Self-Heal

The ConfigMap was intentionally modified in-cluster by changing `APP_REGION` to `manual-drift`.

Observed result:

```text
drifted_at=2026-04-22T17:04:36.4473664+03:00 changed_value=manual-drift
config_healed=2026-04-22T17:04:46.9741848+03:00 restored_value=lab13-dev
```

Interpretation:

- ArgoCD detected the manual ConfigMap drift
- `APP_REGION` was restored to the value from Git
- after the heal cycle, the application returned to `Synced` and `Healthy`

## Bonus - ApplicationSet

`k8s/argocd/applicationset.yaml` was also verified.

The bonus ApplicationSet was intentionally isolated from the main lab applications so both approaches can coexist without name collisions:

- generated app names: `devops-info-service-dev-appset`, `devops-info-service-prod-appset`
- generated namespaces: `dev-appset`, `prod-appset`
- generated release names: `devops-info-service-dev-appset`, `devops-info-service-prod-appset`

This avoids conflicts with:

- `devops-info-service-dev`
- `devops-info-service-prod`

The dev ApplicationSet app uses automated sync and self-heal. The prod ApplicationSet app remains manual. Both were healthy on the final validation run.

## Screenshots

Captured from the live ArgoCD UI:

- [Applications overview](./screenshots/06-argocd-applications.png)
- [Dev application details](./screenshots/07-argocd-dev-details.png)
- [Prod application details](./screenshots/08-argocd-prod-details.png)

What the screenshots show:

- all applications are present in ArgoCD
- all applications are `Synced` and `Healthy`
- source repository is `https://github.com/Ravwvil/DevOps-Core-Course.git`
- target revision is branch `lab13`

## Conclusion

Lab 13 is completed and verified on a live cluster:

- ArgoCD was installed and accessed through the UI and CLI
- manual, dev, and prod applications were deployed from Git
- environment-specific Helm values were applied correctly
- self-healing was confirmed for replica drift and ConfigMap drift
- Kubernetes pod replacement behavior was confirmed
- ApplicationSet bonus was implemented without conflicting with the main solution
