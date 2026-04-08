# Lab 11 — Kubernetes Secrets & HashiCorp Vault

## 1. Kubernetes Secrets

### Create a secret with kubectl

```bash
kubectl create secret generic app-credentials \
  --from-literal=username=dev-user \
  --from-literal=password=dev-password
```

### View secret in YAML

```bash
kubectl get secret app-credentials -o yaml
```

Example:

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: app-credentials
type: Opaque
data:
  username: ZGV2LXVzZXI=
  password: ZGV2LXBhc3N3b3Jk
```

### Decode base64 values

```bash
echo "ZGV2LXVzZXI=" | base64 -d
echo "ZGV2LXBhc3N3b3Jk" | base64 -d
```

Decoded:

```text
username = dev-user
password = dev-password
```

### Encoding vs encryption

Kubernetes Secret values are base64-encoded.  
Base64 is **encoding**, not encryption.

### Security implications

Kubernetes Secrets are not strongly protected just because they are stored as Secret objects.  
For production:
- enable **etcd encryption at rest**
- restrict access with **RBAC**
- do not commit real secrets to Git
- prefer an external secret manager for sensitive workloads

### What is etcd encryption

Kubernetes stores cluster state in **etcd**.  
If encryption at rest is enabled, secret values are encrypted before being stored in etcd.

---

## 2. Helm Secret Integration

### Chart structure

```text
k8s/python-app/
├── values.yaml
├── values-dev.yaml
├── values-prod.yaml
├── values-vault.yaml
└── templates/
    ├── _helpers.tpl
    ├── deployment.yaml
    ├── secrets.yaml
    ├── service.yaml
    └── serviceaccount.yaml
```

### Secret template

`templates/secrets.yaml` was added:

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: {{ include "python-app.secretName" . }}
  labels:
    {{- include "python-app.labels" . | nindent 4 }}
type: Opaque
stringData:
  APP_USERNAME: {{ .Values.secrets.data.APP_USERNAME | quote }}
  APP_PASSWORD: {{ .Values.secrets.data.APP_PASSWORD | quote }}
```

### Secret values in Helm

`values.yaml` contains placeholders:

```yaml
secrets:
  create: true
  name: ""
  data:
    APP_USERNAME: "change-me"
    APP_PASSWORD: "change-me"
```

### Secret consumption in Deployment

The Deployment consumes the Secret with `envFrom.secretRef`:

```yaml
envFrom:
  - secretRef:
      name: {{ include "python-app.secretName" . }}
```

### ServiceAccount

A dedicated ServiceAccount was added for Vault authentication:

```yaml
serviceAccount:
  create: true
  name: ""
```

---

## 3. Verification of Helm Secret Injection

### Deploy chart

```bash
helm lint k8s/python-app
helm template python-app-dev k8s/python-app -f k8s/python-app/values-dev.yaml
helm upgrade --install python-app-dev k8s/python-app -f k8s/python-app/values-dev.yaml
```

### Verify pods, secrets, and service account

```bash
kubectl get pods
kubectl get secrets
kubectl get sa
```

Observed output:

```text
NAME                              READY   STATUS    RESTARTS   AGE
python-app-dev-7568dc97b6-6b4kw   1/1     Running   0          31s

NAME                    TYPE     DATA   AGE
python-app-dev-secret   Opaque   2      14s

NAME             AGE
default          14d
python-app-dev   14s
```

### Verify environment variables in pod

```bash
kubectl exec -it python-app-dev-7568dc97b6-6b4kw -- env | grep -E '^(APP_NAME|APP_VERSION|APP_DESCRIPTION|APP_USERNAME|APP_PASSWORD)='
```

Observed output:

```text
APP_DESCRIPTION=DevOps course info service
APP_USERNAME=dev-user
APP_PASSWORD=dev-password
APP_NAME=python-app
APP_VERSION=lab11-dev
```

### Verify pod description

```bash
kubectl describe pod python-app-dev-7568dc97b6-6b4kw
```

Relevant fragments:

```text
Service Account:  python-app-dev

Environment Variables from:
  python-app-dev-secret  Secret  Optional: false

Environment:
  APP_NAME:         python-app
  APP_VERSION:      lab11-dev
  APP_DESCRIPTION:  DevOps course info service
```

This confirms:
- Secret is injected into the pod
- ServiceAccount is used
- secret values are not shown directly in `kubectl describe pod`

---

## 4. Resource Management

Configured in Deployment:

```yaml
resources:
  requests:
    cpu: 50m
    memory: 64Mi
  limits:
    cpu: 100m
    memory: 128Mi
```

Observed in pod:

```text
Limits:
  cpu:     100m
  memory:  128Mi
Requests:
  cpu:      50m
  memory:   64Mi
```

### Requests vs limits

- **Requests**: minimum resources reserved for the container
- **Limits**: maximum resources the container can use

These values are appropriate for a lightweight FastAPI development workload.

---

## 5. Vault Installation

### Install Vault via Helm

```bash
helm repo add hashicorp https://helm.releases.hashicorp.com
helm repo update
helm install vault hashicorp/vault \
  --set="server.dev.enabled=true" \
  --set="injector.enabled=true"
```

### Verify Vault pods

