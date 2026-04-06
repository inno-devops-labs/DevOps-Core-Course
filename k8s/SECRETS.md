# Secret Management (Lab 11)

**Evidence types**

- **Recorded in this workspace:** outputs from `helm lint`, `helm template`, and `base64` decoding run on the course repo (no Kubernetes API available here).
- **Illustrative cluster transcripts:** realistic `kubectl` / `vault` style output for steps that require a live cluster. Namespaces, UIDs, and timestamps are representative; replace with your cluster’s values when you run the lab for credit.

---

## 1. Kubernetes Secrets

### Create a secret (imperative)

```bash
kubectl create secret generic app-credentials \
  --from-literal=username=demo-user \
  --from-literal=password=demo-password
```

**Illustrative `kubectl` response:**

```text
secret/app-credentials created
```

### View as YAML

```bash
kubectl get secret app-credentials -o yaml
```

**Illustrative API object** (stored `data` is base64; `resourceVersion` / `uid` will differ on your cluster):

```yaml
apiVersion: v1
kind: Secret
metadata:
  creationTimestamp: "2026-04-07T10:15:32Z"
  name: app-credentials
  namespace: default
  resourceVersion: "284915"
  uid: 8f3c1a2e-4b0d-4c8e-9a1f-2d3e4f5a6b7c
type: Opaque
data:
  username: ZGVtby11c2Vy
  password: ZGVtby1wYXNzd29yZA==
```

For literals `demo-user` and `demo-password`, the encodings above are correct (see decoding below).

### Decode base64 (recorded on this workspace)

```bash
echo "ZGVtby11c2Vy" | base64 -d
echo "ZGVtby1wYXNzd29yZA==" | base64 -d
```

**Actual shell output:**

```text
demo-user
demo-password
```

### Encoding vs encryption

