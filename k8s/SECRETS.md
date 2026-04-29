# Secret management — Lab 11

---

## Terminal evidence (copy-paste from console)

### Cluster: `minikube start`

```text
* minikube v1.37.0 on Linuxmint 22.3
* minikube 1.38.1 is available! Download it: https://github.com/kubernetes/minikube/releases/tag/v1.38.1
* To disable this notice, run: `minikube config set WantUpdateNotification false`

* Using the docker driver based on existing profile
* Starting "minikube" primary control-plane node in "minikube" cluster
* Pulling base image v0.0.48 ...
* Verifying Kubernetes components...
  - Using image gcr.io/k8s-minikube/storage-provisioner:v5
* Enabled addons: storage-provisioner, default-storageclass
* Done! kubectl is now configured to use "minikube" cluster and "default" namespace by default
```

### Task 1 — `kubectl` Secret create / view / decode

```text
$ kubectl cluster-info && kubectl get nodes -o wide
Kubernetes control plane is running at https://192.168.49.2:8443
CoreDNS is running at https://192.168.49.2:8443/api/v1/namespaces/kube-system/services/kube-dns:dns/proxy

To further debug and diagnose cluster problems, use 'kubectl cluster-info dump'.
NAME       STATUS   ROLES           AGE   VERSION   INTERNAL-IP    EXTERNAL-IP   OS-IMAGE             KERNEL-VERSION    CONTAINER-RUNTIME
minikube   Ready    control-plane   13d   v1.34.0   192.168.49.2   <none>        Ubuntu 22.04.5 LTS   6.17.0-1017-oem   docker://28.4.0
```

```text
$ kubectl delete secret app-credentials --ignore-not-found
$ kubectl create secret generic app-credentials \
  --from-literal=username=demo-user \
  --from-literal=password=demo-pass-change-me
secret/app-credentials created
=== kubectl get secret app-credentials -o yaml ===
apiVersion: v1
data:
  password: ZGVtby1wYXNzLWNoYW5nZS1tZQ==
  username: ZGVtby11c2Vy
kind: Secret
metadata:
  creationTimestamp: "2026-04-09T17:03:53Z"
  name: app-credentials
  namespace: default
  resourceVersion: "7416"
  uid: 0f6095a8-38f8-4a80-9dd9-93e0ae45109c
type: Opaque
=== decode username ===
demo-user
=== decode password ===
demo-pass-change-me
```

### Task 2 — Helm install (ClusterIP; NodePort 30080 was already taken)

First attempt failed on NodePort:

```text
Error: 1 error occurred:
	* Service "lab11-devops-info-service" is invalid: spec.ports[0].nodePort: Invalid value: 30080: provided port is already allocated
```

Successful install:

```text
$ helm version
version.BuildInfo{Version:"v3.20.1", GitCommit:"a2369ca71c0ef633bf6e4fccd66d634eb379b371", GitTreeState:"clean", GoVersion:"go1.25.8"}

$ helm upgrade --install lab11 k8s/devops-info-service \
  --namespace default \
  --set secrets.username=helm-user \
  --set secrets.password=helm-pass-lab11 \
  --set service.type=ClusterIP \
  --wait --timeout 5m
Release "lab11" does not exist. Installing it now.
NAME: lab11
LAST DEPLOYED: Thu Apr  9 20:04:33 2026
NAMESPACE: default
STATUS: deployed
REVISION: 1
TEST SUITE: None
NOTES:
devops-info-service has been deployed!
...
```

### Task 2 — Pod verification and `kubectl describe` (no literal secret values)

