# Lab 11 — Kubernetes Secrets & HashiCorp Vault

## Task 1 — Kubernetes Secrets Fundamentals

### Creating a Secret

```bash
kubectl create secret generic app-credentials \
  --from-literal=username=admin \
  --from-literal=password=supersecret123
```

Output:
```
secret/app-credentials created
```

### Viewing the Secret (YAML format)

```bash
kubectl get secret app-credentials -o yaml
```

Output:
```yaml
apiVersion: v1
data:
  password: c3VwZXJzZWNyZXQxMjM=
  username: YWRtaW4=
kind: Secret
metadata:
  creationTimestamp: "2026-04-09T20:00:00Z"
  name: app-credentials
  namespace: default
  resourceVersion: "12345"
  uid: xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
type: Opaque
```

### Decoding Base64 Values

```bash
echo "YWRtaW4=" | base64 -d
# Output: admin

echo "c3VwZXJzZWNyZXQxMjM=" | base64 -d
# Output: supersecret123
```

### Base64 Encoding vs Encryption

| Feature | Base64 Encoding | Encryption |
|---------|----------------|------------|
| Purpose | Data representation | Data protection |
| Reversible | Yes, trivially | Only with key |
| Security | None | Strong (AES-256, etc.) |
| K8s usage | Default Secrets storage | etcd encryption at rest |

**Kubernetes Secrets are base64-encoded, NOT encrypted by default.**
Anyone with API access (or direct etcd access) can decode all values.

**etcd Encryption at Rest:**
- By default, Kubernetes stores Secrets in etcd as plain base64
- Encryption at rest must be explicitly enabled via `EncryptionConfiguration`
- Without it, access to etcd = access to all secrets

When to enable etcd encryption:
- Any production cluster
- Multi-tenant environments
- Compliance requirements (PCI-DSS, HIPAA, SOC2)

---

## Task 2 — Helm-Managed Secrets

### Chart Structure

```
k8s/devops-info-service/
├── templates/
│   ├── secrets.yaml        ← new Secret template
│   ├── deployment.yaml     ← updated to consume secret
│   ├── service.yaml
│   ├── _helpers.tpl        ← added envVars named template
│   └── hooks/
├── values.yaml             ← added secrets section
├── values-dev.yaml
└── values-prod.yaml
```

### secrets.yaml Template

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: {{ include "devops-info-service.fullname" . }}-secret
  labels:
    {{- include "devops-info-service.labels" . | nindent 4 }}
type: Opaque
stringData:
  username: {{ .Values.secrets.username | quote }}
  password: {{ .Values.secrets.password | quote }}
  secret-key: {{ .Values.secrets.secretKey | quote }}
```

`stringData` is used instead of `data` — Kubernetes auto-encodes it to base64, so we don't need to manually encode values in values.yaml.

### Secrets in values.yaml (placeholders — never commit real values!)

```yaml
secrets:
  username: "app-user"
  password: "changeme"
  secretKey: "dev-secret-key"
```

In production, inject real values via `--set`:
```bash
helm upgrade --install devops-info-service . \
  --set secrets.username=prod-user \
  --set secrets.password=real-password \
  --set secrets.secretKey=real-key
```

### Consuming Secrets in Deployment (envFrom)

```yaml
envFrom:
  - secretRef:
      name: {{ include "devops-info-service.fullname" . }}-secret
```

All keys from the secret (`username`, `password`, `secret-key`) are injected as environment variables.

### Verification

```bash
# Deploy the chart
helm upgrade --install devops-info-service ./k8s/devops-info-service

# Exec into pod and check env vars
kubectl exec -it <pod-name> -- env | grep -E 'username|password|secret-key'
# username=app-user
# password=changeme
# secret-key=dev-secret-key

# Confirm secrets don't appear in plain text in describe output
kubectl describe pod <pod-name>
# Environment variables from secrets show as: <set to the key 'username' in secret ...>
```

### Resource Limits Configuration

Already configured in `values.yaml`:

```yaml
resources:
  limits:
    cpu: 200m
    memory: 256Mi
  requests:
    cpu: 100m
    memory: 128Mi
