# Lab 10 — Helm Package Manager

![difficulty](https://img.shields.io/badge/difficulty-intermediate-yellow)
![topic](https://img.shields.io/badge/topic-Helm-blue)
![points](https://img.shields.io/badge/points-10%2B2-orange)
![tech](https://img.shields.io/badge/tech-Helm%204-informational)

> Package your Lab 9 Kubernetes manifests into a reusable, configurable Helm chart that ships through dev, staging, and prod with one value file per environment.

## Overview

In Lab 9 you deployed your apps with raw YAML — a Deployment and Service per service, copied and hand-edited. That stops scaling around the second environment. This lab converts those manifests into a single **Helm chart**: parameterized templates, a `values.yaml` per environment, lifecycle hooks, and an OCI push to GHCR.

**What You'll Learn:**
- Helm 4 chart anatomy: `Chart.yaml`, `values.yaml`, `templates/`, `_helpers.tpl`
- Go templates + Sprig functions, named templates, `include`, `nindent`
- The release lifecycle: `install / upgrade / rollback / lint / template / test`
- Multi-environment delivery via a values hierarchy (dev / staging / prod)
- Lifecycle hooks (pre-install / post-install) with weights and delete policies
- Publishing charts as OCI artifacts to GHCR

**Tech Stack:** Helm 4.1.4 | Kubernetes 1.33+ | Go templating + Sprig | GHCR (OCI)

> **Helm version note:** This course standardizes on **Helm 4** (4.1.4, released April 2026). Helm 3 is in support mode only (bug fixes through July 2026). Most Helm 3 syntax carries over unchanged — `apiVersion: v2` in `Chart.yaml` is still correct in Helm 4 — but run all commands below with a Helm 4.1+ binary so output and behavior match.

---

## Tasks

Main tasks sum to **10 points**. The bonus is worth **2 points**.

### Task 1 — Helm Fundamentals & Setup (1 pt)

**Objective:** Install Helm 4 and understand charts, releases, and values before you build one.

**Requirements:**

1. **Install Helm 4** and verify the version is **4.1.x**.
2. **Explore a public chart** to see real-world structure — pull and inspect one chart from an OCI registry (e.g. Bitnami) without installing it.
3. **Document** the three core concepts in your own words: **Chart**, **Release**, **Values**.

```bash
# Install (or upgrade) Helm — see https://helm.sh/docs/intro/install/
helm version            # must report v4.1.x

# Inspect a public chart from an OCI registry (no install)
helm show chart oci://registry-1.docker.io/bitnamicharts/nginx
helm show values oci://registry-1.docker.io/bitnamicharts/nginx | head -40
```

<details>
<summary>💡 The three concepts you must be able to explain</summary>

- **Chart** — a package of templated Kubernetes resources (the `.deb`/`.rpm` of K8s).
- **Release** — one installed instance of a chart in a cluster, with a tracked revision history.
- **Values** — the configuration inputs (`values.yaml` + `-f` files + `--set`) that fill the templates.

Helm 4 keeps `apiVersion: v2` charts (the Helm 3 format). No Tiller — release state lives in Secrets in the release namespace.

Reference: [Three Big Concepts](https://helm.sh/docs/intro/using_helm/#three-big-concepts)

</details>

**Documentation required:** terminal output of `helm version` (showing 4.1.x), output of the `helm show chart` exploration, and a 2-3 sentence explanation of Chart vs Release vs Values.

---

### Task 2 — Build the Chart (3 pts)

**Objective:** Convert your Lab 9 manifests (the **web** app and the **echo** app) into one Helm chart with clean templating.

Create the chart under `k8s/lab10-app/`. Below is the **skeleton you must produce** — files marked `YOUR-TASK` are the ones *you* write (that is the skill this lab grades). Do not run `helm create` and submit the generated boilerplate untouched; build the templates from your Lab 9 YAML.

```
k8s/lab10-app/
├── Chart.yaml                 # provided shape below — fill metadata
├── values.yaml                # YOUR-TASK: extract every hardcoded value here
├── values.schema.json         # optional, used in the bonus
├── values-dev.yaml            # Task 3
├── values-staging.yaml        # Task 3
├── values-prod.yaml           # Task 3
└── templates/
    ├── _helpers.tpl           # YOUR-TASK: name + label named templates
    ├── deployment.yaml        # YOUR-TASK: templatize Lab 9 web Deployment
    ├── service.yaml           # YOUR-TASK: templatize Lab 9 web Service
    ├── echo-deployment.yaml   # YOUR-TASK: templatize Lab 9 echo Deployment
    ├── echo-service.yaml      # YOUR-TASK: templatize Lab 9 echo Service
    ├── hooks/                 # Task 4
    └── NOTES.txt              # optional: printed after install
```

**Requirements:**

1. **`Chart.yaml`** — `apiVersion: v2`, a real `name`, `description`, `type: application`, a SemVer `version`, and an `appVersion`. Add `kubeVersion: ">=1.33.0"`.
2. **`values.yaml`** — every value that was hardcoded in Lab 9 (image repo/tag, replica count, service type/ports, resource requests/limits, probe settings) must be a value with a sensible default. Both `web` and `echo` get their own value blocks.
3. **`_helpers.tpl`** — define at least `name`, `fullname`, `labels`, and `selectorLabels` named templates and use them in your manifests via `include`.
4. **Templates** — render the four Lab 9 manifests from values. Image must be `"{{ .Values.image.repository }}:{{ .Values.image.tag | default .Chart.AppVersion }}"`.
5. **Keep the health checks.** Liveness and readiness probes stay — make them configurable via values, never comment them out.

`Chart.yaml` you start from:

```yaml
apiVersion: v2                 # correct for Helm 4 (NOT v1)
name: lab10-app
description: DevOps Core Lab 10 — web + echo packaged as a Helm chart
type: application
version: 0.1.0                 # chart version (SemVer); bump on chart changes
appVersion: "1.0.0"            # app version; bump on image changes
kubeVersion: ">=1.33.0"
```

<details>
<summary>💡 Templating idioms you will need</summary>

```yaml
# values lookup with a fallback
replicas: {{ .Values.web.replicaCount | default 2 }}

# call a named template and indent the result
metadata:
  labels:
    {{- include "lab10-app.labels" . | nindent 4 }}

# render a values sub-tree as YAML (e.g. resources, probes)
{{- with .Values.web.resources }}
resources:
  {{- toYaml . | nindent 12 }}
{{- end }}
```

- `include` (not `template`) returns a string you can pipe.
- `nindent N` = newline + indent by N spaces. The single most common Helm bug is using `indent` where you needed `nindent`.
- `{{- ... -}}` trims surrounding whitespace.

Reference: [Chart Template Guide](https://helm.sh/docs/chart_template_guide/)

</details>

<details>
<summary>💡 `_helpers.tpl` starting point (adapt the chart name)</summary>

```handlebars
{{- define "lab10-app.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" }}
{{- end }}

{{- define "lab10-app.fullname" -}}
{{- $name := default .Chart.Name .Values.nameOverride -}}
{{- printf "%s-%s" .Release.Name $name | trunc 63 | trimSuffix "-" }}
{{- end }}

{{- define "lab10-app.labels" -}}
helm.sh/chart: {{ printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" | trunc 63 | trimSuffix "-" }}
{{ include "lab10-app.selectorLabels" . }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end }}

{{- define "lab10-app.selectorLabels" -}}
app.kubernetes.io/name: {{ include "lab10-app.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}
```

`selectorLabels` is a strict subset of `labels` — selectors are immutable after a Deployment exists, so never put `version` in them.

</details>

**Validate as you go:**

```bash
helm lint k8s/lab10-app
helm template demo k8s/lab10-app                 # render to stdout, inspect the YAML
helm install demo k8s/lab10-app --dry-run --debug
helm install demo k8s/lab10-app -n demo --create-namespace
```

**Documentation required:** `helm lint` output, a snippet of `helm template` showing values flowing into the rendered Deployment, and `kubectl get all -n <ns>` proving both web and echo are running.

---

### Task 3 — Multi-Environment Values (3 pts)

**Objective:** Drive three environments from one chart using a base + override values hierarchy.

**Requirements:**

1. Create **`values-dev.yaml`**, **`values-staging.yaml`**, and **`values-prod.yaml`**. Each holds only the *deltas* from `values.yaml` — do not duplicate the whole file.
2. Make the environments meaningfully different. Suggested shape:

   | | dev | staging | prod |
   |---|---|---|---|
   | replicas (web) | 1 | 2 | 3+ |
   | image.tag | `latest` | a pinned tag | a pinned SemVer |
   | service.type | NodePort | NodePort | LoadBalancer |
   | resources | relaxed | medium | full requests+limits |

3. **Install all three** into separate namespaces and prove the rendered config differs.

```bash
helm install web-dev     k8s/lab10-app -n dev     --create-namespace -f k8s/lab10-app/values-dev.yaml
helm install web-staging k8s/lab10-app -n staging --create-namespace -f k8s/lab10-app/values-staging.yaml
helm install web-prod    k8s/lab10-app -n prod    --create-namespace -f k8s/lab10-app/values-prod.yaml

# prove they differ without a cluster
helm template web-prod k8s/lab10-app -f k8s/lab10-app/values-prod.yaml | grep -E "replicas|image:|type:"
```

<details>
<summary>💡 Values precedence (lowest → highest)</summary>

1. `values.yaml` (chart defaults)
2. each `-f file.yaml` (later files override earlier ones)
3. `--set key=value` on the CLI

So `-f values.yaml -f values-prod.yaml --set web.replicaCount=10` ends with 10 replicas. You usually don't need to pass `values.yaml` explicitly — Helm always loads it as the base.

</details>

**Documentation required:** the three values files, the install commands, and evidence (`kubectl get deploy -A` or per-namespace `helm template | grep`) that replicas / image tag / service type differ per environment.

---

### Task 4 — Lifecycle Hooks (2 pts)

**Objective:** Run a Job at specific points in the release lifecycle.

**Requirements:**

1. **Pre-install hook** — a Job that runs *before* the main resources (e.g. a fake DB migration / readiness check). Use `hook-weight` so it runs first.
2. **Post-install hook** — a Job that runs *after* everything is installed (e.g. a smoke test / notification).
3. Both hooks set a **`hook-delete-policy`** so they clean up after themselves.
4. **Verify** the hooks render (`helm template`), execute on install, and are removed per policy.

The hook templates live under `k8s/lab10-app/templates/hooks/` and are `YOUR-TASK`. Pattern:

```yaml
apiVersion: batch/v1
kind: Job
metadata:
  name: "{{ include "lab10-app.fullname" . }}-pre-install"
  labels:
    {{- include "lab10-app.labels" . | nindent 4 }}
  annotations:
    "helm.sh/hook": pre-install
    "helm.sh/hook-weight": "-5"
    "helm.sh/hook-delete-policy": before-hook-creation,hook-succeeded
spec:
  template:
    spec:
      restartPolicy: Never
      containers:
        - name: pre-install
          image: busybox:1.37
          command: ["sh", "-c", "echo running pre-install migration && sleep 5 && echo done"]
```

<details>
<summary>💡 Hook reference</summary>

- **Hook points:** `pre-install`, `post-install`, `pre-upgrade`, `post-upgrade`, `pre-delete`, `post-delete`, `test`.
- **`hook-weight`** orders multiple hooks at the same point — lower runs first; ties broken alphabetically.
- **`hook-delete-policy`:** `before-hook-creation` (default), `hook-succeeded`, `hook-failed`. Without one, failed hook Jobs accumulate — `helm uninstall` does **not** delete hook resources.

Reference: [Chart Hooks](https://helm.sh/docs/topics/charts_hooks/)

</details>

```bash
helm install demo k8s/lab10-app -n demo --create-namespace
kubectl get jobs -n demo            # watch the hook Job appear and complete
kubectl logs -n demo job/<release>-pre-install
kubectl get jobs -n demo            # confirm it was deleted per policy
```

**Documentation required:** both hook templates, `kubectl get jobs` showing execution, hook Job logs, and a confirmation that the delete policy cleaned them up.

---

### Task 5 — Documentation (1 pt)

**Objective:** Document the chart so a teammate can operate it.

Create **`k8s/lab10-app/HELM.md`** covering:

1. **Chart overview** — structure, what each template renders, how values are organized.
2. **Configuration** — the key values and how the three environments differ.
3. **Hooks** — what you implemented, the weights, and the delete policies (and why).
4. **Operations** — the exact `install`, `upgrade`, `rollback`, and `uninstall` commands you ran.
5. **Evidence** — `helm list -A`, `kubectl get all`, hook output, and proof of a per-environment difference.

```bash
# the operations you should be able to demonstrate
helm upgrade web-dev k8s/lab10-app -n dev -f k8s/lab10-app/values-dev.yaml --set web.image.tag=v1.0.1
helm history web-dev -n dev
helm rollback web-dev 1 -n dev
helm uninstall web-dev -n dev
```

---

## Bonus Task — Publish to GHCR via OCI (2 pts)

**Objective:** Package the chart and push it to GitHub Container Registry as an OCI artifact, then install it straight from the registry.

**Requirements:**

1. **Package** the chart into a `.tgz`.
2. **Log in** to GHCR with a GitHub PAT (scope `write:packages`).
3. **Push** the chart to `oci://ghcr.io/<your-username>/charts`.
4. **Pull and install** the chart *from the registry* (not the local directory) to prove the round-trip works.
5. **Document** the published artifact (GHCR package URL) and the install-from-OCI command.

```bash
# 1. package → produces lab10-app-0.1.0.tgz
helm package k8s/lab10-app

# 2. auth (use a PAT, never your password; CI would use GITHUB_TOKEN)
echo $GHCR_PAT | helm registry login ghcr.io -u <your-username> --password-stdin

# 3. push
helm push lab10-app-0.1.0.tgz oci://ghcr.io/<your-username>/charts

# 4. install from the registry
helm install web-oci oci://ghcr.io/<your-username>/charts/lab10-app \
  --version 0.1.0 -n oci-test --create-namespace
```

<details>
<summary>💡 Why OCI for charts?</summary>

Since 2022 Helm pushes/pulls charts using the same OCI protocol as container images: one registry, one auth model, one set of access controls for both your images and your charts. It replaced the legacy `helm repo add` HTTP index model. GHCR, Docker Hub, Harbor, and ECR all support OCI artifacts.

Make the GHCR package **public** (or grant your grader access) so the install-from-OCI step is reproducible.

Reference: [Use OCI-based registries](https://helm.sh/docs/topics/registries/)

</details>

**Documentation required:** the package + push terminal output, the GHCR package URL, and the successful `helm install oci://...` output.

---

## How to Submit

1. **Create Branch:**
   ```bash
   git checkout -b lab10
   ```

2. **Commit Work:**
   ```bash
   git add k8s/lab10-app/
   git commit -m "feat: package lab09 manifests into a helm chart (lab10)"
   git push -u origin lab10
   ```

3. **Create Pull Requests:**
   - **PR #1:** `your-fork:lab10` → `course-repo:master`
   - **PR #2:** `your-fork:lab10` → `your-fork:master`

4. **Verify:**
   - Chart lints clean and installs
   - Three environment value files present and demonstrably different
   - Hooks execute and clean up
   - `k8s/lab10-app/HELM.md` complete with evidence

---

## Acceptance Criteria

### Main Tasks (10 points)

**Fundamentals & Setup (1 pt):**
- [ ] Helm reports v4.1.x
- [ ] A public chart inspected via `helm show`
- [ ] Chart / Release / Values explained

**Build the Chart (3 pts):**
- [ ] `Chart.yaml` with `apiVersion: v2`, SemVer `version`, and `appVersion`
- [ ] Web + echo manifests templated from values (nothing hardcoded)
- [ ] `_helpers.tpl` defines and uses `name` / `fullname` / `labels` / `selectorLabels`
- [ ] Liveness + readiness probes kept and value-configurable (not commented out)
- [ ] `helm lint` passes and the chart installs

**Multi-Environment Values (3 pts):**
- [ ] `values-dev.yaml`, `values-staging.yaml`, `values-prod.yaml` created (deltas only)
- [ ] Replicas / image tag / service type / resources differ per environment
- [ ] All three render or install and the differences are shown

**Lifecycle Hooks (2 pts):**
- [ ] Pre-install hook with negative `hook-weight`
- [ ] Post-install hook
- [ ] `hook-delete-policy` set on both
- [ ] Hooks execute and are cleaned up per policy (shown)

**Documentation (1 pt):**
- [ ] `k8s/lab10-app/HELM.md` covers overview, config, hooks, operations, and evidence

### Bonus Task (2 points)

- [ ] Chart packaged to `.tgz`
- [ ] Pushed to `oci://ghcr.io/<username>/charts`
- [ ] Installed *from the registry* (not the local path)
- [ ] GHCR package URL + install-from-OCI output documented

---

## Rubric

| Criteria | Points | Description |
|----------|--------|-------------|
| **Fundamentals** | 1 pt | Helm 4 installed, concepts explained |
| **Chart Build** | 3 pts | Proper templating, values, helpers, probes kept |
| **Multi-Environment** | 3 pts | dev/staging/prod values, demonstrably different |
| **Hooks** | 2 pts | Pre/post-install hooks with weights + delete policy |
| **Documentation** | 1 pt | Complete `HELM.md` with evidence |
| **Bonus** | 2 pts | OCI package + push + install from GHCR |
| **Total** | 12 pts | 10 pts required + 2 pts bonus |

**Grading:**
- **10/10:** Clean templating, three working environments, hooks fire and clean up, thorough docs
- **8-9/10:** Chart installs, hooks work, minor best-practice gaps
- **6-7/10:** Basic chart works, missing multi-env or hook polish
- **<6/10:** Chart doesn't install, hardcoded values, commented-out probes

---

## Resources

<details>
<summary>📚 Official Helm Documentation</summary>

- [Helm Documentation](https://helm.sh/docs/) (Helm 4)
- [Chart Template Guide](https://helm.sh/docs/chart_template_guide/)
- [Chart Best Practices](https://helm.sh/docs/chart_best_practices/)
- [Chart Hooks](https://helm.sh/docs/topics/charts_hooks/)
- [Use OCI-based registries](https://helm.sh/docs/topics/registries/)

</details>

<details>
<summary>🎓 Learning Resources</summary>

- [Quickstart Guide](https://helm.sh/docs/intro/quickstart/)
- [Using Helm](https://helm.sh/docs/intro/using_helm/)
- [Built-in Objects](https://helm.sh/docs/chart_template_guide/builtin_objects/)
- [Sprig function reference](https://masterminds.github.io/sprig/)
- *Learning Helm* (2e, 2024) — Butcher, Farina, Dolitsky (O'Reilly)

</details>

<details>
<summary>🛠️ Tools & Registries</summary>

- [Helm](https://helm.sh/) — official site
- [Artifact Hub](https://artifacthub.io/) — public chart search
- [helm-docs](https://github.com/norwoodj/helm-docs) — generate docs from values
- [chart-testing](https://github.com/helm/chart-testing) — lint and test charts in CI
- [GitHub Container Registry (GHCR)](https://docs.github.com/en/packages/working-with-a-github-packages-registry/working-with-the-container-registry)

</details>

---

## Looking Ahead

- **Lab 11:** Secrets management with OpenBao — because `values.yaml` is git-tracked and your DB password isn't
- **Lab 12:** ConfigMaps and persistent volumes
- **Lab 13:** ArgoCD deploys your Helm chart via GitOps
- **Lab 14:** Progressive delivery with Argo Rollouts
- **Lab 15:** StatefulSets for stateful applications

---

**Good luck!** ⛵

> **Remember:** Template everything, hardcode nothing (except sensible defaults). One chart, N value files. And never comment out a health check — make it a value instead.
