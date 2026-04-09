# Lab 11 — Kubernetes Secrets & HashiCorp Vault

## 1. Kubernetes Secrets Fundamentals

### 1.1 Secret creation (imperative `kubectl create secret`)

```bash
kubectl create secret generic app-credentials \
  --from-literal=username=lab11-user \
  --from-literal=password=lab11-pass \
  --dry-run=client -o yaml
```

Output:

```yaml
apiVersion: v1
data:
  password: bGFiMTEtcGFzcw==
  username: bGFiMTEtdXNlcg==
kind: Secret
metadata:
  creationTimestamp: null
  name: app-credentials
```

### 1.2 Decoding base64 values

```powershell
$manifest = kubectl create secret generic app-credentials --from-literal=username=lab11-user --from-literal=password=lab11-pass --dry-run=client -o json | ConvertFrom-Json
[System.Text.Encoding]::UTF8.GetString([System.Convert]::FromBase64String($manifest.data.username))
[System.Text.Encoding]::UTF8.GetString([System.Convert]::FromBase64String($manifest.data.password))
```

Output:

```text
lab11-user
lab11-pass
```

### 1.3 Encoding vs encryption

- Base64 in Secret `data` is only encoding (readability/transport format), not cryptographic protection.
- If someone has API access to read Secrets, they can decode values immediately.

### 1.4 Security implications

- Kubernetes Secrets are not encrypted at rest by default in etcd unless encryption-at-rest is explicitly configured by cluster admin.
- etcd encryption should be enabled in production to reduce risk from etcd snapshots/backups or disk compromise.
- RBAC must still restrict who can `get/list/watch` Secrets.

---

## 2. Helm Secret Integration

### 2.1 Chart changes

Added/updated files in chart `k8s/devops-info-service`:

- `templates/secrets.yaml` — Secret resource with `stringData` from values.
- `templates/serviceaccount.yaml` — ServiceAccount for Vault Kubernetes auth binding.
- `templates/deployment.yaml` — secret injection (`envFrom.secretRef`), named `env` template include, Vault annotations.
- `templates/_helpers.tpl` — added helpers:
  - `devops-info-service.secretName`
  - `devops-info-service.serviceAccountName`
  - `devops-info-service.commonEnv` (bonus named template)
- `values.yaml`, `values-dev.yaml`, `values-prod.yaml` — added secret/serviceAccount/vault/env config.

### 2.2 Secret consumption in Deployment

Deployment uses:

- `envFrom.secretRef` for all Secret keys.
- `env` from named helper template (`APP_ENV`, `LOG_LEVEL`).

Rendered proof (`helm template ... -f values-prod.yaml`):

```yaml
env:
  - name: APP_ENV
    value: "prod"
  - name: LOG_LEVEL
    value: "info"
envFrom:
  - secretRef:
      name: lab11-devops-info-service-secret
```

### 2.3 Resource requests/limits

Configured via values and rendered into Deployment:

```yaml
resources:
  limits:
    cpu: 500m
    memory: 512Mi
  requests:
    cpu: 200m
    memory: 256Mi
```

Requests reserve guaranteed baseline resources for scheduling.
Limits cap maximum usage to protect node stability.

### 2.4 Validation

```bash
helm lint k8s/devops-info-service
```

Output:

```text
==> Linting k8s/devops-info-service
[INFO] Chart.yaml: icon is recommended
1 chart(s) linted, 0 chart(s) failed
```

---

## 3. Vault Integration

## 3.1 Helm/Vault status in this environment

`kubectl` context exists (`kind-lab9`), but cluster API is currently unreachable:

```text
Unable to connect to the server: dial tcp 127.0.0.1:55886: connectex: No connection could be made because the target machine actively refused it.
```

Because of this, Vault pods cannot be installed/verified in this session.

### 3.2 Implemented app-side Vault integration in chart

When `vault.enabled=true`, Deployment renders annotations:

