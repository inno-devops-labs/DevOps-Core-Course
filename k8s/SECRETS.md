# Lab 11 - Kubernetes Secrets and HashiCorp Vault

Validated on April 8, 2026 on the `lab11` branch.

Environment used for this run:
- Kubernetes: `kind` cluster `lab11`
- Kubeconfig: `k8s/lab11-kubeconfig`
- Helm: repo-local binary `./.tools/helm.exe`
- Vault chart: `hashicorp/vault` in dev mode with injector enabled
- Application namespace: `lab11`
- Vault namespace: `vault`

## 1. Kubernetes Secrets Fundamentals

### Create a Secret with `kubectl`

Command used:

```powershell
kubectl --kubeconfig .\k8s\lab11-kubeconfig create namespace lab11 --dry-run=client -o yaml | kubectl --kubeconfig .\k8s\lab11-kubeconfig apply -f -
kubectl --kubeconfig .\k8s\lab11-kubeconfig -n lab11 create secret generic app-credentials `
  --from-literal=username=lab11-admin `
  --from-literal=password=lab11-password `
  --dry-run=client -o yaml | kubectl --kubeconfig .\k8s\lab11-kubeconfig apply -f -
```

Observed output:

```text
namespace/lab11 created
secret/app-credentials created
```

Secret YAML:

```yaml
apiVersion: v1
data:
  password: bGFiMTEtcGFzc3dvcmQ=
  username: bGFiMTEtYWRtaW4=
kind: Secret
metadata:
  name: app-credentials
  namespace: lab11
type: Opaque
```

Decoded values:

```text
username=lab11-admin
password=lab11-password
```

### Base64 Encoding vs Encryption

- Base64 is an encoding format. It makes binary-safe transport easier, but it does not protect confidentiality.
- Encryption transforms data with a key. Without the key, the stored value should not be readable.
- Kubernetes Secrets are only base64-encoded unless encryption at rest is explicitly enabled for the API server / etcd path.

### Security implications

Short answer:
- Kubernetes Secrets are not encrypted at rest by default.
- They are stored in etcd unless you configure API-server encryption.
- RBAC still matters even after enabling encryption at rest.

When to enable etcd encryption:
- Always in any shared, persistent, or production cluster.
- Whenever etcd backups, snapshots, or host-level access are in scope.
- Whenever your compliance baseline requires encryption of credentials, tokens, or keys at rest.

What etcd encryption changes:
- New writes for selected resource types such as `secrets` are encrypted before the API server stores them in etcd.
- It protects against plain-text disclosure from etcd compromise or backup leakage.
- It does not replace RBAC, network isolation, or node security.

## 2. Helm-Managed Secrets

### Chart changes

The Helm chart in `k8s/devops-info-service/` was extended with these files:

```text
k8s/devops-info-service/
+-- templates/_helpers.tpl
+-- templates/deployment.yaml
+-- templates/secrets.yaml
+-- templates/serviceaccount.yaml
+-- values.yaml
+-- values-dev.yaml
+-- values-prod.yaml
+-- values-vault.yaml
```

Key implementation points:
- `templates/secrets.yaml` creates a namespaced `Opaque` Secret from `Values.secrets.data`.
- `templates/deployment.yaml` now imports the Secret with `envFrom.secretRef`.
- `templates/serviceaccount.yaml` creates a dedicated service account for Vault auth.
- `_helpers.tpl` contains named templates for DRY env var rendering and Vault annotations.
- `values.yaml` contains only placeholders for secret values.
- `values-vault.yaml` contains non-secret Vault injector settings.

Installed command:

```powershell
.\.tools\helm.exe upgrade --install devops-info-service .\k8s\devops-info-service `
  --kubeconfig .\k8s\lab11-kubeconfig `
  --namespace lab11 `
  -f .\k8s\devops-info-service\values-dev.yaml `
  --set secrets.data.username=chart-user `
  --set secrets.data.password=chart-password `
  --wait --wait-for-jobs --timeout 8m
