# Lab 11 — Kubernetes Secrets & HashiCorp Vault

## 1. Kubernetes Secrets

### Create secret with `kubectl`
```bash
kubectl create secret generic app-credentials \
  --from-literal=username=demo-user \
  --from-literal=password='demo-password'
```

### View secret YAML
```bash
kubectl get secret app-credentials -o yaml
```

Actual output from this run:
```yaml
apiVersion: v1
data:
  password: ZGVtby1wYXNzd29yZA==
  username: ZGVtby11c2Vy
kind: Secret
metadata:
  creationTimestamp: "2026-04-09T18:18:18Z"
  name: app-credentials
  namespace: default
  resourceVersion: "57625"
  uid: ec9e3112-c681-4215-a38a-401dc82551cc
type: Opaque
```

### Decode values
```bash
kubectl get secret app-credentials -o jsonpath='{.data.username}' | base64 -d
kubectl get secret app-credentials -o jsonpath='{.data.password}' | base64 -d
```

Actual output:
```text
demo-user
demo-password
```

### Encoding vs encryption
- Base64 is **encoding** (reversible representation), not cryptographic protection.
- Kubernetes Secrets are not strongly protected unless cluster security controls are configured.

### Security implication
- Secrets are accessible to subjects with relevant RBAC/API permissions.
- Enable **etcd encryption at rest** in production to encrypt secret payloads in storage backend.

---

## 2. Helm Secret Integration

Implemented in chart `k8s/devops-info-service`:

- `templates/secrets.yaml` creates an Opaque Secret from values.
- `values.yaml` contains placeholder secret defaults:
  - `secrets.data.username`
  - `secrets.data.password`
- `templates/deployment.yaml` consumes secret via:
  - `envFrom -> secretRef`

### Chart structure (relevant)
```text
k8s/devops-info-service/
  templates/
    deployment.yaml
    secrets.yaml
    serviceaccount.yaml
    _helpers.tpl
```

### Render check
```bash
helm template devops-release k8s/devops-info-service | grep -n "kind: Secret\|secretRef\|envFrom"
```

Actual output:
```text
16:kind: Secret
83:      serviceAccountName: devops-release-devops-info-service
106:          envFrom:
107:            - secretRef:
```

### Verify env variables in pod (without printing values)
```bash
POD=$(kubectl get pod -l app.kubernetes.io/instance=devops-release -o jsonpath='{.items[0].metadata.name}')
kubectl exec "$POD" -- sh -c 'printenv | grep -E "^(username|password|APP_ENV|LOG_LEVEL)=" | sed "s/=.*$/=<redacted>/"'
```

Actual output:
```text
LOG_LEVEL=<redacted>
username=<redacted>
password=<redacted>
APP_ENV=<redacted>
```

Secret is injected as env vars without exposing values in this report.

---

## 3. Resource Management

Resource configuration is kept in values and used by Deployment:

```yaml
resources:
  requests:
    memory: "64Mi"
    cpu: "100m"
  limits:
    memory: "128Mi"
    cpu: "200m"
```

- **requests**: guaranteed baseline for scheduler placement.
- **limits**: hard cap; protects node stability from resource overconsumption.

How to choose values:
1. Start with conservative defaults.
2. Observe real usage (`kubectl top pods`, load tests).
3. Increase requests/limits based on measured steady-state and peak behavior.

---

## 4. Vault Integration

### Install Vault with injector
```bash
helm repo add hashicorp https://helm.releases.hashicorp.com
helm repo update
helm upgrade --install vault hashicorp/vault \
  --set "server.dev.enabled=true" \
  --set "injector.enabled=true"
```

### Verify pods
```bash
kubectl get pods -l app.kubernetes.io/name=vault
kubectl get pods -l app.kubernetes.io/name=vault-agent-injector
```

Actual output:
```text
NAME      READY   STATUS    RESTARTS   AGE
vault-0   1/1     Running   0          36s

NAME                                    READY   STATUS    RESTARTS   AGE
vault-agent-injector-848dd747d7-8m7jl   1/1     Running   0          36s
```

