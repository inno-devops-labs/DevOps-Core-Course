# Lab 11 - Kubernetes Secrets and HashiCorp Vault

## What I changed

For this lab I extended the Python Helm chart from Lab 10 so it can handle secrets in two ways:

- plain Kubernetes `Secret` objects managed by Helm
- Vault Agent sidecar injection for secrets rendered as files

I also kept the chart practical instead of hardcoding a one-off demo:

- the chart now creates a dedicated `ServiceAccount`
- the deployment reads a Kubernetes `Secret` through `envFrom`
- Vault injection is switchable through values
- the Vault template is rendered into one `.env`-style file with multiple keys
- common environment variables were moved into a named Helm template so the deployment YAML stays smaller

The local verification namespace for the lab is `lab11`.

## Kubernetes Secrets fundamentals

I first created a standalone secret with `kubectl` to show what native Kubernetes secrets actually look like before Helm gets involved.

Command:

```bash
kubectl create secret generic app-credentials -n lab11 \
  --from-literal=username=lab11-user \
  --from-literal=password='lab11-pass-please-change'
```

Viewed as YAML:

```yaml
apiVersion: v1
data:
  password: bGFiMTEtcGFzcy1wbGVhc2UtY2hhbmdl
  username: bGFiMTEtdXNlcg==
kind: Secret
metadata:
  name: app-credentials
  namespace: lab11
type: Opaque
```

Decoded values:

```text
lab11-user
lab11-pass-please-change
```

That is the important part of Task 1: base64 is only an encoding layer. It makes binary-safe transport easy, but it does not protect the data. If someone can read the Secret object, they can decode it in one command.

For the security question:

- by default, Kubernetes stores Secrets in etcd without API-level encryption at rest
- encryption at rest only starts when the API server is configured with an `EncryptionConfiguration`
- etcd encryption matters when you want Secret data protected in the control plane datastore, not only in transit

In practice, I would enable etcd encryption in any cluster that is more serious than a throwaway dev lab, and I would still keep RBAC tight because encryption at rest does not replace access control.

## Helm-managed secrets

### Chart structure

The Python chart now includes secret-related templates directly:

```text
k8s/devops-info-service/
├── Chart.yaml
├── values.yaml
└── templates/
    ├── _helpers.tpl
    ├── deployment.yaml
    ├── secrets.yaml
    ├── service.yaml
    └── serviceaccount.yaml
```

What each new piece does:

- `templates/secrets.yaml`
  Creates an opaque Kubernetes Secret from values in `values.yaml`
- `templates/serviceaccount.yaml`
  Creates the service account that Vault auth binds to
- `templates/_helpers.tpl`
  Adds a secret-name helper, a service-account-name helper, a named environment template, and a helper that renders Vault annotations

### Values and template approach

The chart keeps placeholders in Git instead of real credentials:

```yaml
secret:
  create: true
  name: ""
  data:
    username: placeholder-user
    password: placeholder-password
```

For the actual local install I overrode those values:

```bash
helm upgrade --install devops-info-service-lab11 k8s/devops-info-service \
  -n lab11 \
  --set service.nodePort=30081 \
  --set secret.data.username=chart-user \
  --set secret.data.password='chart-password-123' \
  --wait --wait-for-jobs --timeout 240s
```

Rendered Secret in the cluster:

```yaml
apiVersion: v1
data:
  password: Y2hhcnQtcGFzc3dvcmQtMTIz
  username: Y2hhcnQtdXNlcg==
kind: Secret
metadata:
  name: devops-info-service-lab11-secret
  namespace: lab11
type: Opaque
```

### How the deployment consumes the secret

The deployment uses `envFrom.secretRef`, so every key in the Secret becomes an environment variable inside the app container.

That means:

- `username` becomes `username`
- `password` becomes `password`

The chart-specific application variables still come from a named Helm template in `_helpers.tpl`, so the deployment keeps one source of truth for:

- `PORT`
- `SERVICE_NAME`
- `SERVICE_VERSION`
- `SERVICE_DESCRIPTION`
- `SERVICE_FRAMEWORK`

### Verification inside the pod

I checked the running pod and listed only the variable names so the documentation does not repeat the actual values:

```text
PORT
SERVICE_DESCRIPTION
SERVICE_FRAMEWORK
SERVICE_NAME
SERVICE_VERSION
password
username
```

I also checked `kubectl describe pod` to confirm that Kubernetes shows the secret reference, not the secret contents:

```text
Environment Variables from:
  devops-info-service-lab11-secret  Secret  Optional: false
Environment:
  PORT:                 5000
  SERVICE_NAME:         devops-info-service
  SERVICE_VERSION:      1.0.0
  SERVICE_DESCRIPTION:  DevOps course info service
  SERVICE_FRAMEWORK:    Flask
```

