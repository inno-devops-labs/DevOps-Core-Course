# Lab 11 - Kubernetes Secrets and HashiCorp Vault

Validated on `2026-04-09` with:

- `helm v4.1.3`
- `kubectl v1.35.3`
- `kind v0.31.0`
- Kubernetes `v1.35.0`
- Vault Helm chart `0.32.0`
- Vault `1.21.2`
- Vault Agent Injector image `hashicorp/vault-k8s:1.7.2`

Environment note:

- The host kubeconfig pointed at a stale forwarded API endpoint, so live validation used `docker exec lab09-control-plane ...` with `/etc/kubernetes/admin.conf`.

## 1. Kubernetes Secrets

### Secret creation

I created the required native secret imperatively:

```bash
docker exec lab09-control-plane kubectl --kubeconfig=/etc/kubernetes/admin.conf \
  -n devops-lab11 create secret generic app-credentials \
  --from-literal=username=lab11-user \
  --from-literal=password='lab11-pass-123'
```

Result:

```text
secret/app-credentials created
```

### Secret inspection

```bash
docker exec lab09-control-plane kubectl --kubeconfig=/etc/kubernetes/admin.conf \
  -n devops-lab11 get secret app-credentials -o yaml
```

Output:

```yaml
apiVersion: v1
data:
  password: bGFiMTEtcGFzcy0xMjM=
  username: bGFiMTEtdXNlcg==
kind: Secret
metadata:
  name: app-credentials
  namespace: devops-lab11
type: Opaque
```

### Base64 decode demonstration

```bash
printf '%s' 'bGFiMTEtdXNlcg==' | base64 -d
printf '%s' 'bGFiMTEtcGFzcy0xMjM=' | base64 -d
```

Output:

```text
lab11-user
lab11-pass-123
```

### Encoding vs encryption

- Kubernetes Secrets are base64-encoded in the API object. Base64 is transport formatting, not cryptographic protection.
- Anyone with permission to read the Secret can decode it immediately.
- By default, Kubernetes does not encrypt Secret objects at rest in etcd.
- Production clusters should enable `EncryptionConfiguration` on the API server so Secret payloads are encrypted before being written to etcd.
- etcd encryption matters when you need protection against direct datastore access, stolen snapshots, or backups that contain sensitive objects.

## 2. Helm Secret Integration

### Chart changes

Updated chart layout:

```text
k8s/devops-info/
├── Chart.yaml
├── values.yaml
├── values-vault.yaml
├── charts/common-lib-0.1.0.tgz
└── templates/
    ├── _helpers.tpl
    ├── deployment.yaml
    ├── secrets.yaml
    ├── service.yaml
    ├── serviceaccount.yaml
    └── hooks/
```

Important implementation points:

- `templates/secrets.yaml` creates an `Opaque` secret using `stringData`.
- `templates/deployment.yaml` consumes the secret with `envFrom.secretRef`.
- `templates/serviceaccount.yaml` creates `devops-info-sa` for Vault auth.
- `templates/_helpers.tpl` now contains named templates:
  - `devops-info.envVars`
  - `devops-info.vaultSecretTemplate`
  - `devops-info.vaultAnnotations`
- `k8s/common-lib/templates/_security.tpl` was extended so container-level `runAsUser` and `runAsGroup` can be rendered. This was required because Vault's `agent-run-as-same-user` admission logic checks the container security context, not only the pod security context.

### Native secret install

I installed the chart first without Vault injection, only native Helm-managed secrets:

```bash
docker exec lab09-control-plane helm upgrade --install devops-info /tmp/devops-info \
  -n devops-lab11 \
  --create-namespace \
  --kubeconfig /etc/kubernetes/admin.conf \
  --wait \
  --timeout 5m \
  --set secret.data.APP_USERNAME=helm-user \
  --set secret.data.APP_PASSWORD=helm-pass-456
```

Result:

```text
NAME: devops-info
NAMESPACE: devops-lab11
STATUS: deployed
REVISION: 1
DESCRIPTION: Install complete
```

`helm list`:

```text
NAME        NAMESPACE    REVISION  UPDATED                                 STATUS    CHART             APP VERSION
devops-info devops-lab11 1         2026-04-09 16:49:01.792127207 +0000 UTC deployed  devops-info-0.2.0 1.0.0
```

### Secret consumption verification

Secret values were injected as environment variables:

```bash
kubectl exec <pod> -- printenv | grep '^APP_' | sort
```

Actual output:

```text
APP_PASSWORD=helm-pass-456
APP_USERNAME=helm-user
```

`kubectl describe pod` shows the source secret, but not the values:

```text
Environment Variables from:
  devops-info-secret  Secret  Optional: false
Environment:
  HOST:                 0.0.0.0
  LOG_LEVEL:            INFO
  PORT:                 5000
  SERVICE_DESCRIPTION:  DevOps course info service packaged with Helm
  SERVICE_NAME:         devops-info-service
  SERVICE_VARIANT:      primary
  SERVICE_VERSION:      1.0.0
```

This is the expected behavior: the pod spec references the Secret, but `kubectl describe pod` does not print the secret values themselves.

## 3. Resource Management

Configured container resources:

```json
{"limits":{"cpu":"250m","memory":"256Mi"},"requests":{"cpu":"100m","memory":"128Mi"}}
```

Interpretation:

- `requests` reserve scheduler capacity and affect pod placement.
- `limits` cap the maximum CPU and memory a container may consume.
- CPU limits throttle; memory limits can cause OOM termination.

Why these numbers are reasonable here:

- the app is a lightweight FastAPI service
- `100m` / `128Mi` is enough baseline for predictable placement
- `250m` / `256Mi` allows headroom for startup, probes, and observability overhead

How I would choose production values:

1. Measure steady-state and peak usage with Prometheus.
2. Set requests near typical sustained usage.
3. Set limits with headroom for spikes, startup, and dependency variance.
4. Revisit after load tests and real traffic patterns.

## 4. Vault Integration

### Vault installation

I used the official HashiCorp chart:

```yaml
name: vault
version: 0.32.0
appVersion: 1.21.2
description: Official HashiCorp Vault Chart
```

The chart was pulled on the host and installed from a local tarball into the kind node:

```bash
docker exec lab09-control-plane helm upgrade --install vault /tmp/vault-0.32.0.tgz \
  -n vault-lab11 \
  --create-namespace \
  --kubeconfig /etc/kubernetes/admin.conf \
  --set server.dev.enabled=true \
  --set server.dev.devRootToken=root \
  --set injector.enabled=true \
  --wait \
  --timeout 10m
```

`helm list`:

```text
NAME   NAMESPACE   REVISION  UPDATED                                 STATUS    CHART        APP VERSION
vault  vault-lab11 1         2026-04-09 16:51:23.320246652 +0000 UTC deployed  vault-0.32.0 1.21.2
```

`kubectl get pods -n vault-lab11 -o wide`:

```text
NAME                                   READY   STATUS    RESTARTS   AGE     IP            NODE
vault-0                                1/1     Running   0          4m26s   10.244.0.26   lab09-control-plane
vault-agent-injector-f685c86cd-fl27g   1/1     Running   0          4m29s   10.244.0.27   lab09-control-plane
```

### Vault status

```text
Key             Value
---             -----
Initialized     true
Sealed          false
Version         1.21.2
Storage Type    inmem
HA Enabled      false
```

### Secret engine configuration

Default dev mode already had `secret/` as KV v2, but to satisfy the lab explicitly I enabled a dedicated KV v2 mount at `kv/`:

```bash
vault secrets enable -path=kv kv-v2
vault kv put kv/devops-info/config username=vault-user password=vault-pass-789
```

Result:

```text
Success! Enabled the kv-v2 secrets engine at: kv/
======= Secret Path =======
kv/data/devops-info/config
```

### Kubernetes auth, policy, and role

Applied policy:

```hcl
path "kv/data/devops-info/config" {
  capabilities = ["read"]
}
```

Actual policy readback:

```text
path "kv/data/devops-info/config" {
  capabilities = ["read"]
}
```

Role details:

```text
bound_service_account_names       [devops-info-sa]
bound_service_account_namespaces  [devops-lab11]
policies                          [devops-info]
ttl                               24h
```

This binds Vault access to:

- service account `devops-info-sa`
- namespace `devops-lab11`
- policy `devops-info`

### App upgrade with Vault injection

After the Vault auth and policy were ready, I upgraded the app release with `values-vault.yaml`:

```bash
docker exec lab09-control-plane helm upgrade devops-info /tmp/devops-info \
  -n devops-lab11 \
  --kubeconfig /etc/kubernetes/admin.conf \
  -f /tmp/devops-info/values-vault.yaml \
  --wait \
  --timeout 5m
```

Result:

```text
Release "devops-info" has been upgraded. Happy Helming!
NAME: devops-info
STATUS: deployed
REVISION: 3
DESCRIPTION: Upgrade complete
```

Note:

- Revision `2` failed initially because the injector requires `runAsUser` in the container security context when `vault.hashicorp.com/agent-run-as-same-user: "true"` is used.
- I fixed that in the shared library helper and rebuilt the packaged `common-lib` dependency.
- Revision `3` then rolled out successfully.