- **Base64 in `data`** is reversible encoding for YAML transport, not encryption. Anyone with permission to `get` the Secret can decode it.
- **Encryption at rest:** etcd stores objects as plain unless the cluster enables [encryption providers](https://kubernetes.io/docs/tasks/administer-cluster/encrypt-data/). Many managed offerings enable or abstract this; self-managed clusters should configure it explicitly for production.

---

## 2. Helm secret integration

### Chart layout

| File | Purpose |
|------|---------|
| `templates/secrets.yaml` | `Secret` with `stringData` for `username` / `password` |
| `templates/deployment.yaml` | `envFrom` + `secretRef`; optional Vault annotations |
| `values.yaml` | Placeholders; override at install with `--set` or extra values files |
| `files/vault-agent-template.txt` | Vault Agent template (bonus path) |

### `helm lint` (recorded)

```bash
helm lint k8s
```

**Actual output:**

```text
==> Linting k8s
[INFO] Chart.yaml: icon is recommended

1 chart(s) linted, 0 chart(s) failed
```

### Rendered `Secret` and `Deployment` excerpt (recorded)

```bash
helm template lab11-demo k8s
```

**Actual excerpts** (secret + deployment env / resources / `envFrom`):

```yaml
# Source: my-python-app/templates/secrets.yaml
apiVersion: v1
kind: Secret
metadata:
  name: lab11-demo-my-python-app-credentials
  labels:
    app.kubernetes.io/name: my-python-app
    app.kubernetes.io/instance: lab11-demo
    app.kubernetes.io/version: "1.0.0"
    app.kubernetes.io/managed-by: Helm
    helm.sh/chart: my-python-app-0.1.0
type: Opaque
stringData:
  username: "changeme-user"
  password: "changeme-password"
---
# Source: my-python-app/templates/deployment.yaml
# ... metadata omitted ...
          resources:
            limits:
              cpu: 200m
              memory: 256Mi
            requests:
              cpu: 100m
              memory: 128Mi
          env:
            - name: PORT
              value: "8000"
          envFrom:
            - secretRef:
                name: lab11-demo-my-python-app-credentials
```

### Named template (`_helpers.tpl`)

`my-python-app.containerEnv` centralizes non-secret env (e.g. `PORT`); the Deployment uses `{{- include "my-python-app.containerEnv" . | nindent 12 }}`.

### `kubectl describe pod` (illustrative — values not shown)

```bash
kubectl describe pod -l app.kubernetes.io/instance=lab11-demo
```

**Illustrative fragment** (references secret; does not print `username` / `password`):

```text
    Environment:
      PORT:     8000
    Environment Variables from:
      lab11-demo-my-python-app-credentials  Secret  Optional: false
```

### Verify env inside pod (illustrative)

```bash
kubectl exec deploy/lab11-demo-my-python-app -- env | sort | grep -E '^(PORT|username|password)='
```

**Illustrative output** (matches chart defaults until you override secrets):

```text
PORT=8000
password=changeme-password
username=changeme-user
```

---

## 3. Resource management

### Values (default chart)

From `values.yaml` (requests/limits are tunable per environment via `values-dev.yaml` / `values-prod.yaml`):

```yaml
resources:
  requests:
    cpu: 100m
    memory: 128Mi
  limits:
    cpu: 200m
    memory: 256Mi
```

### Requests vs limits

- **Requests:** scheduling and guaranteed minimums; CPU shares and memory reservation behavior depend on cgroup settings.
- **Limits:** maximum CPU throttle point and memory cap before OOM kill.

### Choosing values

Profile with `kubectl top pod` or metrics, set requests near steady state, limits above expected bursts, and revisit after load tests.

---

## 4. HashiCorp Vault integration

### Install Vault (Helm, dev mode — learning only)

```bash
helm repo add hashicorp https://helm.releases.hashicorp.com
helm repo update
helm install vault hashicorp/vault \
  --set "server.dev.enabled=true" \
  --set "injector.enabled=true"
```

**Illustrative `helm install` completion:**

```text
NAME: vault
LAST DEPLOYED: Tue Apr  7 10:22:11 2026
NAMESPACE: default
STATUS: deployed
REVISION: 1
```

### Pods (illustrative)

```bash
kubectl get pods -l app.kubernetes.io/name=vault
```

```text
NAME                                    READY   STATUS    RESTARTS   AGE
vault-0                                 1/1     Running   0          2m14s
vault-agent-injector-7d9f8c6b4-xk2jq    1/1     Running   0          2m12s
```

### Vault CLI inside the pod (illustrative)

```bash
kubectl exec -it vault-0 -- sh -c 'vault secrets enable -path=secret kv-v2'
kubectl exec -it vault-0 -- sh -c 'vault kv put secret/myapp/config username="vault-user" password="vault-password"'
```

**Illustrative `vault kv put` response:**

```text
======= Secret Path =======
secret/data/myapp/config

======= Metadata =======
Key                Value
---                -----
created_time       2026-04-07T10:24:01.883847Z
custom_metadata    <nil>
deletion_time      n/a
destroyed          false
version            1
```

### Policy and role (sanitized, illustrative)

Policy `my-python-app-policy`:

```hcl
path "secret/data/myapp/*" {
  capabilities = ["read", "list"]
}
```

**Illustrative commands and confirmation:**

```text
$ vault policy write my-python-app-policy my-python-app-policy.hcl
Success! Uploaded policy: my-python-app-policy

$ vault write auth/kubernetes/role/my-python-app \
    bound_service_account_names=lab11-vault-my-python-app \
    bound_service_account_namespaces=default \
    policies=my-python-app-policy \
    ttl=24h
Success! Data written to: auth/kubernetes/role/my-python-app
```

Use the real ServiceAccount name from your Helm release (`helm template` shows `metadata.name` under `serviceaccount.yaml` when `vault.enabled=true`).

### Helm render with Vault file injection (recorded)

```bash
helm template lab11-vault k8s --set vault.enabled=true --set secrets.enabled=false
```

**Actual annotation fragment:**

```yaml
      annotations:
        vault.hashicorp.com/agent-inject: "true"
        vault.hashicorp.com/role: "my-python-app"
        vault.hashicorp.com/agent-inject-secret-config: "secret/data/myapp/config"
    spec:
      serviceAccountName: lab11-vault-my-python-app
```

### Helm render with template injection (recorded)

```bash
helm template lab11-vaulttpl k8s \
  --set vault.enabled=true \
  --set vault.template.enabled=true \
  --set secrets.enabled=false
```

**Actual `agent-inject-template-config` body** (Vault Agent Consul-template syntax; not evaluated by Helm):

```yaml
        vault.hashicorp.com/agent-inject-template-config: |

          {{- with secret "secret/data/myapp/config" -}}
          USERNAME={{ .Data.data.username }}
          PASSWORD={{ .Data.data.password }}
          {{- end -}}
```

### Proof under `/vault/secrets` (illustrative)

```bash
kubectl exec -it deploy/lab11-vault-my-python-app -- ls -la /vault/secrets
```

```text
total 4
drwxrwxrwt 2 root root   60 Apr  7 10:30 .
drwxr-xr-x 1 root root 4096 Apr  7 10:30 ..
-rw-r--r-- 1 root root   42 Apr  7 10:30 config
```

```bash
kubectl exec -it deploy/lab11-vault-my-python-app -- cat /vault/secrets/config
```

**Illustrative file mode (file injection):** raw JSON or secret payload as returned by the engine (often one line). **Template mode:** lines similar to:

```text
USERNAME=vault-user
PASSWORD=vault-password
```

### Sidecar injection pattern

The mutating webhook adds init + sidecar containers, mounts a shared volume, and the agent logs in (e.g. via Kubernetes auth), fetches secrets, and writes files under `/vault/secrets`. The application container reads those files without embedding credentials in the image.

---

## 5. Security analysis

| Topic | Kubernetes Secrets | Vault |
|--------|-------------------|--------|
| Storage | etcd objects; base64 in API; combine RBAC + etcd encryption | Central store, policies, audit logs, dynamic secrets |
| Ops cost | Low; native | Higher; run/maintain Vault or use managed Vault |
| Fit | In-cluster apps with good RBAC and encryption at rest | Strong policy, rotation, many teams, compliance |

**Production:** encrypt etcd secrets, least-privilege RBAC, no real secrets in Git, inject at deploy time, and use Vault or a cloud secrets manager when requirements exceed static Secrets.

---

## Bonus: templates, rotation, DRY

### Template annotation

Covered above: `vault.template.enabled=true` embeds `files/vault-agent-template.txt` into `vault.hashicorp.com/agent-inject-template-config`.

### Dynamic refresh and `vault.hashicorp.com/agent-inject-command`

Vault Agent caches secrets and renews based on lease TTL and configuration. When templates change on disk, you can run a hook via `vault.hashicorp.com/agent-inject-command` so a side process reloads config or signals the app. See [injector annotations](https://developer.hashicorp.com/vault/docs/platform/k8s/injector/annotations).

### Named Helm template

`my-python-app.containerEnv` in `templates/_helpers.tpl` keeps shared env definitions in one place and includes them from the Deployment.

### Illustrative rendered template file (after Agent runs)

```text
USERNAME=vault-user
PASSWORD=vault-password
```

---

## Quick validation commands (this repo)

```bash
helm lint k8s
helm template lab11-demo k8s
helm template lab11-vault k8s --set vault.enabled=true --set secrets.enabled=false
helm template lab11-vaulttpl k8s --set vault.enabled=true --set vault.template.enabled=true --set secrets.enabled=false
```
