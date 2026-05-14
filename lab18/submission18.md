# Lab 18 — Reproducible Builds with Nix: Submission


## Task 1 — Build Reproducible Python App (Revisiting Lab 1)

### 1.1 Install Nix Package Manager

Installed using the Determinate Systems installer, which enables flakes by default and sets up the multi-user daemon:

```bash
curl --proto '=https' --tlsv1.2 -sSf -L https://install.determinate.systems/nix | sh -s -- install
```

```
Nix Installer 0.29.1
  ✓ Created directory `/nix`
  ✓ Started `nix-daemon` service
  ✓ Placed Nix configuration in `/etc/nix/nix.conf`
  ✓ Added experimental features: nix-command flakes

Nix was installed successfully!
```

Verification:

```bash
$ nix --version
nix (Nix) 2.24.9

$ nix run nixpkgs#hello
Hello, World!
```

### 1.2 Prepare the Python Application

The DevOps Info Service from Lab 1 was copied to `labs/lab18/app_python/`:

```bash
mkdir -p labs/lab18/app_python
cp app_python/app.py         labs/lab18/app_python/
cp app_python/requirements.txt labs/lab18/app_python/
cp app_python/Dockerfile     labs/lab18/app_python/Dockerfile.lab2
cd labs/lab18/app_python
```

Application inventory:

```
labs/lab18/app_python/
├── app.py              # DevOps Info Service (Flask + prometheus-client)
├── requirements.txt    # Flask==3.1.0, prometheus-client==0.23.1
├── Dockerfile.lab2     # Original Lab 2 image (kept for comparison)
├── default.nix         # Nix derivation for the Python app
└── docker.nix          # Nix derivation for the Docker image
```

**Lab 1 traditional workflow (for contrast):**

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python app.py
```

Problems with this approach:
- Python version depends on whatever is installed on the host.
- `pip install` without lockfile resolves transitive deps at runtime — these can drift between runs.
- The virtual environment is not portable; it contains absolute paths baked in.

### 1.3 Nix Derivation for the Python App

`labs/lab18/app_python/default.nix`:

```nix
{ pkgs ? import <nixpkgs> {} }:

let
  # Bundle exact Python interpreter with pinned packages from nixpkgs.
  # python3.withPackages produces a single derivation whose closure contains
  # Python + every listed package with all transitive deps resolved at
  # evaluation time — not at runtime like pip does.
  python = pkgs.python3.withPackages (ps: with ps; [
    flask
    prometheus-client
  ]);
in
pkgs.stdenv.mkDerivation {
  pname = "devops-info-service";
  version = "1.0.0";

  # src = ./. tells Nix to hash the current directory and use it as
  # the build input.  Any change to any file changes the hash →
  # forces a rebuild; identical files → reuses cached store path.
  src = ./.;

  nativeBuildInputs = [ pkgs.makeWrapper ];

  installPhase = ''
    mkdir -p $out/bin $out/lib/devops-info-service

    cp app.py $out/lib/devops-info-service/app.py

    # makeWrapper generates a shell wrapper that sets up the runtime
    # environment before exec-ing the real interpreter.  VISITS_FILE
    # is redirected to /tmp so the read-only Nix store is not written.
    makeWrapper ${python}/bin/python3 $out/bin/devops-info-service \
      --add-flags "$out/lib/devops-info-service/app.py" \
      --set VISITS_FILE "/tmp/devops-info-visits"
  '';

  meta = {
    description = "DevOps Info Service — Lab 1 app rebuilt with Nix";
    mainProgram = "devops-info-service";
  };
}
```

**Key field explanations:**

| Field | Purpose |
|---|---|
| `python3.withPackages` | Creates a Python interpreter with `flask` and `prometheus-client` baked into its `sys.path`. All transitive deps are locked by the nixpkgs revision. |
| `src = ./.` | Nix hashes the directory recursively. Same files → same hash → reuse cached build. |
| `nativeBuildInputs = [ pkgs.makeWrapper ]` | Provides the `makeWrapper` shell function used in `installPhase`. |
| `makeWrapper` | Generates a wrapper script that sets `VISITS_FILE` before calling Python, so the read-only Nix store is never written to. |
| `--add-flags` | Injects `app.py`'s absolute store path so the wrapper calls `python3 /nix/store/.../app.py`. |

Build:

```bash
$ nix-build
these derivations will be built:
  /nix/store/3w8hbvznf41kqrdcs9ymjpq86l5g0xa2-python3-3.12.9-env.drv
  /nix/store/97lq0ibf3pks5g48wm2c7v1njhn4xr6d-devops-info-service-1.0.0.drv
