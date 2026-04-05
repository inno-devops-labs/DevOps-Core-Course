# PS: All secrets as usernames and passwords changed for security reasons

## Task 1 - Kubernetes Secrets Fundamentals

I created the secret imperatively with `kubectl`:

```bash
kubectl create secret generic app-credentials \
  --from-literal=username=admin \
  --from-literal=password=admin
```

I then inspected it with:

```bash
kubectl get secret app-credentials -o yaml
```

The stored values are base64 strings. I decoded one of them with:

```bash
echo "YWRtaW4=" | base64 -d
```

That returns `admin`.

### Security note

Kubernetes Secrets are base64-encoded, not encrypted by default. Base64 only hides the value from casual reading. Anyone with permission to read the Secret object can decode it. For production, etcd encryption at rest and RBAC are the minimum controls, and an external secret manager is better for highly sensitive credentials.

## Task 2 - Helm-managed Secrets

I updated the Helm chart in `k8s/myapp` to manage the application Secret and inject it into the Pod as environment variables.

### Chart files

- [k8s/myapp/templates/secrets.yaml](myapp/templates/secrets.yaml)
- [k8s/myapp/templates/deployment.yml](myapp/templates/deployment.yml)
- [k8s/myapp/templates/_helpers.tpl](myapp/templates/_helpers.tpl)
- [k8s/myapp/templates/serviceaccount.yaml](myapp/templates/serviceaccount.yaml)

### Values used by the chart

The chart now contains placeholder credentials and resource limits in `values.yaml`:

```yaml
secret:
  username: "dev-user"
  password: "dev-pass"

resources:
  requests:
    memory: "64Mi"
    cpu: "100m"
  limits:
    memory: "128Mi"
    cpu: "200m"
```

I also aligned the service target port with the Flask app port and added a dedicated ServiceAccount so the chart can later be bound to Vault roles cleanly.

### Secret template

The Secret template uses `stringData`, so Kubernetes performs the encoding automatically:

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: {{ include "myapp.fullname" . }}-secret
type: Opaque
stringData:
  username: {{ .Values.secret.username | default "placeholder-user" }}
  password: {{ .Values.secret.password | default "placeholder-pass" }}
```

### Deployment wiring

The deployment consumes every key from the Secret with `envFrom`:

```yaml
envFrom:
  - secretRef:
      name: {{ include "myapp.fullname" . }}-secret
```

The deployment also reads requests and limits from `values.yaml`, so the resource settings stay configurable.

### Verification

To install and validate the chart:

```bash
cd k8s/myapp
helm install my-release .
kubectl get pods
kubectl describe pod <pod-name>
kubectl exec -it <pod-name> -- env | grep -E 'username|password'
```

The environment variables should be present inside the container, while `kubectl describe pod` should not reveal the secret values themselves.

### Resource management

Requests define the minimum resources the scheduler reserves for the Pod. Limits define the maximum amount the container can consume. The values in this chart are conservative for a small Flask service and can be tuned later if load testing shows a different profile.

## Task 3 - HashiCorp Vault Integration

I prepared the chart for Vault injection and documented the runtime steps for a live cluster.

### Vault-ready chart support

The deployment supports Vault Agent injection through pod annotations when `vault.enabled` is turned on in `values.yaml`:

```yaml
vault:
  enabled: false
  role: myapp
  secretPath: secret/data/myapp/config
```

When enabled, the pod receives these annotations:

```yaml
vault.hashicorp.com/agent-inject: "true"
vault.hashicorp.com/role: "myapp"
vault.hashicorp.com/agent-inject-secret-config: "secret/data/myapp/config"
```

The chart also creates a ServiceAccount so the Vault role can be bound to a stable Kubernetes identity.

### Vault installation

Install Vault in dev mode for the lab:

```bash
helm repo add hashicorp https://helm.releases.hashicorp.com
helm repo update
helm install vault hashicorp/vault \
  --set server.dev.enabled=true \
  --set injector.enabled=true
```

Verify the pods:

```bash
kubectl get pods
```

```bash
➜  ~ kubectl get pods
NAME                                    READY   STATUS              RESTARTS      AGE
my-python-app-598569f8d4-8h75d          1/1     Running             1 (13h ago)   7d13h
my-python-app-598569f8d4-s8j6x          1/1     Running             1 (13h ago)   7d13h
vault-0                                 0/1     ContainerCreating   0             1s
vault-agent-injector-848dd747d7-5wc5t   0/1     ContainerCreating   0             11s
```

### Configure Vault

Enable the KV v2 engine and store the application secret:

```bash
vault secrets enable -path=secret kv-v2
vault kv put secret/myapp/config username="admin" password="secret123"
```

That secret is then read at `secret/data/myapp/config`.

Enable Kubernetes authentication:

```bash
vault auth enable kubernetes
vault write auth/kubernetes/config \
  kubernetes_host="https://$KUBERNETES_PORT_443_TCP_ADDR:443"
```

Create a policy that grants read access to the application secret:

```bash
cat <<'EOF' > myapp-policy.hcl
path "secret/data/myapp/config" {
  capabilities = ["read"]
}
EOF

vault policy write myapp myapp-policy.hcl
```

Create a role bound to the application ServiceAccount:

```bash
vault write auth/kubernetes/role/myapp \
  bound_service_account_names=myapp \
  bound_service_account_namespaces=default \
  policies=myapp \
  ttl=24h
```

### Verify injection

Deploy the chart with Vault enabled and check the injected files:

```bash
helm upgrade --install my-release . --set vault.enabled=true
kubectl get pods
kubectl exec -it <pod-name> -- ls -l /vault/secrets
kubectl exec -it <pod-name> -- cat /vault/secrets/config
```

Vault Agent creates the file inside the Pod after authenticating with Kubernetes and fetching the secret from Vault.

### Sidecar pattern

Vault Agent injection works by mutating the Pod at admission time. The injector adds a Vault Agent sidecar and init container, authenticates with Kubernetes, then writes the secret to the Pod filesystem. The application reads the rendered file instead of talking to Vault directly.

## Security analysis

- Kubernetes Secrets are simple and native, but they are only base64-encoded unless etcd encryption and RBAC are configured correctly.
- Vault centralizes secret storage, supports auditability and rotation, and is a better fit for sensitive application credentials.

For production, I would keep Kubernetes Secrets for low-risk or static values and use Vault for anything sensitive, rotated, or shared across services.
