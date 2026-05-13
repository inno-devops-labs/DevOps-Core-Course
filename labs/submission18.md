# Lab 18 — Submission (Reproducible builds with Nix)

All Nix sources for this lab live under `labs/lab18/app_python/` (copy of the Lab 1 Python service plus Nix expressions).

**Windows note:** Nix builds run on Linux (WSL is fine). If editors save `.nix` files with CRLF line endings, the Linux builder can fail with `$'\r': command not found`. This directory includes `.gitattributes` so `*.nix` and `flake.lock` stay LF in Git.

---

## Task 1 — Reproducible Python app (Nix)

### 1.1 Nix installation and verification

Complete the Determinate Nix (or official) installer on a machine where you have admin rights, restart the shell, then record:

```bash
nix --version
nix run nixpkgs#hello
```

**Recorded on this project (WSL2, Determinate Nix):**

```text
nix (Determinate Nix 3.20.0) 2.34.6
Hello, world!
```

### 1.2 Application layout

Copied into `labs/lab18/app_python/`:

- `app.py` — DevOps Info Service (Flask)
- `requirements.txt` — direct Python dependencies
- `Dockerfile` — Lab 2 reference for Task 2 comparison

Traditional Lab 1 flow (non-reproducible in the strong sense): venv + `pip install -r requirements.txt` depends on interpreter version, index state, and unpinned transitive packages unless you add a full lockfile with hashes.

### 1.3 `default.nix` — what each part does

| Piece | Role |
|--------|------|
| `{ pkgs ? import <nixpkgs> { } }` | Impure entry (channel flake of `<nixpkgs>`). The **flake** pins `nixpkgs` exactly via `flake.lock`. |
| `python3.withPackages [...]` | Closed Python environment: Flask, `prometheus-client`, and `python-json-logger` come from the **same** nixpkgs snapshot as the interpreter. |
| `stdenvNoCC.mkDerivation` | No compiler needed; we only wrap a script. |
| `builtins.path` + `filter` | Source input is content-addressed from `app.py` and `requirements.txt` only (ignores unrelated files in the folder). |
| `makeWrapper` | Produces `$out/bin/devops-info-service` that runs `python3` against the installed `app.py` with `PYTHONPATH` set by the wrapped interpreter. |

Build and run (impure `<nixpkgs>` — **not** the same input as the flake unless your channel matches `flake.lock`):

```bash
cd labs/lab18/app_python
nix-build
readlink result
./result/bin/devops-info-service
```

Flake build (locked nixpkgs — **use this** for bit-for-bit agreement with `flake.lock` and classmates):

```bash
cd labs/lab18/app_python
nix build
readlink result
./result/bin/devops-info-service
```

**Store paths from this repo (examples):**

| Command | Example output |
|--------|----------------|
| `nix build` then `readlink result` | `/nix/store/lp5zibzlqvvrnazi32i09z3xfmb49j2z-devops-info-service-1.0.0` |
| `nix-build default.nix` then `readlink result` | `/nix/store/hm4znzmdn0vnnbkvi1mpxlny63vb3i14-devops-info-service-1.0.0` |

The paths differ because **impure `nix-build` resolves `<nixpkgs>` from your channel** (here: Determinate’s nixpkgs), while **`nix build` uses the revision pinned in `flake.lock`**. For the lab’s “same hash everywhere” story, standardize on **`nix build`** (and the same git commit).

**Output hash (flake-built app, for `nix-hash --type sha256` on that path):** `8727e37475388238e9c38fcae507f55e5f9e09dddbdbb152b9ec1d1674f3f582`

Open `http://localhost:8080/` by default (`app.py` uses `PORT` env, default **8080**). For the worksheet’s port **5000**: `PORT=5000 ./result/bin/devops-info-service`. Health check: `curl http://localhost:8080/health` (or `:5000` if you set `PORT`).

### 1.4 Reproducibility vs pip

**Nix store path** (example shape only — yours follows the same pattern):

`/nix/store/<input-hash>-devops-info-service-1.0.0`