That is the behavior I wanted. The pod spec clearly shows where the secret came from, but it does not print the secret values.

## Resource management

The chart already had resource requests and limits from the previous lab, and this lab keeps them in `values.yaml`:

```yaml
resources:
  requests:
    cpu: 100m
    memory: 128Mi
  limits:
    cpu: 250m
    memory: 256Mi
```

Observed in the pod description:

```text
Limits:
  cpu:     250m
  memory:  256Mi
Requests:
  cpu:      100m
  memory:   128Mi
```

How I think about the split:

- requests are the scheduler promise, the minimum the pod expects to get
- limits are the ceiling, the point where Kubernetes starts enforcing the cap

For this Flask service, the values are small but not reckless. `100m` and `128Mi` are enough for steady state in a local cluster, while `250m` and `256Mi` leave some room for spikes without pretending the app is free.

## Vault installation and configuration

### Install

I installed Vault in dev mode with the injector enabled:

```bash
helm repo add hashicorp https://helm.releases.hashicorp.com
helm repo update

helm upgrade --install vault hashicorp/vault \
  -n lab11 \
  --set server.dev.enabled=true \
  --set injector.enabled=true \
  --wait --timeout 300s
```

Verification after the install settled:

```text
vault-0                                     1/1     Running   0          3m54s
vault-agent-injector-84f8c7cdff-ckddr       1/1     Running   0          3m54s
```

The Vault server was `vault-0`, and the injector webhook was `vault-agent-injector`.

### KV engine, policy, and role

I enabled a dedicated KV v2 mount at `apps/` and stored application secrets there:

```bash
vault secrets enable -path=apps kv-v2
vault kv put apps/devops-info-service/config \
  username=vault-user \
  password=vault-password-123 \
  api_key=vault-api-key-xyz
```

Policy used by the app:

```hcl
path "apps/data/devops-info-service/config" {
  capabilities = ["read"]
}
```

Role bound to the application service account:

```text
bound_service_account_names       [devops-info-service-lab11]
bound_service_account_namespaces  [lab11]
policies                          [devops-info-service]
ttl                               24h
```

That binding is the key step. The pod gets a Kubernetes service account token, Vault verifies it through the Kubernetes auth method, and only then hands back a Vault token with the `devops-info-service` policy attached.

## Vault Agent injection

### Helm configuration

The chart exposes Vault injection through values:

```yaml
vault:
  enabled: false
  role: devops-info-service
  secretPath: apps/data/devops-info-service/config
  agentInjectCommand: ""
```

For the live test I upgraded the release with Vault enabled:

```bash
helm upgrade devops-info-service-lab11 k8s/devops-info-service \
  -n lab11 \
  --set service.nodePort=30081 \
  --set secret.data.username=chart-user \
  --set secret.data.password='chart-password-123' \
  --set vault.enabled=true \
  --wait --wait-for-jobs --timeout 300s
```

The pod template then received these annotations:

```yaml
vault.hashicorp.com/agent-inject: "true"
vault.hashicorp.com/role: "devops-info-service"
vault.hashicorp.com/agent-inject-secret-config: "apps/data/devops-info-service/config"
vault.hashicorp.com/agent-inject-template-config: |
  {{- with secret "apps/data/devops-info-service/config" -}}
  APP_USERNAME={{ .Data.data.username }}
  APP_PASSWORD={{ .Data.data.password }}
  APP_API_KEY={{ .Data.data.api_key }}
  {{- end }}
```

### Proof that the sidecar injection worked

The upgraded pods came up as `2/2`, which shows the application container plus the Vault Agent sidecar:

```text
NAME                                        READY   STATUS    RESTARTS   AGE
devops-info-service-lab11-58899b944-79fkt   2/2     Running   0          41s
devops-info-service-lab11-58899b944-8gnmz   2/2     Running   0          58s
devops-info-service-lab11-58899b944-jlxxw   2/2     Running   0          51s
```

`kubectl describe pod` also showed the injector status and the extra containers:

```text
Annotations:
  vault.hashicorp.com/agent-inject: true
  vault.hashicorp.com/agent-inject-status: injected
  vault.hashicorp.com/role: devops-info-service

Init Containers:
  vault-agent-init:
    State: Terminated
      Reason: Completed

Containers:
  devops-info-service
  vault-agent
```

Inside the application container, the rendered file existed exactly where the injector pattern says it should:

```text
total 4
-rw-r--r-- 1 100 1000 86 Apr  5 12:16 config
```

Path:

```text
/vault/secrets/config
```

Rendered content:

```text
APP_USERNAME=vault-user
APP_PASSWORD=vault-password-123
APP_API_KEY=vault-api-key-xyz
```

