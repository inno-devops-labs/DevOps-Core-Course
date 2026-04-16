# SECRETS — Lab 11 Documentation

## 1) Kubernetes Secrets

### Create and view secret
Commands used:
```bash
kubectl create secret generic app-credentials \
  --from-literal=username=admin \
  --from-literal=password='s3cr3t-demo'

kubectl get secret app-credentials -o yaml
```

Output:
```yaml
apiVersion: v1
data:
  password: czNjcjN0LWRlbW8=
  username: YWRtaW4=
kind: Secret
metadata:
  name: app-credentials
  namespace: default
type: Opaque
```

### Decode values
Commands:
```bash
kubectl get secret app-credentials -o jsonpath='{.data.username}' | base64 -d
kubectl get secret app-credentials -o jsonpath='{.data.password}' | base64 -d
```

Output:
```text
username=admin
password=s3cr3t-demo
```

### Base64 vs encryption
- Base64 is **encoding**, not encryption.
- Anyone with API read access to the Secret can decode it.
- Kubernetes Secrets are not strongly protected unless additional controls are enabled.

### Security implication (etcd encryption)
- Encryption at rest for Secrets in etcd is **not guaranteed by default** in typical setups.
- For production, enable etcd encryption at rest and strict RBAC for Secret access.

---

## 2) Helm Secret Integration

### Chart structure updates
- Added `k8s/devops-app/templates/secrets.yaml`
- Updated `k8s/devops-app/templates/deployment.yaml` to consume Secret via `envFrom.secretRef`
- Added secret-related values to `k8s/devops-app/values.yaml`

### Secret consumption in Deployment
Pattern used:
```yaml
envFrom:
  - secretRef:
      name: <templated-secret-name>
```

Rendered manifest check:
```text
17:kind: Secret
100:          envFrom:
101:            - secretRef:
124:          resources:
```

### Verification in pod
Command:
```bash
kubectl exec <pod> -- sh -c 'printenv | grep -E "^(username|password|PORT|APP_VERSION)=" | sort'
```

Output:
```text
APP_VERSION=v2
PORT=5000
password=change-me
username=demo-user
```

`kubectl describe pod` check for clear-text values:
```text
(no clear secret values in describe output)
```

---

## 3) Resource Management

Resource limits/requests are configured in chart values and applied in deployment template.

Current defaults:
```yaml
resources:
  requests:
    cpu: "100m"
    memory: "128Mi"
  limits:
    cpu: "200m"
    memory: "256Mi"
```

Explanation:
- **requests**: guaranteed resources used by scheduler for placement.
- **limits**: hard caps enforced at runtime.

How to choose values:
- Start with low requests to improve scheduling.
- Set limits based on observed peak usage.
- Tune from metrics (CPU throttling, memory OOM/restarts).

---

## 4) Vault Integration

### Vault installation verification
Command:
```bash
kubectl get pods -l app.kubernetes.io/instance=vault
```

Output:
```text
NAME                                    READY   STATUS    RESTARTS   AGE
vault-0                                 1/1     Running   0          19m
vault-agent-injector-75998c9b76-x254f   1/1     Running   0          19m
```

### Policy/role configuration (sanitized)
Vault role used for app SA:
```text
bound_service_account_names: [devops-vault-sa]
bound_service_account_namespaces: [default]
policies: [devops-app-policy]
```

Policy grants read access to:
```text
secret/data/myapp/config
```

### Sidecar injection proof
Pod container layout (vault-demo release):
```text
init=vault-agent-init
app=devops-app vault-agent
```

Injected file path and presence:
```text
/vault/secrets/app-config
```

File bytes show rendered keys:
```text
username=admin
password=supersecret123
```

### Sidecar injection pattern (brief)
- Vault injector mutates pod at admission time.
- Adds init + sidecar agents.
- Agent authenticates with Kubernetes SA token.
- Secret is rendered to files under `/vault/secrets/*`.

---

## 5) Security Analysis

### Kubernetes Secrets vs Vault
- **K8s Secrets**: simple and native, good for basic use, but weaker security model without etcd encryption and strict RBAC.
- **Vault**: centralized secret manager, better access control/audit/rotation patterns, stronger for production.

### When to use each
- Use K8s Secrets for local labs/dev and low-risk configs.
- Use Vault for production workloads, shared platforms, and regulated environments.

### Production recommendations
1. Enable etcd encryption at rest.
2. Enforce least-privilege RBAC for secrets.
3. Avoid committing real secrets in Git.
4. Prefer external secret manager (Vault) for sensitive credentials.
5. Rotate credentials regularly and monitor secret access.
