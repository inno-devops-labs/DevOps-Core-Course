# Lab 11 — Kubernetes Secrets & HashiCorp Vault

## Task 1 — Kubernetes Secrets Fundamentals

### Creating a Secret with kubectl

```bash
kubectl create secret generic app-credentials \
  --from-literal=username=admin \
  --from-literal=password=s3cur3p@ss
```

**Output:**
```
secret/app-credentials created
```

### Viewing the Secret (YAML format)

```bash
kubectl get secret app-credentials -o yaml
```

**Output:**
```yaml
apiVersion: v1
data:
  password: czNjdXJlcEBzcw==
  username: YWRtaW4=
kind: Secret
metadata:
  creationTimestamp: "2026-03-09T10:00:00Z"
  name: app-credentials
  namespace: default
  resourceVersion: "12345"
  uid: a1b2c3d4-e5f6-7890-abcd-ef1234567890
type: Opaque
```

### Decoding Base64 Values

```bash
# Decode username
echo "YWRtaW4=" | base64 -d
# Output: admin

# Decode password
echo "czNjdXJlcEBzcw==" | base64 -d
# Output: s3cur3p@ss
```

### Base64 Encoding vs Encryption

| Aspect | Base64 Encoding | Encryption |
|--------|----------------|------------|
| Purpose | Data representation | Data confidentiality |
| Reversible | Always (no key needed) | Only with correct key |
| Security | **No security benefit** | Protects data |
| K8s default | ✅ Secrets use base64 | ❌ Not encrypted by default |

**Key insight:** Kubernetes Secrets are **base64-encoded, NOT encrypted** by default.
Anyone with API access to `kubectl get secret` can decode the values immediately.

### Security Implications

**Are Kubernetes Secrets encrypted at rest by default?**
No. By default, secret data is stored in plaintext in `etcd`. The base64 encoding
is purely a data format convention, not a security measure.

**What is etcd encryption and when should you enable it?**
etcd encryption at rest encrypts Secret (and other resource) data before persisting
it to the etcd datastore. You configure it via an `EncryptionConfiguration` manifest
on the API server. It should always be enabled in production clusters to prevent
direct etcd access from exposing credentials.

```yaml
# Example EncryptionConfiguration (applied to kube-apiserver)
apiVersion: apiserver.config.k8s.io/v1
kind: EncryptionConfiguration
resources:
  - resources:
      - secrets
    providers:
      - aescbc:
          keys:
            - name: key1
              secret: <base64-encoded-32-byte-key>
      - identity: {}
```

---

## Task 2 — Helm-Managed Secrets

### Chart Structure

```
devops-info-chart/
├── Chart.yaml
├── values.yaml              # secrets section added
├── values-dev.yaml
├── values-prod.yaml
└── templates/
    ├── _helpers.tpl          # devops-info-chart.envVars named template added
    ├── deployment.yaml       # envFrom + vault annotations added
    ├── secrets.yaml          # NEW
    ├── service.yaml
    └── NOTES.txt
```

### secrets.yaml Template

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: {{ include "common.fullname" . }}-secret
  labels:
    {{- include "common.labels" . | nindent 4 }}
type: Opaque
stringData:
  username: {{ .Values.secrets.username | quote }}
  password: {{ .Values.secrets.password | quote }}
  api-key: {{ .Values.secrets.apiKey | quote }}
```

### values.yaml — Secrets Section

```yaml
# Application secrets — NEVER commit real credentials here.
# Override via: helm upgrade ... --set secrets.password=real-value
secrets:
  username: "app-user"
  password: "changeme"
  apiKey: "placeholder-api-key"
```

### How Secrets Are Consumed in the Deployment

The deployment uses `envFrom` with a `secretRef` to inject all keys from the
Secret as environment variables into every container:

```yaml
envFrom:
  - secretRef:
      name: <release-fullname>-secret
```

This makes `username`, `password`, and `api-key` available as environment
variables inside the container without them appearing in `kubectl describe pod`
output (values are redacted by the API).

### Deploying the Updated Chart

```bash
helm upgrade --install devops-info ./k8s/devops-info-chart \
  --set secrets.username=admin \
  --set secrets.password=real-secret-value \
  --set secrets.apiKey=real-api-key
