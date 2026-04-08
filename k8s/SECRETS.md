# Lab 11 - Kubernetes Secrets and HashiCorp Vault

This submission extends the Lab 10 Helm chart with chart-managed Kubernetes Secrets, a dedicated ServiceAccount, and optional HashiCorp Vault Agent Injector annotations. The bonus task was intentionally not implemented.

## 1. Task 1 - Kubernetes Secrets Fundamentals

### Imperative secret creation
The required imperative command is:

```bash
kubectl create secret generic app-credentials \
  --from-literal=username=admin \
  --from-literal=password=super-secret-password
```

### View the Secret as YAML
```bash
kubectl get secret app-credentials -o yaml
```

Expected structure:
```yaml
apiVersion: v1
kind: Secret
metadata:
  name: app-credentials
type: Opaque
data:
  username: YWRtaW4=
  password: c3VwZXItc2VjcmV0LXBhc3N3b3Jk
```

### Decode the values
```bash
echo "YWRtaW4=" | base64 -d
echo "c3VwZXItc2VjcmV0LXBhc3N3b3Jk" | base64 -d
```

Decoded values:
- `username` -> `admin`
- `password` -> `super-secret-password`

### Cluster evidence captured on April 8, 2026
```bash
$ kubectl get secret app-credentials -o yaml
apiVersion: v1
data:
  password: c3VwZXItc2VjcmV0LXBhc3N3b3Jk
  username: YWRtaW4=
kind: Secret
metadata:
  creationTimestamp: "2026-04-08T18:59:46Z"
  name: app-credentials
  namespace: default
type: Opaque
```

```bash
$ echo YWRtaW4= | base64 -d
admin

$ echo c3VwZXItc2VjcmV0LXBhc3N3b3Jk | base64 -d
super-secret-password
```

### Encoding vs encryption
- Base64 is only an encoding format for safely transporting binary/text data in YAML or JSON.
- Anyone who can read the Secret object can decode its values immediately.
- Encryption means the data is protected cryptographically and requires the proper key to recover plaintext.

### Security implications
- Kubernetes Secrets are not encrypted at rest by default in a generic cluster installation.
- By default, Secret values are stored in etcd as base64-encoded data.
- Access is primarily protected by the Kubernetes API, RBAC, and transport security.

### What is etcd encryption and when to enable it?
- etcd encryption at rest uses an `EncryptionConfiguration` on the API server so Secret resources are encrypted before being stored in etcd.
- It should be enabled for any cluster that stores sensitive material and especially for shared, staging, and production environments.
- It reduces the impact of raw etcd backups or disk access being exposed.

## 2. Task 2 - Helm-managed Secrets

### Implemented chart changes
The Helm chart now includes:
- `k8s/python-app/templates/secrets.yaml` for the Kubernetes Secret
- `k8s/python-app/templates/serviceaccount.yaml` for a dedicated workload ServiceAccount
- updated `k8s/python-app/templates/deployment.yaml` to consume the Secret with `envFrom`
- updated `k8s/python-app/values.yaml` with secret and Vault settings

### Secret configuration model
Default values are placeholders:

```yaml
secrets:
  enabled: true
  name: ""
  data:
    username: change-me
    password: change-me
```

The template uses `stringData`, so Helm users can pass plain text and let Kubernetes encode it automatically.

### Deployment secret injection
The Deployment uses:

```yaml
envFrom:
  - secretRef:
      name: {{ include "python-app.secretName" . }}
```

This injects all keys from the Secret as environment variables in the application container.

### Resource limits
Resource requests and limits were already present in the chart and remain configurable through values files:
- default profile in `k8s/python-app/values.yaml`
- development overrides in `k8s/python-app/values-dev.yaml`
- production overrides in `k8s/python-app/values-prod.yaml`

### Local validation performed
Rendered templates validate successfully:

```bash
$ helm lint k8s/python-app
==> Linting k8s/python-app
[INFO] Chart.yaml: icon is recommended

1 chart(s) linted, 0 chart(s) failed
```

```bash
$ helm template lab11-test k8s/python-app
# rendered:
# - ServiceAccount
# - Secret
# - Service
# - Deployment with envFrom -> secretRef
# - existing Helm hook Jobs
```

### Cluster verification commands
When a cluster is available, use:

```bash
helm upgrade --install python-lab11 k8s/python-app \
  -f k8s/python-app/values-dev.yaml \
  --set secrets.data.username=lab11-user \
  --set secrets.data.password=lab11-password
```

```bash
kubectl get secret python-lab11-python-app-secret -o yaml
kubectl exec deploy/python-lab11-python-app -- printenv | grep -E '^(username|password)='
kubectl describe pod -l app.kubernetes.io/instance=python-lab11
```

Expected result:
- the Secret exists and contains `username` and `password`
- the pod sees both values as environment variables
- `kubectl describe pod` shows `secretRef` wiring, not the plaintext secret values

### Live verification captured on April 8, 2026
```bash
$ helm upgrade --install python-lab11 k8s/python-app \
  -f k8s/python-app/values-dev.yaml \
  --set secrets.data.username=lab11-user \
  --set secrets.data.password=lab11-password \
  --wait --timeout 5m

NAME: python-lab11
LAST DEPLOYED: Wed Apr  8 22:00:02 2026
NAMESPACE: default
STATUS: deployed
REVISION: 1
DESCRIPTION: Install complete
```

```bash
$ kubectl exec deploy/python-lab11-python-app -- printenv | grep -E '^(username|password|APP_ENV|PORT)='
APP_ENV=development
PORT=8000
password=lab11-password
username=lab11-user
```

