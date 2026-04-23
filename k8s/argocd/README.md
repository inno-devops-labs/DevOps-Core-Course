# ArgoCD manifests

These manifests deploy `k8s/devops-info-chart` from the `lab12` branch.

- `application.yaml`: default manual-sync Application in the `default` namespace
- `application-dev.yaml`: dev Application with auto-sync, prune, and self-heal
- `application-prod.yaml`: prod Application with manual sync
- `applicationset.yaml`: bonus ApplicationSet that generates dev/prod Applications

Apply individual Applications:

```bash
kubectl apply -f k8s/argocd/application-dev.yaml
kubectl apply -f k8s/argocd/application-prod.yaml
```

Apply the bonus ApplicationSet instead:

```bash
kubectl apply -f k8s/argocd/applicationset.yaml
```
