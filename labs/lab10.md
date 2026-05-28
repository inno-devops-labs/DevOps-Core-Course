# Lab 10 — Helm Package Manager

![difficulty](https://img.shields.io/badge/difficulty-intermediate-yellow)
![topic](https://img.shields.io/badge/topic-Helm-blue)
![points](https://img.shields.io/badge/points-10%2B2-orange)
![tech](https://img.shields.io/badge/tech-Helm%204-informational)

> **Goal:** Convert your Lab 9 Kubernetes manifests into a hand-written Helm 4 chart that ships through dev / staging / prod with one value file per environment, runs a lifecycle hook, and (bonus) is publishable to GHCR over OCI.
> **Deliverable:** A PR from `lab10` adding `k8s/lab10-app/` (chart) and `k8s/lab10-app/HELM.md` (your report).

---

## Overview

In Lab 9 you wrote four raw manifests (web Deployment + Service, echo Deployment + Service). For one environment that's fine — for three, you'd be copy-editing YAML and praying nothing drifts.

This lab pulls every hardcoded value out of those manifests into a **chart** with a **values file per environment**. The skill being graded is **template authoring**: writing `Chart.yaml`, `values.yaml`, `templates/deployment.yaml`, `templates/service.yaml`, `templates/_helpers.tpl`, and one hook — from scratch. Not `helm create`-and-edit. From scratch.

> ⚠️ **Scope:** No subcharts, no library charts, no `values.schema.json`. Just chart anatomy + values hierarchy + one hook + (bonus) an OCI push.

**What you'll practice:**
- Helm 4 chart anatomy: `Chart.yaml`, `values.yaml`, `templates/`, `_helpers.tpl`
- Go templates + Sprig (`include`, `nindent`, `default`, `toYaml`, `printf`, `trunc`, `quote`)
- The release lifecycle: `install / upgrade / rollback / list / history / uninstall`
- Multi-environment delivery via a values hierarchy and **`-f a -f b`** layering
- Lifecycle hooks (`pre-install` / `pre-upgrade`) with weights and delete policies
- Publishing charts as OCI artifacts to GHCR

> 📚 Pairs with **Lecture 10 — Helm Package Management**. Re-read slides 5–11 (chart anatomy, templates, `_helpers.tpl`, lifecycle, multi-env, hooks) before you start.

---

## Project State

**You should have from previous labs:**
- A k3d cluster on Kubernetes 1.36 (Lab 9 — `k3d cluster create devops ...`)
- Your **Lab 2 web image** in a public registry (Docker Hub / GHCR)
- Lab 9 manifests in `k8s/`: `web-deployment.yaml`, `web-service.yaml`, `echo-deployment.yaml`, `echo-service.yaml`

**This lab adds:**
- `k8s/lab10-app/` — a hand-written Helm 4 chart that **replaces** those four manifests
- `k8s/lab10-app/values-prod.yaml` (and optionally `-dev`, `-staging`) — per-environment deltas
- `k8s/lab10-app/templates/hooks/db-migrate.yaml` — one pre-install/pre-upgrade hook
- `k8s/lab10-app/HELM.md` — your submission report

By Lab 13 ArgoCD will deploy this chart through GitOps; by Lab 14 Argo Rollouts will replace the Deployment template you write here. So the template hygiene you build this week outlives Lab 10.

---

## Setup

```bash
helm version            # must report v4.1.x (course pins to 4.1.4)
kubectl get nodes       # your Lab 9 cluster must be up
```

> **Helm 3 vs Helm 4:** Helm 3 is in support-mode only (bug fixes through July 8 2026, security fixes through November 11 2026). The course standardizes on **Helm 4**. Note that `apiVersion: v2` in `Chart.yaml` is still correct on Helm 4 — that header is the Helm-3-and-later chart-format version, **not** the Helm binary version. `apiVersion: v1` is Helm 2 only.

Install instructions: <https://helm.sh/docs/intro/install/>.

You will write every file under `k8s/lab10-app/` yourself — **do not run `helm create`** (see Common Pitfalls).

---

## Task 1 — Helm fundamentals & setup (1 pt)

### 1.1 — Install Helm 4 and inspect a real chart

`YOUR TASK`: install (or upgrade to) Helm 4.1.x, then pull metadata and default values from an OCI-hosted public chart **without installing it**:

```bash
helm show chart  oci://registry-1.docker.io/bitnamicharts/nginx
helm show values oci://registry-1.docker.io/bitnamicharts/nginx | head -40
```

Look at the shape: `apiVersion`, `name`, `version`, `appVersion`, `dependencies`; in `values.yaml` notice how every numeric/string knob is exposed.

### 1.2 — Explain the three concepts in your own words

In `HELM.md`, write 2–3 sentences each for **Chart**, **Release**, **Values**. Don't copy the docs — you must be able to answer them at a viva. Hints:

- *Chart* is the package on disk; *Release* is one running instance of it; *Values* fill the template.
- Helm 4 stores release state in a `helm.sh/release.v1` Secret in the release's namespace (Tiller is long gone — Helm 2).

### 1.3 — Proof of work

Paste into `HELM.md`:

- `helm version` output showing v4.1.x
- The first ~20 lines of one of the `helm show` calls above
- Your 2–3-sentence explanations of Chart vs Release vs Values

---

## Task 2 — Build the chart (3 pts)

**Objective:** Write the chart from scratch. The skeleton below is the **directory shape** you must produce. **Do not** run `helm create`; you'd ship boilerplate references to a `serviceaccount.yaml` you didn't write, then break `helm lint` the moment you edit `values.yaml` (see Common Pitfalls).

```
k8s/lab10-app/
├── Chart.yaml
├── values.yaml
├── values-prod.yaml                # Task 3
└── templates/
    ├── _helpers.tpl
    ├── deployment.yaml             # web
    ├── service.yaml                # web
    ├── echo-deployment.yaml        # echo (Task 2.6)
    ├── echo-service.yaml           # echo (Task 2.6)
    ├── hooks/
    │   └── db-migrate.yaml         # Task 4
    └── NOTES.txt                   # optional; printed after install
```

### 2.1 — `Chart.yaml`

`YOUR TASK`: fill in the metadata. Both `version` (chart SemVer — bump on chart changes) and `appVersion` (image-side version string — bump on image changes) matter; they evolve independently. `kubeVersion` makes Helm refuse to install against an older cluster.

```yaml
apiVersion: ___                  # YOUR TASK: chart-format version (Helm 3/4 expects this value)
name: ___                        # YOUR TASK: chart name (must match the directory name)
description: ___                 # YOUR TASK: one sentence; shows in `helm show chart`
type: application                # 'application' (default) or 'library' — leave as-is for this lab
version: ___                     # YOUR TASK: SemVer for the chart, e.g. 0.1.0
appVersion: "___"                # YOUR TASK: quoted string, image-side version (your Lab 2 tag)
kubeVersion: "___"               # YOUR TASK: a range, e.g. ">=1.33.0" — refuses older clusters
# dependencies:                  # OPTIONAL — not used in this lab
#   - name: ...
#     version: ...
#     repository: ...
```

### 2.2 — `values.yaml`

`YOUR TASK`: list every value your templates will reference, with a sensible default. **Every hardcoded number/string from your Lab 9 manifests becomes a value here.** Both `web` and `echo` need their own blocks.

The minimum surface (you may add more):

```yaml
# YOUR TASK: fill every default. The keys below are the contract between
# values.yaml and your templates — your templates will fail to render if you
# rename a key here without updating the template, and vice versa.

replicaCount: ___                # default replicas for `web`

image:
  repository: ___                # your Lab 2 image, e.g. docker.io/<you>/devops-info
  tag: ""                        # empty → templates fall back to .Chart.AppVersion
  pullPolicy: ___                # IfNotPresent | Always | Never

service:
  type: ___                      # NodePort for local k3d; LoadBalancer in prod
  port: ___                      # the Service port (clients hit this)
  # the container's listen port lives under `containerPort` below

containerPort: ___               # what your Lab 2 app listens on (8000? 5000?)

resources:
  requests:
    cpu: ___
    memory: ___
  limits:
    cpu: ___
    memory: ___

probes:
  liveness:
    path: ___                    # /health from Lab 1
    initialDelaySeconds: ___
    periodSeconds: ___
  readiness:
    path: ___
    periodSeconds: ___

ingress:
  enabled: false                 # not used in this lab; reserved for Lab 16

echo:
  replicaCount: ___              # default replicas for the echo sidecar service
  image:
    repository: ghcr.io/inno-devops-labs/echo
    tag: v1
  service:
    type: ClusterIP
    port: 80
    targetPort: 8081

# Hook config (Task 4)
hooks:
  dbMigrate:
    enabled: true
    image: busybox:1.37          # any small image — the hook is a fake migration
```

### 2.3 — `templates/_helpers.tpl`

Named templates avoid copy-pasting label blocks across every manifest. You will define **four**: `name`, `fullname`, `labels`, `selectorLabels`. They are the muscle memory of Helm; you'll write them in every chart for the rest of your career.

`YOUR TASK`: implement the bodies. The function shape is given — fill the body of each `define` block so that:

| Template | What it must return |
|---|---|
| `lab10-app.name` | The chart name (or `nameOverride` if a user sets one), truncated to 63 chars (K8s label limit) and with any trailing `-` stripped. |
| `lab10-app.fullname` | A unique-per-release name: `<release-name>-<chart-name>` (or `nameOverride` if set), truncated to 63, trailing `-` stripped. This is what most metadata.name fields use. |
| `lab10-app.labels` | The full label set: `helm.sh/chart`, every selector label (include `selectorLabels`), `app.kubernetes.io/version`, `app.kubernetes.io/managed-by`. |
| `lab10-app.selectorLabels` | A **strict subset** of `labels`: only `app.kubernetes.io/name` and `app.kubernetes.io/instance`. Selectors are immutable after creation — never put `version` here (see Common Pitfalls). |

```handlebars
{{/* YOUR TASK: return the chart name, truncated to 63 chars, no trailing dash */}}
{{- define "lab10-app.name" -}}
{{- /* your body — hint: `default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-"` is the canonical form */ -}}
{{- end }}

{{/* YOUR TASK: return <release-name>-<chart-name>, truncated to 63, no trailing dash */}}
{{- define "lab10-app.fullname" -}}
{{- /* your body — hint: `printf "%s-%s" .Release.Name (chart-name) | trunc 63 | trimSuffix "-"` */ -}}
{{- end }}

{{/* YOUR TASK: return the full label set (5 labels including the helm.sh/chart line) */}}
{{- define "lab10-app.labels" -}}
{{- /* your body — must include `lab10-app.selectorLabels`; emit `helm.sh/chart`,
       `app.kubernetes.io/version`, `app.kubernetes.io/managed-by` */ -}}
{{- end }}

{{/* YOUR TASK: return ONLY the two selector labels (name + instance). No version. */}}
{{- define "lab10-app.selectorLabels" -}}
{{- /* your body */ -}}
{{- end }}
```

Reference functions you'll need (all from Sprig): `default`, `trunc`, `trimSuffix`, `printf`, `replace`, `quote`. See [Sprig docs](https://masterminds.github.io/sprig/) and [Chart Template Guide](https://helm.sh/docs/chart_template_guide/).

### 2.4 — `templates/deployment.yaml` (web)

`YOUR TASK`: templatize your Lab 9 web Deployment. The YAML shape is given so you don't reinvent the wheel — each `{{ ___ }}` is a token you must fill (and many of those will need pipelines like `| nindent 4` or `| default ...`).

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: {{ ___ }}                                # YOUR TASK: `include` your fullname template
  labels:
    {{- ___ | nindent 4 }}                       # YOUR TASK: `include` your labels template
spec:
  replicas: {{ ___ }}                            # YOUR TASK: from .Values.replicaCount (with a sane default)
  selector:
    matchLabels:
      {{- ___ | nindent 6 }}                     # YOUR TASK: `include` your SELECTOR labels template
  template:
    metadata:
      labels:
        {{- ___ | nindent 8 }}                   # YOUR TASK: `include` your SELECTOR labels template
    spec:
      containers:
        - name: web
          image: "{{ ___ }}:{{ ___ | default .Chart.AppVersion }}"   # YOUR TASK: repo + tag from values
          imagePullPolicy: {{ ___ }}             # YOUR TASK: from .Values.image.pullPolicy
          ports:
            - name: http
              containerPort: {{ ___ }}           # YOUR TASK: from .Values.containerPort
              protocol: TCP
          livenessProbe:
            httpGet:
              path: {{ ___ }}                    # YOUR TASK: from values
              port: http
            initialDelaySeconds: {{ ___ }}
            periodSeconds: {{ ___ }}
          readinessProbe:
            httpGet:
              path: {{ ___ }}
              port: http
            periodSeconds: {{ ___ }}
          {{- with .Values.resources }}
          resources:
            {{- ___ | nindent 12 }}              # YOUR TASK: render the whole sub-tree as YAML (one Sprig fn)
          {{- end }}
```

> **`indent` vs `nindent`:** `nindent N` = newline + indent by N spaces. `indent N` = indent only. When a `{{- ... -}}` action sits on its own line and consumed the preceding newline, `indent` produces invalid YAML. Use `nindent` 9 times out of 10.

### 2.5 — `templates/service.yaml` (web)

`YOUR TASK`: same drill, much shorter.

```yaml
apiVersion: v1
kind: Service
metadata:
  name: {{ ___ }}                                # YOUR TASK: fullname template
  labels:
    {{- ___ | nindent 4 }}                       # YOUR TASK: labels template
spec:
  type: {{ ___ }}                                # YOUR TASK: from .Values.service.type
  ports:
    - port: {{ ___ }}                            # YOUR TASK: from .Values.service.port
      targetPort: http                           # named ports beat numbers; this points at the deployment's `name: http`
      protocol: TCP
      name: http
  selector:
    {{- ___ | nindent 4 }}                       # YOUR TASK: SELECTOR labels template (NOT the full labels)
```

### 2.6 — `templates/echo-deployment.yaml` + `templates/echo-service.yaml`

`YOUR TASK`: same pattern, but for the echo sidecar. Two notable differences:

1. Image comes from `.Values.echo.image.repository` + `.Values.echo.image.tag` (no `default .Chart.AppVersion` — echo's image is independent of your app's `appVersion`).
2. Use a different label discriminator (e.g. `app.kubernetes.io/component: echo`) on the pod template + Service selector so the **web** Service doesn't accidentally select echo pods. You can either:
   - Extend your `selectorLabels` helper with an optional component (pass `.Values.echo` into `include`), **or**
   - Hand-write a small additional selector key in this manifest only.

Take a moment to decide which — both are valid.

### 2.7 — Validate, render, install

Run, in this order: `helm lint <chart>`, `helm template <release> <chart>` (eyeball the rendered YAML), `helm install <release> <chart> --dry-run --debug`, then a real `helm install --create-namespace` into a fresh namespace. Finish with `helm list` (expect `REVISION 1`) and `kubectl get deploy,svc,pods` to confirm both pods are Ready.

```bash
helm install demo k8s/lab10-app -n helm-demo --create-namespace
# expected: helm list shows STATUS deployed, REVISION 1
```

### 2.8 — Proof of work

Paste into `HELM.md`:

- `helm lint k8s/lab10-app` output (must say `0 chart(s) failed`)
- The first ~30 lines of `helm template demo k8s/lab10-app` showing your values flowing into the rendered Deployment (image, replicas, probes, resources)
- `helm list -n helm-demo` showing **REVISION 1** for release `demo`
- `kubectl get deploy,svc,pods -n helm-demo` showing both web and echo pods Ready

---

## Task 3 — Multi-environment values (3 pts)

**Objective:** Drive ≥ 2 environments from one chart using a base + override values hierarchy.

### 3.1 — Create `values-prod.yaml` (and optionally `values-dev.yaml` / `values-staging.yaml`)

`YOUR TASK`: write a **deltas-only** override file — only the keys that differ from `values.yaml`. Suggested shape:

| | dev (defaults in `values.yaml`) | prod (`values-prod.yaml`) |
|---|---|---|
| `replicaCount` | 1 | 4 |
| `image.tag` | `""` (→ `appVersion`) | a pinned SemVer, e.g. `v1.2.0` |
| `service.type` | `NodePort` | `LoadBalancer` |
| `resources.requests.cpu` | `100m` | `500m` |
| `resources.limits.memory` | `256Mi` | `1Gi` |

For ≥ 3 envs, add `values-staging.yaml` between them.

### 3.2 — Upgrade an existing release with a layered values hierarchy

This is the **headline proof** of Task 3 — the same chart, the same release, going from REVISION 1 to REVISION 2 because `-f` layered a prod override on top of the base.

```bash
helm upgrade demo k8s/lab10-app -n helm-demo \
  -f k8s/lab10-app/values.yaml \
  -f k8s/lab10-app/values-prod.yaml
# expected: STATUS deployed, REVISION 2
# expected: deploy/demo-lab10-app spec.replicas = your prod override (was 1 at REV 1)
```

Then run `helm list`, `kubectl get deploy ... -o jsonpath='{.spec.replicas}'`, and `helm history` to capture the evidence.

> **Values precedence (lowest → highest):**
> 1. `values.yaml` (chart default, **always loaded** — you don't have to pass it explicitly)
> 2. Each `-f file.yaml` in order — later files override earlier ones
> 3. `--set key=value` on the CLI
>
> So `-f values.yaml -f values-prod.yaml --set replicaCount=10` ends with 10 replicas.

### 3.3 — Render a per-env diff without a cluster

`YOUR TASK`: use `helm template` against the chart **without** and **with** `-f values-prod.yaml`, then `diff` the two outputs. The visible delta is your proof the override file did something — no cluster required. Capture the first ~20 diff lines in `HELM.md`.

### 3.4 — Rollback

`YOUR TASK`: `helm rollback demo 1 -n helm-demo`, then re-query the deployment's replica count — it must return to the dev default. Capture `helm history` showing REVISION 3 with the rollback description.

### 3.5 — Proof of work

Paste into `HELM.md`:

- The contents of `values-prod.yaml` (deltas only — should be short)
- `helm list -n helm-demo` **at REVISION 2**, captured after the upgrade
- `kubectl get deploy ... -o jsonpath='{.spec.replicas}'` returning the prod value
- `helm history demo` showing REVISION 1 superseded by REVISION 2
- The first 20 lines of the `diff` from 3.3 — the visible delta between rendered envs

---

## Task 4 — Lifecycle hooks (2 pts)

**Objective:** Add **one** Job hook that runs at `pre-install` AND `pre-upgrade` (e.g. a fake DB migration), ordered by `hook-weight`, cleaned up by `hook-delete-policy`.

### 4.1 — Write `templates/hooks/db-migrate.yaml`

The four annotation keys are the entire hook contract — the rest is a normal `batch/v1` Job. `YOUR TASK`: write the file. The skeleton:

```yaml
{{- if .Values.hooks.dbMigrate.enabled }}
apiVersion: batch/v1
kind: Job
metadata:
  name: {{ ___ }}-db-migrate                  # YOUR TASK: fullname template + "-db-migrate"
  labels:
    {{- ___ | nindent 4 }}                    # YOUR TASK: labels template
  annotations:
    "helm.sh/hook": ___                       # YOUR TASK: TWO comma-separated points — pre-install,pre-upgrade
    "helm.sh/hook-weight": "___"              # YOUR TASK: a string, NOT a number (Helm quirk). Negative runs earlier.
    "helm.sh/hook-delete-policy": ___         # YOUR TASK: comma-separated policies — before-hook-creation,hook-succeeded
spec:
  backoffLimit: 1
  template:
    spec:
      restartPolicy: Never
      containers:
        - name: db-migrate
          image: {{ ___ }}                    # YOUR TASK: from .Values.hooks.dbMigrate.image
          command: ["sh", "-c"]
          args:
            - |
              echo "running pre-install/pre-upgrade migration for release {{ .Release.Name }}";
              sleep 5;
              echo "migration complete";
{{- end }}
```

The **four annotation keys** you must set (and what they do):

| Annotation | Required value here | What it does |
|---|---|---|
| `helm.sh/hook` | `pre-install,pre-upgrade` | When to run. Comma-separated for multiple points. |
| `helm.sh/hook-weight` | A quoted string like `"-5"` | Ordering among hooks at the same point. Lower runs first; ties broken alphabetically. **Must be a quoted string** — Helm parses it as a string and converts internally. |
| `helm.sh/hook-delete-policy` | `before-hook-creation,hook-succeeded` | When to remove the hook resource. Without this, failed Jobs pile up forever — `helm uninstall` does NOT delete hook resources. |
| (none — the resource is the Job itself) | — | The hook IS a normal Job, just not part of the regular release. |

### 4.2 — Verify the hook fires on install AND upgrade

`YOUR TASK`: uninstall the release for a clean slate, then re-install. During the install, run `kubectl get jobs -n helm-demo` (the hook Job should appear) and `kubectl logs job/<hook-job>` to capture your `running pre-install migration` echo. Then `helm upgrade` with `-f values-prod.yaml` and confirm the **same hook fires again** at `pre-upgrade`. Finally, re-query jobs — `before-hook-creation,hook-succeeded` should have deleted the previous one.

### 4.3 — Proof of work

Paste into `HELM.md`:

- Your `db-migrate.yaml` annotations block (the four-key contract)
- `kubectl get jobs -n helm-demo` captured **during** the install (Job present)
- `kubectl logs` from the hook Job showing your "running pre-install migration" echo
- `kubectl get jobs -n helm-demo` captured **after** the policy triggers (Job gone)

---

## Task 5 — Documentation (1 pt)

`YOUR TASK`: create `k8s/lab10-app/HELM.md` covering, in this order:

1. **Chart overview** — directory tree, what each template renders, the `values.yaml` contract
2. **Configuration** — table of the top-level values and how `values-prod.yaml` differs from defaults
3. **Helpers** — your four named templates and one sentence on why `selectorLabels` is a subset of `labels`
4. **Hook** — the four annotations on your `db-migrate` Job and what each one does
5. **Operations** — the exact `install`, `upgrade -f a -f b`, `history`, `rollback`, `uninstall` commands you ran
6. **Evidence** — all the captures from Tasks 1.3 / 2.8 / 3.5 / 4.3
7. **Challenges & learnings** — at least one real one (`indent`/`nindent` bug, immutable selector, `hook-weight` not quoted, etc.)

---

## Bonus Task — Publish to GHCR via OCI (2 pts)

**Objective:** Package the chart, push it to GHCR as an OCI artifact, then **install it from the registry** to prove the round-trip.

`YOUR TASK`: less hand-holding here.

1. `helm package` your chart into `lab10-app-<version>.tgz`.
2. Log in to `ghcr.io` with a GitHub PAT (scope `write:packages`). In CI you'd use `GITHUB_TOKEN`; locally use a PAT. **Never paste the PAT in a committed file.**
3. `helm push <tgz> oci://ghcr.io/<your-username>/charts`.
4. Make the GHCR package **public** (Package settings → Change visibility) so your grader can pull it.
5. In a fresh namespace, `helm install … oci://ghcr.io/<your-username>/charts/lab10-app --version <ver>` — and prove the install came **from the registry**, not your local directory (the `STATUS` will show the OCI source).

Commands you'll need (look them up — `helm package`, `helm registry login`, `helm push`, `helm install oci://...`). Pipe the PAT to login via `--password-stdin`; **never** put it on the command line (lands in shell history).

Paste into `HELM.md`:

- The `helm package` output
- The `helm push` output **with the digest**
- The GHCR package URL (e.g. `https://github.com/users/<you>/packages/container/package/charts%2Flab10-app`)
- The `helm install oci://…` output and `helm list` showing the OCI-sourced release

---

## How to Submit

Same flow as Lab 9: branch `lab10`, add `k8s/lab10-app/`, commit, push, open **two** PRs.

```bash
git switch -c lab10
git add k8s/lab10-app/
git commit -m "feat(lab10): package web + echo as a helm 4 chart"
git push -u origin lab10
```

PRs:

- `your-fork:lab10` → `course-repo:master` *(reviewed)*
- `your-fork:lab10` → `your-fork:master` *(merges into your own main when done)*

PR checklist:

```text
- [ ] Task 1 done — helm v4.1.x, public chart inspected, concepts explained
- [ ] Task 2 done — Chart.yaml, values.yaml, _helpers.tpl (4 templates), deployment + service + echo manifests, lint clean, REVISION 1 installed
- [ ] Task 3 done — values-prod.yaml + `helm upgrade -f base -f override` → REVISION 2 with replica count change
- [ ] Task 4 done — pre-install/pre-upgrade hook with the four annotations, hook fires + cleans up
- [ ] Task 5 done — HELM.md with all seven sections + evidence
- [ ] Bonus done — chart pushed to GHCR via OCI and installed from the registry
```

---

## Acceptance Criteria

### Task 1 (1 pt)
- ✅ `helm version` reports v4.1.x
- ✅ A public OCI chart inspected via `helm show chart` / `helm show values`
- ✅ Chart / Release / Values explained in your own words

### Task 2 (3 pts)
- ✅ `Chart.yaml` with the correct `apiVersion`, SemVer `version`, and `appVersion`
- ✅ `values.yaml` with every Lab 9 hardcoded value exposed (replicas, image, ports, resources, probes, echo block)
- ✅ `_helpers.tpl` defines and uses **four** named templates: `name`, `fullname`, `labels`, `selectorLabels`
- ✅ `selectorLabels` is a strict subset of `labels` (no `version` in it)
- ✅ All four manifest templates render via `include`, `nindent`, `default`, `with`
- ✅ Liveness + readiness probes kept and value-configurable
- ✅ `helm lint` is clean and `helm install` reaches REVISION 1

### Task 3 (3 pts)
- ✅ `values-prod.yaml` (and optionally dev/staging) contains **only deltas** from `values.yaml`
- ✅ `helm upgrade ... -f values.yaml -f values-prod.yaml` produces REVISION 2
- ✅ A real value (replica count) visibly changes between revisions
- ✅ `helm rollback` returns the release to REVISION 1

### Task 4 (2 pts)
- ✅ One Job hook with `helm.sh/hook: pre-install,pre-upgrade`
- ✅ `helm.sh/hook-weight` set (quoted string)
- ✅ `helm.sh/hook-delete-policy` set so the Job is cleaned up
- ✅ Hook fires on both install and upgrade; logs captured

### Task 5 (1 pt)
- ✅ `HELM.md` covers all seven required sections with the captures pasted in

### Bonus (2 pts)
- ✅ Chart packaged to `.tgz`
- ✅ Pushed to `oci://ghcr.io/<username>/charts`
- ✅ Installed *from the registry* (not from the local directory)
- ✅ GHCR URL + install-from-OCI output in `HELM.md`

---

## Rubric

| Task | Points | Criteria |
|------|-------:|----------|
| **Task 1** — Fundamentals | **1** | v4.1.x, public chart inspected, concepts explained |
| **Task 2** — Chart build | **3** | Clean templating, four helpers, lint clean, install reaches REVISION 1 |
| **Task 3** — Multi-env | **3** | `-f a -f b` layering produces REVISION 2 with a visible value change; rollback works |
| **Task 4** — Hooks | **2** | Pre-install/pre-upgrade hook with weight + delete policy; fires and cleans up |
| **Task 5** — Documentation | **1** | Complete `HELM.md` with evidence |
| **Bonus** — OCI push | **2** | Chart packaged, pushed to GHCR, installed *from the registry* |
| **Total** | **12** | 10 main + 2 bonus |

**Grading:**
- **10/10:** Clean templating from scratch, multi-env upgrade visible across revisions, hook fires + cleans up, thorough docs
- **8–9/10:** Chart installs and upgrades, minor gaps in helpers or hook annotations
- **6–7/10:** Basic chart installs but multi-env upgrade or hook polish missing
- **<6/10:** `helm create` boilerplate submitted, hardcoded values, no hook, or chart doesn't lint

---

## Resources

<details>
<summary>📚 Documentation</summary>

- [Helm Documentation](https://helm.sh/docs/) — Helm 4
- [Chart Template Guide](https://helm.sh/docs/chart_template_guide/)
- [Chart Best Practices](https://helm.sh/docs/chart_best_practices/)
- [Chart Hooks](https://helm.sh/docs/topics/charts_hooks/)
- [Use OCI-based registries](https://helm.sh/docs/topics/registries/)
- [Sprig function reference](https://masterminds.github.io/sprig/) — the function library you'll consult weekly
- [Built-in Objects](https://helm.sh/docs/chart_template_guide/builtin_objects/) — `.Release`, `.Chart`, `.Values`, `.Files`, `.Capabilities`

</details>

<details>
<summary>🛠️ Tools & Registries</summary>

- [Artifact Hub](https://artifacthub.io/) — public chart search (15,000+ charts)
- [helm-docs](https://github.com/norwoodj/helm-docs) — auto-generate README from values
- [chart-testing](https://github.com/helm/chart-testing) — lint & install charts in CI
- [GHCR](https://docs.github.com/en/packages/working-with-a-github-packages-registry/working-with-the-container-registry) — OCI registry for both images and charts

</details>

<details>
<summary>⚠️ Common Pitfalls (from real dry-runs)</summary>

- **`helm create` overwrites your work.** Running it inside an existing chart directory clobbers your hand-written `Chart.yaml`, `values.yaml`, and helpers without asking. Don't run it. Write the files yourself — this lab grades that skill.
- **Replacing the whole `helm create` `values.yaml` breaks `helm lint`.** The generated boilerplate ships a `templates/serviceaccount.yaml` that references `.Values.serviceAccount.create`. The moment you blow away that block in `values.yaml`, `helm lint` errors out because the referenced key vanished. Either edit the defaults in place **or** (recommended) skip `helm create` entirely. *(This is the exact self-inflicted snag from the lab's own reference run.)*
- **`indent` vs `nindent`.** `nindent N` = newline + N spaces; `indent N` = N spaces only. When a `{{- ... -}}` action has already eaten the previous newline, `indent` produces invalid YAML that `helm lint` will catch and `helm install` will refuse. Use `nindent` unless you're sure.
- **Mutable selector labels break rolling updates.** Once a `Deployment` exists, K8s rejects changes to `spec.selector.matchLabels`. If `version` is in your selector labels, every `appVersion` bump triggers a chart upgrade that K8s refuses — you'll have to `kubectl delete deploy ...` and lose zero-downtime. Keep `selectorLabels` to `name` + `instance` only.
- **`hook-weight` must be a quoted string.** `"helm.sh/hook-weight": -5` (unquoted) silently parses as a number and Helm ignores it; you'll get non-deterministic hook ordering. Always quote: `"helm.sh/hook-weight": "-5"`.
- **Hook resources outlive `helm uninstall`.** Hook Jobs are *not* part of the release. Without `hook-delete-policy`, failed Jobs pile up forever and `helm uninstall` won't remove them. Always set `before-hook-creation,hook-succeeded`.
- **Forgetting `helm dependency update` after editing `Chart.yaml`.** If you add a `dependencies:` entry (not required in this lab, but easy to add for the bonus), the subchart isn't downloaded into `charts/` until you run `helm dependency update`. `helm install` then fails with a missing-dependency error that's confusingly worded.
- **OCI auth gotcha.** `helm registry login ghcr.io` uses Docker config, not a separate Helm credential store. If a stale Docker login exists for `ghcr.io`, you may need `docker logout ghcr.io` first. Always pipe the PAT via `--password-stdin`; never put it on the command line (it lands in your shell history).
- **`apiVersion: v2` vs `v1` in `Chart.yaml`.** `v2` is the chart-format version introduced by Helm 3 and still used by Helm 4 — **not** the Helm binary version. `v1` is Helm 2 only. Helm 4 against a `v1` chart fails immediately; Helm 3 against a `v2` chart works. Always write `apiVersion: v2`.
- **Empty `image.tag` in `values.yaml`.** Setting `tag: ""` lets `{{ .Values.image.tag | default .Chart.AppVersion }}` fall back. Setting `tag: latest` defeats reproducibility (kills rollbacks and breaks ArgoCD diff in Lab 13). Leave it empty in defaults; pin a SemVer in `values-prod.yaml`.

</details>

<details>
<summary>📖 Learning Resources</summary>

- [Quickstart Guide](https://helm.sh/docs/intro/quickstart/)
- [Using Helm](https://helm.sh/docs/intro/using_helm/)
- [Three Big Concepts](https://helm.sh/docs/intro/using_helm/#three-big-concepts)
- *Learning Helm* (2e, 2024) — Butcher, Farina, Dolitsky (O'Reilly)

</details>

---

## Looking Ahead

| Lab | What it adds to this chart |
|---:|---|
| 11 | Secrets management with OpenBao — because `values.yaml` is git-tracked and your DB password isn't |
| 12 | ConfigMaps + PVCs added as new templates in this same chart |
| 13 | ArgoCD deploys this chart via GitOps; `helm template` becomes the rendering step |
| 14 | Argo Rollouts replaces the Deployment template with a Rollout for canary delivery |
| 16 | kube-prometheus-stack (a Helm chart itself) scrapes your app via a ServiceMonitor you add to this chart |

---

**Good luck!** ⛵

> **Remember:** Template everything, hardcode nothing (except sensible defaults in `values.yaml`). One chart, N value files. Never comment out a health check — make it a value instead. And **never** run `helm create` inside this lab.
