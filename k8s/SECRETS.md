# Lab 11 — Kubernetes Secrets & HashiCorp Vault

## 1. Kubernetes Secrets

### 1.1 Create and inspect a Secret with kubectl

```bash
$ kubectl create secret generic app-credentials \
  --from-literal=username=lab11-user \
  --from-literal=password='Lab11-P@ssw0rd!'
secret/app-credentials created

$ kubectl get secret app-credentials -o yaml
apiVersion: v1
data:
  password: TGFiMTEtUEBzc3cwcmQh
  username: bGFiMTEtdXNlcg==
kind: Secret
metadata:
  name: app-credentials
  namespace: default
type: Opaque
```

### 1.2 Decode values (base64 demonstration)

```bash
$ echo 'bGFiMTEtdXNlcg==' | base64 -d
lab11-user

$ echo 'TGFiMTEtUEBzc3cwcmQh' | base64 -d
Lab11-P@ssw0rd!
```

### 1.3 Base64 encoding vs encryption

- Base64 is only an encoding format for transport/storage; it is fully reversible without a key.
- Encryption requires a cryptographic key and protects confidentiality when stored.
- Kubernetes Secret manifests store values base64-encoded, not encrypted by default.

### 1.4 Security implications

- Kubernetes Secrets are **not encrypted at rest by default** unless encryption at rest is explicitly configured.
- Without at-rest encryption, Secret data is stored in etcd as plain (readable) values after base64 decode.
- Production clusters should enable etcd encryption at rest and strict RBAC for Secret access.

### 1.5 etcd encryption and when to enable

Enable etcd encryption at rest in all non-trivial environments (staging/prod, shared clusters, any compliance requirement). It reduces impact if etcd snapshots/backups or disk data are exposed.

---

## 2. Helm Secret Integration

### 2.1 Chart structure changes

```text
k8s/devops-info/
├── values.yaml
└── templates/
    ├── _helpers.tpl
    ├── deployment.yaml
    ├── secrets.yaml
    └── serviceaccount.yaml
```

Implemented:
- `templates/secrets.yaml` creates an Opaque Secret using `stringData`.
- `values.yaml` now contains:
  - `secret.enabled`, `secret.name`, `secret.data.username`, `secret.data.password`
  - `serviceAccount.create`, `serviceAccount.name`
  - `vault.*` toggles for Task 3
- `templates/deployment.yaml` now:
  - uses `serviceAccountName`
  - consumes Secret via `envFrom.secretRef`
  - supports Vault injector annotations when enabled

### 2.2 Deploy and verify env var injection

```bash
$ helm upgrade --install devops-info-dev k8s/devops-info \
  -f k8s/devops-info/values-dev.yaml \
  --set secret.data.username=helm-user \
  --set secret.data.password='Helm-Secret-123!'
Release "devops-info-dev" has been upgraded. Happy Helming!
STATUS: deployed
```

Pod environment verification (actual secret values intentionally masked):

```bash
$ kubectl exec <pod> -- sh -c 'printenv | grep -E "^(username|password|HOST|PORT)=" | sort'
HOST=0.0.0.0
PORT=8080
password=***
username=***
```

`kubectl describe pod` shows references, not plaintext values:

```bash
Environment Variables from:
  devops-info-dev-secret  Secret  Optional: false
Environment:
  HOST:  0.0.0.0
  PORT:  8080
```

### 2.3 Resource limits configuration

Current deployment (dev profile):

```bash
$ kubectl get deploy devops-info-dev -o jsonpath='{.spec.template.spec.containers[0].resources}'
{"limits":{"cpu":"100m","memory":"128Mi"},"requests":{"cpu":"50m","memory":"64Mi"}}
```

Requests vs limits:
- `requests`: minimum resources reserved for scheduling and baseline performance.
- `limits`: hard cap to prevent a container from over-consuming node resources.

How to choose values:
- Start from observed steady-state usage (metrics server/Prometheus).
- Set requests near p50-p75 usage.
- Set limits near expected burst (p95+), avoiding excessive throttling/OOM.
- Recalibrate after load testing and production telemetry.

---

## 3. Vault Integration

### 3.1 Vault installation via Helm