```

Live resources after install:

```text
NAME                                   READY   STATUS    RESTARTS   AGE
devops-info-service-58b7f577fb-dvrcs   1/1     Running   0          37s

NAME                  TYPE       CLUSTER-IP   EXTERNAL-IP   PORT(S)        AGE
devops-info-service   NodePort   10.96.6.57   <none>        80:30080/TCP   37s
```

Rendered Helm-managed Secret:

```yaml
apiVersion: v1
data:
  password: Y2hhcnQtcGFzc3dvcmQ=
  username: Y2hhcnQtdXNlcg==
kind: Secret
metadata:
  name: devops-info-service-secret
  namespace: lab11
type: Opaque
```

### Verify Secret injection inside the pod

Sanitized environment check:

```text
LOG_LEVEL=debug
username=<redacted>
password=<redacted>
APP_ENV=development
```

`kubectl describe pod` excerpt proving the Secret reference is visible but the Secret values are not:

```text
Environment Variables from:
  devops-info-service-secret  Secret  Optional: false
Environment:
  HOST:       0.0.0.0
  PORT:       8000
  APP_ENV:    development
  LOG_LEVEL:  debug
```

This is the expected behavior: Kubernetes shows the source Secret object in pod description, not the decoded values.

### Resource management

Current resource settings:

```yaml
resources:
  requests:
    cpu: 100m
    memory: 128Mi
  limits:
    cpu: 250m
    memory: 256Mi
```

Dev profile used in the live run:

```yaml
resources:
  requests:
    cpu: 50m
    memory: 64Mi
  limits:
    cpu: 100m
    memory: 128Mi
```

Requests vs limits:
- `requests` reserve scheduler capacity and influence bin-packing.
- `limits` cap how much CPU or memory the container may consume.
- CPU throttles when it exceeds the limit; memory overage risks OOM kill.

How to choose values:
- Start from observed steady-state usage.
- Keep requests near normal operating load.
- Keep limits above expected bursts but below abusive values.
- Revisit them after metrics exist in production.

Note:
- The chart now probes `/health` for readiness as well as liveness/startup. The published `ravwvil/devops-info-service:1.0.0` image used for this lab run does not expose `/ready`, while the current repo source does. Using `/health` keeps the chart deployable with the pinned image.

## 3. Vault Integration

### Install Vault

Commands used:

```powershell
.\.tools\helm.exe repo add hashicorp https://helm.releases.hashicorp.com
.\.tools\helm.exe repo update
kubectl --kubeconfig .\k8s\lab11-kubeconfig create namespace vault --dry-run=client -o yaml | kubectl --kubeconfig .\k8s\lab11-kubeconfig apply -f -
.\.tools\helm.exe upgrade --install vault hashicorp/vault `
  --kubeconfig .\k8s\lab11-kubeconfig `
  --namespace vault `
  --set server.dev.enabled=true `
  --set injector.enabled=true `
  --wait --timeout 10m
```

Verification:

```text
NAME                                   READY   STATUS    RESTARTS   AGE
vault-0                                1/1     Running   0          3m
vault-agent-injector-8c76487db-v7dbw   1/1     Running   0          3m
```

### Configure KV engine, policy, and Kubernetes auth

Commands executed inside `vault-0`:

```sh
vault login -no-print root
vault secrets enable -path=kv kv-v2
vault kv put kv/devops-info-service/config username=vault-user password=vault-password
vault auth enable kubernetes
vault write auth/kubernetes/config \
  token_reviewer_jwt="$(cat /var/run/secrets/kubernetes.io/serviceaccount/token)" \
  kubernetes_host="https://kubernetes.default.svc:443" \
  kubernetes_ca_cert=@/var/run/secrets/kubernetes.io/serviceaccount/ca.crt
```

Policy used for the application:

```hcl
path "kv/data/devops-info-service/*" {
  capabilities = ["read"]
}
```