### Sidecar injection proof

Injected pod containers:

```text
devops-info vault-agent
```

Pod annotations:

```text
vault.hashicorp.com/agent-inject: true
vault.hashicorp.com/agent-inject-file-app-config: app.env
vault.hashicorp.com/agent-inject-secret-app-config: kv/data/devops-info/config
vault.hashicorp.com/agent-inject-status: injected
vault.hashicorp.com/role: devops-info
vault.hashicorp.com/secret-volume-path-app-config: /vault/secrets
```

Rendered file presence:

```text
total 4
-rw-r----- 1 appuser 1000 51 Apr  9 16:56 app.env
```

Rendered file contents:

```text
APP_USERNAME=vault-user
APP_PASSWORD=vault-pass-789
```

At the same time, the native Kubernetes Secret still populated the container environment:

```text
APP_PASSWORD=native-dev-password
APP_USERNAME=native-dev-user
```

This demonstrates both secret delivery paths working at once:

- Kubernetes Secret -> environment variables
- Vault Agent Injector -> rendered file in `/vault/secrets/app.env`

### Sidecar injection pattern explanation

What happened during injection:

1. The mutating webhook saw the Vault annotations on the pod template.
2. It added `vault-agent-init` and `vault-agent` containers plus an in-memory shared volume.
3. The init container authenticated with Vault using the pod service account JWT.
4. The sidecar kept the auth token and rendered the template into `/vault/secrets/app.env`.
5. The main app container read the file from the shared in-memory volume.

## 5. Bonus - Vault Agent Templates

### Template annotation

I implemented the bonus template flow in `templates/_helpers.tpl`:

```yaml
vault.hashicorp.com/agent-inject-template-app-config: |
  {{- with secret "kv/data/devops-info/config" -}}
  APP_USERNAME={{ .Data.data.username }}
  APP_PASSWORD={{ .Data.data.password }}
  {{- end -}}
```

This renders a custom `.env`-style file instead of Vault's default key/value formatting.

### Named template for environment variables

I also extracted the normal application env vars into a named Helm template:

```yaml
{{- define "devops-info.envVars" -}}
{{- range $name, $value := .Values.env }}
- name: {{ $name }}
  value: {{ $value | quote }}
{{- end }}
{{- end -}}
```

`deployment.yaml` then reuses it:

```yaml
env:
  {{- include "devops-info.envVars" . | nindent 12 }}
```

This keeps the deployment template smaller and makes future labs easier to extend.

### Dynamic updates and `agent-inject-command`

Operational notes:

- Vault Agent renews leased secrets and re-renders templates when source data is refreshed.
- For dynamic secrets, that enables rotation without changing the application manifest.
- For static KV values, the agent can re-render the file after the value changes, but the application still needs a way to reload configuration if it only reads the file once at startup.
- `vault.hashicorp.com/agent-inject-command-<name>` can be used to run a command after a template is rendered, for example to signal the app, rewrite permissions, or trigger a config reload hook.

## 6. Security Analysis

### Kubernetes Secrets vs Vault

| Capability | Kubernetes Secret | HashiCorp Vault |
|---|---|---|
| Storage | etcd | Vault storage backend |
| Default protection | base64 only | encrypted and access-controlled |
| Rotation | manual | first-class workflows |
| Dynamic secrets | no | yes |
| Audit trail | limited | strong audit support |
| Multi-cluster use | awkward | natural central service |
| Operational complexity | low | higher |

### When to use each

Use Kubernetes Secrets when:

- the application is simple
- the cluster is the only runtime boundary
- you only need a few static values
- operational simplicity matters more than centralization

Use Vault when:

- you need centralized secret management
- multiple apps or clusters consume the same secret source
- you need dynamic or short-lived credentials
- auditing, rotation, revocation, and policy separation matter

### Production recommendations

- Never commit real secret values to Git.
- Keep only placeholders in `values.yaml`.
- Enable etcd encryption at rest for Kubernetes Secrets.
- Use dedicated service accounts, not `default`.
- Restrict RBAC access to Secrets and service account tokens.
- Prefer Vault or another external manager for production-grade credentials.
- Use rotation and reload patterns so applications do not require pod restarts for secret changes.

## 7. Final State

Lab 11 deliverables completed:

- imperative Kubernetes Secret creation and decoding
- Helm-managed secret template with `envFrom`
- resource requests and limits in the chart
- dedicated service account for Vault auth
- Vault installation via Helm
- KV v2 secret mount and seeded secret data
- Kubernetes auth configuration
- Vault policy and role bound to the app service account
- Vault Agent Injector annotations and rendered `.env` file
- documentation of native Secrets, Vault integration, and security tradeoffs