The `<input-hash>` is derived from **all** build inputs (sources, dependency closure, build script, flags). Rebuild with unchanged inputs: same path (cache hit). After `nix-store --delete` on that path, a rebuild yields the **same** path again — bit-for-bit output for the same inputs.

**Why `requirements.txt` is weaker than Nix**

- Unpinned or loosely pinned lines resolve to “whatever the index returns today.”
- Even pinned **top-level** packages still pull **transitive** wheels that can change when maintainers publish new compatible versions unless you use a complete hashed lockfile (e.g. pip-tools + hashes) and the same Python build.
- Nix pins the **entire closure** (interpreter + libraries + build tools) to one nixpkgs revision; flakes add a cryptographic lock on that revision in `flake.lock`.

**Pip demonstration** (from the lab handout): repeat install from an unpinned file into two fresh venvs after clearing cache; `pip freeze` for Flask can differ. Paste `diff freeze1.txt freeze2.txt` here after you run the handout commands: _(fill in when run)_.

### 1.5 Optional Go app

_(If you use `app_go`, add a matching `default.nix` there and document it; this submission focuses on the Python service.)_

---

## Task 2 — Reproducible Docker image (`dockerTools`)

### 2.1 Lab 2 Dockerfile (reference)

See `labs/lab18/app_python/Dockerfile` (based on `python:3.11-slim`, `PORT=8080`). Rebuilding twice yields different image IDs and metadata timestamps even when application code is unchanged.

### 2.2 `docker.nix` — field summary

| Field | Role |
|--------|------|
| `import ./default.nix` | Reuses the same application derivation as the CLI package. |
| `dockerTools.buildLayeredImage` | Builds a minimal layer tarball from the **Nix store closure** of `contents`. |
| `name` / `tag` | Repository name and tag after `docker load`. |
| `contents = [ app ]` | Puts the app and its runtime closure into the image. |
| `config.Env = [ "PORT=5000" ]` | Aligns container listen port with Lab 18 examples (`-p 5001:5000`). |
| `config.Cmd` | Default command: Nix-built `devops-info-service` binary. |
| `config.ExposedPorts` | Documents port 5000. |
| `created` | Fixed timestamp so layer metadata stays deterministic across builds. |

Commands:

```bash
cd labs/lab18/app_python
# Prefer flake output so the image matches flake.lock (same idea as Task 1):
nix build .#dockerImage
docker load < result
# Impure alternative: nix-build docker.nix  (uses <nixpkgs>, may differ from classmates)

docker stop lab2-container nix-container 2>/dev/null || true
docker rm lab2-container nix-container 2>/dev/null || true

docker build -t lab2-app:v1 -f Dockerfile .
docker run -d -p 5000:8080 --name lab2-container lab2-app:v1

docker run -d -p 5001:5000 --name nix-container devops-info-service-nix:1.0.0

curl http://localhost:5000/health
curl http://localhost:5001/health
```

### 2.3 Reproducibility and size

**Nix tarball twice** (use the flake so the tarball matches `flake.lock`; impure `nix-build docker.nix` can differ across channels):

```bash
rm -f result
nix build .#dockerImage
sha256sum result

rm -f result
nix build .#dockerImage
sha256sum result
```

Expect **identical** SHA-256 of `result` when inputs are unchanged.

**Recorded (two consecutive `nix build .#dockerImage` in `labs/lab18/app_python`, same commit):**

```text
669475522b05307cf9c61f5ffc807316c3dc1331b9952f97abdd1e1c5ae0cd36  result
669475522b05307cf9c61f5ffc807316c3dc1331b9952f97abdd1e1c5ae0cd36  result
```

**Docker image store path (tarball) from `nix build .#dockerImage --print-out-paths`:** `/nix/store/91zxfyv0piq440g2s72yj8z71nvhpri9-devops-info-service-nix.tar.gz`

**Traditional image twice:**

```bash
docker build -t lab2-app:test1 .
docker save lab2-app:test1 | sha256sum
sleep 2
docker build -t lab2-app:test2 .
docker save lab2-app:test2 | sha256sum
```

