# Lab 11 — Secrets and Vault

Required tasks only; bonus not done.

Chart: `lab11c/k8s/devops-info` (v0.2.0). Hooks from Lab 10 stay off in default `values.yaml` so this lab stays about secrets.

---

## 1) Kubernetes Secrets

**Create (imperative):**

```bash
kubectl create secret generic app-credentials \
  --from-literal=username=demo-user \
  --from-literal=password=demo-pass
```

**Inspect:**

```bash
kubectl get secret app-credentials -o yaml
```

You get `data.username` and `data.password` as base64 blobs. That is encoding for transport/storage in the API object, not encryption.

**Decode (PowerShell):**

```powershell
[Text.Encoding]::UTF8.GetString([Convert]::FromBase64String("<paste-value-here>"))
```

**Security:** Secrets are not encrypted at rest in etcd unless you configure [encryption at rest](https://kubernetes.io/docs/tasks/administer-cluster/encrypt-data/) (EncryptionConfiguration + KMS). RBAC still matters: anyone who can read the Secret object gets the values.

---

## 2) Helm-managed Secret

**Layout:**

- `templates/secrets.yaml` — Secret when `helmSecret.enabled`; name via helper `devops-info.helmSecretName`; `stringData` for `username` / `password` from values.
- `values.yaml` — `helmSecret.enabled` and placeholders `REPLACE_ME` (never commit real credentials).
- `templates/deployment.yaml` — `envFrom` + `secretRef` pointing at that Secret so all keys become env vars.

Install/upgrade with overrides (example):

```bash
helm upgrade --install app11 lab11c/k8s/devops-info \
  -f lab11c/k8s/devops-info/values-prod.yaml \
  --set helmSecret.username=helmuser \
  --set helmSecret.password='your-temp-password'
```

**Verification:**

- `kubectl describe pod <pod>` lists **only the Secret name** under “Environment Variables from”, not the cleartext values.
- `kubectl exec deploy/app11-devops-info -c app -- printenv` shows `username` and `password` in the container — fine for a lab; don’t paste that output into git or tickets.

**Note:** `helm get values` can show what you passed with `--set`; treat that as sensitive too.

---

## 3) Resource management

CPU/memory come from `values.yaml` and are overridden per env in `values-dev.yaml` / `values-prod.yaml`.

- **Requests** — what the scheduler uses for placement; kubelet guarantees at least this much.
- **Limits** — hard cap; container throttled (CPU) or OOM-killed (memory) if it goes over.

Pick requests from steady usage (metrics), limits a bit above peak. Dev: smaller; prod: higher replicas + larger limits (see prod values file).

---

## 4) Vault integration

**Install:** Official Helm repo was unreachable from this network (403), so Vault was installed from a local checkout of HashiCorp’s `vault-helm` chart (tag v0.29.1), namespace `vault`, dev server + injector:

```bash
helm install vault ./path-to-vault-helm-chart -n vault --create-namespace \
  --set server.dev.enabled=true \
  --set injector.enabled=true
```

**Cluster check:**

```text
kubectl get pods -n vault
# vault-0 and vault-agent-injector should be Running
```

**Inside Vault (dev pod, example flow):**

- KV v2 at path `secret/` (default mount name `secret`).
- Example secret: `secret/devops-info/config` with at least two keys (e.g. `username`, `password`, plus `api_key` for demo).
- `vault auth enable kubernetes`
- `vault write auth/kubernetes/config ...` (kubernetes host, CA, token reviewer — per tutorial).
- Policy `devops-info-read`:

```hcl
path "secret/data/devops-info/*" {
  capabilities = ["read"]
}
```

- Role `devops-info` bound to service account `app11-devops-info` in namespace `default`, policy `devops-info-read`.

**Injection:** With `vault.injector.enabled: true` (see `values-dev.yaml` / `values-prod.yaml`), the pod template gets annotations such as:

- `vault.hashicorp.com/agent-inject: "true"`
- `vault.hashicorp.com/role: "devops-info"`
- `vault.hashicorp.com/agent-inject-secret-vaultconfig: "secret/data/devops-info/config"`
- `vault.hashicorp.com/service: "http://vault.vault.svc:8200"`

Pod goes to **2/2** (app + `vault-agent`). Injected file path:

```text
/vault/secrets/vaultconfig
```

Content is KV data in a small text blob — don’t commit real contents; confirm with `ls` / `head` in the lab only.

**Pattern:** Mutating webhook adds the agent; agent authenticates to Vault using Kubernetes auth; it writes secrets into a shared volume the app reads as files.

---

## 5) Security analysis

| Topic | Native Secret | Vault |
|--------|----------------|--------|
| Storage | etcd (encode + optional encryption at rest) | Dedicated store, policies, audit |
| Rotation | Manual / external tooling | Built for rotation, dynamic secrets |
| Access | RBAC on Secret objects | Policies, namespaces, roles |
| Footprint | None extra | Agent sidecar or CSI / API |

**When to use what:** In-cluster Secret is fine for small teams and non-critical data if etcd encryption and RBAC are in good shape. Vault (or another external manager) pays off for many apps, strict audit, rotation, and when several clusters need the same source of truth.

**Production:** encrypt etcd; narrow RBAC; avoid `stringData` defaults with real passwords in git; prefer external secret sync or Vault Agent/CSI; dev mode Vault is **not** for production.
