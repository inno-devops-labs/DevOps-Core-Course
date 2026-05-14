# Lab 18 — Submission: Reproducible builds with Nix

**Merge request:** branch **`lab18`** into the course repository default branch.  
**Author:** Rokkel Maria CBS-01  
**Environment:** macOS (Darwin); **Determinate Nix** on host — `nix (Determinate Nix 3.20.0) 2.34.6`; Linux build uses **`nixos/nix:latest`** → `nix (Nix) 2.34.7`.

---

## 1. Task 1 — Reproducible Python app (Lab 1 revisited)

### 1.1 Nix installation and sanity check

```text
$ nix --version
nix (Determinate Nix 3.20.0) 2.34.6

$ nix run nixpkgs#hello
Hello, world!
```

### 1.2 Lab layout

- Application sources: **`labs/lab18/app_python/`** (`app.py`, `requirements.txt`, same service as Lab 1).
- Nix derivation: **`labs/lab18/app_python/default.nix`**.

### 1.3 Derivation overview

The derivation uses **`python3.withPackages`** with **`flask`** and **`prometheus-client`** from the pinned **nixpkgs** closure (not `pip` at build time). The wrapper binary **`devops-info-service`** runs `app.py` with **`VISITS_FILE`** defaulting to **`/tmp/devops-info-visits`** so the service runs without a bind-mounted **`/data`**. Full expression: **`labs/lab18/app_python/default.nix`** in the repository.

### 1.4 Store path and rebuild evidence

From **`labs/lab18/app_python/`**, the application package was built with **`nix build .#default`** (flake). The store path below is the **`devops-info-service-1.0.0`** derivation output.

| Step | Command | `readlink -f result` / notes |
|------|---------|------------------------------|
| First build | `nix build .#default` | `/nix/store/va7wv7crvlxyhx62wwbzc51h0a86pr8x-devops-info-service-1.0.0` |
| Rebuild after removing symlink | `rm -f result && nix build .#default` | Same path (binary cache hit; no inputs changed) |

`nix-hash` on the output was not recorded on the host when the **`result`** symlink pointed only at container-local **`/nix/store`** paths; the store-path table above is the primary reproducibility evidence for Task 1.

### 1.5 pip vs Nix (limitations of `requirements.txt`)

Compared to **`pip install -r requirements.txt`** in a venv:

- **`requirements.txt`** pins direct deps; transitive deps still float unless fully locked (e.g. `pip-tools`, strict hashes).
- **Nix / nixpkgs** fixes the entire dependency graph for a given revision.

| Aspect | Lab 1 (`pip` + `venv`) | Lab 18 (Nix derivation) |
|--------|------------------------|-------------------------|
| Python runtime | Whatever the machine / image uses | From nixpkgs |
| Dependency graph | Resolved at `pip install` time | Fixed at nixpkgs revision |
| Binary cache | No standard shared cache | `cache.nixos.org` for identical store paths |
| Store path / hashing | N/A | Content-addressed `/nix/store/<hash>-…` |

### 1.6 Nix store path format

Example output path: **`/nix/store/va7wv7crvlxyhx62wwbzc51h0a86pr8x-devops-info-service-1.0.0`**. The **`va7wv7crv…`** prefix is the **content hash** of all fixed inputs (source nar, dependency drvs, builder script, flags). The suffix **`devops-info-service-1.0.0`** is **`pname-version`**. Same inputs ⇒ same hash ⇒ same path (binary cache safe).

### 1.7 Screenshots (Task 1)

Nix-built service with **`PORT=5001`** (port 5000 busy on macOS); **`GET /health`**.

![Nix-built service: `PORT=5001` and `GET /health`](lab18/screenshots/nix-run-health.png)

---

## 2. Task 2 — Reproducible Docker image (`dockerTools`)

### 2.1 Lab 2 Dockerfile reference

Images for comparison were built from the repository root using **`app_python/Dockerfile`**. A parallel copy exists under **`labs/lab18/app_python/Dockerfile`** for documentation only; all **`docker build`** commands below use **`./app_python`**.

