# Lab 13 — GitOps with ArgoCD

## 1. ArgoCD Setup

### Installation

```bash
helm repo add argo https://argoproj.github.io/argo-helm
kubectl create namespace argocd
helm install argocd argo/argo-cd --namespace argocd
```

See pod list in [`argocd/evidence/01-setup-apps.txt`](./argocd/evidence/01-setup-apps.txt).

### UI access

```bash
kubectl port-forward svc/argocd-server -n argocd 8444:443
# Open https://localhost:8444  username: admin
kubectl -n argocd get secret argocd-initial-admin-secret \
  -o jsonpath="{.data.password}" | base64 -d
```

### CLI

```bash
brew install argocd
argocd login localhost:8444 --insecure --username admin --password <pass>
argocd app list
```

CLI version: **v3.3.9**

---

## 2. Application Configuration

All Application manifests live in [`k8s/argocd/`](./argocd/).

### `application.yaml` — default namespace, manual sync

```yaml
spec:
  source:
    repoURL: https://github.com/merkulovleo/DevOps-Core-Course.git
    targetRevision: lab13
    path: k8s/helm/devops-info
  destination:
    server: https://kubernetes.default.svc
    namespace: default
  syncPolicy:
    syncOptions:
      - CreateNamespace=true
```

### `application-dev.yaml` — dev namespace, auto-sync with selfHeal + prune

```yaml
  syncPolicy:
    automated:
      prune: true
      selfHeal: true
    syncOptions:
      - CreateNamespace=true
```

### `application-prod.yaml` — prod namespace, manual sync

No `automated` block → operator must run `argocd app sync devops-info-prod`
or click "Sync" in the UI.

Deploy and sync:

```bash
kubectl apply -f k8s/argocd/application-dev.yaml \
              -f k8s/argocd/application-prod.yaml
# prod manual sync:
argocd app sync devops-info-prod
```

---

## 3. Multi-Environment Deployment

| Setting | dev | prod |
|---------|-----|------|
| Replicas | 1 | 5 |
| Image tag | `latest` | `v1` |
| Service | NodePort | LoadBalancer |
| CPU limit | 100m | 500m |
| Memory limit | 128Mi | 512Mi |
| Sync policy | **Auto + selfHeal + prune** | **Manual** |
| Namespace | `dev` | `prod` |

**Why manual for prod?** Production deployments should go through a review/approval
step. Auto-sync on prod means any accidental commit (or unreviewed PR) immediately
reaches users. Manual sync forces a human to confirm each deployment.

---

## 4. Self-Healing Evidence

### Scale drift test

```bash
kubectl scale deployment/devops-info-dev -n dev --replicas=5
# devops-info-dev scaled
kubectl get deployment -n dev
# NAME              READY   DESIRED  ...
# devops-info-dev   5/5     5        ← manual drift
```

ArgoCD detected the diff (desired=1 in Git vs actual=5 in cluster) and
automatically reverted within ~15 s:

```
=== After ArgoCD self-heal (back to 1 replica) ===
NAME              READY   UP-TO-DATE   AVAILABLE
devops-info-dev   1/1     1            1
```

See [`argocd/evidence/02-self-heal.txt`](./argocd/evidence/02-self-heal.txt).

### Pod deletion test

Kubernetes — not ArgoCD — handles pod recreation. When a pod is deleted, the
ReplicaSet controller immediately spawns a replacement. ArgoCD only acts when
the *Deployment spec* drifts from Git (e.g., replica count, image, labels).

### Configuration drift test

If you manually add a label with `kubectl edit deployment ...`, ArgoCD's selfHeal
will detect the diff on the next reconciliation loop (default 3 min, or trigger
via Git webhook) and revert the label.

### Sync intervals

- **Polling:** ArgoCD reconciles every 3 minutes by default.
- **Webhook:** immediate sync on `git push` — set up via
  `argocd repo add --insecure-ignore-host-key` + GitHub webhook.
- **Manual:** `argocd app sync <name>`

---

## Bonus — ApplicationSet

```yaml
apiVersion: argoproj.io/v1alpha1
kind: ApplicationSet
metadata:
  name: devops-info-set
  namespace: argocd
spec:
  goTemplate: true
  generators:
    - list:
        elements:
          - env: dev
            namespace: dev
            valuesFile: values-dev.yaml
          - env: prod
            namespace: prod
            valuesFile: values-prod.yaml
  template:
    metadata:
      name: 'devops-info-{{ .env }}'
    spec:
      source:
        helm:
          valueFiles:
            - values.yaml
            - '{{ .valuesFile }}'
      destination:
        namespace: '{{ .namespace }}'
```

**Benefits vs individual Applications:**

| Aspect | Individual Applications | ApplicationSet |
|--------|------------------------|----------------|
| Adding a new env | Create new file + apply | Add element to list |
| Consistency | Can drift per file | Template guarantees uniformity |
| DRY | Source URL repeated | Defined once |
| Generators | N/A | List, Cluster, Git, Matrix, Merge |

See [`argocd/evidence/03-applicationset.txt`](./argocd/evidence/03-applicationset.txt).

**When to use which generator:**

- **List** — small fixed set of known environments (this lab)
- **Cluster** — multi-cluster fleet management
- **Git (directory)** — mono-repo with one app per directory, auto-discovery
- **Matrix** — cross-product of clusters × environments
