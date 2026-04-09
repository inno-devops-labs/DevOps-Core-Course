# LAB11 - Kubernetes Secrets and HashiCorp Vault


Cluster: `minikube`
Namespace used for app: `lab11`

## 1. Kubernetes Secrets Fundamentals

### 1.1 Create secret with imperative kubectl

```bash
kubectl create namespace lab11 --dry-run=client -o yaml | kubectl apply -f -
kubectl -n lab11 create secret generic app-credentials \
  --from-literal=username=lab11-user \
  --from-literal=password='Str0ngP@ss-lab11'
```

Output:

```text
namespace/lab11 created
secret/app-credentials created
```

### 1.2 View secret YAML and decode Base64

```bash
kubectl -n lab11 get secret app-credentials -o yaml
```

Output:

```yaml
apiVersion: v1
data:
  password: U3RyMG5nUEBzcy1sYWIxMQ==
  username: bGFiMTEtdXNlcg==
kind: Secret
metadata:
  name: app-credentials
  namespace: lab11
type: Opaque
```

```bash
echo 'U3RyMG5nUEBzcy1sYWIxMQ==' | base64 -d
echo 'bGFiMTEtdXNlcg==' | base64 -d
```

Output:

```text
Str0ngP@ss-lab11
lab11-user
```

### 1.3 Encoding vs encryption and security implications

- Base64 is only encoding (representation change), not cryptographic protection.
- By default, Kubernetes Secrets are not encrypted in etcd unless encryption at rest is explicitly configured.
- etcd encryption at rest means API server uses an `EncryptionConfiguration` provider (for example `aescbc` or KMS) before writing Secret data into etcd.
- Enable etcd encryption in any non-trivial environment (shared clusters, production, or regulated workloads).

## 2. Helm-Managed Secrets Integration

### 2.1 Chart structure (with secret template)

```text
k8s/devops-info/
├── values.yaml
└── templates/
    ├── _helpers.tpl
    ├── deployment.yaml
    ├── secrets.yaml
    ├── service.yaml
    └── serviceaccount.yaml
```

### 2.2 Implemented Helm secret management

`templates/secrets.yaml`:

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: {{ include "devops-info.secretName" . }}
  labels:
    {{- include "devops-info.labels" . | nindent 4 }}
type: Opaque
stringData:
  {{- range $key := keys .Values.secrets.data | sortAlpha }}
  {{ $key }}: {{ index $.Values.secrets.data $key | quote }}
  {{- end }}
```

`values.yaml` (placeholder defaults):

```yaml
secrets:
  create: true
  name: ""
  data:
    APP_USERNAME: "change-me-username"
    APP_PASSWORD: "change-me-password"
```

`templates/deployment.yaml` (secret consumption):

```yaml
envFrom:
  - secretRef:
      name: {{ include "devops-info.secretName" . }}
```

### 2.3 Deploy and verify env injection

```bash
helm upgrade --install lab11-app k8s/devops-info -n lab11 --create-namespace --wait \
  --set-string secrets.data.APP_USERNAME=helm-user \
  --set-string secrets.data.APP_PASSWORD='helm-pass-123' \
  --set-string env.RELEASE_VERSION=lab11
```

Output:

```text
STATUS: deployed
REVISION: 1
```

Verify env vars inside pod (values redacted):

```bash
POD=$(kubectl -n lab11 get pod -l app.kubernetes.io/instance=lab11-app -o jsonpath='{.items[0].metadata.name}')
kubectl -n lab11 exec "$POD" -- /bin/sh -c 'printenv | grep -E "^(APP_USERNAME|APP_PASSWORD)=" | sed -E "s/=.*/=<redacted>/"'
```

Output:

```text
APP_USERNAME=<redacted>
APP_PASSWORD=<redacted>
```

Verify no secret values exposed by `kubectl describe pod`:

```bash
kubectl -n lab11 describe pod "$POD" | sed -n '/Environment Variables from:/,/Mounts:/p'
```

Output:

```text
Environment Variables from:
  lab11-app-devops-info-credentials  Secret  Optional: false
Environment:
  DEBUG:            false
  HOST:             0.0.0.0
  PORT:             5000
  RELEASE_VERSION:  lab11
```

## 3. Resource Management

Resource requests/limits are configured and templated through values:

```yaml
resources:
  limits:
    cpu: 200m
    memory: 256Mi
  requests:
    cpu: 100m
    memory: 128Mi
