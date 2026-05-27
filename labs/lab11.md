# Lab 11 — Kubernetes Secrets & OpenBao

![difficulty](https://img.shields.io/badge/difficulty-intermediate-yellow)
![topic](https://img.shields.io/badge/topic-Secret%20Management-blue)
![points](https://img.shields.io/badge/points-10%2B2-orange)
![tech](https://img.shields.io/badge/tech-OpenBao%202.5%20%7C%20K8s%20Secrets-informational)

> Stop putting passwords in Git. Secure your Kubernetes applications with native Secrets, Helm-managed secrets, and an **OpenBao** secret manager — the open-source successor to HashiCorp Vault.

## Overview

Secret management is critical for production Kubernetes. Hardcoded credentials in code, config files, or `values.yaml` are the single cheapest-to-prevent cause of cloud breaches. This lab teaches you the real security model behind Kubernetes Secrets (base64 is **not** encryption) and how to centralize secrets with **OpenBao**.

**What You'll Learn:**
- Kubernetes Secrets creation and consumption (env vars + file mounts)
- Why base64 encoding is not encryption, and what etcd encryption-at-rest is
- Helm-based secret management and resource limits
- Deploying **OpenBao 2.5** in Kubernetes via Helm
- Kubernetes auth method + KV-v2 + read policy + role binding
- Injecting secrets into pods via the OpenBao Agent sidecar pattern

**Building On:** Your Helm chart from Lab 10 is extended with secret management.

> **Why OpenBao, not Vault?** In August 2023 HashiCorp re-licensed Vault under the Business Source License (BSL 1.1), restricting commercial use. The community forked it as **OpenBao**, now governed by the Linux Foundation under the truly open MPL-2.0 license. OpenBao is wire-compatible: the `bao` CLI is a drop-in for `vault`, and the legacy `vault` CLI still works unchanged against an OpenBao server. We teach OpenBao so the manifests you build today run on a production cluster tomorrow without a license re-litigation.

**Tech Stack:** Kubernetes **1.36** | **OpenBao 2.5.0** (Linux Foundation, MPL-2.0) | OpenBao Helm chart | Helm **4** | `bao` CLI (`vault` CLI also compatible) | External Secrets Operator (bonus)

---

## Tasks

> **Note on outputs:** All command outputs shown below are **illustrative** — your hashes, pod names, and timestamps will differ. Capture *your own* real output for the documentation task.

### Task 1 — Kubernetes Secrets Fundamentals (2 pts)

**Objective:** Understand how Kubernetes Secrets actually work and their security model. This task is standalone — it does not depend on your Lab 10 chart.

**Requirements:**

1. **Create a Secret Using kubectl**
   - Create a namespace `lab11` (`kubectl create namespace lab11`).
   - Create a secret named `app-credentials` in `lab11` with a `username` key and a `password` key.
   - Use the imperative `kubectl create secret generic` command with `--from-literal`.

2. **Examine the Secret**
   - View the secret in YAML format.
   - Decode the base64-encoded values back to plaintext.
   - Demonstrate in writing the difference between **encoding** (base64) and **encryption**.

3. **Understand Security Implications**
   - Answer in your docs: Are Kubernetes Secrets encrypted at rest by default? (No — they are base64 in etcd.)
   - Explain what an `EncryptionConfiguration` / KMS provider does and when you should enable etcd encryption-at-rest.
   - Note that RBAC protects the API *path*, not the data at rest.

<details>
<summary>💡 Hints</summary>

**Creating Secrets (three patterns):**
- `kubectl create secret generic` — from literals or files (imperative)
- A `kind: Secret` YAML manifest (declarative)
- A Helm `templates/secrets.yaml` (Task 2)

**Useful Commands (illustrative output):**
```bash
kubectl create namespace lab11

kubectl create secret generic app-credentials -n lab11 \
  --from-literal=username=admin \
  --from-literal=password='S3cure!2026'

# View the stored object — values are base64, not encrypted
kubectl get secret app-credentials -n lab11 -o yaml
# data:
#   password: UzNjdXJlITIwMjY=
#   username: YWRtaW4=

# Decode — no key, no password, just decode
echo "YWRtaW4=" | base64 -d        # -> admin
echo "UzNjdXJlITIwMjY=" | base64 -d  # -> S3cure!2026
```

**Encoding vs Encryption:**

| base64 (encoding) | AES-GCM / KMS (encryption) |
|-------------------|----------------------------|
| Reversible by anyone with the string | Requires a key to decrypt |
| For binary-safe text transport | For confidentiality |
| Same data, different format | Mathematically secure |

Secrets are base64 because `data` values must be valid string-safe YAML/JSON (binary like a TLS key wouldn't fit). Confidentiality is the job of RBAC + etcd-at-rest, not base64.

**etcd encryption-at-rest** is enabled with a kube-apiserver `--encryption-provider-config` pointing at an `EncryptionConfiguration` (prefer a `kms` provider; the `identity` provider, meaning no encryption, must be last). On managed control planes (EKS/GKE/AKS) disk-level provider encryption is often on, but that is a different threat model than K8s-level `EncryptionConfiguration`.

**Resources:**
- [Kubernetes Secrets Concepts](https://kubernetes.io/docs/concepts/configuration/secret/)
- [Encrypting Secret Data at Rest](https://kubernetes.io/docs/tasks/administer-cluster/encrypt-data/)

</details>

---

### Task 2 — Helm-Managed Secrets (3 pts)

**Objective:** Integrate secrets into your Lab 10 Helm chart and inject them into your application as environment variables.

**Requirements:**

1. **Create a Secret Template**
   - Add `templates/secrets.yaml` to your Helm chart.
   - Define placeholder secret values in `values.yaml` (never commit real secrets).
   - Use templated name and standard labels.

2. **Inject Secrets as Environment Variables**
   - Update your Deployment to consume the secret via `envFrom` + `secretRef` (all keys), or individual `env` + `secretKeyRef`.

3. **Verify Secret Injection**
   - Deploy the updated chart with Helm 4.
   - Exec into the pod and confirm the environment variables exist.
   - Confirm the secret *values* are not exposed by `kubectl describe pod`.

4. **Add Resource Limits**
   - Configure CPU and memory `requests`/`limits` in your Deployment, driven from `values.yaml`.

**Skeleton — `templates/secrets.yaml` (fill in the YOUR-TASK markers):**
```yaml
apiVersion: v1
kind: Secret
metadata:
  name: {{ include "mychart.fullname" . }}-secret   # YOUR-TASK: match your chart's helper name
  labels:
    {{- include "mychart.labels" . | nindent 4 }}
type: Opaque
stringData:                                          # stringData: Helm/K8s base64-encodes for you
  # YOUR-TASK: reference placeholder values from values.yaml, e.g.:
  # username: {{ .Values.appSecret.username | quote }}
  # password: {{ .Values.appSecret.password | quote }}
```

<details>
<summary>💡 Hints</summary>

**`values.yaml` placeholders (never real values):**
```yaml
appSecret:
  username: "PLACEHOLDER_USER"
  password: "PLACEHOLDER_PASS"   # override with --set or a secret manager at deploy time
```

**Consuming the secret — Pattern 1 (all keys):**
```yaml
envFrom:
  - secretRef:
      name: {{ include "mychart.fullname" . }}-secret
```

**Pattern 2 (specific keys):**
```yaml
env:
  - name: DATABASE_PASSWORD
    valueFrom:
      secretKeyRef:
        name: {{ include "mychart.fullname" . }}-secret
        key: password
```

**Resource limits (from values.yaml):**
```yaml
resources:
  requests: {memory: "64Mi", cpu: "100m"}
  limits:   {memory: "128Mi", cpu: "200m"}
```

**Deploy + verify (illustrative):**
```bash
helm upgrade --install mychart ./mychart -n lab11 \
  --set appSecret.password='S3cure!2026'

kubectl exec -n lab11 deploy/mychart -- env | grep -i pass   # shows the var exists
kubectl describe pod -n lab11 -l app=mychart                 # values NOT shown
```

**Never** put real values in `values.yaml` — that file ships to Git with your chart. Use `--set` for the lab and a secret manager (Task 3) for real deployments.

**Resources:**
- [Managing Secrets with kubectl](https://kubernetes.io/docs/tasks/configmap-secret/managing-secret-using-kubectl/)
- [Resource Management](https://kubernetes.io/docs/concepts/configuration/manage-resources-containers/)
- [Helm 4 docs](https://helm.sh/docs/)

</details>

---

### Task 3 — OpenBao Integration (3 pts)

**Objective:** Deploy **OpenBao 2.5** and configure it to inject a secret into your application via the Agent sidecar pattern.

**Requirements:**

1. **Install OpenBao via Helm**
   - Add the OpenBao Helm repository.
   - Install OpenBao in **dev mode** (learning only — unsealed, in-memory) with the Agent injector enabled.
   - Verify the OpenBao server pod and the agent-injector pod are `Running`.

2. **Configure OpenBao**
   - Enable the KV-v2 secrets engine at path `secret`.
   - Write a secret at `secret/lab11/db` with at least two key-value pairs.

3. **Configure Kubernetes Authentication**
   - Enable the `kubernetes` auth method.
   - Write a policy granting **read** on your secret path.
   - Create a role binding that policy to a ServiceAccount (`lab11-sa`) in namespace `lab11`.

4. **Enable Agent Injection**
   - Add OpenBao Agent annotations to your Deployment's pod template.
   - Set `serviceAccountName: lab11-sa`.
   - Verify the rendered secret file appears at `/vault/secrets/...` inside the pod.

**Skeleton — Agent annotations on your Deployment (fill in the YOUR-TASK markers):**
```yaml
spec:
  template:
    metadata:
      annotations:
        vault.hashicorp.com/agent-inject: "true"
        vault.hashicorp.com/role: "lab11"                 # YOUR-TASK: the role you create below
        # YOUR-TASK: source path -> file at /vault/secrets/db
        vault.hashicorp.com/agent-inject-secret-db: "secret/data/lab11/db"
    spec:
      serviceAccountName: lab11-sa
      containers:
        - name: app
          # ... your container ...
```

> **Annotation prefix note:** OpenBao's Agent injector keeps the `vault.hashicorp.com/*` annotation keys for drop-in compatibility with existing Vault tooling, and renders files under `/vault/secrets/`. This is expected — OpenBao deliberately preserved the wire/annotation contract.

<details>
<summary>💡 Hints</summary>

**Install OpenBao (illustrative output):**
```bash
helm repo add openbao https://openbao.github.io/openbao-helm
helm repo update

helm install openbao openbao/openbao \
  --namespace openbao --create-namespace \
  --set "server.dev.enabled=true" \      # dev mode = unsealed + in-memory, NEVER prod
  --set "injector.enabled=true" \        # deploy the Agent injector
  --set "server.image.tag=2.5.0"

kubectl get pods -n openbao
# NAME                                READY   STATUS
# openbao-0                           1/1     Running
# openbao-agent-injector-7f...        1/1     Running
```

**Configure OpenBao (exec into the server pod).** The `bao` CLI is primary; `vault` is an accepted alias on the same binary:
```bash
kubectl exec -n openbao -it openbao-0 -- /bin/sh

# Enable KV v2 (versioned static secrets)
bao secrets enable -path=secret kv-v2

# Write a secret (>= 2 keys)
bao kv put secret/lab11/db username=app password='S3cure!2026'

# Enable Kubernetes auth (validates a pod's ServiceAccount JWT via TokenReview)
bao auth enable kubernetes
bao write auth/kubernetes/config \
  kubernetes_host="https://$KUBERNETES_PORT_443_TCP_ADDR:443"

# Read-only policy on the exact data path
bao policy write lab11-read - <<EOF
path "secret/data/lab11/db" {
  capabilities = ["read"]
}
EOF

# Role tying SA + namespace + policy together
bao write auth/kubernetes/role/lab11 \
  bound_service_account_names=lab11-sa \
  bound_service_account_namespaces=lab11 \
  policies=lab11-read \
  ttl=1h
```

> The legacy `vault` command works too: `vault status`, `vault kv put ...`, etc. all run unchanged against OpenBao.

**Create the ServiceAccount** (declarative, in `lab11`):
```bash
kubectl create serviceaccount lab11-sa -n lab11
```

**How injection works:** the injector is a `MutatingAdmissionWebhook` that, when it sees the `agent-inject` annotation, patches your podspec with an init container (fetches the secret before your app boots) and a sidecar (renews the token, refreshes the file). The file lands on a shared `emptyDir` at `/vault/secrets/<name>`.

**Verify (illustrative):**
```bash
kubectl exec -n lab11 deploy/mychart -c app -- cat /vault/secrets/db
# data: map[password:S3cure!2026 username:app]
# metadata: ...
```

**Resources:**
- [OpenBao docs](https://openbao.org/docs/)
- [OpenBao Helm chart](https://github.com/openbao/openbao-helm)
- [OpenBao Kubernetes auth](https://openbao.org/docs/auth/kubernetes/)
- [Vault Agent annotations reference (applies to OpenBao injector)](https://developer.hashicorp.com/vault/docs/platform/k8s/injector/annotations)

</details>

---

### Task 4 — Documentation (2 pts)

**Objective:** Document your secret management implementation with real evidence.

**Create `k8s/SECRETS.md` with:**

1. **Kubernetes Secrets**
   - Your real output of creating and viewing `app-credentials`.
   - The decoded values demonstration.
   - Your explanation of base64 encoding vs encryption.

2. **Helm Secret Integration**
   - Chart structure showing `templates/secrets.yaml`.
   - How the secret is consumed in the Deployment.
   - Verification output (env vars present in the pod — redact the actual values).

3. **Resource Management**
   - Your `requests`/`limits` configuration.
   - Explanation of requests vs limits and how to choose values.

4. **OpenBao Integration**
   - Installation verification (`kubectl get pods -n openbao`).
   - Policy and role configuration (sanitized).
   - Proof of injection (the `/vault/secrets/...` file exists — redact the secret value).
   - Explanation of the Agent sidecar injection pattern.

5. **Security Analysis**
   - Comparison: native K8s Secrets vs OpenBao.
   - When to use each approach.
   - One paragraph on the Vault → OpenBao licensing history (BSL 1.1, Aug 2023) and why it matters.
   - Production recommendations (no dev mode, integrated Raft storage, auto-unseal, audit device, TLS, least-privilege roles).

---

## Bonus Task — Choose ONE (2 pts)

Pick **one** of the two tracks below. Both are worth the full 2 points; do not do both.

### Option A — OpenBao Agent Templating

**Objective:** Render injected secrets in a custom format and wire up reload-on-rotation.

**Requirements:**

1. **Custom Template Annotation**
   - Use `vault.hashicorp.com/agent-inject-template-*` to render `secret/data/lab11/db` as a `.env`-style file containing **multiple** keys.

2. **Reload Mechanism**
   - Add `vault.hashicorp.com/agent-inject-command-*` to signal your app to reload after a re-render.
   - Document, in your own words, how the Agent re-renders on rotation.

3. **Named Helm Template (DRY)**
   - Add a named template in `_helpers.tpl` for shared environment variables and `include` it in your Deployment.

**Skeleton (fill in the YOUR-TASK markers):**
```yaml
vault.hashicorp.com/agent-inject-template-db: |
  {{`{{- with secret "secret/data/lab11/db" -}}`}}
  DB_USER={{`{{ .Data.data.username }}`}}
  DB_PASS={{`{{ .Data.data.password }}`}}
  {{`{{- end -}}`}}
# YOUR-TASK: signal PID 1 to reload after re-render
vault.hashicorp.com/agent-inject-command-db: "kill -HUP 1"
```
> The inner `{{ ... }}` is OpenBao Agent's *consul-template* syntax, escaped with Helm's `` {{` ` `}} `` so Helm doesn't try to evaluate it. This double-templating gotcha is the most common bonus mistake.

**Named template — `_helpers.tpl` skeleton:**
```yaml
{{- define "mychart.envVars" -}}
- name: APP_ENV
  value: {{ .Values.environment | quote }}   # YOUR-TASK: add more shared vars
{{- end -}}
```
In the Deployment: `{{- include "mychart.envVars" . | nindent 12 }}`

<details>
<summary>💡 Hints</summary>

- `agent-inject-template-*` lets you render any format: `.env`, JSON, YAML, a full app config.
- `agent-inject-command-*` runs an in-pod command after each re-render so the app reloads.
- The sidecar polls/renews the lease; when the source secret changes it re-renders the file and runs your command.

**Resources:**
- [Agent templates annotation](https://developer.hashicorp.com/vault/docs/platform/k8s/injector/annotations#vault-hashicorp-com-agent-inject-template)
- [Helm Named Templates](https://helm.sh/docs/chart_template_guide/named_templates/)

</details>

### Option B — External Secrets Operator (ESO)

**Objective:** Sync a secret from OpenBao into a native K8s `Secret` using ESO — no sidecar; the app reads a normal `Secret`.

**Requirements:**

1. **Install ESO** via its Helm chart (current release) into an `external-secrets` namespace.
2. **`SecretStore`** pointing at your OpenBao server using the `vault` provider with `kubernetes` auth and `serviceAccountRef: lab11-sa`.
3. **`ExternalSecret`** that produces a native K8s `Secret` (`target.name: db-creds`) from `secret/lab11/db`, then consume it via `envFrom: secretRef`.

**Skeleton (fill in the YOUR-TASK markers):**
```yaml
apiVersion: external-secrets.io/v1
kind: SecretStore
metadata: {name: openbao, namespace: lab11}
spec:
  provider:
    vault:                                # ESO's vault provider is compatible with OpenBao
      server: "http://openbao.openbao:8200"
      path: "secret"
      version: "v2"
      auth:
        kubernetes:
          mountPath: "kubernetes"
          role: "lab11"                   # YOUR-TASK: the OpenBao role from Task 3
          serviceAccountRef: {name: lab11-sa}
---
apiVersion: external-secrets.io/v1
kind: ExternalSecret
metadata: {name: db, namespace: lab11}
spec:
  refreshInterval: 1h
  secretStoreRef: {name: openbao, kind: SecretStore}
  target: {name: db-creds}                # produces a native K8s Secret
  data:
    - secretKey: password                 # YOUR-TASK: add the username key too
      remoteRef: {key: lab11/db, property: password}
```

<details>
<summary>💡 Hints</summary>

```bash
helm repo add external-secrets https://charts.external-secrets.io
helm repo update
helm install external-secrets external-secrets/external-secrets \
  -n external-secrets --create-namespace

# After applying the manifests, ESO creates the native Secret:
kubectl get secret db-creds -n lab11        # illustrative — should appear within the refresh window
```
ESO polls every `refreshInterval`; apps consume the resulting `Secret` with `envFrom: {secretRef: {name: db-creds}}` and never know ESO exists.

**Resources:**
- [external-secrets.io](https://external-secrets.io/)
- [ESO Vault/OpenBao provider](https://external-secrets.io/latest/provider/hashicorp-vault/)

</details>

**Bonus Documentation (either option):** add a section to `k8s/SECRETS.md` showing your annotation/manifest config, the rendered/synced result (redact values), and the benefit of the approach you chose.

---

## How to Submit

1. **Create Branch:**
   ```bash
   git checkout -b lab11
   ```

2. **Commit Work:**
   ```bash
   git add k8s/ <your-chart-dir>/
   git commit -m "feat: implement lab11 secrets management with OpenBao"
   git push -u origin lab11
   ```

3. **Create Pull Requests:**
   - **PR #1:** `your-fork:lab11` → `course-repo:master`
   - **PR #2:** `your-fork:lab11` → `your-fork:master`

4. **Verify:** chart files present, `k8s/SECRETS.md` complete, evidence captured, **no real secret values committed**.

---

## Acceptance Criteria

### Main Tasks (10 points)

**Task 1 — Kubernetes Secrets Fundamentals (2 pts):**
- [ ] `app-credentials` secret created via `kubectl create secret generic` in namespace `lab11`
- [ ] Secret viewed in YAML and base64 values decoded
- [ ] base64-vs-encryption and etcd-at-rest implications documented

**Task 2 — Helm-Managed Secrets (3 pts):**
- [ ] `templates/secrets.yaml` added to the chart
- [ ] Placeholder values in `values.yaml` (no real secrets)
- [ ] Deployment consumes the secret as env vars
- [ ] Env vars verified present in the pod; values absent from `describe`
- [ ] Resource `requests`/`limits` configured from values

**Task 3 — OpenBao Integration (3 pts):**
- [ ] OpenBao 2.5 installed via Helm (server + injector `Running`)
- [ ] KV-v2 engine enabled; `secret/lab11/db` written with ≥2 keys
- [ ] Kubernetes auth enabled; read policy + role bound to `lab11-sa`
- [ ] Agent annotations added; `serviceAccountName: lab11-sa` set
- [ ] Rendered secret file present at `/vault/secrets/...` in the pod

**Task 4 — Documentation (2 pts):**
- [ ] `k8s/SECRETS.md` complete with all five sections and real evidence
- [ ] Security analysis + Vault→OpenBao licensing note included

### Bonus Task (2 points) — one option only
- [ ] **A:** custom `agent-inject-template-*` renders multi-key file; reload command set; named template in `_helpers.tpl` used, **OR**
- [ ] **B:** ESO installed; `SecretStore` + `ExternalSecret` produce a native `db-creds` Secret consumed by the app
- [ ] Bonus documented in `k8s/SECRETS.md`

---

## Rubric

| Criteria | Points | Description |
|----------|--------|-------------|
| **K8s Secrets Fundamentals** | 2 pts | Create, view, decode, security model documented |
| **Helm-Managed Secrets** | 3 pts | Template, inject as env, verify, resource limits |
| **OpenBao Integration** | 3 pts | Install, KV-v2, k8s auth + policy + role, Agent injection |
| **Documentation** | 2 pts | Complete `SECRETS.md` with evidence + security analysis |
| **Bonus** | 2 pts | Agent templating (A) **or** ESO sync (B) |
| **Total** | 12 pts | 10 pts required + 2 pts bonus |

**Grading:**
- **10/10:** Working OpenBao injection, proper Helm secrets, strong documentation
- **8–9/10:** OpenBao working, minor docs/config issues
- **6–7/10:** K8s + Helm secrets work, OpenBao partially configured
- **<6/10:** Secrets not properly implemented, missing OpenBao setup

---

## Resources

<details>
<summary>📚 Official Documentation</summary>

- [Kubernetes Secrets](https://kubernetes.io/docs/concepts/configuration/secret/)
- [Encrypting Data at Rest](https://kubernetes.io/docs/tasks/administer-cluster/encrypt-data/)
- [OpenBao docs](https://openbao.org/docs/)
- [OpenBao 2.5.0 release notes](https://openbao.org/community/release-notes/2-5-0/)
- [OpenBao Helm chart](https://github.com/openbao/openbao-helm)
- [Helm 4 docs](https://helm.sh/docs/)

</details>

<details>
<summary>🎓 Tutorials</summary>

- [OpenBao Kubernetes auth method](https://openbao.org/docs/auth/kubernetes/)
- [Agent annotations reference (OpenBao injector compatible)](https://developer.hashicorp.com/vault/docs/platform/k8s/injector/annotations)
- [External Secrets Operator quickstart](https://external-secrets.io/latest/introduction/getting-started/)

</details>

<details>
<summary>🔐 Security Best Practices</summary>

- [Kubernetes Secrets Best Practices](https://kubernetes.io/docs/concepts/security/secrets-good-practices/)
- [External Secrets Operator](https://external-secrets.io/) — controller-synced alternative
- [getsops.io](https://getsops.io/) and [Sealed Secrets](https://github.com/bitnami-labs/sealed-secrets) — GitOps-friendly fallbacks
- [gitleaks](https://github.com/gitleaks/gitleaks) — scan every commit for leaked secrets

</details>

---

## Looking Ahead

- **Lab 12:** ConfigMaps for non-sensitive configuration and persistent storage
- **Lab 13:** ArgoCD deploys your secured Helm charts via GitOps
- **Lab 14:** Progressive delivery with Argo Rollouts
- **Lab 15:** StatefulSets with persistent storage

---

**Good luck!** 🔐

> **Remember:** Never commit real secrets to version control. Use placeholder values and inject real secrets at deploy time. In production, run a real secret manager like **OpenBao** — never dev mode.