```yaml
vault.hashicorp.com/agent-inject: "true"
vault.hashicorp.com/role: "devops-info-role"
vault.hashicorp.com/agent-inject-secret-config: "secret/data/devops-info/config"
vault.hashicorp.com/secret-volume-path: "/vault/secrets"
vault.hashicorp.com/agent-inject-template-config: |
  {{- with secret "secret/data/devops-info/config" -}}
  APP_USERNAME={{ .Data.data.username }}
  APP_PASSWORD={{ .Data.data.password }}
  API_KEY={{ .Data.data.api_key }}
  {{- end -}}
```

Also ServiceAccount is created and attached to the Pod:

```yaml
serviceAccountName: lab11-devops-info-service
automountServiceAccountToken: true
```

This is required for Vault Kubernetes auth role binding.

### 3.3 Vault setup commands to run on a live cluster

```bash
helm repo add hashicorp https://helm.releases.hashicorp.com
helm repo update
helm install vault hashicorp/vault \
  --set "server.dev.enabled=true" \
  --set "injector.enabled=true"

kubectl get pods -l app.kubernetes.io/name=vault

kubectl exec -it vault-0 -- /bin/sh
vault secrets enable -path=secret kv-v2
vault kv put secret/devops-info/config username="vault-user" password="vault-pass" api_key="vault-api-key"

vault auth enable kubernetes
vault write auth/kubernetes/config \
  kubernetes_host="https://$KUBERNETES_PORT_443_TCP_ADDR:443"

cat <<EOF > /tmp/devops-info-policy.hcl
path "secret/data/devops-info/config" {
  capabilities = ["read"]
}
EOF
vault policy write devops-info-policy /tmp/devops-info-policy.hcl

vault write auth/kubernetes/role/devops-info-role \
  bound_service_account_names="lab11-devops-info-service" \
  bound_service_account_namespaces="default" \
  policies="devops-info-policy" \
  ttl="24h"
```

---

## 4. Bonus — Templates and Rotation

### 4.1 Vault Agent template annotation

Implemented with `vault.hashicorp.com/agent-inject-template-config`.
Secrets are rendered into one file in `.env` style (`APP_USERNAME`, `APP_PASSWORD`, `API_KEY`).

### 4.2 Dynamic secret rotation behavior

- Vault Agent periodically renews tokens/leases and refreshes rendered files when source secrets change.
- For static KV secrets, file re-render depends on template polling/render cycle and secret updates in Vault.
- `vault.hashicorp.com/agent-inject-command` can run a command after re-render (for example, SIGHUP app or config reload script).

### 4.3 Named template in `_helpers.tpl` (DRY)

Implemented:

```yaml
{{- define "devops-info-service.commonEnv" -}}
- name: APP_ENV
  value: {{ .Values.env.appEnv | quote }}
- name: LOG_LEVEL
  value: {{ .Values.env.logLevel | quote }}
{{- end }}
```

Used in Deployment:

```yaml
env:
  {{- include "devops-info-service.commonEnv" . | nindent 12 }}
```

This removes duplication and keeps environment variable mapping centralized.

---

## 5. Security Analysis

### 5.1 Kubernetes Secrets vs Vault

- Kubernetes Secrets:
  - Native, simple, integrated with Kubernetes RBAC.
  - Good for low-complexity setups.
  - Requires etcd encryption + strict RBAC for production hardening.
- Vault:
  - Centralized secret management, policy-based access, dynamic secrets, rotation workflows.
  - Better fit for production, multi-service, compliance-heavy environments.

### 5.2 When to use each

- Use K8s Secrets for simple internal apps and non-critical environments.
- Use Vault for production systems, dynamic credentials, auditability, and secret lifecycle automation.

### 5.3 Production recommendations

- Enable etcd encryption at rest.
- Restrict Secret access via RBAC and namespace boundaries.
- Avoid storing real secrets in Git; use placeholders in values files.
- Use Vault with Kubernetes auth and least-privilege policies.
- Add secret rotation/reload strategy (agent command + app reload endpoint/signal).

---

## 6. Evidence Summary

- Helm installed: `v4.1.4`.
- Chart linted successfully.
- Secret + ServiceAccount + Vault annotations rendered correctly.
- Kubernetes runtime verification (pods/exec) blocked in this session due offline/unreachable cluster API.