```text
$ kubectl get pods -l app.kubernetes.io/instance=lab11 -o wide
NAME                                       READY   STATUS    RESTARTS   AGE   IP            NODE       NOMINATED NODE   READINESS GATES
lab11-devops-info-service-bf9b64c9-4xd2d   1/1     Running   0          48s   10.244.0.60   minikube   <none>           <none>
lab11-devops-info-service-bf9b64c9-m6t6f   1/1     Running   0          48s   10.244.0.62   minikube   <none>           <none>
lab11-devops-info-service-bf9b64c9-pn99s   1/1     Running   0          48s   10.244.0.61   minikube   <none>           <none>

$ kubectl exec "$POD" -- sh -c 'env | grep -E "^(username|password)=" | sed "s/=.*/=<set>/"'
username=<set>
password=<set>

$ kubectl exec "$POD" -- sh -c 'test -n "$username" && test -n "$password" && echo OK: username and password env vars are non-empty'
OK: username and password env vars are non-empty
```

`kubectl describe pod` shows the Secret reference without decoding values:

```text
    Environment Variables from:
      lab11-devops-info-service-secret  Secret  Optional: false
```

### `helm lint` (chart check)

```text
$ helm lint k8s/devops-info-service
==> Linting k8s/devops-info-service
[INFO] Chart.yaml: icon is recommended

1 chart(s) linted, 0 chart(s) failed
```

### Task 3 — Vault chart from GitHub + Helm install

```text
$ git clone --depth 1 https://github.com/hashicorp/vault-helm.git /tmp/vault-helm
Cloning into '/tmp/vault-helm'...

$ helm install vault /tmp/vault-helm \
  --namespace default \
  --set 'server.dev.enabled=true' \
  --set 'injector.enabled=true' \
  --wait --timeout 5m
I0409 20:06:20.872817   33480 warnings.go:107] "Warning: spec.SessionAffinity is ignored for headless services"
NAME: vault
LAST DEPLOYED: Thu Apr  9 20:06:19 2026
NAMESPACE: default
STATUS: deployed
REVISION: 1
NOTES:
Thank you for installing HashiCorp Vault!
...
```

### Task 3 — Vault pods

```text
$ kubectl get pods -o wide | grep vault
vault-0                                         1/1     Running   0              49s     10.244.0.65   minikube   <none>           <none>
vault-agent-injector-7845f59846-hrhvn           1/1     Running   0              49s     10.244.0.64   minikube   <none>           <none>
```

### Task 3 — Vault CLI (KV, Kubernetes auth, policy, role)

```text
=== Vault: enable KV v2 (if needed) ===
Error enabling: Error making API request.

URL: POST http://127.0.0.1:8200/v1/sys/mounts/secret
Code: 400. Errors:

* path is already in use at secret/
command terminated with exit code 2
=== Vault: put secret at secret/myapp/config ===
====== Secret Path ======
secret/data/myapp/config

======= Metadata =======
Key                Value
---                ---
created_time       2026-04-09T17:07:25.583061099Z
custom_metadata    <nil>
deletion_time      n/a
destroyed          false
version            1
=== Vault: enable kubernetes auth ===
Success! Enabled kubernetes auth method at: kubernetes/
=== Vault: kubernetes auth config ===
Success! Data written to: auth/kubernetes/config
```

```text
=== Vault: policy devops-info-service ===
Success! Uploaded policy: devops-info-service
=== Vault: read policy (sanitized) ===
path "secret/data/myapp/config" {
  capabilities = ["read"]
}
=== Vault: kubernetes role ===
WARNING! The following warnings were returned from Vault:

  * Role devops-info-service does not have an audience configured. While
    audiences are not required, consider specifying one if your use case would
    benefit from additional JWT claim verification.
```

### Task 3 — Helm upgrade: enable injector + proof of files in pod

```text
$ helm upgrade lab11 k8s/devops-info-service \
  --namespace default \
  --set secrets.username=helm-user \
  --set secrets.password=helm-pass-lab11 \
  --set service.type=ClusterIP \
  --set vault.injector.enabled=true \
  --set vault.role=devops-info-service \
  --wait --timeout 8m
Release "lab11" has been upgraded. Happy Helming!
NAME: lab11
...
STATUS: deployed
REVISION: 2
```

