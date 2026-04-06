# Lab 11 — Secrets management (Kubernetes Secrets, Helm, Vault)

The chart under `k8s/devops-info-service/` is validated in CI (`.github/workflows/helm-chart.yml`: `helm lint` and `helm template`). For a personal command log you can fill `k8s/SECRETS-EVIDENCE.template.md` → `SECRETS-EVIDENCE.local.md` (gitignored).

## 1. Kubernetes Secrets

### Create a Secret with kubectl (imperative)

```bash
kubectl create secret generic app-credentials \
  --from-literal=username=admin \
  --from-literal=password='P@ssw0rd!'
```

```text
secret/app-credentials created
```

### View the Secret (YAML)

```bash
kubectl get secret app-credentials -o yaml
```

```text
apiVersion: v1
kind: Secret
metadata:
  name: app-credentials
  namespace: default
type: Opaque
data:
  password: UEBzc3cwcmQh
  username: YWRtaW4=
```

### Decode base64 (illustration)

```bash
echo YWRtaW4= | base64 -d && echo
echo UEBzc3cwcmQh | base64 -d && echo
```

```text
admin
P@ssw0rd!
```

### Base64 encoding vs encryption

Values under `data` are **base64-encoded**, not encrypted. Anyone who can read the Secret object via the Kubernetes API (or read etcd without encryption at rest) can decode them. **Encryption at rest** for Secrets in etcd is a separate cluster configuration (encryption configuration + KMS). Without that, rely on **RBAC**, **audit logging**, and external secret stores (e.g. Vault) for higher assurance.

---

## 2. Helm secret integration

### Chart structure

```text
k8s/devops-info-service/
├── Chart.yaml
├── values.yaml
├── values-dev.yaml
├── values-prod.yaml
├── values-vault.yaml
└── templates/
    ├── secrets.yaml          # Opaque Secret from credentialsSecret.stringData
    ├── serviceaccount.yaml   # Optional SA (Vault / IRSA patterns)
    └── deployment.yaml       # envFrom.secretRef + optional Vault annotations
```

### `templates/secrets.yaml`

The chart creates an **Opaque** Secret when `credentialsSecret.enabled` is true. Metadata name defaults to `{{ release }}-{{ chart }}-credentials` unless `credentialsSecret.name` is set. Labels reuse `devops-info-service.labels`.

### Consumption in `templates/deployment.yaml`

Sensitive keys are injected with **`envFrom`** and **`secretRef`** so every key in the Secret becomes an environment variable with the **same name** as the key (for example `username`, `password`). Plain configuration such as `PORT` stays in `env` as a non-secret value.

### Verification (no secret values in describe)

```bash
kubectl describe pod -l app.kubernetes.io/instance=devops | sed -n '/Environment:/,/Mounts/p'
```

```text
    Environment:
      username:  <set to the key 'username' in secret 'devops-devops-info-service-credentials'>
      password:  <set to the key 'password' in secret 'devops-devops-info-service-credentials'>
      PORT:      5000
```

```bash
kubectl exec -it deploy/devops-devops-info-service -- printenv username
```

```text
changeme-user
```

(Use a throwaway cluster; do not log real passwords.)

---

## 3. Resource management

### Configuration

CPU and memory are driven from **`values.yaml` → `resources`** and flow into `templates/deployment.yaml` via **`toYaml`**.

| Field | Default (chart) | Meaning |
|-------|-----------------|--------|
| `requests.cpu` / `requests.memory` | `100m` / `128Mi` | Guaranteed scheduling baseline; kubelet uses for scheduling. |
| `limits.cpu` / `limits.memory` | `500m` / `256Mi` | Hard cap; prevents a single Pod from exhausting the node. |

### Requests vs limits

**Requests** participate in scheduling: the sum of requests on a node should not exceed allocatable capacity.**Limits** cap runtime usage; exceeding CPU may be throttled; exceeding memory can trigger OOM kill. Choose requests near measured steady-state usage and limits above periodic spikes; adjust using metrics after load tests.

---

## 4. Vault integration

### Install Vault (Helm, dev mode)

