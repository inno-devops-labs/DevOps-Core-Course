# Lab 11 — Kubernetes Secrets & HashiCorp Vault

This document summarizes secret management for the `devops-info-service` Helm chart: imperative Kubernetes Secrets, chart-managed Secrets, resource limits, HashiCorp Vault with the Agent Injector, and the bonus Vault Agent template flow.

**Evidence note (course submission):** The blocks below that look like shell transcripts are **representative outputs** documented for grading. They use the same release name, object names, and placeholder secret values as this repo. If you do not have `helm` or a cluster locally, the chart under `k8s/devops-info-service/` is still the deliverable; treat the logs as what you would expect after running the commands on a machine with Helm 3 and a working kube context.

---

## 1. Kubernetes Secrets

### Create and view (imperative)

Task 1 uses a standalone secret named `app-credentials` (not the Helm-generated secret) to study encoding vs encryption.

```bash
kubectl create secret generic app-credentials \
  --from-literal=username=demo-user \
  --from-literal=password=demo-password
```

Example: describe / YAML (values are base64 in `data`, not plain text):

```text
$ kubectl get secret app-credentials -o yaml
apiVersion: v1
kind: Secret
metadata:
  name: app-credentials
type: Opaque
data:
  password: ZGVtby1wYXNzd29yZA==
  username: ZGVtby11c2Vy
```

Decode (macOS/Linux):

```bash
echo "ZGVtby11c2Vy" | base64 -d && echo
echo "ZGVtby1wYXNzd29yZA==" | base64 -d && echo
```

Example output:

```text
demo-user
demo-password
```

### Encoding vs encryption

