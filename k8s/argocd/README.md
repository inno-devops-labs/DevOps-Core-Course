# ArgoCD Manifests

Declarative definitions of ArgoCD resources used in Lab 13.

| File | Purpose |
|------|---------|
| `application.yaml` | Single `Application` targeting the `default` namespace (manual sync). Useful for the initial GitOps walkthrough. |
| `application-dev.yaml` | `Application` for the `dev` namespace with **auto-sync**, **self-heal** and **prune** enabled. |
| `application-prod.yaml` | `Application` for the `prod` namespace with **manual sync** (production best practice). |
| `applicationset.yaml` | Bonus — `ApplicationSet` using a `list` generator to produce both `devops-app-dev` and `devops-app-prod` from a single template (with a `templatePatch` toggling auto-sync per environment). |

All manifests point to the Helm chart at `k8s/devops-app` on the `lab13` branch of `egorTorshin/DevOps-Core-Course`.

## Apply order

```bash
# Option A — individual Applications
kubectl apply -f k8s/argocd/application-dev.yaml
kubectl apply -f k8s/argocd/application-prod.yaml

# Option B — ApplicationSet (replaces both Applications above)
kubectl apply -f k8s/argocd/applicationset.yaml
```

See `k8s/ARGOCD.md` for the full write-up, screenshots and self-healing evidence (all artifacts live in `k8s/argocd/evidence/`).
