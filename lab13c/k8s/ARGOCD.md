# Lab 13: Argo CD

No ApplicationSet bonus in this repo.

Helm chart lives at `lab12c/k8s/devops-info` in [DevOps-CC](https://github.com/TsixPhoenix/DevOps-CC). Argo `Application` YAML is under `lab13c/k8s/argocd/`.

Applications use `targetRevision: lab12` because that branch already has the chart on GitHub. After you merge or push chart updates elsewhere, change `targetRevision` in all three manifests to match.

## Install (Helm)

```powershell
helm repo add argo https://argoproj.github.io/argo-helm
helm repo update
kubectl create namespace argocd
helm upgrade --install argocd argo/argo-cd -n argocd --version 7.7.16 `
  --set configs.params.server.insecure=true `
  --set server.extraArgs="{--insecure}" `
  --wait --timeout 10m
```

Check pods: `kubectl get pods -n argocd` (everything should be Running or Completed).

## UI

Insecure setup for kind only. Forward port 80 on the Service:

```powershell
kubectl port-forward svc/argocd-server -n argocd 8080:80
```

Browser: `http://localhost:8080`. User `admin`. Password:

```powershell
$pw = kubectl -n argocd get secret argocd-initial-admin-secret -o jsonpath="{.data.password}"
[Text.Encoding]::UTF8.GetString([Convert]::FromBase64String($pw))
```

## CLI (Windows)

Grab `argocd-windows-amd64.exe` from [releases](https://github.com/argoproj/argo-cd/releases). With another forward, e.g. `18080:80`:

```powershell
kubectl port-forward svc/argocd-server -n argocd 18080:80
argocd login localhost:18080 --username admin --password "<paste>" --plaintext
argocd app list --plaintext --server localhost:18080
```

## Application files

| File | Namespace | Values | Sync |
|------|-----------|--------|------|
| `application.yaml` | default | `values.yaml` | manual |
| `application-dev.yaml` | dev | `values-dev.yaml` | automated, prune, selfHeal |
| `application-prod.yaml` | prod | `values-prod.yaml` | manual |

```powershell
kubectl apply -f lab13c/k8s/argocd/application.yaml
kubectl apply -f lab13c/k8s/argocd/application-dev.yaml
kubectl apply -f lab13c/k8s/argocd/application-prod.yaml
```

Sync the two manual apps after CLI login:

```text
argocd app sync devops-info --plaintext --server localhost:18080
argocd app sync devops-info-prod --plaintext --server localhost:18080
```

`devops-info-dev` syncs on its own.

Image `tsixphoenix/devops-info-python:lab12` is often missing on Docker Hub. Build and load into kind:

```powershell
docker build -t tsixphoenix/devops-info-python:lab12 .\lab12c\app_python
kind load docker-image tsixphoenix/devops-info-python:lab12 --name lab11
```

## Environments

dev: one replica, smaller resources, NodePort 30081, `RELEASE_ID=dev`, auto-sync + selfHeal.

prod: one replica, PVC RWO, bigger limits, Service type LoadBalancer in values (on kind external IP stays pending; pod still runs), `RELEASE_ID=prod`, manual sync.

default (single app from `application.yaml`): `values.yaml`, NodePort 30080, manual sync.

Prod stays manual so someone clicks Sync after reviewing the diff.

## Self-heal and drift (dev)

Scaling `devops-info-dev` to 5 replicas was reverted back to 1 in about 20 seconds with selfHeal on.

Deleting a pod in dev gets you a new pod from the ReplicaSet. That is normal Kubernetes behavior, not Argo CD fixing Git drift.

Changing `values-dev.yaml` in Git (e.g. `replicaCount`), committing, and pushing to `lab12` makes the dev app go OutOfSync within a few minutes (default poll ~3 min), then it auto-syncs. Prod shows OutOfSync until you sync it manually.

Extra labels on the Deployment may stick until the next comparison; replica count is the clean demo. `argocd app diff devops-info-dev` shows drift.

Kubernetes keeps replica counts for a Deployment. Argo CD reapplies the full desired state from Git on sync/selfHeal. Poll interval is configurable; default is on the order of a few minutes.

## Run output (kind, Apr 2026)

Applications:

```text
NAME               SYNC STATUS   HEALTH STATUS
devops-info        Synced        Healthy
devops-info-dev    Synced        Healthy
devops-info-prod   Synced        Progressing
```

On kind, prod can sit at Progressing when the Service is LoadBalancer with no external IP; workloads were still Running.

dev:

```text
deployment.apps/devops-info-dev   1/1
service/devops-info-dev           NodePort   80:30081/TCP
```

prod:

```text
deployment.apps/devops-info-prod   1/1
service/devops-info-prod           LoadBalancer   80:32607/TCP   EXTERNAL-IP pending
```

default:

```text
deployment.apps/devops-info   1/1
service/devops-info           NodePort   80:30080/TCP
```

Scale test: `kubectl scale deployment devops-info-dev -n dev --replicas=5` then back to 1 replica.

## 8. UI screenshots

All screenshots in the folder docs/

---
