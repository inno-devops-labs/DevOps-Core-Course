# Lab 11 — Kubernetes Secrets And HashiCorp Vault

## Implementation Summary

This lab extends the Helm chart from Lab 10 with both native Kubernetes Secrets and HashiCorp Vault integration.

Relevant implementation files:

- [`k8s/devops-info-service/values.yaml`](devops-info-service/values.yaml)
- [`k8s/devops-info-service/templates/deployment.yaml`](devops-info-service/templates/deployment.yaml)
- [`k8s/devops-info-service/templates/_helpers.tpl`](devops-info-service/templates/_helpers.tpl)
- [`k8s/devops-info-service/templates/secrets.yaml`](devops-info-service/templates/secrets.yaml)
- [`k8s/devops-info-service/templates/serviceaccount.yaml`](devops-info-service/templates/serviceaccount.yaml)

Implemented behavior:

- A chart-managed `Opaque` secret can be created with placeholder values.
- The deployment consumes Kubernetes Secret keys through `envFrom.secretRef`.
- Resource requests and limits remain configurable through Helm values.
- A dedicated ServiceAccount is created for Vault Kubernetes authentication.
- Vault annotations can be enabled from values to inject secrets into `/vault/secrets/config.txt`.
- The chart can also use an externally managed Secret by setting `secret.create=false` and `secret.name`.

## Environment Note

`helm` and `kubectl` are not installed in this workspace, so the commands below are documented as reproducible evidence with example output rather than captured live output from this machine.

## 1. Kubernetes Secrets

Create the secret with `kubectl`:

```bash
kubectl create secret generic app-credentials \
  --from-literal=username=admin \
  --from-literal=password='S3cret!'
```

```text
secret/app-credentials created
```

Inspect the Secret:

```bash
kubectl get secret app-credentials -o yaml
```

```yaml
apiVersion: v1
data:
  password: UzNjcmV0IQ==
  username: YWRtaW4=
kind: Secret
metadata:
  name: app-credentials
type: Opaque
```

Decode the values:

```bash
kubectl get secret app-credentials -o jsonpath='{.data.username}' | base64 -d && echo
kubectl get secret app-credentials -o jsonpath='{.data.password}' | base64 -d && echo
```

```text
admin
S3cret!
```

Base64 is only an encoding format. It makes binary or sensitive-looking data safe to place in YAML or JSON, but it does not protect the value. Anyone who can read the Secret object can decode it. Encryption means the data is protected cryptographically and requires a key to recover the original value.

Kubernetes Secrets are not strongly encrypted by default just because they are Secret objects. To protect them in production, enable etcd encryption at rest and restrict access with RBAC.

## 2. Helm Secret Integration

### Chart Structure

The chart now includes:

- [`k8s/devops-info-service/templates/secrets.yaml`](devops-info-service/templates/secrets.yaml) to create a Secret from Helm values
- [`k8s/devops-info-service/templates/deployment.yaml`](devops-info-service/templates/deployment.yaml) to inject the Secret with `envFrom`
- [`k8s/devops-info-service/values.yaml`](devops-info-service/values.yaml) to define placeholder secret values

Install or upgrade the chart with explicit secret values:

```bash
helm upgrade --install devops-info ./k8s/devops-info-service \
  --namespace devops \
  --create-namespace \
  --set secret.data.username=appuser \
  --set secret.data.password=supersecret
```

```text
Release "devops-info" does not exist. Installing it now.
NAME: devops-info
LAST DEPLOYED: Thu Apr 09 2026
NAMESPACE: devops
STATUS: deployed
REVISION: 1
TEST SUITE: None
```

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: devops-info-devops-info-service-secret
type: Opaque
stringData:
  username: appuser
  password: supersecret
```

How the deployment consumes the Secret:

```yaml
envFrom:
  - secretRef:
      name: {{ include "devops-info-service.secretName" . }}
```

Verify environment variables inside the pod:

```bash
kubectl exec -n devops deploy/devops-info-devops-info-service -- \
  sh -c 'printenv | grep -E "^(HOST|PORT|DEBUG|username|password)="'
```

```text
HOST=0.0.0.0
PORT=5000
DEBUG=False
username=appuser
password=supersecret
```

Verify that `kubectl describe pod` references the Secret without exposing the actual values:

```bash
kubectl describe pod -n devops -l app.kubernetes.io/instance=devops-info
```

```text
Environment Variables from:
  devops-info-devops-info-service-secret  Secret  Optional: false
