# Lab 11 — Kubernetes Secrets and Vault Integration

**Author:** Nikita Maksimenko  
**Date:** 2026-04-05  
**Sources for non-secret literals:** `k8s/deployment.yml` (image `nexonm22/devops-info-service:lab08`, metadata name `devops-info-service`)

---

## Runtime environment

The exercises used Docker Desktop with Engine `28.1.1` (`linux/arm64`, context `desktop-linux`), minikube `v1.38.1`, Kubernetes `v1.35.1` on the server, kubectl client `v1.35.3`, and Helm `v4.1.3`. The active context was `minikube`.

```
$ kubectl get nodes -o wide
NAME       STATUS   ROLES           AGE   VERSION   INTERNAL-IP    EXTERNAL-IP   OS-IMAGE                         KERNEL-VERSION     CONTAINER-RUNTIME
minikube   Ready    control-plane   14m   v1.35.1   192.168.49.2   <none>        Debian GNU/Linux 12 (bookworm)   6.10.14-linuxkit   docker://29.2.1
```

---

## Kubernetes Secrets

### Imperative Secret object

The `app-credentials` Secret was created with literals taken from Lab 9 (`nexonm22` from the image repository prefix, `devops-info-service` from the Deployment name in `k8s/deployment.yml`).

```
$ kubectl create secret generic app-credentials --from-literal=username=nexonm22 --from-literal=password=devops-info-service
secret/app-credentials created
```

### Inspecting the object in YAML

```
$ kubectl get secret app-credentials -o yaml
apiVersion: v1
data:
  password: ZGV2b3BzLWluZm8tc2VydmljZQ==
  username: bmV4b25tMjI=
kind: Secret
metadata:
  creationTimestamp: "2026-04-05T15:18:26Z"
  name: app-credentials
  namespace: default
  resourceVersion: "541"
  uid: 89b42713-6bc9-41c9-a5e8-df3f57d8c210
type: Opaque
```

### Base64 fields and decoding

The API stores `data` as base64. Decoding matched the literals above:

```
$ echo -n 'bmV4b25tMjI=' | base64 -d
nexonm22
$ echo -n 'ZGV2b3BzLWluZm8tc2VydmljZQ==' | base64 -d
devops-info-service
```

The same values were read back through the API:

```
$ kubectl get secret app-credentials -o jsonpath='{.data.username}' | base64 -d

nexonm22
$ kubectl get secret app-credentials -o jsonpath='{.data.password}' | base64 -d

devops-info-service
```

### Encoding versus encryption

Base64 is an encoding, not encryption: anyone who can read the Secret through the API can decode these strings. Kubernetes did not encrypt Secret contents at rest by default in this cluster; RBAC and audit still applied, while etcd stored the values in readable form unless **encryption at rest** was enabled for the `secrets` resource in the API server configuration. Etcd encryption at rest wrapped Secret (and ConfigMap) writes with a configured KMS or local key; production clusters often enabled it when etcd backups and disk access were sensitive.

---

## Helm Secret Integration

### Chart structure

The chart gained a dedicated Secret template, a ServiceAccount, and optional Vault Agent Injector annotations.

```
k8s/devops-info-service/
├── Chart.yaml
├── values.yaml
├── values-dev.yaml
├── values-prod.yaml
├── values-vault.yaml
└── templates/
    ├── _helpers.tpl
    ├── deployment.yaml
    ├── service.yaml
    ├── serviceaccount.yaml
    ├── secrets.yaml
    └── hooks/
        ...
```

`templates/secrets.yaml` renders when `credentialsSecret.enabled` is true. Metadata reused `devops-info-service.labels`. The Secret name followed `{{ include "devops-info-service.fullname" . }}-{{ .Values.credentialsSecret.nameSuffix }}`. For release `lab11-app` the object was `lab11-app-devops-info-service-credentials`.

### Deployment consumption

The workload consumed the Helm Secret with `envFrom` and `secretRef` as rendered by the chart (release `lab11-app`).

### Lint

```
$ helm lint k8s/devops-info-service
==> Linting k8s/devops-info-service
[INFO] Chart.yaml: icon is recommended

1 chart(s) linted, 0 chart(s) failed
```

### Live install and status

The application chart was installed with Vault injector values. The first `helm install` waited on the Deployment until the five replicas became Ready; Vault Agent Init failed with `invalid role name "devops-info-service"` until the Kubernetes auth role existed, so Helm exited with a timeout. After `vault write auth/kubernetes/role/devops-info-service` pointed at ServiceAccount `lab11-app-devops-info-service`, the pods reached `2/2` and a `helm upgrade` with `--wait` marked the release `deployed`.

