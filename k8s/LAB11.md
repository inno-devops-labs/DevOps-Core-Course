# Lab 11 Report - Kubernetes Secrets and HashiCorp Vault

## 1. Kubernetes Secrets

### 1.1 Create Secret via kubectl

```bash
kubectl create secret generic app-credentials \
  --from-literal=username=app-user \
  --from-literal=password='S3cr3t-P@ss'
```

Expected output:

```text
secret/app-credentials created
```

### 1.2 View Secret YAML

```bash
kubectl get secret app-credentials -o yaml
```

Example output (sanitized):

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: app-credentials
type: Opaque
data:
  username: YXBwLXVzZXI=
  password: UzNjcjN0LVBAccNz
```

### 1.3 Decode Secret Values

```bash
echo 'YXBwLXVzZXI=' | base64 -d; echo
echo 'UzNjcjN0LVBAccNz' | base64 -d; echo
```

### 1.4 Encoding vs Encryption

- Base64 is encoding, not encryption. It only transforms representation and is reversible without a key.
- Kubernetes Secret values in manifest/API responses are base64-encoded for transport format compatibility.
- Real protection requires encryption at rest, transport security, strict RBAC, and external secret systems for high-security workloads.

### 1.5 Are Secrets encrypted at rest by default?

- Not guaranteed by default in all clusters.
- In production, enable etcd encryption at rest using an EncryptionConfiguration on the API server.
- Also restrict access with RBAC and audit secret access.

---

## 2. Helm Secret Integration

Implemented in chart: k8s/devops-info

### 2.1 Chart structure changes

```text
k8s/devops-info/
  values.yaml
  templates/
    _helpers.tpl
    deployment.yaml
    secrets.yaml
    serviceaccount.yaml
```

### 2.2 Secret template

Created: `templates/secrets.yaml`

- Uses `apiVersion: v1`, `kind: Secret`, `type: Opaque`
- Uses `stringData` so values from `values.yaml` are auto-encoded by Kubernetes
- Secret name is templated using helper `devops-info.secretName`

### 2.3 Values for secret and vault

Added to `values.yaml`:

- `secret.enabled`, `secret.name`, `secret.data.username`, `secret.data.password`
- `serviceAccount.create`, `serviceAccount.name`
- `vault.enabled`, `vault.role`, `vault.secretPath`, `vault.fileName`, `vault.template`, `vault.command`

### 2.4 Secret consumption in Deployment

`deployment.yaml` now consumes secret values with `envFrom.secretRef`:

```yaml
envFrom:
  - secretRef:
      name: {{ include "devops-info.secretName" . }}
```

This exposes each key from the Secret as environment variables inside the container.

### 2.5 Verify secret injection

```bash
# Deploy/upgrade chart
helm upgrade --install devops-info k8s/devops-info

# Check secret exists
kubectl get secret

# Check pod env variable names (do not print actual values in report)
POD=$(kubectl get pods -l app.kubernetes.io/name=devops-info -o jsonpath='{.items[0].metadata.name}')
kubectl exec "$POD" -- sh -c 'env | grep -E "^(username|password)=" | cut -d= -f1'
```

Expected output should show only variable names:

```text
username
password
```

Security check:

```bash
kubectl describe pod "$POD"
```

- Secret values are not printed in clear text in pod describe output.
- Secret references can appear, but not actual values.

---

## 3. Resource Management

### 3.1 Configured resources

In `values.yaml`:

```yaml
resources:
  requests:
    cpu: 100m
    memory: 128Mi
  limits:
    cpu: 250m
    memory: 256Mi
```

### 3.2 Requests vs Limits

- Requests: scheduler guarantee used for bin-packing and QoS decisions.
- Limits: hard upper bound enforced by kernel cgroups.
- If memory usage exceeds limit, container can be OOM-killed.
- CPU over limit is throttled.

### 3.3 How to choose values

- Start from observed baseline (p50/p95 usage under normal and peak load).
- Set requests near steady-state plus safety margin.
- Set limits to protect node stability while allowing realistic burst.
- Revisit values after load tests and production telemetry.

---

## 4. Vault Integration

### 4.1 Install Vault with Helm (dev mode)

```bash
helm repo add hashicorp https://helm.releases.hashicorp.com
helm repo update

helm upgrade --install vault hashicorp/vault \
  --set 'server.dev.enabled=true' \
  --set 'injector.enabled=true'
```

Verification:

```bash
kubectl get pods -l app.kubernetes.io/name=vault
```

Expected: vault server and injector pods in Running state.

### 4.2 Configure Vault KV and secret

```bash
kubectl exec -it vault-0 -- sh

