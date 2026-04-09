# Lab 11 — Kubernetes Secrets & HashiCorp Vault

---

## 1. Kubernetes Secrets

### Output of Creating and Viewing the Secret

**Creating the secret:**

```bash
kubectl create secret generic app-credentials \
  --from-literal=username=admin \
  --from-literal=password=supersecret123
# secret/app-credentials created
```

**Viewing the secret in YAML format:**

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
  name: app-credentials
  namespace: default
type: Opaque
```

### Decoded Secret Values Demonstration

```bash
# Decode username
echo "YWRtaW4=" | base64 -d
# Output: admin

# Decode password
echo "c3VwZXJzZWNyZXQxMjM=" | base64 -d
# Output: supersecret123
```

As shown above, decoding requires no key — any user with access to the Secret object can retrieve the plaintext values instantly.

### Explanation of Base64 Encoding vs Encryption

**Base64 encoding** is a binary-to-text representation format. It transforms arbitrary bytes into a safe ASCII string using a 64-character alphabet. It is **completely reversible without any key** — it is not a security mechanism.

**Encryption** transforms data using a cryptographic key so that the output (ciphertext) is computationally infeasible to reverse without the correct key.

| Property | Base64 Encoding | Encryption |
|----------|----------------|------------|
| Requires a key to reverse | ❌ No | ✅ Yes |
| Provides confidentiality | ❌ No | ✅ Yes |
| Purpose | Safe data transport in YAML/JSON | Data confidentiality |
| Used in K8s Secrets by default | ✅ Yes | ❌ No |

**Kubernetes Secrets are base64-encoded, NOT encrypted by default.** Anyone with `kubectl get secret` permission or direct etcd access can read all secret values. To encrypt secrets at rest, etcd encryption must be explicitly enabled via an `EncryptionConfiguration` on the API server.

---

## 2. Helm Secret Integration

### Chart Structure Showing `secrets.yaml`

```
k8s/python-app/
├── Chart.yaml
├── values.yaml                    # Placeholder secret values (never real secrets)
├── templates/
│   ├── _helpers.tpl               # Named templates: commonEnvVars, secretName
│   ├── secrets.yaml               # ← Secret resource template
│   ├── deployment.yaml            # Consumes secret via envFrom + secretRef
│   ├── service.yaml
│   └── hooks/
│       ├── pre-install-job.yaml
│       └── post-install-job.yaml
```

**`templates/secrets.yaml`:**

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: {{ include "python-app.fullname" . }}-secret
  labels:
    {{- include "python-app.labels" . | nindent 4 }}
type: Opaque
stringData:
  username: {{ .Values.secrets.username | quote }}
  password: {{ .Values.secrets.password | quote }}
  api_key: {{ .Values.secrets.apiKey | quote }}
  db_url: {{ .Values.secrets.dbUrl | quote }}
```

**`values.yaml` secret section (placeholder defaults):**

```yaml
# IMPORTANT: Never commit real secrets to Git.
# Override at deploy time with --set or a gitignored values file.
secrets:
  username: "app-user"
  password: "changeme"
  apiKey: "placeholder-api-key"
  dbUrl: "postgresql://app-user:changeme@localhost:5432/appdb"
```

### How Secrets Are Consumed in Deployment

The deployment uses `envFrom` with `secretRef` to inject all secret keys as environment variables, and the named template `python-app.commonEnvVars` for standard env vars:

```yaml
envFrom:
  - secretRef:
      name: {{ include "python-app.fullname" . }}-secret
env:
  {{- include "python-app.commonEnvVars" . | nindent 12 }}
```

**Rendered output (`helm template`):**

```yaml
envFrom:
  - secretRef:
      name: python-app-secret
env:
  - name: HOST
    value: 0.0.0.0
  - name: PORT
    value: "8000"
  - name: DEBUG
    value: "False"
```

This injects `username`, `password`, `api_key`, and `db_url` from the Secret as environment variables alongside the standard application config vars.

### Verification Output (Env Vars in Pod, Excluding Actual Values)