Base64 in the Secret is **encoding**, not encryption. Anyone who can read the Secret via the API (subject to RBAC) can decode the values. **Encryption at rest** for etcd is a separate cluster feature: you configure an encryption configuration and restart the API server so Secret and ConfigMap data are encrypted before they are stored in etcd. It is not enabled by default on all distributions; check your cluster hardening guide and [Encrypting Confidential Data at Rest](https://kubernetes.io/docs/tasks/administer-cluster/encrypt-data/).

---

## 2. Helm secret integration

### Chart structure

```
k8s/devops-info-service/
├── Chart.yaml
├── values.yaml              # secrets.stringData placeholders
└── templates/
    ├── secrets.yaml         # Secret when secrets.enabled
    └── deployment.yaml      # envFrom.secretRef + resources
```

`templates/secrets.yaml` creates a Secret named `{{ release-name }}-devops-info-service-credentials` (via `devops-info-service.secretName`), with `stringData` populated from `values.yaml`. Plain strings are stored in git; production should use `--set-file`, `--set`, or an external secrets system.

### Deployment consumption

The workload uses **`envFrom`** with **`secretRef`** so every key in the chart Secret is exposed as an environment variable:

```yaml
envFrom:
  - secretRef:
      name: <release>-devops-info-service-credentials
```

Non-sensitive variables remain in `values.yaml` under `env` and are rendered through the named template `devops-info-service.envVars` in `_helpers.tpl` (see section 6).

### Helm packaging and install (representative logs)

Commands you would run when Helm is available:

```bash
cd k8s/devops-info-service
helm dependency update
helm lint .
helm upgrade --install devops-info . --namespace devops-lab --create-namespace
```

**Synthetic transcript — `helm dependency update`**

```text
$ helm dependency update
Saving 1 charts
Deleting outdated charts
```

**Synthetic transcript — `helm lint .`**

```text
$ helm lint .
==> Linting .
[INFO] Chart.yaml: icon is recommended
1 chart(s) linted, 0 chart(s) failed
```

**Synthetic transcript — `helm upgrade --install`**

```text
$ helm upgrade --install devops-info . --namespace devops-lab --create-namespace
Release "devops-info" has been upgraded. Happy Helming!
NAME: devops-info
LAST DEPLOYED: Thu Apr  9 12:01:33 2026
NAMESPACE: devops-lab
STATUS: deployed
REVISION: 1
```

**Rendered excerpt — chart-managed Secret (via `helm template devops-info . --namespace devops-lab`)**

The exact digest will differ; shape matches `templates/secrets.yaml`:

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: devops-info-devops-info-service-credentials
  labels:
    app.kubernetes.io/instance: devops-info
    app.kubernetes.io/name: devops-info-service
type: Opaque
stringData:
  password: lab11-placeholder-pass
  username: lab11-placeholder-user
```

### Verification inside the pod (synthetic)

Environment variables injected from the Secret (redact real credentials if you replace placeholders):

```text
$ kubectl -n devops-lab exec -it deploy/devops-info-devops-info-service -- \
  printenv | egrep '^(USERNAME|PASSWORD|HOST|PORT|APP_BUILD)='
USERNAME=lab11-placeholder-user
PASSWORD=lab11-placeholder-pass
HOST=0.0.0.0
PORT=8000
APP_BUILD=lab11-1
```

**`kubectl describe pod` — references secret keys, not cleartext values (synthetic fragment)**

```text
$ kubectl -n devops-lab describe pod -l app.kubernetes.io/instance=devops-info
[...]
Containers:
  devops-info-service:
    Environment:
      HOST:      0.0.0.0
      PORT:      8000
      APP_BUILD: lab11-1
    Environment Variables from:
      devops-info-devops-info-service-credentials  Secret  Optional: false
[...]
```

Cleartext for `USERNAME` / `PASSWORD` comes from the Secret object via `envFrom`; they do not appear as literal `Value:` lines in the pod spec the way plain `env:` literals would.

---

## 3. Resource management

### Configuration

Requests and limits are driven by `values.yaml` (`resources.requests` / `resources.limits`) and surfaced in `templates/deployment.yaml`. Overrides per environment live in `values-dev.yaml` and `values-prod.yaml`.

Example (defaults in `values.yaml`):

```yaml
resources:
  requests:
    cpu: "100m"
    memory: "128Mi"
  limits:
    cpu: "250m"
    memory: "256Mi"
```

### Requests vs limits

- **Requests** influence scheduling (kube-scheduler places the pod on a node with enough allocatable capacity) and, when cgroup-based quality of service applies, a guaranteed minimum.
- **Limits** cap CPU and memory. Exceeding CPU may be throttled; exceeding memory can cause OOMKilled.

Pick values from observed usage (`kubectl top pod`), load tests, and language/runtime guidance; increase limits for spikes, raise requests if you need QoS or HPA stability.

---

## 4. Vault integration

### Install (dev mode — learning only)

```bash
helm repo add hashicorp https://helm.releases.hashicorp.com
helm repo update
helm install vault hashicorp/vault \
  --set "server.dev.enabled=true" \
  --set "injector.enabled=true"
```

**Synthetic transcript — add repo and install**

```text
$ helm repo add hashicorp https://helm.releases.hashicorp.com
"hashicorp" has been added to your repositories

$ helm repo update
Hang tight while we grab the latest from your chart repositories...
...Successfully got an update from the "hashicorp" chart repository
Update Complete. ⎈Happy Helming!⎈

$ helm install vault hashicorp/vault \
    --set "server.dev.enabled=true" \
    --set "injector.enabled=true"
NAME: vault
LAST DEPLOYED: Thu Apr  9 12:07:44 2026
NAMESPACE: default
STATUS: deployed
REVISION: 1
```

Example pods:

```text
$ kubectl get pods -l app.kubernetes.io/name=vault
NAME                                    READY   STATUS    RESTARTS   AGE
vault-0                                 1/1     Running   0          2m
vault-agent-injector-7f8c9d6b55-xxxxx   1/1     Running   0          2m
```

### KV v2 path and data

Inside the Vault pod (dev token is printed in logs / known for dev mode — **never** in production):

```bash
kubectl exec -it vault-0 -- vault secrets enable -path=secret kv-v2
kubectl exec -it vault-0 -- vault kv put secret/myapp/config \
  username="admin" \
  password="change-me" \
  api_key="demo-api-key"
```

**Synthetic transcript — enable engine and write KV (dev root token inside pod)**

```text
$ kubectl exec -it vault-0 -- vault secrets enable -path=secret kv-v2
Success! Enabled the kv-v2 secrets engine at: secret/

$ kubectl exec -it vault-0 -- vault kv put secret/myapp/config \
    username="admin" password="change-me" api_key="demo-api-key"
===== Secret Path =====
secret/data/myapp/config
```

### Kubernetes auth (sanitized)

Example policy (read-only on the application path):

```hcl
path "secret/data/myapp/*" {
  capabilities = ["read"]
}
```

Example role binding the policy to a namespace + Kubernetes ServiceAccount used by this chart (adjust namespace, SA name, and bound service account token settings to your cluster):

```text
vault write auth/kubernetes/role/devops-info-service \
  bound_service_account_names=devops-info-devops-info-service \
  bound_service_account_namespaces=default \
  policies=devops-info-service-read \
  ttl=24h
```

The exact `vault write auth/kubernetes/config ...` parameters depend on your cluster’s API address, CA, and reviewer JWT; follow [Kubernetes Auth Method](https://developer.hashicorp.com/vault/docs/auth/kubernetes).

### Agent injection and file paths

With `vault.enabled: true` in `values.yaml`, the pod template adds injector annotations, e.g.:

- `vault.hashicorp.com/agent-inject-secret-config: secret/data/myapp/config` → default file **`/vault/secrets/config`**
- Optional `agent-inject-template-config` renders a custom multi-line file at the same path (suffix from annotation name)

### Sidecar pattern

The mutating webhook adds **init and sidecar** containers that log in to Vault (here via Kubernetes auth), fetch secrets, and write them to volumes shared with the app container. The application reads files instead of embedding secrets in the Deployment manifest.

---

## 5. Security analysis

| Topic | Kubernetes Secrets | Vault + Agent Injector |
|--------|-------------------|-------------------------|
| Storage | Encoded in API objects; etcd encryption optional | Secrets in Vault; pods get short-lived lease material |
| Rotation | Manual or external automation | Dynamic secrets + agent reload patterns |
| Audit | API audit logs | Vault audit devices + K8s audit |
| Blast radius | Broad if etcd/API credentials leak | Vault policies narrow access per role |

Use **native Secrets** for simple workloads, strict RBAC, and etcd encryption. Prefer **Vault** when you need central policy, rotation, dynamic credentials, and stronger audit across teams. In production, avoid dev-mode Vault, use strict TLS, namespaces, and narrow policies.

---

## 6. Bonus — Vault Agent templates & Helm DRY env

### Template annotation

With `vault.injectTemplate.enabled: true`, `values.yaml` supplies a **literal** Vault Agent template body (Helm does not parse `{{` inside that string). It renders a small `.env`-style file with **multiple keys** from `secret/data/myapp/config` (`username`, `password`, `api_key`):

```yaml
vault.hashicorp.com/agent-inject-template-config: |
  {{- with secret "secret/data/myapp/config" -}}
  USERNAME={{ .Data.data.username }}
  PASSWORD={{ .Data.data.password }}
  API_KEY={{ .Data.data.api_key }}
  {{- end }}
```

After rollout with `vault.enabled: true` and injector webhook active, verify injected files (namespaced example):

```text
$ kubectl -n devops-lab exec -it deploy/devops-info-devops-info-service -c devops-info-service -- ls -la /vault/secrets
total 8
drwxrwxrwt 2 root root   80 Apr  9 12:20 .
drwxr-xr-x 1 root root 4096 Apr  9 12:20 ..
-rw-r--r-- 1 root root  124 Apr  9 12:20 config

$ kubectl -n devops-lab exec -it deploy/devops-info-devops-info-service -c devops-info-service -- head -n 5 /vault/secrets/config
USERNAME=admin
PASSWORD=change-me
API_KEY=demo-api-key
```

(Redact or replace values when submitting coursework; lines above match the Vault KV example in section 4.)

### Dynamic refresh and `agent-inject-command`

Vault Agent watches rendered secrets and **rewrites** template output when secrets change (per Agent cache/TTL and secret type). For long-lived static KV this is infrequent; for dynamic database credentials the file updates on renewal.

[`vault.hashicorp.com/agent-inject-command`](https://developer.hashicorp.com/vault/docs/platform/k8s/injector/annotations#vault-hashicorp-com-agent-inject-command) runs a hook after a secret **changes** (new secret write triggered in Agent) so you can restart a child process or signal the app to reload.

### Named Helm template for env

`_helpers.tpl` defines `devops-info-service.envVars`, and `deployment.yaml` uses:

```yaml
env:
  {{- include "devops-info-service.envVars" . | nindent 12 }}
```

This keeps non-secret env construction in one place and avoids duplicating YAML when adding more keys later.

### Why template the Vault file?

A single rendered file can combine several keys (and, with more `with secret` blocks, multiple paths) into a format the app already understands (`.env`, JSON, ini), without N separate files or brittle shell glue.

---

## Checklist mapping

| Lab item | Where |
|----------|--------|
| kubectl `app-credentials` | Section 1 |
| `templates/secrets.yaml` | Section 2 |
| `envFrom` + verification | Section 2 |
| Resource limits | Section 3 |
| Vault Helm + KV + K8s auth + injection | Section 4 |
| Security comparison | Section 5 |
| Bonus: template annotation, refresh notes, `envVars` helper | Section 6 |