vault secrets enable -path=secret kv-v2
vault kv put secret/myapp/config username='vault-user' password='vault-pass'
```

### 4.3 Configure Kubernetes auth, policy, and role

Policy (`devops-info-policy.hcl`):

```hcl
path "secret/data/myapp/config" {
  capabilities = ["read"]
}
```

Apply policy and role:

```bash
vault auth enable kubernetes

vault policy write devops-info-policy devops-info-policy.hcl

vault write auth/kubernetes/role/devops-info-role \
  bound_service_account_names=devops-info \
  bound_service_account_namespaces=default \
  policies=devops-info-policy \
  ttl=1h
```

### 4.4 Vault Agent Injector in chart

Implemented via helper template and deployment annotations when `vault.enabled=true`.

Current chart uses:

- `vault.hashicorp.com/agent-inject: "true"`
- `vault.hashicorp.com/role: "devops-info-role"`
- `vault.hashicorp.com/agent-inject-secret-config: "secret/data/myapp/config"`
- `vault.hashicorp.com/agent-inject-template-config: | ...`

### 4.5 Verify file-based injection

```bash
helm upgrade --install devops-info k8s/devops-info \
  --set vault.enabled=true

POD=$(kubectl get pods -l app.kubernetes.io/name=devops-info -o jsonpath='{.items[0].metadata.name}')

kubectl exec "$POD" -- ls -la /vault/secrets
kubectl exec "$POD" -- cat /vault/secrets/config
```

Expected:

- `/vault/secrets/config` exists.
- File contains rendered key-value content from Vault template.

### 4.6 Sidecar injection pattern explanation

- Mutating webhook adds Vault Agent container and shared volume to pod.
- Agent authenticates using pod service account JWT through Vault Kubernetes auth method.
- Agent retrieves secret, renders template, writes file in shared volume.
- App container reads file without embedding static credentials in image or chart values.

---

## 5. Security Analysis

### 5.1 Kubernetes Secrets vs Vault

- Kubernetes Secret:
  - Native and simple.
  - Good for low-complexity internal workloads.
  - Requires strict RBAC and etcd encryption for stronger security.

- HashiCorp Vault:
  - Centralized secret lifecycle and policy model.
  - Supports dynamic secrets, lease/TTL, revocation, rotation workflows.
  - Better fit for production-grade multi-service or compliance-heavy environments.

### 5.2 When to use which

- Use Kubernetes Secrets for small projects, bootstrap config, or low-risk non-critical credentials.
- Use Vault for production environments requiring auditability, rotation, short-lived credentials, and centralized governance.

### 5.3 Production recommendations

- Enable etcd encryption at rest.
- Apply least-privilege RBAC for Secret reads.
- Avoid committing real secrets to Git.
- Prefer external secret manager (Vault or cloud managed equivalent).
- Rotate credentials regularly and monitor access logs.

---

## Bonus - Vault Agent Templates

### B1. Template annotation implementation

Implemented in chart using:

```yaml
vault.hashicorp.com/agent-inject-template-config: |
  {{- with secret "secret/data/myapp/config" -}}
  APP_USERNAME={{ .Data.data.username }}
  APP_PASSWORD={{ .Data.data.password }}
  {{- end -}}
```

This renders multiple values into one file (`/vault/secrets/config`) in env-style format.

### B2. Dynamic refresh mechanism

- Vault Agent renews token/leases where applicable and re-renders templates on data updates.
- File update events can trigger in-container reload logic.
- `vault.hashicorp.com/agent-inject-command` can run a command after template re-render (for example: send SIGHUP to app).

### B3. Named template for environment variables (DRY)

Implemented helper in `_helpers.tpl`:

```yaml
{{- define "devops-info.envVars" -}}
{{- range .Values.env }}
- name: {{ .name }}
  value: {{ .value | quote }}
{{- end }}
{{- end -}}
```

Deployment uses:

```yaml
env:
  {{- include "devops-info.envVars" . | nindent 12 }}
```

Benefit: one reusable source of env rendering logic, easier maintenance, less duplication.

---

## Final Checklist Mapping

- [x] Kubernetes Secret created/viewed/decoded commands documented.
- [x] Base64 vs encryption explained.
- [x] Helm secret template added and wired to deployment.
- [x] Resource requests/limits documented and present.
- [x] Vault install/config/auth/role/policy steps documented.
- [x] Vault injection and sidecar pattern documented.
- [x] Bonus template annotation and named template documented.

## Notes

- Real cluster command output can differ by namespace, release name, and chart version.
- Keep placeholders in Git and pass real values via `--set`, `-f`, CI secrets, or Vault only.