Role created for the chart service account:

```text
bound_service_account_names       [devops-info-service]
bound_service_account_namespaces  [lab11]
policies                          [devops-info-service]
ttl                               24h
```

### Enable Vault Agent injection in the application

Upgrade command:

```powershell
.\.tools\helm.exe upgrade devops-info-service .\k8s\devops-info-service `
  --kubeconfig .\k8s\lab11-kubeconfig `
  --namespace lab11 `
  -f .\k8s\devops-info-service\values-dev.yaml `
  -f .\k8s\devops-info-service\values-vault.yaml `
  --set secrets.data.username=chart-user `
  --set secrets.data.password=chart-password `
  --wait --wait-for-jobs --timeout 10m
```

Verification after rollout:

```text
NAME                                   READY   STATUS    RESTARTS   AGE
devops-info-service-5c848dd6b6-ktqkk   2/2     Running   0          25s
```

Pod annotation excerpt:

```yaml
vault.hashicorp.com/agent-inject: "true"
vault.hashicorp.com/agent-inject-file-config: app.env
vault.hashicorp.com/agent-inject-secret-config: kv/data/devops-info-service/config
vault.hashicorp.com/role: devops-info-service
```

Proof that the rendered file exists inside the application container:

```text
total 4
-rw-r----- 1 100 appgroup 52 Apr  8 08:30 app.env
---
APP_USERNAME=<redacted>
APP_PASSWORD=<redacted>
```

### Sidecar injection pattern explained

What happened in this pod:
- The mutating webhook saw the Vault annotations.
- It patched the pod spec before scheduling.
- Vault Agent authenticated with the pod service account via Kubernetes auth.
- The agent rendered the template into `/vault/secrets/app.env`.
- The application container consumed that file from a shared in-memory volume.

This pattern keeps Vault data out of Git and avoids hardcoding secret values in the container image.

## 4. Security Analysis

### Kubernetes Secrets vs Vault

| Topic | Kubernetes Secret | HashiCorp Vault |
|---|---|---|
| Storage model | Stored in etcd | Stored in Vault backend |
| Default confidentiality | Base64 only, no default at-rest encryption | Secret storage is managed by Vault and access is policy-driven |
| Access control | Kubernetes RBAC | Vault policies plus auth methods |
| Rotation | Manual unless additional tooling is added | Built for dynamic secrets, leases, renewal, revocation |
| Pod delivery | Env vars or mounted files | Injected files, sidecar/agent, dynamic issuance |
| Best fit | Simple cluster-local secrets | Centralized, auditable, rotating, multi-platform secret management |

### When to use each

Use Kubernetes Secrets when:
- The workload is simple and cluster-local.
- You only need a small number of static values.
- You still enforce RBAC and at-rest encryption.

Use Vault when:
- You need secret rotation or short-lived credentials.
- Multiple platforms or clusters share the same secret source.
- You need auditability, revocation, and stronger separation of duties.

### Production recommendations

- Enable encryption at rest for `secrets` in the Kubernetes API server.
- Restrict secret access with least-privilege RBAC.
- Avoid storing real credentials in `values.yaml` or Git.
- Prefer external secret managers for production-grade credentials.
- Use dedicated service accounts per workload.
- Rotate credentials and audit access regularly.

## 5. Bonus - Vault Agent Templates

### Implemented template annotation

The chart implements the bonus requirement with a named helper in `_helpers.tpl` that renders a single `.env`-style file from multiple Vault keys:

```yaml
vault.hashicorp.com/agent-inject-template-config: |
  {{- with secret "kv/data/devops-info-service/config" -}}
  APP_USERNAME={{ .Data.data.username }}
  APP_PASSWORD={{ .Data.data.password }}
  {{- end }}
