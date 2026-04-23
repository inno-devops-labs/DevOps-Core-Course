# Lab 13 — Evidence Log

Prepared on `2026-04-23`.

Keep this file as the single submission artifact for terminal evidence and screenshots.

## 1) Lab and git context

```bash
$ git branch --show-current
[PASTE: branch]
```

```bash
$ git rev-parse --short HEAD
[PASTE: commit]
```

## 2) ArgoCD installation

```bash
$ helm repo add argo https://argoproj.github.io/argo-helm
[PASTE: output]
```

```bash
$ helm repo update
[PASTE: output]
```

```bash
$ kubectl create namespace argocd
[PASTE: output]
```

```bash
$ helm install argocd argo/argo-cd --namespace argocd --wait
[PASTE: output]
```

```bash
$ kubectl get crd | grep argoproj
[PASTE: output]
```

```bash
$ kubectl get deploy,sts,svc,pods -n argocd
[PASTE: output]
```

## 3) Local manifest checks (no cluster required)

```bash
$ helm lint k8s/devops-info
[PASTE: output]
```

```bash
$ helm template devops-info k8s/devops-info -f k8s/devops-info/values.yaml >/dev/null
$ helm template devops-info-dev k8s/devops-info -f k8s/devops-info/values.yaml -f k8s/devops-info/values-dev.yaml >/dev/null
$ helm template devops-info-prod k8s/devops-info -f k8s/devops-info/values.yaml -f k8s/devops-info/values-prod.yaml >/dev/null
[PASTE: output]
```

## 4) Apply application manifests

```bash
$ kubectl apply -f k8s/argocd/application.yaml
[PASTE: output]
```

```bash
$ kubectl apply -f k8s/argocd/application-dev.yaml
[PASTE: output]
```

```bash
$ kubectl apply -f k8s/argocd/application-prod.yaml
[PASTE: output]
```

```bash
$ kubectl apply -f k8s/argocd/applicationset.yaml
[PASTE: output]
```

```bash
$ kubectl get applications,applicationsets -A -o wide
[PASTE: output]
```

## 5) GitOps workflow checks (as in lab13.md)

```bash
$ argocd app sync devops-info
[PASTE: output]
```

```bash
$ argocd app sync devops-info-prod
[PASTE: output]
```

```bash
$ argocd app get devops-info-dev
[PASTE: output]
```

```bash
$ argocd app get devops-info-prod
[PASTE: output]
```

## 6) Self-healing checks

```bash
$ kubectl scale deployment devops-info-dev -n dev --replicas=5
[PASTE: output]
```

```bash
$ argocd app diff devops-info-dev
[PASTE: output]
```

```bash
$ kubectl delete pod -n dev -l app.kubernetes.io/instance=devops-info-dev
[PASTE: output]
```

```bash
$ kubectl get pods -n dev -w
[PASTE: output]
```

```bash
$ kubectl label deployment devops-info-dev -n dev drift=manual --overwrite
[PASTE: output]
```

```bash
$ argocd app diff devops-info-dev
[PASTE: output]
```

## 7) Screenshots to attach (single bundle)

- `lab13-apps-list.png` — applications list includes `devops-info`, `devops-info-dev`, `devops-info-prod`
- `lab13-dev-auto-sync.png` — `devops-info-dev` auto-sync + selfHeal settings visible
- `lab13-prod-manual-sync.png` — `devops-info-prod` manual sync flow
- `lab13-prod-after-sync.png` — `devops-info-prod` synced and healthy
- `lab13-self-heal.png` — evidence of manual drift and reconciliation on `devops-info-dev`

## 8) Final checklist

- [x] application manifests created and documented
- [x] baseline + dev + prod applications defined
- [x] ApplicationSet for dev/prod defined
- [x] values layering in chart verified via `helm template`
- [ ] all command blocks replaced with real outputs
- [ ] screenshots attached
