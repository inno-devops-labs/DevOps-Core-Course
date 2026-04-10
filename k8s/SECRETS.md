# Lab 11 — Kubernetes Secrets and HashiCorp Vault

I completed Lab 11 and the bonus task on the local `kind-lab9` cluster. The implementation extends the Helm chart from Lab 10 in `k8s/devops-info-service/` with:

- native Kubernetes Secrets managed by Helm
- environment variable injection from Secrets
- configurable CPU and memory requests/limits
- a dedicated ServiceAccount for Vault auth
- Vault Agent Injector annotations for file-based secret delivery
- bonus templating support for rendered `.env` files and configurable static secret refresh

All values committed to Git remain placeholders such as `change-me`. The live cluster was verified with non-production demo values only.

## Task 1 — Kubernetes Secrets Fundamentals

### Create a Secret with `kubectl`

I created the required secret imperatively in the `devops-lab11` namespace:

```bash
kubectl -n devops-lab11 create secret generic app-credentials \
  --from-literal=username=lab11-user \
  --from-literal=password=lab11-pass
```

Result:

```yaml
apiVersion: v1
data:
  password: bGFiMTEtcGFzcw==
  username: bGFiMTEtdXNlcg==
kind: Secret
metadata:
  name: app-credentials
  namespace: devops-lab11
type: Opaque
```

### Decode the Base64 Values

```bash
printf '%s' 'bGFiMTEtdXNlcg==' | base64 -d
printf '%s' 'bGFiMTEtcGFzcw==' | base64 -d
```

Decoded values:

```text
lab11-user
lab11-pass
```

### Encoding vs Encryption

- Base64 is encoding, not encryption. It only converts bytes into a transport-safe text representation.
- Anyone who can read the Secret object can decode the values immediately.
- Kubernetes Secrets are therefore only as safe as the API access, RBAC rules, and storage protection behind the cluster.

### Are Kubernetes Secrets Encrypted at Rest by Default?

No. By default, Kubernetes Secrets are stored in etcd without encryption at rest. They are base64-encoded in the API object, but that is not cryptographic protection.

### What Is etcd Encryption and When Should You Enable It?

etcd encryption at rest encrypts Secret payloads before they are written to etcd. It should be enabled for any non-trivial environment, especially when:

- the cluster is shared
- backups of etcd are taken
- cloud snapshots or disk access are possible
- compliance or audit requirements apply

Production recommendation:

- enable etcd encryption at rest
- restrict Secret access with RBAC
- prefer an external secret manager such as Vault for sensitive credentials

## Task 2 — Helm-Managed Secrets

### Chart Changes

I updated the chart in `k8s/devops-info-service/`:

```text
templates/
  _helpers.tpl
  deployment.yaml
  secrets.yaml
  serviceaccount.yaml
values.yaml
Chart.yaml
```

Key changes:

- `templates/secrets.yaml` creates an `Opaque` Secret from `.Values.secrets.data`
- `templates/serviceaccount.yaml` creates a dedicated ServiceAccount for the app
- `templates/_helpers.tpl` now contains:
  - `devops-info-service.secretName`
  - `devops-info-service.serviceAccountName`
  - `devops-info-service.envVars`
  - `devops-info-service.vaultAnnotations`
- `templates/deployment.yaml` now:
  - injects static env vars through the named helper
  - injects Secret keys through `envFrom.secretRef`
  - sets `serviceAccountName`
  - keeps requests/limits configurable from `values.yaml`
  - adds Vault annotations only when `.Values.vault.enabled=true`

### Placeholder Secret Values in `values.yaml`

Committed defaults are placeholders only:

```yaml
secrets:
  enabled: true
  data:
    APP_USERNAME: "change-me"
    APP_PASSWORD: "change-me"
```

### Verify Secret Injection

I deployed the chart into `devops-lab11`:

```bash
helm upgrade --install lab11 k8s/devops-info-service \
  -n devops-lab11 \
  --wait \
  --set replicaCount=1 \
  --set service.nodePort=30082 \
  --set secrets.data.APP_USERNAME=lab11-user \
  --set secrets.data.APP_PASSWORD=lab11-pass
```

Verified inside the pod:

```text
APP_USERNAME=<redacted>
SERVICE_NAME=<redacted>
APP_PASSWORD=<redacted>
```

`kubectl describe pod` confirms that the Secret is referenced without printing the secret values:

```text
Environment Variables from:
  lab11-devops-info-service-secret  Secret  Optional: false
Environment:
  HOST:                 0.0.0.0
  PORT:                 5000
  SERVICE_NAME:         devops-info-service
  SERVICE_VERSION:      1.0.0
  SERVICE_DESCRIPTION:  DevOps course info service deployed with Helm
  RELEASE_TRACK:        stable
```

