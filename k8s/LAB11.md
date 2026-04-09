# Lab 11 — Kubernetes Secrets & HashiCorp Vault

## 1. Kubernetes Secrets

### 1.1 Creating a Secret via kubectl

```bash
kubectl create secret generic app-credentials \
  --from-literal=username=admin \
  --from-literal=password=secret123
```

Output:
```
# secret/app-credentials created
```

### 1.2 Viewing the Secret

```bash
kubectl get secret app-credentials -o yaml
```

Output:
```yaml
apiVersion: v1
data:
  password: c2VjcmV0MTIz
  username: YWRtaW4=
kind: Secret
metadata:
  creationTimestamp: "2026-04-09T13:12:39Z"
  name: app-credentials
  namespace: default
  resourceVersion: "745"
  uid: f57b7fda-7df6-454b-8182-4012f5bc2f10
type: Opaque
```

### 1.3 Decoding base64 Values

```bash
echo "YWRtaW4=" | base64 -d   # → admin
echo "c2VjcmV0MTIz" | base64 -d  # → secret123
```

Output:
```
(.venv) (base) arinazimina@arino4ka DevOps-Core-Course % echo "YWRtaW4=" | base64 -d
admin%                                                                                                
(.venv) (base) arinazimina@arino4ka DevOps-Core-Course % echo "c2VjcmV0MTIz" | base64 -d
secret123%  
```

### 1.4 Base64 Encoding vs Encryption

**Base64 encoding** is NOT encryption. It is a reversible text transformation that converts binary data to ASCII characters. Anyone with access to the Kubernetes API can decode a Secret's values instantly:

```bash
kubectl get secret app-credentials -o jsonpath='{.data.password}' | base64 -d
```

Output:
```
secret123%  
```

