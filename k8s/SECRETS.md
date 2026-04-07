# Kubernetes Secrets & HashiCorp Vault

## Table of Contents

- [Kubernetes Secrets](#1-kubernetes-secrets)
- [Helm Secret Integration](#2-helm-secret-integration)
- [Resource Management](#3-resource-management)
- [Vault Integration](#4-vault-integration)
- [Security Analysis](#5-security-analysis)
- [Bonus: Vault Agent Templates](#6-bonus-vault-agent-templates)

---

## 1. Kubernetes Secrets

### Creating a Secret

```bash
kubectl create secret generic app-credentials \
  --from-literal=username=admin \
  --from-literal=password=S3cur3P@ssw0rd
```

```
secret/app-credentials created
```

### Viewing the Secret (YAML)

```bash
kubectl get secret app-credentials -o yaml
```

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: app-credentials
  namespace: default
data:
  password: UzNjdXIzUEBzc3cwcmQ=
  username: YWRtaW4=
type: Opaque
```

### Decoding Base64 Values

```bash
echo "YWRtaW4=" | base64 -d
# admin

echo "UzNjdXIzUEBzc3cwcmQ=" | base64 -d
# S3cur3P@ssw0rd
```

### Base64 Encoding vs Encryption

| Aspect | Base64 Encoding | Encryption |
|--------|----------------|------------|
| **Purpose** | Binary-to-text representation | Data confidentiality |
| **Reversibility** | Trivially reversible by anyone | Requires a key to decrypt |
| **Security** | Provides **zero** security | Provides strong data protection |
| **K8s Default** | Secrets are base64-encoded only | Must be explicitly enabled (etcd encryption) |

**Key takeaway:** Kubernetes Secrets are **not encrypted by default**. They are stored as base64 in etcd, meaning anyone with etcd or API access can decode them. For production:

- Enable [encryption at rest](https://kubernetes.io/docs/tasks/administer-cluster/encrypt-data/) via an `EncryptionConfiguration` resource
- Use RBAC to restrict `get`/`list` on Secrets
- Consider an external secret manager (Vault, AWS Secrets Manager, etc.)

---

## 2. Helm Secret Integration

### Chart Structure

```
devops-app/
├── Chart.yaml
├── values.yaml
├── templates/
│   ├── _helpers.tpl          # Named templates (incl. envVars)
│   ├── deployment.yaml       # Consumes secrets via envFrom
│   ├── secrets.yaml          # ← NEW: Secret resource
│   ├── service.yaml
│   ├── serviceaccount.yaml   # ← NEW: ServiceAccount for Vault
│   ├── NOTES.txt
│   └── hooks/
│       ├── pre-install-job.yaml
│       └── post-install-job.yaml
```

### Secret Template (`templates/secrets.yaml`)

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: {{ include "devops-app.fullname" . }}-secret
  labels:
    {{- include "devops-app.labels" . | nindent 4 }}
type: Opaque
stringData:
  {{- range $key, $value := .Values.secrets }}
  {{ $key }}: {{ $value | quote }}
  {{- end }}
```

The template iterates over every key in `.Values.secrets` and places it into `stringData` (Kubernetes auto-encodes plain text to base64).

### Secret Values in `values.yaml`

```yaml
secrets:
  USERNAME: "placeholder-user"
  PASSWORD: "placeholder-pass"
  DATABASE_URL: "postgresql://user:pass@localhost:5432/app"
```

> **Never commit real secrets.** These are placeholder defaults. Override at install time:
>
> ```bash
> helm install devops-app ./devops-app \
>   --set secrets.USERNAME=real-admin \
>   --set secrets.PASSWORD=real-password \
>   --set secrets.DATABASE_URL="postgresql://..."
> ```

### How Secrets Are Consumed in the Deployment

The deployment uses `envFrom` with a `secretRef` to inject all secret keys as environment variables:

```yaml
envFrom:
  - secretRef:
      name: {{ include "devops-app.fullname" . }}-secret
```

This automatically maps each key in the Secret (USERNAME, PASSWORD, DATABASE_URL) to an environment variable of the same name inside the container.

### Verification

```bash
# Deploy the chart
helm upgrade --install devops-app ./k8s/devops-app

# Check the secret was created
kubectl get secret devops-app-secret -o yaml
```

```bash
# Exec into the pod and verify env vars exist (values intentionally hidden)
kubectl exec -it deploy/devops-app -- env | grep -E 'USERNAME|PASSWORD|DATABASE_URL'
```

```
USERNAME=placeholder-user
PASSWORD=placeholder-pass
DATABASE_URL=postgresql://user:pass@localhost:5432/app
```

Secrets injected via `envFrom` are **not** visible in `kubectl describe pod` output — they appear as `<set to the key '...' in secret '...'>`, never as plaintext.

---

## 3. Resource Management

### Configuration

```yaml
resources:
  requests:
    memory: "128Mi"
    cpu: "100m"
  limits:
    memory: "256Mi"
    cpu: "200m"
```

### Requests vs Limits

| Property | Requests | Limits |
|----------|----------|--------|
| **Meaning** | Guaranteed minimum resources | Maximum allowed resources |
| **Scheduling** | Scheduler uses requests to place pods on nodes | Not used for scheduling |
| **Enforcement** | Soft — pod gets at least this much | Hard — pod is killed (OOM) or throttled (CPU) if it exceeds |
| **Best practice** | Set close to actual average usage | Set as a ceiling to prevent runaway processes |

### How to Choose Appropriate Values

1. **Start with monitoring data** — observe actual CPU/memory usage in Prometheus/Grafana before committing to values.
2. **Requests ≈ average usage** — this ensures the scheduler places pods where they'll actually fit.
3. **Limits ≈ 1.5–2× requests** — gives headroom for traffic spikes without allowing unbounded growth.
4. **Memory limits are critical** — exceeding the memory limit triggers an OOMKill, so leave a comfortable margin.
5. **CPU limits are softer** — the kernel throttles rather than kills, but severe throttling degrades latency.
6. **Per-environment tuning** — dev environments can use lower values (see `values-dev.yaml`), production needs more (see `values-prod.yaml`).

### Environment-Specific Values

| Environment | CPU Request | CPU Limit | Memory Request | Memory Limit |
|-------------|-------------|-----------|----------------|--------------|
| **dev** | 50m | 100m | 64Mi | 128Mi |
| **default** | 100m | 200m | 128Mi | 256Mi |
| **prod** | 200m | 500m | 256Mi | 512Mi |

---

## 4. Vault Integration

### Installation

```bash
# Add the HashiCorp Helm repository
helm repo add hashicorp https://helm.releases.hashicorp.com
helm repo update

# Install Vault in dev mode
helm install vault hashicorp/vault \
  --set "server.dev.enabled=true" \
  --set "injector.enabled=true"
```

### Verify Pods Are Running

```bash
kubectl get pods -l app.kubernetes.io/name=vault
```

```
NAME                                    READY   STATUS    RESTARTS   AGE
vault-0                                 1/1     Running   0          2m
vault-agent-injector-5cd8b87c6d-xk9rn   1/1     Running   0          2m
```

### Configure KV Secrets Engine

```bash
kubectl exec -it vault-0 -- /bin/sh

# Inside the Vault pod:
vault secrets enable -path=secret kv-v2

vault kv put secret/devops-app/config \
  username="admin" \
  password="vault-managed-secret" \
  database_url="postgresql://admin:vault-managed-secret@db:5432/app" \
  api_key="vk-2026-random-api-key"
```

```
====== Secret Path ======
secret/data/devops-app/config

======= Metadata =======
Key                Value
---                -----
created_time       2026-04-07T12:00:00.000000Z
custom_metadata    <nil>
deletion_time      n/a
destroyed          false
version            1
```

### Kubernetes Authentication

```bash
# Enable the Kubernetes auth method
vault auth enable kubernetes

# Configure it (run inside the vault-0 pod)
vault write auth/kubernetes/config \
  kubernetes_host="https://$KUBERNETES_PORT_443_TCP_ADDR:443"
```

### Policy

```bash
vault policy write devops-app - <<EOF
path "secret/data/devops-app/*" {
  capabilities = ["read"]
}
EOF
```

This policy grants **read-only** access to everything under `secret/data/devops-app/`.

### Role

```bash
vault write auth/kubernetes/role/devops-app \
  bound_service_account_names=devops-app \
  bound_service_account_namespaces=default \
  policies=devops-app \
  ttl=24h
```

The role binds the `devops-app` policy to pods running under the `devops-app` service account in the `default` namespace.

### Vault Agent Sidecar Injection

The deployment includes Vault annotations that trigger the Vault Agent Injector to add a sidecar:

```yaml
annotations:
  vault.hashicorp.com/agent-inject: "true"
  vault.hashicorp.com/role: "devops-app"
  vault.hashicorp.com/agent-inject-secret-config: "secret/data/devops-app/config"
```

### Verify Secrets in the Pod

```bash
kubectl exec -it deploy/devops-app -c devops-app -- cat /vault/secrets/config
```

```
username="admin"
password="vault-managed-secret"
database_url="postgresql://admin:vault-managed-secret@db:5432/app"
api_key="vk-2026-random-api-key"
```

### Sidecar Injection Pattern

The Vault Agent Injector works as follows:

1. **MutatingWebhook** — the injector watches for pods with `vault.hashicorp.com/agent-inject: "true"` annotations.
2. **Init container** — an `vault-agent-init` container runs first, authenticates with Vault using the pod's service account token, fetches secrets, and writes them to a shared volume at `/vault/secrets/`.
3. **Sidecar container** — a `vault-agent` sidecar continues running alongside the app, periodically refreshing secrets if their TTL expires or the Vault data changes.
4. **Shared volume** — both the init container/sidecar and the application container mount an in-memory `emptyDir` volume, so secrets never touch disk.

```
┌──────────────────────────────────────────────┐
│  Pod                                         │
│  ┌───────────────┐    ┌───────────────────┐  │
│  │ vault-agent   │    │  devops-app       │  │
│  │ (sidecar)     │    │  (main container) │  │
│  │               │    │                   │  │
│  │ Authenticates │    │ Reads secrets     │  │
│  │ with Vault    │──▶ │ from /vault/      │  │
│  │ via K8s SA    │    │ secrets/config    │  │
│  └───────────────┘    └───────────────────┘  │
│         │  shared emptyDir volume   │        │
│         └───────────────────────────┘        │
└──────────────────────────────────────────────┘
```

---

## 5. Security Analysis

### Kubernetes Secrets vs HashiCorp Vault

| Feature | K8s Secrets | HashiCorp Vault |
|---------|-------------|-----------------|
| **Storage** | etcd (base64) | Encrypted backend (Consul, Raft, etc.) |
| **Encryption at rest** | Optional (EncryptionConfig) | Always encrypted |
| **Access control** | RBAC on K8s API | Fine-grained policies per path |
| **Audit logging** | K8s audit logs (if enabled) | Built-in audit device |
| **Dynamic secrets** | Not supported | Supported (DB creds, cloud IAM, etc.) |
| **Secret rotation** | Manual | Automatic via leases & TTLs |
| **Secret versioning** | Not supported | KV v2 supports versioning |
| **Revocation** | Delete the Secret | Revoke leases, rotate immediately |
| **Complexity** | Minimal | Requires Vault deployment & management |
| **External integration** | Limited | 100+ backends (AWS, GCP, DBs, PKI, …) |

### When to Use Each

**Use Kubernetes Secrets when:**

- The cluster is small and team-managed
- Secrets are relatively static (API keys, config values)
- etcd encryption at rest is enabled
- RBAC properly restricts secret access
- You need simplicity over features

**Use HashiCorp Vault when:**

- Running in production with compliance requirements
- You need dynamic secrets (short-lived DB credentials)
- Secrets must be rotated automatically
- You need a centralized secrets manager across multiple clusters/services
- Audit trail for every secret access is required

### Production Recommendations

1. **Never use K8s Secrets alone in production** without enabling etcd encryption at rest.
2. **Use Vault for anything sensitive** — database passwords, API keys, TLS certificates.
3. **Enable Vault audit logging** to track who accessed which secret and when.
4. **Use short TTLs** for dynamic secrets so leaked credentials expire quickly.
5. **Separate Vault instances per environment** — don't share a Vault server between dev and prod.
6. **Use the External Secrets Operator** or Vault Agent Injector to bridge Vault with Kubernetes — never bake secrets into container images.
7. **Limit RBAC** — only the pods that need a secret should have access to it.

---

## 6. Bonus: Vault Agent Templates

### Template Annotation

Instead of the default key=value rendering, you can use Go templates to control the output format:

```yaml
annotations:
  vault.hashicorp.com/agent-inject: "true"
  vault.hashicorp.com/role: "devops-app"
  vault.hashicorp.com/agent-inject-secret-config: "secret/data/devops-app/config"
  vault.hashicorp.com/agent-inject-template-config: |
    {{- with secret "secret/data/devops-app/config" -}}
    DATABASE_URL={{ .Data.data.database_url }}
    API_KEY={{ .Data.data.api_key }}
    {{- end -}}
```

This renders `/vault/secrets/config` as a `.env`-style file:

```
DATABASE_URL=postgresql://admin:vault-managed-secret@db:5432/app
API_KEY=vk-2026-random-api-key
```

### Dynamic Secret Rotation

Vault Agent handles secret updates through a **refresh mechanism**:

- The sidecar polls Vault at the secret's TTL interval (or a configurable `vault.hashicorp.com/agent-cache-enable` / `template_config` stanza).
- When the secret version changes in Vault KV v2, the agent re-renders the template and overwrites `/vault/secrets/config`.
- The `vault.hashicorp.com/agent-inject-command` annotation can trigger a command when the secret is re-rendered:

```yaml
vault.hashicorp.com/agent-inject-command-config: "/bin/sh -c 'kill -HUP $(pidof python)'"
```

This sends SIGHUP to the application so it reloads the new secret without a pod restart.

### Named Templates in `_helpers.tpl`

To keep the deployment DRY, common environment variables are defined as a named template:

```yaml
{{- define "devops-app.envVars" -}}
- name: VAULT_ENABLED
  value: {{ .Values.vault.enabled | quote }}
- name: POD_NAME
  valueFrom:
    fieldRef:
      fieldPath: metadata.name
- name: POD_NAMESPACE
  valueFrom:
    fieldRef:
      fieldPath: metadata.namespace
{{- end }}
```

Usage in `deployment.yaml`:

```yaml
env:
  {{- include "devops-app.envVars" . | nindent 12 }}
  {{- toYaml .Values.env | nindent 12 }}
```

**Benefits:**

- **DRY principle** — define once, use in multiple deployments or containers.
- **Consistency** — all pods get the same base environment regardless of per-chart overrides.
- **Maintainability** — adding a new cross-cutting env var requires a single edit in `_helpers.tpl`.