```

- `requests` define scheduler guarantees (minimum reserved resources).
- `limits` define hard upper bounds per container.
- Sizing approach used: start from low safe defaults for Flask API, monitor CPU/memory usage, then increase requests to typical baseline and limits to short-burst headroom.

## 4. HashiCorp Vault Integration

### 4.1 Vault install via Helm

```bash
helm repo add hashicorp https://helm.releases.hashicorp.com
helm repo update
helm upgrade --install vault hashicorp/vault \
  -n vault --create-namespace \
  --set server.dev.enabled=true \
  --set injector.enabled=true \
  --wait --timeout 5m
```

Verification:

```bash
kubectl -n vault get pods
```

Output:

```text
NAME                                   READY   STATUS    RESTARTS   AGE
vault-0                                1/1     Running   0          ...
vault-agent-injector-6b4f84b6c-cgrx2   1/1     Running   0          ...
```

### 4.2 Configure KV and create app secret

```bash
kubectl -n vault exec vault-0 -- /bin/sh -c 'export VAULT_ADDR=http://127.0.0.1:8200; vault login root >/dev/null; vault kv put secret/myapp/config username="vault-user" password="vault-pass-123"'
```

Output:

```text
====== Secret Path ======
secret/data/myapp/config
version            1
```

### 4.3 Configure Kubernetes auth, policy, and role

```bash
# Enable and configure auth
vault auth enable kubernetes
vault write auth/kubernetes/config \
  kubernetes_host="https://$KUBERNETES_PORT_443_TCP_ADDR:443" \
  token_reviewer_jwt="$(cat /var/run/secrets/kubernetes.io/serviceaccount/token)" \
  kubernetes_ca_cert=@/var/run/secrets/kubernetes.io/serviceaccount/ca.crt

# Policy
path "secret/data/myapp/config" {
  capabilities = ["read"]
}

# Role
vault write auth/kubernetes/role/devops-info-role \
  bound_service_account_names=lab11-app-devops-info \
  bound_service_account_namespaces=lab11 \
  policies=devops-info-policy ttl=24h
```

Verified role:

```text
bound_service_account_names      [lab11-app-devops-info]
bound_service_account_namespaces [lab11]
policies                         [devops-info-policy]
ttl                              24h
```

### 4.4 Enable Vault Agent injection in app deployment

Helm values used:

```bash
helm upgrade --install lab11-app k8s/devops-info -n lab11 --wait --reuse-values \
  --set vault.enabled=true \
  --set vault.role=devops-info-role \
  --set vault.secretPath=secret/data/myapp/config \
  --set vault.injectFileName=config
```

Pod-level verification:

```text
READY   STATUS
2/2     Running
```

Mutated containers:

```text
initContainers: vault-agent-init
containers: app vault-agent
```

Injected file verification:

```bash
kubectl -n lab11 exec "$POD" -c app -- ls -la /vault/secrets
```

Output:

```text
-rw-r--r-- 1 app 1000 ... config
```

Sanitized injected content proof:

```text
data: map[password:<redacted> username:<redacted>
metadata: map[created_time:... version:1]
```

### 4.5 Sidecar injection pattern explanation

Vault Injector mutates pod specs at admission time based on annotations:

- Adds `vault-agent-init` (initial auth + first secret render).
- Adds `vault-agent` sidecar (token renewal and re-render support).
- Mounts shared volume (`/vault/secrets`) into app container.

The app reads secrets from files instead of hardcoding credentials into image or ConfigMap.

## 5. Security Analysis

### Kubernetes Secrets vs Vault

| Aspect | Kubernetes Secret | Vault |
|---|---|---|
| Storage | etcd (base64 value, optional encryption at rest) | Vault encrypted storage |
| Access control | Kubernetes RBAC | Vault policies + auth methods |
| Rotation/dynamic secrets | Manual/limited | Built-in dynamic and lease-based patterns |
| Audit | Kubernetes audit logs | Detailed Vault audit backends |
| App integration | Native and simple | More setup, stronger security model |

### When to use each

- Use Kubernetes Secrets for low-complexity internal configs where RBAC + etcd encryption are enforced.
- Use Vault for production secrets, multi-team clusters, strict compliance, short-lived credentials, and centralized secret governance.

### Production recommendations

- Enable etcd encryption at rest for all Secret resources.
- Lock down Secret access with least-privilege RBAC.
- Never commit real credentials to Git; keep placeholders in `values.yaml`.
- Use Vault (or another external secrets manager) for critical credentials and rotation.
- Enable auditing and regularly review auth policies and service-account bindings.

