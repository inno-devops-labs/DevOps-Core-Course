# Lab 2 — Docker Containerization

![difficulty](https://img.shields.io/badge/difficulty-beginner-success)
![topic](https://img.shields.io/badge/topic-Containerization-blue)
![points](https://img.shields.io/badge/points-10%2B2-orange)
![tech](https://img.shields.io/badge/tech-Docker%2029-informational)

> **Goal:** Containerize your Lab 1 service with a hand-written, multi-stage Dockerfile; scan the image; push it to a registry. By the end of this week you have *the* artifact that every later lab deploys.
> **Deliverable:** A PR from `lab02` adding `app_python/Dockerfile`, `.dockerignore`, a `docs/LAB02.md` report, and (optionally) the Go distroless bonus under `app_go/`.

---

## Overview

In Lab 1 your service "worked on your machine." This lab makes it **work everywhere**. The actual skill being graded is *writing a Dockerfile line-by-line*: which base image, in which order, as which user, with which entrypoint. The skeletons below show the **directives** but not the **values** — you fill those in and you defend the choice in `docs/LAB02.md`.

In this lab you will practice:
- Writing production-ready, layer-cache-friendly Dockerfiles by hand
- Running containers as a non-root user (defense-in-depth against container escape)
- Multi-stage builds for small, reproducible images
- Image vulnerability scanning with Trivy and CI-style exit-code gating
- Tagging by SemVer/SHA and pushing to a public registry

> ⚠️ **Scope:** Compose, Kubernetes, and CI gates come later. This lab is one service, one image, one registry.

**Tech stack (May 2026):** Docker Engine 29.x recommended (containerd image store default); **23+ also works** — BuildKit was on by default in 23 and `# syntax=docker/dockerfile:1` is honoured · `python:3.13-slim` · Trivy v0.69.3+

---

## Project State

**You should have from previous labs:**
- `app_python/` — the Flask/FastAPI/Django service from Lab 1 with `GET /` and `GET /health`
- *(optional)* `app_go/` (or other compiled-language sibling) from the Lab 1 bonus

**This lab adds:**
- `app_python/Dockerfile` — single-stage, then refactored to multi-stage
- `app_python/.dockerignore`
- `app_python/docs/LAB02.md` — your submission report
- A published image at `ghcr.io/<you>/devops-info-service:1.0.0` (or Docker Hub equivalent)
- *(bonus)* `app_go/Dockerfile` — multi-stage with a distroless final stage

By Lab 9 Kubernetes pulls this image; by Lab 13 ArgoCD ships new versions of it. The tag you push today is the artifact reference for the next 14 weeks.

---

## Setup

```bash
docker version              # Engine 29.x recommended; 23+ works (BuildKit on by default since 23); rootless OK
docker buildx version       # BuildKit is required (bundled)
trivy --version             # v0.69.3 or newer — NOT v0.69.4 (see warning below)
```

> ⚠️ **Trivy supply-chain warning.** Install **v0.69.3** or a later clean patch. **Never install `v0.69.4`** — that release was compromised (CVE-2026-33634, the March 2026 supply-chain attack). If you wire Trivy into GitHub Actions in Lab 3, pin `trivy-action@v0.35.0+` / `setup-trivy@v0.2.6+`.

> 🌐 **Trivy DB mirror.** On rate-limited or restricted networks the default DB pull from `ghcr.io/aquasecurity/trivy-db` returns `DENIED`. If that happens, pass `--db-repository public.ecr.aws/aquasecurity/trivy-db:2` to every `trivy image` call. This is the one operational gotcha worth remembering — your campus network might bite.

Create the layout (you'll write the contents yourself):

```
app_python/
├── Dockerfile             # YOU WRITE — Task 1 → refactor in Task 3
├── .dockerignore          # YOU WRITE — Task 1
├── README.md              # extend with a Docker section in Task 5
├── docs/
│   └── LAB02.md           # YOU WRITE — submission report
└── (your Lab 1 sources)
```

---

## Task 1 — Write a Production Dockerfile (3 pts)

### 1.1 — The single-stage Dockerfile

`YOUR TASK`: write `app_python/Dockerfile` from the skeleton below. Every `___` is yours. There is **no fully-formed example** in this lab — by the time a Dockerfile is given to you whole, it's not learning, it's typing practice. The lecture (slides 11, 13, 14, 15) explains the *why* for every line; bring it.

```dockerfile
# syntax=docker/dockerfile:1
FROM ___                  # YOUR TASK: pin a slim Python base. Why slim? Why pinned? (slide 15)
WORKDIR ___               # YOUR TASK: absolute path. Not / and not ~
RUN ___                   # YOUR TASK: create a NUMERIC non-root user (uid >= 10000)
COPY ___ ___              # YOUR TASK: one file FIRST — the one that changes rarely
RUN pip install --___ -r ___  # YOUR TASK: which flag stops pip from baking its cache into the layer?
COPY ___ ___              # YOUR TASK: app source LAST. Explain the layer-cache reasoning in docs
USER ___                  # YOUR TASK: switch to the numeric UID from above
EXPOSE ___                # YOUR TASK: which port does your Lab 1 app listen on?
# YOUR TASK (recommended): HEALTHCHECK pinging GET /health. slim has NO curl + NO wget — pick deliberately
CMD [___]                 # YOUR TASK: exec form, not shell form (PID 1 trap → SIGTERM lost)
```

**Each blank is a rubric line.** A "good" answer matches the lecture's reasoning; a "lucky" answer that compiles but can't be defended in `docs/LAB02.md` will lose points.

### 1.2 — `.dockerignore`

`YOUR TASK`: write `app_python/.dockerignore` so `COPY . .` doesn't ship `.git/`, virtualenvs, IDE configs, `__pycache__/`, or `.env` into the image.

```gitignore
# YOUR TASK: list at minimum
# - VCS metadata (the Toyota 2022 .git leak — slide 16)
# - Python caches (__pycache__, *.pyc)
# - Virtualenvs (.venv, venv/)
# - Local env files (.env)
# - Editor dirs (.idea/, .vscode/)
# - Docs/tests (not needed at runtime — smaller context, faster builds)
```

Hint: same syntax as `.gitignore`, but evaluated by the Docker build context — *not* git. A `.dockerignore` is mandatory for this task; missing it costs the entire `.dockerignore` rubric line.

### 1.3 — Proof of work

**Paste into `docs/LAB02.md`:**

- The contents of your `Dockerfile` (yes, the whole file — it's short and it's the artifact being graded)
- The contents of your `.dockerignore`
- A one-sentence justification per `# YOUR TASK` line — *why this value*, not *what it is*
- Output of `docker build -t devops-info-service:lab02 ./app_python` showing the final image hash (illustrative — your numbers will differ)

<details>
<summary>💡 Why each rule matters (read before you write)</summary>

- **Pinned slim base** — `python:3.13` ≈ 1.2 GB, `python:3.13-slim` ≈ 150 MB. Smaller image = faster pulls (Lab 9 K8s autoscale), fewer packages = fewer CVEs (Task 4). `:latest` is mutable so two builds from "the same Dockerfile" can produce different images.
- **Numeric non-root UID** — A kernel container-escape CVE (e.g. CVE-2022-0185) gives root on the host **if your process is root**. `USER 10001` neutralises it. Numeric (vs `USER appuser`) keeps working under `runAsNonRoot: true` admission policies you'll meet in Lab 9+.
- **Layer order (deps before code)** — Each instruction is a cached layer. `COPY . . && pip install` re-installs every dependency on every 1-character code change. `COPY requirements.txt . && pip install && COPY . .` re-uses the dep layer until `requirements.txt` actually changes.
- **`--no-cache-dir`** — pip's `~/.cache/pip` is tens of MB of wheels you never need at runtime. Layers are additive — deleting the cache in a later `RUN` does NOT remove it from the image; it just hides it behind another layer.
- **Exec form `CMD`** — Shell form: `/bin/sh -c "python app.py"` → sh is PID 1, your app is PID 2, signals never reach you. Exec form `["python","app.py"]` → your app *is* PID 1.
- **`.dockerignore`** — Toyota 2022: customer data leaked because `.git/` was packaged into a deployed image. Standard mitigation.

References: [Dockerfile best practices](https://docs.docker.com/build/building/best-practices/) · [Dockerfile reference](https://docs.docker.com/reference/dockerfile/)

</details>

---

## Task 2 — Build, Run, and Verify (2 pts)

### 2.1 — Build, run, hit the endpoints

`YOUR TASK`: build the image, run it, and prove both endpoints respond exactly like Lab 1. Capture the real CLI output.

```bash
# YOUR TASK: build it
docker build -t devops-info-service:lab02 ./app_python

# YOUR TASK: run it (background, host:container port mapping is yours to choose)
docker run -d --rm -p ___:___ --name lab02 devops-info-service:lab02

# YOUR TASK: hit both endpoints and capture the JSON
curl -s http://localhost:___/ | jq .
curl -s http://localhost:___/health | jq -c .
```

### 2.2 — Prove the container is non-root

`YOUR TASK`: run the same image with `id -u` as the entrypoint and capture the output. **It must NOT print `0`.**

```bash
docker run --rm devops-info-service:lab02 id -u
# YOUR TASK: paste the captured number into docs/LAB02.md
```

If you see `0`, your `USER ___` is missing or above the `COPY` that overwrites it. Re-order, rebuild, re-verify.

### 2.3 — Inspect the artifact

```bash
docker images devops-info-service --format '{{.Tag}}\t{{.Size}}'
docker history devops-info-service:lab02
```

`YOUR TASK`: read your own `docker history` output. In `docs/LAB02.md`, identify the **single largest layer** and explain in one sentence why it's that big — base image, deps, or your source code?

### 2.4 — Proof of work

**Paste into `docs/LAB02.md`:**

- Build log tail (last ~10 lines including the `=> exporting to image` step)
- Both endpoint JSONs from real `curl` runs
- The `id -u` line proving non-root (illustrative — `10001`, your value will differ if you picked another UID)
- `docker images` row showing your real size (illustrative — `~130 MB` is typical for a slim-based Flask app)
- One-sentence "biggest layer" analysis

---

## Task 3 — Multi-Stage Build (2 pts)

### 3.1 — Refactor to two stages

`YOUR TASK`: rewrite `app_python/Dockerfile` (or create `Dockerfile.multi`) as a multi-stage build. The **builder** stage installs deps into an isolated location; the **runtime** stage copies only what it needs and contains no `pip`, no build toolchain, no apt caches.

```dockerfile
# syntax=docker/dockerfile:1
# ---------- Stage 1: builder ----------
FROM ___ AS builder           # YOUR TASK: same slim base (or a fatter one if you need gcc for wheels)
WORKDIR ___                   # YOUR TASK: pick a build location
COPY requirements.txt .
RUN ___                       # YOUR TASK: install deps into an ISOLATED dir — venv at /opt/venv OR pip --prefix=/install

# ---------- Stage 2: runtime ----------
FROM ___ AS runtime           # YOUR TASK: same slim base — minimal final surface
RUN ___                       # YOUR TASK: numeric non-root user again (stages don't share USER)
WORKDIR ___                   # YOUR TASK: absolute path
COPY --from=builder ___ ___   # YOUR TASK: copy ONLY the deps dir from the builder
ENV PATH="___:$PATH"          # YOUR TASK: prepend your venv/prefix bin dir
COPY ___ ___                  # YOUR TASK: app source LAST
USER ___                      # YOUR TASK: numeric UID
EXPOSE ___                    # YOUR TASK: same port as Task 1
CMD [___]                     # YOUR TASK: exec form
```

### 3.2 — Build and compare

```bash
# If you replaced Dockerfile in-place:
docker build -t devops-info-service:lab02-multi ./app_python

# If you kept the single-stage as Dockerfile and put the multi-stage in Dockerfile.multi,
# pass it explicitly with -f (otherwise docker build picks the default Dockerfile):
docker build -f app_python/Dockerfile.multi -t devops-info-service:lab02-multi ./app_python

docker images devops-info-service --format '{{.Tag}}\t{{.Size}}'
```

`YOUR TASK`: capture both rows (`lab02` vs `lab02-multi`) and write a **one-paragraph** finding in `docs/LAB02.md`.

> ⚠️ **Honest finding you might hit:** for a **pure-Python** Flask app, the multi-stage image can be *slightly larger* (e.g. 133 vs 130 MB) than the single-stage — Flask has no compiled wheels, so there's no toolchain to discard, and the venv copy adds a few MB of metadata. **That's expected.** Document it; don't fake a size drop you didn't measure. The dramatic win comes for **compiled languages** (the Bonus) — there, multi-stage shrinks 60×.

### 3.3 — Proof of work

**Paste into `docs/LAB02.md`:**

- Your `Dockerfile.multi` contents
- `docker images` rows showing your real `lab02` vs `lab02-multi` sizes
- One paragraph: did multi-stage shrink the image, leave it about the same, or grow it slightly? Why? (If your answer doesn't reference compiled wheels / build toolchain, you didn't understand the lecture.)
- `curl -s localhost:___/health` from the multi-stage container — same response as Task 2

<details>
<summary>💡 Multi-stage concepts</summary>

- **Why two stages?** Builder may need a C compiler to build a wheel (e.g. `cryptography`, `psycopg2`). Runtime never does. `COPY --from=builder` is how you discard everything the runtime doesn't need.
- **Naming stages.** `FROM image AS builder`, then `COPY --from=builder /src /dst`. The `AS` name is the handle.
- **Where this shines.** Compiled languages. `golang:1.25` ≈ 900 MB; multi-stage to `distroless/static` ≈ 15 MB. Same binary, 60× smaller, zero shell, zero package manager. That's the Bonus.

Reference: [Multi-stage builds](https://docs.docker.com/build/building/multi-stage/)

</details>

---

## Task 4 — Scan with Trivy (2 pts)

### 4.1 — Full scan + gated scan

`YOUR TASK`: run two scans against your multi-stage image and capture both outputs.

```bash
# Full informational scan — lists every CVE by severity
trivy image devops-info-service:lab02-multi

# CI-style gate — fails (non-zero exit) on HIGH/CRITICAL findings.
# This is the exact gate you'll add to GitHub Actions in Lab 3.
trivy image --severity HIGH,CRITICAL --exit-code 1 devops-info-service:lab02-multi
echo "exit code: $?"
```

> 🌐 If the DB pull dies with `ghcr.io/aquasecurity/trivy-db: DENIED`, add `--db-repository public.ecr.aws/aquasecurity/trivy-db:2`. AWS hosts an anonymous mirror — Aqua publishes there explicitly because ghcr.io anonymous tokens get rate-limited.

### 4.2 — Severity table

`YOUR TASK`: fill in your **real** counts in `docs/LAB02.md` (the numbers below are illustrative — yours will differ depending on base-image freshness):

| Severity  | Count *(illustrative — your numbers will differ)* |
|-----------|--------:|
| CRITICAL  | 2 |
| HIGH      | 5 |
| MEDIUM    | 33 |
| LOW       | 63 |
| UNKNOWN   | 5 |
| **Total** | **108** |

### 4.3 — Explain one finding + remediate

`YOUR TASK`: pick **one** finding (ideally a HIGH or CRITICAL — easier to defend the priority). In `docs/LAB02.md` write **at least 3 sentences** covering:

1. The package + CVE id (e.g. `libncursesw6 6.5+20250216-2 — CVE-2025-69720`)
2. Why it's flagged — what the upstream advisory says
3. What you'd do — rebuild on a fresh `python:3.13-slim` (often fixes itself when Debian patches land), pin a fixed library version, switch to a smaller base (distroless has near-zero CVEs — see the Bonus), or document it as **unfixable today** (no upstream patch yet)

> 🚫 **Do NOT suppress findings via `.trivyignore`** to make the gate pass. If a CVE has no fix yet, document it explicitly. Hiding unfixed CVEs from CI is how you ship the next Log4Shell to prod.

### 4.4 — Proof of work

**Paste into `docs/LAB02.md`:**

- Full Trivy output (or a screenshot — long, but the table at the top is the load-bearing part)
- Your severity table with real numbers
- The gated scan command + its exit code
- Your one-finding explanation and remediation reasoning

<details>
<summary>💡 Why scan, why gate on exit code</summary>

- `trivy image <ref>` reports CVEs against OS packages **and** language dependencies (e.g. `requirements.txt`).
- `--severity HIGH,CRITICAL --exit-code 1` is the "fail the pipeline" idiom — by ignoring LOW/MEDIUM you keep the gate noise-free while still catching the dangerous stuff.
- Smaller base → fewer packages → fewer CVEs. Slim → distroless → scratch is a vulnerability-reduction ladder. The Bonus shows this concretely (Python slim ≈ 108 CVEs vs Go distroless ≈ 0).

Reference: [Trivy docs](https://trivy.dev/) · [Trivy `image` command](https://trivy.dev/latest/docs/target/container_image/)

</details>

---

## Task 5 — Push to a Registry & Document (1 pt)

### 5.1 — Tag + push

`YOUR TASK`: publish your image to **GHCR** (recommended — free for public, integrates with the Actions you'll write in Lab 3) or Docker Hub.

For **GHCR** (recommended): create a Personal Access Token (classic) with the `write:packages` scope, then:

```bash
# Put your token in a shell variable FIRST — do NOT paste the token onto the docker login
# line (it would land in your shell history). --password-stdin reads from stdin only.
export GHCR_PAT='ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx'

echo "$GHCR_PAT" | docker login ghcr.io -u <github-username> --password-stdin
docker tag devops-info-service:lab02-multi ghcr.io/<github-username>/devops-info-service:___   # YOUR TASK: real version tag
docker push ghcr.io/<github-username>/devops-info-service:___                                  # YOUR TASK: same tag
```

> 🤖 **In CI (Lab 3), don't use a PAT.** GitHub Actions provides an ephemeral `GITHUB_TOKEN` per run that has `write:packages` for the repo's own GHCR namespace. The Lab 3 docker job uses
> `password: ${{ secrets.GITHUB_TOKEN }}` — no long-lived PAT to leak. PATs are only for *your laptop today*.

> 📢 **GHCR packages are PRIVATE by default after first push.** The Acceptance Criteria below require *publicly pullable* — after `docker push` succeeds the first time, go to **your GitHub profile → Packages → `devops-info-service` → Package settings (right side) → Change visibility → Public**. Confirm by typing the package name. Without this step the `docker pull` from a clean cache below will work only because your login is still cached; a grader running `docker pull` without your token will get `401 Unauthorized`.

`YOUR TASK`: pick a tagging strategy and put the real tag in both blanks above. **Not `:latest`** — see slide 20. Pick one:

| Strategy   | Example       | When to use |
|------------|---------------|-------------|
| SemVer     | `1.0.0`       | A real release of the service |
| Git SHA    | `git-3a7f29c` | CI builds; always unique |
| CalVer     | `2026.05.0`   | Time-driven release cadence |

Verify it's actually pullable from a **truly clean state** — `docker logout` first so cached credentials don't mask a private-package mistake:

```bash
docker logout ghcr.io                                            # forget the PAT so we test the public path
docker rmi  ghcr.io/<github-username>/devops-info-service:___   # YOUR TASK: your tag
docker pull ghcr.io/<github-username>/devops-info-service:___   # YOUR TASK: must succeed anonymously (package must be Public)
```

If `docker pull` returns `unauthorized` after `docker logout`, your package is still private — flip its visibility to Public per the note above, then re-pull.

### 5.2 — Update `app_python/README.md`

`YOUR TASK`: add a **Docker** section to your Lab 1 README with three subsections:

1. **Build** — your `docker build` command
2. **Run** — your `docker run` command (host:container port mapping)
3. **Pull from registry** — the public pull command using your real registry URL

No need to paste the Dockerfile contents into the README — link to the file in the repo instead.

### 5.3 — `app_python/docs/LAB02.md` — submission report

Required sections (in order):

1. **Dockerfile decisions** — your Task 1 file + a *why* line per `YOUR TASK`
2. **Multi-stage results** — single-stage vs multi-stage size with real numbers and a one-line takeaway (including the honest "no change because pure Python" answer if that's what you measured)
3. **Trivy scan** — severity table with real counts, one finding explained, remediation reasoning, gated-scan exit code
4. **Build / run / push evidence** — the captured outputs from Tasks 2 and 5, including the public registry URL
5. **Challenges & Solutions** — at least one real one (the `slim has no curl` healthcheck trap, or the Trivy DB mirror, are both fair game — pick what you actually hit)

### 5.4 — Proof of work

**Paste into `docs/LAB02.md`:**

- `docker push` output showing the digest
- `docker pull` output from the clean state (proves the image is public and pullable)
- The registry URL (e.g. `https://github.com/<you>/devops-info-service/pkgs/container/devops-info-service`)
- The Docker section of your updated `README.md` (or a link to it in the PR)

---

## Bonus Task — Distroless Multi-Stage (Go) (2 pts)

Re-containerize your Lab 1 bonus app (Go recommended) as a multi-stage build with a **distroless or `scratch`** final stage. This is where the lecture's "60× smaller, zero CVEs" payoff actually shows up.

`YOUR TASK`: fill the skeleton. Less hand-holding than the main tasks — by now you've written two Dockerfiles.

```dockerfile
# syntax=docker/dockerfile:1
# ---------- build stage: full Go toolchain ----------
FROM ___ AS build             # YOUR TASK: pin a Go base (e.g. golang:1.25). Not :latest
WORKDIR ___                   # YOUR TASK: pick a build dir
COPY go.mod go.sum* ./
RUN go mod download
COPY . .
RUN ___                       # YOUR TASK: build a FULLY STATIC binary. Which env var disables cgo? (slide 17)
                              # WHY this matters: cgo links against the build image's libc dynamically.
                              # A static binary (no libc dep) is what makes `FROM scratch` / distroless/static
                              # viable — those images literally don't ship libc.

# ---------- final stage: ~nothing but the binary ----------
FROM ___                      # YOUR TASK: gcr.io/distroless/static-debian12 OR scratch — choose + defend in docs
COPY --from=build ___ ___     # YOUR TASK: copy the static binary out of the build stage
USER ___                      # YOUR TASK: distroless ships `nonroot:nonroot`; or pick a numeric UID
EXPOSE ___                    # YOUR TASK: same port as Lab 1
ENTRYPOINT [___]              # YOUR TASK: exec form — single static binary, no shell needed
```

### Bonus requirements

- Multi-stage Dockerfile in `app_go/` with a distroless or `scratch` final stage
- Statically-linked binary — explain in `app_go/docs/LAB02.md` *why* static linking is what makes distroless/scratch viable (no libc at runtime)
- Working containerized app — both `/` and `/health` respond
- Trivy scan of the distroless image — compare its finding count to the Python multi-stage image and explain *why* it's so much lower (no shell, no package manager, near-zero attack surface)
- Size + CVE comparison documented (the lecture predicts ~15 MB / ~0 CVEs — capture your real numbers)

**Expected payoff** *(illustrative — your numbers will differ)*: Python slim ≈ **130 MB / ~100 CVEs** → Go distroless ≈ **8 MB / 0 CVEs**.

<details>
<summary>💡 Distroless vs scratch — when each fits</summary>

- **`gcr.io/distroless/static-debian12`** — empty userspace except CA certs + `/etc/passwd` (a `nonroot` user) + `tzdata`. Recommended default for Go.
- **`scratch`** — empty. ~0 CVEs because there's nothing in the image. Works only for fully static binaries. You'd add CA certs manually if your binary calls HTTPS.
- **Trade-off** — no shell means no `docker exec ... sh` for debugging in production. That's a *feature* under attack and an *annoyance* during dev. Keep a `*-debug` distroless variant around if you need it locally.

Reference: [distroless](https://github.com/GoogleContainerTools/distroless) · [Multi-stage builds](https://docs.docker.com/build/building/multi-stage/)

</details>

---

## How to Submit

```bash
git switch -c lab02
git add app_python/Dockerfile app_python/.dockerignore app_python/README.md app_python/docs/LAB02.md
git add app_go/                   # only if you did the bonus
git commit -m "feat(lab02): containerize devops info service (multi-stage + trivy + push)"
git push -u origin lab02
```

Open **two** PRs:

- `your-fork:lab02` → `course-repo:master` *(reviewed)*
- `your-fork:lab02` → `your-fork:master` *(merges into your own main when done)*

PR checklist:

```text
- [ ] Task 1 — Dockerfile + .dockerignore written by hand
- [ ] Task 2 — build / run / non-root verified with real curl + id -u captures
- [ ] Task 3 — multi-stage Dockerfile with size comparison
- [ ] Task 4 — Trivy full + gated scan; one finding explained
- [ ] Task 5 — image pushed to GHCR/Docker Hub with SemVer or SHA tag (not :latest only)
- [ ] Bonus  — Go distroless image, ~order-of-magnitude smaller, ~0 CVEs (if attempted)
```

---

## Acceptance Criteria

### Task 1 — Dockerfile (3 pts)
- ✅ `app_python/Dockerfile` written from the skeleton (every `___` resolved)
- ✅ Pinned slim base (not `latest`, not the full image)
- ✅ `WORKDIR` set explicitly
- ✅ **Numeric** non-root `USER` (uid ≥ 10000)
- ✅ Dependencies installed before app code (cache-friendly order); `--no-cache-dir`
- ✅ `CMD` in exec form (JSON array)
- ✅ `app_python/.dockerignore` present with VCS / venv / cache / IDE exclusions

### Task 2 — Build & Run (2 pts)
- ✅ Image builds clean
- ✅ `GET /` and `GET /health` return the same JSON as Lab 1
- ✅ `docker run ... id -u` prints a non-zero UID
- ✅ `docker images` size + "biggest layer" one-liner in docs

### Task 3 — Multi-stage (2 pts)
- ✅ Two stages with `COPY --from=builder`
- ✅ No build toolchain / pip cache in the final image
- ✅ Real size numbers in docs — including the **honest** explanation if multi-stage didn't shrink it for your pure-Python app

### Task 4 — Trivy (2 pts)
- ✅ Full scan + gated `--severity HIGH,CRITICAL --exit-code 1` both run
- ✅ Severity counts with real numbers
- ✅ One finding explained with remediation reasoning
- ✅ No findings hidden via `.trivyignore`

### Task 5 — Registry & Docs (1 pt)
- ✅ Image pushed and **publicly pullable** (`docker rmi && docker pull` from clean works)
- ✅ Real version tag (SemVer or SHA), not only `:latest`
- ✅ `README.md` Docker section
- ✅ `docs/LAB02.md` complete (all 5 sections, real evidence, registry URL)

### Bonus (2 pts)
- ✅ Multi-stage Go Dockerfile, distroless or `scratch` final stage
- ✅ Statically-linked binary; both endpoints work
- ✅ Trivy scan of distroless image with finding-count comparison
- ✅ `app_go/docs/LAB02.md` with size metrics, static-linking explanation, security analysis

---

## Rubric

| Task | Points | Criteria |
|------|-------:|----------|
| **Task 1** — Dockerfile  | **3** | Pinned slim base, numeric non-root, cache-friendly layers, exec-form `CMD`, `.dockerignore` |
| **Task 2** — Build & Run | **2** | Builds clean; both endpoints match Lab 1; non-root verified |
| **Task 3** — Multi-stage | **2** | Two stages, no toolchain in final image, documented size reality (even if it's "no change, here's why") |
| **Task 4** — Trivy       | **2** | Full + gated scan, real counts, one explained finding, nothing hidden |
| **Task 5** — Registry    | **1** | Publicly pullable, real version tag, complete `LAB02.md` + README Docker section |
| **Bonus** — Distroless Go | **2** | Distroless/scratch multi-stage with size + CVE comparison |
| **Total** | **12** | 10 main + 2 bonus |

**Grading guidance:**
- **10/10** — Small, secure, reproducible image; multi-stage discipline; scan understood; clean push; reasoning in docs goes beyond "the lecture said to."
- **8–9/10** — Working multi-stage image as non-root, scanned and pushed, defends most choices.
- **6–7/10** — Container works and runs as non-root, but single-stage only or shallow scan/analysis.
- **<6/10** — Runs as root, no `.dockerignore`, no scan, or copy-paste Dockerfile the student can't explain.

---

## Resources

<details>
<summary>📚 Docker Documentation</summary>

- [Dockerfile Best Practices](https://docs.docker.com/build/building/best-practices/)
- [Dockerfile Reference](https://docs.docker.com/reference/dockerfile/)
- [Multi-Stage Builds](https://docs.docker.com/build/building/multi-stage/)
- [`.dockerignore`](https://docs.docker.com/reference/dockerfile/#dockerignore-file)
- [Docker Engine 29 release notes](https://docs.docker.com/engine/release-notes/)
- [containerd image store](https://docs.docker.com/engine/storage/containerd/)

</details>

<details>
<summary>🔒 Security & Scanning</summary>

- [Trivy docs](https://trivy.dev/) · [Trivy `image` scanning](https://trivy.dev/latest/docs/target/container_image/)
- [Distroless](https://github.com/GoogleContainerTools/distroless)
- [Why non-root containers](https://docs.docker.com/build/building/best-practices/#user)
- [CIS Docker Benchmark](https://www.cisecurity.org/benchmark/docker)
- *Container Security* — Liz Rice (O'Reilly, 2020)

</details>

<details>
<summary>🛠️ Dev tools worth knowing</summary>

- [Hadolint](https://github.com/hadolint/hadolint) — Dockerfile linter
- [Dive](https://github.com/wagoodman/dive) — explore image layers interactively
- [GHCR](https://docs.github.com/packages/working-with-a-github-packages-registry/working-with-the-container-registry) · [Docker Hub](https://hub.docker.com/)

</details>

<details>
<summary>⚠️ Common Pitfalls (from real dry-runs)</summary>

- **`COPY . .` before `pip install`** — kills the layer cache. A one-character code change re-installs every dependency. The single most common mistake in this lab — fix it by copying `requirements.txt` first and `pip install`-ing before the rest of the source. (Lecture slide 14.)
- **`USER appuser` (non-numeric) under `runAsNonRoot: true`** — works in Docker, fails the Lab 9 K8s admission policy because it can't verify the UID without parsing `/etc/passwd`. Always use a **numeric** `USER 10001`.
- **Trivy DB `ghcr.io ... DENIED`** — campus / restricted networks rate-limit the anonymous ghcr.io token. Use `--db-repository public.ecr.aws/aquasecurity/trivy-db:2` — Aqua publishes there explicitly for this case.
- **`python:3.13-slim` has no `curl` and no `wget`** — your HEALTHCHECK breaks silently. Either use `python -c 'import urllib.request; urllib.request.urlopen("http://127.0.0.1:8080/health")'` or `apt-get install curl` (and accept the extra CVEs). Don't add the line and assume it works.
- **Trivy `v0.69.4` is malicious** — CVE-2026-33634 supply-chain compromise (March 2026). Pin `v0.69.3` or a later clean patch. In CI: `trivy-action@v0.35.0+`.
- **BuildKit not enabled** — older Docker Engines (<23) ignore `# syntax=docker/dockerfile:1` and skip `COPY --from=builder` features. Docker 29 has BuildKit on by default; if your build fails on `RUN --mount=type=cache` syntax, you're on an ancient Docker.
- **`.dockerignore` missing** — your `COPY . .` ships `.git/`, `.venv/`, IDE configs, and **`.env` with secrets** into the image. Layers are forever — once the secret is in the image, even deleting it in a later layer doesn't remove it.
- **`COPY secrets.env / && rm secrets.env`** — does NOT remove the secret. It's still in the earlier layer, visible via `docker history` and `docker save | tar -xvf`. Treat every layer as immutable.
- **Multi-stage marginally LARGER for pure Python** — Flask has no compiled wheels, so the builder stage has nothing to discard, and the venv copy adds ~3 MB. This is **expected and correct** — document it, don't hide it. The big multi-stage win is compiled languages (Bonus task).
- **Image cache stale after `apt-get update`** — if you `RUN apt-get update && apt-get install foo` in two separate layers, the `update` is cached forever while `install` re-runs against a stale package list. Always combine them in one `RUN`. Same lesson, different package manager: don't split related work across layers.
- **Container hostname is the container ID, not your laptop** — `socket.gethostname()` inside the container returns something like `a3f29c8b1d04`. That's correct behaviour (Lab 1 footnote), not a bug. You're seeing the PID/UTS namespace at work.
- **`docker run` as root by default** — even if your Dockerfile has `USER 10001`, `docker run --user root` overrides it. The Dockerfile sets the *default*; runtime can override. In Lab 9, Kubernetes PSA / Pod Security policies enforce this from the orchestrator side.

</details>

---

## Looking Ahead

The image you build this week follows your service through the rest of the course:

| Lab | What it adds |
|---:|---|
| 3  | CI: pytest + ruff + image build + Trivy gate on every PR |
| 7  | Structured JSON logs via Alloy → Loki |
| 8  | `/metrics` endpoint + Prometheus instrumentation |
| 9  | Deploy to k3d Kubernetes using the `/health` probe |
| 10 | Helm 4 chart packaging this image |
| 13 | ArgoCD GitOps shipping new tags automatically |

---

**Hot take:** a good Dockerfile is small, secure, and reproducible. Two out of three is a bug. Run as non-root, scan every image, never deploy `:latest`. Everything else in this course is a variation on those three rules.
