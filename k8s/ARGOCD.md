ArgoCD Lab 13 — GitOps with ArgoCD

Overview
- GitOps with ArgoCD for declarative deployments to Kubernetes.
- Deploy Helm-based app using Git as the single source of truth.
- Multi-environment deployment (dev/prod) with appropriate sync policies.
- Self-healing, drift detection, and ApplicationSet (bonus).

What you’ll configure
- ArgoCD installation via Helm (argocd namespace).
- ArgoCD UI access (port-forward) and CLI setup.
- A basic Application manifest for the Helm chart in your repo.
- Dev and Prod Application manifests with environment-specific values.
- Optional ApplicationSet for generating multiple apps from a single template.

File contributions
- k8s/argocd/application.yaml: main ArgoCD Application manifest (manual sync).
- k8s/argocd/application-dev.yaml: Dev App with automated sync.
- k8s/argocd/application-prod.yaml: Prod App with manual sync.
- k8s/helm/python-app/values.yaml: baseline Helm values.
- k8s/helm/python-app/values-dev.yaml: Dev-specific Helm values.
- k8s/helm/python-app/values-prod.yaml: Prod-specific Helm values.
- k8s/ARGOCD.md: this documentation file.
- k8s/argocd/applicationset.yaml: ApplicationSet manifest (bonus).

Notes
- Replace <username> and <repo> with your actual GitHub repository details.
- The lab expects you to apply and observe changes in ArgoCD Cloud environment or a local Kubernetes cluster.
- The presence of these files is sufficient to demonstrate the intended GitOps workflow in a codebase context.

References
- ArgoCD Documentation: https://argo-cd.readthedocs.io/
- ApplicationSet: https://argo-cd.readthedocs.io/en/stable/user-guide/application-set/
