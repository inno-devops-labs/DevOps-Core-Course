# lab 11: kubernetes secrets & hashicorp vault

## 1. kubernetes secrets fundamentals

### creating a secret imperatively

```bash
# create secret with username and password
kubectl create secret generic app-credentials \
  --from-literal=username=admin \
  --from-literal=password=supersecret123

# output: secret/app-credentials created
```

### viewing the secret

[secrets and its decoded values](screenshots/kubectl-get-secret.png)

### encoding vs encryption

| aspect | encoding (base64) | encryption |
|--------|-------------------|------------|
| purpose | data representation | data protection |
| reversibility | anyone can decode | requires key |
| security | none | strong protection |
| k8s default | yes | no (unless enabled) |

**key insight:** kubernetes secrets are **encoded**, not encrypted by default.

### etcd encryption

| question | answer |
|----------|--------|
| are secrets encrypted at rest by default? | no, only base64-encoded |
| what is etcd encryption? | encrypts secret data in etcd database |
| when to enable? | production, compliance requirements, multi-tenant clusters |

---

## 2. helm-managed secrets

### chart structure (updated)

```
k8s/devops-info-service/
├── Chart.yaml
├── values.yaml
└── templates/
    ├── _helpers.tpl
    ├── deployment.yaml
    ├── secrets.yaml      # <-- new: secret template
    ├── service.yaml
    └── serviceaccount.yaml
```

### secrets.yaml template

```yaml
{{- if .Values.secrets.enabled }}
apiVersion: v1
kind: Secret
metadata:
  name: {{ include "devops-info-service.fullname" . }}-credentials
  labels:
    {{- include "devops-info-service.labels" . | nindent 4 }}
type: Opaque
stringData:
  {{- range $key, $value := .Values.secrets.data }}
  {{ $key }}: {{ $value | quote }}
  {{- end }}
{{- end }}
```

### values.yaml secret configuration

```yaml
secrets:
  enabled: true
  data:
    username: "placeholder-user"
    password: "placeholder-password"
```

### consuming secrets in deployment

**pattern: individual keys with secretKeyRef**

```yaml
env:
  - name: APP_USERNAME
    valueFrom:
      secretKeyRef:
        name: {{ include "devops-info-service.fullname" . }}-credentials
        key: username
  - name: APP_PASSWORD
    valueFrom:
      secretKeyRef:
        name: {{ include "devops-info-service.fullname" . }}-credentials
        key: password
```

### secret injection patterns

| pattern | use case |
|---------|----------|
| `envFrom` + `secretRef` | load all keys as env vars |
| `env` + `secretKeyRef` | load specific keys |
| volume mount | load as files |

### verification

[helm secrets integration](screenshots/kubectl-get-secret.png)

---

## 3. resource management

### resource configuration

```yaml
resources:
  limits:
    cpu: 200m
    memory: 256Mi
  requests:
    cpu: 100m
    memory: 128Mi
```

### requests vs limits

| aspect | requests | limits |
|--------|----------|--------|
| purpose | guaranteed resources | maximum allowed |
| scheduling | used for pod placement | not used |
| behavior | reserved | kill (memory) / throttle (cpu) |
| qos class | affects burstable/guaranteed |

### resource units

| type | unit | example |
|------|------|---------|
| cpu | millicores (m) | 100m = 0.1 core, 1000m = 1 core |
| memory | mebibytes (Mi) | 128Mi, 256Mi, 512Mi |

### choosing values

| approach | recommendation |
|----------|----------------|
| monitor usage | `kubectl top pods` |
| requests | based on observed usage |
| limits | 1.5-2x requests |
| production | requests = limits (guaranteed qos) |

---

## 4. hashicorp vault integration

### installing vault

[hashicorp installation verification](screenshots/hashicorp-vault-installed.png)

### configuring vault

```bash
# exec into vault pod
kubectl exec -it vault-0 -- /bin/sh
```

**inside vault pod:**

```bash
# enable kv secrets engine v2
vault secrets enable -path=secret kv-v2

# create secret for application
vault kv put secret/devops-info/config username="app-user" password="secure-password-123"

# enable kubernetes auth
vault auth enable kubernetes

# configure kubernetes auth
vault write auth/kubernetes/config \
  kubernetes_host="https://$KUBERNETES_PORT_443_TCP_ADDR:443"
```

### creating policy and role

```bash
# create policy
cat <<EOF | vault policy write devops-info-policy -
path "secret/data/devops-info/config" {
  capabilities = ["read"]
}
EOF

# create role binding policy to service account
vault write auth/kubernetes/role/devops-info-service \
  bound_service_account_names=devops-info-service \
  bound_service_account_namespaces=default \
  policies=devops-info-policy \
  ttl=24h
```

