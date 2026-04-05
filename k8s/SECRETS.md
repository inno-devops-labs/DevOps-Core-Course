# Lab 11 - Kubernetes Secrets & HashiCorp Vault

Validated locally on April 5, 2026 against:

- Kubernetes context `kind-devops-lab9`
- Kubernetes `v1.34.3`
- Helm `v4.1.1`
- Vault Helm chart `0.32.0`
- Vault `1.21.2`

This lab extends the Python Helm chart from Lab 10 with:

- native Kubernetes Secret management
- resource requests and limits
- HashiCorp Vault installation and Kubernetes auth
- Vault Agent injection with template rendering
- DRY Helm named templates for environment variables

## 1. Kubernetes Secrets

### Imperative secret creation

Task 1 required using the imperative `kubectl create secret` command.

Command used:

```bash
kubectl create secret generic app-credentials \
  -n lab11 \
  --from-literal=username=admin \
  --from-literal=password=lab11-demo-password
```

Observed output:

```text
secret/app-credentials created
```

### Secret viewed as YAML

Command used:

```bash
kubectl get secret app-credentials -n lab11 -o yaml
```

Observed output:

```yaml
apiVersion: v1
data:
  password: bGFiMTEtZGVtby1wYXNzd29yZA==
  username: YWRtaW4=
kind: Secret
metadata:
  creationTimestamp: "2026-04-05T09:11:27Z"
  name: app-credentials
  namespace: lab11
type: Opaque
```

### Base64 decoding demonstration

Commands used:

```bash
kubectl get secret app-credentials -n lab11 -o jsonpath='{.data.username}' \
  | python3 -c 'import base64,sys; print(base64.b64decode(sys.stdin.read()).decode())'

kubectl get secret app-credentials -n lab11 -o jsonpath='{.data.password}' \
  | python3 -c 'import base64,sys; print(base64.b64decode(sys.stdin.read()).decode())'
```

Observed output:

```text
admin
lab11-demo-password
```

### Encoding vs encryption

Base64 is only an encoding format. It makes binary data safe for YAML/JSON transport, but it does not provide confidentiality.

In practice:

- anyone who can read the Secret object can decode the value immediately
- base64 does not protect data at rest
- Kubernetes Secret safety depends on API access, RBAC, audit policy, namespace isolation, and optional etcd encryption

### Are Kubernetes Secrets encrypted at rest by default?

Per the official Kubernetes documentation, no: by default the API server stores plain-text representations of resources in etcd unless encryption at rest is explicitly configured.

I also checked the current local kind control-plane manifest:

```bash
sh -lc "kubectl get pod -n kube-system kube-apiserver-devops-lab9-control-plane -o yaml | rg --line-number 'encryption-provider-config' || echo not-configured"
```

Observed output:

```text
not-configured
```

That means this local cluster does not appear to have API-server at-rest encryption configured.

### What etcd encryption is and when to enable it

etcd encryption at rest is Kubernetes API-server encryption for persisted resource data such as Secrets. It is configured via `--encryption-provider-config` on `kube-apiserver`.

Enable it when:

- the cluster stores any real credentials, tokens, API keys, or certificates
- the control-plane host or etcd storage may be accessible to operators or backups
- compliance or security policy requires defense beyond RBAC

For production, enabling at-rest encryption for Secrets should be considered baseline hygiene, not an optional hardening extra.

## 2. Helm Secret Integration

### Chart changes

The Lab 11 Python chart now contains these additional files:

```text
k8s/devops-info-python/
|-- values.yaml
|-- values-vault.yaml
`-- templates/
    |-- _helpers.tpl
    |-- deployment.yaml
    |-- secrets.yaml
    |-- serviceaccount.yaml
    |-- service.yaml
    `-- hooks/
        |-- pre-install-job.yaml
        `-- post-install-job.yaml

k8s/scripts/
`-- bootstrap-lab11-vault.sh
```

What each new piece does:

- `templates/secrets.yaml`: creates the chart-managed Kubernetes Secret
- `templates/serviceaccount.yaml`: creates a dedicated service account for Vault auth
- `templates/_helpers.tpl`: adds named templates for secret naming, service account naming, common env vars, and Vault annotations
- `values-vault.yaml`: enables Vault integration, reserves `NodePort 30081`, and keeps non-sensitive demo secret values for reproducible local validation
- `scripts/bootstrap-lab11-vault.sh`: re-applies the dev-mode Vault auth method, KV secret, policy, and role after a fresh install or Vault pod restart, and it can follow a non-default auth mount through `VAULT_AUTH_PATH`
- default values disable service-account token automount; the Vault profile explicitly enables it because Kubernetes auth needs the pod token

### Secret template

The chart-managed Secret is rendered from `templates/secrets.yaml` and keeps only placeholder defaults in Git:

```yaml
type: Opaque
stringData:
  username: {{ .Values.secret.username | quote }}
  password: {{ .Values.secret.password | quote }}
```

### Named template for env vars

The bonus requirement for DRY Helm env configuration is implemented in `templates/_helpers.tpl` via `devops-info-python.commonEnvVars`.

The Deployment uses:

```yaml
env:
  {{- include "devops-info-python.commonEnvVars" . | nindent 12 }}
  - name: APP_USERNAME
    valueFrom:
      secretKeyRef:
        name: {{ include "devops-info-python.secretName" . }}
        key: username
  - name: APP_PASSWORD
    valueFrom:
      secretKeyRef:
        name: {{ include "devops-info-python.secretName" . }}
        key: password
```

That arrangement keeps the repetitive non-secret env vars DRY while still wiring the two secret-backed values explicitly through `secretKeyRef`.

The named template renders:

- plain env vars: `HOST`, `PORT`, `LOG_LEVEL`

### Chart-managed Secret created by Helm

Command used:

```bash
kubectl get secret -n lab11 lab11-python-devops-info-python-credentials -o yaml
```

Observed output:

```yaml
apiVersion: v1
data:
  password: bGFiMTEtazhzLXBhc3N3b3Jk
  username: bGFiMTEtazhzLXVzZXI=
kind: Secret
metadata:
  annotations:
    meta.helm.sh/release-name: lab11-python
    meta.helm.sh/release-namespace: lab11
  labels:
    app.kubernetes.io/component: web
    app.kubernetes.io/instance: lab11-python
    app.kubernetes.io/managed-by: Helm
    app.kubernetes.io/name: devops-info-python
    app.kubernetes.io/part-of: lab11
    helm.sh/chart: devops-info-python-0.2.0
  name: lab11-python-devops-info-python-credentials
  namespace: lab11
type: Opaque
```

### Pod wiring without leaking values in `kubectl describe`

Command used:

```bash
kubectl describe pod -n lab11 <running-pod> | sed -n '/^Containers:/,/^Conditions:/p'
```

Relevant excerpt:

```text
Containers:
  devops-info-python:
    Environment:
      HOST:          0.0.0.0
      PORT:          3000
      LOG_LEVEL:     INFO
      APP_USERNAME:  <set to the key 'username' in secret 'lab11-python-devops-info-python-credentials'>  Optional: false
      APP_PASSWORD:  <set to the key 'password' in secret 'lab11-python-devops-info-python-credentials'>  Optional: false
```

This is exactly what Task 2 wanted:

- the pod consumes secret values
- `kubectl describe pod` shows the secret reference
- the actual secret values are not printed
- the `sed` filter starts at the regular container section, so it does not mix in init-container output from the Vault injector

### Secret-backed env vars confirmed inside the pod

Command used:

```bash
kubectl exec -n lab11 deploy/lab11-python-devops-info-python \
  -c devops-info-python \
  -- sh -lc "env | grep -E '^(APP_USERNAME|APP_PASSWORD|HOST|PORT|LOG_LEVEL)=' | sed 's/=.*$/=<redacted>/'"
```

Observed output:

```text
LOG_LEVEL=<redacted>
PORT=<redacted>
APP_USERNAME=<redacted>
HOST=<redacted>
APP_PASSWORD=<redacted>
```

## 3. Resource Management

The app container keeps explicit requests and limits in `values.yaml`:

```yaml
resources:
  requests:
    cpu: 100m
    memory: 128Mi
  limits:
    cpu: 250m
    memory: 256Mi
```

Why these values make sense for this lab:

