# Lab 11 Report — Kubernetes Secrets & HashiCorp Vault

Note: the lab handout asks for `k8s/SECRETS.md`, but this report is stored as `k8s/LAB11.md` by request. The old `SECRETS.md` file now only points here.

## 1. Overview

Lab 11 extends the Helm chart from Lab 10 with two secret-management approaches:

- native Kubernetes Secrets for simple application-level secret injection
- HashiCorp Vault for centralized secret storage and file-based sidecar injection

The final implementation supports both modes:

- revision 1 of the `lab11-devops-info` release used Helm-managed Kubernetes Secrets
- revision 2 upgraded the same release to Vault injection using a dedicated service account and Vault Agent sidecar

Relevant files:

```text
k8s/
├── LAB11.md
├── SECRETS.md
├── devops-info/
│   ├── values.yaml
│   ├── values-dev.yaml
│   ├── values-prod.yaml
│   ├── values-vault.yaml
│   └── templates/
│       ├── _helpers.tpl
│       ├── deployment.yaml
│       ├── secrets.yaml
│       ├── service.yaml
│       └── serviceaccount.yaml
└── vault/
    ├── configure-dev-vault.sh
    ├── dev-values.yaml
    └── devops-info-policy.hcl
```

## 2. Task 1 — Kubernetes Secrets Fundamentals

### 2.1 Secret creation with `kubectl`

The first task required an imperative Secret named `app-credentials` with `username` and `password` keys. I created it in the dedicated `lab11` namespace:

```bash
$ kubectl create namespace lab11
namespace/lab11 created

$ kubectl -n lab11 create secret generic app-credentials \
    --from-literal=username=lab11-user \
    --from-literal=password=lab11-password
secret/app-credentials created
```

This uses the imperative `kubectl create secret generic` workflow exactly as requested in the lab.

### 2.2 Viewing the Secret in YAML

The Secret contents in Kubernetes are stored under the `data` field:

```yaml
$ kubectl -n lab11 get secret app-credentials -o yaml
apiVersion: v1
data:
  password: bGFiMTEtcGFzc3dvcmQ=
  username: bGFiMTEtdXNlcg==
kind: Secret
metadata:
  creationTimestamp: "2026-04-09T19:14:33Z"
  name: app-credentials
  namespace: lab11
  resourceVersion: "76906"
  uid: 005e75d7-485e-4fc0-b239-fbdfe968485e
type: Opaque
```

### 2.3 Decoding the base64 values

The lab explicitly asks to decode the values and explain what this means:

```bash
$ kubectl -n lab11 get secret app-credentials -o jsonpath='{.data.username}' | base64 --decode
lab11-user

$ kubectl -n lab11 get secret app-credentials -o jsonpath='{.data.password}' | base64 --decode
lab11-password
```

### 2.4 Encoding vs encryption

This is the key explanation for Task 1:

- base64 is an encoding, not encryption
- encoding changes representation so data can be safely stored in YAML/JSON
- encryption protects confidentiality and requires a key to decrypt

For example:

- `lab11-user` became `bGFiMTEtdXNlcg==`
- `lab11-password` became `bGFiMTEtcGFzc3dvcmQ=`

Anyone who can read the Secret object can decode those values immediately. That means Kubernetes Secrets are convenient API objects, but base64 alone is not a security boundary.

### 2.5 Are Kubernetes Secrets encrypted at rest by default?

Not in the way production environments need. By default, Kubernetes Secrets are only base64-encoded in the API object. If etcd encryption at rest is not enabled on the cluster, Secret values can still end up stored in plaintext form inside etcd.

That is why production clusters should not rely on “Secret” as meaning “secure by default”.

### 2.6 What etcd encryption is and when to enable it

etcd encryption at rest means the Kubernetes API server encrypts sensitive resources, such as Secrets, before writing them into etcd.

It should be enabled when:

- the cluster stores passwords, tokens, certificates, or API keys
- backups or etcd snapshots must not expose plaintext credentials
- the cluster is shared across teams
- the environment has security or compliance requirements

In practice, etcd encryption should be considered a standard production control.