```text
$ kubectl get pods -l app.kubernetes.io/instance=lab11 -o wide
NAME                                         READY   STATUS    RESTARTS   AGE   IP            NODE       NOMINATED NODE   READINESS GATES
lab11-devops-info-service-6c9f6fb95f-4wlth   2/2     Running   0          49s   10.244.0.69   minikube   <none>           <none>
lab11-devops-info-service-6c9f6fb95f-g82gk   2/2     Running   0          73s   10.244.0.68   minikube   <none>           <none>
lab11-devops-info-service-6c9f6fb95f-lpg6q   2/2     Running   0          97s   10.244.0.67   minikube   <none>           <none>

$ kubectl get pod "$POD" -o jsonpath='{.spec.containers[*].name}' && echo
devops-info-service vault-agent

$ kubectl get pod "$POD" -o jsonpath='{.spec.initContainers[*].name}' && echo
vault-agent-init

$ kubectl get pod "$POD" -o jsonpath='{.metadata.annotations}' | tr ',' '\n' | grep vault
"vault.hashicorp.com/agent-inject":"true"
"vault.hashicorp.com/agent-inject-secret-config":"secret/data/myapp/config"
"vault.hashicorp.com/agent-inject-status":"injected"
"vault.hashicorp.com/role":"devops-info-service"

$ kubectl exec "$POD" -c devops-info-service -- ls -la /vault/secrets
total 8
drwxrwsrwt 2 root appuser   60 Apr  9 17:08 .
drwxr-xr-x 3 root root    4096 Apr  9 17:08 ..
-rw-r--r-- 1  100 appuser  179 Apr  9 17:08 config

$ kubectl exec "$POD" -c devops-info-service -- wc -c /vault/secrets/config
179 /vault/secrets/config
```

### Release values after upgrade (Helm stores user-supplied values)

```text
$ helm get values lab11
USER-SUPPLIED VALUES:
secrets:
  password: helm-pass-lab11
  username: helm-user
service:
  type: ClusterIP
vault:
  injector:
    enabled: true
  role: devops-info-service
```

---

## 1. Kubernetes Secrets (Task 1)

### Create a Secret with `kubectl`

```bash
kubectl create secret generic app-credentials \
  --from-literal=username=demo-user \
  --from-literal=password=demo-pass-change-me
```

### View and decode

```bash
kubectl get secret app-credentials -o yaml
```

Example shape (values are **base64-encoded**, not encrypted):

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: app-credentials
type: Opaque
data:
  username: ZGVtby11c2Vy              # echo ... | base64 -d  →  demo-user
  password: ZGVtby1wYXNzLWNoYW5nZS1tZQ==
```

Decode:

```bash
kubectl get secret app-credentials -o jsonpath='{.data.username}' | base64 -d
echo
kubectl get secret app-credentials -o jsonpath='{.data.password}' | base64 -d
echo
```

### Encoding vs encryption

- **Base64** in the API is an encoding so binary data can travel in JSON/YAML. Anyone who can `kubectl get secret` (or read etcd with sufficient access) can recover the original strings.
- **Encryption** means ciphertext that requires keys to read. That is **not** what base64 provides.

### Security implications

- **At rest:** Kubernetes does **not** encrypt Secret *values* in etcd by default. You should use **encryption at rest** (EncryptionConfiguration with a provider such as `identity`, `aescbc`, or `kms`) so etcd backups and disk access do not expose plaintext.
- **In use:** Restrict who can read Secrets with RBAC; avoid logging env vars; prefer short-lived credentials where possible.
- **When to enable etcd encryption:** For any environment where etcd or control-plane backups could be exposed, or for compliance requirements—enable before relying on Secrets for sensitive production data.

---

## 2. Helm secret integration (Task 2)

### Chart layout

| File | Purpose |
|------|---------|
| `k8s/devops-info-service/templates/secrets.yaml` | `Secret` with `stringData` for `username` / `password` |
| `k8s/devops-info-service/templates/deployment.yaml` | `envFrom.secretRef` → all keys become environment variables |
| `k8s/devops-info-service/values.yaml` | `secrets.*` defaults (placeholders only) |

The rendered Secret name is `{{ release-name }}-{{ chart-name }}-secret` (helper `devops-info-service.secretName`). Example for release `lab11`:

```yaml
metadata:
  name: lab11-devops-info-service-secret
