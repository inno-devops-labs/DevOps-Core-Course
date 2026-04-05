# Lab 11 - Kubernetes Secrets and HashiCorp Vault

## 1. Kubernetes Secrets

### 1.1 Create secret with kubectl (imperative)

```bash
kubectl create secret generic app-credentials \
  --from-literal=username=demo-user \
  --from-literal=password=demo-pass
```

### 1.2 View secret and decode values

```bash
kubectl get secret app-credentials -o yaml
kubectl get secret app-credentials -o jsonpath='{.data.username}' | base64 -d && echo
kubectl get secret app-credentials -o jsonpath='{.data.password}' | base64 -d && echo
```

Example output (sanitized):

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: app-credentials
type: Opaque
data:
  username: ZGVtby11c2Vy
  password: ZGVtby1wYXNz
```

### 1.3 Encoding vs encryption

- Base64 in Kubernetes Secret `data` is encoding only, not cryptographic protection.
- Anyone with API read access to Secrets can decode values.
- Encrypting Secret values at rest requires etcd encryption configuration on the cluster control plane.

### 1.4 Security implications

- Kubernetes Secrets are **not encrypted at rest by default** in many cluster setups unless explicitly enabled.
- Enable etcd encryption at rest for production clusters.
- Combine with strict RBAC, namespace isolation, and audit logging.

---

## 2. Helm Secret Integration

### 2.1 Chart changes

Added file:

- `k8s/devops-python/templates/secrets.yaml`

Updated files:

- `k8s/devops-python/values.yaml`
- `k8s/devops-python/templates/deployment.yaml`
- `k8s/devops-python/templates/_helpers.tpl`
- `k8s/devops-python/values-dev.yaml`
- `k8s/devops-python/values-prod.yaml`

### 2.2 Secret template

`templates/secrets.yaml` uses `stringData` and placeholders from values:

- `secrets.username`
- `secrets.password`

Secret name uses helper template:

- `{{ include "devops-python.secretName" . }}`

### 2.3 Secret consumption in deployment

Deployment consumes all secret keys via `envFrom.secretRef`:

```yaml
envFrom:
  - secretRef:
      name: <release>-devops-python-credentials
```

Common non-secret env vars are provided via named template (`bonus` requirement):

- `APP_ENV`
- `LOG_LEVEL`

### 2.4 Verification commands

```bash
helm template lab11-release k8s/devops-python -f k8s/devops-python/values-dev.yaml
helm upgrade --install lab11-release k8s/devops-python -f k8s/devops-python/values-dev.yaml
kubectl get secret lab11-release-devops-python-credentials
kubectl exec deploy/lab11-release-devops-python -- printenv | grep -E 'username|password|APP_ENV|LOG_LEVEL'
```

Check that `kubectl describe pod` does not print secret values:

```bash
kubectl describe pod <pod-name>
```

Expected behavior:

- Secret references are shown.
- Secret values are not printed in plain text.

---

## 3. Resource Management

### 3.1 Configured requests and limits

`values.yaml`:

```yaml
resources:
  requests:
    cpu: 100m
    memory: 128Mi
  limits:
    cpu: 200m
    memory: 256Mi
```

`values-dev.yaml` (lighter):

```yaml
resources:
  requests:
    cpu: 50m
    memory: 64Mi
  limits:
    cpu: 100m
    memory: 128Mi
```

`values-prod.yaml` (heavier):

```yaml
resources:
  requests:
    cpu: 200m
    memory: 256Mi
  limits:
    cpu: 500m
    memory: 512Mi
```

### 3.2 Requests vs limits

- Requests: guaranteed baseline used by scheduler.
- Limits: maximum allowed before throttling (CPU) or OOM kill (memory).
- Choose values from real metrics (p95 usage, startup spikes, and headroom).

---

## 4. Vault Integration

### 4.1 Install Vault via Helm (dev mode)

```bash
helm repo add hashicorp https://helm.releases.hashicorp.com
helm repo update
helm upgrade --install vault hashicorp/vault \
  --set "server.dev.enabled=true" \
  --set "injector.enabled=true"
kubectl get pods
```

Expected pods include `vault-0` and `vault-agent-injector-*` in `Running` state.

### 4.2 Configure KV and application secret

```bash
kubectl exec -it vault-0 -- sh
vault secrets enable -path=secret kv-v2
vault kv put secret/myapp/config username="vault-user" password="vault-pass"
vault kv get secret/myapp/config
```

### 4.3 Configure Kubernetes auth, policy, and role

```bash
vault auth enable kubernetes

