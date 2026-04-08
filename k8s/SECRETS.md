# Lab 11 — Kubernetes Secrets & HashiCorp Vault

## Task 1 — Kubernetes Secrets Fundamentals

### Creating the Secret

```bash
kubectl create secret generic app-credentials --from-literal=username=admin --from-literal=password=supersecret123
```

Output:
```
secret/app-credentials created
```

### Viewing the Secret (YAML format)

```bash
kubectl get secret app-credentials -o yaml
```

```yaml
apiVersion: v1
data:
  password: c3VwZXJzZWNyZXQxMjM=
  username: YWRtaW4=
kind: Secret
metadata:
  creationTimestamp: "2026-04-08T17:26:21Z"
  name: app-credentials
  namespace: default
  resourceVersion: "21425"
  uid: ee44cde5-dccb-432d-bbe7-45de4996adbb
type: Opaque
```

### Decoding Base64 Values

```bash
kubectl get secret app-credentials -o jsonpath='{.data.username}' | base64 -d
# Output: admin

kubectl get secret app-credentials -o jsonpath='{.data.password}' | base64 -d
# Output: supersecret123
```

Both values are instantly recoverable — confirming that base64 is encoding, not encryption.

### Base64 Encoding vs Encryption

**Base64 encoding** is NOT encryption. It is a reversible encoding scheme — anyone
with access to the cluster can decode secret values instantly with `base64 -d`.
Kubernetes Secrets are base64-encoded purely for safe transport of binary data,
not for security purposes.

**Encryption** requires a secret key and a cryptographic algorithm (e.g. AES-256).
Without the key, the ciphertext cannot be read. Base64 has no key — anyone can
decode it with a single command.

### Are Kubernetes Secrets Encrypted at Rest by Default?

**No.** By default, Kubernetes Secrets are stored in etcd in plain base64-encoded
form. Anyone with direct etcd access can read all secret values without any key.

**etcd encryption at rest** can be enabled via the `EncryptionConfiguration` API
server flag. When enabled, secrets are encrypted before being written to etcd using
a provider such as `aescbc`, `aesgcm`, or a cloud KMS (e.g. AWS KMS, GCP KMS).

You should enable etcd encryption in production when:
- Running self-managed Kubernetes (not a managed cloud service)
- Compliance requirements mandate encryption at rest (PCI-DSS, HIPAA, SOC2)
- Storing highly sensitive credentials (API keys, DB passwords, TLS private keys)

Managed services (EKS, GKE, AKS) offer etcd encryption as a cluster option
that must be explicitly enabled.

---

## Task 2 — Helm-Managed Secrets

### Chart Structure with Secrets

```
k8s/python-app/
├── Chart.yaml
├── values.yaml                  ← secret placeholders added
├── values-dev.yaml
├── values-prod.yaml
└── templates/
    ├── _helpers.tpl
    ├── deployment.yaml          ← updated with envFrom + vault annotations
    ├── secrets.yaml             ← NEW: Secret template
    ├── service.yaml
    ├── NOTES.txt
    └── hooks/
        ├── pre-install-job.yaml
        └── post-install-job.yaml
```

### secrets.yaml Template

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: {{ include "python-app.fullname" . }}-secret
  labels:
    {{- include "python-app.labels" . | nindent 4 }}
type: Opaque
stringData:
  APP_USERNAME: {{ .Values.secret.username | quote }}
  APP_PASSWORD: {{ .Values.secret.password | quote }}
  APP_SECRET_KEY: {{ .Values.secret.secretKey | quote }}
```

`stringData` is used instead of `data` — Kubernetes automatically base64-encodes
the values, so plain text can be written directly in templates without manual encoding.

### Secrets in values.yaml (Placeholders Only)

```yaml
secret:
  username: "placeholder-user"
  password: "placeholder-password"
  secretKey: "placeholder-secret-key"
```

Real values are injected at deploy time via `--set`, never committed to Git:

```bash
helm upgrade --install myrelease k8s/python-app \
  --set secret.username="admin" \
  --set secret.password="supersecret123" \
  --set secret.secretKey="my-app-secret-key-abc123"
```

### Consuming Secrets in Deployment

The deployment uses `envFrom` with `secretRef` to inject all secret keys as
environment variables automatically:

```yaml
envFrom:
  - secretRef:
      name: {{ include "python-app.fullname" . }}-secret
