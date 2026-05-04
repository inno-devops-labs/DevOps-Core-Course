# Lab 11 — Kubernetes Secrets & HashiCorp Vault

## 1. Kubernetes Secrets

### Secret creation

The first step of the lab was to create a native Kubernetes Secret using the imperative `kubectl create secret generic` command.

```bash
kubectl create secret generic app-credentials \
  --from-literal=username=admin \
  --from-literal=password=secret123
```

### Viewing the Secret

The created Secret was inspected in YAML format.

```yaml
apiVersion: v1
data:
  password: c2VjcmV0MTIz
  username: YWRtaW4=
kind: Secret
metadata:
  creationTimestamp: "2026-04-01T06:25:56Z"
  name: app-credentials
  namespace: default
  resourceVersion: "1325"
  uid: 8a470b46-7805-4195-929c-844594d472f7
type: Opaque
```

### Decoding the values

The secret data was manually decoded:

```bash
echo "c2VjcmV0MTIz" | base64 -d
echo "YWRtaW4=" | base64 -d
```

Decoded values:
- `password` → `secret123`
- `username` → `admin`

### Base64 encoding vs encryption

Kubernetes Secrets are **base64-encoded**, not encrypted by default.  
Base64 is only a transport/storage encoding and provides no actual security. Anyone with API access and permission to read the Secret can decode the values immediately.

### Security implications

By default, Kubernetes Secrets are stored in etcd and are not strongly protected unless additional cluster configuration is enabled.

For production:
- enable **etcd encryption at rest**
- limit access through **RBAC**
- avoid storing real production secrets directly in Git
- prefer an external secret manager such as **HashiCorp Vault**

---

## 2. Helm Secret Integration

### Chart changes

The Helm chart from Lab 10 was extended with a new template:

- `app-python-chart/templates/secrets.yaml`

This file creates a Kubernetes Secret for the application using values from `values.yaml`.

### Secret template

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: {{ include "app-python-chart.fullname" . }}-secret
  labels:
    {{- include "app-python-chart.labels" . | nindent 4 }}
type: Opaque
stringData:
  username: {{ .Values.secret.username }}
  password: {{ .Values.secret.password }}
```

### Values configuration

The Helm values file was extended with placeholder defaults:

```yaml
secret:
  username: "placeholder-user"
  password: "placeholder-password"
```

These are placeholder values only and should be overridden during real deployments.

### Secret consumption in Deployment

The Deployment template was updated to inject all Secret keys as environment variables using `envFrom`:

```yaml
envFrom:
  - secretRef:
      name: {{ include "app-python-chart.fullname" . }}-secret
```

### Verification in the Pod

Secret injection was verified by executing into a running application pod:

```bash
kubectl exec -it app-release-app-python-chart-7bd8499df8-6ffwn -- env | grep -E 'username|password|USERNAME|PASSWORD'
```

Output:

```text
password=placeholder-password
username=placeholder-user
```

This confirms that the Helm-managed Secret was successfully injected as environment variables.

### Visibility in `kubectl describe pod`

The pod description showed that the Secret was referenced:

```text
Environment Variables from:
  app-release-app-python-chart-secret  Secret  Optional: false
Environment:                           <none>
```

Important observation:
- Kubernetes shows the Secret reference
- Kubernetes does **not** show the actual secret values in `kubectl describe pod`

This is expected and is the correct security behavior.

---

## 3. Resource Management

Resource requests and limits remained configured in the Deployment template.

```yaml
resources:
  limits:
    cpu: 200m
    memory: 256Mi
  requests:
    cpu: 100m
    memory: 128Mi
```

### Requests vs limits

- **requests** define the minimum resources reserved for the container
- **limits** define the maximum resources the container is allowed to consume

### Why these values were chosen

The application is a small Flask service, so modest values are sufficient:
- enough CPU and memory for stable startup and health checks
- enough control to prevent a pod from consuming too much of the node

In a production environment, these values should be chosen using:
- profiling
- load testing
- historical metrics from monitoring tools

---

## 4. Vault Integration

### Vault installation

Vault was installed using the official HashiCorp Helm chart in development mode with the injector enabled.

```bash
helm repo add hashicorp https://helm.releases.hashicorp.com
helm repo update

helm install vault hashicorp/vault \
  --set "server.dev.enabled=true" \
  --set "injector.enabled=true"
