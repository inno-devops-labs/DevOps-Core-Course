# Secrets Management Documentation

## 1. Kubernetes Secrets

### Creating a Secret

```bash
$ kubectl create secret generic app-credentials \
  --from-literal=username=admin \
  --from-literal=password=supersecret
secret/app-credentials created
```

### Viewing the Secret

```bash
$ kubectl get secret app-credentials -o yaml
apiVersion: v1
data:
  password: c3VwZXJzZWNyZXQ=
  username: YWRtaW4=
kind: Secret
metadata:
  creationTimestamp: "2026-04-09T14:37:39Z"
  name: app-credentials
  namespace: default
  resourceVersion: "7053"
  uid: de7dd61e-6500-474a-a6e2-8b7a87f3bcbc
type: Opaque
```

### Decoding Base64 Values

```bash
$ echo "YWRtaW4=" | base64 -d
admin

$ echo "c3VwZXJzZWNyZXQ=" | base64 -d
supersecret
```

### Base64 Encoding vs Encryption

Kubernetes Secrets are **base64-encoded, not encrypted**. Base64 is a simple encoding scheme — anyone who can read the secret object can trivially decode the value in one command. It exists only to allow binary data to be stored as a string.

By default, Secrets are stored in plaintext in etcd. This means:

- Any user or service account with `get`/`list` access to the Secret API can read all values.
- Anyone with direct access to the etcd datastore can read them without any Kubernetes credentials.

To actually protect secrets at rest, you must enable **etcd encryption** via an `EncryptionConfiguration` resource, which encrypts secret data before it is written to etcd using a key managed by you (or a KMS provider). This is not enabled by default on most distributions including minikube.

For production, the recommended approach is to use an external secret manager such as HashiCorp Vault (configured in Task 3) and avoid storing sensitive data in etcd at all.

---

## 2. Helm-Managed Secrets

### Chart Structure

```
k8s/app-python/
├── Chart.yaml
├── values.yaml          ← placeholder secret values defined here
├── values-dev.yaml
├── values-prod.yaml
└── templates/
    ├── _helpers.tpl     ← named envVars template (bonus)
    ├── deployment.yaml  ← consumes the secret via envFrom
    ├── secrets.yaml     ← Secret resource template
    └── ...
```

### secrets.yaml Template

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: {{ include "app-python.fullname" . }}-secret
  labels:
    {{- include "app-python.labels" . | nindent 4 }}
type: Opaque
stringData:
  SERVICE_NAME: {{ .Values.secrets.serviceName | quote }}
  API_KEY: {{ .Values.secrets.apiKey | quote }}
```

`stringData` accepts plain text — Helm renders the values and Kubernetes handles the base64 encoding automatically.

### values.yaml Secret Defaults

```yaml
secrets:
  serviceName: "devops-info-service"
  apiKey: "changeme"
```

Real values are never committed. They are supplied at deploy time via `--set`:

```bash
helm upgrade myapp k8s/app-python \
  --set secrets.apiKey="real-key-here"
```

### Consuming Secrets in deployment.yaml

```yaml
envFrom:
  - secretRef:
      name: {{ include "app-python.fullname" . }}-secret
env:
  {{- include "app-python.envVars" . | nindent 12 }}
```

All keys from the Secret (`SERVICE_NAME`, `API_KEY`) are injected as environment variables via `envFrom`. Static non-sensitive variables (`APP_ENV`, `LOG_LEVEL`) come from the named template.

### Verification — Environment Variables in Pod

```bash
$ kubectl exec deploy/myapp-app-python -- env | grep -E "SERVICE_NAME|API_KEY|APP_ENV|LOG_LEVEL"
APP_ENV=production
LOG_LEVEL=info
API_KEY=changeme
SERVICE_NAME=devops-info-service
```

Secrets are present as environment variables. Note that `kubectl describe pod` shows the secret reference by name only — actual values are not printed.

### Helm-managed Secret in the Cluster

```bash
$ kubectl get secret myapp-app-python-secret -o yaml
apiVersion: v1
data:
  API_KEY: Y2hhbmdlbWU=
  SERVICE_NAME: ZGV2b3BzLWluZm8tc2VydmljZQ==
kind: Secret
metadata:
  labels:
    app.kubernetes.io/instance: myapp
    app.kubernetes.io/managed-by: Helm
    app.kubernetes.io/name: app-python
    app.kubernetes.io/version: "1.0"
    helm.sh/chart: app-python-0.1.0
  name: myapp-app-python-secret
  namespace: default
type: Opaque
```

---

## 3. Resource Management

### Configuration in values.yaml

```yaml
resources:
  limits:
    cpu: 200m
    memory: 256Mi
  requests:
    cpu: 100m
    memory: 128Mi
```

### Requests vs Limits

**Requests** are what the scheduler uses to decide which node to place the pod on. The container is guaranteed to get at least this much.

**Limits** are the maximum the container is allowed to consume. If the container exceeds the memory limit it is OOM-killed. If it exceeds the CPU limit it is throttled (not killed).

### Choosing Values

- Set requests based on normal steady-state usage observed in metrics.
- Set limits to a reasonable ceiling — high enough to handle spikes, low enough to protect the node.
- For this Python FastAPI app: `100m` CPU / `128Mi` memory for requests is conservative but safe on minikube. The `200m` / `256Mi` limits leave headroom for burst traffic.

### dev vs prod Values

|                  | Dev     | Prod    |
| ---------------- | ------- | ------- |
| `cpu request`    | `50m`   | `200m`  |
| `cpu limit`      | `100m`  | `500m`  |
| `memory request` | `64Mi`  | `256Mi` |
| `memory limit`   | `128Mi` | `512Mi` |

---

## 4. Vault Integration

### Installation

```bash
$ helm repo add hashicorp https://helm.releases.hashicorp.com
$ helm repo update
$ helm install vault hashicorp/vault \
    --set "server.dev.enabled=true" \
    --set "injector.enabled=true"