SA_NAME="lab11-release-devops-python"
SA_NS="default"
TOKEN_REVIEW_JWT=$(cat /var/run/secrets/kubernetes.io/serviceaccount/token)
KUBE_HOST="https://${KUBERNETES_PORT_443_TCP_ADDR}:443"
KUBE_CA_CERT=@/var/run/secrets/kubernetes.io/serviceaccount/ca.crt

vault write auth/kubernetes/config \
  token_reviewer_jwt="$TOKEN_REVIEW_JWT" \
  kubernetes_host="$KUBE_HOST" \
  kubernetes_ca_cert="$KUBE_CA_CERT"
```

Policy (`myapp-policy.hcl`):

```hcl
path "secret/data/myapp/config" {
  capabilities = ["read"]
}
```

```bash
vault policy write myapp-policy myapp-policy.hcl
vault write auth/kubernetes/role/devops-python-role \
  bound_service_account_names="$SA_NAME" \
  bound_service_account_namespaces="$SA_NS" \
  policies="myapp-policy" \
  ttl="1h"
```

### 4.4 Enable agent injection in Helm values

Use overrides during deploy:

```bash
helm upgrade --install lab11-release k8s/devops-python \
  -f k8s/devops-python/values-dev.yaml \
  --set vault.enabled=true \
  --set vault.role=devops-python-role \
  --set vault.secretPath=secret/data/myapp/config \
  --set serviceAccount.create=true
```

### 4.5 Verify injection path in pod

```bash
kubectl get pod -l app.kubernetes.io/instance=lab11-release
kubectl exec <pod-name> -- ls -la /vault/secrets
kubectl exec <pod-name> -- cat /vault/secrets/app-env
```

Expected files:

- `/vault/secrets/config`
- `/vault/secrets/app-env`

This is the sidecar injection pattern: Vault Agent (injected sidecar/init container) authenticates using pod service account, fetches secret from Vault, and writes it to shared in-memory volume mounted to the application container.

---

## 5. Bonus: Vault Agent Templates and DRY Env Template

### 5.1 Template annotation implementation

In deployment template:

- `vault.hashicorp.com/agent-inject-template-<name>` renders a `.env` style file.
- Multiple secret keys are rendered in one file:
  - `APP_USERNAME={{ .Data.data.username }}`
  - `APP_PASSWORD={{ .Data.data.password }}`

### 5.2 Dynamic secret rotation behavior

- Vault Agent periodically renews tokens/leases and re-renders templated files when source secrets change.
- For dynamic secret backends, rotation is automatic by lease renewal/reauth.
- `vault.hashicorp.com/agent-inject-command-<name>` can trigger a command after template rewrite (for example app reload).

### 5.3 Named template in `_helpers.tpl`

Implemented helper:

- `devops-python.envVars`

Used in deployment:

```yaml
env:
  {{- include "devops-python.envVars" . | nindent 12 }}
```

This keeps env block DRY and reusable.

---

## 6. Security Analysis

### Kubernetes Secrets vs Vault

- Kubernetes Secrets:
  - Simple and native.
  - Good for low-complexity workloads.
  - Needs etcd encryption + strong RBAC for production-grade posture.

- Vault:
  - Centralized secret manager with policies, auditing, rotation, and dynamic secrets.
  - Better for multi-team/multi-env production systems and compliance requirements.

### Production recommendations

- Never commit real credentials to Git.
- Keep placeholders in `values.yaml`; pass real values via CI/CD secret store or external manager.
- Enable etcd encryption at rest.
- Apply least-privilege RBAC (`get` only specific secrets).
- Use Vault with Kubernetes auth for sensitive or frequently rotated credentials.
- Enable secret access audit logs and periodic policy reviews.

---

## 7. Validation Status in This Repository

Implemented in code:

- Kubernetes Secret template and secret injection into pod env.
- Resource requests/limits in values files.
- Vault injector annotations, role/path wiring, and templated file rendering.
- Bonus named Helm template for common environment variables.

Note:

- This editing session could not execute your WSL binaries (`wsl ...` returned `E_ACCESSDENIED`), so live cluster command outputs are provided as runnable commands and expected/sanitized examples for your environment.