Expect **different** hashes (timestamps, metadata, base image digest drift).

| Metric | Lab 2 Dockerfile | Lab 18 Nix `dockerTools` |
|--------|------------------|-------------------------|
| Reproducible digest of `docker save` | No (timestamps / base tag movement) | Yes (same inputs → same tarball bytes) |
| Base image | `python:3.11-slim` (moving target) | No classic base; store paths only |
| Typical size | Larger (full distro layer) | Smaller closure (varies with deps) |

Paste `docker history` for both images after you load/run them locally: _(fill in — e.g. `docker history lab2-app:v1` and `docker history devops-info-service-nix:1.0.0`)_.

### 2.4 Why Dockerfiles are not bit-for-bit reproducible

Layer IDs and config include creation times, build host metadata, and non-pinned package fetches (`apt`, `pip` without full lock). Base image tags can be retagged to new digests. Nix fixes inputs (`flake.lock` + store model) and can fix `created` in the image spec.

**Reflection:** If Lab 2 were redone with Nix first, you would treat the image as **the output of a pure build** (`nix build .#dockerImage`), load it, and optionally reference **immutable** digests from your registry in Helm values.

---

## Bonus — Flakes and comparison to Helm (Lab 10)

### `flake.nix` overview

- **`inputs.nixpkgs.url`** — follows `nixos-24.11`; **`flake.lock`** pins the exact `rev` and `narHash`.
- **`packages.<system>.default`** — same app as `default.nix` but with locked `nixpkgs`.
- **`packages.<system>.dockerImage`** — locked `docker.nix` output.
- **`devShells.<system>.default`** — `nix develop` drops you into Python with the same packages as the app (compare to `python -m venv` + `pip install`).

Lock snippet (your machine will match structurally; rev may update if you run `nix flake update`):

```json
"nixpkgs": {
  "locked": {
    "lastModified": 1751274312,
    "narHash": "sha256-/bVBlRpECLVzjV19t5KMdMFWSwKLtb5RyXdjz3LJT+g=",
    "owner": "NixOS",
    "repo": "nixpkgs",
    "rev": "50ab793786d9de88ee30ec4e4c24fb4236fc2674",
    "type": "github"
  }
}
```

### Helm (`k8s/devops-app/values.yaml`) vs Flakes

Helm pins the **image** repository and tag:

```yaml
image:
  repository: ray326sq/devops-info-python
  tag: "lab03"
  pullPolicy: IfNotPresent
```

That does **not** pin bytes inside the image, Python wheels, or chart dependencies. A flake lock pins **nixpkgs** (tens of thousands of packages) and therefore the whole build closure.

**Combined approach:** `nix build .#dockerImage` → load/push image → in Helm use an **immutable digest** (`image: repo@sha256:…`) so deploys reference exact bytes; the flake still proves how those bytes were produced.

### Cross-machine check

After pushing Git:

```bash
nix build github:<youruser>/DevOps-Core-Course?dir=labs/lab18/app_python#default
readlink result
```

Two machines on the same commit get the **same** store path for the flake default package.

### Dev shell vs venv

| Aspect | Lab 1 venv | `nix develop` |
|--------|------------|----------------|
| Python version | Whatever you installed | Pinned by nixpkgs revision |
| Dependencies | pip-resolved | Nix closure / same as app |
| Sharing | Requires exporting lock + hashes | `flake.lock` only |

**Recorded `nix develop` check (this flake):**

```text
Python: Python 3.12.8
Flask: 3.0.3  # via python -c "import flask; print(flask.__version__)" (deprecation warning may appear)
```

---

## Reflection (short)

- **Nix from day one in Lab 1:** One locked toolchain for every teammate and CI job; no “works on my laptop” from drifting wheels.
- **Flakes vs Helm tags:** Helm is great for **what** runs in the cluster; flakes prove **how** the artifact was built. Together (image digest + flake lock) is stronger than either alone.
