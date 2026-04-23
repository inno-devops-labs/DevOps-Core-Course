# Lab 13: kind + Argo CD (copy-paste)

Repo root is `DevOps-CC`. Cluster name below is `lab11`; change `--name` if yours differs.

## Cluster and image

```powershell
kind create cluster --name lab11 --wait 5m
docker build -t tsixphoenix/devops-info-python:lab12 .\lab12c\app_python
kind load docker-image tsixphoenix/devops-info-python:lab12 --name lab11
```

## Argo CD

```powershell
helm repo add argo https://argoproj.github.io/argo-helm
helm repo update
kubectl create namespace argocd
helm upgrade --install argocd argo/argo-cd -n argocd --version 7.7.16 `
  --set configs.params.server.insecure=true `
  --set server.extraArgs="{--insecure}" `
  --wait --timeout 10m
```

## Applications

```powershell
kubectl apply -f .\lab13c\k8s\argocd\application.yaml
kubectl apply -f .\lab13c\k8s\argocd\application-dev.yaml
kubectl apply -f .\lab13c\k8s\argocd\application-prod.yaml
```

`devops-info-dev` syncs alone. For the other two use the UI Sync button or CLI.

## CLI sync for manual apps

```powershell
Invoke-WebRequest -Uri "https://github.com/argoproj/argo-cd/releases/download/v2.13.3/argocd-windows-amd64.exe" -OutFile "$env:TEMP\argocd.exe"
$pwB64 = kubectl -n argocd get secret argocd-initial-admin-secret -o jsonpath="{.data.password}"
$pw = [Text.Encoding]::UTF8.GetString([Convert]::FromBase64String($pwB64))
Start-Process kubectl -ArgumentList "port-forward","svc/argocd-server","-n","argocd","18080:80" -WindowStyle Hidden
Start-Sleep 5
& "$env:TEMP\argocd.exe" login localhost:18080 --username admin --password $pw --plaintext
& "$env:TEMP\argocd.exe" app sync devops-info --plaintext --server localhost:18080
& "$env:TEMP\argocd.exe" app sync devops-info-prod --plaintext --server localhost:18080
```

## Quick checks

```powershell
kubectl get applications -n argocd
kubectl get pods -n dev
kubectl get pods -n prod
kubectl get pods -n default
```

## Self-heal check (dev)

```powershell
kubectl scale deployment devops-info-dev -n dev --replicas=5
Start-Sleep 30
kubectl get deploy -n dev devops-info-dev
```

Expect 1 replica again.

## Tear down

```powershell
helm uninstall argocd -n argocd
kind delete cluster --name lab11
```