### Vault configuration (policy + role)
Commands executed:
```bash
kubectl exec vault-0 -- sh -lc 'export VAULT_ADDR=http://127.0.0.1:8200 VAULT_TOKEN=root && vault kv put secret/myapp/config username=demo-user password=demo-password api_key=demo-api-key'
kubectl exec vault-0 -- sh -lc 'export VAULT_ADDR=http://127.0.0.1:8200 VAULT_TOKEN=root && vault auth enable kubernetes'
kubectl exec vault-0 -- sh -lc 'export VAULT_ADDR=http://127.0.0.1:8200 VAULT_TOKEN=root && vault write auth/kubernetes/config kubernetes_host="https://kubernetes.default.svc:443" token_reviewer_jwt="$(cat /var/run/secrets/kubernetes.io/serviceaccount/token)" kubernetes_ca_cert=@/var/run/secrets/kubernetes.io/serviceaccount/ca.crt'
```

Policy (sanitized):
```hcl
path "secret/data/myapp/config" {
  capabilities = ["read"]
}
```

Role example:
```bash
kubectl exec vault-0 -- sh -lc 'export VAULT_ADDR=http://127.0.0.1:8200 VAULT_TOKEN=root && vault write auth/kubernetes/role/devops-info-role \
  bound_service_account_names="devops-release-devops-info-service" \
  bound_service_account_namespaces="default" \
  policies="devops-info-read" \
  ttl="24h"'
```

Role readback (actual):
```text
bound_service_account_names                 [devops-release-devops-info-service]
bound_service_account_namespaces            [default]
policies                                    [devops-info-read]
token_ttl                                   24h
ttl                                         24h
```

### Chart-side Vault injection
Implemented in `templates/deployment.yaml` (enabled by `.Values.vault.enabled`):
- `vault.hashicorp.com/agent-inject: "true"`
- `vault.hashicorp.com/role`
- `vault.hashicorp.com/agent-inject-secret-config`
- `vault.hashicorp.com/agent-inject-template-config`
- optional `vault.hashicorp.com/agent-inject-command-config`

Service account is managed by `templates/serviceaccount.yaml` and attached in Deployment via `serviceAccountName`.

### Verify secret file in pod
```bash
kubectl exec "$POD" -- ls -la /vault/secrets
kubectl exec "$POD" -- cat /vault/secrets/config
```

Actual output:
```text
total 8
drwxrwxrwt 2 root root      60 Apr  9 18:19 .
drwxr-xr-x 3 root root    4096 Apr  9 18:19 ..
-rw-r--r-- 1  100 appuser   80 Apr  9 18:19 config

DATABASE_USERNAME=demo-user
DATABASE_PASSWORD=demo-password
API_KEY=demo-api-key
```

This validates sidecar injection pattern: Vault Agent (injected sidecar/init) authenticates with Kubernetes service account, fetches Vault data, and writes rendered files into shared volume for the app container.

---

## 5. Security Analysis

### Kubernetes Secrets vs Vault
- **Kubernetes Secrets**
  - Native and simple.
  - Good for low-complexity and small deployments.
  - Requires strong RBAC and etcd encryption-at-rest for safer production usage.
- **Vault**
  - Externalized, centralized secret management.
  - Stronger access controls, dynamic secrets, rotation workflows, auditability.
  - Better fit for multi-service and production-grade environments.

### When to use each
- Use Kubernetes Secrets for simple internal scenarios where operational overhead must stay minimal.
- Use Vault when you need centralized policy, secret lifecycle control, rotation, and stronger compliance posture.

### Production recommendations
1. Never commit real credentials to Git.
2. Use placeholders in `values.yaml`, pass real values at deploy time.
3. Enable etcd encryption, strict RBAC, and namespace isolation.
4. Prefer external secret managers (Vault) for critical systems.

---

## Bonus — Vault Agent Templates + Named Helm Template

### Implemented
- Vault template annotation (`agent-inject-template-config`) renders multiple keys in one file (`/vault/secrets/config`).
- Optional `vault.hashicorp.com/agent-inject-command-config` is configurable with `.Values.vault.injectCommand`.
- Named Helm template in `_helpers.tpl`:
  - `devops-info-service.commonEnv`
  - included in Deployment env block via `include`.

### Secret refresh mechanism (research summary)
- Vault Agent periodically renews/reauthenticates and refreshes rendered templates.
- On value change or lease renewal, rendered file is updated.
- `agent-inject-command-*` can trigger an in-container command after template rewrite (for reload hooks).

### Benefits
- DRY chart design (shared env template).
- Single rendered secret file for app consumption.
- Cleaner separation of static chart config and runtime secret material.
