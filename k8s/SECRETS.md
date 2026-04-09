### Creating the Secret

### Viewing the Secret

```bash
kubectl get secret app-credentials -o yaml
```

```yaml
apiVersion: v1
data:
  password: U3VwZXJTZWNyZXQxMjM=
  username: YWRtaW4=
kind: Secret
metadata:
  creationTimestamp: "2026-04-09T18:55:59Z"
  name: app-credentials
  namespace: default
  resourceVersion: "448"
  uid: 300e0fd1-0714-400e-8b38-c345a25127c3
type: Opaque
```

### Decoding Base64 Values

```bash
echo "YWRtaW4=" | base64 -d
echo "U3VwZXJTZWNyZXQxMjM=" | base64 -d
```

```
username: admin
password: SuperSecret123
```

### Base64 Encoding vs Encryption

|                        | Base64 Encoding                            | Encryption                                     |
|------------------------|--------------------------------------------|------------------------------------------------|
| **Purpose**            | Encoding binary-safe text for transport    | Protecting data confidentiality                |
| **Reversible**         | Yes - trivially, no key needed             | Only with the correct key                      |
| **Security**           | None - anyone with the value can decode it | Strong - computationally infeasible to reverse |
| **Kubernetes default** | Secrets are base64-encoded                 | NOT encrypted by default                       |

**Key takeaway:** Kubernetes Secrets are base64-encoded, not encrypted. 
Any user with `kubectl get secret` access can retrieve and decode secret values immediately.

### Security Implications

**Are Kubernetes Secrets encrypted at rest by default?**

No. By default, Secrets are stored unencrypted in etcd. 
Anyone with direct access to etcd or a cluster backup can read all secret values.

**etcd Encryption at Rest:**

etcd encryption should be enabled via an `EncryptionConfiguration` resource in the kube-apiserver manifest. Recommended providers:

1. `aescbc` - AES-CBC with PKCS#7 padding
2. `aesgcm` - AES-GCM
3. `secretbox` - XSalsa20 and Poly1305

**When to enable:** Always in production. 
At minimum, enable RBAC to restrict secret access and consider external secret managers.

---

### Chart Structure with Secrets

```
k8s/devops-info-service/
├── Chart.yaml
├── values.yaml                    # secret placeholders defined here
└── templates/
    ├── _helpers.tpl               # named template for env vars
    ├── deployment.yaml            # consumes secret via envFrom
    ├── secrets.yaml               # Secret resource template
    ├── serviceaccount.yaml        # ServiceAccount for Vault auth
    └── service.yaml
```

### `templates/secrets.yaml`

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: {{ include "devops-info-service.fullname" . }}-secret
  labels:
    {{- include "devops-info-service.labels" . | nindent 4 }}
type: Opaque
stringData:
  APP_USERNAME: {{ .Values.secret.appUsername | quote }}
  APP_PASSWORD: {{ .Values.secret.appPassword | quote }}
  DB_URL: {{ .Values.secret.dbUrl | quote }}
```

`stringData` is used so Helm accepts plain-text values - Kubernetes automatically base64-encodes them on storage.

### `values.yaml` - Secret Defaults (Placeholder Values)

```yaml
secret:
  appUsername: "placeholder-user"
  appPassword: "placeholder-password"
  dbUrl: "postgresql://placeholder-host:5432/appdb"
```

Real values are supplied at deploy time via `--set` flags and are never committed to Git.

### Consuming Secrets in Deployment (`envFrom`)

Pattern used: **all keys from secret** via `envFrom`:

```yaml
envFrom:
  - secretRef:
      name: {{ include "devops-info-service.fullname" . }}-secret
```

This injects `APP_USERNAME`, `APP_PASSWORD`, and `DB_URL` as environment variables in every container.

### Verification - Env Vars Present in Pod

```bash
kubectl exec <pod> -- env | grep -E "APP_USERNAME|APP_PASSWORD|DB_URL"
```

```
APP_USERNAME=admin
DB_URL=postgresql://db-host:5432/appdb
APP_PASSWORD=SecretPass123
```

### Secret Values NOT Visible in `kubectl describe pod`

```bash
kubectl describe pod <pod> | grep -E "APP_USERNAME|APP_PASSWORD|SecretPass"
# (no output - secrets are not exposed in describe)
```

### Resource Limits Configuration

```yaml
resources:
  requests:
    cpu: "100m"
    memory: "128Mi"
  limits:
    cpu: "200m"
    memory: "256Mi"
