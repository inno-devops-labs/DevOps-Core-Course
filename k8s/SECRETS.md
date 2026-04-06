# Lab 11 — Kubernetes Secrets & HashiCorp Vault

## Task 1 — Kubernetes Secrets Fundamentals

### Creating the Secret

```bash
kubectl create secret generic app-credentials \
  --from-literal=username=admin \
  --from-literal=password=supersecret123
```

### Viewing the Secret in YAML

```yaml
apiVersion: v1
data:
  password: c3VwZXJzZWNyZXQxMjM=
  username: YWRtaW4=
kind: Secret
metadata:
  creationTimestamp: "2026-04-06T10:55:21Z"
  name: app-credentials
  namespace: default
  resourceVersion: "484"
  uid: 428f7366-cf6b-42c4-8b0b-ee8bc7d09496
type: Opaque
```

### Decoding the Values

```bash
$ echo "YWRtaW4=" | base64 -d
admin

$ echo "c3VwZXJzZWNyZXQxMjM=" | base64 -d
supersecret123
```

### Base64 Encoding vs Encryption

Kubernetes Secrets are **base64-encoded, not encrypted**. Base64 is just a way to represent binary data as text — anyone can decode it instantly. It is not a security mechanism.

By default, Secrets are stored in etcd in plain base64 form. This means:
- Anyone with access to etcd or the Kubernetes API can read them
- `kubectl get secret -o yaml` shows the "hidden" values to anyone with RBAC access

**etcd encryption at rest** means Kubernetes encrypts secret data before writing it to etcd. You enable it by configuring an `EncryptionConfiguration` on the API server. This should be enabled in production clusters so that even if someone gets raw etcd access, they cannot read the secrets.

---

## Task 2 — Helm-Managed Secrets

### Chart Structure

```
k8s/devops-info-service/
├── Chart.yaml
├── values.yaml
├── templates/
│   ├── _helpers.tpl        # includes named envVars template (bonus)
│   ├── deployment.yaml     # uses envFrom + named env template
│   ├── secrets.yaml        # secret template (new)
│   ├── service.yaml
│   └── hooks/
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
  APP_USERNAME: {{ .Values.secret.username | quote }}
  APP_PASSWORD: {{ .Values.secret.password | quote }}
```

### values.yaml — Secret Defaults

```yaml
secret:
  username: "changeme"
  password: "changeme"

appEnv: "production"
logLevel: "INFO"
```

Real values are passed at deploy time with `--set`, never committed to git.

### How Secrets Are Consumed in Deployment

Using `envFrom` to load all secret keys as environment variables:

```yaml
envFrom:
  - secretRef:
      name: {{ include "devops-info-service.fullname" . }}-secret
```

### Verification — Environment Variables in Pod

```bash
$ kubectl exec devops-info-service-df684b8cc-bzwhn -c devops-info-service -- env | grep APP
APP_PASSWORD=supersecret123
APP_USERNAME=admin
APP_ENV=production
LOG_LEVEL=INFO
```

### kubectl describe — Secret Values Not Shown

```
Environment Variables from:
  devops-info-service-secret  Secret  Optional: false
Environment:
  APP_ENV:    production
  LOG_LEVEL:  INFO
```

Secret values are hidden — only the secret name is shown. Individual env vars from `envFrom` are not listed in describe output.

---

## Task 2 Continued — Resource Management

Resource limits are configured in `values.yaml` and applied in the deployment:

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
- **Requests** — the minimum resources the container needs. Kubernetes uses this to decide which node to schedule the pod on.
- **Limits** — the maximum resources the container can use. If it exceeds the memory limit, the container is killed (OOMKilled). If it exceeds the CPU limit, it gets throttled.

**How to choose values:**
- Start with small requests (what the app actually needs at idle)
- Set limits to 2–4x the request to allow for spikes
- Monitor actual usage with `kubectl top pods` and tune accordingly

---

## Task 3 — HashiCorp Vault Integration

### Installing Vault via Helm

```bash
helm repo add hashicorp https://helm.releases.hashicorp.com
helm repo update

helm install vault hashicorp/vault \
  --set "server.dev.enabled=true" \
  --set "injector.enabled=true"
```

### Vault Pods Running

```
NAME                                    READY   STATUS    RESTARTS   AGE
vault-0                                 1/1     Running   0          2m33s
vault-agent-injector-75998c9b76-9bgk7   1/1     Running   0          2m33s
```

### Configuring KV Secrets Engine

```bash
# KV v2 is pre-enabled in dev mode at "secret/"
# Create a secret for our app
kubectl exec vault-0 -- vault kv put secret/devops-info-service/config \
  username="vault-admin" \
  password="vault-secret-456"
```

Output:
```
============= Secret Path =============
secret/data/devops-info-service/config

======= Metadata =======
Key          Value
---          -----
version      1

====== Data ======
Key         Value
---         -----
password    vault-secret-456
username    vault-admin
```

### Kubernetes Auth Configuration

```bash
# Enable Kubernetes auth
kubectl exec vault-0 -- vault auth enable kubernetes

# Configure it to talk to the cluster
kubectl exec vault-0 -- sh -c \
  'vault write auth/kubernetes/config kubernetes_host="https://${KUBERNETES_PORT_443_TCP_ADDR}:443"'
```

### Policy

```hcl
path "secret/data/devops-info-service/*" {
  capabilities = ["read"]
}
```