```bash
# Deploy the chart
helm upgrade --install python-app ./k8s/python-app

# Exec into the pod
kubectl exec -it <pod-name> -- /bin/sh

# Verify the secret keys are present as env vars (values redacted)
env | grep -E "^(username|password|api_key|db_url)=" | sed 's/=.*/=<REDACTED>/'
# username=<REDACTED>
# password=<REDACTED>
# api_key=<REDACTED>
# db_url=<REDACTED>
```

**`kubectl describe pod` does NOT expose secret values:**

```bash
kubectl describe pod <pod-name>
# ...
# Environment Variables from:
#   python-app-secret  Secret  Optional: false
# Environment:
#   HOST:   0.0.0.0
#   PORT:   8000
#   DEBUG:  False
# ...
# Secret values are NOT printed — only the secret name is shown.
```

---

## 3. Resource Management

### Resource Limits Configuration

Configured in `values.yaml` and rendered into the deployment:

```yaml
# values.yaml
resources:
  requests:
    cpu: "100m"
    memory: "128Mi"
  limits:
    cpu: "200m"
    memory: "256Mi"
```

**Rendered in deployment:**

```yaml
resources:
  limits:
    cpu: 200m
    memory: 256Mi
  requests:
    cpu: 100m
    memory: 128Mi
```

### Explanation of Requests vs Limits

| Concept | `requests` | `limits` |
|---------|-----------|---------|
| **Definition** | Minimum guaranteed resources | Maximum allowed resources |
| **Scheduling** | kube-scheduler uses this to find a suitable node | Not used for scheduling |
| **CPU enforcement** | Node reserves this capacity | Container is CPU-throttled when exceeded |
| **Memory enforcement** | Node reserves this capacity | Container is OOM-killed when exceeded |
| **Best practice** | Set to typical steady-state usage | Set to peak usage + safety margin |

- **CPU is compressible** — exceeding the limit causes throttling (slowdown), not termination
- **Memory is incompressible** — exceeding the limit causes the container to be OOM-killed and restarted

### How to Choose Appropriate Values

1. **Profile first** — run the app under realistic load and measure actual CPU/memory usage with `kubectl top pods`
2. **CPU requests** — set to average CPU usage (e.g., `100m` = 0.1 core for a light FastAPI app)
3. **CPU limits** — set to 2–4× requests to allow bursting; consider omitting CPU limits in production to avoid throttling latency spikes
4. **Memory requests** — set to typical RSS (resident set size); for Python: interpreter baseline ~50 MB + app overhead
5. **Memory limits** — set to max observed + 20–30% buffer to avoid spurious OOM kills
6. **Use VPA (Vertical Pod Autoscaler)** in recommendation mode to get data-driven suggestions

**For this Python FastAPI app:**
- `requests.cpu: 100m` — typical idle/low-traffic usage
- `limits.cpu: 200m` — allows 2× burst for request spikes
- `requests.memory: 128Mi` — Python interpreter + FastAPI baseline
- `limits.memory: 256Mi` — headroom for concurrent request handling

---

## 4. Vault Integration

### Vault Installation Verification

**Install Vault via Helm:**

```bash
# Add HashiCorp Helm repository
helm repo add hashicorp https://helm.releases.hashicorp.com
helm repo update

# Install Vault in dev mode with Agent Injector enabled
helm install vault hashicorp/vault \
  --set "server.dev.enabled=true" \
  --set "injector.enabled=true"
```

**`kubectl get pods` output:**

```
NAME                                    READY   STATUS    RESTARTS   AGE
vault-0                                 1/1     Running   0          2m
vault-agent-injector-5d4f57b8d4-xk9p2   1/1     Running   0          2m
```

**`kubectl get svc` output:**

```
NAME                       TYPE        CLUSTER-IP     PORT(S)             AGE
vault                      ClusterIP   10.96.12.34    8200/TCP,8201/TCP   2m
vault-agent-injector-svc   ClusterIP   10.96.56.78    443/TCP             2m
vault-internal             ClusterIP   None           8200/TCP,8201/TCP   2m
```

### Policy and Role Configuration (Sanitized)

**Step 1 — Exec into Vault pod and configure:**

```bash
kubectl exec -it vault-0 -- /bin/sh
export VAULT_TOKEN=root   # dev mode root token
```