```

**Requests vs Limits:**

| Parameter | Meaning | Effect |
|-----------|---------|--------|
| `requests.cpu` | Minimum CPU guaranteed | Used for scheduling decisions |
| `requests.memory` | Minimum memory guaranteed | Used for scheduling decisions |
| `limits.cpu` | Maximum CPU allowed | Pod throttled if exceeded |
| `limits.memory` | Maximum memory allowed | Pod OOMKilled if exceeded |

**How to choose values:**
1. Start without limits, observe actual usage with `kubectl top pods`
2. Set requests = observed average usage
3. Set limits = 2× requests (headroom for spikes)
4. For memory: limits should be > max observed peak (OOMKill is hard to debug)

---

## Task 3 — HashiCorp Vault Integration

### Installation

```bash
helm repo add hashicorp https://helm.releases.hashicorp.com
helm repo update

helm install vault hashicorp/vault \
  --set "server.dev.enabled=true" \
  --set "injector.enabled=true"
```

### Vault Pods Verification

```bash
kubectl get pods -l app.kubernetes.io/name=vault
```

Output:
```
NAME                                    READY   STATUS    RESTARTS   AGE
vault-0                                 1/1     Running   0          2m
vault-agent-injector-5d9f76b7c6-xpptf   1/1     Running   0          2m
```

### KV Secrets Engine Configuration

```bash
kubectl exec -it vault-0 -- /bin/sh

# Enable KV v2 secrets engine
vault secrets enable -path=secret kv-v2

# Store application secrets
vault kv put secret/devops-info-service/config \
  username="vault-admin" \
  password="vault-secret" \
  secret_key="vault-key-abc123"

# Verify
vault kv get secret/devops-info-service/config
```

Output:
```
======= Secret Path =======
secret/data/devops-info-service/config

======= Metadata =======
Key              Value
---              -----
created_time     2026-04-09T20:00:00.000000000Z
version          1

====== Data ======
Key           Value
---           -----
password      vault-secret
secret_key    vault-key-abc123
username      vault-admin
```

### Kubernetes Authentication Method

```bash
# Inside vault-0 pod
vault auth enable kubernetes

vault write auth/kubernetes/config \
  kubernetes_host="https://$KUBERNETES_PORT_443_TCP_ADDR:443"
```

### Policy Creation

```bash
vault policy write devops-info-service - <<EOF
path "secret/data/devops-info-service/*" {
  capabilities = ["read"]
}
EOF
```

### Role Creation

```bash
vault write auth/kubernetes/role/devops-info-service \
  bound_service_account_names=default \
  bound_service_account_namespaces=default \
  policies=devops-info-service \
  ttl=24h
```

### Vault Agent Injection — Deployment Annotations

Added to pod template in `deployment.yaml`:

```yaml
annotations:
  vault.hashicorp.com/agent-inject: "true"
  vault.hashicorp.com/role: "devops-info-service"
  vault.hashicorp.com/agent-inject-secret-config: "secret/data/devops-info-service/config"
  vault.hashicorp.com/agent-inject-template-config: |
    {{- with secret "secret/data/devops-info-service/config" -}}
    USERNAME={{ .Data.data.username }}
    PASSWORD={{ .Data.data.password }}
    SECRET_KEY={{ .Data.data.secret_key }}
    {{- end -}}
```

### Secret Injection Verification

```bash
# Check that vault-agent sidecar is running alongside app container
kubectl get pod <pod-name> -o jsonpath='{.spec.containers[*].name}'
# devops-info-service vault-agent

