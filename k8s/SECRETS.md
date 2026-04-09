# Lab 11: Kubernetes Secrets & HashiCorp Vault

## Task 1: Kubernetes Secrets Fundamentals

### Creating and Viewing a Secret
![creating and viewing secrets](screenshots/lab11_screenshots/creating%20and%20viewing%20secrets%201.png)

### Decoding Secrets
![decoded secrets](screenshots/lab11_screenshots/decoded%20secret%20values%201.png)

### Security Implications
Kubernetes Secrets are base64-encoded, not encrypted. Anyone with API access can decode them. For production:
- Enable etcd encryption at rest
- Use RBAC to limit access
- Consider external secret managers (Vault)

## Task 2: Helm-Managed Secrets
### Chart Structure
![chart structure](screenshots/lab11_screenshots/chart%20structure%202.png)

### Secret Template (templates/secrets.yaml)
```yaml
apiVersion: v1
kind: Secret
metadata:
  name: {{ include "python-app.fullname" . }}-secrets
  labels:
    {{- include "python-app.labels" . | nindent 4 }}
type: Opaque
data:
  username: {{ .Values.secrets.username | b64enc | quote }}
  password: {{ .Values.secrets.password | b64enc | quote }}
  api-key: {{ .Values.secrets.apiKey | b64enc | quote }}
```

### Consuming Secrets in Deployment
```yaml
envFrom:
- secretRef:
    name: {{ include "python-app.fullname" . }}-secrets
```

### Verification
![verification](screenshots/lab11_screenshots/verification%202.png)

### Resource Limits
```yaml
resources:
  limits:
    cpu: 100m
    memory: 128Mi
  requests:
    cpu: 50m
    memory: 64Mi
```

### Requests vs Limits:
- Requests: Guaranteed resources for scheduling
- Limits: Maximum resources a container can use

## Task 3: HashiCorp Vault Integration
### Vault Installation
![vault installation](screenshots/lab11_screenshots/vault%20installed%20via%20helm%203.png)

![vault installation verification](screenshots/lab11_screenshots/vault%20installation%20verification%203.png)

### Vault Configuration
```bash
$ vault secrets enable -path=secret kv-v2

$ vault kv put secret/myapp/config \
  username="vault-admin" \
  password="vault-secret-456"

$ vault auth enable kubernetes

$ vault policy write myapp-policy - << EOF
path "secret/data/myapp/*" {
  capabilities = ["read"]
}
EOF

$ vault write auth/kubernetes/role/myapp-role \
  bound_service_account_names=myapp-sa \
  bound_service_account_namespaces=dev \
  policies=myapp-policy
```

### Vault Agent Annotations
```yaml
annotations:
        vault.hashicorp.com/address: "http://vault.vault:8200"
        vault.hashicorp.com/agent-inject: "true"
        vault.hashicorp.com/role: "myapp-role"
        vault.hashicorp.com/agent-inject-secret-config: "secret/myapp/config"
        vault.hashicorp.com/agent-inject-template-config: |
          {{`{{- with secret "secret/myapp/config" -}}
          export USERNAME="{{ .Data.username }}"
          export PASSWORD="{{ .Data.password }}"
          export API_KEY="{{ .Data.apikey }}"
          {{- end }}`}}
```

### Verification
![verification](screenshots/lab11_screenshots/kv%20secrets%20engine%20configured%203.png)

## Security Analysis
### K8s Secrets vs Vault

| Aspect	| K8s Secrets	| HashiCorp Vault |
| ------- | ------------ | -------------- |
| Encryption at rest	| Optional (etcd encryption)	| Yes(by default)
| Audit logging	| Limited	| Comprehensive
| Dynamic secrets	| No	| Yes
| Secret rotation	| Manual	| Automatic
| Lease management	| No	| Yes
| Complexity	| Low	| Higher

### When to Use Each
Kubernetes Secrets:
- Simple deployments
- Non-production environments
- When Vault is overkill

HashiCorp Vault:
- Production systems
- Regulatory compliance required
- Dynamic secrets needed
- Multi-cloud environments

### Production Recommendations
- Always enable etcd encryption for K8s Secrets
- Use RBAC to limit secret access
- Never commit secrets to Git
- Rotate secrets regularly
- Use external secret manager (Vault) for production
- Enable audit logging in Vault
- Use short TTLs for dynamic secrets