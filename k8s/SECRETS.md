# Lab 11 — Kubernetes Secrets & HashiCorp Vault

## Environment

Local validation was completed on April 9, 2026 with:

```text
helm:      v3.17.1
kubectl:   v1.32.2
minikube:  v1.35.0
docker:    28.3.3
cluster:   minikube profile "lab11"
node:      Kubernetes v1.32.0
```

The lab was implemented by extending the existing Helm chart from Lab 10 in [`k8s/python-app`](/Users/mazzz3r/study/DevOps/k8s/python-app).

## 1. Kubernetes Secrets Fundamentals

### Secret creation

Imperative secret creation command:

```bash
kubectl create secret generic app-credentials \
  --namespace lab11 \
  --from-literal=username=lab11-user \
  --from-literal=password='S3cr3t-Lab11!'
```

Observed output:

```text
secret/app-credentials created
```

### Secret YAML

```bash
kubectl get secret app-credentials -n lab11 -o yaml
```

```yaml
apiVersion: v1
data:
  password: UzNjcjN0LUxhYjExIQ==
  username: bGFiMTEtdXNlcg==
kind: Secret
metadata:
  creationTimestamp: "2026-04-09T17:31:45Z"
  name: app-credentials
  namespace: lab11
type: Opaque
```

### Base64 decoding demo

```bash
printf 'bGFiMTEtdXNlcg==' | base64 -d
printf 'UzNjcjN0LUxhYjExIQ==' | base64 -d
```

```text
lab11-user
S3cr3t-Lab11!
```

### Encoding vs encryption

- Base64 is only an encoding format. It makes binary or special data safe to transport in YAML/JSON, but it does not protect confidentiality.
- Encryption transforms data with a key so unauthorized readers cannot recover the plaintext.
- Kubernetes Secrets are base64-encoded in manifests and API responses, but that alone is not encryption.

### Security implications

- Kubernetes Secrets are not encrypted at rest by default in a way you should rely on for strong protection. Without at-rest encryption, secret values stored in `etcd` can be recovered by anyone with sufficient datastore or API access.
- `etcd` encryption at rest should be enabled when a cluster stores real credentials, tokens, certificates, or other sensitive material.
- Even with encryption at rest enabled, RBAC is still required because anyone with Secret read access through the API can still retrieve the decrypted values.

## 2. Helm-Managed Secrets

### Chart changes

Implemented files:

```text
k8s/python-app/
├── values.yaml
├── values-dev.yaml
├── values-prod.yaml
└── templates/
    ├── _helpers.tpl
    ├── deployment.yaml
    ├── secrets.yaml
    ├── service.yaml
    └── serviceaccount.yaml
```

Key additions:

- [`k8s/python-app/templates/secrets.yaml`](/Users/mazzz3r/study/DevOps/k8s/python-app/templates/secrets.yaml): creates the chart-managed `Secret`.
- [`k8s/python-app/templates/serviceaccount.yaml`](/Users/mazzz3r/study/DevOps/k8s/python-app/templates/serviceaccount.yaml): creates a dedicated service account for Vault auth binding.
- [`k8s/python-app/templates/_helpers.tpl`](/Users/mazzz3r/study/DevOps/k8s/python-app/templates/_helpers.tpl): adds named helpers for secret names, service account names, shared env vars, and the bonus Vault template.
- [`k8s/python-app/templates/deployment.yaml`](/Users/mazzz3r/study/DevOps/k8s/python-app/templates/deployment.yaml): consumes both Kubernetes Secrets and Vault annotations.

### Secret values in `values.yaml`

Placeholder defaults are kept in version control:

```yaml
secret:
  create: true
  name: ""
  data:
    APP_USERNAME: "placeholder-user"
    APP_PASSWORD: "placeholder-password"
    APP_API_KEY: "placeholder-api-key"
```

Real values were passed during install with `--set`, not committed to Git.

### Deployment consumption

The app consumes the Helm Secret through `envFrom`:

```yaml
env:
  {{- include "python-app.envVars" . | nindent 12 }}
envFrom:
  - secretRef:
      name: {{ include "python-app.secretName" . }}
```

This keeps non-secret variables in the normal `env` section and injects all secret keys from the Kubernetes Secret.

### Helm install used for verification

```bash
helm upgrade --install python-lab11 k8s/python-app \
  --namespace lab11 \
  --create-namespace \
  -f k8s/python-app/values-dev.yaml \
  --set secret.data.APP_USERNAME=chart-user \
  --set secret.data.APP_PASSWORD='chart-pass-123' \
  --set secret.data.APP_API_KEY='lab11-api-key'
```

### Rendered Helm Secret in the cluster

```bash
kubectl get secret python-lab11-devops-info-python-secret -n lab11 -o yaml
```

```yaml
apiVersion: v1
data:
  APP_API_KEY: bGFiMTEtYXBpLWtleQ==
  APP_PASSWORD: Y2hhcnQtcGFzcy0xMjM=
  APP_USERNAME: Y2hhcnQtdXNlcg==
kind: Secret
metadata:
  name: python-lab11-devops-info-python-secret
  namespace: lab11
type: Opaque
```