```
$ helm install lab11-app k8s/devops-info-service -f k8s/devops-info-service/values-vault.yaml --wait --timeout 5m
Error: INSTALLATION FAILED: resource Deployment/default/lab11-app-devops-info-service not ready. status: InProgress, message: Available: 0/5
context deadline exceeded
```

```
$ helm upgrade lab11-app k8s/devops-info-service -f k8s/devops-info-service/values-vault.yaml --wait --timeout 3m
Release "lab11-app" has been upgraded. Happy Helming!
...
STATUS: deployed
REVISION: 2
```

```
$ helm status lab11-app
...
==> v1/Deployment
NAME                            READY   UP-TO-DATE   AVAILABLE
lab11-app-devops-info-service   5/5     5            5
...
==> v1/Secret
NAME                                        TYPE     DATA   AGE
lab11-app-devops-info-service-credentials   Opaque   2      ...
```

### `kubectl describe pod` (no literal values)

`kubectl describe pod` showed where environment variables came from without echoing the Secret contents.

```
$ kubectl describe pod "$(kubectl get pods -l app.kubernetes.io/instance=lab11-app -o jsonpath='{.items[0].metadata.name}')" | grep -A4 "Environment Variables from:"
    Environment Variables from:
      lab11-app-devops-info-service-credentials  Secret  Optional: false
    Environment:                                 <none>
    Mounts:
      /var/run/secrets/kubernetes.io/serviceaccount from kube-api-access-88k69 (ro)
```

### Process environment (values redacted)

```
$ kubectl exec -c devops-info-service "$(kubectl get pods -l app.kubernetes.io/instance=lab11-app -o jsonpath='{.items[0].metadata.name}')" -- sh -c 'env | grep -E "^(username|password)=" | sed "s/=.*$/=<present>/"'
username=<present>
password=<present>
```

---

## Resource Management

### Configuration

Requests and limits matched `k8s/deployment.yml`: requests `100m` CPU and `128Mi` memory; limits `500m` CPU and `256Mi` memory. `kubectl describe pod` on an application container showed those fields alongside the liveness and readiness probes.

### Requests versus limits

Requests were used by the scheduler for placement and by `kubelet` for guaranteed minimums on the node. Limits capped burst usage; a container that exceeded its memory limit was terminated; CPU was throttled when usage rose above the limit. The chart kept the Lab 9 sizing table in `values.yaml` so production defaults matched the static manifest.

---

## Vault Integration

### Helm chart source (repository 403)

`helm repo add hashicorp https://helm.releases.hashicorp.com` failed with HTTP `403 Forbidden` from CloudFront when this environment fetched `index.yaml`, so the chart was unpacked from the upstream Git tag tarball instead.

```
$ helm repo add hashicorp https://helm.releases.hashicorp.com
Error: looks like "https://helm.releases.hashicorp.com" is not a valid chart repository or cannot be reached: failed to fetch https://helm.releases.hashicorp.com/index.yaml : 403 Forbidden
```

```
$ curl -sSIL https://helm.releases.hashicorp.com/index.yaml | head -6
HTTP/2 403
server: CloudFront
...
```

The chart directory came from `https://github.com/hashicorp/vault-helm/archive/refs/tags/v0.29.0.tar.gz`, extracted to `/tmp/vault-helm-0.29.0`.

### Install output

```
$ helm install vault /tmp/vault-helm-0.29.0 --set server.dev.enabled=true --set injector.enabled=true --wait --timeout 5m
NAME: vault
LAST DEPLOYED: Sun Apr  5 18:18:56 2026
NAMESPACE: default
STATUS: deployed
REVISION: 1
CHART: vault-0.29.0
APP VERSION: 1.18.1
```

### Pod verification

```
$ kubectl get pods -l app.kubernetes.io/name=vault
NAME                                    READY   STATUS    RESTARTS   AGE
vault-0                                 1/1     Running   0          ...
vault-agent-injector-7b94fddd44-kwzkc   1/1     Running   0          ...
```

`vault-0` logs contained the standard HashiCorp warning that **dev mode** is enabled and must not be used in production; the printed Unseal Key and Root Token lines were not copied into this report.

### KV data

The dev server already exposed KV v2 at mount `secret/`. A two-field object was written at `secret/devops-info-service/config`.

```
$ kubectl exec vault-0 -- sh -c 'export VAULT_TOKEN=<redacted> VAULT_ADDR=http://127.0.0.1:8200; vault kv put secret/devops-info-service/config username=nexonm22 password=devops-info-service'
============= Secret Path =============
secret/data/devops-info-service/config

======= Metadata =======
Key                Value
---                -----
created_time       2026-04-05T15:19:45.653690468Z
custom_metadata    <nil>
deletion_time      n/a
destroyed          false
version            1
```

