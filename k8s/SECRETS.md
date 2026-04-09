# Lab 11: Kubernetes Secrets & HashiCorp Vault

## 1. Kubernetes Secrets Fundamentals

### Creating and Viewing
Created an opaque secret using `kubectl`:
```bash
$ kubectl create secret generic app-credentials --from-literal=username=admin --from-literal=password=secret123
secret/app-credentials created

$ kubectl get secret app-credentials -o yaml
apiVersion: v1
data:
  password: c2VjcmV0MTIz
  username: YWRtaW4=
kind: Secret
metadata:
  name: app-credentials
  namespace: default
type: Opaque
```

### Decoding Secret Values
The encoded values are Base64 encoded, not encrypted. This can be easily decoded:
```bash
$ echo "c2VjcmV0MTIz" | base64 -d
secret123
```

### Security Implications
- **Encoding vs Encryption**: Kubernetes secrets are by default just base64 encoded strings, meaning anyone with access to the `Secret` object via `kubectl get secrets` can decode them.
- **Encryption at Rest**: By default, secrets are not encrypted in `etcd`. It is highly recommended to enable `EncryptionConfiguration` to encrypt data at rest within `etcd`. Additionally, RBAC must be strictly enforced so that only necessary ServiceAccounts and users can read specific secrets.


## 2. Helm Secret Integration

### Chart Structure
Added a `templates/secrets.yaml` to the Helm chart:
```yaml
apiVersion: v1
kind: Secret
metadata:
  name: {{ include "pythonapp.fullname" . }}-secret
  labels:
    {{- include "pythonapp.labels" . | nindent 4 }}
type: Opaque
stringData:
  username: {{ .Values.secrets.username | quote }}
  password: {{ .Values.secrets.password | quote }}
```

### Secret Consumption (Deployment)
The deployment is configured to consume these secrets using `envFrom`:
```yaml
          envFrom:
            - secretRef:
                name: {{ include "pythonapp.fullname" . }}-secret
```

### Verification
When the container starts, the secret keys become environment variables:
```bash
$ kubectl exec pythonapp-dev-pythonapp-dc464768b-82r4f -c pythonapp -- printenv | grep "username"
username=admin
```


## 3. Resource Management

### Configuration (`values.yaml`)
Configured appropriate resource limits to ensure the application stays bounded:
```yaml
resources:
  requests:
    cpu: 50m
    memory: 64Mi
  limits:
    cpu: 100m
    memory: 128Mi
```
- **Requests**: What Kubernetes guarantees the pod will get on the node for scheduling.
- **Limits**: The hard cap; if the container pushes beyond the memory limit, it is OOMKilled by the node.


## 4. HashiCorp Vault Integration

### Vault Installation
Vault was deployed via Helm with the Vault Injector enabled.
```bash
$ helm install vault hashicorp/vault --set "server.dev.enabled=true" --set "injector.enabled=true"

$ kubectl get pods
NAME                                       READY   STATUS    RESTARTS   AGE
vault-0                                    1/1     Running   0          24m
vault-agent-injector-848dd747d7-47s89      1/1     Running   0          24m
```

### Vault Configuration (Policy and Role)
Vault was configured with a Secret engine (KV v2) and K8s auth.
`myapp` Policy:
```hcl
path "secret/data/myapp/config" {
  capabilities = ["read", "list"]
}
```
Role binding to the default Kubernetes service account limits who can inherit this policy.

### Vault Agent Injection
By adding specific annotations to the Deployment, the Vault Injector intercepts pod creation to inject the `vault-agent-init` and `vault-agent` sidecars.

**Deployment Annotations:**
```yaml
      annotations:
        vault.hashicorp.com/agent-inject: "true"
        vault.hashicorp.com/role: "myapp"
        vault.hashicorp.com/agent-inject-secret-config: "secret/data/myapp/config"
```

**Proof of Secret Injection:**
```bash
$ kubectl exec pythonapp-dev-pythonapp-dc464768b-82r4f -c pythonapp -- cat /vault/secrets/config
data: map[password:secret123 username:admin]
metadata: map[created_time:... version:1]
```
*The sidecar pattern allows the application to read secrets from a local memory-backed file (`/vault/secrets/config`) without needing Vault SDKs integrated into its code.*


## 5. Security Analysis

| Feature | Kubernetes Secrets | HashiCorp Vault |
|---------|---------------------|-----------------|
| **Storage Engine** | Stored in `etcd` (base64, unencrypted by default). | Stored securely, encrypted in transit and rest. |
| **Access Control** | K8s RBAC namespace scoping. | Rich K8s service account TTL auth and specific read policies. |
| **Rotation** | Must manually update Secret and restart pods. | Dynamic and supports short-lived TTL based credentials. |
| **Use Case** | Useful for internal infra configuration not containing highly sensitive DB/API keys. | Production grade applications containing strict sensitive secrets (Passwords, API Tokens). |

**Production Recommendation**: Always use HashiCorp Vault (or another external secrets manager like AWS Secrets Manager via External Secrets Operator) for production deployments. Avoid natively pushing credentials to K8s secrets unless heavily protected and encrypted at rest within etcd.