### Verification inside the pod

Pod env verification command:

```bash
kubectl exec -n lab11 <pod> -- sh -c \
  'printenv | grep "^APP_" | sed "s/=.*$/=<redacted>/"'
```

Observed output:

```text
APP_USERNAME=<redacted>
APP_API_KEY=<redacted>
APP_PASSWORD=<redacted>
```

### `kubectl describe pod` does not expose values

Observed excerpt:

```text
Environment Variables from:
  python-lab11-devops-info-python-secret  Secret  Optional: false
Environment:
  DEBUG:          false
  HOST:           0.0.0.0
  PORT:           8000
  RELEASE_TRACK:  dev
```

The pod description shows the secret reference, not the secret values themselves.

## 3. Resource Management

### Configured requests and limits

Base chart defaults:

```yaml
resources:
  requests:
    cpu: 100m
    memory: 128Mi
  limits:
    cpu: 250m
    memory: 256Mi
```

Dev override used during validation:

```yaml
resources:
  requests:
    cpu: 50m
    memory: 64Mi
  limits:
    cpu: 100m
    memory: 128Mi
```

Observed pod resources:

```text
Limits:
  cpu:     100m
  memory:  128Mi
Requests:
  cpu:      50m
  memory:   64Mi
```

### Requests vs limits

- Requests define the minimum resources the scheduler reserves for the container.
- Limits define the maximum resources the container is allowed to consume at runtime.
- Good starting values come from measuring normal and peak application behavior, then leaving some safety headroom without wasting cluster capacity.

## 4. Vault Integration

### Vault installation

Vault was installed with the HashiCorp Helm chart in dev mode:

```bash
env HELM_CONFIG_HOME=/tmp/helm-lab11 \
    HELM_CACHE_HOME=/tmp/helm-lab11/cache \
    HELM_DATA_HOME=/tmp/helm-lab11/data \
    helm upgrade --install vault hashicorp/vault \
      --namespace vault \
      --create-namespace \
      --set server.dev.enabled=true \
      --set injector.enabled=true \
      --set ui.enabled=true
```

Verification:

```bash
kubectl get pods -n vault -o wide
```

```text
NAME                                   READY   STATUS    RESTARTS   AGE
vault-0                                1/1     Running   0          3m36s
vault-agent-injector-6b4f84b6c-zp46c   1/1     Running   0          3m36s
```

### Vault secret creation

The dev server was available with root token `root`:

```bash
kubectl exec -n vault vault-0 -- sh -c \
  'export VAULT_ADDR=http://127.0.0.1:8200 VAULT_TOKEN=root && vault status'
```

Stored application secrets:

```bash
kubectl exec -n vault vault-0 -- sh -c \
  'export VAULT_ADDR=http://127.0.0.1:8200 VAULT_TOKEN=root && \
   vault kv put secret/python-app/config \
     APP_USERNAME=vault-user \
     APP_PASSWORD=vault-pass-456 \
     APP_API_KEY=vault-api-key'
```

Observed output:

```text
======== Secret Path ========
secret/data/python-app/config
```

### Kubernetes auth configuration

Enabled auth method:

```bash
kubectl exec -n vault vault-0 -- sh -c \
  'export VAULT_ADDR=http://127.0.0.1:8200 VAULT_TOKEN=root && \
   vault auth enable kubernetes'
```

Configured the auth backend to trust the Kubernetes API server and a token reviewer JWT from the `vault` service account.

### Policy

Sanitized policy used:

```hcl
path "secret/data/python-app/config" {
  capabilities = ["read"]
}
```

Uploaded with:

```bash
vault policy write python-app /tmp/python-app-policy.hcl
```

### Role

Configured role:

```bash
vault write auth/kubernetes/role/python-app-role \
  bound_service_account_names=python-lab11-devops-info-python-sa \
  bound_service_account_namespaces=lab11 \
  policies=python-app \
  ttl=24h
```

Verification:

```bash
kubectl exec -n vault vault-0 -- sh -c \
  'export VAULT_ADDR=http://127.0.0.1:8200 VAULT_TOKEN=root && \
   vault read auth/kubernetes/role/python-app-role'
```

```text
bound_service_account_names      [python-lab11-devops-info-python-sa]
bound_service_account_namespaces [lab11]
policies                         [python-app]
ttl                              24h
```

### Vault injector annotations

The deployment now includes:

```yaml
annotations:
  vault.hashicorp.com/agent-inject: "true"
  vault.hashicorp.com/auth-type: "kubernetes"
  vault.hashicorp.com/auth-path: "auth/kubernetes"
  vault.hashicorp.com/role: "python-app-role"
  vault.hashicorp.com/agent-inject-secret-config: "secret/data/python-app/config"
  vault.hashicorp.com/agent-inject-file-config: "app.env"
  vault.hashicorp.com/agent-inject-template-config: |
    {{- with secret "secret/data/python-app/config" -}}
    APP_USERNAME={{ .Data.data.APP_USERNAME }}
    APP_PASSWORD={{ .Data.data.APP_PASSWORD }}
    APP_API_KEY={{ .Data.data.APP_API_KEY }}
    {{- end -}}
  vault.hashicorp.com/agent-inject-command-config: 'sh -c "chmod 0440 /vault/secrets/app.env"'
```