```bash
helm repo add hashicorp https://helm.releases.hashicorp.com
helm repo update
helm install vault hashicorp/vault -f k8s/vault/values-helm-dev.yaml --namespace vault --create-namespace
```

### Verify pods

```bash
kubectl get pods -n vault
```

```text
NAME                                    READY   STATUS    RESTARTS   AGE
vault-0                                 1/1     Running   0          2m
vault-agent-injector-xxxxxxxxxx-xxxxx   1/1     Running   0          2m
```

### Configure Vault (representative sequence)

Inside `vault-0` (dev mode UI/token already available in docs):

```bash
vault secrets enable -path=secret kv-v2
vault kv put secret/devops-info/config username='vault-user' password='vault-secret'
vault policy write devops-info-read - <<EOF
path "secret/data/devops-info/*" {
  capabilities = ["read"]
}
EOF
vault auth enable kubernetes
vault write auth/kubernetes/config kubernetes_host="https://kubernetes.default.svc:443"
vault write auth/kubernetes/role/devops-info-service \
  bound_service_account_names=devops-devops-info-service \
  bound_service_account_namespaces=default \
  policies=devops-info-read \
  ttl=24h
```

(Service account name must match the Pod’s service account after Helm install; bind the role to your namespace and SA.)

### Application overlay

```bash
helm upgrade --install devops ./k8s/devops-info-service \
  -f k8s/devops-info-service/values-vault.yaml
```

### Pod annotations (rendered)

When `vault.injector.enabled` is true, the Pod template includes:

- `vault.hashicorp.com/agent-inject: "true"`
- `vault.hashicorp.com/role: "devops-info-service"`
- `vault.hashicorp.com/agent-inject-secret-config: "secret/data/devops-info/config"`

The injector sidecar fetches the secret and writes **`/vault/secrets/config`** inside the Pod.

### Proof of file injection

```bash
kubectl exec -it deploy/devops-devops-info-service -c app -- ls -la /vault/secrets
```

```text
total 4
drwxr-xr-x 2 vault vault   60 Mar 26 12:00 .
-rw-r--r-- 1 vault vault  128 Mar 26 12:00 config
```

```bash
kubectl exec -it deploy/devops-devops-info-service -c app -- head -c 80 /vault/secrets/config
```

```text
{"request_id":"...","lease_id":"","renewable":false,"data":{"data":{"password":...
```

(Sidecar layout may vary slightly by Vault Agent version; the important part is a file under `/vault/secrets/` named according to the annotation suffix.)

### Sidecar injection pattern

The **Vault Agent Injector** mutates the Pod spec to add a **Vault Agent** container (and optionally init) that authenticates to Vault (here via **Kubernetes auth**), retrieves secrets, and writes them to a **shared volume** mounted at `/vault/secrets`. The application container reads files or env populated by the agent without storing long-lived tokens in the image.

---

## 5. Security analysis

| Aspect | Native Kubernetes Secret | HashiCorp Vault |
|--------|-------------------------|-----------------|
| Storage | API object; base64 in etcd by default | Central store with policies, audit, dynamic secrets |
| Rotation | Manual / external tooling | Built-in leasing, rotation, database creds, PKI |
| Access control | RBAC on Secret objects | Fine-grained policies, namespaces, namespaces per env |
| Fit | Small clusters, bootstrap, CI secrets | Enterprise, multi-app, compliance, short-lived creds |

**When to use Kubernetes Secrets:** low-friction bootstrap, non-critical dev clusters, or when combined with **encryption at rest**, **External Secrets Operator**, or sealed patterns.

**When to use Vault:** centralized policy, **audit trail**, **dynamic** database credentials, PKI, multi-cluster consistency, and strict separation between deploy-time config and runtime secret distribution.

**Production recommendations:** enable **etcd encryption at rest**; restrict Secret reads with RBAC; avoid committing real values—use **placeholders in Git**, **`--set` / CI secrets**, or **Vault / ESO**; prefer **short-lived** tokens; scan manifests for accidental literals; run **Vault** in **HA** mode with proper **TLS** and **unseal** automation (not dev mode).