(The real command used the dev-mode root token from pod logs only inside the shell; the token string was replaced above.)

### Kubernetes auth

```
$ kubectl exec vault-0 -- sh -c 'export VAULT_TOKEN=<redacted> VAULT_ADDR=http://127.0.0.1:8200; vault auth enable kubernetes'
Success! Enabled kubernetes auth method at: kubernetes/
```

Configuration used the Kubernetes Service address inside the Vault pod (`https://$KUBERNETES_SERVICE_HOST:$KUBERNETES_SERVICE_PORT`, which expanded to `https://10.96.0.1:443` in this run), the pod service-account JWT at `/var/run/secrets/kubernetes.io/serviceaccount/token`, and the cluster CA bundle at `/var/run/secrets/kubernetes.io/serviceaccount/ca.crt`, with issuer `https://kubernetes.default.svc.cluster.local`.

```
$ kubectl exec vault-0 -- sh -c 'export VAULT_TOKEN=<redacted> VAULT_ADDR=http://127.0.0.1:8200
TOKEN=$(cat /var/run/secrets/kubernetes.io/serviceaccount/token)
vault write auth/kubernetes/config \
  kubernetes_host="https://$KUBERNETES_SERVICE_HOST:$KUBERNETES_SERVICE_PORT" \
  token_reviewer_jwt="$TOKEN" \
  kubernetes_ca_cert=@/var/run/secrets/kubernetes.io/serviceaccount/ca.crt \
  issuer="https://kubernetes.default.svc.cluster.local"'
Success! Data written to: auth/kubernetes/config
```

### Policy and role (sanitised)

Policy `devops-info-service` + role `devops-info-service`:

```
$ kubectl exec vault-0 -- sh -c 'export VAULT_TOKEN=<redacted> VAULT_ADDR=http://127.0.0.1:8200; vault read auth/kubernetes/role/devops-info-service'
Key                                         Value
---                                         -----
bound_service_account_names                 [lab11-app-devops-info-service]
bound_service_account_namespaces            [default]
policies                                    [devops-info-service]
token_ttl                                   1h
ttl                                         1h
```

```
$ kubectl exec vault-0 -- sh -c 'export VAULT_TOKEN=<redacted> VAULT_ADDR=http://127.0.0.1:8200; vault read sys/policy/devops-info-service'
Key      Value
---      -----
name     devops-info-service
rules    path "secret/data/devops-info-service/*" {
  capabilities = ["read"]
}
path "secret/metadata/devops-info-service/*" {
  capabilities = ["read", "list"]
}
```

### Agent injector annotations

With `values-vault.yaml`, the Pod template carried `vault.hashicorp.com/agent-inject: "true"`, `vault.hashicorp.com/role: "devops-info-service"`, and `vault.hashicorp.com/agent-inject-secret-config: "secret/data/devops-info-service/config"`.

### Injected file path

Application pods ran two containers (`devops-info-service` and `vault-agent`) after the init container exited.

```
$ kubectl get pods -l app.kubernetes.io/instance=lab11-app
NAME                                             READY   STATUS    RESTARTS   AGE
lab11-app-devops-info-service-56b5b4f549-24hx6   2/2     Running   0          ...
...
```

```
$ kubectl exec -c devops-info-service "$(kubectl get pods -l app.kubernetes.io/instance=lab11-app -o jsonpath='{.items[0].metadata.name}')" -- sh -c 'ls -la /vault/secrets && wc -c /vault/secrets/config'
total 8
drwxrwsrwt 2 root appuser   60 Apr  5 15:25 .
drwxr-xr-x 3 root root    4096 Apr  5 15:25 ..
-rw-r--r-- 1  100 appuser  180 Apr  5 15:25 config
180 /vault/secrets/config
```

The file body stayed inside the cluster; only the path and size were recorded here.

---

## Security Analysis

### Kubernetes Secrets versus Vault

Native Secrets stayed inside the etcd snapshot for the cluster; RBAC and audit were the main guardrails unless encryption at rest was on. Vault moved secrets to a dedicated system with policies, identities, and audit devices; the Injector fetched data through short-lived tokens (via Kubernetes login here) and mounted files so values did not need a second copy in a ConfigMap.

### When each approach fit

Flat manifests and Helm `stringData` were acceptable for dev namespaces with synthetic data. Vault auth and the Agent sidecar suited teams that needed central rotation, many consumers, or separation between cluster admins and secret owners.

### Production-style recommendations

Encryption at rest for Secrets, tight RBAC, no long-lived root tokens outside break-glass storage, and production Raft or cloud-backed Vault mattered beyond coursework. The dev-mode Helm settings from this lab were not production patterns.

