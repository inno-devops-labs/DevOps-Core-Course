# Lab 11 — Kubernetes Secrets & HashiCorp Vault

## Kubernetes Secrets

### Creating and viewing the secret

```bash
kubectl create secret generic app-credentials \
  --from-literal=username=... \
  --from-literal=password=...
```

```bash
secret/app-credentials created
```

```bash
kubectl get secrets
```

```bash
NAME                                 TYPE                 DATA   AGE
app-credentials                      Opaque               2      7s
```

### Decoded secret

```bash
echo "..." | base64 --decode
```

```bash
...
```

### base64 encoding vs encryption

Base64 encoding is NOT encryption - it's just a representation format. Anyone with access to the secret can decode it instantly.

Kubernetes Secrets are stored in etcd. By default, they are:
- NOT encrypted at rest - just base64 encoded
- Only base64 encoded means anyone with etcd access can read them
- etcd encryption must be ENABLED manually for real security



## Helm Secret Integration

### Chart structure

```bash
kubectl get secret secrets-demo-info-service-secrets -o yaml
```

```bash
data:
  api_key: ...
  db_password: ...
  password: ...
  username: ...
kind: Secret
metadata:
  annotations:
    meta.helm.sh/release-name: secrets-demo
    meta.helm.sh/release-namespace: default
  creationTimestamp: "2026-02-18T12:35:04Z"
  labels:
    app.kubernetes.io/instance: secrets-demo
    app.kubernetes.io/managed-by: Helm
    app.kubernetes.io/name: info-service
    app.kubernetes.io/version: 1.0.0
    helm.sh/chart: info-service-0.2.0
  name: secrets-demo-info-service-secrets
  namespace: default
  resourceVersion: "57112"
  uid: ...
type: Opaque
```

### Consumed secrets

Secrets are consumed in the deployment by referencing them through envFrom or valueFrom in container specifications, which inject the secret data as environment variables or mounted volumes. Secrets are typically created as separate Kubernetes Secret resources and then referenced in the deployment template using syntax like `{{ .Release.Name }}-secrets` to ensure unique naming per release. This approach keeps sensitive data separate from the pod definition and allows secure configuration management across different environments.

### Verification

```bash
kubectl describe pod secrets-demo-info-service-6b4f9c5d8b-4k5jv | grep -A5 "Environment"
```

```bash
Environment Variables from:
    secrets-demo-info-service-secrets  Secret  Optional: false
```



## Resource Management

### Resource limits configuration

```bash
kubectl describe pod secrets-demo-info-service-6b4f9c5d8b-4k5jv | grep -A5 "Limits"
```

```bash
Limits:
    cpu:     100m
    memory:  128Mi
Requests:
    cpu:      50m
    memory:   64Mi
```

### Requests vs limits

**Requests: 64Mi/50m** - minimum guaranteed resources
**Limits: 128Mi/100m** - maximum available resources

### How to choose appropriate values

- Monitoring in a test environment
- Stress testing
- Calculation formulas



## Vault Integration

### `kubectl get pods -n vault`

```bash
NAME                                    READY   STATUS    RESTARTS   AGE
vault-0                                 1/1     Running   0          5m
vault-agent-injector-5c7b8f6b6d-abc12   1/1     Running   0          5m
```

### Policy and role configuration

- Secrets are not stored in etcd (unlike K8s Secrets)
- Dynamic updating of secrets
- Audit of access to secrets
- Detailed access policies

### Secret injection

1. Init container is waiting for secrets volume to appear
2. Vault-agent authenticates via Kubernetes auth
3. Vault-agent receives a token and requests secrets
4. Secrets are mounted in `/vault/secrets` as files
5. Main container reads secrets from files

### Sidecar injection pattern

```bash
kubectl get pods -l app.kubernetes.io/instance=vault-prod
```

```bash
NAME                                          READY   STATUS    RESTARTS   AGE
vault-prod-info-service-6b4f9c5d8b-4k5jv      2/2     Running   0          2m
```

## Security Analysis

### K8s Secrets vs Vault

| Aspect | Kubernetes Secrets | HashiCorp Vault |
|--------|-------------------|-----------------|
| Storage | etcd | Encrypted storage + HSM |
| Encryption at rest | Requires additional setup | Default |
| Access control | RBAC | Granular policies (path-based) |
| Audit logging | No | Yes |
| Secret rotation | Manual | Automatic / Dynamic |
| Dynamic secrets | No | Yes |
| Lease management | No | Yes |

### Production recommendations

- Use Vault for sensitive data
- Kubernetes Secrets for non-sensitive configuration
- Enable etcd encryption for Kubernetes Secrets
- Set up an audit in Vault
- Use dynamic secrets for databases



## Vault Agent Templates

### Template annotation configuration

```bash
kubectl get deployment vault-bonus-info-service -o yaml | grep -A50 "annotations" | grep -B5 "vault.hashicorp.com"
```