```bash
kubectl exec vault-0 -- sh -c 'vault policy write devops-info-service-policy - << EOF
path "secret/data/devops-info-service/*" {
  capabilities = ["read"]
}
EOF'
```

### Role Binding

```bash
kubectl exec vault-0 -- vault write auth/kubernetes/role/devops-info-service \
  bound_service_account_names="default" \
  bound_service_account_namespaces="default" \
  policies="devops-info-service-policy" \
  ttl="24h"
```

### Vault Agent Injection — Annotations in Deployment

```yaml
annotations:
  vault.hashicorp.com/agent-inject: "true"
  vault.hashicorp.com/role: "devops-info-service"
  vault.hashicorp.com/agent-inject-secret-config: "secret/data/devops-info-service/config"
  vault.hashicorp.com/agent-inject-template-config: |
    {{- with secret "secret/data/devops-info-service/config" -}}
    APP_USERNAME={{ .Data.data.username }}
    APP_PASSWORD={{ .Data.data.password }}
    {{- end -}}
```

### Proof of Secret Injection

After deploying with Vault annotations, pods run with 2 containers (app + vault-agent sidecar):

```
NAME                                    READY   STATUS    RESTARTS   AGE
devops-info-service-df684b8cc-2xlgt     2/2     Running   0          31s
devops-info-service-df684b8cc-bzwhn     2/2     Running   0          49s
devops-info-service-df684b8cc-wnq8s     2/2     Running   0          40s
```

Secret file is available inside the pod:

```bash
$ kubectl exec devops-info-service-df684b8cc-bzwhn -c devops-info-service -- ls /vault/secrets/
config

$ kubectl exec devops-info-service-df684b8cc-bzwhn -c devops-info-service -- cat /vault/secrets/config
APP_USERNAME=vault-admin
APP_PASSWORD=vault-secret-456
```

### How Sidecar Injection Works

When the Vault Agent Injector (a mutating webhook) sees a pod with `vault.hashicorp.com/agent-inject: "true"`, it automatically adds a `vault-agent` init container and a `vault-agent` sidecar container to the pod.

The init container authenticates to Vault using the pod's service account token, fetches the secrets, and writes them to a shared volume at `/vault/secrets/`. The sidecar container keeps running to refresh the secrets when they expire.

The app container reads secrets from files at `/vault/secrets/config` instead of environment variables. This is more secure because:
- Secrets are not visible in `kubectl describe` or `env` listings
- They can be rotated without restarting the pod

---

## Bonus — Vault Agent Templates

### Template Annotation

The `agent-inject-template-config` annotation uses Vault's Go template syntax to render secrets in a custom format (`.env` style in our case):

```yaml
vault.hashicorp.com/agent-inject-template-config: |
  {{- with secret "secret/data/devops-info-service/config" -}}
  APP_USERNAME={{ .Data.data.username }}
  APP_PASSWORD={{ .Data.data.password }}
  {{- end -}}
```

This renders the file `/vault/secrets/config` as:
```
APP_USERNAME=vault-admin
APP_PASSWORD=vault-secret-456
```

You can also render as JSON, INI, or any other format just by changing the template.

### Dynamic Secret Rotation

Vault Agent keeps running as a sidecar and periodically checks if the lease on the secret has expired. When a dynamic secret (like a database credential) is about to expire, Vault Agent automatically fetches a new one and rewrites the file.

The `vault.hashicorp.com/agent-inject-command` annotation lets you specify a command to run after the secret file is updated — for example, to send a SIGHUP to reload the app config without restarting the container.

### Named Templates in _helpers.tpl

We added a named template for common environment variables to avoid repeating them in multiple places:

```yaml
{{/*
Common environment variables
*/}}
{{- define "devops-info-service.envVars" -}}
- name: APP_ENV
  value: {{ .Values.appEnv | default "production" | quote }}
- name: LOG_LEVEL
  value: {{ .Values.logLevel | default "INFO" | quote }}
{{- end }}
```

Used in deployment.yaml with `include`:

```yaml
env:
  {{- include "devops-info-service.envVars" . | nindent 12 }}
```

This follows the DRY (Don't Repeat Yourself) principle — if you add a new standard env var, you update it in one place and all deployments get it automatically.

---

## Security Analysis — K8s Secrets vs Vault

| Feature | Kubernetes Secrets | HashiCorp Vault |
|---|---|---|
| Storage | etcd (base64, optionally encrypted) | Encrypted storage with audit log |
| Access control | RBAC | Fine-grained policies per path |
| Secret rotation | Manual | Automatic (dynamic secrets) |
| Audit log | Basic K8s audit | Full audit trail of who read what |
| Dynamic secrets | No | Yes (DB credentials, PKI, etc.) |
| Complexity | Simple | More setup required |

### When to Use Each

**Kubernetes Secrets are fine for:**
- Simple apps in a trusted cluster
- Non-production environments
- Secrets that don't need rotation
- When you want minimal infrastructure

**Vault is better when:**
- You need audit logs of secret access
- Secrets need automatic rotation
- You have dynamic credentials (DB, cloud IAM)
- Multiple teams or environments share the cluster
- Compliance requires strong secret management

### Production Recommendations

1. Always enable etcd encryption at rest
2. Use RBAC to restrict who can read secrets
3. For anything serious, use Vault or an external secret manager
4. Never commit real secrets to Git — use placeholder values and inject at deploy time
5. Consider the External Secrets Operator if you want to sync secrets from Vault/AWS/GCP into K8s Secrets automatically
