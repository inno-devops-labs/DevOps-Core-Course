# Local Kubernetes runbook (labs 11 & 12)

What you need: Docker, `kubectl`, `helm` 3+, `git`, and [kind](https://kind.sigs.k8s.io/docs/user/quick-start/). Paths below assume repo root `DevOps-CC` and PowerShell on Windows (adjust paths for bash).

## 1. Cluster

```powershell
kind create cluster --name lab11 --wait 5m
kubectl config use-context kind-lab11
```

## 2. Images

```powershell
docker pull tsixphoenix/devops-info-python:lab9
docker build -t tsixphoenix/devops-info-python:lab12 .\lab12c\app_python
kind load docker-image tsixphoenix/devops-info-python:lab9 --name lab11
kind load docker-image tsixphoenix/devops-info-python:lab12 --name lab11
```

Use `IfNotPresent` / registry pull in real use; for kind-only images add `--set image.pullPolicy=Never` on helm install.

## 3. Vault (lab 11) — install from Git if Helm repo fails

```powershell
git clone --depth 1 --branch v0.29.1 https://github.com/hashicorp/vault-helm.git .cache\vault-helm
helm upgrade --install vault .cache\vault-helm -n vault --create-namespace `
  --set server.dev.enabled=true --set injector.enabled=true --wait --timeout 5m
```

Configure (run in order; ignore “already enabled” errors where noted):

```powershell
kubectl exec -n vault vault-0 -- vault secrets enable -path=secret kv-v2
kubectl exec -n vault vault-0 -- vault kv put secret/devops-info/config username="vault-demo-user" password="vault-demo-password" api_key="vault-demo-api-key"
kubectl exec -n vault vault-0 -- sh -c "vault auth enable kubernetes 2>/dev/null; true"
kubectl exec -n vault vault-0 -- sh -c "vault write auth/kubernetes/config kubernetes_host=https://kubernetes.default.svc:443 kubernetes_ca_cert=@/var/run/secrets/kubernetes.io/serviceaccount/ca.crt token_reviewer_jwt=@/var/run/secrets/kubernetes.io/serviceaccount/token issuer=https://kubernetes.default.svc.cluster.local"
"path `"secret/data/devops-info/*`" { capabilities = [`"read`"] }" | kubectl exec -i -n vault vault-0 -- vault policy write devops-info-read -
kubectl exec -n vault vault-0 -- vault write auth/kubernetes/role/devops-info bound_service_account_names=app11-devops-info bound_service_account_namespaces=default policies=devops-info-read ttl=1h
```

## 4. Lab 11 app (Helm)

```powershell
helm upgrade --install app11 .\lab11c\k8s\devops-info -f .\lab11c\k8s\devops-info\values-dev.yaml --set image.pullPolicy=Never --wait --timeout 5m
```

Check: `kubectl get pods` — pod should be `2/2` if Vault injector is enabled in values.

## 5. Imperative Secret (task 1)

```powershell
kubectl create secret generic app-credentials --from-literal=username=demo-user --from-literal=password=demo-pass
kubectl get secret app-credentials -o yaml
```

## 6. Lab 12 app (Helm)

`values-dev.yaml` uses NodePort **30081** so it does not collide with lab 11 on **30080**.

```powershell
helm upgrade --install app12 .\lab12c\k8s\devops-info -f .\lab12c\k8s\devops-info\values-dev.yaml --set image.pullPolicy=Never --wait --timeout 5m
```

## 7. Quick checks

```powershell
kubectl get configmap,pvc
kubectl exec deploy/app12-devops-info -c app -- cat /config/config.json
kubectl exec deploy/app12-devops-info -c app -- printenv | findstr APP_
kubectl exec deploy/app11-devops-info -c app -- ls /vault/secrets
```

**Persistence:** bump counter with HTTP calls to `/`, read `/data/visits`, delete the app12 pod, wait for reschedule, read `/data/visits` again — value should match.

## 8. Tests (no cluster)

```powershell
cd lab12c\app_python
pip install -r requirements.txt pytest httpx
pytest -q
```

## 9. Cleanup

```powershell
helm uninstall app12 app11 -n default
helm uninstall vault -n vault
kind delete cluster --name lab11
```

The `.cache/` folder with `vault-helm` is gitignored; delete it if you want a clean tree.
