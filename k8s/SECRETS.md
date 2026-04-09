# Lab 11 — Secret management

This report covers native Kubernetes `Secrets`, a Helm-managed `Secret` for [`devops-info-service`](./devops-info-service/), and HashiCorp Vault Agent Injector integration.

---

## 1. Kubernetes Secrets (Task 1)

```bash
kubectl create secret generic app-credentials \
  --from-literal=username=demo-user \
  --from-literal=password=demo-pass \
  --namespace default
```

```text
secret/app-credentials created
```

```bash
kubectl get secret app-credentials -o yaml
```

```yaml
apiVersion: v1
data:
  password: ZGVtby1wYXNz
  username: ZGVtby11c2Vy
kind: Secret
metadata:
  creationTimestamp: "2026-04-09T18:09:34Z"
  name: app-credentials
  namespace: default
  resourceVersion: "310032"
  uid: d899aee7-04c3-4da1-aac5-9dcd1322f9c0
type: Opaque
```

```bash
kubectl get secret app-credentials -o jsonpath='{.data.username}' | base64 -d
echo
kubectl get secret app-credentials -o jsonpath='{.data.password}' | base64 -d
echo
```

```text
demo-user
demo-pass
```

The `data` fields are base64-encoded, not encrypted: whoever can `kubectl get` the object can decode the values. Encryption would mean keys and algorithms (e.g. AES) so ciphertext stays useless without the key. In a real cluster, etcd may still store objects in plaintext unless the admin turns on [encryption at rest](https://kubernetes.io/docs/tasks/administer-cluster/encrypt-data/) for API resources. Limit access with RBAC either way.

---

## 2. Helm-managed Secret (Task 2)

| File | Role |
|------|------|
| [`templates/secrets.yaml`](./devops-info-service/templates/secrets.yaml) | `Secret` (`stringData` keys `username`, `password`) |
| [`templates/deployment.yaml`](./devops-info-service/templates/deployment.yaml) | `envFrom.secretRef` when `credentials.enabled` |
| [`values.yaml`](./devops-info-service/values.yaml) | Default `credentials.*`; overrides via `--set` or a file outside Git |

Rendered Secret name for release `lab11`: `lab11-devops-info-service-credentials`.

Install initially failed with **Invalid value: 30081: provided port is already allocated** (NodePort collision). [`values-dev.yaml`](./devops-info-service/values-dev.yaml) uses **`nodePort: 30082`**. Successful install:

```bash
helm upgrade --install lab11 ./k8s/devops-info-service \
  -f k8s/devops-info-service/values-dev.yaml \
  --namespace lab11 --create-namespace \
  --set credentials.username=demo-user \
  --set credentials.password=demo-pass
```

```text
Release "lab11" has been upgraded. Happy Helming!
NAME: lab11
LAST DEPLOYED: Thu Apr  9 21:34:51 2026
NAMESPACE: lab11
STATUS: deployed
REVISION: 2
TEST SUITE: None
NOTES:
1. Get the application URL by running these commands:
  export NODE_PORT=$(kubectl get --namespace lab11 -o jsonpath="{.spec.ports[0].nodePort}" services lab11-devops-info-service)
  export NODE_IP=$(kubectl get nodes --namespace lab11 -o jsonpath="{.items[0].status.addresses[0].address}")
  echo http://$NODE_IP:$NODE_PORT/health

Release: lab11
Namespace: lab11
```

```bash
kubectl get secret -n lab11
```

```text
NAME                                    TYPE                 DATA   AGE
lab11-devops-info-service-credentials   Opaque               2      20m
sh.helm.release.v1.lab11.v1             helm.sh/release.v1   1      20m
sh.helm.release.v1.lab11.v2             helm.sh/release.v1   1      91s
```

```bash
kubectl get secret lab11-devops-info-service-credentials -n lab11 -o yaml
```

```yaml
apiVersion: v1
data:
  password: ZGVtby1wYXNz
  username: ZGVtby11c2Vy
kind: Secret
metadata:
  annotations:
    meta.helm.sh/release-name: lab11
    meta.helm.sh/release-namespace: lab11
  creationTimestamp: "2026-04-09T18:14:21Z"
  labels:
    app.kubernetes.io/instance: lab11
    app.kubernetes.io/managed-by: Helm
    app.kubernetes.io/name: devops-info-service
    app.kubernetes.io/version: 1.0.0
    helm.sh/chart: devops-info-service-0.1.0
  name: lab11-devops-info-service-credentials
  namespace: lab11
  resourceVersion: "310284"
  uid: 39874459-383d-447a-8f15-81c66f64cdb1
type: Opaque
```

```bash
kubectl exec -it deploy/lab11-devops-info-service -n lab11 -- printenv username
kubectl exec -it deploy/lab11-devops-info-service -n lab11 -- printenv password
```

```text
demo-user
demo-pass
```

`kubectl describe pod` references the Secret for injected keys; it does not show the secret material:

```bash
kubectl describe pod -n lab11 -l app.kubernetes.io/instance=lab11
```

```text
Name:             lab11-devops-info-service-674b6f7484-998jp
Namespace:        lab11
...
Containers:
  devops-info-service:
    ...
    Limits:
      cpu:     150m
      memory:  192Mi
    Requests:
      cpu:      50m
      memory:   64Mi
    ...
    Environment Variables from:
      lab11-devops-info-service-credentials  Secret  Optional: false
    Environment:
      HOST:            0.0.0.0
      PORT:            5000
      LAB9_UPDATE_ID:  v4
...
```

```bash
helm lint ./k8s/devops-info-service
```

```text
==> Linting ./k8s/devops-info-service
[INFO] Chart.yaml: icon is recommended
1 chart(s) linted, 0 chart(s) failed
```

---

## 3. Resource management

For release `lab11` with [`values-dev.yaml`](./devops-info-service/values-dev.yaml), the `kubectl describe pod` excerpt shows **requests** `50m` CPU / `64Mi` memory and **limits** `150m` CPU / `192Mi` memory.

**Requests** reserve scheduling guarantees; **limits** cap usage (CPU may throttle; memory pressure can trigger OOMKill).

---

## 4. HashiCorp Vault (Task 3)

Context: `minikube` (`kubectl config current-context`); control plane Running.

### Helm repo and install (dev mode — lab only)

```bash
helm repo add hashicorp https://helm.releases.hashicorp.com
helm repo update
```

`helm repo add` / `helm repo update` returned **403 Forbidden** on the index without VPN; with VPN the index downloaded successfully.

```bash
helm install vault hashicorp/vault \
  --set "server.dev.enabled=true" \
  --set "injector.enabled=true" \
  --namespace vault --create-namespace
```

```text
NAME: vault
LAST DEPLOYED: Thu Apr  9 21:40:53 2026
NAMESPACE: vault
STATUS: deployed
REVISION: 1
NOTES:
Thank you for installing HashiCorp Vault!
...
```

`vault-agent-injector` became **Running** first. `vault-0` remained **ContainerCreating** during a long pull of `hashicorp/vault:1.21.2`. The image was already on the node (`minikube ssh -- docker pull hashicorp/vault:1.21.2` reported *Image is up to date*). Deleting the pod (`kubectl delete pod vault-0 -n vault`) forced recreation; **`vault-0`** then reached **1/1 Running**.

```text
NAME                                   READY   STATUS    RESTARTS   AGE
vault-0                                1/1     Running   0          ...
vault-agent-injector-6b4f84b6c-sdr8g   1/1     Running   0          ...
```

### Configure Vault (inside `vault-0`)

```bash
kubectl exec -it vault-0 -n vault -- sh
export VAULT_ADDR=http://127.0.0.1:8200
export VAULT_TOKEN=root
```

`vault secrets enable -path=secret kv-v2` failed because `secret/` was already mounted:

```text
vault secrets enable -path=secret kv-v2
Error enabling: Error making API request.
...
* path is already in use at secret/
```

KV v2 secret:

```text
vault kv put secret/devops-info/config username="vault-user" password="vault-pass"
========= Secret Path =========
secret/data/devops-info/config

======= Metadata =======
Key                Value
---                -----
created_time       2026-04-09T19:23:33.183054171Z
custom_metadata    <nil>
deletion_time      n/a
destroyed          false
version            1
```

Kubernetes auth and API server address:

```text
vault auth enable kubernetes
Success! Enabled kubernetes auth method at: kubernetes/

vault write auth/kubernetes/config kubernetes_host="https://kubernetes.default.svc:443"
Success! Data written to: auth/kubernetes/config
```

Policy:

```text
vault policy write devops-info-read - <<'EOF'
path "secret/data/devops-info/*" {
  capabilities = ["read"]
}
EOF
Success! Uploaded policy: devops-info-read
```

Role `devops-info-service` for ServiceAccount `lab11-devops-info-service-sa` in namespace `lab11`:

```text
vault write auth/kubernetes/role/devops-info-service \
  bound_service_account_names=lab11-devops-info-service-sa \
  bound_service_account_namespaces=lab11 \
  policies=devops-info-read \
  ttl=24h
WARNING! The following warnings were returned from Vault:

  * Role devops-info-service does not have an audience configured. While
  audiences are not required, consider specifying one if your use case would
  benefit from additional JWT claim verification.
```

```text
vault read auth/kubernetes/role/devops-info-service
Key                                         Value
---                                         -----
alias_name_source                           serviceaccount_uid
bound_service_account_names                 [lab11-devops-info-service-sa]
bound_service_account_namespace_selector    n/a
bound_service_account_namespaces            [lab11]
policies                                    [devops-info-read]
token_policies                              [devops-info-read]
token_ttl                                   24h
token_type                                  default
ttl                                         24h
```

### Deploy the app with injection

Upgrade release `lab11` with [`values-dev.yaml`](./devops-info-service/values-dev.yaml) and [`values-vault.yaml`](./devops-info-service/values-vault.yaml):

```bash
helm upgrade lab11 ./k8s/devops-info-service \
  -f k8s/devops-info-service/values-dev.yaml \
  -f k8s/devops-info-service/values-vault.yaml \
  --namespace lab11
```

```text
Release "lab11" has been upgraded. Happy Helming!
NAME: lab11
LAST DEPLOYED: Thu Apr  9 22:41:14 2026
NAMESPACE: lab11
STATUS: deployed
REVISION: 3
...
```

With `vaultInjection.enabled: true` and `credentials.enabled: true`, the Pod keeps `envFrom` from the chart `Secret` and receives Vault Agent annotations (`agent-inject`, `role: devops-info-service`, `agent-inject-secret-config: secret/data/devops-info/config`); the rendered file is **`/vault/secrets/config`**.

### Rollout, pods, injected file

```bash
kubectl rollout status deployment/lab11-devops-info-service -n lab11
```

```text
Waiting for deployment "lab11-devops-info-service" rollout to finish: 1 old replicas are pending termination...
deployment "lab11-devops-info-service" successfully rolled out
```

```bash
kubectl get pods -n lab11
```

```text
NAME                                         READY   STATUS    RESTARTS   AGE
lab11-devops-info-service-7cfb88f5bf-m4pn8   2/2     Running   0          5m23s
```

**2/2**: application container and **vault-agent** sidecar (after init completes).

```bash
kubectl exec -it deploy/lab11-devops-info-service -n lab11 -c devops-info-service -- cat /vault/secrets/config
```

```text
data: map[password:vault-pass username:vault-user]
metadata: map[created_time:2026-04-09T19:23:33.183054171Z custom_metadata:<nil> deletion_time: destroyed:false version:1]
```

The file reflects the KV **v2** API shape (`data` and `metadata`).

### Sidecar pattern

The mutating webhook adds an **init container and sidecar** that authenticate to Vault with the Pod’s Kubernetes service account JWT, fetch secrets, and refresh them on a schedule. The application can read files (or env) materialized by the agent instead of embedding credentials in the Pod spec.

---

## 5. Security analysis

| Topic | Kubernetes Secret | Vault |
|--------|-------------------|--------|
| Storage | etcd (base64; optionally encrypt at rest) | Vault storage backend |
| Rotation | Manual / external automation | Leases, rotation, dynamic secrets |
| Access model | RBAC on Secret objects | Policies, auth methods |
| Audit | Kubernetes audit logs | Vault audit devices |

Native Secrets suit low sensitivity and simple deployments; Vault suits centralized policy, rotation, and stronger audit. This lab used Vault **dev mode**; production would use TLS, HA, auto-unseal, and tight RBAC.