**Kubernetes Secrets are NOT encrypted by default.** Values are stored as plaintext in etcd (the cluster's key-value store). This means:
- Any user with `kubectl get secret` RBAC permission can read the values
- etcd backups contain raw secret data
- etcd traffic may expose secrets if not encrypted in transit

**etcd encryption at rest** is an optional Kubernetes feature that encrypts Secret data before writing to etcd using AES-CBC or AES-GCM. It should be enabled in production clusters via the `EncryptionConfiguration` API server flag. Even with etcd encryption, secrets are decrypted when served through the API — so RBAC restrictions remain essential.

**Production recommendations:**
- Enable etcd encryption at rest
- Apply tight RBAC (principle of least privilege)
- Use an external secret manager (HashiCorp Vault, AWS Secrets Manager, etc.)
- Audit secret access with Kubernetes audit logs

---

## 2. Helm Secret Integration

### 2.1 Chart Structure

```
devops-python-chart/
├── Chart.yaml
├── values.yaml               ← secret.username / secret.password placeholders
├── templates/
│   ├── _helpers.tpl          ← envVars named template (bonus DRY pattern)
│   ├── deployment.yaml       ← envFrom + vault annotations
│   ├── secrets.yaml          ← Secret resource (NEW in Lab 11)
│   ├── service.yaml
│   └── ingress.yaml
```

### 2.2 secrets.yaml Template

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: {{ include "devops-python-chart.fullname" . }}-secret
  labels:
    {{- include "devops-python-chart.labels" . | nindent 4 }}
type: Opaque
stringData:
  username: {{ .Values.secret.username | quote }}
  password: {{ .Values.secret.password | quote }}
```

`stringData` is used so that plain-text values can be written directly in templates — Kubernetes automatically base64-encodes them before storage.

### 2.3 Consuming Secrets in Deployment

The Deployment uses `envFrom` with `secretRef` to inject all Secret keys as environment variables:

```yaml
envFrom:
  - secretRef:
      name: {{ include "devops-python-chart.fullname" . }}-secret
```

This means every key in the Secret (`username`, `password`) becomes an environment variable inside the container.

### 2.4 Deploy and Verify

```bash
# Deploy with real secret values via --set (never commit real values!)
helm upgrade --install devops-python ./k8s/devops-python-chart \
  --set secret.username=admin \
  --set secret.password=mysecretpass

# Get pod name
kubectl get pods

# Verify env vars are injected
kubectl exec -it <pod-name> -- env | grep -iE "username|password"
```

Output (env vars in pod):
```
password=mysecretpass
username=admin
```

### 2.5 Secret Values NOT Visible in kubectl describe

```bash
kubectl describe pod <pod-name>
```

Output excerpt:
```
Name:             devops-python-devops-python-chart-5d5759f5b6-64dmk
Namespace:        default
Priority:         0
Service Account:  default
Node:             minikube/192.168.49.2
Start Time:       Thu, 09 Apr 2026 16:25:52 +0300
Labels:           app.kubernetes.io/instance=devops-python
                  app.kubernetes.io/name=devops-python-chart
                  pod-template-hash=5d5759f5b6
Annotations:      <none>
Status:           Running
IP:               10.244.0.10
IPs:
  IP:           10.244.0.10
Controlled By:  ReplicaSet/devops-python-devops-python-chart-5d5759f5b6
Containers:
  devops-python-chart:
    Container ID:   docker://8dff8a5a148d18962852677243efe7e940ce77b7e2d206095df0eb1f1f861ae4
    Image:          mirana18/devops-info-service:latest
    Image ID:       docker://sha256:be29d83d5dcf91ed1dd273f47832a7dddcd9e0d326b4f982b187cf7ca915623b
    Port:           5001/TCP (http)
    Host Port:      0/TCP (http)
    State:          Running
      Started:      Thu, 09 Apr 2026 16:25:53 +0300
    Ready:          True
    Restart Count:  0
    Limits:
      cpu:     200m
      memory:  256Mi
    Requests:
      cpu:      100m
      memory:   128Mi
    Liveness:   http-get http://:5001/health delay=10s timeout=1s period=10s #success=1 #failure=3
    Readiness:  http-get http://:5001/health delay=5s timeout=1s period=5s #success=1 #failure=3
    Environment Variables from:
      devops-python-devops-python-chart-secret  Secret  Optional: false
    Environment:
      PORT:   5001
      HOST:   0.0.0.0
      DEBUG:  False
    Mounts:
      /var/run/secrets/kubernetes.io/serviceaccount from kube-api-access-hhb5m (ro)
Conditions:
  Type                        Status
  PodReadyToStartContainers   True 
  Initialized                 True 
  Ready                       True 
  ContainersReady             True 
  PodScheduled                True 
Volumes:
  kube-api-access-hhb5m:
    Type:                    Projected (a volume that contains injected data from multiple sources)
    TokenExpirationSeconds:  3607
    ConfigMapName:           kube-root-ca.crt
    Optional:                false
    DownwardAPI:             true
QoS Class:                   Burstable
Node-Selectors:              <none>
Tolerations:                 node.kubernetes.io/not-ready:NoExecute op=Exists for 300s
                             node.kubernetes.io/unreachable:NoExecute op=Exists for 300s
Events:
  Type    Reason     Age    From               Message
  ----    ------     ----   ----               -------
  Normal  Scheduled  9m56s  default-scheduler  Successfully assigned default/devops-python-devops-python-chart-5d5759f5b6-64dmk to minikube
  Normal  Pulled     9m55s  kubelet            spec.containers{devops-python-chart}: Container image "mirana18/devops-info-service:latest" already present on machine and can be accessed by the pod
  Normal  Created    9m55s  kubelet            spec.containers{devops-python-chart}: Container created
  Normal  Started    9m55s  kubelet            spec.containers{devops-python-chart}: Container started
```

---

## 3. Resource Management

### 3.1 Resource Limits Configuration

Defined in `values.yaml` and applied in `deployment.yaml` via `{{- toYaml .Values.resources | nindent 12 }}`:

```yaml
resources:
  requests:
    cpu: "100m"
    memory: "128Mi"
  limits:
    cpu: "200m"
    memory: "256Mi"
```

### 3.2 Requests vs Limits

| | Requests | Limits |
|---|---|---|
| **Purpose** | Minimum guaranteed resources | Maximum allowed resources |
| **Scheduling** | Kubernetes uses this to decide which node to place the pod on | Not used for scheduling |
| **Enforcement** | Node won't be chosen if it can't satisfy requests | Container is throttled (CPU) or OOM-killed (memory) if exceeded |

**CPU:** expressed in millicores (`100m` = 0.1 CPU core). Going over the limit causes CPU throttling — the container slows down but is not killed.

**Memory:** expressed in bytes with SI suffixes (`128Mi` = 128 mebibytes). Going over the limit causes the container to be OOM-killed and restarted.

### 3.3 Choosing Appropriate Values

1. **Start with no limits** and monitor actual usage with `kubectl top pods`
2. Set **requests** to the typical ("P50") usage — this is what the scheduler relies on
3. Set **limits** to the peak ("P99") usage plus a small buffer
4. For production workloads use separate `values-dev.yaml` / `values-prod.yaml` with different sizes (already configured in this chart)

---

## 4. Vault Integration

### 4.1 Install Vault via Helm

```bash
helm repo add hashicorp https://helm.releases.hashicorp.com
helm repo update

helm install vault hashicorp/vault \
  --set "server.dev.enabled=true" \
  --set "injector.enabled=true"
```

Verify all pods are running:

```bash
kubectl get pods
```

Output:
```
NAME                                                 READY   STATUS    RESTARTS   AGE
devops-python-devops-python-chart-5d5759f5b6-64dmk   1/1     Running   0          12m
devops-python-devops-python-chart-5d5759f5b6-6tpv6   1/1     Running   0          12m
devops-python-devops-python-chart-5d5759f5b6-q8tqj   1/1     Running   0          12m
vault-0                                              1/1     Running   0          8m58s
vault-agent-injector-848dd747d7-zmnzt                1/1     Running   0          9m
```

### 4.2 Configure Vault (exec into vault-0)

```bash
kubectl exec -it vault-0 -- /bin/sh
```

Inside the pod, run:

```bash
# Enable KV v2 secrets engine
vault secrets enable -path=secret kv-v2

# Store application secrets
vault kv put secret/myapp/config \
  username="admin" \
  password="secret123"

# Verify
vault kv get secret/myapp/config
```

Output:
```
====== Secret Path ======
secret/data/myapp/config

======= Metadata =======
Key                Value
---                -----
created_time       2026-04-09T13:31:48.921763215Z
custom_metadata    <nil>
deletion_time      n/a
destroyed          false
version            1

====== Data ======
Key         Value
---         -----
password    secret123
username    admin
```

### 4.3 Configure Kubernetes Authentication

Still inside vault-0:

```bash
# Enable Kubernetes auth method
vault auth enable kubernetes

# Configure it to talk to the cluster
vault write auth/kubernetes/config \
  kubernetes_host="https://$KUBERNETES_PORT_443_TCP_ADDR:443"

# Create a policy granting read access to the app's secret path
vault policy write devops-python-policy - <<EOF
path "secret/data/myapp/config" {
  capabilities = ["read"]
}
EOF

# Create a role binding the policy to the app's service account
vault write auth/kubernetes/role/devops-python-role \
  bound_service_account_names=default \
  bound_service_account_namespaces=default \
  policies=devops-python-policy \
  ttl=24h

exit
```

Policy configuration (sanitized):
```
> path "secret/data/myapp/config" {
>   capabilities = ["read"]
> }
> EOF
Success! Uploaded policy: devops-python-policy
/ $ vault policy read devops-python-policy
path "secret/data/myapp/config" {
  capabilities = ["read"]
}
```

Role configuration (sanitized):
```
Key                                         Value
---                                         -----
alias_name_source                           serviceaccount_uid
bound_service_account_names                 [default]
bound_service_account_namespace_selector    n/a
bound_service_account_namespaces            [default]
policies                                    [devops-python-policy]
token_bound_cidrs                           []
token_explicit_max_ttl                      0s
token_max_ttl                               0s
token_no_default_policy                     false
token_num_uses                              0
token_period                                0s
token_policies                              [devops-python-policy]
token_ttl                                   24h
token_type                                  default
ttl                                         24h
```

### 4.4 Enable Vault Agent Injection in the Helm Chart

The Deployment template already contains the conditional Vault annotations. Enable them:

```bash
helm upgrade devops-python ./k8s/devops-python-chart \
  --set vault.enabled=true \
  --set secret.username=placeholder \
  --set secret.password=placeholder
```

The rendered annotations on the pod template will look like:

```yaml
annotations:
  vault.hashicorp.com/agent-inject: "true"
  vault.hashicorp.com/role: "devops-python-role"
  vault.hashicorp.com/agent-inject-secret-config: "secret/data/myapp/config"
```

### 4.5 Verify Secret Injection

```bash
# Get the new pod name (vault injector creates an init container + sidecar)
kubectl get pods

# Check the injected secret file
kubectl exec -it <pod-name> -c devops-python-chart -- cat /vault/secrets/config
```

Output:
```
data: map[password:secret123 username:admin]
metadata: map[created_time:2026-04-09T13:31:48.921763215Z custom_metadata:<nil> deletion_time: destroyed:false version:1]
```

### 4.6 Sidecar Injection Pattern

The Vault Agent Injector works via a **Kubernetes Mutating Admission Webhook**:

1. When a pod with `vault.hashicorp.com/agent-inject: "true"` annotation is created, the webhook intercepts the request
2. The injector mutates the pod spec, adding:
   - An **init container** (`vault-agent-init`) that authenticates with Vault and writes secrets to a shared `emptyDir` volume before the app container starts
   - A **sidecar container** (`vault-agent`) that keeps the secrets fresh (renews tokens, updates files on rotation)
3. The app container reads secrets from `/vault/secrets/` — a shared in-memory volume
4. No secrets ever appear in the pod spec, environment variables, or Kubernetes Secret objects

```
┌─────────────────────────────────────────────────────┐
│  Pod                                                │
│                                                     │
│  [vault-agent-init] → auth → write /vault/secrets/ │
│         ↕ emptyDir volume                           │
│  [app-container]   ← reads /vault/secrets/config   │
│         ↕ emptyDir volume (shared)                  │
│  [vault-agent]     ← sidecar, refreshes secrets    │
└─────────────────────────────────────────────────────┘
          ↕ Kubernetes auth
   [HashiCorp Vault] ← stores actual secrets
```

---

## 5. Bonus — Vault Agent Templates

### 5.1 Template Annotation

Enable the `.env`-format template rendering by setting `vault.template=true`:

```bash
helm upgrade devops-python ./k8s/devops-python-chart \
  --set vault.enabled=true \
  --set vault.template=true \
  --set secret.username=placeholder \
  --set secret.password=placeholder
```

The rendered annotation:

```yaml
vault.hashicorp.com/agent-inject-template-config: |
  {{- with secret "secret/data/myapp/config" -}}
  USERNAME={{ .Data.data.username }}
  PASSWORD={{ .Data.data.password }}
  {{- end -}}
```

Instead of the raw JSON output, the file at `/vault/secrets/config` will contain:

```
NAME: devops-python
LAST DEPLOYED: Thu Apr  9 16:49:50 2026
NAMESPACE: default
STATUS: deployed
REVISION: 4
DESCRIPTION: Upgrade complete
TEST SUITE: None
USERNAME=admin
PASSWORD=secret123% 
```

This is useful for apps that source a `.env` file at startup.

### 5.2 Secret Rotation with Vault Agent

The Vault Agent sidecar container **continuously monitors** the lease expiry of the secrets it fetched. When a secret approaches expiry:

1. The agent re-authenticates with Vault
2. Fetches the updated secret value
3. Re-renders the template and overwrites `/vault/secrets/config`

The `vault.hashicorp.com/agent-inject-command` annotation can trigger a command inside the app container after a secret is refreshed (e.g., send `SIGHUP` to reload config without restarting the pod):

```yaml
vault.hashicorp.com/agent-inject-command: "kill -HUP $(cat /app/app.pid)"
```

For static KV secrets (not dynamic), rotation must be triggered manually by updating the secret in Vault — the agent will pick up the new version on the next TTL cycle.

### 5.3 Named Template for Environment Variables (DRY Principle)

Instead of repeating env var definitions in every template that needs them, a named template is defined once in `_helpers.tpl`:

```yaml
{{- define "devops-python-chart.envVars" -}}
- name: PORT
  value: {{ .Values.env.port | quote }}
- name: HOST
  value: {{ .Values.env.host | quote }}
- name: DEBUG
  value: {{ .Values.env.debug | quote }}
{{- end }}
```

And referenced in `deployment.yaml` with a single `include`:

```yaml
env:
  {{- include "devops-python-chart.envVars" . | nindent 12 }}
```

Benefits:
- Single source of truth — change the variable list in one place
- Can be reused in Job templates (e.g., hooks) without duplication
- Consistent indentation via `nindent`

---

## 6. Security Analysis

### 6.1 Kubernetes Secrets vs HashiCorp Vault

| Feature | Kubernetes Secrets | HashiCorp Vault |
|---|---|---|
| Storage | etcd (base64, optionally encrypted) | Encrypted backend (Consul, etcd, S3, etc.) |
| Access control | Kubernetes RBAC | Vault policies (fine-grained paths) |
| Secret rotation | Manual | Automatic (dynamic secrets) |
| Audit logging | Kubernetes audit log | Built-in detailed audit log |
| Dynamic secrets | No | Yes (DB credentials, AWS keys, etc.) |
| Secret leasing/TTL | No | Yes — secrets expire automatically |
| Setup complexity | Low (built-in) | High (separate service to deploy) |
| Encryption at rest | Off by default | Always encrypted |

### 6.2 When to Use Each Approach

**Kubernetes Secrets are sufficient when:**
- Running in a managed cluster (EKS, GKE, AKE) with etcd encryption enabled by the provider
- Secret rotation is infrequent and manual processes are acceptable
- The team is small and RBAC can be kept simple
- You need a quick, zero-dependency solution

**HashiCorp Vault is the better choice when:**
- Secrets need to rotate automatically (database credentials, API keys)
- You need dynamic secrets (credentials generated on-demand per pod)
- Compliance requires detailed audit trails of every secret access
- Multiple teams/environments share a secret store
- You need fine-grained access control beyond what Kubernetes RBAC offers

### 6.3 Production Recommendations

1. **Never commit real secrets to Git** — use `--set` at deploy time or a CI/CD secret store
2. **Enable etcd encryption at rest** on self-managed clusters
3. **Apply RBAC** — only the application's ServiceAccount should be able to read its secrets
4. **Prefer Vault for new greenfield projects** — the operational overhead pays off quickly
5. **Use Vault dynamic secrets** for database access — credentials are unique per pod and expire
6. **Consider External Secrets Operator** as an alternative to Vault Agent Injector — it syncs secrets from Vault/AWS/GCP into native Kubernetes Secrets, keeping app manifests clean of Vault-specific annotations
