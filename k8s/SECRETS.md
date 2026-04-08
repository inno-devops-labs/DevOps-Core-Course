# Lab 11 — Secret Management Report

This document covers Kubernetes native Secrets, Helm-managed secrets in the `devops-info-service` chart, container resource limits, HashiCorp Vault with the Kubernetes auth method and Vault Agent Injector, optional Vault Agent templating (bonus), and a short security comparison.

---

## 1. Kubernetes Secrets 

### Creating and viewing a Secret

Use imperative `kubectl` (or the helper script `k8s/scripts/lab11-task1-app-credentials.sh`):

```bash
kubectl create secret generic app-credentials \
  --from-literal=username=demo-user \
  --from-literal=password=demo-pass
kubectl get secret app-credentials -o yaml
```

### Decoding values

Keys under `data` are **base64-encoded**. Decode (macOS/Linux):

```bash
kubectl get secret app-credentials -o jsonpath='{.data.username}' | base64 -d; echo
kubectl get secret app-credentials -o jsonpath='{.data.password}' | base64 -d; echo
```

### Base64 encoding vs encryption

- **Base64** in `Secret` objects is **encoding**, not encryption. Anyone who can read the Secret through the API (within RBAC) can decode the values.
- **Encryption at rest** in etcd is a separate cluster feature (KMS or static configuration). It is **not** guaranteed on every distribution by default; verify for your platform (EKS, GKE, kubeadm with `--encryption-provider-config`, etc.).
- **When to enable etcd encryption:** production clusters where you need defense-in-depth for control-plane disks and backups.