```bash
$ kubectl describe pod -l app.kubernetes.io/instance=python-lab11
...
Environment Variables from:
  python-lab11-python-app-secret  Secret  Optional: false
Environment:
  APP_ENV:  development
  PORT:     8000
...
```

## 3. Task 3 - HashiCorp Vault Integration

### Chart support added
The Deployment now supports optional Vault Agent Injector annotations controlled by values:

```yaml
vault:
  enabled: false
  role: python-app
  secretPath: secret/data/python-app/config
  injectFileName: config
```

When enabled, the Deployment renders annotations like:
- `vault.hashicorp.com/agent-inject: "true"`
- `vault.hashicorp.com/role: "python-app"`
- `vault.hashicorp.com/agent-inject-secret-config: "secret/data/python-app/config"`
- `vault.hashicorp.com/agent-inject-template-config: | ...`

The injected file will be written to:
- `/vault/secrets/config`

### Vault installation and configuration commands
Use the following commands on a working local cluster:

```bash
helm repo add hashicorp https://helm.releases.hashicorp.com
helm repo update
helm upgrade --install vault hashicorp/vault \
  --set server.dev.enabled=true \
  --set injector.enabled=true
```

Verify:
```bash
kubectl get pods -l app.kubernetes.io/name=vault
```

Configure Vault:
```bash
kubectl exec -it vault-0 -- /bin/sh
export VAULT_ADDR='http://127.0.0.1:8200'
vault secrets enable -path=secret kv-v2
vault kv put secret/python-app/config username="vault-user" password="vault-password"
vault auth enable kubernetes
vault policy write python-app - <<'EOF'
path "secret/data/python-app/config" {
  capabilities = ["read"]
}
EOF
```

Configure Kubernetes auth inside the Vault pod:
```bash
TOKEN_REVIEW_JWT=$(cat /var/run/secrets/kubernetes.io/serviceaccount/token)
KUBE_CA_CERT=/var/run/secrets/kubernetes.io/serviceaccount/ca.crt
KUBE_HOST="https://${KUBERNETES_PORT_443_TCP_ADDR}:443"

vault write auth/kubernetes/config \
  token_reviewer_jwt="$TOKEN_REVIEW_JWT" \
  kubernetes_host="$KUBE_HOST" \
  kubernetes_ca_cert=@"$KUBE_CA_CERT"
```

Bind the role to the Helm-created ServiceAccount:
```bash
vault write auth/kubernetes/role/python-app \
  bound_service_account_names=python-lab11-python-app \
  bound_service_account_namespaces=default \
  policies=python-app \
  ttl=24h
```

Deploy the chart with Vault injection enabled:
```bash
helm upgrade --install python-lab11 k8s/python-app \
  -f k8s/python-app/values-dev.yaml \
  --set vault.enabled=true \
  --set vault.role=python-app \
  --set vault.secretPath=secret/data/python-app/config
```

Verify injection:
```bash
kubectl get pod -l app.kubernetes.io/instance=python-lab11
kubectl describe pod -l app.kubernetes.io/instance=python-lab11
kubectl exec deploy/python-lab11-python-app -- ls -l /vault/secrets
kubectl exec deploy/python-lab11-python-app -- cat /vault/secrets/config
```

Expected injected file content:
```text
username=vault-user
password=vault-password
```

### Live verification captured on April 8, 2026
Installed releases:
```bash
$ helm list
NAME         NAMESPACE REVISION UPDATED                              STATUS   CHART            APP VERSION
python-lab11 default   2        2026-04-08 22:05:05.928715 +0300 MSK deployed python-app-0.1.0 1.0.0
vault        default   1        2026-04-08 22:03:37.145215 +0300 MSK deployed vault-0.32.0     1.21.2
```

Vault pod:
```bash
$ kubectl get pods -l app.kubernetes.io/name=vault -o wide
NAME      READY   STATUS    RESTARTS   AGE    IP           NODE       NOMINATED NODE   READINESS GATES
vault-0   1/1     Running   0          2m9s   10.244.0.6   minikube   <none>           <none>
```

Injected pod evidence:
```bash
$ kubectl describe pod -l app.kubernetes.io/instance=python-lab11
...
Annotations:
  vault.hashicorp.com/agent-inject: true
  vault.hashicorp.com/agent-inject-secret-config: secret/data/python-app/config
  vault.hashicorp.com/agent-inject-status: injected
  vault.hashicorp.com/role: python-app
Init Containers:
  vault-agent-init:
    State: Terminated
    Reason: Completed
Containers:
  python-app:
    Mounts:
      /vault/secrets from vault-secrets (rw)
  vault-agent:
    State: Running
...
```

Injected file inside the app container:
```bash
$ kubectl exec deploy/python-lab11-python-app -c python-app -- ls -l /vault/secrets
total 4
-rw-r--r-- 1 100 appuser 44 Apr  8 19:05 config

$ kubectl exec deploy/python-lab11-python-app -c python-app -- cat /vault/secrets/config
username=vault-user
password=vault-password
```

Vault Agent logs:
```bash
$ kubectl logs pod/python-lab11-python-app-696c6d486-fktl7 -c vault-agent --tail=20
...
agent.auth.handler: authentication successful, sending token to sinks
agent.template.server: template server received new token
...
```

Service reachability:
```bash
$ minikube service python-lab11-python-app --url
http://127.0.0.1:55527

$ curl -s http://127.0.0.1:55527/health
{"status":"healthy","timestamp":"2026-04-08T19:06:07.660041+00:00","uptime_seconds":51}
```
