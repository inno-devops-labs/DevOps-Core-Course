# Lab 13 — GitOps with ArgoCD

## Scope

This lab integrates ArgoCD with the Helm chart from `k8s/devops-info` so that Kubernetes state is reconciled from Git.

Implemented artifacts:

- `k8s/argocd/application.yaml`
- `k8s/argocd/application-dev.yaml`
- `k8s/argocd/application-prod.yaml`
- `k8s/argocd/applicationset.yaml`
- `k8s/ARGOCD.md`

GitOps source configured in all manifests:

- Repository: `https://github.com/ebortsov/DevOps-Core-Course.git`
- Target revision: `lab13`
- Path: `k8s/devops-info`

## ArgoCD Application Design

- Baseline app `devops-info`
  - Namespace: `devops-gitops`
  - Helm release: `devops-info`
  - Values: `values.yaml`
  - Sync: manual

- Development app `devops-info-dev`
  - Namespace: `dev`
  - Helm release: `devops-info-dev`
  - Values: `values.yaml` + `values-dev.yaml`
  - Sync: automatic + prune + selfHeal

- Production app `devops-info-prod`
  - Namespace: `prod`
  - Helm release: `devops-info-prod`
  - Values: `values.yaml` + `values-prod.yaml`
  - Sync: manual

### ApplicationSet

`k8s/argocd/applicationset.yaml` generates the dev/prod applications from a `list` generator and switches on `autoSync` per environment.

## Environment Strategy

This lab uses environment-specific values to keep a single chart:

- `k8s/devops-info/values-dev.yaml` enables small footprint `NodePort` and debug-friendly app behavior.
- `k8s/devops-info/values-prod.yaml` enables production-like high availability and resources with `LoadBalancer`.
- Base `k8s/devops-info/values.yaml` provides common defaults.

## Submission Notes

Use [`docs/LAB13-EVIDENCE.md`](/home/eugene/IU/DevOps/DevOps-Core-Course/docs/LAB13-EVIDENCE.md) as the single evidence file for:

- command outputs
- sync status snippets
- ArgoCD screenshots

Because no commands were run in this pass, [`docs/LAB13-EVIDENCE.md`](/home/eugene/IU/DevOps/DevOps-Core-Course/docs/LAB13-EVIDENCE.md) is prepared as a capture template:
- keep command blocks unchanged,
- paste actual output from your live cluster run into each block,
- add real screenshots in section 6.