```

### Vault installation verification

After installation, the following pods were running:

- `vault-0`
- `vault-agent-injector-848dd747d7-xqmhd`

This confirmed that:
- the Vault server was running
- the Vault Agent Injector admission webhook was active

### Secret engine and secret creation

Inside the Vault pod, a KV secret was created.

Commands used:

```bash
vault kv put secret/myapp/config username="admin" password="vault-secret"
vault kv get secret/myapp/config
```

Verification output showed:

- `username = admin`
- `password = vault-secret`

### Kubernetes auth configuration

The Kubernetes authentication method was enabled and configured inside Vault.

Commands used:

```bash
vault auth enable kubernetes

vault write auth/kubernetes/config \
  kubernetes_host="https://$KUBERNETES_PORT_443_TCP_ADDR:443"
```

### Policy configuration

A policy was created to allow read access to the application secret path:

```hcl
path "secret/data/myapp/config" {
  capabilities = ["read"]
}
```

The policy was uploaded with:

```bash
vault policy write app-policy /tmp/app-policy.hcl
```

### Role configuration

A Vault role was created and bound to the `default` service account in the `default` namespace:

```bash
vault write auth/kubernetes/role/app-role \
  bound_service_account_names=default \
  bound_service_account_namespaces=default \
  policies=app-policy \
  ttl=1h
```

### Vault Agent injection annotations

The application Deployment template was updated with Vault annotations:

```yaml
annotations:
  vault.hashicorp.com/agent-inject: "true"
  vault.hashicorp.com/role: "app-role"
  vault.hashicorp.com/agent-inject-secret-config: "secret/data/myapp/config"
```

### Proof of sidecar injection

After upgrading the Helm release, the application pods changed from `1/1` containers to `2/2` containers.

This indicates:
- the main application container
- the Vault agent sidecar container

In addition, `kubectl describe pod` showed:

- `vault-agent-init` init container
- `vault-agent` sidecar container
- annotation `vault.hashicorp.com/agent-inject-status: injected`

This is direct proof that sidecar injection worked.

### Injected secret file

Inside the application pod, the following commands were used:

```bash
kubectl exec -it app-release-app-python-chart-5b6797cdd6-8jfz5 -- ls -R /vault/secrets
kubectl exec -it app-release-app-python-chart-5b6797cdd6-8jfz5 -- cat /vault/secrets/config
```

Observed result:

```text
/vault/secrets:
config
```

Secret file content:

```text
data: map[password:vault-secret username:admin]
metadata: map[created_time:2026-04-01T06:36:23.833233388Z custom_metadata:<nil> deletion_time: destroyed:false version:1]
```

This proves that Vault successfully rendered the secret into the pod filesystem at `/vault/secrets/config`.

### Sidecar injection pattern explanation

The Vault Agent Injector works as a mutating admission webhook:
1. It intercepts pod creation
2. It injects an init container and a sidecar
3. The init container authenticates and prepares secret rendering
4. The sidecar maintains access to Vault and writes secrets into a shared in-memory volume
5. The main application container reads the rendered files from `/vault/secrets`

This pattern avoids hardcoding secrets in application manifests and avoids putting real secret values directly in the pod spec.

---

## 5. Security Analysis

### Kubernetes Secrets vs Vault

| Aspect | Kubernetes Secrets | Vault |
|---|---|---|
| Storage | etcd | external secret backend |
| Protection | base64 only by default | purpose-built secret manager |
| Rotation | manual | supports dynamic and centralized secret workflows |
| Access control | Kubernetes RBAC | policies, roles, auth methods |
| Secret delivery | env vars / mounted secret objects | file injection, dynamic retrieval, templates |
| Production readiness | acceptable for simple cases | much stronger for real production systems |

### When to use Kubernetes Secrets

Kubernetes Secrets are acceptable when:
- the environment is simple
- the team needs basic secret injection
- secrets are low-risk
- there is no external secret manager available yet

### When to use Vault

Vault is more appropriate when:
- secrets are high-value
- strong access control is required
- centralized secret governance is needed
- secret rotation matters
- multiple workloads and platforms must share a common secret system

### Production recommendations

For production systems:
- do not commit real secrets to Git
- enable etcd encryption at rest
- use least-privilege RBAC
- separate service accounts for applications
- use Vault or another enterprise-grade secret manager
- rotate secrets regularly
- monitor secret access and injector behavior

---

## 6. Final Result

By the end of the lab, the following were implemented successfully:

- native Kubernetes Secret creation and decoding
- Helm-managed Secret templating and environment injection
- resource requests and limits retained in the Deployment
- HashiCorp Vault installed via Helm
- KV secret stored in Vault
- Kubernetes auth configured in Vault
- Vault policy and role created
- Vault Agent sidecar injection enabled
- secret file successfully rendered into the application pod

This lab demonstrated the progression from simple Kubernetes-native secret handling to a much more secure and production-oriented secret delivery model using HashiCorp Vault.