```

### Environment Variable Verification

```bash
kubectl exec -it myrelease-python-app-8f899bb4f-djfbp -- env
```

```
APP_PASSWORD=supersecret123
APP_SECRET_KEY=my-app-secret-key-abc123
APP_USERNAME=admin
ENV=production
```

All three secret keys are available as environment variables inside the container ✅

### Secrets Not Visible in kubectl describe

```bash
kubectl describe pod myrelease-python-app-8f899bb4f-djfbp
```

Relevant section:
```
Environment Variables from:
  myrelease-python-app-secret  Secret  Optional: false
Environment:
  ENV:  production
```

Only the secret **name** is shown — the actual values are never exposed in
`kubectl describe`. This is the expected secure behavior.

### Resource Management

```yaml
resources:
  requests:
    cpu: "100m"
    memory: "128Mi"
  limits:
    cpu: "200m"
    memory: "256Mi"
```

**Requests vs Limits:**

- **Requests** — the minimum resources guaranteed to the container. The Kubernetes
  scheduler uses requests to decide which node can fit the pod. The container is
  always allocated at least this amount.
- **Limits** — the maximum resources the container is allowed to use. If a container
  exceeds its memory limit, it is OOMKilled and restarted. If it exceeds its CPU
  limit, it is throttled but not killed.

**Choosing appropriate values:**

1. Profile the app under realistic load using `kubectl top pod`
2. Set requests to the average observed usage
3. Set limits to ~2x the request value as safe headroom
4. For a lightweight Flask app at low traffic: `cpu: 100m/200m`, `memory: 128Mi/256Mi`
   is a reasonable baseline

---

## Task 3 — HashiCorp Vault Integration

### Vault Installation

```bash
helm repo add hashicorp https://helm.releases.hashicorp.com
helm repo update
helm install vault hashicorp/vault \
  --set "server.dev.enabled=true" \
  --set "injector.enabled=true"
```

### Vault Pods Running

```bash
kubectl get pods
```

```
NAME                                          READY   STATUS    RESTARTS       AGE
myrelease-python-app-654cd4958b-54sks         2/2     Running   0              60s
myrelease-python-app-654cd4958b-db29h         2/2     Running   0              52s
myrelease-python-app-654cd4958b-xnh6c         2/2     Running   0              70s
vault-0                                       1/1     Running   1 (10m ago)    94m
vault-agent-injector-848dd747d7-grfvg         1/1     Running   4 (10m ago)    94m
```

Both `vault-0` (Vault server) and `vault-agent-injector-*` (Mutating Webhook) are
Running ✅. Application pods show `2/2` — the Vault Agent sidecar was injected.

### KV Secrets Engine Configuration

```bash
# KV v2 is pre-enabled in dev mode at path secret/
vault kv put secret/myapp/config username="vault-admin" password="vault-secret-password" secret_key="vault-app-key-xyz789"
```

```
====== Secret Path ======
secret/data/myapp/config
======= Metadata =======
Key                Value
---                -----
created_time       2026-04-08T19:13:12.527052245Z
custom_metadata    <nil>
deletion_time      n/a
destroyed          false
version            1
```

```bash
vault kv get secret/myapp/config
```

```
====== Secret Path ======
secret/data/myapp/config
======= Metadata =======
Key                Value
---                -----
created_time       2026-04-08T19:13:12.527052245Z
custom_metadata    <nil>
deletion_time      n/a
destroyed          false
version            1
======= Data =======
Key           Value
---           -----
password      vault-secret-password
secret_key    vault-app-key-xyz789
username      vault-admin
```

### Kubernetes Authentication

```bash
vault auth enable kubernetes
# Success! Enabled kubernetes auth method at: kubernetes/

vault write auth/kubernetes/config kubernetes_host="https://$KUBERNETES_PORT_443_TCP_ADDR:443"
# Success! Data written to: auth/kubernetes/config
```

### Policy Configuration

```hcl
path "secret/data/myapp/config" {
  capabilities = ["read"]
}
```

```bash
vault policy write python-app-policy - <<EOF
path "secret/data/myapp/config" {
  capabilities = ["read"]
}
EOF
# Success! Uploaded policy: python-app-policy
```

```bash
vault policy read python-app-policy
```

```
path "secret/data/myapp/config" {
  capabilities = ["read"]
}
```

### Role Configuration

```bash
vault write auth/kubernetes/role/python-app-role \
  bound_service_account_names=default \
  bound_service_account_namespaces=default \
  policies=python-app-policy \
  ttl=24h