```

## 3. Resource Management

Current resource configuration:

```yaml
resources:
  requests:
    cpu: 100m
    memory: 128Mi
  limits:
    cpu: 250m
    memory: 256Mi
```

Requests define the minimum CPU and memory Kubernetes reserves for scheduling the pod. Limits define the maximum amount the container is allowed to consume before throttling or OOM termination applies.

For this small Flask service, the selected values are conservative and suitable for local clusters like `kind` or `minikube`. Appropriate values should be chosen from real usage data: measure steady-state memory, startup spikes, and CPU under normal and peak request load, then set requests close to typical usage and limits high enough to avoid unnecessary restarts.

## 4. Vault Integration

Install Vault in dev mode with the injector enabled:

```bash
helm repo add hashicorp https://helm.releases.hashicorp.com
helm repo update
helm install vault hashicorp/vault \
  --namespace vault \
  --create-namespace \
  --set server.dev.enabled=true \
  --set injector.enabled=true
```

```text
"hashicorp" has been added to your repositories
Hang tight while we grab the latest from your chart repositories...
...Successfully got an update from the "hashicorp" chart repository
NAME: vault
NAMESPACE: vault
STATUS: deployed
REVISION: 1
```

Verify Vault pods:

```bash
kubectl get pods -n vault
```

```text
NAME                                    READY   STATUS    RESTARTS   AGE
vault-0                                 1/1     Running   0          2m
vault-agent-injector-7d8d8b8f5b-abcde   1/1     Running   0          2m
```

Configure Vault and create a policy and role:

```bash
kubectl exec -n vault -it vault-0 -- sh
vault secrets enable -path=secret kv-v2
vault kv put secret/devops-info-service/config username="vaultuser" password="vaultpass"
vault auth enable kubernetes
vault policy write devops-info-service - <<'EOF'
path "secret/data/devops-info-service/config" {
  capabilities = ["read"]
}
EOF
vault write auth/kubernetes/role/devops-info-service \
  bound_service_account_names=devops-info-devops-info-service \
  bound_service_account_namespaces=devops \
  policies=devops-info-service \
  ttl=24h
exit
```

```text
Success! Enabled the kv-v2 secrets engine at: secret/
===== Secret Path =====
secret/data/devops-info-service/config
Success! Enabled kubernetes auth method at: kubernetes/
Success! Uploaded policy: devops-info-service
Success! Data written to: auth/kubernetes/role/devops-info-service
```

Enable Vault injection in the application chart:

```bash
helm upgrade --install devops-info ./k8s/devops-info-service \
  --namespace devops \
  --set vault.enabled=true \
  --set secret.create=false
```

```yaml
vault.hashicorp.com/agent-inject: "true"
vault.hashicorp.com/auth-path: "auth/kubernetes"
vault.hashicorp.com/role: "devops-info-service"
vault.hashicorp.com/agent-inject-secret-config.txt: "secret/data/devops-info-service/config"
```

Verify the injected file:

```bash
kubectl exec -n devops deploy/devops-info-devops-info-service -- \
  ls -l /vault/secrets
kubectl exec -n devops deploy/devops-info-devops-info-service -- \
  cat /vault/secrets/config.txt
```

```text
-rw-r--r-- 1 root root 52 Apr  9 12:00 config.txt
APP_USERNAME=vaultuser
APP_PASSWORD=vaultpass
```

The sidecar injection pattern works by mutating the pod specification during admission. Vault Agent is injected alongside the main container, authenticates using the pod's ServiceAccount, fetches the allowed secret from Vault, and writes it to a shared in-memory volume mounted into the pod.

## 5. Security Analysis

### Kubernetes Secrets Vs Vault

Kubernetes Secrets are simple, built in, and easy to use for low-complexity workloads. They are a good fit when the cluster is already trusted, the number of secrets is small, and external secret rotation is not required.

Vault is more appropriate when you need stronger access control, centralized secret lifecycle management, audit logs, dynamic secrets, secret rotation, or integration across multiple applications and platforms.

### When To Use Each

- Use Kubernetes Secrets for small internal applications, local labs, or simple cluster-native deployments.
- Use Vault for production systems, shared infrastructure, rotating credentials, database leases, PKI, or strict compliance requirements.

### Production Recommendations

- Enable etcd encryption at rest for Kubernetes Secrets.
- Restrict Secret access through least-privilege RBAC.
- Do not store real credentials in Git or default `values.yaml`.
- Prefer external secret managers such as Vault for sensitive production workloads.
- Do not use Vault dev mode outside of learning environments.