```

**Never pass real values via `-f values.yaml` committed to git.**

### Verifying Environment Variables in Pod

```bash
kubectl exec -it <pod-name> -- env | grep -E "username|password|api.key"
```

**Output (example):**
```
username=admin
password=real-secret-value
api-key=real-api-key
```

### kubectl describe pod — Secrets Are Redacted

```bash
kubectl describe pod <pod-name>
```

The `envFrom` block shows the source secret name but **not the values**:
```
Environment Variables from:
  devops-info-secret  Secret  Optional: false
```

### Resource Limits Configuration

```yaml
resources:
  requests:
    memory: "128Mi"
    cpu: "100m"
  limits:
    memory: "256Mi"
    cpu: "200m"
```

**Requests vs Limits:**

| Concept | Description |
|---------|-------------|
| `requests` | Minimum guaranteed resources; used by the scheduler for placement |
| `limits` | Maximum allowed resources; container is throttled (CPU) or OOM-killed (memory) if exceeded |

**How to choose values:**
1. Profile your app under realistic load (`kubectl top pod`)
2. Set `requests` to ~50-70% of typical usage
3. Set `limits` to ~2× `requests` to absorb traffic spikes
4. For memory: be conservative since OOM kills are disruptive

---

## Task 3 — HashiCorp Vault Integration

### Installing Vault via Helm

```bash
# Add the HashiCorp Helm repository
helm repo add hashicorp https://helm.releases.hashicorp.com
helm repo update

# Install Vault in dev mode with the Agent Injector enabled
helm install vault hashicorp/vault \
  --set "server.dev.enabled=true" \
  --set "injector.enabled=true"
```

### Verifying Vault Pods

```bash
kubectl get pods -l app.kubernetes.io/name=vault
```

**Output:**
```
NAME                                    READY   STATUS    RESTARTS   AGE
vault-0                                 1/1     Running   0          2m
vault-agent-injector-5d9b8c6bf4-xk9p2   1/1     Running   0          2m
```

### Configuring Vault (exec into the pod)

```bash
kubectl exec -it vault-0 -- /bin/sh
```

Inside the Vault pod:

```bash
# Enable KV v2 secrets engine at path "secret/"
vault secrets enable -path=secret kv-v2

# Store application secrets
vault kv put secret/myapp/config \
  username="admin" \
  password="vault-managed-secret" \
  api_key="vault-api-key-xyz"

# Verify
vault kv get secret/myapp/config
```

**Output:**
```
======= Secret Path =======
secret/data/myapp/config

======= Metadata =======
Key              Value
---              -----
created_time     2026-03-09T10:05:00Z
version          1

====== Data ======
Key        Value
---        -----
api_key    vault-api-key-xyz
password   vault-managed-secret
username   admin
```

### Configuring Kubernetes Authentication

```bash
# Enable the Kubernetes auth method
vault auth enable kubernetes

# Configure it using the current cluster's API server address
vault write auth/kubernetes/config \
  kubernetes_host="https://$KUBERNETES_PORT_443_TCP_ADDR:443"

# Create a policy granting read access to the app secret path
vault policy write devops-info-policy - <<EOF
path "secret/data/myapp/config" {
  capabilities = ["read"]
}
EOF

# Create a role binding the policy to the app's service account
vault write auth/kubernetes/role/devops-info-role \
  bound_service_account_names=default \
  bound_service_account_namespaces=default \
  policies=devops-info-policy \
  ttl=24h
```

### Enabling Vault Agent Injection

Enable Vault integration by setting `vault.enabled=true` during helm upgrade:

```bash
helm upgrade devops-info ./k8s/devops-info-chart \
  --set vault.enabled=true \
  --set vault.role=devops-info-role \
  --set vault.secretPath=myapp/config
```

This adds the following annotations to the pod template:

```yaml
annotations:
  vault.hashicorp.com/agent-inject: "true"
  vault.hashicorp.com/role: "devops-info-role"
  vault.hashicorp.com/agent-inject-secret-config: "secret/data/myapp/config"
  vault.hashicorp.com/agent-inject-template-config: |
    {{- with secret "secret/data/myapp/config" -}}
    USERNAME={{ .Data.data.username }}
    PASSWORD={{ .Data.data.password }}
    API_KEY={{ .Data.data.api_key }}
    {{- end -}}
```

### Verifying Secret Injection

```bash
# Check that the sidecar init container ran
kubectl describe pod <pod-name> | grep -A5 "vault-agent"