```

That template is emitted through the Helm helper and written to:

```text
/vault/secrets/app.env
```

The live pod also carries the related refresh and post-render annotations:

```yaml
vault.hashicorp.com/agent-inject-command-config: chmod 0640 /vault/secrets/app.env
vault.hashicorp.com/template-static-secret-render-interval: 2m
```

### Named template usage in Helm

A named template was added for common environment variables so the deployment stays DRY:

```yaml
{{- define "devops-info-service.envVars" -}}
- name: HOST
  value: {{ .Values.env.host | quote }}
- name: PORT
  value: {{ .Values.container.port | quote }}
- name: APP_ENV
  value: {{ .Values.env.appEnv | quote }}
- name: LOG_LEVEL
  value: {{ .Values.env.logLevel | quote }}
{{- end -}}
```

And used from `templates/deployment.yaml`:

```yaml
env:
  {{- include "devops-info-service.envVars" . | nindent 12 }}
```

### Rotation and refresh behavior

Important distinction:
- Dynamic secrets are renewed according to their lease.
- Static secrets such as KV v2 are re-fetched and re-rendered on an interval rather than lease renewal.

For this lab:
- The injected file is generated from KV v2 data under `kv/data/devops-info-service/config`.
- Vault Agent handles refresh through the template engine.
- For non-leased secrets, the refresh interval is controlled by the template engine's static secret render interval.
- The chart exposes that setting and the live run used `2m`.

### `agent-inject-command`

This chart also sets:

```yaml
vault.hashicorp.com/agent-inject-command-config: "chmod 0640 /vault/secrets/app.env"
```

Purpose:
- Run a command after the secret file is rendered or updated.
- Useful for permission fixes, app reload hooks, or SIGHUP-based config reload flows.
- In a real application, this can trigger a graceful reload after a secret update.

## 6. Reproducible commands

Cluster bootstrap:

```powershell
.\.tools\kind.exe create cluster --name lab11 --config .\k8s\kind-config-lab11.yml --kubeconfig .\k8s\lab11-kubeconfig
```

Imperative Secret task:

```powershell
kubectl --kubeconfig .\k8s\lab11-kubeconfig -n lab11 create secret generic app-credentials --from-literal=username=lab11-admin --from-literal=password=lab11-password
kubectl --kubeconfig .\k8s\lab11-kubeconfig -n lab11 get secret app-credentials -o yaml
```

Helm Secret task:

```powershell
.\.tools\helm.exe upgrade --install devops-info-service .\k8s\devops-info-service --kubeconfig .\k8s\lab11-kubeconfig --namespace lab11 -f .\k8s\devops-info-service\values-dev.yaml --set secrets.data.username=chart-user --set secrets.data.password=chart-password --wait --wait-for-jobs --timeout 8m
```

Vault task:

```powershell
.\.tools\helm.exe upgrade --install vault hashicorp/vault --kubeconfig .\k8s\lab11-kubeconfig --namespace vault --set server.dev.enabled=true --set injector.enabled=true --wait --timeout 10m
.\.tools\helm.exe upgrade devops-info-service .\k8s\devops-info-service --kubeconfig .\k8s\lab11-kubeconfig --namespace lab11 -f .\k8s\devops-info-service\values-dev.yaml -f .\k8s\devops-info-service\values-vault.yaml --set secrets.data.username=chart-user --set secrets.data.password=chart-password --wait --wait-for-jobs --timeout 10m
```

## Sources

Official references used for the security and rotation notes:
- Kubernetes Secrets: https://kubernetes.io/docs/concepts/configuration/secret/
- Kubernetes encryption at rest: https://kubernetes.io/docs/tasks/administer-cluster/encrypt-data/
- Kubernetes Secret good practices: https://kubernetes.io/docs/concepts/security/secrets-good-practices/
- Vault Agent Injector annotations: https://developer.hashicorp.com/vault/docs/deploy/kubernetes/injector/annotations
- Vault Agent Injector overview: https://developer.hashicorp.com/vault/docs/deploy/kubernetes/injector
- Vault Agent templates and refresh behavior: https://developer.hashicorp.com/vault/docs/agent/template