Two successive **`docker build`** runs produce different image IDs and different **`docker save`** digests (section 2.3) even when layers are cached, because BuildKit adds **per-build attestation** metadata. **`docker inspect … --format '{{.Created}}'`** is another non-reproducibility signal when builds are not identical; with a fully cached graph, **`Created`** can look close in time, but the saved tar still differs.

### 2.2 Nix-built image

Expression: **`labs/lab18/app_python/docker.nix`**.

- **`buildLayeredImage`**: layered store paths for smaller diffs.
- **`created = "1970-01-01T00:00:01Z"`**: avoids time-based tarball drift.
- **`contents`**: the Task 1 derivation only (minimal closure).

On this macOS host, **`nix build .#docker`** fails inside **`dockerTools`** (**`fakeroot`** / **`dyld`**, `_fstat$INODE64`). The image was therefore built with **`./nix-docker-linux.sh`**: Nix runs in a **Linux** container with the repo bind-mounted at **`/repo`**, using a **`path:`** flake reference so evaluation does not depend on **`git`** inside the container. The script copies **`devops-info-service-nix.tar.gz`** into **`labs/lab18/app_python/`** because the **`result`** symlink often targets a **`/nix/store`** path that exists only inside that container, not on the macOS host.

Commands used after a successful build:

```bash
cd labs/lab18/app_python
sha256sum devops-info-service-nix.tar.gz
docker load -i devops-info-service-nix.tar.gz
docker run --rm -d -p 5001:5000 --name nix-lab18 devops-info-service-nix:1.0.0
curl -sS http://127.0.0.1:5001/health
docker stop nix-lab18
```

Two tarball checksums were taken around a **`rm devops-info-service-nix.tar.gz`** and a full **`./nix-docker-linux.sh`** rebuild:

| Build | `sha256sum devops-info-service-nix.tar.gz` |
|-------|--------------------------------------------|
| Before `rm` + rebuild | `ab101797fbc04600800b03208f934837d607b22938ed514352acfaf86879acc9` |
| After `./nix-docker-linux.sh` again | `e8932c8d6d58f4ca067e35f6ded3fc3c920532e105ff237071b1f372bebd1707` |

The digests differ because the **path flake** source is the entire **`labs/lab18/app_python/`** directory; removing the previous tarball (and any other change under that path) changes the **narHash** of the flake input, so the **`devops-info-service-1.0.0`** intermediate store path changes as well. With a **bit-identical** source tree between runs, two consecutive **`./nix-docker-linux.sh`** invocations produce the **same** tarball hash (same inputs → same Nix store output).

On **Linux** or **WSL**, **`nix build .#docker`** followed by **`docker load < result`** is the direct workflow when **`dockerTools`** runs natively.

### 2.3 Lab 2 image non-reproducibility (tar hash)

```bash
docker build -t lab2-app:test1 ./app_python
docker save lab2-app:test1 | shasum -a 256
docker build -t lab2-app:test2 ./app_python
docker save lab2-app:test2 | shasum -a 256
```

| Image | `docker save \| shasum -a 256` |
|-------|--------------------------------|
| `lab2-app:test1` | `460599dc3f49a57656d45a83aa5db33a4f5295ecc5f5454a1ad42429423dba20` |
| `lab2-app:test2` | `4b60642f8dfd9be6242fb40493849e84789d6331847d84b3fde1e3009b19055e` |

BuildKit exported a **different attestation manifest** per build (`exporting attestation manifest sha256:…`), so the saved tar digest changes even when application layers are cached.

### 2.4 Image size and `docker history`

```bash
docker images | grep -E 'lab2-app|devops-info-service-nix'
docker history lab2-app:test1
docker history devops-info-service-nix:1.0.0
```

| Metric | Lab 2 Dockerfile | Lab 18 Nix `dockerTools` |
|--------|------------------|--------------------------|
| Reported image size (`docker images`) | **~241 MB** (`lab2-app:test1`) | **~433 MB** (`devops-info-service-nix:1.0.0` — includes full closure as reported by Docker Desktop) |
| Reproducible tarball / digest | No — `docker save` differs run-to-run (attestation / metadata) | Yes **when flake inputs + local path are unchanged** — fixed `created` in `docker.nix` |
| Base image | `python:3.13-slim` + `apt` | None (store paths only) |