### Proof of injection

After Vault auth was configured, the application deployment was restarted so the new pod would pass through the mutating webhook.

Injected pod verification:

```bash
kubectl get pod <new-pod> -n lab11 \
  -o jsonpath='{.metadata.annotations.vault\.hashicorp\.com/agent-inject-status}'
```

Observed output:

```text
injected
```

Injected containers:

```bash
kubectl get pod <new-pod> -n lab11 \
  -o jsonpath='{.spec.initContainers[*].name} {.spec.containers[*].name}'
```

Observed output:

```text
vault-agent-init devops-info-python vault-agent
```

Proof that the rendered file exists inside the application container:

```bash
kubectl exec -n lab11 <new-pod> -c devops-info-python -- sh -c \
  'ls -l /vault/secrets && sed "s/=.*$/=<redacted>/" /vault/secrets/app.env'
```

Observed output:

```text
total 4
-r--r----- 1 100 1000 77 Apr  9 17:37 app.env
APP_USERNAME=<redacted>
APP_PASSWORD=<redacted>
APP_API_KEY=<redacted>
```

### Sidecar injection pattern

The injector mutates the pod at admission time and adds:

- an init container (`vault-agent-init`) to authenticate and render initial files
- a sidecar (`vault-agent`) to continue running with Vault Agent
- an in-memory shared volume mounted at `/vault/secrets`

This keeps secrets out of the container image and out of Git, while still making them available to the app at runtime.

## 5. Bonus Task — Vault Agent Templates

### Template annotation implementation

The bonus requirement was implemented with `vault.hashicorp.com/agent-inject-template-config` and a named helper in [`k8s/python-app/templates/_helpers.tpl`](/Users/mazzz3r/study/DevOps/k8s/python-app/templates/_helpers.tpl):

```yaml
{{- define "python-app.vaultTemplate" -}}
{{`{{- with secret "`}}{{ .Values.vault.secretPath }}{{`" -}}`}}
APP_USERNAME={{`{{ .Data.data.APP_USERNAME }}`}}
APP_PASSWORD={{`{{ .Data.data.APP_PASSWORD }}`}}
APP_API_KEY={{`{{ .Data.data.APP_API_KEY }}`}}
{{`{{- end -}}`}}
{{- end -}}
```

This renders several Vault values into one `.env`-style file instead of generating separate files for each key.

### Named template for common environment variables

Also added a DRY helper for regular environment variables:

```yaml
{{- define "python-app.envVars" -}}
{{- range $name, $value := .Values.env }}
- name: {{ $name }}
  value: {{ $value | quote }}
{{- end }}
{{- end -}}
```

Used in the deployment as:

```yaml
env:
  {{- include "python-app.envVars" . | nindent 12 }}
```

### Dynamic secret rotation notes

- Vault Agent keeps running in the sidecar and can re-render destination files when secret data changes.
- For renewable or leased secrets, the agent renews leases when possible and rewrites templates as needed.
- For static KV secrets like this lab, the most visible update path in a simple demo is to change the secret in Vault and let the agent refresh or restart the pod to force a fresh render.
- The injected file approach is better for rotation than plain environment variables because file contents can change without rebuilding the image.

### `agent-inject-command` explanation

- `vault.hashicorp.com/agent-inject-command-*` runs after Vault Agent renders the target file.
- In this lab it is used to tighten file permissions on `/vault/secrets/app.env`.
- The final command was set to `chmod 0440` so the non-root app container can still read the file via group permissions.

## 6. Security Analysis

### Kubernetes Secrets vs Vault

Kubernetes Secrets:

- Easy to use and built into the platform.
- Good for simple workloads or small clusters.
- Still depend heavily on RBAC and cluster-side protection.
- Weak choice for centralized auditing, rotation workflows, or multi-platform secret reuse.

Vault:

- Centralizes secret storage, access control, auditability, and rotation workflows.
- Supports dynamic secrets, scoped policies, and workload identity-based access.
- Better fit for production systems with multiple apps or stronger compliance requirements.
- Adds operational complexity compared with native Kubernetes Secrets.

### When to use each

- Use Kubernetes Secrets when you need a small, native, low-friction solution and the cluster already has good RBAC plus encryption at rest.
- Use Vault when you need stronger separation of duties, secret leasing/rotation, cross-platform secret delivery, or auditable access policies.

### Production recommendations

- Never commit real secrets to Git.
- Enable `etcd` encryption at rest.
- Restrict secret access with RBAC and namespace boundaries.
- Prefer dedicated service accounts per workload.
- Use an external secret manager such as Vault for higher-value credentials.
- Replace Vault dev mode with HA storage, TLS, proper auth audiences, and audit logging in production.