```bash
kubectl get pods
```

Observed relevant output:

```text
vault-0                                 1/1     Running   0   4m52s
vault-agent-injector-848dd747d7-h2pmn   1/1     Running   0   4m53s
```

### Vault status

Inside `vault-0`:

```bash
kubectl exec -it vault-0 -- sh
export VAULT_ADDR='http://127.0.0.1:8200'
export VAULT_TOKEN='root'
vault status
```

Observed output:

```text
Seal Type       shamir
Initialized     true
Sealed          false
Version         1.21.2
Storage Type    inmem
HA Enabled      false
```

---

## 6. Vault Configuration

### Store secret in Vault

```bash
vault kv put secret/myapp/config username='vault-user' password='vault-password'
vault kv get secret/myapp/config
```

Observed output:

```text
====== Data ======
Key         Value
---         -----
password    vault-password
username    vault-user
```

### Enable Kubernetes auth

```bash
vault auth enable kubernetes
vault write auth/kubernetes/config \
  kubernetes_host="https://$KUBERNETES_PORT_443_TCP_ADDR:443"
```

### Create policy

Policy file:

```hcl
path "secret/data/myapp/config" {
  capabilities = ["read"]
}
```

Commands:

```bash
vault policy write python-app-policy /tmp/python-app-policy.hcl
vault policy read python-app-policy
```

Observed output:

```text
path "secret/data/myapp/config" {
  capabilities = ["read"]
}
```

### Create role

```bash
vault write auth/kubernetes/role/python-app-role \
  bound_service_account_names=python-app-dev \
  bound_service_account_namespaces=default \
  policies=python-app-policy \
  ttl=24h
```

Role was created successfully. Vault returned a non-blocking warning about missing audience.

---

## 7. Vault Agent Injection

### Enable injection in Helm

```bash
helm upgrade --install python-app-dev k8s/python-app \
  -f k8s/python-app/values-dev.yaml \
  -f k8s/python-app/values-vault.yaml
```

### Verify mutated pod

```bash
kubectl get pods -l app.kubernetes.io/instance=python-app-dev
```

Observed output:

```text
NAME                              READY   STATUS    RESTARTS   AGE
python-app-dev-55b678d7ff-z4cdt   2/2     Running   0          21s
```

The pod changed from `1/1` to `2/2`, which confirms sidecar injection.

### Verify pod annotations and injected containers

```bash
kubectl describe pod python-app-dev-55b678d7ff-z4cdt
```

Relevant fragments:

```text
Annotations:
  vault.hashicorp.com/agent-inject: true
  vault.hashicorp.com/agent-inject-secret-config: secret/data/myapp/config
  vault.hashicorp.com/agent-inject-status: injected
  vault.hashicorp.com/role: python-app-role
```

Observed injected components:
- `vault-agent-init`
- `vault-agent`
- mounted volume `/vault/secrets`

### Verify secret file inside pod

```bash
kubectl exec -it python-app-dev-55b678d7ff-z4cdt -- ls -R /vault/secrets
kubectl exec -it python-app-dev-55b678d7ff-z4cdt -- cat /vault/secrets/config
```

Observed output:

```text
/vault/secrets:
config
```

File contents:

```text
data: map[password:vault-password username:vault-user]
metadata: map[created_time:2026-04-08T12:52:35.575852137Z custom_metadata:<nil> deletion_time: destroyed:false version:1]
```

This confirms that Vault injected the secret into the pod filesystem at the expected path.

---

## 8. Sidecar Injection Pattern

Vault Agent Injector uses a mutating admission webhook.

In this lab:
1. The pod was created with Vault annotations.
2. The injector added:
   - `vault-agent-init`
   - `vault-agent`
   - shared volume `/vault/secrets`
3. Vault Agent authenticated using the pod ServiceAccount.
4. The secret was fetched from Vault and rendered into a file inside the pod.

---

## 9. Security Analysis

### Kubernetes Secrets

**Pros**
- simple and built into Kubernetes
- easy to use with Helm
- good for small internal deployments

**Cons**
- backed by etcd
- require RBAC and encryption at rest for stronger protection
- limited compared to external secret managers

### Vault

**Pros**
- centralized secret management
- fine-grained access control
- Kubernetes authentication support
- sidecar-based secret delivery
- better suited for production-grade secret workflows

**Cons**
- more operational complexity
- additional installation and configuration required

### When to use

Use **Kubernetes Secrets** for simple internal deployments.

Use **Vault** when stronger security, centralized control, and better secret management are required.

### Production recommendations

- never commit real secrets to Git
- use placeholder values in Helm charts
- enable etcd encryption at rest
- limit access with RBAC
- use an external secret manager such as Vault for sensitive workloads

---

## 10. Conclusion

Implemented in this lab:
- Kubernetes Secret creation and decoding
- Helm-managed Secret template
- Secret injection into the application as environment variables
- resource requests and limits
- Vault installation via Helm
- KV secret creation in Vault
- Kubernetes auth, policy, and role configuration
- Vault Agent sidecar injection
- secret delivery into the pod as a file

This satisfies the Lab 11 requirements for Kubernetes Secrets, Helm-managed secrets, Vault integration, and documentation
