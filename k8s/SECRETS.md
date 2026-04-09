# Lab 11 - Kubernetes Secrets & HashiCorp Vault

## Kubernetes Secrets

Created a secret with kubectl:

```
$ kubectl create secret generic app-credentials --from-literal=username=iu-capstone-ad --from-literal=password=foobar
secret/app-credentials created
```

Viewing it in YAML:

```
$ kubectl get secret app-credentials -o yaml
apiVersion: v1
data:
  password: Zm9vYmFy
  username: aXUtY2Fwc3RvbmUtYWQ=
kind: Secret
metadata:
  creationTimestamp: "2026-04-09T19:09:05Z"
  name: app-credentials
  namespace: default
  resourceVersion: "5748"
  uid: 743ee111-9a81-469c-80a8-fd325bd66583
type: Opaque
```

Decoding:

```
$ echo "aXUtY2Fwc3RvbmUtYWQ=" | base64 -d
iu-capstone-ad
$ echo "Zm9vYmFy" | base64 -d
foobar
```

base64 is encoding, not encryption. Anyone with kubectl access can decode secret values. Secrets are stored as plaintext.

## Helm Secret Integration

### Chart structure

```
k8s/devops-info-service/
  templates/
    secrets.yaml         # secret manifest
    serviceaccount.yaml  # service account
    deployment.yaml      # consumes secret via envFrom, vault annotations
    _helpers.tpl         # named envVars template
  values.yaml
```

`templates/secrets.yaml` uses `stringData` so values are auto-encoded on write:

```yaml
stringData:
  username: {{ .Values.secret.username | quote }}
  password: {{ .Values.secret.password | quote }}
```

Placeholder defaults in `values.yaml`:

```yaml
secret:
  username: "change-me"
  password: "change-me"
```

Real values are passed at install time, never committed:

```
helm upgrade myrelease ./devops-info-service --set secret.username=iu-capstone-ad --set secret.password=foobar
```

### Consuming secrets in deployment

All keys from the secret are injected as env vars via `envFrom`:

```yaml
envFrom:
  - secretRef:
      name: {{ include "devops-info-service.fullname" . }}-secret
```

### Verification

```
$ kubectl exec myrelease-devops-info-service-6769f88554-g9v2l -c devops-info-service -- env | grep -iE "username|password|APP_ENV|LOG_LEVEL"
password=foobar
username=iu-capstone-ad
APP_ENV=production
LOG_LEVEL=info
```

Secrets are not visible in `kubectl describe pod` -- only the secret reference name is shown.

## Resource Management

Configured in `values.yaml`:

```yaml
resources:
  requests:
    memory: "128Mi"
    cpu: "100m"
  limits:
    memory: "256Mi"
    cpu: "200m"
```

Requests are what the scheduler uses to place the pod. The pod is guaranteed at least that much. Limits are the hard cap -- exceeding memory causes OOM kill, exceeding CPU causes throttling. Requests should match typical steady-state usage. Limits should leave headroom for bursts but stay tight enough to prevent one pod from starving others.

## Vault Integration

### Installation

```
$ helm repo add hashicorp https://helm.releases.hashicorp.com
"hashicorp" has been added to your repositories

$ helm install vault hashicorp/vault --set "server.dev.enabled=true" --set "injector.enabled=true"
NAME: vault
LAST DEPLOYED: Thu Apr  9 22:18:01 2026
STATUS: deployed
```

```
$ kubectl get pods -l app.kubernetes.io/instance=vault
NAME                                    READY   STATUS    RESTARTS   AGE
vault-0                                 1/1     Running   0          9m19s
vault-agent-injector-848dd747d7-2s989   1/1     Running   0          9m20s
```

### Secret engine and KV secret

```
$ kubectl exec vault-0 -- vault kv put secret/myapp/config username="iu-capstone-ad" password="foobar"
====== Secret Path ======
secret/data/myapp/config

$ kubectl exec vault-0 -- vault kv get secret/myapp/config
====== Data ======
Key         Value
---         -----
password    foobar
username    iu-capstone-ad
```

### Kubernetes auth