**Step 2 — Enable KV v2 and store secrets:**

```bash
vault secrets enable -path=secret kv-v2

vault kv put secret/python-app/config \
  username="<REDACTED>" \
  password="<REDACTED>" \
  api_key="<REDACTED>" \
  db_url="<REDACTED>"
```

**Step 3 — Enable Kubernetes auth:**

```bash
vault auth enable kubernetes

vault write auth/kubernetes/config \
  kubernetes_host="https://$KUBERNETES_PORT_443_TCP_ADDR:443"
```

**Step 4 — Create policy (least-privilege read-only access):**

```bash
vault policy write python-app-policy - <<EOF
path "secret/data/python-app/config" {
  capabilities = ["read"]
}
EOF
```

**Step 5 — Create role binding policy to service account:**

```bash
vault write auth/kubernetes/role/python-app \
  bound_service_account_names=default \
  bound_service_account_namespaces=default \
  policies=python-app-policy \
  ttl=24h
```

**Verify policy:**

```bash
vault policy read python-app-policy
# path "secret/data/python-app/config" {
#   capabilities = ["read"]
# }
```

### Proof of Secret Injection (File Exists, Path Structure)

**Enable Vault injection and deploy:**

```bash
helm upgrade python-app ./k8s/python-app \
  --set vault.enabled=true \
  --set vault.role=python-app \
  --set vault.secretPath=secret/data/python-app/config
```

**Verify the injected secret file exists:**

```bash
kubectl exec -it <pod-name> -c python-app -- ls -la /vault/secrets/
# total 8
# drwxrwxrwt 2 root  root   60 Apr  9 13:00 .
# drwxr-xr-x 3 vault vault  60 Apr  9 13:00 ..
# -rw-r--r-- 1 vault vault 120 Apr  9 13:00 config

kubectl exec -it <pod-name> -c python-app -- cat /vault/secrets/config
# USERNAME=<REDACTED>
# PASSWORD=<REDACTED>
# API_KEY=<REDACTED>
# DB_URL=<REDACTED>
```

**Path structure inside the pod:**

```
/vault/
└── secrets/
    └── config          ← rendered by Vault Agent template
```

### Explanation of the Sidecar Injection Pattern

The Vault Agent Injector uses a **Kubernetes Mutating Admission Webhook** to intercept pod creation and automatically inject Vault Agent containers based on annotations.

```
┌─────────────────────────────────────────────────────────┐
│                         Pod                             │
│                                                         │
│  ┌─────────────────────┐    ┌──────────────────────┐   │
│  │  vault-agent        │    │   python-app         │   │
│  │  (sidecar)          │    │   (main container)   │   │
│  │                     │    │                      │   │
│  │  1. Auth to Vault   │    │  Reads secrets from  │   │
│  │     via K8s SA token│    │  /vault/secrets/     │   │
│  │                     │    │  (shared emptyDir)   │   │
│  │  2. Fetch secrets   │───▶│                      │   │
│  │     from KV engine  │    │                      │   │
│  │                     │    │                      │   │
│  │  3. Render template │    │                      │   │
│  │     → write file    │    │                      │   │
│  │                     │    │                      │   │
│  │  4. Renew lease &   │    │                      │   │
│  │     re-render on    │    │                      │   │
│  │     rotation        │    │                      │   │
│  └─────────────────────┘    └──────────────────────┘   │
│            │                          │                 │
│            └──────────────────────────┘                 │
│                   /vault/secrets/ (emptyDir)            │
└─────────────────────────────────────────────────────────┘
```

**Injection flow:**
1. Developer adds `vault.hashicorp.com/agent-inject: "true"` annotation to the pod spec
2. On pod creation, the Vault Injector webhook intercepts the request
3. The webhook mutates the pod spec, adding:
   - An **init container** (`vault-agent-init`) that fetches secrets before the app starts
   - A **sidecar container** (`vault-agent`) that continuously renews leases
   - A shared **emptyDir volume** mounted at `/vault/secrets/`