```

```yaml
resources:
  requests:
    cpu: {{ .Values.resources.requests.cpu | quote }}
    memory: {{ .Values.resources.requests.memory | quote }}
  limits:
    cpu: {{ .Values.resources.limits.cpu | quote }}
    memory: {{ .Values.resources.limits.memory | quote }}
```

### Requests vs Limits

|                   | Requests                                                 | Limits                                                     |
|-------------------|----------------------------------------------------------|------------------------------------------------------------|
| **Definition**    | Minimum guaranteed resources                             | Maximum allowed resources                                  |
| **Scheduler use** | Used to place the pod on a node with sufficient capacity | Not used for scheduling                                    |
| **Enforcement**   | Node allocates this amount                               | Kubernetes throttles CPU / OOM-kills for memory            |
| **Best practice** | Set conservatively based on observed baseline usage      | Set at 2–4× requests for CPU; equal to requests for memory |

### Choosing Appropriate Values

1. Start with no limits and observe with `kubectl top pods`
2. Set `requests` = average consumption observed
3. Set `limits` = peak + 20–30% headroom for CPU; for memory, match requests to avoid OOM kills
4. Use VPA (Vertical Pod Autoscaler) to automate recommendations in production

## Task 4 - HashiCorp Vault Integration

### Vault Installation via Helm

```bash
helm repo add hashicorp https://helm.releases.hashicorp.com
helm repo update

helm install vault hashicorp/vault \
  --set "server.dev.enabled=true" \
  --set "injector.enabled=true" \
  --namespace vault \
  --create-namespace
```

### Vault Pods Running

```
NAME                                   READY   STATUS    RESTARTS   AGE
vault-0                                1/1     Running   0          3m48s
vault-agent-injector-8c76487db-clkqw   1/1     Running   0          13m
```

### KV Secrets Engine Configuration

```bash
vault kv put secret/devops-info-service/config \
  username="vault-admin" \
  password="VaultSecret456" \
  db_url="postgresql://vault-db:5432/proddb"
```

Verification:
```
============= Secret Path =============
secret/data/devops-info-service/config

====== Data ======
Key         Value
---         -----
db_url      postgresql://vault-db:5432/proddb
password    VaultSecret456
username    vault-admin
```

### Kubernetes Authentication Configuration

```bash
vault auth enable kubernetes

vault write auth/kubernetes/config \
  kubernetes_host="https://$KUBERNETES_PORT_443_TCP_ADDR:443"
```

```
Key                  Value
---                  -----
kubernetes_host      https://10.96.0.1:443
disable_iss_validation  true
```

### Policy Creation

Policy `devops-info-service` grants read access to the application secret path:

```hcl
path "secret/data/devops-info-service/config" {
  capabilities = ["read"]
}
```

```bash
vault policy write devops-info-service /tmp/policy.hcl
# Success! Uploaded policy: devops-info-service
```

### Role Binding

```bash
vault write auth/kubernetes/role/devops-info-service \
  bound_service_account_names="devops-info-service-devops-info-service-sa" \
  bound_service_account_namespaces="default" \
  policies="devops-info-service" \
  ttl="24h"
```

Role details:
```
bound_service_account_names     [devops-info-service-devops-info-service-sa]
bound_service_account_namespaces  [default]
policies                        [devops-info-service]
token_ttl                       24h
```

### Vault Agent Injection Annotations

Added to the Deployment pod template via Helm values (`vault.enabled=true`):

```yaml
annotations:
  vault.hashicorp.com/agent-inject: "true"
  vault.hashicorp.com/role: "devops-info-service"
  vault.hashicorp.com/agent-inject-secret-config: "secret/data/devops-info-service/config"
  vault.hashicorp.com/agent-inject-template-config: |
    {{- with secret "secret/data/devops-info-service/config" -}}
    APP_USERNAME={{ .Data.data.username }}
    APP_PASSWORD={{ .Data.data.password }}
    DB_URL={{ .Data.data.db_url }}
    {{- end -}}
```

### Proof of Secret Injection - Sidecar Pattern

Pods with Vault injection run **2/2 containers**:
- `devops-info-service` - the application
- `vault-agent` - the Vault Agent sidecar

```
NAME                                                       READY   STATUS    RESTARTS
devops-info-service-devops-info-service-8487db89c8-d5tsr   2/2     Running   0
devops-info-service-devops-info-service-8487db89c8-nj8db   2/2     Running   0
```

Secret file present at `/vault/secrets/config`:

```bash
kubectl exec <pod> -c devops-info-service -- ls /vault/secrets/
# config