```bash
$ helm repo add hashicorp https://helm.releases.hashicorp.com
$ helm repo update
$ helm upgrade --install vault hashicorp/vault \
  --set server.dev.enabled=true \
  --set injector.enabled=true
```

Runtime verification:

```bash
$ kubectl get pods | rg vault
vault-0                                 1/1   Running
vault-agent-injector-75998c9b76-w7b55   1/1   Running
```

### 3.2 Configure KV secrets engine and app secret

Configured inside `vault-0`:

```bash
vault secrets enable -path=secret kv-v2
vault kv put secret/myapp/config username="vault-user" password="Vault-Strong-123!"
vault kv get secret/myapp/config
```

### 3.3 Configure Kubernetes auth, policy, and role

Commands executed in Vault:

```bash
vault auth enable kubernetes
vault write auth/kubernetes/config \
  token_reviewer_jwt="$(cat /var/run/secrets/kubernetes.io/serviceaccount/token)" \
  kubernetes_host="https://kubernetes.default.svc:443" \
  kubernetes_ca_cert=@/var/run/secrets/kubernetes.io/serviceaccount/ca.crt

vault policy write devops-info-policy /tmp/devops-info-policy.hcl
vault write auth/kubernetes/role/devops-info \
  bound_service_account_names=devops-info-sa \
  bound_service_account_namespaces=default \
  policies=devops-info-policy \
  ttl=1h
```

Policy and role (sanitized) verification:

```bash
$ vault policy read devops-info-policy
path "secret/data/myapp/config" {
  capabilities = ["read"]
}

$ vault read auth/kubernetes/role/devops-info
bound_service_account_names       [devops-info-sa]
bound_service_account_namespaces  [default]
policies                          [devops-info-policy]
ttl                               1h
```

### 3.4 Vault Agent sidecar injection verification

Helm deployment enabled with annotations:

```yaml
vault.hashicorp.com/agent-inject: "true"
vault.hashicorp.com/role: "devops-info"
vault.hashicorp.com/agent-inject-secret-config: "secret/data/myapp/config"
```

Pod proof:

```bash
$ kubectl get pods -l app.kubernetes.io/instance=devops-info-dev
devops-info-dev-58bd6949b8-jn2pk   2/2   Running
```

The `2/2` shows app container + `vault-agent` sidecar.

Injected file proof:

```bash
$ kubectl exec <pod> -c devops-info -- ls -la /vault/secrets
-rw-r--r-- 1 app 1000 ... config
```

Path used by injector:
- `/vault/secrets/config`

### 3.5 Sidecar injection pattern explanation

- Mutating webhook sees Vault annotations and injects Vault Agent into the Pod.
- Agent authenticates to Vault using the Pod service account token (Kubernetes auth method).
- Agent fetches secrets according to annotation path and writes them to an in-memory volume mounted at `/vault/secrets`.
- Application reads secrets from files without embedding long-lived credentials in image/env.

---

## 4. Security Analysis

### 4.1 Kubernetes Secrets vs Vault

Kubernetes Secrets:
- Simple and native to K8s.
- Good for low-complexity workloads.
- Requires etcd encryption + strict RBAC for acceptable security.
- Rotation and dynamic credentials are manual unless extra tooling is added.

Vault:
- Centralized secret lifecycle, policies, auth methods, audit support.
- Better for multi-service, multi-environment, and compliance-sensitive deployments.
- Supports dynamic secrets, leases, and short TTL credentials.
- More operational overhead (Vault cluster, policies, auth integration).

### 4.2 When to use each

Use Kubernetes Secrets when:
- Small cluster, low-risk internal data, simple operations.

Use Vault when:
- You need strong policy boundaries, dynamic/rotated secrets, detailed auditability, or enterprise controls.

### 4.3 Production recommendations

1. Enable etcd encryption at rest for all Secret resources.
2. Apply least-privilege RBAC (avoid broad `get/list` on Secrets).
3. Prefer external secret manager (Vault or cloud secret service) for sensitive credentials.
4. Use short-lived credentials and automated rotation.
5. Avoid storing real secrets in Git/Helm values files.
6. Add secret access audit/alerting and periodic permission reviews.
