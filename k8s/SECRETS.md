# Lab 11 Secrets Implementation

This document records the Lab 11 implementation for Kubernetes Secrets and HashiCorp Vault using the Helm chart in `k8s/devops-info-service`.

Because the host kubeconfig endpoint timed out in this environment, live Kubernetes commands were executed from inside the running `kind` control-plane container with `docker exec lab10-control-plane ...`.

## Kubernetes Secrets

### Create a Secret Imperatively

Command:

```bash
docker exec lab10-control-plane kubectl create secret generic app-credentials \
  -n devops-lab11 \
  --from-literal=username=lab11-admin \
  --from-literal=password=lab11-passw0rd
```

Output:

```text
secret/app-credentials created
```

View the Secret:

```bash
docker exec lab10-control-plane kubectl get secret app-credentials -n devops-lab11 -o yaml
```

```yaml
apiVersion: v1
data:
  password: bGFiMTEtcGFzc3cwcmQ=
  username: bGFiMTEtYWRtaW4=
kind: Secret
metadata:
  name: app-credentials
  namespace: devops-lab11
type: Opaque
```

Decode the values:

```bash
docker exec lab10-control-plane sh -lc \
  "kubectl get secret app-credentials -n devops-lab11 -o jsonpath='{.data.username}' | base64 -d && printf '\n' && \
   kubectl get secret app-credentials -n devops-lab11 -o jsonpath='{.data.password}' | base64 -d && printf '\n'"
```

```text
lab11-admin
lab11-passw0rd
```

### Encoding vs Encryption

- Base64 is only an encoding format. It is reversible by anyone who can read the value.
- Kubernetes `Secret` objects are not meaningfully protected just because the `data` field is base64-encoded.
- Protection comes from RBAC, network boundaries, admission controls, and optional encryption at rest.

### Are Kubernetes Secrets Encrypted at Rest by Default?

No. By default, Kubernetes stores Secrets in etcd without encryption at rest unless the cluster admin enables an encryption provider configuration.

### What Is etcd Encryption and When Should You Enable It?

etcd encryption at rest encrypts sensitive Kubernetes resources before they are written into etcd. It should be enabled for any shared or production cluster, especially when storing:

- application credentials
- API tokens
- TLS private keys
- service-account style bootstrap secrets

It reduces the impact of an etcd snapshot leak or direct etcd access, but it does not replace RBAC and audit controls.

## Helm Secret Integration

### Chart Changes

The Lab 10 chart was extended with:

```text
k8s/devops-info-service/
├── values.yaml
├── values-dev.yaml
├── values-prod.yaml
├── values-vault.yaml
└── templates/
    ├── _helpers.tpl
    ├── deployment.yaml
    ├── secrets.yaml
    ├── serviceaccount.yaml
    └── service.yaml
```

Main changes:

- `templates/secrets.yaml` creates an `Opaque` Secret with `stringData`.
- `templates/serviceaccount.yaml` creates a dedicated service account for Vault auth binding.
- `templates/_helpers.tpl` now contains:
  - `devops-info-service.secretName`
  - `devops-info-service.serviceAccountName`
  - `devops-info-service.envVars`
  - `devops-info-service.vaultAnnotations`
- `templates/deployment.yaml` now:
  - consumes the Secret with `envFrom.secretRef`
  - uses the named env template
  - sets `serviceAccountName`
  - adds Vault injector annotations when enabled

### Deploy the Helm-Managed Secret Release

Install command:

```bash
helm upgrade --install lab11-dev k8s/devops-info-service \
  -n devops-lab11 \
  -f k8s/devops-info-service/values-dev.yaml
```

Live release status:

```text
NAME: lab11-dev
NAMESPACE: devops-lab11
STATUS: deployed
REVISION: 1
```

Rendered Secret in the cluster:

```bash
docker exec lab10-control-plane kubectl get secret lab11-dev-devops-info-service-secret -n devops-lab11 -o yaml
```