### 2.7 Security implications of native Kubernetes Secrets

Native Secrets are acceptable for simple workloads, but they still require other controls:

- RBAC to restrict who can read Secret objects
- least-privilege service accounts
- etcd encryption at rest
- Git hygiene so real secrets are never committed into `values.yaml`

That leads into Task 2, where the Secret is managed by Helm but still kept out of source control as a real value.

## 3. Task 2 — Helm-Managed Secrets

### 3.1 Goal of the Helm integration

Task 2 asks for the Lab 10 chart to be extended so it can:

- create a Secret template
- consume that Secret inside the Deployment
- verify secret injection
- keep resource requests and limits configurable

The `devops-info` chart now does all of that.

### 3.2 Secret template implementation

The new file `k8s/devops-info/templates/secrets.yaml` creates the Secret:

```yaml
{{- if and .Values.secret.enabled .Values.secret.create }}
apiVersion: v1
kind: Secret
metadata:
  name: {{ include "devops-info.secretName" . }}
  labels:
    {{- include "common.labels" . | nindent 4 }}
type: {{ .Values.secret.type }}
stringData:
  {{- range $key, $value := .Values.secret.stringData }}
  {{ $key }}: {{ $value | quote }}
  {{- end }}
{{- end }}
```

Why this design is correct:

- it uses the standard `v1` `Secret` resource
- the name is templated instead of hardcoded
- the chart reuses shared labels
- `stringData` is used so plain text values can be provided and Kubernetes will encode them automatically

### 3.3 Secret values in `values.yaml`

The chart stores only placeholder defaults, never real credentials:

```yaml
secret:
  enabled: true
  create: true
  name: ""
  type: Opaque
  injectAsEnvFrom: true
  stringData:
    username: placeholder-user
    password: placeholder-password
```

This matches the lab requirement and good security practice:

- placeholders are safe to keep in Git
- real values are supplied at install or upgrade time via `--set` or an external system such as Vault

### 3.4 How the Deployment consumes the Secret

The Deployment imports all Secret keys through `envFrom.secretRef`:

```yaml
env:
  {{- include "devops-info.envVars" . | nindent 12 }}
envFrom:
  - secretRef:
      name: {{ include "devops-info.secretName" . }}
```

This means:

- normal non-secret variables still come from `.Values.env`
- secret keys become environment variables inside the container automatically
- the chart stays DRY because the common env list is rendered through the named template `devops-info.envVars`

### 3.5 Secret-based release install

The first `lab11` release was installed in Secret mode:

```bash
$ helm upgrade --install lab11-devops-info ./k8s/devops-info \
    -n lab11 \
    -f ./k8s/devops-info/values-dev.yaml \
    --set secret.stringData.username=lab11-user \
    --set secret.stringData.password=lab11-password \
    --set service.nodePort=30084
```

That became revision 1 of the release:

```bash
$ helm history lab11-devops-info -n lab11
REVISION   UPDATED                  STATUS      CHART             APP VERSION   DESCRIPTION
1          Thu Apr  9 22:15:11 2026 superseded  devops-info-0.1.0 lab2          Install complete
2          Thu Apr  9 22:38:52 2026 deployed    devops-info-0.1.0 lab2          Upgrade complete
```

Revision 2 is the later Vault upgrade from Task 3. That is why the current live Pod no longer uses `envFrom`.

### 3.6 Verification of secret injection

The lab requires proof that the secret reached the Pod and that values are not printed by `kubectl describe`.

Recorded verification from the Secret-based revision:

```text
Environment Variables from:
  lab11-devops-info-secret  Secret  Optional: false
Environment:
  HOST:          0.0.0.0
  PORT:          5002
  APP_ENV:       helm-dev
  APP_REVISION:  dev-v1
```

Why this matters:

- `kubectl describe pod` shows the Secret reference
- it does not print the actual `username` and `password` values
- that is the expected safe behavior for Kubernetes Secret references

In-pod verification for the Secret-based revision also confirmed the env vars existed. The values are redacted here as requested by the lab:

```bash
$ kubectl exec -n lab11 deployment/lab11-devops-info -- printenv | grep -E '^(username|password)='
username=<redacted>
password=<redacted>
```