```

```bash
vault read auth/kubernetes/role/python-app-role
```

```
Key                                         Value
---                                         -----
alias_name_source                           serviceaccount_uid
bound_service_account_names                 [default]
bound_service_account_namespace_selector    n/a
bound_service_account_namespaces            [default]
policies                                    [python-app-policy]
token_bound_cidrs                           []
token_explicit_max_ttl                      0s
token_max_ttl                               0s
token_no_default_policy                     false
token_num_uses                              0
token_period                                0s
token_policies                              [python-app-policy]
token_ttl                                   24h
token_type                                  default
ttl                                         24h
```

### Vault Agent Injection — Annotations

The following annotations were added to the pod template in `deployment.yaml`:

```yaml
annotations:
  vault.hashicorp.com/agent-inject: "true"
  vault.hashicorp.com/role: "python-app-role"
  vault.hashicorp.com/agent-inject-secret-config: "secret/data/myapp/config"
```

### Proof of Secret Injection

```bash
kubectl exec -it myrelease-python-app-654cd4958b-54sks -c python-app -- cat /vault/secrets/config
```

```
data: map[password:vault-secret-password secret_key:vault-app-key-xyz789 username:vault-admin]
metadata: map[created_time:2026-04-08T19:13:12.527052245Z custom_metadata:<nil> deletion_time: destroyed:false version:1]
```

All three secrets from Vault (`username`, `password`, `secret_key`) are available
inside the pod at `/vault/secrets/config` ✅

### Sidecar Injection Pattern Explained

The **Vault Agent Injector** works as a Kubernetes Mutating Admission Webhook:

1. When a pod with `vault.hashicorp.com/agent-inject: "true"` is created, the
   webhook intercepts the pod creation request before it reaches the scheduler
2. It automatically adds a Vault Agent **init container** (fetches secrets before
   the app starts) and a Vault Agent **sidecar container** (keeps secrets refreshed)
3. The Vault Agent authenticates to Vault using the pod's Kubernetes Service Account JWT
4. Secrets are written to a shared in-memory volume at `/vault/secrets/`
5. The application reads secrets from files — they never appear in the pod spec,
   making them invisible to `kubectl describe`

This pattern requires **zero application code changes** to integrate with Vault.

---

## Security Analysis

### Kubernetes Secrets vs HashiCorp Vault

| Feature | Kubernetes Secrets | HashiCorp Vault |
|---|---|---|
| Storage | etcd (base64, not encrypted by default) | Encrypted storage backend |
| Access control | RBAC (coarse-grained) | Fine-grained policies per path |
| Audit logging | Kubernetes audit log | Built-in detailed audit log |
| Secret rotation | Manual | Automatic (dynamic secrets) |
| Dynamic secrets | No | Yes (DB credentials, PKI, etc.) |
| Complexity | Low | Medium-High |
| Best for | Non-sensitive config, TLS certs | Production credentials, compliance |

### When to Use Each Approach

**Use Kubernetes Secrets when:**
- The cluster has etcd encryption at rest enabled
- RBAC policies are strict and well-maintained
- Secrets are low-sensitivity (feature flags, non-critical config)
- Team is small and operational complexity must stay low

**Use HashiCorp Vault when:**
- Storing database credentials, API keys, or private keys
- Compliance requirements mandate audit trails (SOC2, PCI-DSS, HIPAA)
- Secret rotation must be automated
- Multiple services and teams need to share secrets safely
- Dynamic short-lived credentials are needed

### Production Recommendations

1. **Always enable etcd encryption at rest** if using native Kubernetes Secrets
2. **Never commit secret values to Git** — use placeholder defaults in `values.yaml`
   and inject real values via `--set` at deploy time
3. **Use RBAC** to restrict which service accounts can read which secrets
4. **Prefer Vault** for any credential that would cause a security incident if leaked
5. **Use Vault dynamic secrets** for database access — credentials are auto-generated
   and expire, so a leaked password becomes useless after TTL
6. **Enable Vault audit logging** to track every secret access for compliance