### Resource Limits

Applied values:

```yaml
resources:
  requests:
    cpu: 100m
    memory: 128Mi
  limits:
    cpu: 250m
    memory: 256Mi
```

Verified on the running pod:

```text
Limits:
  cpu:     250m
  memory:  256Mi
Requests:
  cpu:      100m
  memory:   128Mi
```

### Requests vs Limits

- Requests reserve minimum CPU and memory for scheduling and QoS.
- Limits cap the maximum resources the container may consume.
- I kept the requests conservative and the limits moderately above them because the Flask service is small and does not need aggressive reservations.

## Task 3 — HashiCorp Vault Integration

### Install Vault via Helm

For reproducibility, I added a repo-local values file:

```text
k8s/vault-values-lab11.yaml
```

The intended installation flow is the one required by the lab:

```bash
helm repo add hashicorp https://helm.releases.hashicorp.com
helm repo update

helm upgrade --install vault hashicorp/vault \
  -n vault \
  --create-namespace \
  --wait \
  -f k8s/vault-values-lab11.yaml
```

The values file enables Vault dev mode and the agent injector:

```yaml
server:
  dev:
    enabled: true
    devRootToken: root

injector:
  enabled: true
```

Verification:

```text
NAME                                   READY   STATUS    RESTARTS   AGE
vault-0                                1/1     Running   0          2m7s
vault-agent-injector-8c76487db-gqrrn   1/1     Running   0          2m7s
```

### KV Secrets Engine and Application Secret

To satisfy the rubric explicitly, I enabled a dedicated KV v2 mount for the application:

```bash
vault secrets enable -path=kvv2 -version=2 kv
```

Verification:

```text
Key                  Value
---                  -----
description          key/value secret storage
options              map[version:2]
```

I stored app credentials under `kvv2/devops-info-service/config`:

```bash
vault kv put kvv2/devops-info-service/config \
  username=vault-user \
  password=vault-pass \
  api_token=vault-api-token
```

Verification:

```text
============= Secret Path =============
kvv2/data/devops-info-service/config

====== Data ======
Key          Value
---          -----
api_token    vault-api-token
password     vault-pass
username     vault-user
```

### Kubernetes Authentication

I enabled the Kubernetes auth method, created a policy, and bound a role to the application ServiceAccount in `devops-lab11`.

Policy:

```hcl
path "kvv2/data/devops-info-service/config" {
  capabilities = ["read"]
}
```

Role verification:

```text
bound_service_account_names       [devops-info-service]
bound_service_account_namespaces  [devops-lab11]
policies                          [devops-info-service]
ttl                               1h
```

### Enable Vault Agent Injection

I upgraded the release with Vault enabled:

```bash
helm upgrade lab11 k8s/devops-info-service \
  -n devops-lab11 \
  --wait \
  --set replicaCount=1 \
  --set service.nodePort=30082 \
  --set secrets.data.APP_USERNAME=lab11-user \
  --set secrets.data.APP_PASSWORD=lab11-pass \
  --set vault.enabled=true \
  --set vault.staticSecretRenderInterval=15s
```

The chart is now self-consistent by default:

- `serviceAccount.name` defaults to `devops-info-service`
- `vault.role` defaults to `devops-info-service`
- `vault.secretPath` defaults to `kvv2/data/devops-info-service/config`

Deployment annotations:

```text
vault.hashicorp.com/agent-inject: "true"
vault.hashicorp.com/agent-inject-file-config: "app.env"
vault.hashicorp.com/agent-inject-secret-config: "kvv2/data/devops-info-service/config"
vault.hashicorp.com/auth-path: "auth/kubernetes"
vault.hashicorp.com/role: "devops-info-service"
vault.hashicorp.com/secret-volume-path: "/vault/secrets"
vault.hashicorp.com/template-static-secret-render-interval: "15s"
```

### Proof of Sidecar Injection

After the upgrade the application pod became `2/2 Running`, which shows the main app container plus the Vault Agent sidecar:

```text
NAME                                         READY   STATUS    RESTARTS   AGE
lab11-devops-info-service-7645896cb6-jq2fk   2/2     Running   0          18s
```

`kubectl describe pod` shows the full injection pattern:

```text
Init Containers:
  vault-agent-init:
    State:          Terminated
      Reason:       Completed

Containers:
  devops-info-service:
    Mounts:
      /vault/secrets from vault-secrets (rw)
  vault-agent:
    State:          Running
```

Vault rendered the file to the expected path:

```text
total 4
-rw-r--r-- 1 100 appgroup 74 Apr 10 20:14 app.env
---
APP_USERNAME=vault-user
APP_PASSWORD=vault-pass
API_TOKEN=vault-api-token
```

This is the classic sidecar injection pattern:

- init container authenticates and prepares the initial render
- sidecar keeps running and manages future template refreshes
- application container reads files from the shared in-memory volume

## Bonus Task — Vault Agent Templates

### 1. Template Annotation

I implemented templated rendering through `devops-info-service.vaultAnnotations` in `templates/_helpers.tpl`.

The rendered annotation is:

```yaml
vault.hashicorp.com/agent-inject-template-config: |
  {{- with secret "kvv2/data/devops-info-service/config" -}}
  APP_USERNAME={{ .Data.data.username }}
  APP_PASSWORD={{ .Data.data.password }}
  API_TOKEN={{ .Data.data.api_token }}
  {{- end }}
```

This renders multiple secret fields into a single `.env`-style file named `app.env`.

### 2. Dynamic Secret Rotation

I also added support for:

```yaml
vault.hashicorp.com/template-static-secret-render-interval: "15s"
```

That allowed me to verify an actual re-render without redeploying the pod.

Before updating the secret:

```text
20:16:33
APP_USERNAME=vault-user
APP_PASSWORD=vault-pass
API_TOKEN=vault-api-token
```

I updated the KV v2 secret to version 2:

```text
version            2
```

After waiting a little over the configured `15s` interval:

```text
20:17:03
APP_USERNAME=vault-user-rotated
APP_PASSWORD=vault-pass-rotated
API_TOKEN=vault-api-token-rotated
```

This proves that the rendered file was refreshed inside the running pod.

About `vault.hashicorp.com/agent-inject-command-*`:

- this annotation can run a command after a template is rendered or re-rendered
- it is useful for notifying an app, touching a marker file, or triggering a lightweight reload action
- I added chart support for it through `.Values.vault.agentInjectCommand`, but kept it unset in the live deployment because the lab did not require a post-render hook

### 3. Named Templates for Environment Variables

The bonus also required a named Helm template for common env vars. I implemented:

```gotemplate
{{- define "devops-info-service.envVars" -}}
...
{{- end -}}
```

This helper is used from `templates/deployment.yaml`:

```gotemplate
env:
  {{- include "devops-info-service.envVars" . | nindent 12 }}
```

Benefits:

- avoids repeating the same env block inline
- keeps `deployment.yaml` smaller
- makes Vault-specific env values conditional in one place
- follows the DRY principle required by the bonus task

## Security Analysis

### Kubernetes Secrets vs Vault

| Aspect | Kubernetes Secret | Vault |
|---|---|---|
| Storage | Stored in etcd | Stored in Vault backend |
| Default protection | Base64 only | Access controlled by Vault policies |
| Rotation | Manual/process-driven | Centralized and automatable |
| Delivery model | API object mounted or injected | Agent/sidecar/template/file/token-based |
| Best use case | Simple cluster-local config | Sensitive credentials and production secrets |

### When to Use Each

Use Kubernetes Secrets when:

- the secret is low-risk
- the environment is simple
- operational overhead must stay minimal

Use Vault when:

- credentials are sensitive
- rotation matters
- access policies must be fine-grained
- secret auditability and centralized control are needed

### Production Recommendations

- never commit real credentials into `values.yaml`
- enable etcd encryption at rest
- restrict Secret access with RBAC
- use dedicated ServiceAccounts per workload
- prefer Vault or another external secret manager for production credentials
- use short-lived or dynamic secrets where possible

## Verification Summary

- `helm lint k8s/devops-info-service` passed
- Helm chart renders both with and without Vault enabled
- Kubernetes Secret creation, viewing, and decoding were verified
- Secret env injection into the running app pod was verified
- requests and limits were verified on the running pod
- Vault server and injector were deployed successfully
- KV v2 secret creation, policy, role, and Kubernetes auth were verified
- Vault Agent rendered a custom `.env` file into `/vault/secrets/app.env`
- bonus refresh behavior was verified by rotating the secret and observing file updates in the live pod

## References

- Kubernetes Secrets: https://kubernetes.io/docs/concepts/configuration/secret/
- Encrypting Secret Data at Rest: https://kubernetes.io/docs/tasks/administer-cluster/encrypt-data/
- Vault Helm Chart: https://github.com/hashicorp/vault-helm
- Vault Kubernetes Injector Annotations: https://developer.hashicorp.com/vault/docs/platform/k8s/injector/annotations
- Vault Agent Configuration and Static Secret Rendering: https://developer.hashicorp.com/vault/docs/agent-and-proxy/agent/generate-config