### 3.7 Resource limits and requests

The lab also asks to configure resources via values.

Development values in `values-dev.yaml`:

```yaml
resources:
  requests:
    cpu: 50m
    memory: 64Mi
  limits:
    cpu: 100m
    memory: 128Mi
```

Production-style values in `values-prod.yaml`:

```yaml
resources:
  requests:
    cpu: 200m
    memory: 256Mi
  limits:
    cpu: 500m
    memory: 512Mi
```

Explanation:

- requests are the minimum resources the scheduler uses to place the Pod
- limits are the maximum resources the container may consume

How to choose appropriate values:

- start from real usage measurements
- set requests close to normal operating usage
- set limits high enough for bursts but low enough to protect the node
- adjust over time using metrics rather than guesswork

For this Flask service, the development values are intentionally small because the workload is lightweight and mainly serves JSON responses and health endpoints.

## 4. Task 3 — HashiCorp Vault Integration

### 4.1 Why Vault was added

Kubernetes Secrets are fine for basic cases, but Vault gives stronger centralized secret management:

- one place to store and control secret access
- explicit read policies
- Kubernetes-authenticated workloads
- agent-based file rendering instead of embedding secrets in Git or static Pod specs

### 4.2 Vault installation via Helm

The lab required Vault to be installed through Helm in dev mode.

Repository setup and install:

```bash
$ helm repo add hashicorp https://helm.releases.hashicorp.com
$ helm repo update

$ helm upgrade --install vault hashicorp/vault \
    -n vault \
    --create-namespace \
    -f ./k8s/vault/dev-values.yaml
```

The values file `k8s/vault/dev-values.yaml` enables:

- Vault server dev mode
- Vault Agent Injector
- Vault UI

Current live verification:

```bash
$ kubectl get pods -n vault
NAME                                   READY   STATUS    RESTARTS   AGE
vault-0                                1/1     Running   0          5d16h
vault-agent-injector-8c76487db-5htj2   1/1     Running   0          5d16h
```

This satisfies the installation and “verify pods are running” requirement.

### 4.3 Configuring Vault: KV engine and application secret

The application secret is stored in Vault at:

```text
secret/data/devops-info/config
```

The automation for this is in `k8s/vault/configure-dev-vault.sh`. It performs these steps:

1. ensures the KV v2 engine exists at `secret/`
2. writes the application secret values
3. enables Kubernetes auth if needed
4. configures Vault to talk to the in-cluster Kubernetes API
5. uploads the policy
6. creates the role bound to the application service account

Live check of the stored Vault secret:

```bash
$ kubectl exec -n vault vault-0 -- \
    env VAULT_ADDR=http://127.0.0.1:8200 VAULT_TOKEN=root \
    vault kv get secret/devops-info/config

========= Secret Path =========
secret/data/devops-info/config

====== Data ======
Key         Value
---         -----
password    vault-password
username    vault-user
```

### 4.4 Kubernetes authentication in Vault

The chart uses a dedicated service account in Vault mode:

```yaml
serviceAccount:
  create: true
  name: devops-info-vault
```

The policy is intentionally minimal:

```hcl
path "secret/data/devops-info/config" {
  capabilities = ["read"]
}
```

The role binds that policy to the application workload:

```bash
vault write auth/kubernetes/role/devops-info-role \
  bound_service_account_names="devops-info-vault" \
  bound_service_account_namespaces="lab11" \
  policies="devops-info" \
  ttl="24h"
```

Why this is correct:

- the app only gets read access to one path
- the role only applies to one service account
- the scope is limited to the `lab11` namespace

That is least-privilege access and is much better than giving broad cluster-wide secret access.

### 4.5 Vault annotations in the Deployment

The Deployment switches into Vault mode through `values-vault.yaml`, which disables the Helm Secret path and enables Vault annotations:

```yaml
secret:
  enabled: false
  create: false
  injectAsEnvFrom: false

serviceAccount:
  create: true
  name: devops-info-vault

vault:
  enabled: true
  authPath: auth/kubernetes
  role: devops-info-role
  secretPath: secret/data/devops-info/config
  fileName: app-config.txt
```