[hashicorp vault role](screenshots/hashicorp-vault-role.png)

### vault agent annotations

```yaml
annotations:
  vault.hashicorp.com/agent-inject: "true"
  vault.hashicorp.com/role: "devops-info-service"
  vault.hashicorp.com/agent-inject-secret-config: "secret/data/devops-info/config"
  vault.hashicorp.com/agent-inject-template-config: |
    {{- with secret "secret/data/devops-info/config" -}}
    username={{ .Data.data.username }}
    password={{ .Data.data.password }}
    {{- end }}
```

### verifying secret injection

[secret injection](screenshots/secret-injection.png)


### sidecar injection pattern

```
┌─────────────────────────────────────────────────────────┐
│                         pod                              │
│  ┌──────────────────┐    ┌──────────────────────────┐   │
│  │   application    │    │   vault agent sidecar    │   │
│  │   container      │◄───│   - auth with k8s        │   │
│  │                  │    │   - retrieve secrets     │   │
│  │  /vault/secrets/ │    │   - write to shared vol  │   │
│  │  └── config      │    │   - auto-renew token     │   │
│  └──────────────────┘    └──────────────────────────┘   │
└─────────────────────────────────────────────────────────┘
```

**how it works:**
1. mutation webhook intercepts pod creation
2. detects `vault.hashicorp.com/agent-inject: "true"`
3. injects vault-agent sidecar container
4. sidecar authenticates and retrieves secrets
5. secrets written to `/vault/secrets/`

---

## 5. security analysis

### k8s secrets vs vault

| feature | k8s secrets | vault |
|---------|-------------|-------|
| encryption | base64 only | aes-256 |
| access control | rbac | fine-grained policies |
| audit logging | limited | comprehensive |
| secret rotation | manual | automatic |
| dynamic secrets | no | yes |
| lease & renewal | no | yes, with ttl |

### when to use each

| use k8s secrets | use vault |
|-----------------|-----------|
| dev/test environments | production |
| simple applications | compliance requirements |
| few secrets | need audit trails |
| trusted team | dynamic secrets needed |
| secrets rarely change | rotation requirements |

### production recommendations

| recommendation | reason |
|----------------|--------|
| never use dev mode vault | use proper init/unseal |
| enable tls | secure communication |
| dedicated namespace | isolation |
| backup strategy | disaster recovery |
| monitoring & alerting | health visibility |
| short ttls | limit exposure |
| audit logging | compliance |

---

## 6. bonus: vault agent templates

### template annotation

```yaml
vault.hashicorp.com/agent-inject-template-config: |
  {{- with secret "secret/data/devops-info/config" -}}
  # application configuration
  DATABASE_URL=postgres://{{ .Data.data.username }}:{{ .Data.data.password }}@db:5432/myapp
  API_KEY={{ .Data.data.api_key }}
  {{- end }}
```

### named templates in _helpers.tpl

```yaml
{{/*
common environment variables from values
*/}}
{{- define "devops-info-service.envVars" -}}
- name: HOST
  value: {{ .Values.env.HOST | quote }}
- name: PORT
  value: {{ .Values.env.PORT | quote }}
- name: DEBUG
  value: {{ .Values.env.DEBUG | quote }}
{{- end }}

{{/*
secret environment variables
*/}}
{{- define "devops-info-service.secretEnvVars" -}}
- name: APP_USERNAME
  valueFrom:
    secretKeyRef:
      name: {{ include "devops-info-service.fullname" . }}-credentials
      key: username
- name: APP_PASSWORD
  valueFrom:
    secretKeyRef:
      name: {{ include "devops-info-service.fullname" . }}-credentials
      key: password
{{- end }}
```

### secret rotation mechanism

| step | action |
|------|--------|
| 1 | vault agent monitors secret ttl |
| 2 | renews lease before expiration |
| 3 | re-renders template files |
| 4 | notifies app via command hook |

```yaml
# notify app on secret change
vault.hashicorp.com/agent-inject-command-config: |
  pkill -HUP myapp
```

### templating benefits

| benefit | description |
|---------|-------------|
| dry principle | define once, reference everywhere |
| format flexibility | .env, json, yaml, any format |
| automatic rotation | secrets update without restart |
| reduced complexity | app reads files, no vault sdk |

---

## 8. file references

| file | description |
|------|-------------|
| [secrets.yaml](../devops-info-service/templates/secrets.yaml) | secret template |
| [deployment.yaml](../devops-info-service/templates/deployment.yaml) | updated deployment |
| [_helpers.tpl](../devops-info-service/templates/_helpers.tpl) | named templates |
| [values.yaml](../devops-info-service/values.yaml) | updated values |
