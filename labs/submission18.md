# Lab 18 submission — Reproducible builds with Nix

**Student environment:** macOS (Darwin). Nix commands were run inside the official **`nixos/nix`** Docker image with the repository bind-mounted at `/src`, because Nix is not installed on the host. Builds used **Linux aarch64** (`arm64`) inside that container.

**Repository layout:**

- `app_python/` — Lab 1–2 baseline (Flask service + traditional `Dockerfile`) for comparison.
- `labs/lab18/app_python/` — same app plus `default.nix`, `docker.nix`, `flake.nix`, `flake.lock`.

---

## Task 1 — Reproducible Python app

### Nix usage

Example invocations (from repo root):

```bash
docker run --rm -v "$PWD:/src:rw" -w /src/labs/lab18/app_python nixos/nix:latest \
  nix-build --option sandbox false default.nix
./result/bin/devops-info-service   # inside the container; health on port 5000
```

`nix --version` inside `nixos/nix` (verified earlier in the lab): **Nix 2.31** (image updates may bump the patch level).

### `default.nix` — field-by-field

| Field | Role |
|--------|------|
| `pkgs ? import <nixpkgs> {}` | Entry point: evaluates against the ambient nixpkgs (channel in the container, or flake-locked `pkgs` when imported from `flake.nix`). |
| `runCommand "devops-info-service-src"` | Builds a **minimal source tree** containing only `app.py` and `requirements.txt`. This avoids accidentally hashing build artefacts such as the `result` symlink or `flake.lock` when they appear in the same directory (see “Pitfalls” below). |
| `buildPythonApplication` | nixpkgs helper for Python programs. |
| `pname` / `version` | Package identity; appears in the store path name. |
| `format = "other"` | No `pyproject.toml` / `setup.py`; install is custom. |
| `propagatedBuildInputs` | Runtime Python deps (`flask` and its closure). |
| `nativeBuildInputs = [ makeWrapper ]` | Provides `makeWrapper` for the install phase. |
| `installPhase` | Copies `app.py` under `$out/libexec/...` and wraps `python3` with `PYTHONPATH` so the Flask app runs as `devops-info-service`. |

### Store paths and reproducibility

After `nix-build default.nix` (Docker workflow above), the output was linked as:

```text
/nix/store/bdp6afdbidkgdrdi43nwqyiy1cjplwgc-devops-info-service-1.0.0
```

Repeated builds with unchanged sources reuse this path (cache hit) or reproduce it after garbage collection (same path hash).

Example: after `nix-build default.nix` in `nixos/nix` (Linux **aarch64**), `nix-hash --type sha256 result` reported **`509707673e7ce13d4dbf9948749337e1ac5ebec70c263e75a2ffb20d5e5fb1e7`**, with `readlink result` → `/nix/store/bdp6afdbidkgdrdi43nwqyiy1cjplwgc-devops-info-service-1.0.0`. Rebuilding with the same nixpkgs reproduces the same path and hash.

**Practical check:** `readlink result` twice after `nix-collect-garbage` / `nix-store --delete` should return the **same path** if nothing in the derivation inputs changed.

### Pitfall: `src = ./.` and local files

Using the entire directory as `src` means **any new file** (for example `flake.lock` or a `result` symlink left by `nix-build docker.nix`) changes the source hash and produces a **different** store path and Docker tarball. This was observed as differing `sha256sum result` between back-to-back `nix-build docker.nix` runs until the source was narrowed to **only** the application files.

### Lab 1 `pip` vs Nix

| Aspect | Lab 1 (venv + pip) | Lab 18 (Nix) |
|--------|--------------------|--------------|
| Python version | Whatever the developer installed | Fixed by nixpkgs revision |
| Transitive deps | Not pinned unless using strict pip tooling | Fully pinned via nixpkgs graph |
| Reproducibility | Best-effort with lock files | Content-addressed store paths |
| `requirements.txt` | Declares direct deps only; still useful for docs | Kept for parity with Lab 1; build uses nixpkgs `flask` |

**Why `requirements.txt` is weaker:** it does not, by itself, pin the entire **closed** dependency graph the way a nixpkgs revision does; transitives and build tools can still drift unless you adopt additional Python packaging discipline.

### Nix store path shape

`/nix/store/<hash>-<name>-<version>/`

- **`<hash>`** — cryptographic hash of *all* inputs (sources, deps, builder flags).
- **`<name>-<version>`** — human-readable package id (here `devops-info-service-1.0.0`).

### Reflection

If Nix had been used from Lab 1, everyone would share the same interpreter, Flask, and transitive libraries without hand-managed virtualenvs, and CI could verify the same store path as developers.

---

## Task 2 — Reproducible Docker images

### Lab 2 `Dockerfile` (reference)

See `app_python/Dockerfile`: `python:3.13-slim`, `pip install`, copy `app.py`.

### `docker.nix`

| Attribute | Role |
|-----------|------|
| `import ./default.nix { inherit pkgs; }` | Reuses the same application derivation as Task 1. |
| `buildLayeredImage` | Builds a layered tarball loadable with `docker load`. |
| `contents = [ app ]` | Closes over the app and its runtime dependencies. |
| `config.Cmd` | Runs the wrapped entrypoint in the image. |
| `created = "1970-01-01T00:00:01Z"` | **Fixed** timestamp for reproducibility (per lab guidance). |

