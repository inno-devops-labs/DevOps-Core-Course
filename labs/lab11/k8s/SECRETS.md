# Lab 11 — Kubernetes Secrets & HashiCorp Vault

## 1. Kubernetes Secrets

### Secret creation with kubectl

A Kubernetes Secret named `app-credentials` was created using the imperative command:

```bash
kubectl create secret generic app-credentials \
  --from-literal=username=devuser \
  --from-literal=password=devpass123
```

### Viewing the secret

```bash
kubectl get secret app-credentials -o yaml
```

Example output:

apiVersion: v1
data:
  password: ZGV2cGFzczEyMw==
  username: ZGV2dXNlcg==
kind: Secret
metadata:
  name: app-credentials
type: Opaque

### Decoding the values

```bash
echo "ZGV2dXNlcg==" | base64 -d
echo
echo "ZGV2cGFzczEyMw==" | base64 -d
echo
```

Decoded values:

username = devuser
password = devpass123

### Base64 encoding vs encryption

Kubernetes Secrets store values in base64-encoded format.
Base64 is only encoding, not encryption.

This means:

anyone with access to the Secret object can decode the values
Secrets are not automatically strongly protected just because they are stored as Secret resources
Security implications

For production environments:

RBAC should restrict access to Secrets
encryption at rest should be enabled for etcd
external secret managers such as Vault are recommended for stronger security

## 2. Helm Secret Integration

### Chart structure

The Helm chart was extended with secret management:

labs/lab11/k8s/devops-info-service/
├── Chart.yaml
├── values.yaml
├── values-dev.yaml
├── values-prod.yaml
└── templates/
    ├── deployment.yaml
    ├── service.yaml
    ├── secrets.yaml
    ├── serviceaccount.yaml
    ├── _helpers.tpl
    ├── NOTES.txt
    └── hooks/
    
### Secret template

A new template file was added:

templates/secrets.yaml

This template creates a Kubernetes Secret using values from Helm configuration.

Secret values

Secret values are defined in:

values.yaml with placeholder defaults
values-dev.yaml with development values
values-prod.yaml with placeholder production values
Secret consumption in Deployment

The Deployment consumes the Secret using:

envFrom:
  - secretRef:
      name: <templated-secret-name>


### Verification inside the pod

The Helm release was installed:

```bash
helm install secrets-release . -f values-dev.yaml
```

The created Secret:

```bash
kubectl get secrets
```

Example output included:

app-credentials
secrets-release-devops-info-service-secret

Environment variables inside the pod were verified with:

```bash
kubectl exec -it secrets-release-devops-info-service-7b8848dbcd-7vrb2 -- env | grep -i -E 'username|password'
```

Output:

password=devpass123
username=devuser

### Pod description verification

```bash
kubectl describe pod secrets-release-devops-info-service-7b8848dbcd-7vrb2
```

The pod description showed:

Environment Variables from:
  secrets-release-devops-info-service-secret  Secret  Optional: false

The actual secret values were not shown in kubectl describe pod, only the reference to the Secret.

## 3. Resource Management

### Configured resources

The Deployment includes configurable CPU and memory requests/limits.

Example configuration:

resources:
  requests:
    cpu: "50m"
    memory: "64Mi"
  limits:
    cpu: "100m"
    memory: "128Mi"
    
### Requests vs limits

Requests define the minimum amount of CPU and memory required for scheduling
Limits define the maximum amount of CPU and memory the container is allowed to use

### Choosing values

For this lab:

lower values were used in development for local cluster efficiency
the chart still follows Kubernetes resource management best practices
values remain configurable through Helm

## 4. Vault Integration

### Vault installation

Vault was installed using Helm:

```bash
helm repo add hashicorp https://helm.releases.hashicorp.com
helm repo update

helm install vault hashicorp/vault \
  --set "server.dev.enabled=true" \
  --set "injector.enabled=true"  
```

### Vault installation verification

```bash
kubectl get pods
```

Relevant running resources:

vault-0
vault-agent-injector-...

### Secret creation in Vault

Inside the Vault pod, a secret was written to the KV path:

```bash
vault kv put secret/devops-info-service/config username="vaultuser" password="vaultpass123"
```

### Kubernetes auth configuration

Vault Kubernetes authentication was configured with:

Kubernetes auth method
policy devops-info-service
role devops-info-service

The role was bound to the application service account:

vault-release-devops-info-service
Vault Agent injection

Vault annotations were enabled in the Deployment template.

Verified annotations from the pod:

vault.hashicorp.com/agent-inject: true
vault.hashicorp.com/agent-inject-secret-config: secret/data/devops-info-service/config
vault.hashicorp.com/agent-inject-status: injected
vault.hashicorp.com/role: devops-info-service


### Sidecar injection pattern

The injected pod contained:

init container: vault-agent-init
application container: devops-info-service
sidecar container: vault-agent

This demonstrates the Vault Agent sidecar injection pattern:

the init container prepares authentication and secret rendering
the sidecar agent keeps Vault integration active
the application reads secrets from files mounted into the pod

### Proof of secret injection

Secrets were verified inside the pod:

```bash
kubectl exec -it vault-release-devops-info-service-64db8d7688-xlnhp -c devops-info-service -- ls -R /vault/secrets
kubectl exec -it vault-release-devops-info-service-64db8d7688-xlnhp -c devops-info-service -- cat /vault/secrets
```

config

Output:

/vault/secrets:
config

Rendered content:

data: map[password:vaultpass123 username:vaultuser]
metadata: map[created_time:2026-04-09T08:46:08.785957176Z custom_metadata:<nil> deletion_time: destroyed:false version:1]

This confirms that Vault successfully injected the application secret into the pod filesystem.

## 5. Security Analysis

### Kubernetes Secrets

Advantages

built into Kubernetes
easy to create and use
simple integration with pods via env vars or mounted volumes

Disadvantages

values are only base64-encoded
not strongly protected without etcd encryption at rest
secret lifecycle management is limited
not ideal for larger production environments
HashiCorp Vault

Advantages

centralized secret management
policy-based access control
Kubernetes authentication support
sidecar injection pattern for secret delivery
better production-oriented security model

Disadvantages

more complex to install and configure
additional operational overhead
requires extra components and maintenance
When to use each approach

Use Kubernetes Secrets when:

the application is simple
the environment is small
native Kubernetes integration is sufficient

Use Vault when:

stronger security controls are needed
multiple applications need centralized secret management
policy-based access control is required
production-grade secret handling is needed
Production recommendations

For production environments:

never commit real secrets to Git
use placeholder values in Helm files
enable etcd encryption at rest
restrict access to Secrets with RBAC
prefer Vault or another external secret manager for sensitive workloads
avoid using the default service account for Vault-authenticated workloads