- the Flask app is lightweight, so `100m` CPU and `128Mi` memory are enough to schedule reliably on a local kind cluster
- the limits still cap accidental runaway usage
- the values stay configurable through Helm overrides

Requests vs limits:

- `requests` influence scheduling; the scheduler reserves at least that much capacity
- `limits` are enforced by the kubelet/runtime and cap consumption

The deployment kept these values in the final release and remained healthy:

```text
deployment.apps/lab11-python-devops-info-python   3/3   3   3
```

## 4. Vault Integration

### Vault installation

The official HashiCorp Helm repository was added and checked before installation:

```bash
/tmp/darwin-arm64/helm repo add hashicorp https://helm.releases.hashicorp.com
/tmp/darwin-arm64/helm repo update
/tmp/darwin-arm64/helm search repo hashicorp/vault -l | head -n 5
```

Observed output:

```text
NAME               CHART VERSION   APP VERSION   DESCRIPTION
hashicorp/vault    0.32.0          1.21.2        Official HashiCorp Vault Chart
hashicorp/vault    0.31.0          1.20.4        Official HashiCorp Vault Chart
```

Installation command:

```bash
/tmp/darwin-arm64/helm upgrade --install vault hashicorp/vault \
  --version 0.32.0 \
  --namespace lab11 \
  --create-namespace \
  --set server.dev.enabled=true \
  --set server.dev.devRootToken=root \
  --set injector.enabled=true \
  --wait --timeout 5m
```

Repeatability note:

- Vault `dev` mode uses in-memory storage, so a Vault pod restart wipes the Lab 11 auth method, policy, role, and stored demo secret.
- To restore the lab to a working state after any restart, run `./k8s/scripts/bootstrap-lab11-vault.sh` and then restart or re-upgrade the application release.
- If you override `vault.authPath` in Helm values, pass the same path to the helper, for example `VAULT_AUTH_PATH=auth/custom-k8s ./k8s/scripts/bootstrap-lab11-vault.sh`.
- The helper script intentionally uses only demo credentials and the fixed dev root token from this lab setup.

Vault installation verification:

```bash
kubectl get pods -n lab11
```

Observed output:

```text
NAME                                               READY   STATUS    RESTARTS   AGE
lab11-python-devops-info-python-5849d86b76-b9hmp   2/2     Running   0          4m37s
lab11-python-devops-info-python-5849d86b76-s72jk   2/2     Running   0          5m4s
lab11-python-devops-info-python-5849d86b76-vvb76   2/2     Running   0          4m50s
vault-0                                            1/1     Running   0          13m
vault-agent-injector-7979544d8b-xrmpn              1/1     Running   0          13m
```

### Vault state and secret engine

Commands used:

```bash
kubectl exec -n lab11 vault-0 -- env VAULT_ADDR=http://127.0.0.1:8200 VAULT_TOKEN=root vault status
kubectl exec -n lab11 vault-0 -- env VAULT_ADDR=http://127.0.0.1:8200 VAULT_TOKEN=root vault secrets list -detailed
```

Relevant output:

```text
Version         1.21.2
Storage Type    inmem
Sealed          false
```

```text
Path      Type   Options
secret/   kv     map[version:2]
```

That confirms the `secret/` mount is KV v2.

### Vault secret creation

Command used inside the Vault pod:

```bash
vault kv put secret/devops-info-python/config \
  username="lab11-user" \
  password="lab11-password" \
  database_url="postgresql://lab11-user:lab11-password@db.example.internal:5432/app"
```

Verification command:

```bash
kubectl exec -n lab11 vault-0 -- env VAULT_ADDR=http://127.0.0.1:8200 VAULT_TOKEN=root vault kv get secret/devops-info-python/config
```

Relevant output:

```text
Secret Path: secret/data/devops-info-python/config

Data:
database_url    postgresql://lab11-user:lab11-password@db.example.internal:5432/app
password        lab11-password
username        lab11-user
```

### Kubernetes auth configuration

Commands used:

```bash
vault auth enable kubernetes
vault write auth/kubernetes/config \
  kubernetes_host="https://$KUBERNETES_SERVICE_HOST:$KUBERNETES_SERVICE_PORT" \
  disable_iss_validation=true
```

Verification command:

```bash
kubectl exec -n lab11 vault-0 -- env VAULT_ADDR=http://127.0.0.1:8200 VAULT_TOKEN=root vault read auth/kubernetes/config
```

Observed output:

```text
disable_local_ca_jwt    false
kubernetes_ca_cert_set  false
kubernetes_host         https://10.96.0.1:443
token_reviewer_jwt_set  false
```

This lab uses HashiCorp's documented short-lived token pattern for in-cluster Vault: omit `token_reviewer_jwt` and `kubernetes_ca_cert` so Vault uses its local service-account token and CA file instead.

### Policy and role

Policy used:

```hcl
path "secret/data/devops-info-python/config" {
  capabilities = ["read"]
}
```

Policy verification:

```bash
kubectl exec -n lab11 vault-0 -- env VAULT_ADDR=http://127.0.0.1:8200 VAULT_TOKEN=root vault policy read devops-info-python
```

Observed output:

```text
path "secret/data/devops-info-python/config" {
  capabilities = ["read"]
}
```

Role created for the chart service account:

```bash
vault write auth/kubernetes/role/devops-info-python \
  bound_service_account_names=devops-info-python-vault \
  bound_service_account_namespaces=lab11 \
  policies=devops-info-python \
  audience=https://kubernetes.default.svc.cluster.local \
  ttl=24h
```

The bootstrap helper now auto-discovers that audience from the cluster's
`/.well-known/openid-configuration` endpoint when `ROLE_AUDIENCE` is not set, so
the demo role benefits from JWT audience verification without hardcoding a
cluster-specific value into the script.

Role verification:

```bash
kubectl exec -n lab11 vault-0 -- env VAULT_ADDR=http://127.0.0.1:8200 VAULT_TOKEN=root vault read -format=json auth/kubernetes/role/devops-info-python
```

Observed output:

```json
{
  "data": {
    "audience": "https://kubernetes.default.svc.cluster.local",
    "bound_service_account_names": [
      "devops-info-python-vault"
    ],
    "bound_service_account_namespaces": [
      "lab11"
    ],
    "policies": [
      "devops-info-python"
    ],
    "token_ttl": 86400
  }
}
```

### App chart deployment with Vault enabled

Final deployment command:

```bash
/tmp/darwin-arm64/helm upgrade --install lab11-python k8s/devops-info-python \
  --namespace lab11 \
  --reset-values \
  -f k8s/devops-info-python/values-vault.yaml \
  --wait --timeout 5m
```

Effective release values were verified after install:

```text
service.nodePort: 30081
serviceAccount.name: devops-info-python-vault
vault.enabled: true
vault.role: devops-info-python
vault.secretPath: secret/data/devops-info-python/config
```

### Proof of injection

File existence and rendered content:

```bash
kubectl exec -n lab11 deploy/lab11-python-devops-info-python \
  -c devops-info-python \
  -- sh -lc "ls -la /vault/secrets && sed 's/=.*$/=<redacted>/' /vault/secrets/app.env"
```

Observed output:

```text
total 8
drwxrwxrwt 2 root root   60 Apr  5 09:09 .
drwxr-xr-x 3 root root 4096 Apr  5 09:09 ..
-r-------- 1 app  1000   68 Apr  5 09:09 app.env
APP_USERNAME=<redacted>
APP_PASSWORD=<redacted>
```

### Rotation check

To verify the bonus refresh behavior, I rotated the Vault KV data without redeploying the application:

```bash
kubectl exec -n lab11 vault-0 -- sh -lc '
  export VAULT_ADDR=http://127.0.0.1:8200 VAULT_TOKEN=root
  vault kv put secret/devops-info-python/config \
    username="vault-user-rotated" \
    password="vault-password-rotated" \
    database_url="postgresql://vault-user-rotated:vault-password-rotated@db.example.internal:5432/app"
'

sleep 70
```

The Kubernetes Secret-backed environment variables stayed unchanged in the app container:

```bash
kubectl exec -n lab11 <running-pod> -c devops-info-python -- printenv APP_USERNAME APP_PASSWORD
```

Observed output:

```text
lab11-k8s-user
lab11-k8s-password
```

The Vault-rendered file changed to the new values:

```bash
kubectl exec -n lab11 <running-pod> -c devops-info-python -- cat /vault/secrets/app.env
```

