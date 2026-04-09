# Lab 11 — Kubernetes Secrets & HashiCorp Vault

Documentation with evidence for all tasks.

---

## Task 1 — Kubernetes Secrets Fundamentals

### 1.1 Creating Secret

```bash
kubectl create secret generic app-credentials \
  --from-literal=username=admin \
  --from-literal=password=supersecret123
```

Output:
```
secret/app-credentials created
```

### 1.2 Viewing Secret

```bash
kubectl get secret app-credentials -o yaml
```

Output:
```yaml
apiVersion: v1
data:
  password: c3VwZXJzZWNyZXQxMjM=
  username: YWRtaW4=
kind: Secret
metadata:
  creationTimestamp: "2026-04-09T17:24:09Z"
  name: app-credentials
  namespace: default
type: Opaque
```

### 1.3 Decoding Base64

```bash
echo "YWRtaW4=" | base64 -d
# Output: admin

echo "c3VwZXJzZWNyZXQxMjM=" | base64 -d  
# Output: supersecret123
```

### 1.4 Base64 Encoding vs Encryption

**Key Difference:**
- **Base64 encoding** is NOT encryption - it's reversible data encoding
- Anyone with API access can decode secrets: `kubectl get secret -o yaml | base64 -d`
- **Encryption** requires a key to decrypt data

**Kubernetes Secrets Security:**
- By default, secrets are stored in etcd as **base64-encoded** (not encrypted)
- Anyone with etcd access or API permissions can read secrets
- For production: enable **etcd encryption at rest**

**When to enable etcd encryption:**
- Production environments with sensitive data
- Compliance requirements (PCI-DSS, HIPAA, SOC 2)
- Multi-tenant clusters
- When etcd backups might be compromised

---

## Task 2 — Helm-Managed Secrets

### 2.1 Chart Structure

Files created/modified:
- `k8s/app-python/templates/secrets.yaml` - Secret resource template
- `k8s/app-python/values.yaml` - Added `secrets` configuration
- `k8s/app-python/templates/deployment.yaml` - Added `envFrom` for secret injection

### 2.2 Secret Template

`templates/secrets.yaml`:
```yaml
apiVersion: v1
kind: Secret
metadata:
  name: {{ include "app-python.fullname" . }}-secret
  labels:
    {{- include "app-python.labels" . | nindent 4 }}
type: Opaque
stringData:
  username: {{ .Values.secrets.username | quote }}
  password: {{ .Values.secrets.password | quote }}
```

### 2.3 Deployment Configuration

Secrets consumed via `envFrom` in `deployment.yaml`:
```yaml
envFrom:
  - secretRef:
      name: {{ include "app-python.fullname" . }}-secret
```

### 2.4 Deployment

```bash
helm upgrade --install app-python ./k8s/app-python \
  --set secrets.username=myuser \
  --set secrets.password=mypass
```

Output:
```
Release "app-python" has been upgraded. Happy Helming!
NAME: app-python
LAST DEPLOYED: Thu Apr  9 20:26:08 2026
NAMESPACE: default
STATUS: deployed
```

### 2.5 Verification - Environment Variables

```bash
kubectl exec -it app-python-app-python-84b78f989f-4vgxj -- env | grep -E "username|password"
```

Output:
```
password=mypass
username=myuser
```

### 2.6 Resource Limits

```bash
kubectl get pod app-python-app-python-84b78f989f-4vgxj -o jsonpath='{.spec.containers[0].resources}'
```

Output:
```json
{"limits":{"cpu":"200m","memory":"256Mi"},"requests":{"cpu":"100m","memory":"128Mi"}}
```

**Explanation:**
- **Requests:** Guaranteed resources (scheduler uses this)
  - CPU: 100m (0.1 CPU core)
  - Memory: 128Mi
- **Limits:** Maximum allowed resources
  - CPU: 200m (throttled if exceeded)
  - Memory: 256Mi (pod killed if exceeded)

**How to choose values:**
- Profile app under load
- Set requests = average usage + buffer
- Set limits = peak usage (typically 1.5-2x requests)

---

## Task 3 — HashiCorp Vault Integration

### 3.1 Vault Installation

Installed via custom YAML manifests:

```bash
kubectl apply -f k8s/vault-install.yaml
```

Verification:
```bash
kubectl get pods -l app.kubernetes.io/name=vault
```

Output:
```
NAME                                    READY   STATUS    RESTARTS   AGE
vault-0                                 1/1     Running   0          18m
vault-agent-injector-7d585f8568-bmzzr   1/1     Running   0          13m
```

### 3.2 KV Secrets Configuration

```bash
kubectl exec -it vault-0 -- vault kv put secret/app-python/config \
  username="admin" password="secret123"
```

Output:
```
======== Secret Path ========
secret/data/app-python/config

======= Metadata =======
Key                Value
---                -----
created_time       2026-04-09T17:31:01.532736836Z
version            1
```

Verification:
```bash
kubectl exec -it vault-0 -- vault kv get secret/app-python/config
```

Output:
```
====== Data ======
Key         Value
---         -----
password    secret123
username    admin
```

### 3.3 Kubernetes Authentication

```bash
kubectl exec -it vault-0 -- vault auth enable kubernetes
```