References: [Secrets](https://kubernetes.io/docs/concepts/configuration/secret/), [Encrypting data at rest](https://kubernetes.io/docs/tasks/administer-cluster/encrypt-data/).

### Security implications 

Secrets are not “encrypted” merely because they are base64 in YAML. Combine RBAC, etcd encryption at rest where required, and external secret managers for higher assurance.

---

## 2. Helm Secret Integration (Task 2)

### Chart structure

| File | Purpose |
|------|---------|
| `k8s/devops-info-service/templates/secrets.yaml` | `Secret` with `stringData` keys `username` / `password` when `secrets.enabled` is true |
| `k8s/devops-info-service/values.yaml` | Placeholder `secrets.*` values (do not commit real secrets) |
| `k8s/devops-info-service/templates/deployment.yaml` | `envFrom` + `secretRef` to load all keys; `env` from `values.env` plus `include "devops-info-service.extraEnv"` |
| `k8s/devops-info-service/templates/_helpers.tpl` | Named template `devops-info-service.extraEnv` (DRY) |
| `k8s/devops-info-service/templates/serviceaccount.yaml` | ServiceAccount for Vault Kubernetes auth |

### How the Deployment consumes the Secret

- **`envFrom` / `secretRef`:** injects every key of the Helm-created Secret as environment variables. Key names are used as-is (`username`, `password`), so they appear as `username` and `password`, not `USERNAME`/`PASSWORD`, unless you rename keys in the Secret.
- **`kubectl describe pod`** does not print secret values; it may show that a secret is referenced.

### Install with overrides

The **Helm release name** can differ from the workload name (`fullnameOverride: devops-info-service`). If resources were first installed as release `devops-dev`, reuse that release name or `helm uninstall` the old release first. Example:

```bash
cd k8s/devops-info-service
helm upgrade --install devops-dev . \
  -f values-dev.yaml \
  --set secrets.username=alice \
  --set secrets.password='replace-at-deploy-time'
```

### Verification (env in the Pod)

```bash
kubectl exec -it deploy/devops-info-service -n default -- \
  env | grep -E '^(username|password|CHART_NAME|RELEASE_NAME)='
```

Redact sensitive values in submissions (e.g. show `password=<redacted>`).

---

## 3. Resource Management (Task 2)

### Configuration

`values.yaml`, `values-dev.yaml`, and `values-prod.yaml` define `resources.requests` and `resources.limits` for the application container (for example, dev may use lower requests/limits than prod).

### Requests vs limits

- **Requests:** used by the scheduler for placement; kubelet uses them for QoS class and as a minimum guarantee where cgroups allow.
- **Limits:** hard cap; CPU may be throttled, memory may trigger OOMKill.

### Choosing values

Start from measured CPU/memory under load, add headroom. For **Guaranteed** QoS, set limits equal to requests for the container. For bursty workloads, requests can be lower than limits (**Burstable** QoS).

---

## 4. HashiCorp Vault Integration (Task 3)

### Defaults in this chart

- `vault.secretPath`: `secret/data/devops-info-service/config` (KV v2 API path)
- `vault.role`: `devops-info-service`
- Pod `ServiceAccount`: `devops-info-service` (same namespace as the release, e.g. `default`)

### Installing Vault (dev mode + injector)

Preferred (when the Helm repo is reachable):

```bash
helm repo add hashicorp https://helm.releases.hashicorp.com
helm repo update
helm upgrade --install vault hashicorp/vault \
  --set server.dev.enabled=true \
  --set injector.enabled=true
```

**Workaround used in this lab:** the HashiCorp Helm repo returned **403 Forbidden** (network/region). Vault was installed from the official chart source:

```bash
git clone --depth 1 https://github.com/hashicorp/vault-helm.git /tmp/vault-helm
cd /tmp/vault-helm
helm upgrade --install vault . \
  --set server.dev.enabled=true \
  --set injector.enabled=true
```

### KV v2 and application secret

Enable KV v2 on mount `secret` (if not already), then:

```bash
vault kv put secret/devops-info-service/config username="vault-user" password="vault-pass"
```

The logical path `secret/data/devops-info-service/config` matches `vault.secretPath` in `values.yaml`.

### Kubernetes auth, policy, and role (sanitized)

1. **RBAC:** bind the Vault server `ServiceAccount` (typically `vault` in `default`) to `system:auth-delegator` so Vault can use the TokenReview API:

   ```bash
   kubectl create clusterrolebinding vault-auth-delegator \
     --clusterrole=system:auth-delegator \
     --serviceaccount=default:vault
   ```

2. **Enable and configure Kubernetes auth** inside Vault (`vault auth enable kubernetes`, then `vault write auth/kubernetes/config` with cluster CA, API host, and token reviewer JWT).

3. **Policy (example, read-only on app path):**

   ```hcl
   path "secret/data/devops-info-service/*" {
     capabilities = ["read"]
   }
   ```

4. **Role (parameters, sanitized):** bind policy `devops-info-service` to ServiceAccount `devops-info-service` in namespace `default`, TTL e.g. `1h`. Vault may warn about missing **audience** on the role; acceptable for this lab.

### Deploy the app with Vault Agent injection

From the repository root, using the same Helm release name as in Task 2:

```bash
helm upgrade --install devops-dev ./k8s/devops-info-service \
  -f k8s/devops-info-service/values-dev.yaml \
  --set vault.enabled=true \
  --set vault.role=devops-info-service
```

### Injection verification and sidecar pattern

- **Check pods:** Vault-related pods running; app pod should be `2/2` (app + `vault-agent`).
- **Files:** default mount path `/vault/secrets/`; filename from `vault.secretFileName` (default `config`).

The **sidecar injection pattern:** a mutating webhook adds Vault Agent init and sidecar containers. They authenticate to Vault using the pod’s Kubernetes service account token, fetch secrets per annotations, and materialize them as files (or rendered templates). The application does not embed long-lived Vault tokens in the image.

---

## 5. Bonus — Vault Agent Templates

### Template annotation

With `vault.bonusAgentTemplate=true`, the chart adds `vault.hashicorp.com/agent-inject-template-config` populated from `files/vault-agent-config.ctmpl` (Vault Agent template syntax, not Helm).

### Rendered format

Secrets are rendered as a small **`.env`-style** file (multiple key/value lines from one KV path in a single file), satisfying the bonus requirement for a custom format and multiple fields in one file.

### Dynamic updates and `agent-inject-command`

Vault Agent can renew leases and rewrite rendered files when secrets change in Vault. The annotation `vault.hashicorp.com/agent-inject-command` can run a command after a template is updated (e.g. reload or signal the app).

### Helm named templates (DRY)

`devops-info-service.extraEnv` in `_helpers.tpl` is included in the Deployment for `CHART_NAME` and `RELEASE_NAME`, avoiding duplicated `env` blocks.

### Benefits of templating

You control the on-disk format (e.g. `.env`, JSON) independent of the raw KV JSON, which helps applications that expect a specific config file layout.

### Helm `Files` path (Helm 3 vs 4)

Helm 4 may expose chart files under a `files/` prefix in `.Files`. The Deployment template uses `coalesce` so both `files/vault-agent-config.ctmpl` and `vault-agent-config.ctmpl` work.

---

## 6. Security Analysis (Task 4)

| Topic | Kubernetes Secrets | Vault |
|--------|---------------------|--------|
| **Storage** | API object in etcd (optionally encrypted at rest) | Central store; policies, audit, dynamic secrets |
| **Access** | RBAC on Secret objects | Fine-grained policies, auth methods, audit log |
| **Rotation** | External automation or operators | Leases, dynamic secrets, rotation workflows |
| **Fit** | Simple workloads, bootstrap, low sensitivity | Production, compliance, many teams, strict audit |

**When to use which:** use native Secrets for simplicity and when cluster RBAC plus optional etcd encryption is enough. Use Vault (or another enterprise manager) when you need centralized policy, audit, rotation, and multiple teams.

**Production recommendations:** avoid committing real credentials to Git; use placeholders in `values.yaml` and inject secrets at deploy time (`--set`, CI/CD secrets). Prefer external secret management, narrow RBAC, and etcd encryption at rest where required.

---

## Evidence

### Task 1 — Kubernetes Secrets

Cluster: minikube, namespace `default`, API server from kubeconfig.

```text
kubectl config view --minify | grep server
    server: https://127.0.0.1:50871
./k8s/scripts/lab11-task1-app-credentials.sh
secret/app-credentials created
=== kubectl get secret app-credentials -o yaml ===
apiVersion: v1
data:
  password: ZGVtby1wYXNz
  username: ZGVtby11c2Vy
kind: Secret
metadata:
  name: app-credentials
  namespace: default
type: Opaque
=== Decoded (base64 -d) ===
username: demo-user
password: demo-pass
```

The `data` fields are base64-encoded in the API; decoding recovers the literal values (encoding, not encryption).

### Task 2 — Helm secrets and env verification

Helm release name **`devops-dev`**; workload name **`devops-info-service`** (`fullnameOverride`).

If a new release name conflicts with existing resources owned by another release, Helm reports an ownership error (release name in annotations must match). Using **`devops-dev`** consistently resolves this.

```text
helm upgrade --install devops-dev . -f values-dev.yaml \
  --set secrets.username=alice --set secrets.password='...'
```

```text
Release "devops-dev" has been upgraded. Happy Helming!
STATUS: deployed
REVISION: 4
```

```text
kubectl exec -it deploy/devops-info-service -n default -- env | grep -E '^(username|password|CHART_NAME|RELEASE_NAME)='
password=...
username=alice
CHART_NAME=devops-info-service
RELEASE_NAME=devops-dev
```

### Task 3 — Vault installation and injection

Helm repo returned **403**; Vault installed from **GitHub** `vault-helm` chart (see §4). RBAC binding for TokenReview created. Vault configured: KV v2, `vault kv put`, Kubernetes auth, policy, role (audience warning accepted for lab).

```text
helm upgrade --install devops-dev ./k8s/devops-info-service \
  -f k8s/devops-info-service/values-dev.yaml \
  --set vault.enabled=true \
  --set vault.role=devops-info-service
REVISION: 5
```

```text
kubectl get pods -n default -l app.kubernetes.io/instance=devops-dev
NAME                                   READY   STATUS    RESTARTS   AGE
devops-info-service-64fb5b474c-66ttc   2/2     Running   0          13s
```

```text
kubectl exec -n default -it deploy/devops-info-service -- ls -la /vault/secrets/
-rw-r--r-- 1  100 1000  173 ... config
```

```text
kubectl exec -n default -it deploy/devops-info-service -- cat /vault/secrets/config
data: map[password:vault-pass username:vault-user]
metadata: map[created_time:... version:1]
```

### Bonus — Template rendering

```text
helm upgrade --install devops-dev ./k8s/devops-info-service \
  -f k8s/devops-info-service/values-dev.yaml \
  --set vault.enabled=true \
  --set vault.role=devops-info-service \
  --set vault.bonusAgentTemplate=true
REVISION: 6
```

```text
kubectl rollout status deploy/devops-info-service -n default
deployment "devops-info-service" successfully rolled out
kubectl get pods -n default -l app.kubernetes.io/instance=devops-dev
devops-info-service-754544ff9-wg4fh   2/2     Running   0          40s
```

```text
kubectl exec -n default -it deploy/devops-info-service -- cat /vault/secrets/config
# Rendered by Vault Agent (bonus template); not Helm
APP_USERNAME=vault-user
APP_PASSWORD=vault-pass
```