That satisfied both the main Vault task and the bonus templating task because the file is a custom multi-key `.env`-style render, not just a raw secret dump.

### Sidecar injection pattern in plain words

This pattern is simple once you see it live:

1. the mutating webhook sees the Vault annotations on the pod template
2. it injects a Vault init container, a Vault sidecar, and a shared in-memory volume
3. the init container authenticates to Vault and writes the first rendered secret file
4. the application starts with that file already present
5. the sidecar keeps running and can re-render templates later if the secret changes

The app itself never has to speak to Vault directly.

## Bonus task

### Named Helm template for environment variables

I moved the common environment block into `templates/_helpers.tpl` and included it from the deployment.

Helper:

```yaml
{{- define "devops-info-service.envVars" -}}
- name: PORT
  value: {{ .Values.env.port | quote }}
- name: SERVICE_NAME
  value: {{ .Values.env.serviceName | quote }}
- name: SERVICE_VERSION
  value: {{ .Values.env.serviceVersion | quote }}
- name: SERVICE_DESCRIPTION
  value: {{ .Values.env.serviceDescription | quote }}
- name: SERVICE_FRAMEWORK
  value: {{ .Values.env.serviceFramework | quote }}
{{- end -}}
```

Usage:

```yaml
env:
  {{- include "devops-info-service.envVars" . | nindent 12 }}
```

This is a small change, but it is the right kind of small change. The deployment template no longer carries a repeated literal block, and future edits to shared app variables happen in one place.

### Secret refresh behavior

For Vault Agent templates, static secrets such as KV v2 values are not renewed like leased database credentials. Instead, the agent periodically re-renders them. HashiCorp documents this with the `static_secret_render_interval` setting, which defaults to `5m` for non-leased secrets.

That means the rough behavior is:

- the sidecar does not restart the app by itself
- it refreshes the rendered file when the template is re-run and the source value changed
- the application still needs some way to notice the file update if it only reads config once at startup

### `agent-inject-command`

I added optional chart support for the matching annotation:

```yaml
vault:
  agentInjectCommand: ""
```

If that value is set, the chart renders:

```yaml
vault.hashicorp.com/agent-inject-command-config: "<your command>"
```

This is useful when a file update alone is not enough. A common example would be sending a reload signal, rebuilding an app config cache, or copying the rendered file to another path after every successful render. I left it empty for the local Flask run because the lab only needed the file injection itself.

## Local functional test

After the Vault-enabled rollout, I still checked the service path through Kubernetes DNS:

```bash
kubectl run lab11-curl-check --rm -i --restart=Never -n lab11 \
  --image=curlimages/curl:8.12.1 \
  --command -- sh -c 'curl -fsS http://devops-info-service-lab11/health'
```

Response:

```json
{"status":"healthy","timestamp":"2026-04-05T12:16:58.087724+00:00","uptime_seconds":44}
```

So the app still served traffic normally after the injector sidecar was added.

## Security analysis

### Kubernetes Secrets vs Vault

Kubernetes Secrets are fine when:

- the secret set is small
- Kubernetes is already your main control plane
- rotation is simple or rare
- you only need the data inside the cluster

Vault is stronger when:

- you want short-lived credentials or structured rotation workflows
- teams should not have broad access to raw Kubernetes Secrets
- you want audit trails around secret reads
- one secret manager needs to serve multiple systems, not only Kubernetes
- applications should receive secrets as files without bundling Vault client logic

### Production recommendations

If I were taking this past lab scope, I would do the following:

- keep placeholder values in Git and inject real values at deploy time
- enable etcd encryption at rest for Secrets
- limit Secret access with RBAC, especially `list` and `watch`
- avoid Vault dev mode and run Vault with real storage and unseal strategy
- use tighter Vault policies per workload instead of one broad app path
- make the application reload config from file if secret rotation matters at runtime

## Files touched for the lab

- `k8s/devops-info-service/templates/_helpers.tpl`
- `k8s/devops-info-service/templates/deployment.yaml`
- `k8s/devops-info-service/templates/secrets.yaml`
- `k8s/devops-info-service/templates/serviceaccount.yaml`
- `k8s/devops-info-service/values.yaml`
- `k8s/SECRETS.md`

## References

- [Kubernetes Secrets good practices](https://kubernetes.io/docs/concepts/security/secrets-good-practices/)
- [Kubernetes encryption at rest](https://kubernetes.io/docs/tasks/administer-cluster/encrypt-data/)
- [Vault Agent Injector annotations](https://developer.hashicorp.com/vault/docs/deploy/kubernetes/injector/annotations)
- [Vault Agent templating](https://developer.hashicorp.com/vault/docs/agent/template)
