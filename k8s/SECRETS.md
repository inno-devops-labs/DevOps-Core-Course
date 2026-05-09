# Lab 11 — Kubernetes Secrets & HashiCorp Vault

This document describes secret management for the `devops-python` Helm chart (`k8s/devops-python/`) and how to run the lab tasks locally.

---

## 1. Kubernetes Secrets (Task 1)

### Create a Secret imperatively

```bash
kubectl create secret generic app-credentials \
  --from-literal=username=demo-user \
  --from-literal=password=demo-pass \
  --dry-run=client -o yaml | kubectl apply -f -
```

### View and decode

```bash
kubectl get secret app-credentials -o yaml
# Copy the base64 value and decode:
echo "<base64-string>" | base64 -d
```

### Encoding vs encryption

- **Base64** in Secret objects is **encoding**, not encryption. Anyone with RBAC permission to read `Secret` resources can decode values.
- **Encryption at rest** for etcd is a **cluster-level** feature (see [Encrypting Secret Data at Rest](https://kubernetes.io/docs/tasks/administer-cluster/encrypt-data/)). It is **not** enabled by default on all clusters; check your cluster docs.

**Production:** restrict Secret access with RBAC, enable etcd encryption, use an external secret manager (Vault, cloud SM) for sensitive material.

---

## 2. Helm-managed Secrets (Task 2)

### Chart additions

| File | Purpose |
|------|---------|
| `templates/secrets.yaml` | `Secret` with `stringData` from `.Values.secrets.stringData` |
| `templates/serviceaccount.yaml` | ServiceAccount for Vault Kubernetes auth |
| `templates/rollout.yaml` or `templates/statefulset.yaml` | `envFrom.secretRef` when secrets enabled; Vault pod annotations when enabled (workload toggled by `.Values.workload.kind`) |
| `templates/_helpers.tpl` | `devops-python.secretName`, `devops-python.serviceAccountName`, `devops-python.envVars` (DRY) |

### Default values (placeholders only — do not commit real passwords)

See `values.yaml`:

- `secrets.enabled`, `secrets.create`, `secrets.stringData`
- Use `secrets.existingSecretName` to reference a pre-created Secret instead of chart-managed one.

### Install without committing real secrets

```bash
helm upgrade --install devops ./k8s/devops-python \
  --set secrets.stringData.username=prod-user \
  --set secrets.stringData.password=prod-pass
```

### Verify injection (keys become env vars: `USERNAME`, `PASSWORD`)

```bash
POD=$(kubectl get pods -l app.kubernetes.io/instance=devops -o jsonpath='{.items[0].metadata.name}')
kubectl exec -it "$POD" -- env | grep -E '^(USERNAME|PASSWORD)=' 
```

`kubectl describe pod` does **not** print secret values (only references).

### Resource limits

CPU/memory requests and limits remain in `values.yaml` under `resources` (same as Lab 10).

---

## 3. HashiCorp Vault (Task 3)

### Install Vault (dev mode — learning only)

```bash
helm repo add hashicorp https://helm.releases.hashicorp.com
helm repo update
helm install vault hashicorp/vault \
  --namespace vault --create-namespace \
  --set server.dev.enabled=true \
  --set injector.enabled=true
kubectl get pods -n vault
```

### Configure Vault (run inside `vault-0`)

Exec and use the Vault CLI (dev mode is auto-unsealed):

```bash
kubectl exec -n vault vault-0 -- vault secrets enable -path=secret kv-v2
kubectl exec -n vault vault-0 -- vault kv put secret/myapp/config username="vault-user" password="vault-pass"
```

### Kubernetes auth

Point Vault at your cluster (paths vary; see [Kubernetes auth](https://developer.hashicorp.com/vault/docs/auth/kubernetes)):

```bash
kubectl exec -n vault vault-0 -- vault auth enable kubernetes
kubectl exec -n vault vault-0 -- sh -c 'vault write auth/kubernetes/config \
  kubernetes_host="https://$KUBERNETES_PORT_443_TCP_ADDR:443" \
  kubernetes_ca_cert=@/var/run/secrets/kubernetes.io/serviceaccount/ca.crt \
  token_reviewer_jwt=@/var/run/secrets/kubernetes.io/serviceaccount/token'
```

Create a policy (read KV path) and a role bound to your app’s ServiceAccount:

```bash
kubectl exec -n vault vault-0 -- sh -c 'vault policy write devops-python - <<EOF
path "secret/data/myapp/*" {
  capabilities = ["read"]
}
EOF'
```

Bind the role to the ServiceAccount your Helm release creates (default namespace example):

```bash
RELEASE=devops
NS=default
SA_NAME=$(kubectl get sa -n "$NS" -l "app.kubernetes.io/instance=${RELEASE}" -o jsonpath='{.items[0].metadata.name}')
kubectl exec -n vault vault-0 -- vault write auth/kubernetes/role/devops-python \
  bound_service_account_names="$SA_NAME" \
  bound_service_account_namespaces="$NS" \
  policies=devops-python \
  ttl=1h
```

If the lookup returns empty, list ServiceAccounts and set `SA_NAME` manually:

```bash
kubectl get sa -n default
```

### Enable injection on the chart

In `values.yaml` set:

```yaml
vault:
  injector:
    enabled: true
```

Redeploy. The injector adds a sidecar; secrets appear under `/vault/secrets/` (default filename `config` for `agent-inject-secret-config`).

Verify:

```bash
kubectl exec -it <pod> -- cat /vault/secrets/config
```

---

## 4. Security Analysis

| Approach | Pros | Cons |
|----------|------|------|
| **Kubernetes Secrets** | Simple, native, works offline | Base64 only by default; etcd encryption is cluster config; RBAC critical |
| **Vault** | Centralized secrets, policies, rotation, audit | Operational complexity; needs HA for prod |

**When to use which:** use K8s Secrets for low-sensitivity bootstrap; use Vault (or cloud SM) for credentials, keys, and rotation in production.

---

## 5. Bonus — Vault Agent template file

When `vault.injector.templateEnabled: true`, the chart uses **`files/vault-agent-inject.tpl`** (raw Vault template syntax, not Helm-processed) with `agent-inject-template-config` instead of `agent-inject-secret-config`.

**Named template (Helm):** `devops-python.envVars` in `_helpers.tpl` keeps non-secret env DRY.

**Vault Agent refresh:** the sidecar renews leases and re-renders files on secret changes; see [Agent annotations](https://developer.hashicorp.com/vault/docs/platform/k8s/injector/annotations).

---

## Validation

```bash
helm lint k8s/devops-python
helm template test k8s/devops-python | grep -E 'Secret|envFrom|vault.hashicorp.com' -A2
```
