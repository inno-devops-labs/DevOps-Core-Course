# Lab 11 — Documentation (`k8s/SECRETS.md`)

## 1. Kubernetes Secrets

### Create secret (imperative)

```bash
kubectl -n lab11 create secret generic app-credentials \
  --from-literal=username=lab11-user \
  --from-literal=password=lab11-pass
```

### View secret (YAML)

```bash
kubectl -n lab11 get secret app-credentials -o yaml
```

Output (snippet):

```yaml
apiVersion: v1
data:
  password: bGFiMTEtcGFzcw==
  username: bGFiMTEtdXNlcg==
kind: Secret
metadata:
  name: app-credentials
  namespace: lab11
type: Opaque
```

### Decode values

```bash
kubectl -n lab11 get secret app-credentials -o jsonpath='{.data.username}' | base64 -d; echo
kubectl -n lab11 get secret app-credentials -o jsonpath='{.data.password}' | base64 -d; echo
```

Output:

```text
lab11-user
lab11-pass
```

### Base64 encoding vs encryption

- Secret `data` fields are **base64-encoded** in the API; this is **not** encryption.
- Anyone with `get secret` can decode the values.
- **Encryption at rest** is a separate cluster feature (etcd encryption configuration); it is **not** implied by “Secret” objects alone.

### Security implications

- Secrets are **not guaranteed to be encrypted at rest** unless the cluster enables etcd encryption providers.
- Use RBAC to restrict who can read Secrets; prefer external secret managers (e.g. Vault) when you need audit, rotation, and centralized policy.

---

## 2. Helm secret integration

### Chart layout (both application charts)

- `k8s/devops-app-java/templates/secrets.yaml`
- `k8s/devops-info-service/templates/secrets.yaml`
- `k8s/devops-app-java/templates/serviceaccount.yaml`
- `k8s/devops-info-service/templates/serviceaccount.yaml`
- `templates/deployment.yaml` in each chart: `envFrom` + optional Vault annotations
- `templates/_helpers.tpl`: `secretName`, `serviceAccountName`, `commonEnv` (named template for non-secret env)

Placeholder defaults live in each chart’s `values.yaml` under `secret.data`.

### Lint

```bash
helm lint k8s/devops-app-java
helm lint k8s/devops-info-service
```

Output:

```text
==> Linting k8s/devops-app-java
[INFO] Chart.yaml: icon is recommended

1 chart(s) linted, 0 chart(s) failed
==> Linting k8s/devops-info-service
[INFO] Chart.yaml: icon is recommended

1 chart(s) linted, 0 chart(s) failed
```

### Consumption in Deployment (`envFrom`)

`devops-info-service` (release `lab11-info`):

```text
        envFrom:
        - secretRef:
            name: lab11-info-devops-info-service-secret
```

`devops-app-java` (release `lab11-app`):

```text
        envFrom:
        - secretRef:
            name: lab11-app-devops-app-java-secret
```

### Verification

```bash
kubectl -n lab11 describe pod -l app.kubernetes.io/instance=lab11-info | grep -A4 "Environment Variables from"
```

Output:

```text
    Environment Variables from:
      lab11-info-devops-info-service-secret  Secret  Optional: false
    Environment:
      HOST:                     0.0.0.0
      PORT:                     5000
```

---

## 3. Resource management

Configured per chart in `values.yaml` (example — `devops-info-service` defaults):

```yaml
resources:
  requests:
    cpu: "50m"
    memory: "64Mi"
  limits:
    cpu: "200m"
    memory: "256Mi"
```

- **Requests**: used for scheduling and guaranteed minimum; affects QoS class.
- **Limits**: upper bound; CPU may be throttled, OOMKill if memory exceeded.
- **Choosing values**: measure baseline usage (e.g. metrics / load tests), set requests near steady state, limits above peak with headroom; adjust from production signals.

---

## 4. Vault integration

### Install Vault (Helm, dev mode)

```bash
helm repo add hashicorp https://helm.releases.hashicorp.com
helm repo update
helm upgrade --install vault hashicorp/vault -n lab11 \
  --set "server.dev.enabled=true" \
  --set "injector.enabled=true"
```