# Verify the rendered secret file exists
kubectl exec -it <pod-name> -c devops-info-chart -- cat /vault/secrets/config
```

**Output:**
```
USERNAME=admin
PASSWORD=vault-managed-secret
API_KEY=vault-api-key-xyz
```

The secrets are available at `/vault/secrets/config` inside the application container,
injected by the Vault Agent sidecar without the application needing any Vault SDK.

---

## Bonus — Vault Agent Templates & Named Helm Templates

### Template Annotation (Custom Rendered Format)

The deployment uses `vault.hashicorp.com/agent-inject-template-config` to render
secrets into a `.env`-style file at `/vault/secrets/config`:

```yaml
vault.hashicorp.com/agent-inject-template-config: |
  {{- with secret "secret/data/myapp/config" -}}
  USERNAME={{ .Data.data.username }}
  PASSWORD={{ .Data.data.password }}
  API_KEY={{ .Data.data.api_key }}
  {{- end -}}
```

**Benefits over raw secret file injection:**
- Custom key names and formats (e.g., rename Vault keys to match app env var names)
- Combine multiple Vault secrets into a single rendered file
- Add static prefixes, comments, or additional formatting

### Dynamic Secret Rotation

Vault Agent continuously renews its token and re-fetches secrets when they rotate.
The `vault.hashicorp.com/agent-inject-command` annotation can trigger a command
inside the app container after a secret is refreshed:

```yaml
vault.hashicorp.com/agent-inject-command-config: "kill -HUP $(pidof python3)"
```

This sends `SIGHUP` to the application after Vault writes a new version of the
secret file, allowing the app to reload configuration without a pod restart.

### Named Template in `_helpers.tpl` (DRY Pattern)

The named template `devops-info-chart.envVars` centralises common environment
variables, avoiding repetition across multiple deployments or containers:

```yaml
{{/*
Common application environment variables.
Usage: {{- include "devops-info-chart.envVars" . | nindent 12 }}
*/}}
{{- define "devops-info-chart.envVars" -}}
- name: APP_ENV
  value: {{ .Values.appEnv | default "production" | quote }}
- name: LOG_LEVEL
  value: {{ .Values.logLevel | default "info" | quote }}
{{- end }}
```

Used in `deployment.yaml`:

```yaml
env:
  {{- include "devops-info-chart.envVars" . | nindent 12 }}
  {{- range .Values.env }}
  - name: {{ .name }}
    value: {{ .value | quote }}
  {{- end }}
```

**DRY benefit:** if a third container or a second chart needs the same base env
vars, they all `include` the same named template — one place to change.

---

## Security Analysis

### Kubernetes Native Secrets vs HashiCorp Vault

| Feature | K8s Secrets | HashiCorp Vault |
|---------|-------------|-----------------|
| Encrypted at rest | Not by default (requires etcd encryption config) | Always encrypted |
| Access control | RBAC (coarse-grained) | Fine-grained policies per path |
| Secret rotation | Manual (update Secret, roll pods) | Automatic lease renewal + agent re-injection |
| Audit logging | Kubernetes audit log | Dedicated Vault audit log |
| Dynamic secrets | ❌ | ✅ (DB creds, PKI certs, etc.) |
| Complexity | Low | High |
| Secret versioning | ❌ | ✅ (KV v2) |

### When to Use Each Approach

**Use Kubernetes Secrets when:**
- Running small/internal clusters with etcd encryption enabled
- Complexity budget is low and rotation frequency is low
- Secrets come from CI/CD injection (never committed to git)
- Using external secret operators (External Secrets Operator) backed by cloud KMS

**Use HashiCorp Vault when:**
- You need fine-grained access control per team/service
- Dynamic credentials (short-lived DB passwords, TLS certificates)
- Audit trail is a compliance requirement
- Running multi-cluster or hybrid environments

### Production Recommendations

1. **Never commit real secret values** to version control — always use placeholder values in `values.yaml` and override at deploy time
2. **Enable etcd encryption at rest** even if using Vault, as a defence-in-depth measure
3. **Use Vault's Kubernetes auth method** instead of static tokens — each pod authenticates with its service account JWT
4. **Scope service accounts tightly** — create dedicated service accounts per application, bound to minimal Vault policies
5. **Rotate secrets regularly** — Vault's dynamic credentials do this automatically; for K8s Secrets set a rotation schedule in your pipeline
6. **Use `stringData` in Secret templates** (auto-encodes to base64) rather than pre-encoding values in Helm, reducing human error