The final annotation block rendered into the Pod template is:

```yaml
vault.hashicorp.com/agent-inject: "true"
vault.hashicorp.com/agent-pre-populate-only: "false"
vault.hashicorp.com/auth-path: "auth/kubernetes"
vault.hashicorp.com/role: "devops-info-role"
vault.hashicorp.com/agent-inject-secret-app-config.txt: "secret/data/devops-info/config"
vault.hashicorp.com/agent-inject-template-app-config.txt: |
  {{- with secret "secret/data/devops-info/config" -}}
  username={{ .Data.data.username }}
  password={{ .Data.data.password }}
  {{- end -}}
```

### 4.6 Live verification of Vault injection

The current application Pod is in Vault mode:

```bash
$ kubectl get pods -n lab11
NAME                                 READY   STATUS    RESTARTS   AGE
lab11-devops-info-745c549cd6-hrx4h   2/2     Running   0          5d16h
```

The current Pod description proves the injector mutated the workload:

```text
Service Account:  devops-info-vault
Annotations:
  vault.hashicorp.com/agent-inject: true
  vault.hashicorp.com/agent-inject-secret-app-config.txt: secret/data/devops-info/config
  vault.hashicorp.com/agent-inject-status: injected
  vault.hashicorp.com/agent-pre-populate-only: false
  vault.hashicorp.com/auth-path: auth/kubernetes
  vault.hashicorp.com/role: devops-info-role

Init Containers:
  vault-agent-init: Completed

Containers:
  devops-info: Running
  vault-agent: Running
```

That shows the full sidecar-injection pattern working:

- an init container authenticates and renders the initial secret file
- the application container runs normally
- the `vault-agent` sidecar remains running to manage ongoing secret rendering

### 4.7 Proof that secrets are available in the Pod

The lab asks for proof that the secret is available at the expected path. Current live output:

```bash
$ kubectl exec -n lab11 deployment/lab11-devops-info -c devops-info -- \
    sh -c 'ls -l /vault/secrets && printf "\n---\n" && cat /vault/secrets/app-config.txt'
total 4
-rw-r--r-- 1 100 appgroup 43 Apr  9 19:44 app-config.txt

---
username=vault-user
password=vault-password
```

This satisfies the injection requirement directly.

### 4.8 Explanation of the sidecar injection pattern

The sidecar injection pattern works like this:

1. the Vault injector mutates the Pod at admission time
2. an init container authenticates to Vault
3. the init container renders the requested template to a shared volume
4. the main app reads the rendered file from `/vault/secrets`
5. a long-running Vault Agent sidecar can keep templates refreshed

Why this is useful:

- the application manifest does not hardcode real secret values
- secrets do not need to live in Git
- the app gets a file on disk instead of a static Secret object in Kubernetes
- policy and access control are centralized in Vault

## 5. Task 4 — Required Documentation Topics

The lab’s documentation task asked for specific explanations. This section maps directly to them.

### 5.1 Kubernetes Secrets

Included in this report:

- output of Secret creation
- YAML view of the Secret
- decoded values
- explanation of base64 encoding vs encryption

### 5.2 Helm Secret integration

Included in this report:

- chart structure showing `templates/secrets.yaml`
- explanation of how the Secret is consumed by `envFrom.secretRef`
- verification output showing the Pod referenced the Secret without exposing values

### 5.3 Resource management

Included in this report:

- development and production resource configurations
- explanation of requests vs limits
- rationale for choosing those values

### 5.4 Vault integration

Included in this report:

- Vault installation evidence
- policy and role explanation
- proof of injected secret file and location
- explanation of the sidecar injection model

## 6. Security Analysis

### 6.1 Kubernetes Secrets vs Vault

| Topic | Kubernetes Secrets | Vault |
|---|---|---|
| Storage location | Kubernetes API / etcd | External secret-management system |
| Default protection | Base64 only unless extra controls are enabled | Policy-driven, centrally managed access |
| Operational overhead | Low | Higher |
| Best fit | Simple apps and small clusters | Sensitive, multi-team, or compliance-heavy environments |
| Rotation model | Usually manual or external tooling | Better support for managed rotation and re-rendering |