stringData:
  username: "placeholder-username"
  password: "placeholder-password"
```

### How the Deployment consumes the Secret

```yaml
env:
  - name: HOST
    value: 0.0.0.0
  - name: PORT
    value: "5000"
envFrom:
  - secretRef:
      name: lab11-devops-info-service-secret
```

All keys in the Secret (`username`, `password`) are mounted as environment variables with the same names.

### Deploy (example)

```bash
helm upgrade --install lab11 k8s/devops-info-service \
  --namespace default \
  --set secrets.username=appuser \
  --set secrets.password='use-a-strong-secret-here'
```

### Verify inside the pod (without printing secret values)

```bash
POD=$(kubectl get pods -l app.kubernetes.io/instance=lab11 -o jsonpath='{.items[0].metadata.name}')
kubectl exec -it "$POD" -- env | grep -E '^(username|password)=' | sed 's/=.*/=<redacted>/'
```

Expected: two lines with names `username` and `password`, values redacted.

```bash
kubectl exec -it "$POD" -- sh -c 'test -n "$username" && test -n "$password" && echo "Both vars are set"'
```

### `kubectl describe pod` and secrets

`kubectl describe pod` shows **that** a Secret is referenced (e.g. as an environment source from a Secret), but it does **not** list the decoded key values. Plaintext appears in the API only to clients with `get secret` permission; still avoid relying on “security through describe.”

---

## 3. Resource management (Task 2)

### Configuration

CPU and memory are driven from `values.yaml` (overridable per environment with `-f values-dev.yaml` / `values-prod.yaml`):

```yaml
resources:
  limits:
    cpu: 200m
    memory: 256Mi
  requests:
    cpu: 100m
    memory: 128Mi
```

### Requests vs limits

- **Requests:** Used by the scheduler for placement and by the kubelet for guaranteed minimum resources. They affect **quality of service** and fairness.
- **Limits:** Hard cap; the container cannot exceed these (CPU is throttled; memory OOMKilled if exceeded).

### Choosing values

Start from observed usage (`kubectl top pod` with metrics-server), add headroom for spikes, and set limits to prevent noisy neighbors. For this small HTTP service, the defaults above are a reasonable starting point; production should be validated under load.

---

## 4. HashiCorp Vault integration (Task 3)

### Install Vault (Helm, dev mode — learning only)

```bash
helm repo add hashicorp https://helm.releases.hashicorp.com
helm repo update

helm install vault hashicorp/vault \
  --set 'server.dev.enabled=true' \
  --set 'injector.enabled=true'
```

### Verify pods

```bash
kubectl get pods -l app.kubernetes.io/name=vault
```

Expect `vault-0` Running and the injector pod Ready.

### Configure KV v2 and application secrets

Exec into the Vault pod and use the CLI (dev mode is auto-unsealed):

```bash
kubectl exec -it vault-0 -- vault secrets enable -path=secret kv-v2
# If "path is already in use", list with: vault secrets list

kubectl exec -it vault-0 -- vault kv put secret/myapp/config \
  username="vault-demo-user" \
  password="vault-demo-password"
```

At least two keys are stored under `secret/myapp/config`.

### Enable Kubernetes auth

```bash
kubectl exec -it vault-0 -- vault auth enable kubernetes
```

Configure the auth method from inside `vault-0` using the pod’s ServiceAccount (works on most clusters):

```bash
kubectl exec -it vault-0 -- sh -c '
vault write auth/kubernetes/config \
  token_reviewer_jwt="$(cat /var/run/secrets/kubernetes.io/serviceaccount/token)" \
  kubernetes_host="https://${KUBERNETES_SERVICE_HOST}:${KUBERNETES_SERVICE_PORT}" \
  kubernetes_ca_cert=@/var/run/secrets/kubernetes.io/serviceaccount/ca.crt