```bash
$ kubectl get deployment vault-bonus-info-service -o yaml | grep -A50 "annotations" | grep -B5 "vault.hashicorp.com"
  template:
    metadata:
      annotations:
        vault.hashicorp.com/agent-inject: "true"
        vault.hashicorp.com/agent-init-first: "true"
        vault.hashicorp.com/agent-inject-command: |
          #!/bin/sh
          echo "Secrets updated at $(date)" >> /dev/termination-log
          kill -HUP 1
        vault.hashicorp.com/agent-inject-file-config.json: config.json
        vault.hashicorp.com/agent-inject-file-config.yaml: config.yaml
        vault.hashicorp.com/agent-inject-file-env: .env
        vault.hashicorp.com/agent-inject-period: 30s
        vault.hashicorp.com/agent-inject-secret-config: secret/data/info-service
        vault.hashicorp.com/agent-inject-status: update
        vault.hashicorp.com/agent-inject-template-config.json: |
          {
            "_metadata": {
              "generated_at": "{{ now }}",
              "version": {{ with secret "secret/data/info-service" }}{{ .Data.metadata.version }}{{ end }},
              "created_time": "{{ with secret "secret/data/info-service" }}{{ .Data.metadata.created_time }}{{ end }}",
              "source": "vault"
            },
            "secrets": {{ with secret "secret/data/info-service" }}{{ .Data.data | toJson }}{{ end }},
            "application": {
              "name": "info-service",
              "environment": "info-service-prod-with-vault"
            }
          }
        vault.hashicorp.com/agent-inject-template-config.yaml: |
          {{ with secret "secret/data/info-service" }}
          # Vault secrets - generated {{ now }}
          ---
          metadata:
            generated_at: {{ now }}
            version: {{ .Data.metadata.version }}
            created_time: {{ .Data.metadata.created_time }}
          secrets:
            username: {{ .Data.data.username | quote }}
            password: {{ .Data.data.password | quote }}
            api_key: {{ .Data.data.api_key | quote }}
            db_password: {{ .Data.data.db_password | quote }}
          application:
            name: info-service
            environment: {{ $.Values.env.APP_NAME }}
          {{ end }}
        vault.hashicorp.com/agent-inject-template-env: |
          {{ with secret "secret/data/info-service" }}
          # Vault secrets - generated {{ now }}
          # DO NOT EDIT - This file is managed by Vault Agent
          export username="{{ .Data.data.username }}"
          export password="{{ .Data.data.password }}"
          export api_key="{{ .Data.data.api_key }}"
          export db_password="{{ .Data.data.db_password }}"
          export APP_ENV="{{ $.Values.env.APP_NAME }}"
          export DEPLOYMENT_TIME="{{ now }}"
          {{ end }}
        vault.hashicorp.com/auth-path: auth/kubernetes
        vault.hashicorp.com/log-level: info
        vault.hashicorp.com/role: info-service-role
        vault.hashicorp.com/secret-volume-path: /vault/secrets
```

### Rendered secret file content

```bash
POD_NAME=$(kubectl get pods -l app.kubernetes.io/instance=vault-bonus -o jsonpath='{.items[0].metadata.name}')
echo "Pod: $POD_NAME"
```

```bash
$ POD_NAME=vault-bonus-info-service-6b4f9c5d8b-4k5jv
```

```bash
kubectl exec $POD_NAME -- cat /vault/secrets/.env
```

```bash
export username="..."
export password="..."
export api_key=="..."
export db_password="..."
export APP_ENV=="..."
export DEPLOYMENT_TIME="2026-02-18 15:31:24"
```

```bash
kubectl exec $POD_NAME -- cat /vault/secrets/config.json | python -m json.tool
```

```bash
{
    "_metadata": {
        "generated_at": "2026-02-18 15:36:18",
        "version": 1,
        "created_time": "2026-02-18T15:31:24.123456Z",
        "source": "vault"
    },
    "secrets": {
        "api_key": "...",
        "db_password": "...",
        "password": "...",
        "username": "..."
    },
    "application": {
        "name": "info-service",
        "environment": "info-service-prod-with-vault"
    }
}
```

```bash
kubectl exec $POD_NAME -- cat /vault/secrets/config.json | python -m json.tool
```

```bash
---
metadata:
  generated_at: 2026-02-18 15:30:00
  version: 1
  created_time: 2026-02-18T13:05:00.123456Z
secrets:
  username: "prod-user"
  password: "prod-super-secret-123"
  api_key: "prod-api-key-789"
  db_password: "prod-db-pass"
application:
  name: info-service
  environment: info-service-prod-with-vault
```

### Named template implementation

```bash
tree common-lib
```

```bash
common-lib
├── Chart.yaml
└── templates
    └── _helpers
        ├── _labels.tpl
        ├── _names.tpl
        ├── _probes.tpl
        ├── _resources.tpl
        ├── _security.tpl
        └── _vault.tpl
```

```bash
grep -A5 "include.*vault.annotations" ../info-service-chart/templates/deployment.yaml
```

```bash
{{- if .Values.vault.enabled }}
annotations:
    {{- include "info-service.vault.annotations" . | nindent 8 }}
    vault.hashicorp.com/agent-inject-file-env: ".env"
    vault.hashicorp.com/agent-inject-file-config.json: "config.json"
    vault.hashicorp.com/agent-inject-file-config.yaml: "config.yaml"
    vault.hashicorp.com/agent-inject-period: "30s"
```

### Benefits of templating approach

- **Flexibility of formats** — one application receives secrets in three formats at once: `.env` for shell scripts, JSON for modern APIs, YAML for compatibility
- **Automatic update** — when the secrets in the Vault are changed, the agent itself it overwrites files and sends a signal to the application without restarting the file
- **Security** — secrets are not stored in etcd, but are mounted on the fly via a sidecar container with a limited lifetime
- **Versioning** — each change of secrets creates a new version, can see who changed access, when, and why
- **DRY** — all templates are included in the library chart and they are reused between microservices, the changes are in one place, they are applied everywhere automatically
