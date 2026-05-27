# Lab 2 — Docker Containerization

![difficulty](https://img.shields.io/badge/difficulty-beginner-success)
![topic](https://img.shields.io/badge/topic-Containerization-blue)
![points](https://img.shields.io/badge/points-10%2B2-orange)
![tech](https://img.shields.io/badge/tech-Docker%2029-informational)

> Containerize the Python DevOps Info Service from Lab 1 with a production-grade, multi-stage Dockerfile, scan it for vulnerabilities, and publish it to a registry.

## Overview

In Lab 1 you built a service that "works on your machine." This lab makes it **work everywhere**. You will write a Dockerfile by hand (no copy-paste templates), shrink it with a multi-stage build, run it as a non-root user, scan the image with Trivy, and push it to a public registry.

The image you build this week is **the artifact for the rest of the course** — CI builds it (Lab 3), Kubernetes deploys it (Lab 9), Helm packages it (Lab 10), and ArgoCD ships it (Lab 13).

**What You'll Learn:**
- Writing production-ready, layer-cache-friendly Dockerfiles
- Running containers as a non-root user (defense against container escape)
- Multi-stage builds for small, reproducible images
- Image vulnerability scanning with Trivy and CI-style gating
- Tagging and pushing to a container registry (GHCR or Docker Hub)

**Tech Stack:** Docker Engine 29.x (containerd image store) | BuildKit | Compose v2 | `python:3.13-slim` | Trivy v0.69.3+

---

## Prerequisites

| Tool | Version | Check |
|------|---------|-------|
| Docker Engine | **29.x** | `docker version` |
| BuildKit | bundled with Docker 29 (on by default) | `docker buildx version` |
| Trivy | **v0.69.3 or newer** | `trivy --version` |
| Your Lab 1 `app_python/` service | working locally | `python app.py` |

> ⚠️ **Trivy supply-chain warning:** Install **v0.69.3** or a later patch. **Do NOT install v0.69.4** — that release was malicious (CVE-2026-33634, the March 2026 supply-chain attack on Trivy). When the next clean release is out, prefer it; otherwise pin `v0.69.3`. If you use Trivy in GitHub Actions later (Lab 3), use `trivy-action@v0.35.0+` / `setup-trivy@v0.2.6+`.

Docker 29 makes the **containerd image store the default for new installs**. That gives you local multi-platform builds and better disk reclamation for free — you don't have to configure anything, but it's why `docker buildx` works without registry round-trips.

---

## Tasks

### Task 1 — Write a Production Dockerfile (3 pts)

**Objective:** Write `app_python/Dockerfile` from scratch following the best practices from Lecture 2. You write the Dockerfile — that is the skill being assessed.

Start from this skeleton and replace every `# YOUR-TASK` marker. **Do not just paste a Dockerfile from the internet** — graders check that your layer order, user, and base image are deliberate choices you can explain.

```dockerfile
# syntax=docker/dockerfile:1

# YOUR-TASK: pick a PINNED slim base image (e.g. python:3.13-slim).
#   Never use :latest or an unversioned tag.
FROM python:3.13-slim

# YOUR-TASK: set an explicit working directory (e.g. /app), never / or ~.
WORKDIR ___

# YOUR-TASK: create a non-root user with a NUMERIC uid (e.g. 10001).
#   A numeric UID survives username renames and works with read-only rootfs.
RUN ___

# YOUR-TASK: copy ONLY requirements.txt first (it changes rarely → stays cached),
#   then install deps with --no-cache-dir so pip's cache isn't baked into a layer.
COPY ___ ___
RUN pip install --no-cache-dir -r requirements.txt

# YOUR-TASK: copy the application source LAST (it changes often).
COPY ___ ___

# YOUR-TASK: switch to the non-root user (use the numeric UID).
USER ___

# YOUR-TASK: document the port your app listens on.
EXPOSE ___

# YOUR-TASK (optional but recommended): add a HEALTHCHECK that curls /health.

# YOUR-TASK: start the app in EXEC form so it becomes PID 1 and receives SIGTERM.
#   Shell form (CMD python app.py) makes /bin/sh PID 1 — signals never reach your app.
CMD ["___", "___"]
```

**Must-have requirements (each is a rubric line):**
- Pinned, slim base image (not `latest`, not the full ~1.2 GB image)
- `WORKDIR` set explicitly
- Non-root user via a **numeric** `USER` directive
- Dependencies copied/installed **before** application code (layer-cache order)
- `--no-cache-dir` on `pip install` (no pip cache baked into the layer)
- `CMD`/`ENTRYPOINT` in **exec form** (JSON array)
- A `.dockerignore` (see below)

**Create `app_python/.dockerignore`** so `COPY . .` does not ship `.git`, virtualenvs, caches, or secrets into the image. Same syntax as `.gitignore`:

```gitignore
.git
.venv
venv/
__pycache__/
*.pyc
.env
docs/
tests/
.idea/
.vscode/
```

<details>
<summary>💡 Why each rule matters (read before you write)</summary>

- **Pinned slim base** — `python:3.13` is ~1.2 GB; `python:3.13-slim` is ~150 MB. Smaller = faster pulls, fewer packages, fewer CVEs. `:latest` is mutable → you can't reproduce yesterday's build.
- **Numeric non-root UID** — running as root means a kernel container-escape CVE gets root on the host. `USER 10001` drops that privilege and survives image renames.
- **Layer order (deps before code)** — every instruction is a cached layer. If you `COPY . .` before installing deps, a one-character code change re-installs every dependency. Put rarely-changing things first.
- **`--no-cache-dir`** — pip's download cache adds tens of MB to the layer for no runtime benefit. Layers are additive: deleting the cache in a later step does NOT shrink the image.
- **Exec form `CMD`** — shell form forks `/bin/sh` as PID 1; your app becomes PID 2 and never receives `SIGTERM`, so graceful shutdown breaks and the orchestrator has to `SIGKILL` it.
- **`.dockerignore`** — in 2022 Toyota leaked customer data because a `.git` folder rode into a deployed artifact. Keep build context (and secrets) out.

Reference: [Dockerfile best practices](https://docs.docker.com/build/building/best-practices/) · [Dockerfile reference](https://docs.docker.com/reference/dockerfile/)

</details>

---

### Task 2 — Build, Run, and Verify (2 pts)

**Objective:** Build the image and prove the containerized app behaves exactly like it did locally in Lab 1.

```bash
# Build with a meaningful tag (replace USER/REPO as you like)
docker build -t devops-info-service:lab02 ./app_python

# Run it, mapping the container port to the host
docker run --rm -p 8080:8080 --name lab02 devops-info-service:lab02

# In another terminal — verify both endpoints respond
curl http://localhost:8080/
curl http://localhost:8080/health

# Inspect the result
docker images devops-info-service          # check the final size
docker history devops-info-service:lab02   # see your layers
```

**Requirements:**
- Image builds with no errors
- `GET /` and `GET /health` return the same JSON as your Lab 1 service
- Container runs as non-root — verify it:

```bash
# Should print a non-zero UID (e.g. 10001), NOT 0/root
docker run --rm devops-info-service:lab02 id -u
```

> Capture the build output, the running container, and the endpoint responses for your documentation. (Terminal/`docker images` output shown in this lab is **illustrative** — record your own real output.)

---

### Task 3 — Multi-Stage Build (2 pts)

**Objective:** Convert `app_python/Dockerfile` into a **multi-stage** build that keeps build-time tooling out of the final image.

Even for Python this is worth doing: a builder stage installs dependencies (and any compilers needed for wheels) into a virtualenv or a `--user` prefix, and the final stage copies **only** the installed packages plus your code — no `pip`, no build toolchain, no apt caches.

```dockerfile
# syntax=docker/dockerfile:1

# ---------- Stage 1: builder ----------
# YOUR-TASK: install dependencies into an isolated location (e.g. a venv at /opt/venv
#   or `pip install --prefix`). This stage may carry build tools; that's fine.
FROM python:3.13-slim AS builder
WORKDIR /app
COPY requirements.txt .
RUN ___        # YOUR-TASK: create venv / prefix and install deps into it

# ---------- Stage 2: runtime ----------
FROM python:3.13-slim AS runtime
# YOUR-TASK: create the numeric non-root user
RUN ___
WORKDIR /app
# YOUR-TASK: copy ONLY the installed deps from the builder stage
COPY --from=builder ___ ___
# YOUR-TASK: make the copied deps importable (set PATH or PYTHONPATH)
ENV PATH="/opt/venv/bin:$PATH"
COPY . .
USER 10001
EXPOSE 8080
CMD ["python", "app.py"]
```

**Requirements:**
- At least two stages (`AS builder`, `AS runtime`), using `COPY --from=builder`
- Final image contains **no** build toolchain / pip cache
- App still works identically (`curl` both endpoints)
- Document the **size difference** between your Task 1 image and your multi-stage image

```bash
docker build -t devops-info-service:lab02-multi ./app_python
docker images devops-info-service   # compare lab02 vs lab02-multi sizes
```

<details>
<summary>💡 Multi-stage concepts</summary>

- **Why two stages?** The builder may need a compiler to build a wheel; the runtime never does. Copying only the artifact (`COPY --from=builder`) discards everything the runtime doesn't need.
- **Naming stages** — `FROM image AS builder`, then `COPY --from=builder /src /dst`.
- **Where this shines** — compiled languages. A single-stage `golang:1.24` image is ~900 MB; a multi-stage build copying just the static binary into a tiny base is ~15 MB. That's the Bonus task.

Reference: [Multi-stage builds](https://docs.docker.com/build/building/multi-stage/)

</details>

---

### Task 4 — Scan the Image with Trivy (2 pts)

**Objective:** Find and reason about vulnerabilities in your image — the same gate CI will enforce in Lab 3.

```bash
# Full report (informational): every CVE in the image
trivy image devops-info-service:lab02-multi

# CI-style gate: fail (non-zero exit) on HIGH/CRITICAL findings.
# This is exactly what Lecture 2 / Lab 3 wire into the pipeline.
trivy image --severity HIGH,CRITICAL --exit-code 1 devops-info-service:lab02-multi
echo "exit code: $?"
```

> A 2024 Snyk scan found ~80% of public images carry at least one HIGH-severity CVE — so finding some is normal. The goal is to **understand and reduce** them, not pretend they don't exist.

**Requirements:**
- Run a full Trivy scan and a `--severity HIGH,CRITICAL --exit-code 1` gated scan
- Record the counts by severity (illustrative example — capture **your** real numbers):

  | Severity | Count |
  |----------|------:|
  | CRITICAL | _e.g._ 0 |
  | HIGH | _e.g._ 2 |
  | MEDIUM | _e.g._ 9 |
  | LOW | _e.g._ 14 |

- In your docs, explain **at least one** finding: what package, why it's flagged, and how you'd remediate (rebuild on a fresh base, pin a patched dependency, or switch to a smaller base).
- Re-scan after any base-image change and note whether the count dropped.

> Do **not** suppress findings with `.trivyignore` to make the gate pass. If a CVE has no fix yet, document it (package, CVE id, why it's unfixable right now) instead of hiding it.

<details>
<summary>💡 Why scan, and why gate on exit code</summary>

- `trivy image <ref>` reports OS-package and language-dependency CVEs.
- `--exit-code 1` makes Trivy return non-zero when matching findings exist — that's how a pipeline turns "there are CRITICALs" into a **failed build**.
- Smaller base images (slim → distroless → scratch) carry fewer packages, so they usually scan cleaner. This is the link between Task 3 and Task 4.

Reference: [Trivy docs](https://trivy.dev/) · [Trivy `image` command](https://trivy.dev/latest/docs/target/container_image/)

</details>

---

### Task 5 — Push to a Registry & Document (1 pt)

**Objective:** Publish your image and document the workflow. Use **GHCR** (`ghcr.io`, free for public, integrates with the GitHub Actions you'll write in Lab 3) **or** Docker Hub.

```bash
# --- Option A: GitHub Container Registry (recommended) ---
echo "$GHCR_PAT" | docker login ghcr.io -u <github-username> --password-stdin
docker tag devops-info-service:lab02-multi ghcr.io/<github-username>/devops-info-service:1.0.0
docker push ghcr.io/<github-username>/devops-info-service:1.0.0

# --- Option B: Docker Hub ---
docker login
docker tag devops-info-service:lab02-multi <dockerhub-user>/devops-info-service:1.0.0
docker push <dockerhub-user>/devops-info-service:1.0.0
```

**Requirements:**
1. Image pushed and **publicly pullable** (verify from a clean state: `docker rmi` then `docker pull`)
2. Use a real tagging strategy — a **SemVer** (`1.0.0`) or **Git SHA** tag, **not** `:latest` as your only tag
3. Update `app_python/README.md` with a **Docker** section: command patterns (not necessarily exact) for build, run, and pull-from-registry
4. Create `app_python/docs/LAB02.md` documenting your implementation (sections below)

#### `app_python/docs/LAB02.md` required sections

1. **Dockerfile decisions** — base image + version justification, layer order, the non-root user, and why each matters (the *why*, not just the *what*).
2. **Multi-stage results** — size comparison (single-stage vs multi-stage) with your real `docker images` numbers and a one-line takeaway.
3. **Trivy scan** — your severity counts, one finding explained, and your remediation reasoning. State whether the gated scan passed or failed and why.
4. **Build / run / push evidence** — your real terminal output for build, run, endpoint tests (`curl`), and the push. Include the registry URL.
5. **Challenges & solutions** — what broke, how you debugged it, what you learned.

> 🚫 **Never deploy `:latest` to production** — it's mutable, so you can't reproduce a past deploy. Tag by SemVer or SHA; reference the immutable tag in deploys.

---

## Bonus Task — Distroless Multi-Stage (Go) (2 pts)

**Objective:** Containerize your **Lab 1 bonus** compiled-language app (Go recommended) as a multi-stage build with a **distroless or `scratch`** final image, and show the dramatic size/attack-surface reduction.

```dockerfile
# syntax=docker/dockerfile:1

# ---------- build stage: full toolchain ----------
FROM golang:1.24 AS build
WORKDIR /src
COPY go.mod go.sum* ./
RUN go mod download
COPY . .
# YOUR-TASK: build a fully static binary so it needs no libc at runtime.
#   CGO_ENABLED=0 is what lets you use distroless/static or scratch.
RUN CGO_ENABLED=0 go build -o /app ./...

# ---------- final stage: nothing but the binary ----------
# YOUR-TASK: choose gcr.io/distroless/static-debian12 (has a nonroot user, CA certs)
#   or scratch (literally empty — you must add CA certs yourself if you make HTTPS calls).
FROM gcr.io/distroless/static-debian12
COPY --from=build /app /app
USER nonroot:nonroot
EXPOSE 8080
ENTRYPOINT ["/app"]
```

**Requirements:**
- Multi-stage Dockerfile in `app_go/` (or your chosen language) with a distroless or `scratch` final stage
- Statically-linked binary (`CGO_ENABLED=0` for Go) — explain why static linking is what makes distroless/scratch possible
- Working containerized app (both endpoints respond)
- Trivy scan of the distroless image — compare its finding count to the Python image and explain the difference
- `app_go/docs/LAB02.md` documenting: build vs final size with real numbers, the static-linking requirement, the security benefit (no shell, no package manager → smaller attack surface), and the Trivy comparison

**Bonus points for:** a final image under ~20 MB with metrics, and a clear explanation of the `scratch` vs distroless trade-off (debuggability vs minimalism).

<details>
<summary>💡 Distroless & scratch</summary>

- **Distroless** (Google) — your runtime + app, but **no shell, no apt, no busybox**. `gcr.io/distroless/static-debian12` ships a `nonroot` user and CA certs. Drastically smaller attack surface.
- **`scratch`** — the empty image. Only works for fully static binaries (Go with `CGO_ENABLED=0`, Rust with musl). ~0 CVEs because there's nothing else in the image.
- **Trade-off** — no shell means no `docker exec ... sh` to debug. That's a feature in production, an annoyance in dev. Keep a slim debug variant if you need one.

Reference: [distroless](https://github.com/GoogleContainerTools/distroless) · [Multi-stage builds](https://docs.docker.com/build/building/multi-stage/)

</details>

---

## How to Submit

1. **Create Branch:** `git checkout -b lab02`
2. **Commit Work:** add `app_python/` (Dockerfile, `.dockerignore`, updated `README.md`, `docs/LAB02.md`) and, for the bonus, `app_go/`. Use a conventional-commit message and push to your fork.
3. **Create Pull Requests:**
   - **PR #1:** `your-fork:lab02` → `course-repo:master`
   - **PR #2:** `your-fork:lab02` → `your-fork:master`

---

## Acceptance Criteria

### Main Tasks (10 points)

**Dockerfile (3 pts):**
- [ ] `app_python/Dockerfile` written from the skeleton (all `# YOUR-TASK` resolved)
- [ ] Pinned, slim base image (not `latest`, not the full image)
- [ ] `WORKDIR` set; runs as a **numeric** non-root `USER`
- [ ] Dependencies installed before app code (cache-friendly order); `--no-cache-dir` used
- [ ] `CMD`/`ENTRYPOINT` in exec form
- [ ] `app_python/.dockerignore` present and sensible

**Build & Run (2 pts):**
- [ ] Image builds with no errors
- [ ] `GET /` and `GET /health` match the Lab 1 service
- [ ] `docker run ... id -u` confirms a non-zero (non-root) UID

**Multi-stage (2 pts):**
- [ ] Multi-stage Dockerfile (`builder` + `runtime`, `COPY --from`)
- [ ] No build toolchain / pip cache in the final image
- [ ] Size comparison documented with real numbers

**Trivy scan (2 pts):**
- [ ] Full scan + gated `--severity HIGH,CRITICAL --exit-code 1` scan run
- [ ] Severity counts recorded; at least one finding explained with remediation reasoning
- [ ] No findings hidden via `.trivyignore` (unfixable CVEs documented instead)

**Registry & Docs (1 pt):**
- [ ] Image pushed to GHCR or Docker Hub and publicly pullable
- [ ] SemVer or SHA tag used (not only `:latest`)
- [ ] `app_python/README.md` has a Docker section
- [ ] `app_python/docs/LAB02.md` complete (all 5 sections, real evidence, registry URL)

### Bonus Task (2 points)

- [ ] Multi-stage Dockerfile in `app_<language>/` with distroless or `scratch` final stage
- [ ] Statically-linked binary; working containerized app (both endpoints)
- [ ] Trivy scan of distroless image compared to the Python image
- [ ] `app_<language>/docs/LAB02.md` with size metrics, static-linking explanation, and security analysis

---

## Rubric

| Criteria | Points | Description |
|----------|--------|-------------|
| **Dockerfile** | 3 pts | Pinned slim base, numeric non-root user, cache-friendly layers, exec-form CMD, `.dockerignore` |
| **Build & Run** | 2 pts | Builds clean; endpoints match Lab 1; verified non-root at runtime |
| **Multi-stage** | 2 pts | Two-stage build, no toolchain in final image, documented size reduction |
| **Trivy scan** | 2 pts | Full + gated scan, findings understood and explained, nothing hidden |
| **Registry & Docs** | 1 pt | Public image, SemVer/SHA tag, complete `LAB02.md` + README Docker section |
| **Bonus** | 2 pts | Distroless/scratch multi-stage with size + security analysis |
| **Total** | 12 pts | 10 pts required + 2 pts bonus |

**Grading:**
- **10/10:** Small, secure, reproducible image; multi-stage size win; scan understood and explained; clean push; deep reasoning in docs.
- **8–9/10:** Working multi-stage image as non-root, scanned and pushed, good explanations.
- **6–7/10:** Container works and runs as non-root, but single-stage or shallow scan/analysis.
- **<6/10:** Runs as root, no `.dockerignore`, no scan, or copy-paste Dockerfile without understanding.

---

## Resources

<details>
<summary>📚 Docker Documentation</summary>

- [Dockerfile Best Practices](https://docs.docker.com/build/building/best-practices/)
- [Dockerfile Reference](https://docs.docker.com/reference/dockerfile/)
- [Multi-Stage Builds](https://docs.docker.com/build/building/multi-stage/)
- [.dockerignore](https://docs.docker.com/reference/dockerfile/#dockerignore-file)
- [Docker Engine 29 release notes](https://docs.docker.com/engine/release-notes/)
- [containerd image store](https://docs.docker.com/engine/storage/containerd/)

</details>

<details>
<summary>🔒 Security & Scanning</summary>

- [Trivy documentation](https://trivy.dev/)
- [Trivy `image` scanning](https://trivy.dev/latest/docs/target/container_image/)
- [Distroless Images](https://github.com/GoogleContainerTools/distroless)
- [Why Non-Root Containers](https://docs.docker.com/build/building/best-practices/#user)
- [CIS Docker Benchmark](https://www.cisecurity.org/benchmark/docker)
- *Container Security* — Liz Rice (O'Reilly, 2020)

</details>

<details>
<summary>🛠️ Tools</summary>

- [Hadolint](https://github.com/hadolint/hadolint) — Dockerfile linter
- [Dive](https://github.com/wagoodman/dive) — explore image layers
- [GHCR](https://docs.github.com/packages/working-with-a-github-packages-registry/working-with-the-container-registry) — GitHub Container Registry
- [Docker Hub](https://hub.docker.com/) — container registry

</details>

---

## Looking Ahead

The image you built this week follows your service through the rest of the course:

- **Lab 3:** CI builds, scans (Trivy gate), and pushes this image automatically
- **Lab 7–8:** Run it with Compose for logging and monitoring
- **Lab 9:** Deploy it to Kubernetes using the `/health` probe
- **Lab 10:** Package it with Helm
- **Lab 13:** ArgoCD ships it via GitOps

---

**Good luck!** 🚀

> **Remember:** A good Dockerfile is small, secure, and reproducible. Two out of three is a bug. Run as non-root, scan every image, never deploy `:latest`.