kubectl exec <pod> -c devops-info-service -- cat /vault/secrets/config
# APP_USERNAME=vault-admin
# APP_PASSWORD=VaultSecret456
# DB_URL=postgresql://vault-db:5432/proddb
```

### Sidecar Injection Pattern Explained

The Vault Agent Injector is a **mutating admission webhook**. When a pod with `vault.hashicorp.com/agent-inject: "true"` is created:

1. The webhook intercepts the pod creation request
2. It injects an **init container** (`vault-agent-init`) that authenticates to Vault using the pod's Kubernetes service account token
3. It injects a **sidecar container** (`vault-agent`) that renders secrets as files and keeps them updated
4. The application container reads secrets from the shared `/vault/secrets/` volume

Benefits over environment variables:
- Secrets can be **rotated** without restarting the pod
- Secret values never appear in environment variable dumps
- Access is controlled by Vault policies, not Kubernetes RBAC alone

### Template Annotation

```yaml
vault.hashicorp.com/agent-inject-template-config: |
  {{- with secret "secret/data/devops-info-service/config" -}}
  APP_USERNAME={{ .Data.data.username }}
  APP_PASSWORD={{ .Data.data.password }}
  DB_URL={{ .Data.data.db_url }}
  {{- end -}}
```

### Dynamic Secret Rotation

Vault Agent checks for secret changes at the configured `agent-cache-listener-require-request-header` interval. When a secret is updated in Vault:

1. Vault Agent detects the new version (KV v2 leases)
2. Re-renders the template file at `/vault/secrets/config`
3. If `vault.hashicorp.com/agent-inject-command` is set, the specified command is executed

```yaml
vault.hashicorp.com/agent-inject-command: "kill -HUP 1"
```

### Named Template in `_helpers.tpl` (DRY Principle)

Instead of duplicating environment variable definitions across multiple templates, a named template is defined in `_helpers.tpl`:

```yaml
{{/*
Common environment variables shared across containers.
*/}}
{{- define "devops-info-service.envVars" -}}
- name: APP_HOST
  value: {{ .Values.env.APP_HOST | quote }}
- name: APP_PORT
  value: {{ .Values.env.APP_PORT | quote }}
- name: LOG_FORMAT
  value: {{ .Values.env.LOG_FORMAT | quote }}
{{- end }}
```

```yaml
env:
  {{- include "devops-info-service.envVars" . | nindent 12 }}
```

**Benefits:** Single source of truth for env vars, any future changes need to be made in one place only.

---

## Security Analysis

### Kubernetes Secrets vs HashiCorp Vault

| Feature                  | Kubernetes Secrets                         | HashiCorp Vault                           |
|--------------------------|--------------------------------------------|-------------------------------------------|
| **Storage**              | etcd (base64, not encrypted by default)    | Encrypted storage backend                 |
| **Access control**       | Kubernetes RBAC                            | Vault policies (fine-grained, path-level) |
| **Secret rotation**      | Manual (requires pod restart for env vars) | Automatic via leases and agent templates  |
| **Audit logging**        | Limited (API server audit log)             | Full audit trail per secret read/write    |
| **Dynamic secrets**      | Not supported                              | Supported (DB creds, cloud IAM, PKI)      |
| **Namespacing**          | Kubernetes namespace                       | Vault namespaces + mounts                 |
| **Setup complexity**     | Low                                        | Medium-High                               |
| **Production readiness** | Acceptable with etcd encryption + RBAC     | Enterprise-grade                          |

### When to Use Each Approach

**Use Kubernetes Secrets when:**
- Small teams / simple applications
- Secrets rarely change
- etcd encryption is enabled
- RBAC is tightly configured
- External secret operators are used

**Use HashiCorp Vault when:**
- Multi-team environments needing fine-grained access control
- Dynamic secrets are required
- Compliance requires full audit logging
- Secret rotation without pod restarts is needed
- Running a large microservices platform

### Production Recommendations

1. **Always enable etcd encryption at rest** - even if using Vault, Kubernetes Secrets still live in etcd
2. **Use RBAC** - limit `get`/`list` on Secrets to only the service accounts that need them
3. **Never commit real secrets to Git** - use placeholder values in `values.yaml`, inject real values at deploy time
4. **Prefer Vault for new projects** - the sidecar injection pattern decouples secret management from application code
5. **Enable Vault audit logging** - route to SIEM for compliance
6. **Use KV v2** - versioned secrets allow rollback if a rotation goes wrong
7. **Set short TTLs** on Vault roles - reduces blast radius if a token is compromised
