# Lab 11 - Kubernetes Secrets & HashiCorp Vault

## Overview

This lab demonstrates secure secret management in Kubernetes using:
- Kubernetes native Secrets
- Helm chart integration
- HashiCorp Vault with sidecar injection

## 1. Kubernetes Secrets

### Create a Secret

``` bash
kubectl create secret generic app-credentials \
  --from-literal=username=admin \
  --from-literal=password=supersecret
```

### View the Secret

``` bash
kubectl get secret app-credentials -o yaml
```

Screenshot: `docs/screenshots/11-1-base64.png`

### Decode Values

``` bash
echo "YWRtaW4=" | base64 -d
echo "c3VwZXJzZWNyZXQ=" | base64 -d
```

Screenshot: `docs/screenshots/11-2-decoded.png`

### Explanation

-   Kubernetes Secrets use base64 encoding 
-   Anyone with access can decode them

#### Security Notes

-   Enable etcd encryption at rest
-   Use RBAC
-   Prefer external secret managers (Vault)

## 2. Helm Secret Integration

### Secret Template

``` yaml
apiVersion: v1
kind: Secret
metadata:
  name: {{ include "devops-chart.fullname" . }}-secret
type: Opaque
stringData:
  username: {{ .Values.secret.username }}
  password: {{ .Values.secret.password }}
```

### Inject into Deployment

``` yaml
envFrom:
  - secretRef:
      name: devops-app-devops-chart-secret
```

### Deploy

``` bash
helm upgrade --install devops-app . \
  --set secret.username=admin \
  --set secret.password=supersecret
```

### Verify

``` bash
kubectl exec -it <pod> -- printenv | grep -E 'username|password'
```

``` bash
kubectl describe pod <pod>
```

## 3. Resource Management

``` yaml
resources:
  requests:
    cpu: 100m
    memory: 128Mi
  limits:
    cpu: 200m
    memory: 256Mi
```

Explanation:
- Requests = guaranteed resources
- Limits = max allowed


## 4. Vault Integration

### Install Vault

``` bash
helm repo add hashicorp https://helm.releases.hashicorp.com
helm repo update

helm install vault hashicorp/vault \
  --set "server.dev.enabled=true" \
  --set "injector.enabled=true"
```

``` bash
kubectl get pods
```

### Store Secret

``` bash
vault kv put secret/myapp/config username="vault-user" password="vault-pass"
vault kv get secret/myapp/config
```

### Deploy with Vault

``` bash
helm upgrade --install devops-app . \
  --set secret.enabled=false \
  --set vault.enabled=true \
  --set vault.role=devops-app \
  --set vault.secretPath=secret/data/myapp/config
```

### Verify Injection

``` bash
kubectl get pods
```

Screenshot: `docs/screenshots/11-3-pods.png`

``` bash
kubectl exec -it <pod> -- sh
ls /vault/secrets
cat /vault/secrets/config
```

Screenshot: `docs/screenshots/11-4-injected.png`

### Explanation

Vault uses the **sidecar injection pattern**:
- A Vault agent container runs alongside the app
- Secrets are injected into the pod filesystem


## 5. Security Analysis

### Kubernetes Secrets

-   Simple
-   Base64 encoded
-   Limited security

### Vault

-   Centralized
-   Fine-grained access control
-   Supports rotation

### Conclusion

-   Use Kubernetes Secrets for simple cases
-   Use Vault for production