```yaml
apiVersion: v1
data:
  password: ZGV2LXBhc3N3b3Jk
  username: ZGV2LXVzZXI=
kind: Secret
metadata:
  name: lab11-dev-devops-info-service-secret
  namespace: devops-lab11
type: Opaque
```

### Verify Secret Injection

Pod status:

```text
NAME                                             READY   STATUS    RESTARTS   AGE
lab11-dev-devops-info-service-7d5b7cdb89-8nmkn   1/1     Running   0          10s
```

Environment variables observed in the running pod:

```text
APP_ENV=<redacted>
HOST=<redacted>
LOG_LEVEL=<redacted>
PORT=<redacted>
SERVICE_NAME=<redacted>
SERVICE_VERSION=<redacted>
password=<redacted>
username=<redacted>
```

Pod description proves the secret source is referenced without printing the secret values:

```text
Environment Variables from:
  lab11-dev-devops-info-service-secret  Secret  Optional: false
Environment:
  HOST:             0.0.0.0
  PORT:             5000
  SERVICE_NAME:     devops-info-service
  SERVICE_VERSION:  1.0.0
  APP_ENV:          dev
  LOG_LEVEL:        debug
```

That is the important distinction:

- `kubectl exec ... env` inside the container shows the resolved values
- `kubectl describe pod` shows the Secret reference, not the secret payload

## Resource Management

Resource limits were already present in the Lab 10 chart and are now part of the Lab 11 verification.

Current default values:

```yaml
resources:
  requests:
    cpu: 100m
    memory: 128Mi
  limits:
    cpu: 250m
    memory: 256Mi
```

Development override:

```yaml
resources:
  requests:
    cpu: 50m
    memory: 64Mi
  limits:
    cpu: 100m
    memory: 128Mi
```

Production override:

```yaml
resources:
  requests:
    cpu: 200m
    memory: 256Mi
  limits:
    cpu: 500m
    memory: 512Mi
```

Explanation:

- `requests` reserve scheduler capacity and influence placement.
- `limits` cap the maximum runtime consumption.
- Start with measured steady-state usage, keep headroom for spikes, then tune from metrics instead of guessing.

## Vault Integration

### Install Vault

Vault was installed from the official HashiCorp chart `hashicorp/vault` version `0.30.0` in dev mode with injector enabled.

Command used:

```bash
helm upgrade --install vault hashicorp/vault \
  -n vault \
  --create-namespace \
  --set server.dev.enabled=true \
  --set injector.enabled=true
```

Verification:

```text
NAME                                    READY   STATUS    RESTARTS   AGE
vault-0                                 1/1     Running   0          3m33s
vault-agent-injector-56459c7545-v856j   1/1     Running   0          3m35s
```

### Configure Vault KV

The dev server already had `secret/` mounted as KV v2:

```text
Path      Plugin  Options
secret/   kv      map[version:2]
```

Application secret written to Vault:

```bash
vault kv put secret/devops-info-service/config \
  username=vault-admin \
  password=vault-passw0rd
```

Verification:

```text
============= Secret Path =============
secret/data/devops-info-service/config

====== Data ======
Key         Value
---         -----
password    vault-passw0rd
username    vault-admin
```

### Kubernetes Auth, Policy, and Role

Policy:

```hcl
path "secret/data/devops-info-service/config" {
  capabilities = ["read"]
}
```

Role output:

```text
Key                                         Value
---                                         -----
bound_service_account_names                 [lab11-vault-devops-info-service]
bound_service_account_namespaces            [devops-lab11]
token_policies                              [devops-info-service]
token_ttl                                   24h
```

The working role name used by the injector is `devopsinfoservice`.

### Enable Vault Agent Injection

The chart now supports Vault annotations through `values-vault.yaml`.

The injected pod shows:

```text
Annotations:
  vault.hashicorp.com/agent-inject: true
  vault.hashicorp.com/agent-inject-secret-config: secret/data/devops-info-service/config
  vault.hashicorp.com/agent-inject-status: injected
  vault.hashicorp.com/agent-inject-template-app.env:
    {{- with secret "secret/data/devops-info-service/config" -}}
    USERNAME={{ .Data.data.username }}
    PASSWORD={{ .Data.data.password }}
    {{- end -}}
  vault.hashicorp.com/role: devopsinfoservice
  vault.hashicorp.com/secret-volume-path-config: /vault/secrets
```

Injected files inside the application container:

```text
total 12
drwxrwsrwt 2 root appuser   80 Apr  9 19:20 .
drwxr-xr-x 3 root root    4096 Apr  9 19:20 ..
-rw-r--r-- 1  100 appuser   44 Apr  9 19:20 app.env
-rw-r--r-- 1  100 appuser  178 Apr  9 19:20 config
```

Rendered template file:

```text
USERNAME=vault-admin
PASSWORD=vault-passw0rd
```

This verifies the sidecar injection pattern:

- the mutating webhook adds a Vault init container and sidecar
- the init container authenticates with Vault using the pod service account
- templates are rendered into an in-memory volume
- the main app reads the files from `/vault/secrets`

## Bonus Task

### Template Annotation

Implemented in `templates/_helpers.tpl` via:

```yaml
vault.hashicorp.com/agent-inject-template-{{ .Values.vault.renderedFileName }}: |
  {{`{{- with secret "`}}{{ .Values.vault.secretPath }}{{`" -}}`}}
  {{ upper .Values.vault.templateKeys.username }}={{`{{ .Data.data.`}}{{ .Values.vault.templateKeys.username }}{{` }}`}}
  {{ upper .Values.vault.templateKeys.password }}={{`{{ .Data.data.`}}{{ .Values.vault.templateKeys.password }}{{` }}`}}
  {{`{{- end -}}`}}
```

That renders multiple Vault keys into one `.env` file.

### Named Helm Template for Environment Variables

Implemented as `devops-info-service.envVars` in `_helpers.tpl` and consumed from `deployment.yaml`.

This keeps common app environment variables DRY and separate from secret-driven values.

### Dynamic Secret Rotation Research

Vault Agent keeps rendered files up to date by re-reading secrets and rewriting templates when leases or watched data change. For KV secrets, refresh behavior depends on the agent template watcher and Vault polling lifecycle rather than an in-place environment variable refresh.

Important implication:

- files rendered by Vault Agent can update without restarting the pod
- plain environment variables sourced from Kubernetes Secrets do not update in the running process

`vault.hashicorp.com/agent-inject-command-*` can run a command after a template is rendered or refreshed. Typical uses:

- send `SIGHUP` to reload config
- restart a sidecar-managed process
- transform the rendered file before the app consumes it

The chart exposes this through `vault.injectCommand`.

## Security Analysis

### Kubernetes Secrets vs Vault

Kubernetes Secrets:

- simple and native
- good for small clusters and low-complexity apps
- rely heavily on RBAC and cluster hardening
- no automatic secret rotation workflow by themselves
- values often end up as environment variables, which are easy for the process to consume but harder to rotate safely

Vault:

- central secret store with auditability and policy controls
- supports dynamic credentials, leasing, revocation, and rotation
- better fit for multi-team, production, or compliance-heavy environments
- adds operational complexity and another control plane

### When to Use Each

Use Kubernetes Secrets when:

- the cluster is small
- the threat model is modest
- credentials change infrequently
- external secret infrastructure is not justified yet

Use Vault when:

- you need centralized secret governance
- secrets rotate regularly
- you want short-lived credentials
- teams or namespaces need stricter separation and audit trails

### Production Recommendations

- enable etcd encryption at rest
- restrict secret access with RBAC and namespace boundaries
- avoid committing real secrets into Git
- prefer external secret managers for production credentials
- prefer mounted files over environment variables for high-sensitivity data that may rotate
- use Vault policies with least privilege and short-lived tokens
