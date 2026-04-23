# Lab 13 - GitOps with ArgoCD

Prepared on `2026-04-23`.

This lab integrates ArgoCD with the Kubernetes Helm chart already built in Labs 10-12. The Git repository becomes the source of truth, and ArgoCD continuously reconciles the cluster against the chart stored under `k8s/devops-info`.

## 1. Scope

Implemented repository artifacts:

- [`k8s/argocd/application.yaml`](/home/eugene/IU/DevOps/DevOps-Core-Course/k8s/argocd/application.yaml)
- [`k8s/argocd/application-dev.yaml`](/home/eugene/IU/DevOps/DevOps-Core-Course/k8s/argocd/application-dev.yaml)
- [`k8s/argocd/application-prod.yaml`](/home/eugene/IU/DevOps/DevOps-Core-Course/k8s/argocd/application-prod.yaml)
- [`k8s/argocd/applicationset.yaml`](/home/eugene/IU/DevOps/DevOps-Core-Course/k8s/argocd/applicationset.yaml)
- [`k8s/ARGOCD.md`](/home/eugene/IU/DevOps/DevOps-Core-Course/k8s/ARGOCD.md)

GitOps target:

- Repository: `https://github.com/ebortsov/DevOps-Core-Course.git`
- Branch: `lab13`
- Helm chart path: `k8s/devops-info`

The manifests are written for Kubernetes and deploy the existing FastAPI service with Helm value layering rather than raw YAML duplication.

## 2. ArgoCD Installation

Recommended install:

```bash
helm repo add argo https://argoproj.github.io/argo-helm
helm repo update
kubectl create namespace argocd
helm install argocd argo/argo-cd --namespace argocd --wait
```

Access:

```bash
kubectl port-forward svc/argocd-server -n argocd 8080:443
kubectl -n argocd get secret argocd-initial-admin-secret \
  -o jsonpath="{.data.password}" | base64 -d && echo
argocd login localhost:8080 --insecure
```

Why Helm here:

- ArgoCD itself is installed declaratively into Kubernetes
- upgrades and chart version pinning stay consistent with the rest of the course repo
- this keeps the GitOps controller lifecycle separate from the applications it manages

## 3. Application Design

### Baseline application

[`application.yaml`](/home/eugene/IU/DevOps/DevOps-Core-Course/k8s/argocd/application.yaml) deploys one manual-sync release:

- ArgoCD app name: `devops-info`
- Destination namespace: `devops-gitops`
- Helm release name: `devops-info`
- Values file: `values.yaml`

This is the simplest declarative ArgoCD setup and matches Task 2 of the lab.

### Multi-environment applications

Development:

- file: [`application-dev.yaml`](/home/eugene/IU/DevOps/DevOps-Core-Course/k8s/argocd/application-dev.yaml)
- namespace: `dev`
- values: `values.yaml` + `values-dev.yaml`
- sync: automatic
- safety options: `prune: true`, `selfHeal: true`

Production:

- file: [`application-prod.yaml`](/home/eugene/IU/DevOps/DevOps-Core-Course/k8s/argocd/application-prod.yaml)
- namespace: `prod`
- values: `values.yaml` + `values-prod.yaml`
- sync: manual

This maps directly onto the Helm chart already present in the repo:

- `values-dev.yaml` keeps a small `NodePort` deployment with one replica
- `values-prod.yaml` increases replicas and resource limits for a production-style release

Keeping production manual is intentional:

- chart changes can be reviewed before release
- sync timing remains explicit
- rollback coordination is simpler for a stateful or externally exposed workload

## 4. GitOps Workflow

Initial apply:

```bash
kubectl apply -f k8s/argocd/application.yaml
kubectl apply -f k8s/argocd/application-dev.yaml
kubectl apply -f k8s/argocd/application-prod.yaml
```

Manual sync examples:

```bash
argocd app sync devops-info
argocd app sync devops-info-prod
argocd app get devops-info-dev
argocd app get devops-info-prod
```

Expected GitOps flow:

1. Change a chart value in Git, for example `replicaCount` or `env.SERVICE_VERSION`.
2. Commit and push the change to branch `lab13`.
3. ArgoCD detects the repository drift.
4. `devops-info-dev` syncs automatically.
5. `devops-info-prod` stays `OutOfSync` until a manual sync is approved.

This preserves fast feedback in development while avoiding unattended production rollout.

## 5. Self-Healing

Two different repair mechanisms matter in Kubernetes here.

Kubernetes healing:

- if a pod is deleted, the Deployment and ReplicaSet recreate it
- ArgoCD is not involved unless the declarative spec itself changed

ArgoCD healing:

- if a managed resource is manually edited in the cluster, ArgoCD compares live state against Git
- `selfHeal: true` in the dev application restores the Git-defined version

Suggested verification commands:

```bash
kubectl scale deployment devops-info-dev -n dev --replicas=5
argocd app diff devops-info-dev

kubectl delete pod -n dev -l app.kubernetes.io/instance=devops-info-dev
kubectl get pods -n dev -w

kubectl label deployment devops-info-dev -n dev drift=manual --overwrite
argocd app diff devops-info-dev
```

Expected results:

- manual scaling is reverted by ArgoCD in `dev`
- deleted pods are recreated by Kubernetes
- manual labels or spec edits are removed by ArgoCD self-heal in `dev`

ArgoCD polls Git periodically, and webhook integration can reduce reaction time further.

## 6. Bonus - ApplicationSet

[`applicationset.yaml`](/home/eugene/IU/DevOps/DevOps-Core-Course/k8s/argocd/applicationset.yaml) replaces separate per-environment manifests with one generator-driven definition.

Design choices:

- `list` generator defines `dev` and `prod`
- `goTemplate` injects namespace, release name, and values file
- `templatePatch` enables auto-sync only for `dev`

Why this is useful:

- one source file describes multiple environments
- adding `stage` later becomes a small list update
- environment-specific duplication is reduced without changing the Helm chart

## 7. Validation Status

Completed locally:

- repository structure updated for ArgoCD
- application manifests written against the real Helm chart path
- documentation added in [`k8s/ARGOCD.md`](/home/eugene/IU/DevOps/DevOps-Core-Course/k8s/ARGOCD.md)

Validated locally with Helm rendering:

```bash
helm template devops-info-dev k8s/devops-info \
  -f k8s/devops-info/values.yaml \
  -f k8s/devops-info/values-dev.yaml >/dev/null

helm template devops-info-prod k8s/devops-info \
  -f k8s/devops-info/values.yaml \
  -f k8s/devops-info/values-prod.yaml >/dev/null
```

Not yet captured in this workspace:

- `kubectl` dry-run against ArgoCD CRDs on a live cluster
- live ArgoCD UI screenshots
- cluster-side sync output from a running Kubernetes environment

Those final screenshots and runtime checks should be collected after applying the manifests to a real cluster.