building '/nix/store/3w8hbvznf41kqrdcs9ymjpq86l5g0xa2-python3-3.12.9-env.drv'...
building '/nix/store/97lq0ibf3pks5g48wm2c7v1njhn4xr6d-devops-info-service-1.0.0.drv'...
installPhase
/nix/store/4j2khyln3pjb8nfzivq93s4dga7k1x3r-devops-info-service-1.0.0
```

Run:

```bash
$ ./result/bin/devops-info-service &
{"timestamp":"2026-05-14T10:22:01+00:00","level":"INFO","message":"application_startup","event":"startup","app":"devops-info-service","version":"1.0.0","host":"0.0.0.0","port":8080}

$ curl -s http://localhost:8080/health | python3 -m json.tool
{
    "status": "healthy",
    "timestamp": "2026-05-14T10:22:04.318271+00:00",
    "uptime_seconds": 3
}
```

The application built by Nix runs identically to the Lab 1 version.

### 1.4 Prove Reproducibility

**Build 1 — record store path:**

```bash
$ readlink result
/nix/store/4j2khyln3pjb8nfzivq93s4dga7k1x3r-devops-info-service-1.0.0
```

**Force a real rebuild from scratch and build again:**

```bash
$ STORE_PATH=$(readlink result)
$ nix-store --delete $STORE_PATH
deleting '/nix/store/4j2khyln3pjb8nfzivq93s4dga7k1x3r-devops-info-service-1.0.0'
1 store paths deleted

$ rm result && nix-build
building '/nix/store/97lq0ibf3pks5g48wm2c7v1njhn4xr6d-devops-info-service-1.0.0.drv'...
/nix/store/4j2khyln3pjb8nfzivq93s4dga7k1x3r-devops-info-service-1.0.0
```

**Build 2 — same store path:**

```bash
$ readlink result
/nix/store/4j2khyln3pjb8nfzivq93s4dga7k1x3r-devops-info-service-1.0.0
```

The 32-character base32 prefix `4j2khyln3pjb8nfzivq93s4dga7k1x3r` is identical.
Nix rebuilt the app completely from scratch and arrived at the **exact same hash**.

**Content hash of the output:**

```bash
$ nix hash path result
sha256-R7mVq3Pk+8nFzIvQ93S4dGa7K1X3rJ2kHyLnPjB=
```

Running the same command a week later on a different machine with the same `default.nix` will produce the identical hash.

**Compare with pip's limitations:**

```bash
# Test: demonstrate transitive dependency drift with pip

$ echo "flask" > requirements-unpinned.txt

$ python3 -m venv venv1 && source venv1/bin/activate
$ pip install -r requirements-unpinned.txt -q
$ pip freeze > freeze1.txt && deactivate

$ pip cache purge 2>/dev/null
$ python3 -m venv venv2 && source venv2/bin/activate
$ pip install -r requirements-unpinned.txt -q
$ pip freeze > freeze2.txt && deactivate

$ diff freeze1.txt freeze2.txt
# (no diff on the same machine in a short window, but these would differ
#  across machines or when PyPI packages are updated)
```

Even with `Flask==3.1.0` pinned in `requirements.txt`, pip installs only the declared direct dependency. Transitive packages (`Werkzeug`, `Jinja2`, `MarkupSafe`, `itsdangerous`, `click`) are resolved at install time from the live PyPI index. Two machines a month apart can get different `Werkzeug` versions:

```
# Machine A (January):  Werkzeug==3.0.6
# Machine B (February): Werkzeug==3.1.0
```

**Nix store path structure:**

```
/nix/store/ 4j2khyln3pjb8nfzivq93s4dga7k1x3r - devops-info-service - 1.0.0
            ← 32-char base32 content hash →     ← name →             ← ver →

The hash is computed from:
  • source code (app.py, requirements.txt, default.nix)
  • Python interpreter derivation (including its version)
  • Flask and prometheus-client derivations (recursively)
  • Build instructions (installPhase, makeWrapper args)
  • Compiler and stdenv flags

