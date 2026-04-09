# Secret Management for DevOps Info Service

## 1. Kubernetes Secrets Fundamentals

### 1.1 Creating a Secret

```bash
kubectl create secret generic app-credentials \
  --from-literal=username=myapp_user \
  --from-literal=password=SuperSecret123
```

### 1.2 Examining the Secret

```bash
$ kubectl get secret app-credentials -o yaml
apiVersion: v1
kind: Secret
metadata:
  name: app-credentials
data:
  username: bXlhcHBfdXNlcg==
  password: U3VwZXJTZWNyZXQxMjM=
type: Opaque
```

### 1.3 Decoding Base64 Values

```bash
$ echo "bXlhcHBfdXNlcg==" | base64 -d
myapp_user

$ echo "U3VwZXJTZWNyZXQxMjM=" | base64 -d
SuperSecret123
```

### 1.4 Security Implications

- Kubernetes Secrets are **base64-encoded, NOT encrypted** by default.
- Anyone with API access can decode them.
- For production, enable **etcd encryption at rest** and use **RBAC** to restrict access.
- Never commit real secrets to version control.

---

## 2. Helm-Managed Secrets

### 2.1 Chart Structure

The Helm chart (`my-python-app`) includes:

```
templates/
├── secrets.yaml          # Secret resource template
├── deployment.yaml       # Consumes the secret
└── ...
values.yaml               # Placeholder secret values
```

### 2.2 Secret Template (`templates/secrets.yaml`)

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: {{ include "my-python-app.fullname" . }}-secret
  labels:
    {{- include "my-python-app.labels" . | nindent 4 }}
type: Opaque
data:
  username: {{ .Values.secrets.username | b64enc | quote }}
  password: {{ .Values.secrets.password | b64enc | quote }}
```

### 2.3 Values Placeholder (`values.yaml`)

```yaml
secrets:
  username: placeholder-user
  password: placeholder-password

resources:
  requests:
    memory: "64Mi"
    cpu: "100m"
  limits:
    memory: "128Mi"
    cpu: "200m"
```

### 2.4 Deployment Integration

In `deployment.yaml`, the secret is consumed via `envFrom`:

```yaml
envFrom:
  - secretRef:
      name: {{ include "my-python-app.fullname" . }}-secret
```

### 2.5 Installing with Real Secrets

```bash
helm install myapp ./my-python-app \
  --set secrets.username=myapp_user \
  --set secrets.password=SuperSecret123
```

### 2.6 Verification

```bash
$ kubectl exec -it deployment/myapp-my-python-app -- env | grep -E "username|password"
username=myapp_user
password=SuperSecret123

$ kubectl describe pod myapp-my-python-app-xxxxx | grep -E "username|password"
# (no output – secrets are not exposed)
```

---

## 3. HashiCorp Vault Integration

### 3.1 Install Vault via Helm

```bash
helm repo add hashicorp https://helm.releases.hashicorp.com
helm repo update
helm install vault hashicorp/vault \
  --set "server.dev.enabled=true" \
  --set "injector.enabled=true"

kubectl get pods
# vault-0                          1/1     Running
# vault-agent-injector-xxxxx       1/1     Running
```

### 3.2 Configure Vault

Exec into the Vault pod:

```bash
kubectl exec -it vault-0 -- /bin/sh
```

Inside the pod:

```bash
# Enable KV secrets engine v2
vault secrets enable -path=secret kv-v2

# Create a secret
vault kv put secret/devops-app/config username="vault_user" password="vault_secret_123"

# Enable Kubernetes authentication
vault auth enable kubernetes

# Configure Kubernetes auth (auto-detects service host)
vault write auth/kubernetes/config \
  kubernetes_host="https://$KUBERNETES_SERVICE_HOST:$KUBERNETES_SERVICE_PORT_HTTPS"

# Create a policy for read access
vault policy write devops-app - <<EOF
path "secret/data/devops-app/config" {
  capabilities = ["read"]
}
EOF

# Create a role bound to the default service account
vault write auth/kubernetes/role/devops-app \
  bound_service_account_names=default \
  bound_service_account_namespaces=default \
  policies=devops-app \
  ttl=1h
exit
```

### 3.3 Enable Vault Agent Injection

Add annotations to the deployment’s pod template:

```yaml
annotations:
  vault.hashicorp.com/agent-inject: "true"
  vault.hashicorp.com/role: "devops-app"
  vault.hashicorp.com/agent-inject-secret-config: "secret/data/devops-app/config"
```

### 3.4 Upgrade the Helm Release

```bash
helm upgrade myapp ./my-python-app \
  --set secrets.username=myapp_user \
  --set secrets.password=SuperSecret123
```

### 3.5 Verify Secret Injection

```bash
$ kubectl exec -it deployment/myapp-my-python-app -- cat /vault/secrets/config
data: map[password:vault_secret_123 username:vault_user]
metadata: map[...
```

The Vault sidecar container is also visible:

```bash
kubectl describe pod myapp-my-python-app-xxxxx | grep -A 5 "vault-agent"
```

---

## 4. Resource Management

Resource limits are defined in `values.yaml` and applied in the deployment:

```yaml
resources:
  requests:
    memory: "64Mi"
    cpu: "100m"
  limits:
    memory: "128Mi"
    cpu: "200m"
```

- **Requests** guarantee resources for scheduling.
- **Limits** prevent a container from consuming too many resources.

Check applied limits:

```bash
kubectl describe pod myapp-my-python-app-xxxxx | grep -A 2 "Limits"
```

---

## 5. Security Analysis

| Approach | Pros | Cons |
|----------|------|------|
| **K8s Secrets** | Simple, built-in | Base64 only, no encryption at rest by default |
| **Helm Secrets** | Templated, versionable | Still relies on K8s Secrets; values may be in Git |
| **HashiCorp Vault** | Encrypted at rest, dynamic secrets, audit logs, rotation | More complex, requires management |

### Production Recommendations

- **Enable etcd encryption** for K8s Secrets.
- **Use Vault** for critical secrets (database passwords, API keys).
- **Never commit real secrets** to Git – use placeholders and inject at deploy time.
- **Restrict secret access** with RBAC.
- **Rotate secrets** regularly (Vault can automate this).
