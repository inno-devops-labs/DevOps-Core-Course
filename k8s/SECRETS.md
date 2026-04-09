# Lab 11 - Kubernetes Secrets & HashiCorp Vault

## 1. Kubernetes Secrets Fundamentals

### Secret creation

I created the required Kubernetes Secret with the imperative command:

```bash
kubectl create secret generic app-credentials \
  --from-literal=username=devops-admin \
  --from-literal=password=Lab11Passw0rd!
```

Output:

```text
secret/app-credentials created
```

### Viewing the Secret

`kubectl get secret app-credentials -o yaml`:

```yaml
apiVersion: v1
data:
  password: TGFiMTFQYXNzdzByZCE=
  username: ZGV2b3BzLWFkbWlu
kind: Secret
metadata:
  creationTimestamp: "2026-04-09T16:59:46Z"
  name: app-credentials
  namespace: default
type: Opaque
```

### Decoding the values

```bash
printf 'username='
kubectl get secret app-credentials -o jsonpath='{.data.username}' | base64 -d
printf '\npassword='
kubectl get secret app-credentials -o jsonpath='{.data.password}' | base64 -d
printf '\n'
```

Output:

```text
username=devops-admin
password=Lab11Passw0rd!
```

### Base64 encoding vs encryption

Base64 is only an encoding format. It makes binary-safe transport and YAML embedding easy, but it does not protect confidentiality. Anyone who can read the Secret object can decode it without a key.

Encryption is different:

- Encoding: reversible by anyone, no key required
- Encryption: ciphertext requires a key and a configured crypto system

### Are Kubernetes Secrets encrypted at rest by default?

Not by default. Kubernetes stores Secret data in etcd, and without an encryption provider configuration the values are only base64-encoded in the API object representation.

For this Minikube cluster, I checked the API server manifest:

```bash
minikube ssh -- "sudo grep -n 'encryption-provider-config' /etc/kubernetes/manifests/kube-apiserver.yaml || true"
```

This returned no output, which means the local API server is not configured with an `--encryption-provider-config` flag.

### What is etcd encryption and when should it be enabled?

etcd encryption at rest uses an `EncryptionConfiguration` so the API server encrypts selected resource types, including Secrets, before persisting them into etcd.

It should be enabled in any cluster where:

- Secrets contain real credentials or tokens
- multiple operators or platform components can reach etcd backups
- compliance or audit requirements apply
- the cluster is anything beyond a disposable learning environment

In production, I would combine:

- etcd encryption at rest
- tight RBAC on Secret access
- external secret management for high-value secrets

## 2. Helm Secret Integration

### Chart structure

The Lab 10 chart was extended with a Secret template and a dedicated ServiceAccount for Vault auth:

```text
k8s/devops-info-service/
├── Chart.yaml
├── values.yaml
├── values-dev.yaml
├── values-prod.yaml
└── templates/
    ├── _helpers.tpl
    ├── deployment.yaml
    ├── secrets.yaml
    ├── service.yaml
    ├── serviceaccount.yaml
    └── NOTES.txt
```

### Secret templating

The chart now renders a Kubernetes Secret from `values.yaml` placeholders:

```yaml
secret:
  enabled: true
  create: true
  existingSecret: ""
  name: ""
  type: Opaque
  envFrom: true
  stringData:
    APP_USERNAME: "change-me"
    APP_PASSWORD: "change-me"
```

Rendered manifest excerpt from `helm get manifest lab11-devops`:

```yaml
kind: Secret
metadata:
  name: lab11-devops-devops-info-service-secret
type: Opaque
stringData:
  APP_PASSWORD: "replace-me-in-dev"
  APP_USERNAME: "dev-user"
```

### Deployment consumption

The Deployment consumes the Secret with `envFrom` and uses the chart-created ServiceAccount:

```yaml
serviceAccountName: lab11-devops-devops-info-service
containers:
  - name: devops-info-service
    env:
      - name: PORT
        value: "5000"
    envFrom:
      - secretRef:
          name: lab11-devops-devops-info-service-secret
```

### Helm validation