Observed output:

```text
APP_USERNAME=vault-user-rotated
APP_PASSWORD=vault-password-rotated
```

This is the practical difference between the two approaches:

- environment variables sourced from a Kubernetes Secret stay static until the pod is recreated
- the Vault Agent template can refresh the rendered file in place according to the configured interval

Vault Agent log verification:

```bash
kubectl logs -n lab11 <running-pod> -c vault-agent
```

Relevant excerpt:

```text
agent.auth.handler: authenticating
agent.auth.handler: authentication successful, sending token to sinks
agent.template.server: template server received new token
```

Concise mutation proof from the pod spec:

```bash
kubectl get pods -n lab11 -l app.kubernetes.io/instance=lab11-python --field-selector=status.phase=Running \
  -o jsonpath='{.items[0].metadata.name}{" | "}{.items[0].spec.initContainers[*].name}{" | "}{.items[0].spec.containers[*].name}{" | "}{.items[0].spec.volumes[*].name}'
```

Observed output:

```text
lab11-python-devops-info-python-7fcc6c6986-4nkct | vault-agent-init | devops-info-python vault-agent | kube-api-access-kqk48 home-init home-sidecar vault-secrets
```

That confirms the webhook mutated the pod with:

- an init container: `vault-agent-init`
- a sidecar: `vault-agent`
- a shared memory volume: `vault-secrets`

### Sidecar injection pattern explanation

In this setup:

- the mutating webhook sees `vault.hashicorp.com/agent-inject: "true"`
- it adds `vault-agent-init` to pre-populate `/vault/secrets`
- it adds `vault-agent` to keep authenticating and re-rendering templates while the pod runs
- the application container reads the rendered file from the same in-memory shared volume

This lets the application consume secrets without embedding Vault client logic in the app code.

## 5. Application Verification

The application itself was checked through a local port-forward:

```bash
kubectl port-forward -n lab11 svc/lab11-python-devops-info-python 18080:80
curl -s http://127.0.0.1:18080/health
curl -s http://127.0.0.1:18080/
```

Observed output:

```json
{"status":"healthy","timestamp":"2026-04-05T09:12:48.779713+00:00","uptime_seconds":223}
```

```json
{"endpoints":[{"description":"Service and system information","method":"GET","path":"/"},{"description":"Health check endpoint","method":"GET","path":"/health"},{"description":"Prometheus metrics endpoint","method":"GET","path":"/metrics"}],"request":{"client_ip":"127.0.0.1","method":"GET","path":"/","user_agent":"curl/8.7.1"},"runtime":{"current_time":"2026-04-05T09:12:48.782134+00:00","timezone":"UTC","uptime_human":"0 hours, 3 minutes","uptime_seconds":223},"service":{"description":"DevOps course info service","framework":"Flask","name":"devops-info-service","version":"1.0.0"},"system":{"architecture":"aarch64","cpu_count":4,"hostname":"lab11-python-devops-info-python-5849d86b76-s72jk","platform":"Linux","platform_version":"#1 SMP Mon Feb 16 11:19:07 UTC 2026","python_version":"3.13.12"}}
```

## 6. Bonus - Vault Agent Templates

### Implemented template annotation

The chart now renders these Vault annotations from `templates/_helpers.tpl`:

```yaml
vault.hashicorp.com/agent-inject: "true"
vault.hashicorp.com/agent-inject-secret-app-env: secret/data/devops-info-python/config
vault.hashicorp.com/agent-inject-file-app-env: app.env
vault.hashicorp.com/agent-inject-template-app-env: |
  {{- with secret "secret/data/devops-info-python/config" -}}
  APP_USERNAME={{ .Data.data.username }}
  APP_PASSWORD={{ .Data.data.password }}
  {{- end }}
```

This renders multiple secret values into one `.env`-style file.

### Dynamic secret rotation and refresh behavior

This chart exposes `vault.hashicorp.com/template-static-secret-render-interval` through `vault.templateStaticSecretRenderInterval`, and the default is:

```yaml
vault:
  templateStaticSecretRenderInterval: 1m
```

Why this matters:

- KV v2 data like `secret/data/devops-info-python/config` is a static secret, not a leased dynamic credential
- for static secrets, Vault Agent needs a re-render interval to revisit the secret and refresh the rendered file
- the `1m` interval is appropriate for a lab because it makes refresh behavior visible without adding too much churn

### `agent-inject-command`

The chart also exposes:

```yaml
vault:
  agentInjectCommand: ""
```

If set, it renders:

```yaml
vault.hashicorp.com/agent-inject-command-app-env: "<command>"
```

That annotation is meant for actions like:

- reloading an application after a template re-render
- touching a marker file
- running a lightweight wrapper script

I left it empty by default because this demo app does not need a reload command to prove injection.

### Named template for environment variables

The bonus DRY requirement is implemented in `templates/_helpers.tpl`:

```yaml
{{- define "devops-info-python.commonEnvVars" -}}
- name: HOST
  value: {{ .Values.config.host | quote }}
- name: PORT
  value: {{ .Values.config.port | quote }}
- name: LOG_LEVEL
  value: {{ .Values.config.logLevel | quote }}
{{- end -}}
```

That helper is included directly from the Deployment, so the chart stays DRY for the common environment block while the secret-backed variables remain explicit and easy to audit.

## 7. Security Analysis

### Kubernetes Secrets vs Vault

Kubernetes Secrets are a good fit when:

- the secret is cluster-local
- rotation is simple or infrequent
- the application only needs environment variables or mounted files
- you want the simplest possible operational model

Vault is a better fit when:

- secrets should not live primarily in the cluster API
- access policy should be centralized and auditable
- different workloads need different policies bound to service accounts
- secret rotation, revocation, or dynamic issuance matter
- you want templating, sidecar rendering, or external secret backends

### Production recommendations

- Never commit real credentials to Git. Keep only placeholders in chart defaults.
- Enable Kubernetes at-rest encryption for Secrets via `--encryption-provider-config`.
- Restrict `get`, `list`, and `watch` access to Secrets with least-privilege RBAC.
- Use dedicated service accounts for Vault roles rather than the namespace default account.
- Prefer Vault or another external secret manager when credentials are shared across services, require frequent rotation, or must be centrally revoked.
- Treat environment variables as sensitive runtime data too; avoid logging them.

## 8. Final State Summary

Final namespace inventory:

```bash
kubectl get all -n lab11
```

Observed output:

```text
NAME                                                   READY   STATUS    RESTARTS   AGE
pod/lab11-python-devops-info-python-5849d86b76-b9hmp   2/2     Running   0          4m37s
pod/lab11-python-devops-info-python-5849d86b76-s72jk   2/2     Running   0          5m4s
pod/lab11-python-devops-info-python-5849d86b76-vvb76   2/2     Running   0          4m50s
pod/vault-0                                            1/1     Running   0          13m
pod/vault-agent-injector-7979544d8b-xrmpn              1/1     Running   0          13m

service/lab11-python-devops-info-python   NodePort    80:30081/TCP
service/vault                             ClusterIP   8200/TCP,8201/TCP
service/vault-agent-injector-svc          ClusterIP   443/TCP

deployment.apps/lab11-python-devops-info-python   3/3
deployment.apps/vault-agent-injector              1/1
statefulset.apps/vault                            1/1
```

## Official References

- Kubernetes Secrets: https://kubernetes.io/docs/concepts/configuration/secret/
- Kubernetes Secret good practices: https://kubernetes.io/docs/concepts/security/secrets-good-practices/
- Kubernetes encryption at rest: https://kubernetes.io/docs/tasks/administer-cluster/encrypt-data/
- Kubernetes resource management: https://kubernetes.io/docs/concepts/configuration/manage-resources-containers/
- Vault Helm chart: https://developer.hashicorp.com/vault/docs/platform/k8s/helm
- Vault Kubernetes auth: https://developer.hashicorp.com/vault/docs/auth/kubernetes
- Vault Agent Injector: https://developer.hashicorp.com/vault/docs/deploy/kubernetes/injector
- Vault injector annotations: https://developer.hashicorp.com/vault/docs/platform/k8s/injector/annotations
- Vault sidecar tutorial: https://developer.hashicorp.com/vault/tutorials/kubernetes/kubernetes-sidecar
- Helm named templates: https://helm.sh/docs/chart_template_guide/named_templates/
