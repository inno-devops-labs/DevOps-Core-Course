# Lab 18 — Submission: Reproducible builds with Nix

**Branch:** `feature/lab18` → merge request into the course repository.  
**Author:** *(your name / student id)*  
**Environment:** *(OS, Nix installer: Determinate vs official, `nix --version` output)*

---

## 1. Task 1 — Reproducible Python app (Lab 1 revisited)

### 1.1 Nix installation and sanity check

Paste output of:

```bash
nix --version
nix run nixpkgs#hello
```

*(Restart the shell after install if `nix` is not on `PATH`.)*

### 1.2 Lab layout

- Application sources: **`labs/lab18/app_python/`** (`app.py`, `requirements.txt`, same service as Lab 1).
- Nix derivation: **`labs/lab18/app_python/default.nix`**.

### 1.3 Derivation overview

The derivation uses **`python3.withPackages`** with **`flask`** and **`prometheus-client`** from the pinned **nixpkgs** closure (not `pip` at build time). The wrapper binary **`devops-info-service`** runs `app.py` with **`VISITS_FILE`** defaulting to **`/tmp/devops-info-visits`** so the service works without a bind-mounted `/data`.

*(Optional: paste shortened `default.nix` here or refer only to the repo path above.)*

### 1.4 Store path and rebuild evidence

From **`labs/lab18/app_python/`**:

```bash
nix-build
readlink -f result
```

| Step | Command | `readlink -f result` / notes |
|------|---------|------------------------------|
| First build | `nix-build` | *(paste)* |
| Remove symlink, build again | `rm -f result && nix-build` | *(same path → cache hit)* |
| Force rebuild | `STORE=$(readlink -f result); nix-store --delete "$STORE"` then `rm -f result && nix-build` | *(same path after real rebuild)* |

**`nix-hash` on output (optional):**

```bash
nix-hash --type sha256 "$(readlink -f result)"
```

*(paste hash)*

### 1.5 pip vs Nix (limitations of `requirements.txt`)

Summarise what you observed if you ran the lab’s unpinned / dual-venv experiment, or explain conceptually:

- **`requirements.txt`** pins direct deps; transitive deps still float unless fully locked (e.g. `pip-tools`, strict hashes).
- **Nix / nixpkgs** fixes the entire dependency graph for a given revision.

| Aspect | Lab 1 (`pip` + `venv`) | Lab 18 (Nix derivation) |
|--------|------------------------|-------------------------|
| Python runtime | Whatever the machine / image uses | From nixpkgs |
| Dependency graph | Resolved at `pip install` time | Fixed at nixpkgs revision |
| Binary cache | No standard shared cache | `cache.nixos.org` for identical store paths |
| Store path / hashing | N/A | Content-addressed `/nix/store/<hash>-…` |

### 1.6 Nix store path format

Explain your real store path once: **`<hash>-<name>-<version>`** — what the hash covers (sources + build inputs + instructions).

### 1.7 Screenshots (Task 1)

| # | Description | File |
|---|-------------|------|
| 1 | Service running from **`./result/bin/devops-info-service`** (browser or `curl /health`) | `labs/lab18/screenshots/nix-run-health.png` |

---

## 2. Task 2 — Reproducible Docker image (`dockerTools`)

### 2.1 Lab 2 Dockerfile reference

The canonical Lab 2 image for comparison is built from repo root:

**`app_python/Dockerfile`** (root app) — or **`labs/lab18/app_python/Dockerfile`** (copy under lab18).

```bash
# from repository root
docker build -t lab2-app:v1 ./app_python
docker inspect lab2-app:v1 --format '{{.Created}}'
sleep 5
docker build -t lab2-app:v2 ./app_python
docker inspect lab2-app:v2 --format '{{.Created}}'
```

*(paste: two different `Created` timestamps)*

### 2.2 Nix-built image

Expression: **`labs/lab18/app_python/docker.nix`**.