**`docker history`:** Lab 2 shows **BuildKit** steps with **relative `CREATED` times** (e.g. “5 minutes ago”) and a Debian base layer. Nix image shows **content-addressed store path layers** with **`CREATED` N/A** and fixed epoch-style metadata in the image config (`56 years ago` is Docker’s display of the **1970-01-01** reproducibility timestamp).

### 2.5 Side-by-side runtime

Port **5000** on macOS was busy (system service); Lab 2 was mapped to **5002**, Nix image to **5001**.

| Endpoint | Lab 2 container | Nix container |
|----------|-----------------|---------------|
| `GET /health` | `http://127.0.0.1:5002/health` | `http://127.0.0.1:5001/health` |

```json
{"status":"healthy","timestamp":"2026-05-14T21:21:59.446048+00:00","uptime_seconds":13}
```

```json
{"status":"healthy","timestamp":"2026-05-14T21:22:07.151182+00:00","uptime_seconds":14}
```

### 2.6 Screenshots (Task 2)

Lab 2 container (**host port 5002**) and Nix image (**5001**); both **`GET /health`**.

![Lab 2 on port 5002 and Nix image on port 5001: `GET /health`](lab18/screenshots/docker-both-health.png)

### 2.7 Analysis

**Why traditional Dockerfiles are not bit-for-bit reproducible:** image config timestamps, layer metadata, registry tag drift (`python:3.13-slim` moves), non-deterministic package mirrors (`apt`, unpinned `pip`), and build-time `ARG`/`LABEL` usage.

**Redoing Lab 2 with Nix:** pin **`nixpkgs`** in **`flake.lock`**, build a **`dockerTools`** tarball with a fixed **`created`** timestamp, and treat Docker as transport for that artifact instead of using **`Dockerfile`** + **`pip`** as the resolver.

**Where reproducibility matters:** CI image digest signing, incident rollback to a byte-identical artifact, supply-chain audits, and avoiding environment drift between developer laptops and automation.

---

## 3. Flakes vs Helm pinning (Lab 10 bonus tie-in)

| Idea | Helm / Kubernetes (Lab 10) | Nix Flakes |
|------|------------------------------|------------|
| What is pinned | Chart version + `values.yaml` image tags | `flake.lock` inputs (`nixpkgs`, etc.) |
| Drift source | Upstream chart semver, mutable `:latest` tags | Input URL + locked revision only |
| Rollback | Helm release revision / pinned values | Git revert lock + rebuild |

The course Helm chart **`k8s/devops-info-service/`** pins application images and tunables in **`values.yaml`** and chart version; that is version control at the **Kubernetes delivery** layer. **`flake.lock`** pins the **nixpkgs** (and other) input revisions at the **build** layer. Both reduce drift; Nix additionally fixes the entire compiled dependency graph for the Worker code before an image exists.

---

## 4. Flake lock

The submission repository includes **`labs/lab18/app_python/flake.lock`**. Locked **`nixpkgs`** revision: **`50ab793786d9de88ee30ec4e4c24fb4236fc2674`** (input **`github:NixOS/nixpkgs/nixos-24.11`**).

---

## 5. Reflection

- **How would Nix have helped in Lab 1 from day one?** One pinned **nixpkgs** revision would have fixed Python, Flask, and all transitive libraries at build time, with the same store paths across laptops and CI—no “works with my venv” drift.
- **Biggest surprise building the Nix Docker image vs Lab 2?** Native **`dockerTools`** failed on macOS (**fakeroot** / **dyld**); building inside Linux via **`nix-docker-linux.sh`** worked. Also, **`docker images`** size for the Nix image was **larger** than the slim Dockerfile image here, while the **lab narrative** often stresses smaller images—closure size vs slim multi-stage images depends on what you ship.