```

### Vault Pods Running

```bash
$ kubectl get pods
NAME                                    READY   STATUS    RESTARTS   AGE
myapp-app-python-84d4785464-27d4m       2/2     Running   0          28s
vault-0                                 1/1     Running   0          8m6s
vault-agent-injector-75998c9b76-k5mvs   1/1     Running   0          8m6s
```

`vault-0` is the Vault server. `vault-agent-injector-*` is the mutating webhook that intercepts pod creation and injects the sidecar.

### KV Secrets Engine and Secret

```bash
# KV v2 is pre-enabled in dev mode at path secret/
$ kubectl exec vault-0 -- vault kv put secret/myapp/config \
    username="admin" \
    password="vault-secret123"

====== Secret Path ======
secret/data/myapp/config

======= Metadata =======
Key              Value
---              -----
created_time     2026-04-09T14:41:51.899203758Z
version          1
```

### Kubernetes Auth Method

```bash
$ kubectl exec vault-0 -- vault auth enable kubernetes
Success! Enabled kubernetes auth method at: kubernetes/

$ kubectl exec vault-0 -- sh -c '
vault write auth/kubernetes/config \
  kubernetes_host="https://$KUBERNETES_PORT_443_TCP_ADDR:443" \
  kubernetes_ca_cert=@/var/run/secrets/kubernetes.io/serviceaccount/ca.crt \
  token_reviewer_jwt="$(cat /var/run/secrets/kubernetes.io/serviceaccount/token)"
'
Success! Data written to: auth/kubernetes/config
```

### Policy

```bash
$ kubectl exec vault-0 -- sh -c '
vault policy write app-python - <<EOF
path "secret/data/myapp/config" {
  capabilities = ["read"]
}
EOF
'
Success! Uploaded policy: app-python
```

### Role

```bash
$ kubectl exec vault-0 -- vault write auth/kubernetes/role/app-python \
    bound_service_account_names=default \
    bound_service_account_namespaces=default \
    policies=app-python \
    ttl=24h
```

The role binds the `default` service account in the `default` namespace to the `app-python` policy.

### Vault Agent Injection Annotations

Added to `podAnnotations` in `values.yaml`:

```yaml
podAnnotations:
  vault.hashicorp.com/agent-inject: "true"
  vault.hashicorp.com/role: "app-python"
  vault.hashicorp.com/agent-inject-secret-config: "secret/data/myapp/config"
  vault.hashicorp.com/agent-inject-template-config: |
    {{- with secret "secret/data/myapp/config" -}}
    USERNAME={{ .Data.data.username }}
    PASSWORD={{ .Data.data.password }}
    {{- end -}}
```

### Proof of Secret Injection

```bash
$ kubectl exec myapp-app-python-84d4785464-27d4m -c app-python -- \
    cat /vault/secrets/config

USERNAME=admin
PASSWORD=vault-secret123
```

The file is available at `/vault/secrets/config` inside the application container.

### Sidecar Injection Pattern

When a pod with `vault.hashicorp.com/agent-inject: "true"` is created, the Vault Agent Injector (a Kubernetes mutating admission webhook) intercepts the request and modifies the pod spec before it is persisted:

1. An **init container** (`vault-agent-init`) runs first. It authenticates to Vault using the pod's service account JWT, fetches the secret, renders it to `/vault/secrets/`, then exits.
2. A **sidecar container** (`vault-agent`) continues running to keep the secret file updated when it rotates.
3. The application container starts after the init container, so the secret file is guaranteed to exist before the app runs.

The application reads `/vault/secrets/config` as a regular file — it requires no Vault SDK or any knowledge of Vault.

---

## 5. Security Analysis

### Kubernetes Secrets vs Vault

|                    | K8s Secrets                    | HashiCorp Vault                    |
| ------------------ | ------------------------------ | ---------------------------------- |
| Storage            | etcd (plaintext by default)    | Encrypted at rest always           |
| Access control     | RBAC on Secret objects         | Fine-grained policies per path     |
| Audit log          | K8s audit log (if enabled)     | Built-in detailed audit log        |
| Secret rotation    | Manual                         | Automatic with dynamic secrets     |
| Complexity         | Low                            | Higher                             |
| External consumers | No                             | Yes (any service can authenticate) |
| GitOps safety      | Values end up in Helm releases | Secrets never leave Vault          |

### When to Use Each

**Kubernetes Secrets** are appropriate when:

- The cluster has etcd encryption at rest enabled.
- The secret is low-sensitivity (e.g., a feature flag, a non-critical API key).
- Simplicity is more important than strict access control.
- You have a small team with tightly controlled RBAC.

**HashiCorp Vault** is appropriate when:

- Secrets are high-sensitivity (credentials, private keys, tokens).
- You need a full audit trail of who accessed what and when.
- You want automatic secret rotation.
- Multiple applications or external services need access to the same secrets.
- Compliance requirements demand encryption at rest and access logging.

### Production Recommendations

1. **Never commit real secret values** to Git — use placeholder values in `values.yaml` and inject real values at deploy time or via Vault.
2. **Enable etcd encryption at rest** if using native K8s Secrets for anything sensitive.
3. **Use Vault** (or an equivalent like AWS Secrets Manager) for production workloads.
4. **Restrict RBAC** — service accounts should only have access to the secrets they need.
5. **Rotate secrets regularly** — Vault dynamic secrets make this automatic for databases and cloud credentials.
6. **Do not use `envFrom` for highly sensitive secrets in production** — environment variables are visible to all processes in the container and can leak via debug endpoints. Prefer files (as Vault agent provides).
