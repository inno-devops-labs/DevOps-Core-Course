# Lab 13 - GitOps with ArgoCD

Run date: April 15, 2026

Resource-saving note:
I did not start a Kubernetes cluster or ArgoCD server for this run. Instead, I implemented the full GitOps manifest set, validated it against the upstream ArgoCD Helm chart and the local Helm application chart, and documented the exact commands for live execution. UI screenshots were therefore not captured in this session.

## Files Added

- `k8s/argocd/install-values.yaml`
- `k8s/argocd/namespaces.yaml`
- `k8s/argocd/application.yaml`
- `k8s/argocd/application-dev.yaml`
- `k8s/argocd/application-prod.yaml`
- `k8s/argocd/applicationset.yaml`
- `k8s/ARGOCD.md`

## Validation Summary

Repository and chart validation used for this lab:

```text
.\.tools\helm.exe repo add argo https://argoproj.github.io/argo-helm
.\.tools\helm.exe repo update
.\.tools\helm.exe show chart argo/argo-cd
version: 9.5.0
appVersion: v3.3.6
```

All ArgoCD manifests parse as valid YAML:

```text
k8s\argocd\application-dev.yaml: 1 document(s) parsed
k8s\argocd\application-prod.yaml: 1 document(s) parsed
k8s\argocd\application.yaml: 1 document(s) parsed
k8s\argocd\applicationset.yaml: 1 document(s) parsed
k8s\argocd\install-values.yaml: 1 document(s) parsed
k8s\argocd\namespaces.yaml: 4 document(s) parsed
```

ArgoCD installation values were validated with:

```text
.\.tools\helm.exe template argocd argo/argo-cd --namespace argocd -f .\k8s\argocd\install-values.yaml
```

Verified rendered excerpts:

```yaml
data:
  timeout.reconciliation: 120s
  timeout.reconciliation.jitter: 60s
---
data:
  server.insecure: "true"
---
spec:
  type: ClusterIP
```

Interpretation:

- the ArgoCD server stays `ClusterIP`, which fits the port-forward access model
- `server.insecure: "true"` allows simple local UI/CLI access over the forwarded endpoint
- reconciliation defaults to `120s` with `60s` jitter, so Git polling is effectively about 2-3 minutes unless a manual sync or webhook is used

## ArgoCD Setup

Prepared installation values in `k8s/argocd/install-values.yaml`:

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

Why this configuration:

- `ClusterIP` keeps the install simple and works with `kubectl port-forward`
- `server.insecure: true` avoids local TLS friction during lab login
- `redis-ha.enabled: false` keeps the lab footprint smaller

Prepared namespace bootstrap manifest:

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

Live install commands to run later:

```powershell
kubectl apply -f .\k8s\argocd\namespaces.yaml
.\.tools\helm.exe repo add argo https://argoproj.github.io/argo-helm
.\.tools\helm.exe repo update
.\.tools\helm.exe install argocd argo/argo-cd --namespace argocd -f .\k8s\argocd\install-values.yaml
kubectl get pods -n argocd
kubectl port-forward svc/argocd-server -n argocd 8080:80
kubectl -n argocd get secret argocd-initial-admin-secret -o jsonpath="{.data.password}"
```

UI and CLI access flow prepared for the live run:

```powershell
# decode password in PowerShell
[System.Text.Encoding]::UTF8.GetString([System.Convert]::FromBase64String((kubectl -n argocd get secret argocd-initial-admin-secret -o jsonpath="{.data.password}")))

# browser
http://127.0.0.1:8080

# CLI login once argocd CLI is installed
argocd login 127.0.0.1:8080 --insecure
argocd app list
```

## Application Configuration

### Single Manual Application

`k8s/argocd/application.yaml` creates a manual-sync ArgoCD Application for the Helm chart:

```yaml
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: devops-info-service-manual
  namespace: argocd
spec:
  project: default
  source:
    repoURL: https://github.com/Ravwvil/DevOps-Core-Course.git
    targetRevision: lab13
    path: k8s/devops-info-service
    helm:
      releaseName: devops-info-service-manual
      values: |
        service:
          type: ClusterIP
        env:
          appEnv: gitops
          appRegion: lab13-manual
  destination:
    server: https://kubernetes.default.svc
    namespace: lab13
  syncPolicy:
    syncOptions:
      - CreateNamespace=true
```

Why the base app uses `ClusterIP`:

- the chart defaults to `NodePort` in the base values
- the dev environment also uses `NodePort 30080`
- keeping the manual demonstration app on `ClusterIP` avoids a cluster-wide NodePort collision

### Multi-Environment Applications

Dev application with auto-sync and self-heal:

```yaml
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: devops-info-service-dev
  namespace: argocd
spec:
  source:
    repoURL: https://github.com/Ravwvil/DevOps-Core-Course.git
    targetRevision: lab13
    path: k8s/devops-info-service
    helm:
      releaseName: devops-info-service-dev
      valueFiles:
        - values-dev.yaml
  destination:
    namespace: dev
    server: https://kubernetes.default.svc
  syncPolicy:
    automated:
      prune: true
      selfHeal: true
    syncOptions:
      - CreateNamespace=true
```

Prod application with manual sync:

```yaml
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: devops-info-service-prod
  namespace: argocd
spec:
  source:
    repoURL: https://github.com/Ravwvil/DevOps-Core-Course.git
    targetRevision: lab13
    path: k8s/devops-info-service
    helm:
      releaseName: devops-info-service-prod
      valueFiles:
        - values-prod.yaml
  destination:
    namespace: prod
    server: https://kubernetes.default.svc
  syncPolicy:
    syncOptions:
      - CreateNamespace=true
```

