# Lab 11 — secrets & Vault

Chart is under `lab11c/k8s/devops-info` (v0.2.0). Lab 10 hooks stay off in the default `values.yaml` so they don’t get in the way.

## kubectl secret

Create:

```bash
kubectl create secret generic app-credentials \
  --from-literal=username=demo-user \
  --from-literal=password=demo-pass
```

Inspect:

```bash
kubectl get secret app-credentials -o yaml
```

The `data.*` fields are base64 — that’s encoding for the API, not encryption. Decode in PowerShell (username `demo-user` → `ZGVtby11c2Vy`):

```powershell
[Text.Encoding]::UTF8.GetString([Convert]::FromBase64String("ZGVtby11c2Vy"))
```

Without [etcd encryption at rest](https://kubernetes.io/docs/tasks/administer-cluster/encrypt-data/), secrets in etcd are only as safe as the cluster + RBAC. Anyone who can read the Secret object sees the values.

## Helm secret

The chart has `templates/secrets.yaml` (when `helmSecret.enabled` is true), values in `values.yaml`, and the deployment uses `envFrom` + `secretRef`. The defaults in the repo are dummy creds (`lab11-helm-demo-user` / `lab11-helm-demo-password`) — fine for classwork; use `--set` or something proper in real use.

Install:

```bash
helm upgrade --install app11 lab11c/k8s/devops-info \
  -f lab11c/k8s/devops-info/values-prod.yaml
```

Override without editing files:

```bash
helm upgrade --install app11 lab11c/k8s/devops-info \
  -f lab11c/k8s/devops-info/values-prod.yaml \
  --set helmSecret.username=myuser \
  --set helmSecret.password=mypass
```

`kubectl describe pod` only shows the Secret name under env-from, not the cleartext. Inside the container you’ll see them in `printenv` — ok for debugging, just don’t paste real passwords into the repo or chat. Same story if `helm get values` picked up `--set` args.

## Resources

CPU/memory live in `values.yaml`, with overrides in `values-dev.yaml` / `values-prod.yaml`. Requests = what scheduling assumes; limits = hard cap (CPU gets throttled, memory can OOM).

## Vault

The HashiCorp Helm repo returned 403 from my network, so I installed from source:

```bash
git clone --depth 1 --branch v0.29.1 https://github.com/hashicorp/vault-helm.git vault-helm
helm install vault ./vault-helm -n vault --create-namespace \
  --set server.dev.enabled=true \
  --set injector.enabled=true
```

Check:

```bash
kubectl get pods -n vault
```

Rest is inside `vault-0`. Enable KV v2 on `secret` if it isn’t there yet:

```bash
kubectl exec -n vault vault-0 -- vault secrets enable -path=secret kv-v2
```

(If it already exists you’ll get an error — ignore.)

Stuff I used for the app path:

```bash
kubectl exec -n vault vault-0 -- vault kv put secret/devops-info/config \
  username="vault-demo-user" \
  password="vault-demo-password" \
  api_key="vault-demo-api-key"
```

Wire up Kubernetes auth:

```bash
kubectl exec -n vault vault-0 -- sh -c 'vault auth enable kubernetes 2>/dev/null || true; vault write auth/kubernetes/config \
  kubernetes_host="https://kubernetes.default.svc:443" \
  kubernetes_ca_cert=@/var/run/secrets/kubernetes.io/serviceaccount/ca.crt \
  token_reviewer_jwt=@/var/run/secrets/kubernetes.io/serviceaccount/token \
  issuer="https://kubernetes.default.svc.cluster.local"'
```

Policy + role for release `app11` (ServiceAccount `app11-devops-info`):

```bash
kubectl exec -i -n vault vault-0 -- vault policy write devops-info-read - <<'EOF'
path "secret/data/devops-info/*" {
  capabilities = ["read"]
}
EOF

kubectl exec -n vault vault-0 -- vault write auth/kubernetes/role/devops-info \
  bound_service_account_names=app11-devops-info \
  bound_service_account_namespaces=default \
  policies=devops-info-read \
  ttl=1h
```

Turn on the injector in `values-dev.yaml` / `values-prod.yaml` and you get the usual annotations (`vault.hashicorp.com/agent-inject`, `role`, `agent-inject-secret-vaultconfig`, service URL). Pod goes to 2/2 with the agent sidecar. Injected file landed at `/vault/secrets/vaultconfig` for me — I only checked with `ls`/`cat`, didn’t commit contents.

Rough idea: mutating webhook adds the agent, it logs into Vault with Kubernetes auth, writes files into the volume.

## Takeaway

Built-in Secrets are the easy path; etcd encryption + RBAC still matter, rotation is on you. Vault adds policy/audit/rotation story but it’s another moving part. Dev-mode Vault from the lab is not production material.

---

## Evidence (captured on kind v1.31, 2026-04-11)

**Imperative Secret (YAML fragment):**

```yaml
data:
  password: ZGVtby1wYXNz
  username: ZGVtby11c2Vy
kind: Secret
metadata:
  name: app-credentials
  namespace: default
type: Opaque
```

**Vault pods:**

```text
NAME                                    READY   STATUS    RESTARTS   AGE
vault-0                                 1/1     Running   0          ...
vault-agent-injector-75f9d67594-xxxxx   1/1     Running   0          ...
```

**Helm release pod (injector on):** `app11-devops-info-...` shows `2/2` — app container + `vault-agent`. `kubectl describe pod` lists `Environment Variables from: app11-devops-info-secret` (values only in the container env, not in describe).

**Env check (demo strings from chart values + Vault file):** variables `username` and `password` present; injected file at `/vault/secrets/vaultconfig` starts with KV-style text (contains `username`, `password`, `api_key` from Vault path `secret/data/devops-info/config`).

**Policy:**

```text
path "secret/data/devops-info/*" { capabilities = ["read"] }
```

Full local runbook: see `RUNBOOK.md` in this folder.