```bash
helm lint k8s/devops-info-service
helm template lab11-devops k8s/devops-info-service -f k8s/devops-info-service/values-dev.yaml
helm template lab11-devops k8s/devops-info-service -f k8s/devops-info-service/values-prod.yaml
```

`helm lint` result:

```text
==> Linting k8s/devops-info-service
[INFO] Chart.yaml: icon is recommended

1 chart(s) linted, 0 chart(s) failed
```

### Deploy and verify

Install command:

```bash
helm upgrade --install lab11-devops k8s/devops-info-service \
  -f k8s/devops-info-service/values-dev.yaml \
  --wait --wait-for-jobs --timeout 5m
```

Result:

```text
NAME: lab11-devops
NAMESPACE: default
STATUS: deployed
REVISION: 1
```

Resource snapshot:

```text
NAME                                                    READY   STATUS    RESTARTS   AGE
pod/lab11-devops-devops-info-service-6dd47bd6c4-6w25v   1/1     Running   0          21s

NAME                                       TYPE       CLUSTER-IP      EXTERNAL-IP   PORT(S)        AGE
service/lab11-devops-devops-info-service   NodePort   10.97.206.173   <none>        80:30081/TCP   21s

NAME                                               READY   UP-TO-DATE   AVAILABLE   AGE
deployment.apps/lab11-devops-devops-info-service   1/1     1            1           21s

NAME                                             TYPE     DATA   AGE
secret/lab11-devops-devops-info-service-secret   Opaque   2      21s

NAME                                              AGE
serviceaccount/lab11-devops-devops-info-service   21s
```

### Environment variable verification

I verified the pod received the secret-backed environment variables without printing the actual values:

```bash
kubectl exec lab11-devops-devops-info-service-6dd47bd6c4-6w25v -- \
  sh -c 'printenv | grep "^APP_" | cut -d= -f1 | sort'
```

Output:

```text
APP_PASSWORD
APP_USERNAME
```

### Secrets are not exposed in `kubectl describe pod`

`kubectl describe pod ...` shows the Secret reference, not the values:

```text
Environment Variables from:
  lab11-devops-devops-info-service-secret  Secret  Optional: false
Environment:
  PORT:  5000
```

That is the expected behavior when using `envFrom` with a Secret.

## 3. Resource Management

### Configured requests and limits

The chart already had resource management from Lab 10, and it remains configurable in values files.

Development values:

```yaml
resources:
  requests:
    cpu: 50m
    memory: 64Mi
  limits:
    cpu: 100m
    memory: 128Mi
```

Production-style values:

```yaml
resources:
  requests:
    cpu: 150m
    memory: 192Mi
  limits:
    cpu: 500m
    memory: 512Mi
```

Live pod excerpt:

```text
Limits:
  cpu:     100m
  memory:  128Mi
Requests:
  cpu:      50m
  memory:   64Mi
```

### Requests vs limits

- Requests tell the scheduler the minimum CPU and memory the container needs.
- Limits cap how much CPU and memory the container may consume at runtime.

For this Flask service, the chosen values are intentionally small for Minikube but still realistic enough to demonstrate scheduling and capacity boundaries.

### How to choose appropriate values

For production, I would start with:

- baseline requests from normal steady-state usage
- limits from load-test peaks plus safety margin
- actual telemetry from Prometheus or platform metrics

Then I would tune based on:

- p95 and p99 latency
- CPU throttling events
- OOM kills
- startup time and probe stability

## 4. Vault Integration

### Helm repository and chart version

I added the official HashiCorp Helm repository:

```bash
helm repo add hashicorp https://helm.releases.hashicorp.com
helm repo update
```

Repository search:

```text
NAME                CHART VERSION  APP VERSION  DESCRIPTION
hashicorp/vault     0.32.0         1.21.2       Official HashiCorp Vault Chart
```

### Vault installation

Install command:

```bash
helm upgrade --install vault hashicorp/vault \
  --set server.dev.enabled=true \
  --set injector.enabled=true \
  --wait --timeout 8m
```

Result:

```text
NAME: vault
NAMESPACE: default
STATUS: deployed
REVISION: 1
```

Running pods after installation and app upgrade:

```text
lab11-devops-devops-info-service-5b7674c5cc-cnpdp   2/2     Running   0   53s
vault-0                                             1/1     Running   0   119s
vault-agent-injector-848dd747d7-wfvkg               1/1     Running   0   2m1s
```

### Vault configuration

I configured a dedicated KV v2 mount and stored application credentials:

```bash
kubectl exec vault-0 -- sh -c '
  export VAULT_ADDR=http://127.0.0.1:8200
  export VAULT_TOKEN=root
  vault secrets enable -path=apps kv-v2
  vault kv put apps/devops-info-service/config \
    username="vault-user" \
    password="vault-password"
'
```

Secret path confirmation:

```text
============ Secret Path ============
apps/data/devops-info-service/config
```

### Kubernetes auth configuration

I enabled the Kubernetes auth method and bound a role to the Helm release ServiceAccount:

```bash
kubectl exec vault-0 -- sh -c '
  export VAULT_ADDR=http://127.0.0.1:8200
  export VAULT_TOKEN=root
  vault auth enable kubernetes
  cat <<EOF >/tmp/devops-info-service-policy.hcl
path "apps/data/devops-info-service/config" {
  capabilities = ["read"]
}
EOF
  vault policy write devops-info-service /tmp/devops-info-service-policy.hcl
  vault write auth/kubernetes/config \
    token_reviewer_jwt="$(cat /var/run/secrets/kubernetes.io/serviceaccount/token)" \
    kubernetes_host="https://${KUBERNETES_SERVICE_HOST}:${KUBERNETES_SERVICE_PORT_HTTPS}" \
    kubernetes_ca_cert=@/var/run/secrets/kubernetes.io/serviceaccount/ca.crt
  vault write auth/kubernetes/role/devops-info-service \
    bound_service_account_names="lab11-devops-devops-info-service" \
    bound_service_account_namespaces="default" \
    policies="devops-info-service" \
    ttl="24h"
'
```

Policy used:

```hcl
path "apps/data/devops-info-service/config" {
  capabilities = ["read"]
}
```

Role readback:

```text
bound_service_account_names       [lab11-devops-devops-info-service]
bound_service_account_namespaces  [default]
policies                          [devops-info-service]
token_ttl                         24h
```

### Enable Vault agent injection in the chart

I upgraded the application release with Vault turned on:

```bash
helm upgrade lab11-devops k8s/devops-info-service \
  -f k8s/devops-info-service/values-dev.yaml \
  --set vault.enabled=true \
  --set vault.role=devops-info-service \
  --set vault.secretPath=apps/data/devops-info-service/config \
  --wait --wait-for-jobs --timeout 5m
```

The Deployment now renders these annotations:

```text
vault.hashicorp.com/agent-inject: true
vault.hashicorp.com/agent-inject-file-config: config.env
vault.hashicorp.com/agent-inject-secret-config: apps/data/devops-info-service/config
vault.hashicorp.com/agent-inject-status: injected
vault.hashicorp.com/agent-inject-template-config:
  {{- with secret "apps/data/devops-info-service/config" -}}
  APP_USERNAME={{ .Data.data.username }}
  APP_PASSWORD={{ .Data.data.password }}
  {{- end -}}
vault.hashicorp.com/auth-path: auth/kubernetes
vault.hashicorp.com/role: devops-info-service
vault.hashicorp.com/secret-volume-path-config: /vault/secrets
```

### Proof of sidecar injection

The new app pod came up as `2/2`, which confirms the application container plus Vault sidecar are both running:

```text
lab11-devops-devops-info-service-5b7674c5cc-cnpdp   2/2   Running
```

`kubectl describe pod` shows:

- init container: `vault-agent-init`
- sidecar container: `vault-agent`
- shared in-memory volume: `/vault/secrets`

### Proof of injected file

File path inside the application container:

```bash
kubectl exec lab11-devops-devops-info-service-5b7674c5cc-cnpdp \
  -c devops-info-service -- find /vault -maxdepth 2 -type f | sort
```