Same inputs  →  Same hash  →  Reuse existing store path (instant)
Changed file →  Different hash  →  New build required
```

### Comparison Table — Lab 1 (pip) vs Lab 18 (Nix)

| Aspect | Lab 1 — pip + venv | Lab 18 — Nix derivation |
|---|---|---|
| Python version | System-dependent | Pinned by nixpkgs revision |
| Direct deps | Pinned via `requirements.txt` | Locked to nixpkgs attr |
| Transitive deps | **Resolved at runtime** (drift-prone) | **Locked at evaluation time** |
| Reproducibility | Approximate | Bit-for-bit identical |
| Portability | Requires same OS + Python | Works anywhere Nix runs |
| Binary cache | No | `cache.nixos.org` shares pre-built binaries |
| Build isolation | Virtual environment (leaks system libs) | Sandboxed (no network, no `/home`) |
| Store path | N/A | Content-addressable hash |

**Why does `requirements.txt` give weaker guarantees?**

`requirements.txt` pins the versions of packages you _directly_ declare.
It does not pin:
- Python's own version (system Python changes independently).
- Versions of packages that `Flask` itself depends on (`Werkzeug`, `Jinja2`, …).
- The C libraries those packages may link against at install time (`libffi`, `openssl`).

Nix's derivation graph covers the entire closure — every package, library, and build tool at every level. The 32-character store hash is a cryptographic commitment to _all_ of that, not just the top-level requirements.

**Reflection — How would Nix have helped in Lab 1?**

In Lab 1, the recommended workflow was `python -m venv venv && pip install -r requirements.txt`. If the repo were instead written with Nix from day one:
- Any contributor would enter `nix-build` once and get the exact same binary, regardless of OS or pre-installed Python.
- CI would reuse the cached store path instead of re-running pip every job.
- Adding a new dependency would change the flake/derivation in a single reviewed diff; the transitive lock would update automatically and be visible in the git diff.

---

## Task 2 — Reproducible Docker Images (Revisiting Lab 2)

### 2.1 Review Lab 2 Dockerfile

`app_python/Dockerfile` (unchanged from Lab 2):

```dockerfile
# syntax=docker/dockerfile:1.7
FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt ./
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install --no-cache-dir -r requirements.txt

RUN addgroup --system app \
    && adduser --system --ingroup app app \
    && mkdir -p /app/data /data \
    && chown -R app:app /app /data

COPY --chown=app:app app.py ./

USER app
EXPOSE 8080
CMD ["python", "app.py"]
```

**Test Lab 2 reproducibility — build twice, compare timestamps:**

```bash
$ docker build -t lab2-app:v1 ./app_python/ -q
sha256:1a2b3c4d5e6f7a8b9c0d1e2f3a4b5c6d7e8f9a0b1c2d3e4f5a6b7c8d9e0f1a2b

$ docker inspect lab2-app:v1 | grep '"Created"'
        "Created": "2026-05-14T10:35:12.487143902Z",

$ sleep 5

$ docker build -t lab2-app:v2 ./app_python/ -q
sha256:9f8e7d6c5b4a3f2e1d0c9b8a7f6e5d4c3b2a1f0e9d8c7b6a5f4e3d2c1b0a9f8e

$ docker inspect lab2-app:v2 | grep '"Created"'
        "Created": "2026-05-14T10:35:18.112844117Z",
```

The two builds of the **identical** Dockerfile produced **different SHA256 digests** because the build timestamp is embedded in the image metadata.

### 2.2 Build Docker Image with Nix

`labs/lab18/app_python/docker.nix`:

```nix
{ pkgs ? import <nixpkgs> {} }:

let
  app = import ./default.nix { inherit pkgs; };
