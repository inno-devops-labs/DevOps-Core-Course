# Lab 11 — Kubernetes Secrets & HashiCorp Vault

## 1. Kubernetes Secrets

### Creating and viewing a secret

```bash
kubectl create secret generic app-credentials \
  --from-literal=username=admin \
  --from-literal=password=S3cr3tP4ss!
```

See raw output in [`secrets/evidence/01-k8s-secret.txt`](./secrets/evidence/01-k8s-secret.txt).

The YAML representation stores values as base64:

```yaml
data:
  password: UzNjcjN0UDRzcyE=
  username: YWRtaW4=
```

Decoding:

```bash
echo "YWRtaW4=" | base64 -d  # → admin
echo "UzNjcjN0UDRzcyE=" | base64 -d  # → S3cr3tP4ss!
```

### Base64 encoding ≠ encryption

Base64 is encoding (reversible transformation), not encryption. Anyone with
`kubectl get secret` access can decode the value immediately. Kubernetes Secrets
are **not encrypted at rest by default** — they are stored in plain text in etcd.

**Production hardening:**
- Enable etcd encryption (`EncryptionConfiguration` manifest with `aescbc` / `aesgcm`)
- Use RBAC to limit `get secret` to only the SAs that need it
- Use an external secrets manager (Vault, AWS Secrets Manager, GCP Secret Manager)
- Consider [External Secrets Operator](https://external-secrets.io/) to sync from Vault → k8s Secret automatically

---

## 2. Helm Secret Integration

### Chart structure

```
k8s/helm/devops-info/
├── templates/
│   ├── secrets.yaml    ← Secret from values.yaml data
│   └── deployment.yaml ← consumes the Secret via envFrom
└── values.yaml         ← placeholder credentials
```

`templates/secrets.yaml` uses `stringData` (Kubernetes auto-encodes to base64):

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: {{ include "devops-info.fullname" . }}-secret
  labels: ...
type: Opaque
stringData:
  APP_USERNAME: {{ .Values.secret.username | quote }}
  APP_PASSWORD: {{ .Values.secret.password | quote }}
```

Deployment consumes it via `envFrom`:

```yaml
envFrom:
  - secretRef:
      name: {{ include "devops-info.fullname" . }}-secret
```

### Install with secrets

```bash
helm install devops-info k8s/helm/devops-info \
  --set secret.username=helm-user \
  --set secret.password=HelmP4ss!
```

Verify env vars in pod (values are present but not shown by `describe pod`):

```bash
kubectl exec <pod> -- env | grep APP_
# APP_USERNAME=helm-user
# APP_PASSWORD=HelmP4ss!
```

See [`secrets/evidence/04-helm-secrets.txt`](./secrets/evidence/04-helm-secrets.txt).

---

## 3. Resource Management

```yaml
resources:
  requests:
    cpu: "50m"
    memory: "96Mi"
  limits:
    cpu: "200m"
    memory: "192Mi"
```

- **Requests** — what the scheduler reserves on the node for this Pod.
  Set to the typical steady-state consumption so the scheduler places Pods correctly.
- **Limits** — the hard cap. The container is OOM-killed if it exceeds memory;
  CPU is throttled (not killed).
- **Why these values**: The Flask app is lightweight. 50 m CPU / 96 Mi memory is
  enough for normal traffic. Limits are 4× requests to absorb spikes without
  starving other workloads on the node.

---

## 4. Vault Integration

### Installation

```bash
helm repo add hashicorp https://helm.releases.hashicorp.com
helm install vault hashicorp/vault \
  --set "server.dev.enabled=true" \
  --set "injector.enabled=true"
```

### Configuration steps

```bash
# KV v2 already mounted at secret/ in dev mode
vault kv put secret/devops-info/config username="app-admin" password="V@ultS3cr3t!"

# Kubernetes auth
vault auth enable kubernetes
vault write auth/kubernetes/config \
  kubernetes_host="https://kubernetes.default.svc:443"

# Policy
vault policy write devops-info-policy - <<EOF
path "secret/data/devops-info/*" { capabilities = ["read"] }
EOF

# Role
vault write auth/kubernetes/role/devops-info-role \
  bound_service_account_names=devops-info \
  bound_service_account_namespaces=default \
  policies=devops-info-policy \
  ttl=24h
```

See full evidence in [`secrets/evidence/02-vault-config.txt`](./secrets/evidence/02-vault-config.txt).

### Sidecar injection pattern

The Vault Agent Injector is a mutating admission webhook. When a Pod has the
`vault.hashicorp.com/agent-inject: "true"` annotation, the webhook injects a
`vault-agent` init container (fetches secrets on startup) and a sidecar container
(refreshes secrets on rotation).

Secrets are written to `/vault/secrets/` as files (not env vars by default).
This avoids secrets appearing in `ps`, `env`, or `kubectl describe pod`.

```yaml
annotations:
  vault.hashicorp.com/agent-inject: "true"
  vault.hashicorp.com/role: "devops-info-role"
  vault.hashicorp.com/agent-inject-secret-config: "secret/data/devops-info/config"
  vault.hashicorp.com/agent-inject-template-config: |
    {{- with secret "secret/data/devops-info/config" -}}
    APP_USERNAME={{ .Data.data.username }}
    APP_PASSWORD={{ .Data.data.password }}
    {{- end -}}
```

Verification — secret file exists inside the pod:

```
/vault/secrets/config:
  APP_USERNAME=app-admin
  APP_PASSWORD=V@ultS3cr3t!
```

See [`secrets/evidence/03-vault-injection.txt`](./secrets/evidence/03-vault-injection.txt).

---

## 5. Security Analysis

| Feature | K8s Secrets | HashiCorp Vault |
|---------|------------|-----------------|
| Encryption at rest | Only with etcd encryption enabled | Always encrypted (AES-GCM) |
| Dynamic secrets | No | Yes (DB, AWS, PKI) |
| Secret rotation | Manual | Automatic |
| Audit log | Via K8s audit | Built-in per-request audit |
| Access control | RBAC on Secret objects | Fine-grained path policies |
| Sidecar injection | No | Yes (Vault Agent Injector) |
| Complexity | Low | High |

**When to use K8s Secrets:**
- Small teams, simple apps, low-sensitivity data
- Already have etcd encryption enabled
- Want zero extra infrastructure

**When to use Vault:**
- Production, regulated environments
- Need dynamic credentials (DB passwords, AWS STS)
- Need audit trails per secret access
- Multiple applications sharing the same secrets backend

---

## Bonus — Vault Agent Templates & Named Templates

### Vault Agent template annotation

```yaml
vault.hashicorp.com/agent-inject-template-config: |
  {{- with secret "secret/data/devops-info/config" -}}
  APP_USERNAME={{ .Data.data.username }}
  APP_PASSWORD={{ .Data.data.password }}
  {{- end -}}
```

This renders the secret as a `.env`-style file at `/vault/secrets/config`.
The `vault.hashicorp.com/agent-inject-command-config` annotation sends `SIGHUP`
to PID 1 when the secret is rotated, triggering a graceful reload.

**Secret rotation mechanism:** Vault Agent re-renders the template every
`lease_duration / 2`. When the rendered output changes, the command annotation
fires. This gives the app a chance to reload without a Pod restart.

### Named template in `_helpers.tpl`

```yaml
{{- define "devops-info.commonEnv" -}}
- name: PORT
  value: "5000"
- name: HOST
  value: "0.0.0.0"
- name: CHART_NAME
  value: {{ .Chart.Name | quote }}
- name: CHART_VERSION
  value: {{ .Chart.Version | quote }}
{{- end }}
```

Usage in `deployment.yaml`:

```yaml
env:
  {{- include "devops-info.commonEnv" . | nindent 12 }}
```

This keeps the deployment template DRY — all standard env vars are defined once
and reused across deployment variants.