Output:

```text
/vault/secrets/config.env
```

Redacted file contents:

```bash
kubectl exec lab11-devops-devops-info-service-5b7674c5cc-cnpdp \
  -c devops-info-service -- \
  sh -c 'sed -E "s/=.*/=<redacted>/" /vault/secrets/config.env'
```

Output:

```text
APP_USERNAME=<redacted>
APP_PASSWORD=<redacted>
```

### Sidecar injection pattern explanation

The Vault injector works as a mutating admission webhook:

1. The Deployment submits a pod with Vault annotations.
2. The webhook mutates the pod spec.
3. A `vault-agent-init` container authenticates to Vault and prepares the initial rendered secrets.
4. A long-running `vault-agent` sidecar continues to manage auth/token lifecycle and template rendering.
5. The application reads the rendered secret files from a shared volume, here `/vault/secrets`.

This keeps the secret source external to the app image and avoids hardcoding credentials into Git or container layers.

## 5. Security Analysis

### Kubernetes Secrets vs Vault

| Aspect | Kubernetes Secret | Vault |
|--------|-------------------|-------|
| Storage | etcd | Vault storage backend |
| Default confidentiality | Base64 only, no at-rest encryption unless configured | Built for encrypted secret storage |
| Access control | Kubernetes RBAC | Vault policies plus auth methods |
| Rotation | Manual or controller-driven | Strong built-in support, including dynamic secrets |
| Auditability | Kubernetes audit logging | Rich secret access auditing |
| App integration | Native and simple | More moving parts, stronger security model |

### When to use each

Use Kubernetes Secrets when:

- the application is simple
- secrets are low-risk or environment-scoped
- operational complexity must stay minimal
- the cluster already has RBAC and etcd encryption configured

Use Vault when:

- credentials are high-value
- secrets need rotation
- multiple platforms or teams consume the same secrets
- audit trails matter
- dynamic short-lived credentials are desirable

### Production recommendations

For production, I would do the following:

- never commit real secret values to Git
- replace placeholder Helm values with external injection at deploy time
- enable etcd encryption at rest
- restrict `get/list/watch` access to Secrets through RBAC
- prefer Vault or another external secret manager for databases, APIs, and shared credentials
- rotate credentials regularly
- audit both Kubernetes and Vault access
- consider a reload strategy if the app must react immediately to secret file updates

## 6. Bonus - Vault Agent Templates and Named Helpers

I implemented the bonus pattern in the chart as well.

### Template annotation

The chart now renders:

```yaml
vault.hashicorp.com/agent-inject-template-config: |
  {{- with secret "apps/data/devops-info-service/config" -}}
  APP_USERNAME={{ .Data.data.username }}
  APP_PASSWORD={{ .Data.data.password }}
  {{- end -}}
```

That produces a `.env`-style file inside the pod:

```text
/vault/secrets/config.env
```

### Named helpers added to `_helpers.tpl`

I added reusable helpers for:

- `devops-info-service.envVars`
- `devops-info-service.serviceAccountName`
- `devops-info-service.secretName`
- `devops-info-service.vaultAgentTemplate`
- `devops-info-service.vaultAnnotations`

This keeps the Deployment template smaller and avoids repeating the Vault annotation block.

### Secret refresh behavior

With the sidecar enabled, Vault Agent can continue renewing auth and re-rendering templates when the underlying secret changes. The exact application behavior after a file rewrite depends on the app:

- apps that read the file on every use see the change naturally
- apps that cache values in memory need a reload mechanism

If needed, `vault.hashicorp.com/agent-inject-command` can trigger a command after re-rendering, for example sending a reload signal or touching a watched file.

## 7. Summary

Lab 11 is complete with:

- imperative Secret creation and decoding
- Helm-managed Secret templating
- Secret injection into the application pod
- resource requests and limits preserved in the chart
- HashiCorp Vault installed in dev mode
- KV v2, policy, Kubernetes auth, and role configured
- Vault Agent injection working with rendered secret files
- bonus helper templates and Vault Agent templating implemented