### 6.2 When to use Kubernetes Secrets

Kubernetes Secrets are a good fit when:

- the environment is small and simple
- there are only a few secrets
- secret rotation is infrequent
- operational simplicity matters more than advanced secret-management features

They still need supporting controls such as RBAC and etcd encryption.

### 6.3 When to use Vault

Vault is a better fit when:

- secrets must be centrally governed
- workloads span multiple teams or clusters
- access policy needs to be explicit and auditable
- secret rotation matters
- secrets should be rendered as files instead of injected as plain environment variables

### 6.4 Production recommendations

- never commit real secret values to Git
- enable etcd encryption at rest
- use least-privilege RBAC and service accounts
- avoid Vault dev mode outside lab environments
- prefer external secret managers for high-value credentials
- reload applications cleanly when rendered secret files change

## 7. Bonus — Vault Agent Templates

### 7.1 Template annotation implementation

The bonus task required `vault.hashicorp.com/agent-inject-template-*`. This is implemented in the Deployment template:

```yaml
vault.hashicorp.com/agent-inject-template-app-config.txt: |
  {{- with secret "secret/data/devops-info/config" -}}
  username={{ .Data.data.username }}
  password={{ .Data.data.password }}
  {{- end -}}
```

This renders multiple secrets into one file, which satisfies the bonus requirement.

### 7.2 Rendered custom-format file

The resulting file is effectively a simple `.env`-style config file:

```text
username=vault-user
password=vault-password
```

That is a practical format because it is easy for an entrypoint script or application to parse.

### 7.3 Dynamic secret rotation explanation

Because `agent-pre-populate-only` is set to `false`, the `vault-agent` sidecar stays alive after the Pod starts.

That matters because:

- the agent can continue watching and re-rendering templates
- secret updates can be written back into the mounted file
- the application can pick them up if it supports rereading or reloading configuration

Rotation is not magic: the file can refresh, but the app still needs a reload strategy if it only reads config once at startup.

### 7.4 `agent-inject-command` explanation

The lab asks to explain `vault.hashicorp.com/agent-inject-command`.

This annotation lets Vault Agent run a command after a rendered file changes. Typical uses:

- send `SIGHUP` to reload an application
- call a small wrapper script
- regenerate derived config after secret updates

The chart now supports this through `vault.injectCommand` in `values.yaml` and `values-vault.yaml`, although it is currently left empty by default:

```yaml
vault:
  injectCommand: ""
```

This keeps the feature available without forcing a reload command for every deployment.

### 7.5 Named template implementation in `_helpers.tpl`

The bonus also asked for a named template for environment variables. That is implemented here:

```yaml
{{- define "devops-info.envVars" -}}
{{- toYaml .Values.env -}}
{{- end }}
```

And used in the Deployment like this:

```yaml
env:
  {{- include "devops-info.envVars" . | nindent 12 }}
```

Benefits of this approach:

- cleaner Deployment template
- reusable env rendering logic
- easier future extension
- explicit DRY principle in the Helm chart

## 8. Final Result

Lab 11 is fully implemented and documented.

Completed required work:

- Task 1: native Secret created, viewed, decoded, and explained
- Task 2: Helm-managed Secret templated, consumed, and explained
- Task 3: Vault installed, configured, authenticated, and verified live
- Task 4: full report written with all explanations requested in `labs/lab11.md`

Completed bonus work:

- Vault Agent template annotation
- rendered multi-key config file
- named Helm env template
- explanation of rotation and `agent-inject-command`

Current live state:

```bash
$ kubectl get pods -n lab11
NAME                                 READY   STATUS    RESTARTS   AGE
lab11-devops-info-745c549cd6-hrx4h   2/2     Running   0          5d16h

$ kubectl get pods -n vault
NAME                                   READY   STATUS    RESTARTS   AGE
vault-0                                1/1     Running   0          5d16h
vault-agent-injector-8c76487db-5htj2   1/1     Running   0          5d16h
```
