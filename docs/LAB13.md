# Lab 13 - GitOps with ArgoCD

Prepared on `2026-04-23`.

## Scope

This lab integrates ArgoCD with the Helm chart already stored in this repository under `k8s/devops-info`.

Implemented repository artifacts:

- [`k8s/argocd/application.yaml`](/home/eugene/IU/DevOps/DevOps-Core-Course/k8s/argocd/application.yaml)
- [`k8s/argocd/application-dev.yaml`](/home/eugene/IU/DevOps/DevOps-Core-Course/k8s/argocd/application-dev.yaml)
- [`k8s/argocd/application-prod.yaml`](/home/eugene/IU/DevOps/DevOps-Core-Course/k8s/argocd/application-prod.yaml)
- [`k8s/argocd/applicationset.yaml`](/home/eugene/IU/DevOps/DevOps-Core-Course/k8s/argocd/applicationset.yaml)

GitOps source configured in the manifests:

- Repository: `https://github.com/ebortsov/DevOps-Core-Course.git`
- Branch: `lab13`
- Helm chart path: `k8s/devops-info`

## Application Design

### Baseline ArgoCD application

[`application.yaml`](/home/eugene/IU/DevOps/DevOps-Core-Course/k8s/argocd/application.yaml) defines a single ArgoCD `Application`:

- app name: `devops-info`
- namespace: `argocd`
- destination namespace: `devops-gitops`
- release name: `devops-info`
- values: `values.yaml`
- sync mode: manual

### Environment-specific applications

Development application:

- file: [`application-dev.yaml`](/home/eugene/IU/DevOps/DevOps-Core-Course/k8s/argocd/application-dev.yaml)
- destination namespace: `dev`
- release name: `devops-info-dev`
- values: `values.yaml` + `values-dev.yaml`
- sync mode: automated with `prune: true` and `selfHeal: true`

Production application:

- file: [`application-prod.yaml`](/home/eugene/IU/DevOps/DevOps-Core-Course/k8s/argocd/application-prod.yaml)
- destination namespace: `prod`
- release name: `devops-info-prod`
- values: `values.yaml` + `values-prod.yaml`
- sync mode: manual

Implemented value layering:

- `values.yaml`: common settings, base image, probes, ConfigMap mount, PVC mount
- `values-dev.yaml`: `NodePort`, one replica, lower resources, debug-oriented configuration
- `values-prod.yaml`: `LoadBalancer`, four replicas, higher resources, production-oriented configuration

### ApplicationSet

[`applicationset.yaml`](/home/eugene/IU/DevOps/DevOps-Core-Course/k8s/argocd/applicationset.yaml) provides a generator-based alternative:

- uses a `list` generator for `dev` and `prod`
- uses `goTemplate` to inject namespace, release name, and values file
- enables automated sync only for `dev`

This reduces duplication while preserving different rollout policies for development and production.

## Validation

### Verified locally

The following checks can be verified directly from this workspace:

- Helm chart linting
- Helm template rendering for base, dev, and prod configurations
- manifest structure review for ArgoCD `Application` and `ApplicationSet` resources

Run:

```bash
./k8s/argocd/collect-local-evidence.sh
```

This generates markdown with real local command output that can be attached as evidence for static validation.

### Requires live cluster evidence

The following items still require execution on a real Kubernetes cluster with ArgoCD installed:

- ArgoCD installation output
- `kubectl apply` output for the ArgoCD manifests
- `kubectl get applications,applicationsets -A`
- ArgoCD UI screenshots
- sync status and self-healing demonstrations

Use [`docs/LAB13-EVIDENCE.md`](/home/eugene/IU/DevOps/DevOps-Core-Course/docs/LAB13-EVIDENCE.md) as the capture sheet for those final items.

## GitOps Workflow Summary

Expected workflow after ArgoCD is installed:

1. Commit and push a chart change to branch `lab13`.
2. ArgoCD detects drift between Git and cluster state.
3. `devops-info-dev` auto-syncs because automated sync is enabled.
4. `devops-info-prod` remains pending manual sync.
5. Manual cluster-side edits in `dev` are reverted by ArgoCD self-healing.

## Notes

This report describes repository implementation and the validation approach. It does not claim that cluster-side checks were completed unless the corresponding outputs and screenshots are attached separately.