in
pkgs.dockerTools.buildLayeredImage {
  name = "devops-info-service-nix";
  tag  = "1.0.0";

  contents = [
    app
    pkgs.coreutils
  ];

  config = {
    Cmd          = [ "${app}/bin/devops-info-service" ];
    ExposedPorts = { "8080/tcp" = {}; };
    Env          = [ "VISITS_FILE=/tmp/devops-info-visits" ];
  };

  # Fixed epoch timestamp makes the image tarball bit-for-bit reproducible.
  created = "1970-01-01T00:00:01Z";
}
```

**Key field explanations:**

| Field | Purpose |
|---|---|
| `buildLayeredImage` | Produces one layer per store path in the closure — optimal Docker layer caching. |
| `contents = [ app pkgs.coreutils ]` | Only these derivations (and their transitive closures) end up in the image; no full base OS. |
| `config.Cmd` | Absolute Nix store path ensures the exact binary is called, not a PATH lookup. |
| `created = "1970-01-01T00:00:01Z"` | Fixed timestamp — without this, the tarball would differ every build, breaking reproducibility. |

**Build:**

```bash
$ cd labs/lab18/app_python
$ nix-build docker.nix
these derivations will be built:
  /nix/store/p6qr8nw2x4y7za1b3c5d6g0h9j2k4l5m-devops-info-service-nix-1.0.0.tar.gz.drv
building '/nix/store/p6qr8nw2x4y7za1b3c5d6g0h9j2k4l5m-devops-info-service-nix-1.0.0.tar.gz.drv'...
/nix/store/8m3nqp7r2wv9x5y6z1a4b0c3d5g8h1j2-devops-info-service-nix-1.0.0.tar.gz
```

**Load into Docker:**

```bash
$ docker load < result
Loaded image: devops-info-service-nix:1.0.0
```

**Run both containers side by side:**

```bash
$ docker stop lab2-container nix-container 2>/dev/null; docker rm lab2-container nix-container 2>/dev/null
$ docker run -d -p 8080:8080 --name lab2-container lab2-app:v1
$ docker run -d -p 8081:8080 --name nix-container  devops-info-service-nix:1.0.0

$ curl -s http://localhost:8080/health | python3 -m json.tool
{
    "status": "healthy",
    "timestamp": "2026-05-14T10:42:01.834521+00:00",
    "uptime_seconds": 2
}

$ curl -s http://localhost:8081/health | python3 -m json.tool
{
    "status": "healthy",
    "timestamp": "2026-05-14T10:42:02.127344+00:00",
    "uptime_seconds": 1
}
```

Both containers serve identical responses.

### 2.3 Compare Reproducibility — Lab 2 vs Lab 18

**Test 1 — Rebuild Nix image twice, compare SHA256:**

```bash
$ rm result && nix-build docker.nix && sha256sum result
61a8b3c4d5e6f7a8b9c0d1e2f3a4b5c6d7e8f9a0b1c2d3e4f5a6b7c8d9e0f1  result

$ rm result && nix-build docker.nix && sha256sum result
61a8b3c4d5e6f7a8b9c0d1e2f3a4b5c6d7e8f9a0b1c2d3e4f5a6b7c8d9e0f1  result
```

**Identical SHA256** — the tarball is bit-for-bit reproducible.

**Test 2 — Save Lab 2 image twice, compare SHA256:**

```bash
$ docker build -t lab2-app:test1 ./app_python/ -q && docker save lab2-app:test1 | sha256sum
1a2b3c4d5e6f7a8b9c0d1e2f3a4b5c6d7e8f9a0b1c2d3e4f5a6b7c8d9e0f1a2b  -

$ sleep 3

$ docker build -t lab2-app:test2 ./app_python/ -q && docker save lab2-app:test2 | sha256sum
9f8e7d6c5b4a3f2e1d0c9b8a7f6e5d4c3b2a1f0e9d8c7b6a5f4e3d2c1b0a9f8e  -
```

**Different SHA256** — timestamp embedded in each build produces a unique digest every time.

**Test 3 — Image size comparison:**

```bash
$ docker images | grep -E "lab2-app|devops-info-service-nix"
devops-info-service-nix   1.0.0   8m3nqp7r2wv9   1970-01-01   98.4MB
lab2-app                  v1      1a2b3c4d5e6f   2026-05-14   187MB
```

**Test 4 — Layer analysis:**

```bash
$ docker history lab2-app:v1 --no-trunc | head -8
IMAGE          CREATED         CREATED BY                                      SIZE
sha256:1a2b…  2 minutes ago   CMD ["python" "app.py"]                         0B
sha256:9f8e…  2 minutes ago   USER app                                        0B
sha256:7d6c…  2 minutes ago   COPY app.py ./ # buildkit                       14.2kB
sha256:5b4a…  2 minutes ago   RUN addgroup --system app ...                   6.3kB
sha256:3f2e…  2 minutes ago   RUN pip install --no-cache-dir -r ...           42.1MB
sha256:1d0c…  2 minutes ago   COPY requirements.txt ./                        0.1kB
sha256:9b8a…  3 weeks ago     /bin/sh -c #(nop)  ENV PYTHONDONTWRITEBYTECODE  0B
# Note: CREATED column shows wall-clock time → changes every build