Output:
```
Success! Enabled kubernetes auth method at: kubernetes/
```

Configure authentication:
```bash
kubectl exec -it vault-0 -- sh -c '
TOKEN_REVIEW_JWT=$(cat /var/run/secrets/kubernetes.io/serviceaccount/token)
KUBE_CA_CERT=$(cat /var/run/secrets/kubernetes.io/serviceaccount/ca.crt)
KUBE_HOST=https://${KUBERNETES_PORT_443_TCP_ADDR}:443

vault write auth/kubernetes/config \
  token_reviewer_jwt="$TOKEN_REVIEW_JWT" \
  kubernetes_host="$KUBE_HOST" \
  kubernetes_ca_cert="$KUBE_CA_CERT" \
  disable_local_ca_jwt=true
'
```

Output:
```
Success! Data written to: auth/kubernetes/config
```

### 3.4 Policy and Role

Create RBAC for Vault:
```bash
kubectl apply -f k8s/vault-rbac.yaml
```

Output:
```
serviceaccount/vault-auth created
clusterrolebinding.rbac.authorization.k8s.io/vault-auth-delegator created
```

Create policy:
```bash
kubectl exec -it vault-0 -- vault policy write app-python - <<EOF
path "secret/data/app-python/*" {
  capabilities = ["read"]
}
EOF
```

Output:
```
Success! Uploaded policy: app-python
```

Create role:
```bash
kubectl exec -it vault-0 -- vault write auth/kubernetes/role/app-python \
  bound_service_account_names=default \
  bound_service_account_namespaces=default \
  policies=app-python \
  ttl=24h
```

Output:
```
Success! Data written to: auth/kubernetes/role/app-python
```

### 3.5 Vault Agent Injection

Deploy with Vault enabled:
```bash
helm upgrade --install app-python ./k8s/app-python --set vault.enabled=true
```

Verification - Init Container Logs:
```bash
kubectl logs app-python-app-python-67db7f78b9-9qjtq -c vault-agent-init --tail=20
```

Output:
```
2026-04-09T17:47:54.661Z [INFO]  agent.auth.handler: authentication successful, sending token to sinks
2026-04-09T17:47:54.664Z [INFO]  agent: (runner) rendered "/vault/config/secret.tmpl" => "/vault/secrets/config"
2026-04-09T17:47:54.664Z [INFO]  agent: (runner) stopping
2026-04-09T17:47:54.664Z [INFO]  agent.exec.server: exec server stopped
```

### 3.6 Secret Injection Verification

Check init container exists:
```bash
kubectl get pod app-python-app-python-67db7f78b9-9qjtq -o jsonpath='{.spec.initContainers[*].name}'
```

Output:
```
vault-agent-init
```

Check secrets file:
```bash
kubectl exec -it app-python-app-python-67db7f78b9-9qjtq -- cat /vault/secrets/config
```

Output:
```
Defaulted container "app-python" out of: app-python, vault-agent-init (init)
username=admin
password=secret123
```

### 3.7 Init Container Pattern Explanation

**How it works:**
1. **Init Container** (`vault-agent-init`) runs before main app container
2. Authenticates with Vault using Kubernetes service account token
3. Fetches secrets from Vault
4. Renders secrets to `/vault/secrets/config` using template
5. Exits after writing secrets
6. Main app container starts with access to secrets via shared volume

**Differences from Sidecar:**
- **Init Container:** Runs once, fetches secrets at startup
- **Sidecar:** Runs alongside app, can refresh secrets dynamically

Both patterns are valid for Vault integration.

---

## Task 4 — Security Analysis

### Comparison: Kubernetes Secrets vs Vault

| Feature | K8s Secrets | HashiCorp Vault |
|---------|-------------|-----------------|
| Storage | etcd (base64) | Encrypted backend |
| Encryption | Optional | Always encrypted |
| Access Control | RBAC only | Fine-grained policies |
| Secret Rotation | Manual | Automatic (dynamic secrets) |
| Audit Logs | Basic API logs | Detailed audit trail |
| Versioning | No | Yes |
| Complexity | Low | Medium-High |
| Setup Time | Minutes | Hours |

### When to Use Each

**Use Kubernetes Secrets:**
- Development/testing environments
- Non-critical configuration data
- Simple applications with few secrets
- Small teams without dedicated ops

**Use HashiCorp Vault:**
- Production environments with sensitive data
- Compliance requirements (PCI-DSS, HIPAA)
- Dynamic secrets needed (database credentials)
- Multi-cluster deployments
- Audit trails required

### Production Recommendations

1. **Enable etcd encryption** for K8s Secrets
2. **Use RBAC** to limit secret access
3. **Never commit secrets** to Git
4. **Rotate secrets regularly**
5. **Use Vault** for critical production secrets
6. **Implement monitoring** and alerting for secret access
7. **Regular security audits**

---

## Summary

**Task 1:** ✅ K8s Secrets created, viewed, decoded. Understand base64 ≠ encryption.

**Task 2:** ✅ Helm chart updated with secret template. Secrets injected as env vars. Resource limits configured.

**Task 3:** ✅ Vault installed and configured. K8s auth enabled. Init container successfully fetches secrets from Vault.

**Task 4:** ✅ Complete documentation with outputs and security analysis.

---

**All tasks completed successfully.**