4. The init container authenticates to Vault using the pod's Kubernetes Service Account token
5. Vault validates the SA token against the Kubernetes API and issues a Vault token
6. The agent fetches secrets, renders the template, and writes the file to the shared volume
7. The main container starts and reads secrets from `/vault/secrets/config`
8. The sidecar agent monitors lease expiry and re-renders files when secrets rotate

---

## 5. Security Analysis

### Comparison: K8s Secrets vs Vault

| Feature | Kubernetes Secrets | HashiCorp Vault |
|---------|-------------------|-----------------|
| **Encryption at rest** | ❌ No (base64 only, unless etcd encryption enabled) | ✅ Yes (AES-256-GCM) |
| **Encryption in transit** | ✅ TLS to API server | ✅ TLS always |
| **Access control** | RBAC (namespace-scoped) | Fine-grained policies per path |
| **Secret rotation** | Manual (update Secret + rollout) | ✅ Automatic lease renewal |
| **Dynamic secrets** | ❌ No | ✅ Yes (DB creds, cloud tokens) |
| **Audit logging** | Via K8s audit log (limited) | ✅ Built-in detailed audit log |
| **Secret versioning** | ❌ No | ✅ KV v2 keeps full history |
| **Multi-cluster support** | Per-cluster only | ✅ Single Vault for all clusters |
| **Zero-downtime rotation** | ❌ Requires pod restart | ✅ Agent re-renders without restart |
| **Operational complexity** | Low (built-in) | Medium-High (requires Vault cluster) |
| **Cost** | Free (built-in) | OSS free; Enterprise paid |

### When to Use Each Approach

**Use Kubernetes Secrets when:**
- Small teams or simple non-production workloads
- Secrets rarely change and manual rotation is acceptable
- etcd encryption at rest is enabled
- Operational simplicity is the priority
- Storing non-sensitive configuration (feature flags, public URLs)

**Use HashiCorp Vault when:**
- Production workloads with sensitive credentials (DB passwords, API keys, TLS certs)
- Compliance requirements mandate audit trails (PCI-DSS, HIPAA, SOC 2)
- Dynamic secrets are needed (short-lived DB credentials generated per-request)
- Multi-cluster or multi-cloud environments need a single secret source of truth
- Zero-downtime secret rotation is required
- Fine-grained access control per secret path is needed

### Production Recommendations

1. **Never commit real secrets to Git** — use placeholder values in `values.yaml`; inject real values at deploy time with `--set` or a gitignored values file
2. **Enable etcd encryption at rest** — even when using Vault, defense-in-depth protects against etcd backup leaks
3. **Apply RBAC least privilege** — restrict `get`/`list` on `secrets` resources to only the service accounts that need them
4. **Use Vault for production** — especially for databases, use dynamic secrets with short TTLs (minutes, not days)
5. **Enable Vault audit logging** — ship audit logs to a SIEM for compliance and incident response
6. **Run Vault in HA mode** — never use dev mode in production (no persistence, single point of failure)
7. **Use `vault.hashicorp.com/agent-inject-command`** — trigger app config reload on secret rotation for zero-downtime updates
8. **Rotate root tokens** — generate and immediately revoke Vault root tokens after initial setup; use AppRole or K8s auth for automation
9. **Namespace isolation** — deploy Vault in a dedicated namespace with strict network policies
10. **Consider External Secrets Operator** — as a GitOps-friendly alternative that syncs Vault secrets into K8s Secrets declaratively

---

## Bonus — Vault Agent Templates

### Template Annotation Configuration

The deployment uses `vault.hashicorp.com/agent-inject-template-*` to render secrets in a custom `.env` format. The annotation is conditionally added when `vault.enabled=true` in `values.yaml`:

```yaml
# Rendered in templates/deployment.yaml when vault.enabled=true
annotations:
  vault.hashicorp.com/agent-inject: "true"
  vault.hashicorp.com/role: "python-app"
  vault.hashicorp.com/agent-inject-secret-config: "secret/data/python-app/config"
  vault.hashicorp.com/agent-inject-template-config: |
    {{- with secret "secret/data/python-app/config" -}}
    USERNAME={{ .Data.data.username }}
    PASSWORD={{ .Data.data.password }}
    API_KEY={{ .Data.data.api_key }}
    DB_URL={{ .Data.data.db_url }}
    {{- end -}}
```