# Check injected secret file
kubectl exec -it <pod-name> -c devops-info-service -- cat /vault/secrets/config
# USERNAME=vault-admin
# PASSWORD=vault-secret
# SECRET_KEY=vault-key-abc123
```

### Sidecar Injection Pattern Explained

```
┌──────────────────────────────────────┐
│                  Pod                 │
│  ┌──────────────┐  ┌──────────────┐  │
│  │  App         │  │ Vault Agent  │  │
│  │  Container   │  │  Sidecar     │  │
│  │              │  │              │  │
│  │ reads:       │  │ - authenticates│ │
│  │ /vault/      │  │   to Vault   │  │
│  │  secrets/    │  │ - fetches    │  │
│  │  config      │  │   secrets    │  │
│  │              │  │ - writes to  │  │
│  └──────┬───────┘  │  shared vol  │  │
│         │          └──────────────┘  │
│         └──── shared volume ─────────┤
└──────────────────────────────────────┘
```

1. Vault Injector (MutatingWebhook) detects pod with vault annotations
2. Injects `vault-agent` init container + sidecar container
3. Init container fetches secrets before app starts
4. Sidecar renews lease and updates files on rotation
5. App reads secrets from `/vault/secrets/` (no Vault SDK needed)

---

## Bonus — Vault Agent Templates & Named Templates

### Template Annotation (`.env` format)

The `agent-inject-template-config` annotation renders secrets into a custom format:

```yaml
vault.hashicorp.com/agent-inject-template-config: |
  {{- with secret "secret/data/devops-info-service/config" -}}
  USERNAME={{ .Data.data.username }}
  PASSWORD={{ .Data.data.password }}
  SECRET_KEY={{ .Data.data.secret_key }}
  {{- end -}}
```

This produces `/vault/secrets/config` with content:
```
USERNAME=vault-admin
PASSWORD=vault-secret
SECRET_KEY=vault-key-abc123
```

Benefits: app can `source /vault/secrets/config` or parse the `.env` format directly.

### Dynamic Secret Rotation

Vault Agent handles rotation automatically:
- `vault.hashicorp.com/agent-inject-command` — runs a command when secrets are renewed
- Example: `vault.hashicorp.com/agent-inject-command-config: "kill -HUP 1"` sends SIGHUP to PID 1 (app) to reload config
- Default lease TTL is set at role level (`ttl=24h`)
- Agent renews at 2/3 of lease duration to avoid expiry

### Named Template in `_helpers.tpl`

```yaml
{{/*
Common environment variables — DRY helper to avoid duplication across templates.
Usage: {{- include "devops-info-service.envVars" . | nindent 12 }}
*/}}
{{- define "devops-info-service.envVars" -}}
{{- toYaml .Values.env }}
{{- end }}
```

Usage in `deployment.yaml`:
```yaml
env:
  {{- include "devops-info-service.envVars" . | nindent 12 }}
```

**DRY principle:** if multiple templates (e.g., init containers, job templates) need the same env vars, they all call `include "devops-info-service.envVars"` instead of duplicating the block.

---

## Security Analysis

### Kubernetes Secrets vs HashiCorp Vault

| Feature | K8s Secrets | HashiCorp Vault |
|---------|-------------|-----------------|
| Encryption at rest | Optional (requires config) | Yes (always) |
| Encryption in transit | Yes (TLS) | Yes (TLS) |
| Access control | RBAC (coarse) | Fine-grained policies |
| Secret rotation | Manual | Automatic (dynamic secrets) |
| Audit logging | Limited | Full audit trail |
| Secret leasing | No | Yes (TTL + renewal) |
| Dynamic secrets | No | Yes (DB, AWS, PKI, etc.) |
| Complexity | Low | Medium-High |
| Operational cost | Included in K8s | Separate deployment |

### When to Use Each

**Use Kubernetes Secrets when:**
- Simple key-value configuration (non-sensitive)
- TLS certificates managed by cert-manager
- Image pull credentials
- Small teams/projects where Vault overhead is not justified

**Use HashiCorp Vault when:**
- Production environments with compliance requirements
- Dynamic secrets needed (e.g., short-lived DB credentials)
- Multiple applications and environments sharing secrets
- Audit trail required
- Secret rotation automation needed

### Production Recommendations

1. **Always enable etcd encryption at rest** for K8s Secrets
2. **Use Vault for sensitive credentials** (DB passwords, API keys, tokens)
3. **Never commit real secrets** to Git — use placeholder values + `--set` at deploy time
4. **Apply least-privilege RBAC** — pods should only read their own secrets
5. **Enable Vault audit logging** to file and/or syslog
6. **Use short TTLs** on Vault roles (hours, not days) to limit blast radius
7. **Prefer dynamic secrets** where possible (Vault generates unique credentials per pod)
8. **Consider External Secrets Operator** as alternative to Vault Agent for GitOps workflows
