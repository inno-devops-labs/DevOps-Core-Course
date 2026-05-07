# Kubernetes Module

This directory contains the Kubernetes deliverables for the course application. It includes the raw Kubernetes manifests used in Lab 9, the Helm chart created in Lab 10, and the lab write-ups moved into `k8s/docs/` so the module root stays readable.

The main deployment assets are:

- `deployment.yml`: baseline Kubernetes `Deployment` manifest for the Python app.
- `service.yml`: baseline Kubernetes `Service` manifest exposing the app inside the cluster and via `NodePort`.
- `devops-app-py/`: Helm chart version of the application deployment.
- `ROLLOUTS.md`: compatibility entry point for the Lab 14 Argo Rollouts report.
- `STATEFULSET.md`: compatibility entry point for the Lab 15 StatefulSet report.
- `docs/`: lab documentation split by assignment.

## Documentation

- [Helm Notes](HELM.md)
- [Secrets Notes](SECRETS.md)
- [ConfigMap Notes](CONFIGMAPS.md)
- [ArgoCD Notes](ARGOCD.md)
- [Argo Rollouts Notes](ROLLOUTS.md)
- [StatefulSet Notes](STATEFULSET.md)
- [Lab 09 - Kubernetes Basics](docs/LAB09.md)
- [Lab 10 - Helm Package Manager](docs/LAB10.md)
- [Lab 11 - Kubernetes Secrets and Vault](docs/LAB11.md)
- [Lab 12 - ConfigMaps and Persistent Volumes](docs/LAB12.md)
- [Lab 13 - GitOps with ArgoCD](docs/LAB13.md)
- [Lab 14 - Progressive Delivery with Argo Rollouts](docs/LAB14.md)
- [Lab 15 - StatefulSets and Persistent Storage](docs/LAB15.md)