'
```

### Policy (sanitized) — read only for this app path

Write policy `devops-info-service` (name can match your Vault role):

```hcl
path "secret/data/myapp/config" {
  capabilities = ["read"]
}
```

Apply inside the pod:

```bash
kubectl exec -it vault-0 -- sh -c 'vault policy write devops-info-service - <<EOF
path \"secret/data/myapp/config\" {
  capabilities = [\"read\"]
}
EOF'
```

### Role bound to the workload ServiceAccount

After you deploy the chart **with Vault injection enabled**, the pod uses a ServiceAccount named like `<release>-devops-info-service` (e.g. `lab11-devops-info-service`). Bind the policy to that account in the **namespace where the app runs**:

```bash
RELEASE=lab11
NAMESPACE=default
SA="${RELEASE}-devops-info-service"

kubectl exec -it vault-0 -- vault write auth/kubernetes/role/devops-info-service \
  bound_service_account_names="$SA" \
  bound_service_account_namespaces="$NAMESPACE" \
  policies=devops-info-service \
  ttl=24h
```

### Enable injection in the Helm chart

```bash
helm upgrade --install lab11 k8s/devops-info-service \
  --namespace default \
  --set vault.injector.enabled=true \
  --set vault.role=devops-info-service
```

Rendered annotations (see `templates/deployment.yaml`):

- `vault.hashicorp.com/agent-inject: "true"`
- `vault.hashicorp.com/role: "devops-info-service"`
- `vault.hashicorp.com/agent-inject-secret-config: "secret/data/myapp/config"`

The Agent writes a file per `agent-inject-secret-*` annotation; the suffix `config` maps to **`/vault/secrets/config`** in the pod.

### Proof of file injection

```bash
POD=$(kubectl get pods -l app.kubernetes.io/instance=lab11 -o jsonpath='{.items[0].metadata.name}')
kubectl exec -it "$POD" -- ls -la /vault/secrets
kubectl exec -it "$POD" -- wc -c /vault/secrets/config
```

### Sidecar injection pattern

The **Vault Agent Injector** mutates the pod spec to add an **init** and **sidecar** container. They authenticate to Vault using the pod’s ServiceAccount token, fetch secrets, and keep files (or templates) updated according to Vault policy. Application reads files from a shared volume instead of storing long-lived credentials in the image or plain Helm values.

---

## 5. Security analysis (Task 4)

| Aspect | Kubernetes Secrets | Vault |
|--------|-------------------|--------|
| Storage | etcd (optionally encrypted at rest) | Dedicated store, policies, audit |
| Rotation | Manual / external automation | Dynamic secrets, leases, easier rotation workflows |
| Access control | RBAC on Secret objects | Fine-grained policies, namespaces, auth methods |
| Injection | env / volume from Secret | Agent injector, templates, short-lived tokens |

**When to use which**

- **Kubernetes Secrets:** Simple apps, few static credentials, cluster already hardened (RBAC, etcd encryption, network policy).
- **Vault:** Centralized secrets, many services, strict audit, dynamic DB credentials, or multi-cluster consistency.

**Production recommendations**

- Enable **etcd encryption at rest** and tight **RBAC** for Secret access.
- Prefer **external secret managers** (Vault, cloud secret stores) for high-value credentials; sync to Secrets with tools like External Secrets Operator if needed.
- Never commit real secrets; use CI/CD secret stores and `helm upgrade --set` or sealed secrets for GitOps.
- Do **not** use Helm `server.dev.enabled` Vault in production; use a proper HA/storage backend and unseal workflow.

---

## Appendix — quick `helm template` checks

```bash
helm template lab11 k8s/devops-info-service --show-only templates/secrets.yaml
helm template lab11 k8s/devops-info-service --set vault.injector.enabled=true \
  --show-only templates/deployment.yaml \
  --show-only templates/serviceaccount.yaml
```

---