### Rebuild test — Nix docker tarball

Two consecutive `nix-build docker.nix` runs (after fixing `src`; Linux aarch64 in Docker):

```text
hash1=d249e44726956eb2bdb8e4f60001417c38c7878daca7d384f792848bcbcc8d1f
hash2=d249e44726956eb2bdb8e4f60001417c38c7878daca7d384f792848bcbcc8d1f
```

Identical — the gzip tarball from Nix is bit-identical across rebuilds.

### Rebuild test — traditional Docker image

Two `docker build` + `docker save` runs from `app_python/` (host Docker):

```text
510275ddff612c1cc254ee4e4d5986fde07436a9811169ef2b6a29824176aa6a  -
624089bca243f944736d58cc5ed84d018a1a1016f9ffc61394fd4e03bf9c039a  -
```

Different SHA-256 streams — consistent with non–bit-reproducible layer metadata and timestamps even when layer file content is similar.

### Image size (directional)

| Image | Reported size (`docker images`) |
|-------|----------------------------------|
| `lab18-lab2:a` / `:b` (Dockerfile) | **221MB** |
| Nix-produced image | Load tarball (`docker load < result`) and compare with `docker images devops-info-service-nix:1.0.0` — expected smaller runtime closure than full `python:slim` stack |

### Why ordinary Dockerfiles are not bit-reproducible

Build timestamps, image config metadata, tag roll-forward on base images, and non-deterministic ordering in some tooling all contribute. Nix fixes known inputs (`created`, store paths) so the **exported tarball** hash is stable.

### Reflection

Redoing Lab 2 with Nix would mean treating the image as **another derivation** of the same app, publishing tarball digests, and only tagging images with content hashes for Helm/CI.

---

## Bonus — Flakes (Lab 10 comparison)

### `flake.nix`

- **inputs.nixpkgs** — pinned to branch `nixos-24.11`; exact **rev** captured in `flake.lock`.
- **outputs.packages** — `default` (app) and `dockerImage` (tarball) per supported system in `legacyPackages`.
- **devShells.default** — `python3` + `python3Packages.flask` for interactive work.

### `flake.lock` excerpt

```json
"nixpkgs": {
  "locked": {
    "lastModified": 1751274312,
    "narHash": "sha256-/bVBlRpECLVzjV19t5KMdMFWSwKLtb5RyXdjz3LJT+g=",
    "owner": "NixOS",
    "repo": "nixpkgs",
    "rev": "50ab793786d9de88ee30ec4e4c24fb4236fc2674",
    "type": "github"
  },
  "original": {
    "owner": "NixOS",
    "ref": "nixos-24.11",
    "repo": "nixpkgs",
    "type": "github"
  }
}
```

### Flake build outputs (Linux aarch64, inside Docker)

```bash
nix build --accept-flake-config --extra-experimental-features "nix-command flakes" \
  --option sandbox false .#default
```

```text
/nix/store/6pcxkypq7f54wplx12yc1p0ix93m0hic-devops-info-service-1.0.0
nix-hash --type sha256 result → 6ec2b2694ff6704994c4bd1e9415c3c3c14900ea057e7774dfa2c4fdf1420dd0
```

```bash
nix build ... .#dockerImage
```

```text
/nix/store/a6iq2kd7s1xfxy31imniqs593c8a0lfx-devops-info-service-nix.tar.gz
nix-hash --type sha256 result → 1a3cbbdd31123df21c50e5b29227a261f7d7eb695fe165638d7c84081724e556
```

> **Note:** Classic `nix-build` without flakes used the image’s **nixpkgs channel** (newer Python 3.13 / Flask 3.1.x in logs), while the **flake** used the **locked** nixpkgs rev above (Python **3.12.8**, Flask **3.0.3**). Both are reproducible **within their own pinned nixpkgs**.

### `nix develop`

```text
nix develop ... -c python -c "import flask; print(flask.__version__)"
# → 3.0.3 (with upstream DeprecationWarning on __version__)
```

Compared to Lab 1’s venv: one command enters a shell whose tools are pinned by `flake.lock`, not by whatever `pip` resolves today.

### Helm (Lab 10) vs Flakes

| | Helm `values.yaml` image tag | Flake lock |
|--|------------------------------|------------|
| Pins container tag | Yes | N/A by itself |
| Pins OS/Python/libs inside image | No | Yes (via nixpkgs rev) |
| Pins build tooling | No | Yes |

Combined workflow: `nix build .#dockerImage` → load → push by digest → reference **digest** in Helm values.

---

## PR checklist (course instructions)

```text
Platform: GitHub

- [x] Task 1 — Build Reproducible Artifacts from Scratch (6 pts)
- [x] Task 2 — Reproducible Docker Images with Nix (4 pts)
- [x] Bonus Task — Modern Nix with Flakes (2 pts)
```

Screenshots of browsers hitting `/` and `/health` were omitted here; run the service in Docker or `nix run`/`result/bin/...` and capture if your instructor requires pixels. **Cross-machine check:** clone on a second machine with Nix, run the same `nix build` with the committed `flake.lock`, and compare `readlink result`.