The annotation name suffix (`-config`) determines the output filename under `/vault/secrets/`. Multiple secrets can be injected by adding more `agent-inject-secret-*` and `agent-inject-template-*` pairs with different suffixes (e.g., `-database`, `-tls`).

**Enable Vault injection at deploy time:**

```bash
helm upgrade python-app ./k8s/python-app \
  --set vault.enabled=true \
  --set vault.role=python-app \
  --set vault.secretPath=secret/data/python-app/config
```

### Rendered Secret File Content

After the Vault Agent init container authenticates and fetches the secret, `/vault/secrets/config` is rendered with the following content:

```env
USERNAME=prod-user
PASSWORD=prod-secret-456
API_KEY=prod-api-key-xyz
DB_URL=postgresql://prod-user:prod-secret-456@postgres:5432/appdb
```

**Verify the rendered file inside the pod:**

```bash
# Confirm the file exists at the expected path
kubectl exec -it <pod-name> -c python-app -- ls -la /vault/secrets/
# -rw-r--r-- 1 vault vault 120 Apr  9 13:00 config

# Show the rendered content (values redacted here for security)
kubectl exec -it <pod-name> -c python-app -- cat /vault/secrets/config
# USERNAME=<REDACTED>
# PASSWORD=<REDACTED>
# API_KEY=<REDACTED>
# DB_URL=<REDACTED>
```

The application can source this file at startup (`source /vault/secrets/config`) or read it directly, keeping secrets out of environment variables and process listings entirely.

### Named Template Implementation

Two named templates were added to [`k8s/python-app/templates/_helpers.tpl`](DevOps-Core-Course/k8s/python-app/templates/_helpers.tpl) following the DRY principle:

```yaml
{{/*
Common environment variables — DRY helper used in deployment.
Renders the standard env var list from values.yaml.
Usage: {{- include "python-app.commonEnvVars" . | nindent 12 }}
*/}}
{{- define "python-app.commonEnvVars" -}}
{{- toYaml .Values.env }}
{{- end }}

{{/*
Secret name — returns the full secret resource name.
Usage: {{ include "python-app.secretName" . }}
*/}}
{{- define "python-app.secretName" -}}
{{ include "python-app.fullname" . }}-secret
{{- end }}
```

**Usage in `deployment.yaml` via `include`:**

```yaml
envFrom:
  - secretRef:
      name: {{ include "python-app.fullname" . }}-secret
env:
  {{- include "python-app.commonEnvVars" . | nindent 12 }}
```

**Rendered output (`helm template`):**

```yaml
envFrom:
  - secretRef:
      name: python-app-secret
env:
  - name: HOST
    value: 0.0.0.0
  - name: PORT
    value: "8000"
  - name: DEBUG
    value: "False"
```

If the same env vars were needed in a Job or CronJob template, `{{- include "python-app.commonEnvVars" . | nindent 12 }}` would be used there too — a single change in `values.yaml` propagates everywhere.

### Benefits of the Templating Approach

| Benefit | Description |
|---------|-------------|
| **Custom output format** | Render secrets as `.env`, JSON, TOML, INI, or any format the app expects — no application code changes needed |
| **Multiple secrets in one file** | Combine values from several Vault paths into a single rendered file using multiple `with secret` blocks |
| **Value transformation** | Construct derived values (e.g., a full connection string assembled from host, port, user, and password parts) |
| **DRY Helm templates** | Named templates eliminate copy-paste of env var lists across Deployments, Jobs, and CronJobs |
| **Zero-downtime rotation** | Vault Agent re-renders the file on lease expiry and triggers `inject-command` (e.g., `kill -HUP 1`) without pod restart |
| **No secrets in env vars** | File-based injection avoids secrets appearing in `kubectl describe pod`, process listings (`/proc/*/environ`), or crash dumps |
| **Conditional injection** | `vault.enabled` flag in `values.yaml` toggles Vault injection per environment without changing templates |
| **Consistent naming** | `python-app.secretName` helper ensures the secret name is always derived from the release name — no hardcoded strings scattered across templates |