Apply sequence for a real cluster:

```powershell
kubectl apply -f .\k8s\argocd\application.yaml
kubectl apply -f .\k8s\argocd\application-dev.yaml
kubectl apply -f .\k8s\argocd\application-prod.yaml
argocd app list
argocd app sync devops-info-service-manual
argocd app get devops-info-service-dev
argocd app get devops-info-service-prod
```

## Multi-Environment Differences

The two ArgoCD Applications point at the same Helm chart but different value files.

Validated `values-dev.yaml` render excerpt:

```yaml
APP_ENV: "development"
type: NodePort
nodePort: 30080
claimName: devops-info-service-dev-data
```

Validated `values-prod.yaml` render excerpt:

```yaml
APP_ENV: "production"
storage: 250Mi
type: LoadBalancer
claimName: devops-info-service-prod-data
```

Operational meaning:

- dev is lighter and auto-synced for fast feedback
- prod is heavier, gets larger persistent storage, and remains manual for change control
- separate namespaces keep resource names and PVCs isolated

Why prod remains manual:

- production changes should still be reviewed and intentionally promoted
- rollout timing may need coordination with maintenance windows or business events
- self-heal in dev is ideal for experimentation; prod should not surprise operators

## Self-Healing and Drift Tests

These commands were prepared but not executed in this session because ArgoCD was not started locally.

### 1. Self-Healing by Scaling Drift

```powershell
kubectl scale deployment devops-info-service-dev -n dev --replicas=5
argocd app get devops-info-service-dev
kubectl get deployment devops-info-service-dev -n dev -w
```

Expected result:

- ArgoCD marks the app `OutOfSync`
- because `selfHeal: true`, it reapplies the Git state
- the deployment returns to the replica count defined by `values-dev.yaml`

### 2. Pod Deletion

```powershell
kubectl delete pod -n dev -l app.kubernetes.io/instance=devops-info-service-dev
kubectl get pods -n dev -w
```

Expected result:

- Kubernetes recreates the missing pod through the Deployment/ReplicaSet controller
- this is Kubernetes self-healing, not ArgoCD self-healing
- ArgoCD is about desired configuration drift, not single pod lifecycle replacement

### 3. Configuration Drift

```powershell
kubectl label deployment devops-info-service-dev -n dev drift-test=manual --overwrite
argocd app diff devops-info-service-dev
argocd app get devops-info-service-dev
```

Expected result:

- ArgoCD detects the label change as drift from Git
- diff view shows the extra label
- auto-sync with self-heal removes the manual label

### 4. GitOps Change Detection

Example workflow:

```powershell
git checkout lab13
# edit values-dev.yaml, for example replicaCount or logLevel
git commit -am "Adjust dev values for ArgoCD sync test"
git push -u origin lab13
argocd app get devops-info-service-dev
```

Expected result:

- ArgoCD notices the new Git revision during the next reconciliation cycle, about 2-3 minutes by the rendered defaults
- dev auto-syncs automatically
- prod shows `OutOfSync` and waits for manual approval

## Bonus - ApplicationSet

I also added `k8s/argocd/applicationset.yaml` so dev and prod can be generated from a single manifest.

Implementation summary:

```yaml
apiVersion: argoproj.io/v1alpha1
kind: ApplicationSet
metadata:
  name: devops-info-service-environments
spec:
  goTemplate: true
  generators:
    - list:
        elements:
          - env: dev
            namespace: dev
            releaseName: devops-info-service-dev
            valuesFile: values-dev.yaml
            autoSync: "true"
          - env: prod
            namespace: prod
            releaseName: devops-info-service-prod
            valuesFile: values-prod.yaml
            autoSync: "false"
  templatePatch: |
    {{- if eq .autoSync "true" }}
    spec:
      syncPolicy:
        automated:
          prune: true
          selfHeal: true
        syncOptions:
          - CreateNamespace=true
    {{- end }}
```

Benefits of ApplicationSet here:

- one source of truth for environment generation
- less copy-paste than separate Application manifests
- easy scaling when more environments appear later

When to prefer it:

- multiple environments in one repo
- many similar applications following the same pattern
- multi-cluster or multi-tenant GitOps setups

When individual Applications are still better:

- only one or two apps
- heavy per-environment differences
- you want the most explicit, easiest-to-read manifests possible

## Screenshots

Screenshots were not collected in this run because ArgoCD UI was not started. For a full live submission, capture:

- ArgoCD UI showing `devops-info-service-dev` and `devops-info-service-prod`
- sync status and health columns
- application details page showing source repo, branch `lab13`, chart path, and target namespace
- diff or history view after a manual config drift test

## Command Reference

Useful commands for the live cluster run:

```powershell
kubectl apply -f .\k8s\argocd\namespaces.yaml
.\.tools\helm.exe install argocd argo/argo-cd --namespace argocd -f .\k8s\argocd\install-values.yaml
kubectl apply -f .\k8s\argocd\application.yaml
kubectl apply -f .\k8s\argocd\application-dev.yaml
kubectl apply -f .\k8s\argocd\application-prod.yaml
argocd app list
argocd app sync devops-info-service-manual
argocd app get devops-info-service-dev
argocd app diff devops-info-service-dev
argocd app get devops-info-service-prod
```
