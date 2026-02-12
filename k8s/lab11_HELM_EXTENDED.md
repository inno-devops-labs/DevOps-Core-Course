# Kubernetes Secrets and Hashicorp Vault

This document summarizes the implementation steps and evidence for Kubernetes Secrets, Helm-managed secrets, and HashiCorp Vault integration for Lab 11.

Author: Mikhail Dudinov @ez4gotit

## 1. Creating Secret via kubectl

Required secret format for the task:
- name: app-credentials
- keys: username, password

Example command set for the required secret:
```sh
kubectl create secret generic app-credentials \
  --from-literal=username="appuser" \
  --from-literal=password="P@ssw0rd"
```

Notes on encoding and encryption:
- Kubernetes Secrets store values as base64-encoded strings. Base64 is encoding, not encryption, and provides no confidentiality.
- By default, Kubernetes does not encrypt Secret data at rest in etcd. Encryption at rest must be explicitly enabled with an encryption provider configuration.
- etcd encryption is recommended in production to reduce exposure of Secret values in persistent storage. Access control, RBAC, and network policy should also be enforced.

```sh
kubectl create secret generic test --from-literal=SOME_SECRET=P@ssw0rd
kubectl get secrets
kubectl describe secret test
kubectl get secret test -o jsonpath='{.data}'
echo "UEBzc3cwcmQ=" | base64 --decode
```

![alt text](image-6.png)

## Secrets with Helm

This section applies Secret templating in the Helm chart and injects secret values into the Deployment as environment variables. The Secret name is configurable and defaults to `some-secret`. Labels use the chart helper templates for consistent metadata.

### Create `secrets.yaml`
```sh
vim helm-python/templates/secrets.yaml
```
```yaml
apiVersion: v1
kind: Secret
metadata:
  name: {{ .Values.secrets.name | default "some-secret" }}
  labels:
    {{- include "helm-python.labels" . | nindent 4 }}
data:
  {{- range $key, $val := .Values.secrets.data }}
  {{ $key }}: {{ $val | quote | b64enc }}
  {{- end }}
```

### Add env into Deployment
```sh
vim helm-python/templates/deployment.yaml
```
```yaml
env:
  - name: SOME_SECRET
    valueFrom:
      secretKeyRef:
        name: {{ .Values.secrets.name | default "some-secret" }}
        key: SOME_SECRET
```

### Edit `values.yaml`
```sh
vim helm-python/values.yaml
```
```yaml
secrets:
  name: "some-secret"
  data:
    SOME_SECRET: "P@ssw0rd"
    username: "appuser"
    password: "P@ssw0rd"
```

### Helm Upgrade
```bash
helm upgrade --install helm-secrets ./helm-python/
kubectl get pods,svc
```

![alt text](image-7.png)

### Pod Verification
```bash
kubectl exec pod/helm-secrets-helm-python-84f9c74747-scc9f -- printenv | grep SOME_SECRET
```

![alt text](image-8.png)

## Vault Secret Management System

Vault is used for centralized secret management with stronger access control, auditing, and secret injection capabilities. The deployment uses Vault in development mode for learning purposes.

### Install Vault
```sh
helm repo add hashicorp https://helm.releases.hashicorp.com
helm repo update
helm install vault hashicorp/vault --set "server.dev.enabled=true"
kubectl get pods
```

![alt text](image-9.png)

### Vault Configuration
#### Enable KV-v2 Secrets
```sh
kubectl exec -it vault-0 -- /bin/sh
vault secrets enable -path=internal kv-v2
vault kv put secret/database/config username="dbuser" password="somepassword"
vault kv get secret/database/config
exit
```

![alt text](image-10.png)

#### Enable Kubernetes Auth
```sh
kubectl exec -it vault-0 -- /bin/sh
vault auth enable kubernetes
vault write auth/kubernetes/config kubernetes_host="https://$KUBERNETES_PORT_443_TCP_ADDR:443"
```

#### Create a Policy for read access to secret
```sh
vault policy write internal-app - << EOF
path "internal/data/database/config" {
   capabilities = ["read"]
}
EOF
```

#### Create vault policy
```sh
vault write auth/kubernetes/role/internal-app \
  bound_service_account_names=internal-app \
  bound_service_account_namespaces=default \
  policies=internal-app \
  ttl=24h
exit
```

![alt text](image-11.png)

#### Check result
```sh
kubectl create sa internal-app
kubectl get serviceaccounts
```

![alt text](image-12.png)

```sh
kubectl annotate serviceaccount internal-app \
    meta.helm.sh/release-name=helm-secrets \
    meta.helm.sh/release-namespace=default -n default
```

```sh
kubectl label serviceaccount internal-app \
    app.kubernetes.io/managed-by=Helm -n default
helm install helm-secrets ./helm-python
```

```sh
vim helm-python/values.yaml
helm upgrade --install helm-secrets ./helm-python
kubectl get po
```

![alt text](image-13.png)

```sh
kubectl exec -it helm-secrets-helm-python-6dbb75d64f-r4ww9 --container helm-python -- sh 
```

![alt text](image-14.png)

### Resource Management
```yaml
resources:
  limits:
    cpu: 200m
    memory: 256Mi
  requests:
    cpu: 100m
    memory: 128Mi
```