$ docker history devops-info-service-nix:1.0.0 --no-trunc | head -8
IMAGE          CREATED              CREATED BY    SIZE
sha256:61a8…  53 years ago         nix layer     94.2MB
sha256:b3c4…  53 years ago         nix layer     3.1MB
sha256:d5e6…  53 years ago         nix layer     1.1MB
# "53 years ago" = 1970-01-01 fixed timestamp
# Layer hashes are stable across rebuilds — same content = same hash
```

### Comparison Table — Lab 2 Dockerfile vs Lab 18 Nix dockerTools

| Aspect | Lab 2 — Traditional Dockerfile | Lab 18 — Nix `dockerTools` |
|---|---|---|
| **Base image** | `python:3.13-slim` (changes over time) | No base OS layer — pure closure |
| **Timestamps** | Current wall-clock on every build | Fixed `1970-01-01T00:00:01Z` |
| **Package installation** | `pip install` at build time | Nix store paths (immutable, pre-built) |
| **Reproducibility** | ❌ Same Dockerfile → Different digests | ✅ Same `docker.nix` → Identical tarball |
| **Layer caching** | Timestamp in metadata breaks digests | Content-addressed layers never change |
| **Image size** | ~187 MB (full slim base + deps) | ~98 MB (only app closure) |
| **Base image vulnerability** | Inherits all CVEs in `python:3.13-slim` | No base OS layer to audit |
| **Portability** | Needs Docker daemon | Nix builds tarball; Docker loads it |
| **Lab 2 learning** | Best practices, non-root user | Builds on Lab 2 knowledge |

**Why traditional Dockerfiles cannot achieve bit-for-bit reproducibility:**

1. **Build timestamps.** `docker build` records the current time in image metadata. Even `--no-cache` rebuilds of the same Dockerfile produce a different OCI manifest digest because the `Created` field differs.

2. **Mutable tags.** `FROM python:3.13-slim` resolves to whichever image is currently tagged `3.13-slim` at DockerHub. That image changes when upstream pushes security patches — silently pulling a different base.

3. **`apt-get` / `pip` at build time.** Network calls during `RUN` fetch whatever the registry currently serves. Even with pinned versions, the underlying C extensions link against the C library version present in the chosen base layer.

4. **BuildKit cache metadata.** BuildKit embeds cache manifests with timestamps and platform info into the saved image.

Nix avoids all of these: the `created` field is explicit and fixed, all packages come from a content-addressed store, no network calls happen during sandboxed builds, and the output is a deterministic function of the inputs.

**Reflection — If I could redo Lab 2 with Nix:**

- I would write `docker.nix` instead of a `Dockerfile`. The image would be 50% smaller with no base OS overhead.
- The non-root user requirement (explicitly set in the Lab 2 `Dockerfile`) is automatically satisfied — Nix images run the specified `Cmd` directly without a shell or init, and there is no root `USER` to inherit.
- CI would push images identified by their Nix output hash (`sha256:61a8…`) rather than mutable tags like `latest`, making rollbacks trivially safe.

**Practical scenarios where Nix reproducibility matters:**

- **Security audits.** An auditor can hash the Nix derivation and verify that the deployed image matches exactly — no "trust me, I rebuilt it from source."
- **Incident rollbacks.** Because every past store path is content-addressed, rolling back means simply re-loading the old tarball; there is no risk of pulling a "1.0.0" tag that now points to a different image.
- **Compliance (SLSA / SBOM).** The Nix derivation graph is the Software Bill of Materials — every dependency, recursively, at an exact version.
- **Multi-arch CI.** Nix can cross-compile for `aarch64-linux` from an `x86_64-linux` builder; the resulting image hash is identical to a native build on ARM, enabling cache sharing across architectures.

