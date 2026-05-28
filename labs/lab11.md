# Lab 11 — Kubernetes Secrets & OpenBao

![difficulty](https://img.shields.io/badge/difficulty-intermediate-yellow)
![topic](https://img.shields.io/badge/topic-Secret%20Management-blue)
![points](https://img.shields.io/badge/points-10%2B2-orange)
![tech](https://img.shields.io/badge/tech-OpenBao%202.5%20%7C%20K8s%20Secrets-informational)

> **Goal:** Stop putting passwords in Git. Prove to yourself that a Kubernetes `Secret` is **not** encryption, then centralize secrets in **OpenBao 2.5.0** with a read-only policy enforcing least privilege.
> **Deliverable:** A PR from `lab11` adding `k8s/secrets/` (the policy + sample Secret), `k8s/lab10-app/templates/secret.yaml` to your Lab 10 chart, and `docs/LAB11.md` with **real** evidence (your decoded values, your `bao kv get`, your denied write).

---

## Overview

In this lab you will practice:
- Creating a `kind: Secret` and **decoding its base64 yourself** to drive home that base64 ≠ encryption
- Bringing up **OpenBao 2.5.0** in dev mode and learning the env-var contract (`BAO_ADDR`, `BAO_TOKEN`) that every later production setup will reuse
- Writing a **read-only HCL policy** and a token bound to it, then proving the policy by trying — and failing — to write
- Templating a `Secret` into your Lab 10 chart **without** committing the real value (the value comes from `--set`/`-f` at install time)
- Picking one of two production patterns for injection: **OpenBao Agent Injector** OR **External Secrets Operator (ESO)**

> ⚠️ **Scope:** dev-mode OpenBao only (in-memory, single key, auto-unsealed). Production OpenBao (Raft storage, auto-unseal via cloud KMS, audit device, TLS) is out of scope — but the policies and roles you write here are the same shape.

> 💡 **The five incidents the lecture opened with — Code Spaces 2014, Uber 2016, Toyota 2022, Dropbox 2022, tj-actions 2025 — every single one was a credential stored in the wrong place.** Not a zero-day. Not a sophisticated 0-click. Just a secret in code, a `.git/` directory served by a web server, a phished GitHub account, a compromised GitHub Action dumping `env` to logs. This lab teaches the boring stuff that would have prevented all five.

---

## Project State

**You should have from previous labs:**
- Lab 9: a k3d 1.36 cluster (`k3d cluster create devops`) with your `web` + `echo` services running
- Lab 10: a Helm chart at `k8s/lab10-app/` with `Chart.yaml`, `values.yaml`, `templates/`, `_helpers.tpl`

**This lab adds:**
- `k8s/secrets/app-credentials.yaml` — your hand-written `Secret` manifest (the base64 demo)
- `k8s/lab10-app/templates/secret.yaml` — a templated `Secret` in your chart
- `k8s/secrets/lab11-read.hcl` — the OpenBao read-only policy
- `docs/LAB11.md` — your submission report with the captured CLI evidence
- *(bonus)* either `k8s/secrets/injector.yaml` (Agent Injector annotations) OR `k8s/secrets/eso.yaml` (SecretStore + ExternalSecret CRDs)

---

## Setup

You need (verify before starting):

- `kubectl version --client` → 1.36.x (from Lab 9)
- `helm version` → 4.1.x (from Lab 10)
- `k3d cluster list` shows the `devops` cluster from Lab 9 Running
- **OpenBao 2.5.0** installed locally. Install via the brew tap (`brew install openbao/tap/bao`) or by downloading the `v2.5.0` Linux binary tarball from `github.com/openbao/openbao/releases` and unpacking it onto `PATH`.
- `bao version` must print `OpenBao v2.5.0`

Create the namespace + ServiceAccount that later tasks reuse:

```bash
kubectl create namespace lab11
kubectl create serviceaccount lab11-sa -n lab11
```

> **`bao` is a drop-in for `vault`.** OpenBao kept the wire protocol, CLI subcommands, and API endpoints. If you have old `vault kv put ...` muscle memory it still works against an OpenBao server. We use `bao` in this lab because the binary you installed is OpenBao, not HashiCorp Vault.

> 📜 **One-paragraph BSL callout.** In August 2023 HashiCorp re-licensed Vault under the Business Source License 1.1 — source-available, but with a non-compete that forbids commercial managed-service offerings competing with HashiCorp. The Linux Foundation forked Vault 1.14 as **OpenBao** under MPL-2.0 (true open source). OpenBao 2.0 went GA in March 2024; 2.5.0 (Feb 4 2026) added free Namespaces and horizontal read scalability — features that used to be a HashiCorp Enterprise paywall. Everything you write in this lab is portable to either server; we standardize on OpenBao so the manifests survive any future re-licensing.

---

## Task 1 — Kubernetes Secrets & The Base64 Trap (2 pts)

### 1.1 — Hand-write a `kind: Secret` manifest

`YOUR TASK`: create `k8s/secrets/app-credentials.yaml` containing a `kind: Secret` for a fictional database with username `app` and password of your choosing. Use the **declarative** form (a YAML file you `kubectl apply`), not `kubectl create secret`.

You decide:
- The `type:` value — pick from `Opaque`, `kubernetes.io/dockerconfigjson`, or `kubernetes.io/tls`. The wrong choice fails validation, so the choice matters. In `docs/LAB11.md`, justify why your choice fits a generic username+password.
- The two `data:` keys — name them whatever a real app would consume (think env-var style).
- The base64-encoded values — compute them yourself with `base64`; do **not** use the `stringData:` shortcut for this task. The point is to feel the encoding step by hand.

Skeleton (fill the YOUR-TASK markers):

```yaml
# k8s/secrets/app-credentials.yaml
apiVersion: v1
kind: Secret
metadata:
  name: app-credentials
  namespace: lab11
type: YOUR-TASK                 # which built-in type fits username+password?
data:
  YOUR-TASK: YOUR-TASK          # echo -n 'app' | base64
  YOUR-TASK: YOUR-TASK          # echo -n '<your password>' | base64
```

> ⚠️ **`echo` vs `echo -n`** — `echo "foo" | base64` includes the trailing newline (`Zm9vCg==`); `echo -n "foo" | base64` does not (`Zm9v`). The newline silently breaks password comparisons in the consuming app and is the most common base64 bug in dry-runs. Use `-n`.

Apply it, then read it back:

```bash
kubectl apply -f k8s/secrets/app-credentials.yaml
kubectl get secret app-credentials -n lab11 -o yaml
```

### 1.2 — Decode it yourself and prove the point

`YOUR TASK`: run a one-liner that fetches **your own** Secret from the cluster and pipes the password field through `base64 -d`, recovering the plaintext. Capture the output verbatim into `docs/LAB11.md` under a heading **"The base64 'aha' moment"**.

Hint (the shape of the command — fill in the key name you chose):

```bash
kubectl get secret app-credentials -n lab11 \
  -o jsonpath='{.data.YOUR-TASK}' | base64 -d ; echo
```

In **2–3 sentences** in your `docs/LAB11.md`, answer: *why does the K8s API even use base64 here if it's not for security?* (Hint: `Secret.data` values must be valid JSON/YAML strings; binary like a TLS key wouldn't survive transport.)

### 1.3 — etcd encryption-at-rest, in your own words

Write a paragraph in `docs/LAB11.md` answering all three:
- Are Kubernetes Secrets encrypted at rest by default? (Hint: look up `EncryptionConfiguration`.)
- What does a KMS provider in that config do that the `aescbc` provider doesn't?
- Why is enabling `EncryptionConfiguration` necessary but **not sufficient** for production — what does it not protect you from? (Hint: anyone with `system:masters` RBAC.)

### 1.4 — Proof of work

Paste into `docs/LAB11.md`:

- The contents of `k8s/secrets/app-credentials.yaml` (your real file, your real base64 strings)
- The output of `kubectl get secret app-credentials -n lab11 -o yaml | grep -A2 ^data:`
- The base64-decode one-liner **and its plaintext output** showing you recovered your own password
- Your 2–3 sentence answer to *why base64?* and the etcd-at-rest paragraph from 1.3

---

## Task 2 — Helm-Managed Secrets (3 pts)

### 2.1 — Templated Secret in the Lab 10 chart

`YOUR TASK`: add `templates/secret.yaml` to your Lab 10 chart (`k8s/lab10-app/templates/secret.yaml`). It must render a `kind: Secret` named after the chart's `fullname` helper, carry the standard chart labels, and consume **two** values from `.Values.secret` — `dbUsername` and `dbPassword`.

Critical rules:
- Use `stringData:` (so Helm doesn't double-encode); the K8s API base64-encodes on its side.
- In `values.yaml`, set the two fields to **placeholder strings** (`"PLACEHOLDER_USER"`, `"PLACEHOLDER_PASS"`). The real values come from `--set` or a `-f override.yaml` at install time — *never* committed.

Skeleton (fill the YOUR-TASK markers):

```yaml
# k8s/lab10-app/templates/secret.yaml
apiVersion: v1
kind: Secret
metadata:
  name: YOUR-TASK              # use the fullname helper from your _helpers.tpl
  labels:
    YOUR-TASK                  # use the labels helper from your _helpers.tpl
type: YOUR-TASK                # same choice as Task 1.1
stringData:
  DB_USERNAME: YOUR-TASK       # quote a value pulled from .Values.secret.*
  DB_PASSWORD: YOUR-TASK
```

And in `values.yaml`:

```yaml
secret:
  dbUsername: "PLACEHOLDER_USER"
  dbPassword: "PLACEHOLDER_PASS"   # override at install time, NEVER commit real values
```

### 2.2 — Consume it in the Deployment

`YOUR TASK`: edit your chart's existing Deployment template (`templates/deployment.yaml`) so the `web` container reads both keys as environment variables. Use the `envFrom` + `secretRef` pattern (cleaner than per-key `secretKeyRef` when the whole Secret is for one consumer).

Skeleton (fill the YOUR-TASK marker):

```yaml
containers:
  - name: web
    image: # ... your Lab 10 image ...
    envFrom:
      - secretRef:
          name: YOUR-TASK      # same helper-rendered name as in Task 2.1
```

### 2.3 — Install with the real value out-of-band

`YOUR TASK`: install (or upgrade) the chart, supplying the real password via `--set` **or** a `-f local-secrets.yaml` that is `.gitignore`d. Then verify in the running pod.

> ⚠️ **The `--set` CI-logs trap.** `helm upgrade --install ... --set secret.dbPassword='hunter2'` is fine on your laptop. In CI it ends up in the workflow log unless the variable is wrapped as a secret (`${{ secrets.DB_PASSWORD }}` in GHA) **and** you `helm upgrade ... --set secret.dbPassword="$DB_PASSWORD"` with no echo. Document in `docs/LAB11.md` which pattern you'd use in a real GitHub Action.

Verification commands (illustrative — your output will differ):

```bash
helm upgrade --install lab10-app k8s/lab10-app -n lab11 \
  --set secret.dbPassword='YOUR-PASSWORD'         # YOUR-TASK: pick a value
kubectl exec -n lab11 deploy/lab10-app-web -- env | grep '^DB_'
# DB_USERNAME=app
# DB_PASSWORD=YOUR-PASSWORD                       # ← present in pod env
kubectl describe pod -n lab11 -l app.kubernetes.io/name=lab10-app | grep -A1 -i secret
# (the Secret name appears; the value does NOT — describe redacts envFrom values)
```

### 2.4 — Proof of work

Paste into `docs/LAB11.md`:

- Your `templates/secret.yaml` and the relevant `values.yaml` snippet (placeholder values only — *no real password*)
- The `helm upgrade ... --set` command you actually ran (you can redact the password to `***`)
- The `kubectl exec ... env | grep ^DB_` output proving the values landed in the container (you can redact the password to `***` here too)
- The 2–3 sentence "how I would do this in CI" answer

---

## Task 3 — OpenBao Integration (3 pts)

This is the headline task. You will bring up OpenBao, learn the **env-var contract** that every later production setup reuses, write a **read-only HCL policy**, and prove the policy by trying to write — and failing.

### 3.1 — Bring up the dev server

`YOUR TASK`: start the OpenBao dev server with a **memorable** root token ID (you'll use it to log in). Then export the two environment variables every `bao` command depends on.

Skeleton (fill the YOUR-TASK markers — and yes, the **point** of the blanks is to make you internalize the contract):

```bash
# Start the dev server in the background. -dev = unsealed + in-memory.
bao server -dev -dev-root-token-id=___ &        # YOUR-TASK: pick a token id (e.g. 'devroot')

# Two env vars EVERY bao command needs:
export BAO_ADDR=___                              # YOUR-TASK: the dev server URL (default port is 8200)
export BAO_TOKEN=___                             # YOUR-TASK: must match the -dev-root-token-id above

bao status                                       # Sealed false, Storage Type inmem, Version 2.5.0
```

> 💡 **The contract:** every `bao` (or `vault`) client — your CLI, your apps, the ESO provider, the Agent injector — authenticates by `BAO_ADDR` + a token. In dev mode the token is the root token. In production the token comes from an **auth method** (Kubernetes ServiceAccount JWT, AppRole, OIDC), is short-lived, and is scoped by a policy. The env-var names are the same.

> ⚠️ **Dev server is INMEM.** Every secret you put in goes away when the process restarts. That's deliberate — it makes the lab fast and the security model unmistakable.

### 3.2 — Put and get a secret on the KV-v2 path

`YOUR TASK`: enable the KV-v2 secrets engine at a path you choose, then write a secret containing **at least two** key-value pairs at a path you choose, then read one of the fields back.

Skeleton:

```bash
bao secrets enable -path=___ kv-v2              # YOUR-TASK: pick the mount path (convention: 'secret')

bao kv put ___/lab11/db \                       # YOUR-TASK: the mount path you chose, then a logical name
  ___=app \                                     # YOUR-TASK: a field name
  ___=$(YOUR-PASSWORD)                          # YOUR-TASK: the matching value (use a literal, not a real password)

bao kv get -field=___ ___/lab11/db              # YOUR-TASK: read back one field by name
```

> ⚠️ **KV-v1 vs KV-v2 path gotcha.** `bao kv put secret/foo k=v` writes the *logical* path `secret/foo`, but the **API** path under KV-v2 is `secret/data/foo` (with a `data/` segment inserted). Policies and the Agent injector reference the API path — so an HCL rule must say `path "secret/data/lab11/db"`, not `path "secret/lab11/db"`. Forgetting this is the #1 way a "correct" policy denies a read.

> ⚠️ **`bao kv put` vs `bao write` on the same data path.** KV-v2 versions data under `data/`; `bao write secret/data/foo data='{"k":"v"}'` works but uses a different JSON shape than `bao kv put`. Stick with `bao kv put` / `bao kv get` for KV-v2; `bao write` for everything else (auth backends, policies, roles).

### 3.3 — Write the read-only policy

`YOUR TASK`: create `k8s/secrets/lab11-read.hcl` with one stanza that grants **read** on the exact data path for your secret, and **nothing else**. No `list`, no `update`, no `delete`, no glob — the whole point is least privilege.

Skeleton (fill the YOUR-TASK markers):

```hcl
# k8s/secrets/lab11-read.hcl
path "___" {                                     # YOUR-TASK: the API path to the secret you wrote in 3.2
  capabilities = [___]                           # YOUR-TASK: a single-element list, the minimum verb
}
```

Apply it and mint a token bound to it:

```bash
bao policy write lab11-read k8s/secrets/lab11-read.hcl
APP_TOKEN=$(bao token create -policy=lab11-read -ttl=1h -field=token)
echo "$APP_TOKEN"      # save for the next step
```

### 3.4 — Prove the policy by trying to break it

`YOUR TASK`: log in as the new token (set `BAO_TOKEN=$APP_TOKEN`), then run **two** commands and capture both outputs:

1. A `bao kv get -field=...` that **succeeds** (the policy allows read).
2. A `bao kv put ...` to the same path that **fails** with a 403 (the policy does not allow write).

The second command failing is the evidence. If it succeeds, your policy granted too much — go back to 3.3.

Skeleton:

```bash
BAO_TOKEN=$APP_TOKEN bao kv get -field=___ ___/lab11/db    # YOUR-TASK: should print the value
BAO_TOKEN=$APP_TOKEN bao kv put ___/lab11/db ___=evil      # YOUR-TASK: should fail with 403
# Error writing data to secret/data/lab11/db: ...permission denied
```

Restore your root token for any cleanup: `export BAO_TOKEN=<your-dev-root-token-id>`.

### 3.5 — Proof of work

Paste into `docs/LAB11.md`:

- `bao version` (must show 2.5.0)
- The exact `bao server -dev -dev-root-token-id=...` line and the `export BAO_ADDR`/`BAO_TOKEN` lines (the env-var contract — redact the token if you want)
- `bao status` showing `Sealed false`, `Storage Type inmem`, `Version 2.5.0`
- `bao kv put ...` create confirmation + `bao kv get -field=...` returning your value
- Contents of `k8s/secrets/lab11-read.hcl` (your real policy)
- The **two** outputs from 3.4 side by side — the read succeeding and the write failing with `permission denied`. **This is the headline evidence.**

---

## Task 4 — Documentation (2 pts)

`YOUR TASK`: finalize `docs/LAB11.md` with these sections, in this order:

1. **The base64 'aha' moment** — your decoded plaintext (1.2) + the "why base64 then?" paragraph (1.3)
2. **etcd encryption-at-rest** — the paragraph from 1.3 covering KMS vs `aescbc` and what `EncryptionConfiguration` does not protect
3. **Helm-managed secret** — chart snippet, install command (redacted), pod env proof (2.4)
4. **OpenBao workflow** — env-var contract, KV-v2 put/get, the read-only policy + the denied-write proof (3.5)
5. **Vault → OpenBao history** — one paragraph: BSL Aug 2023, LF fork, why OpenBao for this course
6. **Security analysis** — when native K8s Secret is fine vs when you need OpenBao; what dev mode hides from you that production exposes (no Raft, no audit device, no auto-unseal, no TLS); 2–3 sentences on the SOPS / Sealed Secrets alternatives and when they make sense
7. **Production checklist** — five bullets you would actually put in a prod hardening doc (least-privilege roles, audit device, etc.)

---

## Bonus Task — Pick ONE (2 pts)

Pick **A** or **B**. Both are 2 pts. **Do not do both.** Less hand-holding here on purpose — you've earned it.

### Option A — OpenBao Agent Injector

You install the Agent Injector via the OpenBao Helm chart, annotate a pod, and prove that the secret lands on disk inside the pod without the app knowing about OpenBao.

**Required artifacts** (in `k8s/secrets/injector.yaml`):

1. The **annotations** on your pod template that trigger injection. The names below are the contract — fill in the values; the names that end in `-<file>` are templated by *you* (the filename portion becomes the filename under `/vault/secrets/`):

   ```yaml
   # k8s/secrets/injector.yaml — annotations: section of your pod template
   vault.hashicorp.com/agent-inject: "true"
   vault.hashicorp.com/role: YOUR-TASK                          # the OpenBao role you create below
   vault.hashicorp.com/agent-inject-secret-YOUR-TASK: YOUR-TASK # filename : the KV API path (mind the data/ segment)
   vault.hashicorp.com/agent-inject-template-YOUR-TASK: |       # render the secret as a .env-style file (>=2 keys)
     YOUR-TASK
   ```

2. `serviceAccountName: lab11-sa` on the pod spec — the ServiceAccount whose JWT OpenBao validates.

**Required OpenBao config** (run inside the openbao server pod):

- `bao auth enable kubernetes` and `bao write auth/kubernetes/config kubernetes_host=...`
- A `bao write auth/kubernetes/role/lab11 ...` that binds `lab11-sa`, namespace `lab11`, the `lab11-read` policy, and a sensible `ttl`.

**Proof of work:**

- `kubectl get pods -n openbao` showing the injector pod Running
- `kubectl describe pod -n lab11 <your-pod>` showing the **injected init container + sidecar** (`vault-agent-init` and `vault-agent`) that you did NOT put there
- `kubectl exec -n lab11 <your-pod> -c <app-container> -- cat /vault/secrets/db` showing the rendered file (redact the value if you like — the *existence* of the file is what matters)

> The injector is a **MutatingAdmissionWebhook**. It edits your podspec at admission time. That's why your YAML has *one* container and the running pod has *three* — the webhook added two. This is the same mechanism Istio uses for its envoy sidecar.

### Option B — External Secrets Operator (ESO)

You install ESO via Helm, point a `SecretStore` at your OpenBao server, and an `ExternalSecret` produces a **native K8s Secret** that your app consumes with `envFrom: secretRef`. The app never knows ESO exists.

**Required artifacts** (in `k8s/secrets/eso.yaml`):

1. A `SecretStore` CRD (`apiVersion: external-secrets.io/v1`) named `openbao` in namespace `lab11`, with a `provider.vault` block (ESO's `vault` provider is compatible with OpenBao). It uses `kubernetes` auth, the role you create in OpenBao, and `serviceAccountRef: {name: lab11-sa}`.
2. An `ExternalSecret` CRD producing a native `db-creds` Secret.

Skeleton (fill the YOUR-TASK markers — the CRD field names are the contract):

```yaml
# k8s/secrets/eso.yaml
apiVersion: external-secrets.io/v1
kind: SecretStore
metadata: {name: openbao, namespace: lab11}
spec:
  provider:
    vault:
      server: YOUR-TASK                 # the in-cluster URL of the OpenBao server (Service DNS + port)
      path: YOUR-TASK                   # the KV mount path you chose in Task 3.2
      version: YOUR-TASK                # KV engine version
      auth:
        kubernetes:
          mountPath: kubernetes
          role: YOUR-TASK               # the OpenBao role bound to lab11-sa
          serviceAccountRef: {name: lab11-sa}
---
apiVersion: external-secrets.io/v1
kind: ExternalSecret
metadata: {name: db, namespace: lab11}
spec:
  refreshInterval: YOUR-TASK            # production default vs demo: pick deliberately
  secretStoreRef: {name: openbao, kind: SecretStore}
  target: {name: YOUR-TASK}             # the native K8s Secret ESO will produce (consumed by your app)
  data:
    - secretKey: YOUR-TASK              # the key as it appears IN the produced K8s Secret
      remoteRef: {key: YOUR-TASK, property: YOUR-TASK}  # the OpenBao logical path + the field name in it
    # YOUR-TASK: add a second key — username — with the same shape
```

**Required OpenBao config:** same Kubernetes auth + role binding as Option A (it's the same auth method).

**Required app wiring:** edit your Lab 10 chart to consume `db-creds` via `envFrom: secretRef`. Note that the app is now reading a *native K8s Secret* — no sidecar, no annotations, no OpenBao client in the pod. ESO does the syncing out-of-band.

**Proof of work:**

- `kubectl get pods -n external-secrets` showing the ESO controller Running
- `kubectl get externalsecret db -n lab11` showing `STATUS: SecretSynced`
- `kubectl get secret db-creds -n lab11` showing the ESO-produced Secret exists
- `kubectl exec -n lab11 deploy/lab10-app-web -- env | grep ^DB_` showing the values landed in the app

> ESO **polls** OpenBao every `refreshInterval`. Lower it for the demo (e.g. `30s`), but `1h` is the production default — rotating in OpenBao does not propagate instantly. That trade-off is the headline difference vs the Agent Injector (which renews via the token lease).

**Bonus documentation:** append a section to `docs/LAB11.md` with the manifest you used, the proof captures above, and **one paragraph** on why you picked A or B for the kind of app you'd want to run with it (think: "dynamic DB creds with 15-min TTL" → Agent Injector; "every microservice in a 50-pod monorepo reads the same handful of secrets" → ESO).

---

## How to Submit

```bash
git switch -c lab11
git add k8s/secrets/ k8s/lab10-app/templates/secret.yaml \
        k8s/lab10-app/values.yaml docs/LAB11.md
# also stage k8s/secrets/injector.yaml (Option A) OR k8s/secrets/eso.yaml (Option B) if you did the bonus
git commit -m "feat(lab11): secrets + OpenBao (read-only policy, base64 demo)"
git push -u origin lab11
```

Open **two** PRs:

- `your-fork:lab11` → `course-repo:master` *(reviewed)*
- `your-fork:lab11` → `your-fork:master`

PR checklist:

```text
- [ ] Task 1 — app-credentials.yaml + base64 decode proof in docs/LAB11.md
- [ ] Task 2 — templates/secret.yaml in chart, placeholders only in values.yaml, env proof
- [ ] Task 3 — bao 2.5.0 dev server, BAO_ADDR/BAO_TOKEN exported, KV put/get, read-only policy, denied-write proof
- [ ] Task 4 — docs/LAB11.md has all 7 sections
- [ ] Bonus (optional) — Agent Injector OR ESO with proof captures
- [ ] No real secret values in any committed file (grep your diff before pushing)
```

---

## Acceptance Criteria

### Task 1 (2 pts)
- ✅ `k8s/secrets/app-credentials.yaml` is your own hand-written `kind: Secret` with a deliberate `type:` choice and two base64-encoded `data:` keys
- ✅ `docs/LAB11.md` contains the base64-decode one-liner **with your own plaintext output**
- ✅ "Why base64?" answer and etcd-at-rest paragraph are present and correct

### Task 2 (3 pts)
- ✅ `k8s/lab10-app/templates/secret.yaml` exists, uses the chart's name + label helpers, and reads from `.Values.secret.*`
- ✅ `values.yaml` ships **placeholder** strings only — no real password
- ✅ Deployment consumes the Secret via `envFrom: secretRef`
- ✅ Pod env confirmed via `kubectl exec ... env | grep ^DB_`; `kubectl describe` does NOT show the values
- ✅ `docs/LAB11.md` documents the CI pattern you'd use to avoid `--set` leaking the password

### Task 3 (3 pts)
- ✅ `bao version` shows 2.5.0
- ✅ `bao server -dev -dev-root-token-id=...` was run; `BAO_ADDR` and `BAO_TOKEN` exported
- ✅ KV-v2 enabled, secret written with ≥ 2 keys, read back with `bao kv get -field=...`
- ✅ `k8s/secrets/lab11-read.hcl` grants **read only** on the exact data path (no glob, no extra capabilities)
- ✅ The denied-write evidence (`bao kv put ...` → `permission denied`) is captured in `docs/LAB11.md`

### Task 4 (2 pts)
- ✅ `docs/LAB11.md` has all seven sections (1.2 + 1.3, etcd-at-rest, Helm, OpenBao, Vault→OpenBao history, security analysis, production checklist)

### Bonus (2 pts) — one option only
- ✅ **A:** Agent Injector deployed; injected init+sidecar visible in `kubectl describe pod`; `/vault/secrets/<file>` exists in the app container; custom template renders multi-key `.env`
- ✅ **B:** ESO installed; `ExternalSecret` shows `SecretSynced`; `db-creds` native Secret exists; app pod env contains the values

---

## Rubric

| Task | Points | Criteria |
|------|-------:|----------|
| **Task 1** — K8s Secrets & base64 trap | **2** | Hand-written Secret, decoded plaintext, base64 vs encryption explained, etcd-at-rest understood |
| **Task 2** — Helm-managed Secret | **3** | Templated Secret, placeholder values, envFrom wiring, real value injected at install, CI pattern documented |
| **Task 3** — OpenBao integration | **3** | Dev server up, env-var contract internalized, KV-v2 put/get, read-only policy enforces (denied-write proof) |
| **Task 4** — Documentation | **2** | All seven sections present, security analysis genuine, BSL/OpenBao history correct |
| **Bonus** — Injector OR ESO | **2** | Working injection (A) or sync (B) with manifests + proof |
| **Total** | **12** | 10 main + 2 bonus |

**Grading bands:**
- **10/10:** All four main tasks done, the denied-write evidence is real, no real secrets committed, security analysis shows genuine understanding
- **8–9/10:** All tasks done with minor gaps in docs or one missing proof capture
- **6–7/10:** Tasks 1+2 solid, OpenBao up but policy is too permissive (no denied-write evidence) or KV path wrong
- **<6/10:** OpenBao not running, base64 demo missing, or real secrets committed

---

## Resources

<details>
<summary>📚 Documentation</summary>

- [Kubernetes Secrets](https://kubernetes.io/docs/concepts/configuration/secret/) — concepts + the `type:` table
- [Encrypting Confidential Data at Rest](https://kubernetes.io/docs/tasks/administer-cluster/encrypt-data/) — EncryptionConfiguration, KMS provider, key rotation
- [OpenBao docs](https://openbao.org/docs/) — `bao` CLI, KV-v2, auth methods, policies
- [OpenBao 2.5.0 release notes](https://openbao.org/community/release-notes/2-5-0/) — Feb 4 2026
- [OpenBao Kubernetes auth](https://openbao.org/docs/auth/kubernetes/) — TokenReview API, role binding
- [Vault Agent annotations (OpenBao-compatible)](https://developer.hashicorp.com/vault/docs/platform/k8s/injector/annotations) — annotation reference
- [External Secrets Operator](https://external-secrets.io/) — CRDs + provider list
- [ESO Vault/OpenBao provider](https://external-secrets.io/latest/provider/hashicorp-vault/) — config shape

</details>

<details>
<summary>⚠️ Common Pitfalls (from real dry-runs)</summary>

- **Base64 is encoding, not encryption.** `kubectl get secret -o yaml | grep -A1 data:` followed by `| base64 -d` recovers plaintext with **no key** — the #1 fact every junior gets wrong. If you walk away with one thing from this lab, walk away with this.
- **`echo` adds a trailing newline.** `echo "foo" | base64` ≠ `echo -n "foo" | base64`. The newline silently invalidates passwords inside the app. Use `-n`.
- **etcd encryption-at-rest needs KMS, not just `aescbc`.** Local-key `aescbc` providers store the key on the same disk as the data they "protect" — the key is sitting next to the lock. KMS providers (AWS KMS, GCP KMS, OpenBao Transit) keep the key out of the cluster.
- **OpenBao dev server is INMEM.** Restart the process and every secret is gone. That's the point — dev mode is for learning the API, not for storing anything. Read the lecture's anti-pattern slide on running dev mode in prod.
- **KV-v1 vs KV-v2 path difference.** `bao kv put secret/foo k=v` writes the *logical* path; policies and the Agent injector must reference the **API** path (`secret/data/foo`, with `data/` inserted) or the read silently denies. Same gotcha lives in the ESO `remoteRef.key` field.
- **`bao kv put` vs `bao write`.** Both touch the same path on KV-v2 but use different JSON shapes; stick to `kv put`/`kv get` for KV-v2 to avoid the shape mismatch.
- **Helm `--set` leaks to CI logs.** `helm upgrade ... --set db.password='hunter2'` in a GitHub Action log is a Code Spaces / tj-actions waiting to happen. Wrap as `${{ secrets.* }}` and reference by env var; better, use a real secret manager and let ESO/Agent Injector deliver the value.
- **`automountServiceAccountToken: true` by default.** Every pod gets a SA token whether it needs one or not. For pods that don't talk to the K8s API or OpenBao, set this to `false` to shrink the blast radius.
- **`vault.hashicorp.com/role: admin` is the new `--privileged`.** Bind one role per app per environment. Least privilege is the entire point of the policy you wrote in 3.3.
- **Dev-mode root token in your shell history.** `export BAO_TOKEN=root` survives in `~/.bash_history`. Use a unique value per dev session and clear it (`unset BAO_TOKEN`) when you're done.

</details>

<details>
<summary>🛠️ Tools worth knowing</summary>

- [gitleaks](https://github.com/gitleaks/gitleaks) — pre-commit + CI scanner; catches the human moments
- [trufflehog](https://github.com/trufflesecurity/trufflehog) — deeper detector, finds high-entropy strings in git history
- [SOPS](https://getsops.io/) — file-level encryption with KMS/age/PGP; GitOps-friendly
- [Sealed Secrets](https://github.com/bitnami-labs/sealed-secrets) — per-cluster public-key encryption; CRD + controller
- [k9s](https://k9scli.io/) — terminal UI; `:secret` shows them all at once

</details>

---

## Looking Ahead

| Lab | What it adds |
|---:|---|
| 12 | ConfigMaps + PVC — non-sensitive config + persistent state survives pod deletion |
| 13 | ArgoCD GitOps — your secured chart deploys via Application/ApplicationSet |
| 14 | Argo Rollouts canary; secrets rotate underneath progressive delivery |
| 15 | StatefulSets — stable identity + per-pod PVC + secrets per replica |
| 16 | kube-prometheus stack — scrape OpenBao's `/sys/metrics` |

**Good luck.** 🔐

> **Remember:** the moment you decoded your own Secret with `base64 -d` and got back plaintext is the moment you understood why every breach in the lecture's incident list was preventable. Keep that feeling. Carry it into every PR review where someone "just for now" puts a real value in `values.yaml`.