```
$ kubectl exec vault-0 -- vault auth enable kubernetes
Success! Enabled kubernetes auth method at: kubernetes/

$ kubectl exec vault-0 -- /bin/sh -c 'vault write auth/kubernetes/config kubernetes_host="https://$KUBERNETES_PORT_443_TCP_ADDR:443"'
Success! Data written to: auth/kubernetes/config
```

### Policy and role

Policy grants read on the secret path:

```
$ kubectl exec vault-0 -- /bin/sh -c 'vault policy write devops-info-service - <<EOF
path "secret/data/myapp/config" {
  capabilities = ["read"]
}
EOF'
Success! Uploaded policy: devops-info-service
```

Role binds the policy to the app service account:

```
$ kubectl exec vault-0 -- vault write auth/kubernetes/role/devops-info-service bound_service_account_names=myrelease-devops-info-service bound_service_account_namespaces=default policies=devops-info-service ttl=24h
```

### Vault Agent injection

Annotations in the deployment template (enabled when `vault.enabled=true`):

```yaml
annotations:
  vault.hashicorp.com/agent-inject: "true"
  vault.hashicorp.com/role: "devops-info-service"
  vault.hashicorp.com/agent-inject-secret-config: "secret/data/myapp/config"
  vault.hashicorp.com/agent-inject-template-config: |
    {{- with secret "secret/data/myapp/config" -}}
    USERNAME={{ .Data.data.username }}
    PASSWORD={{ .Data.data.password }}
    {{- end -}}
```

### Proof of injection

```
$ kubectl get pods -l app.kubernetes.io/instance=myrelease
NAME                                             READY   STATUS    RESTARTS   AGE
myrelease-devops-info-service-6769f88554-g9v2l   2/2     Running   0          65s
myrelease-devops-info-service-6769f88554-m54qq   2/2     Running   0          80s
myrelease-devops-info-service-6769f88554-v4dd2   2/2     Running   0          88s

$ kubectl exec myrelease-devops-info-service-6769f88554-g9v2l -c devops-info-service -- cat /vault/secrets/config
USERNAME=iu-capstone-ad
PASSWORD=foobar
```

2/2 READY means the vault-agent sidecar is running alongside the app container. The Vault agent injector is a mutating admission webhook. On pod creation it injects an init container (`vault-agent-init`) that fetches secrets before the app starts, and a sidecar (`vault-agent`) that keeps the token renewed and re-renders secrets on rotation. Secrets land in a shared in-memory volume at `/vault/secrets/`. The app reads files from there -- no Vault SDK needed.

## Security Analysis

K8s Secrets store data as base64 in etcd not encrypted. Vault encrypts on disk and supports dynamic secrets and automatic rotation.

Use K8s Secrets when simplicity is enough.

Use Vault when you need audit trails or short-lived credentials.

## Bonus - Vault Agent Templates

### Template annotation

The template renders secrets as a `.env`-style file:

```yaml
vault.hashicorp.com/agent-inject-template-config: |
  {{- with secret "secret/data/myapp/config" -}}
  USERNAME={{ .Data.data.username }}
  PASSWORD={{ .Data.data.password }}
  {{- end -}}
```

This allows rendering multiple secrets into one file in any format (JSON, TOML, shell exports, etc.) instead of mounting raw Vault JSON.

### Secret rotation

Vault Agent polls the secret lease and re-renders the template when the secret changes. The `vault.hashicorp.com/agent-inject-command` annotation can run an arbitrary command (e.g. `kill -HUP 1`) after re-rendering, so the app reloads config without a pod restart.

### Named template for environment variables

In `_helpers.tpl`:

```yaml
{{- define "devops-info-service.envVars" -}}
- name: APP_ENV
  value: {{ .Values.appEnv | default "production" | quote }}
- name: LOG_LEVEL
  value: {{ .Values.logLevel | default "info" | quote }}
{{- end }}
```

Used in `deployment.yaml`:

```yaml
env:
  {{- include "devops-info-service.envVars" . | nindent 12 }}
```

Keeps common env var definitions in one place. Avoids repeating the same block across templates.