### Verify pods

```bash
kubectl -n lab11 get pods
```

Output (snippet):

```text
NAME                                              READY   STATUS    RESTARTS   AGE
lab11-info-devops-info-service-66b44f76f4-p9nmh   2/2     Running   0          ...
vault-0                                           1/1     Running   0          ...
vault-agent-injector-84f8c7cdff-bksr7             1/1     Running   0          ...
```

### Policy and role (sanitized)

**Policy — `devops-info-service` chart:**

```hcl
path "secret/data/devops-info-service/*" {
  capabilities = ["read"]
}
```

**Role — bound to the app ServiceAccount:**

- Role name: `devops-info-service-role`
- Bound namespace: `lab11`
- Bound service account name: `lab11-info-devops-info-service`
- Policies: `devops-info-service-policy`

**Policy — `devops-app-java` chart:**

```hcl
path "secret/data/devops-app-java/*" {
  capabilities = ["read"]
}
```

**Role:**

- Role name: `devops-app-role`
- Bound service account: `lab11-app-devops-app-java`
- Policies: `devops-app-java-policy`

KV data was stored with:

```bash
kubectl -n lab11 exec vault-0 -- sh -lc \
  'export VAULT_ADDR=http://127.0.0.1:8200 VAULT_TOKEN=root; \
   vault kv put secret/devops-info-service/config username="info-user" password="info-pass" api_token="info-token"'
```

### Agent injection (files)

```bash
POD=$(kubectl -n lab11 get pod -l app.kubernetes.io/instance=lab11-info -o jsonpath='{.items[0].metadata.name}')
kubectl -n lab11 exec "$POD" -c vault-agent -- ls -la /vault/secrets
kubectl -n lab11 exec "$POD" -c vault-agent -- cat /vault/secrets/app.env
```

Output:

```text
total 12
drwxrwxrwt    2 root     root            80 Apr  8 16:39 .
drwxr-xr-x    1 vault    vault         4096 Apr  8 16:39 ..
-rw-r--r--    1 vault    vault           88 Apr  8 16:39 app.env
-rw-r--r--    1 vault    vault          192 Apr  8 16:39 config
APP_VAULT_USERNAME=info-user
APP_VAULT_PASSWORD=info-pass
APP_VAULT_API_TOKEN=info-token
```

Charts set (when `vault.enabled: true`), among others:

- `vault.hashicorp.com/agent-inject: "true"`
- `vault.hashicorp.com/auth-path: "auth/kubernetes"` (must match the mount path; `kubernetes` alone is incorrect for the injector)
- `vault.hashicorp.com/role: "<role>"`
- `vault.hashicorp.com/agent-inject-secret-<name>: "<kv path>"`
- `vault.hashicorp.com/agent-inject-template-<name>: |` (bonus: rendered `.env`-style file)

### Sidecar injection pattern

1. The Vault Agent Injector mutates the Pod and adds init + sidecar containers and a shared `emptyDir` volume (mounted at `/vault/secrets`).
2. The init container authenticates with Vault using the pod’s Kubernetes service account JWT.
3. Vault Agent renders templates into files under `/vault/secrets`.
4. The application container reads secrets from files (not from `kubectl describe`).

---

## 5. Security analysis

| Topic | Kubernetes Secrets | HashiCorp Vault |
| --- | --- | --- |
| Storage | etcd (optionally encrypted at rest if enabled) | Dedicated store; policies and audit features |
| Distribution | Native `Secret` + projected/env/volume | Injected files via agent; centralized policies |
| Rotation | External process / re-apply manifests | Built-in workflows; dynamic secrets where used |

**When to use which**

- **Kubernetes Secrets**: small teams, lower sensitivity, minimal extra infrastructure.
- **Vault**: stricter compliance, centralized audit, rotation, many services/environments.

**Production recommendations**

1. Enable **etcd encryption at rest** and tighten RBAC for Secret access.
2. Run Vault in **HA** with durable storage (not dev mode).
3. Use **short-lived tokens**, narrow policies, and monitor secret access.
4. Prefer **GitOps + sealed/external secrets** patterns where appropriate; never commit real secrets.