- **`buildLayeredImage`**: layered store paths for smaller diffs.
- **`created = "1970-01-01T00:00:01Z"`**: avoids time-based tarball drift.
- **`contents`**: the Task 1 derivation only (minimal closure).

```bash
cd labs/lab18/app_python
nix-build docker.nix
sha256sum result
docker load < result
docker run -d -p 5001:5000 --name nix-lab18 devops-info-service-nix:1.0.0
curl -sS http://127.0.0.1:5001/health
```

Repeat **`nix-build docker.nix`** + **`sha256sum result`** twice:

| Build | `sha256sum result` |
|-------|---------------------|
| 1 | *(paste)* |
| 2 | *(paste — should match build 1)* |

### 2.3 Lab 2 image non-reproducibility (tar hash)

```bash
docker build -t lab2-app:test1 ./app_python
docker save lab2-app:test1 | sha256sum
docker build -t lab2-app:test2 ./app_python
docker save lab2-app:test2 | sha256sum
```

| Image | `docker save \| sha256sum` |
|-------|----------------------------|
| test1 | *(paste)* |
| test2 | *(paste — expect different)* |

### 2.4 Image size and `docker history`

```bash
docker images | grep -E 'lab2-app|devops-info-service-nix'
docker history lab2-app:v1
docker history devops-info-service-nix:1.0.0
```

| Metric | Lab 2 Dockerfile | Lab 18 Nix `dockerTools` |
|--------|------------------|--------------------------|
| Reported image size | *(paste)* | *(paste)* |
| Reproducible tarball / digest | No (time + metadata) | Yes (same `docker.nix` + inputs) |
| Base image | `python:3.13-slim` + `apt` | None (closure only) |

*(Attach or paste trimmed `docker history` highlights: note CREATED BY / timestamps on Lab 2 vs Nix.)*

### 2.5 Side-by-side runtime

| Endpoint | Lab 2 container | Nix container |
|----------|-----------------|---------------|
| `GET /health` | `http://localhost:5000/health` | `http://localhost:5001/health` |

*(paste two `curl` JSON bodies)*

### 2.6 Screenshots (Task 2)

| # | Description | File |
|---|-------------|------|
| 2 | Lab 2 and Nix containers both up; two terminals or split `curl` | `labs/lab18/screenshots/docker-both-health.png` |

### 2.7 Analysis

**Why traditional Dockerfiles are not bit-for-bit reproducible:** image config timestamps, layer metadata, registry tag drift (`python:3.13-slim` moves), non-deterministic package mirrors (`apt`, unpinned `pip`), and build-time `ARG`/`LABEL` usage.

**If Lab 2 were redone with Nix:** you would pin the world in one flake lock / nixpkgs revision, produce a fixed tarball with `dockerTools`, and only use Docker as a transport/runtime, not as the resolver.

**Where reproducibility matters:** CI image digest signing, incident rollback to an exact bit-identical artifact, supply-chain audits, avoiding “works on my laptop” drift between dev and CI.

---

## 3. Flakes vs Helm pinning (Lab 10 bonus tie-in)

| Idea | Helm / Kubernetes (Lab 10) | Nix Flakes |
|------|------------------------------|------------|
| What is pinned | Chart version + `values.yaml` image tags | `flake.lock` inputs (`nixpkgs`, etc.) |
| Drift source | Upstream chart semver, mutable `:latest` tags | Input URL + locked revision only |
| Rollback | Helm release revision / pinned values | Git revert lock + rebuild |

*(Add one sentence linking to your real Lab 10 chart if applicable.)*

---

## 4. Flake lock (optional but recommended)

From **`labs/lab18/app_python/`**:

```bash
nix flake lock
git add flake.lock
```

State **`nixpkgs`** revision from `flake.lock` in one line here: *(paste)*

---

## 5. Reflection

- **How would Nix have helped in Lab 1 from day one?** *(2–4 sentences)*
- **Biggest surprise building the Nix Docker image vs Lab 2?** *(1–3 sentences)*
