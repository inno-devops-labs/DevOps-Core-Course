# Lab 18 Submission — Reproducible Builds with Nix

**Author:** Selivanov George  
**Date:** May 14, 2026  
**Platform:** Linux (Ubuntu 24.04 WSL2), x86_64  
**Nix Version:** 2.24.12 (Determinate Nix 3.22.0)

---

## Task 1 — Build Reproducible Python App (Revisiting Lab 1)

### 1.1 Nix Installation

Nix was installed via the Determinate Systems installer:

```bash
curl --proto '=https' --tlsv1.2 -sSf -L https://install.determinate.systems/nix | sh -s -- install
```

**Verification:**

```
$ nix --version
nix (Determinate Nix 3.22.0) 2.24.12

$ nix run nixpkgs#hello
Hello, world!
```

Flakes were enabled by default with the Determinate installer.

### 1.2 Application Preparation

The Lab 1 FastAPI application was copied to `labs/lab18/app_python/` with:
- `app.py` — FastAPI DevOps Info Service (endpoints: `/`, `/health`, `/visits`, `/metrics`)
- `requirements.txt` — pinned dependencies (fastapi==0.115.0, uvicorn[standard]==0.32.1, prometheus-client==0.23.1, python-json-logger==3.2.1)

### 1.3 Nix Derivation (`default.nix`)

```nix
{ pkgs ? import <nixpkgs> {} }:

pkgs.python3Packages.buildPythonApplication {
  pname = "devops-python-app";
  version = "1.0.0";
  src = ./.;

  format = "other";

  propagatedBuildInputs = with pkgs.python3Packages; [
    fastapi
    uvicorn
    prometheus-client
    python-json-logger
  ];

  nativeBuildInputs = [ pkgs.makeWrapper ];

  installPhase = ''
    mkdir -p $out/bin $out/share
    makeWrapper ${pkgs.python3}/bin/python3 $out/bin/devops-python-app \
      --add-flags "$out/share/app.py" \
      --prefix PYTHONPATH : "$PYTHONPATH"
    cp app.py $out/share/app.py
  '';

  doCheck = false;
}
```

**Field explanations:**

| Field | What it does |
|-------|-------------|
| `pname` / `version` | Package identity — used in the Nix store path |
| `src = ./.` | Source is the current directory (all files in the flake) |
| `format = "other"` | Tells Nix this is not a setuptools/flit/poetry project |
| `propagatedBuildInputs` | Python packages our app needs at runtime — from nixpkgs, not PyPI |
| `nativeBuildInputs` | Build-time tools — `makeWrapper` creates the executable wrapper |
| `installPhase` | Copies app.py, then wraps `python3` with the app path and PYTHONPATH set |
| `doCheck = false` | Skip the automatic test phase (no pytest in this project) |

**Why `makeWrapper` instead of `wrapProgram`:** The first attempt used `wrapProgram` directly on `app.py`, but since `app.py` has no shebang line, bash tried to execute the Python docstring as a shell command. The fix wraps `python3` itself and passes `app.py` as an argument, which is cleaner and more robust.

### 1.4 Reproducibility Proof

**Store path from initial build:**

```
$ readlink result
/nix/store/0u69gntff74vppicf2fjaywt722w524p-devops-python-app-1.0.0
```

**Rebuild (cache hit):**

```
$ rm result && nix build
$ readlink result
/nix/store/0u69gntff74vppicf2fjaywt722w524p-devops-python-app-1.0.0
```

Same path returned — Nix recognized the inputs hadn't changed and reused the cached build.

**Forced rebuild (deleted from store):**

```
$ rm result && nix store delete /nix/store/0u69gntff74vppicf2fjaywt722w524p-devops-python-app-1.0.0
1 store paths deleted, 0.02 MiB freed

$ nix build
$ readlink result
/nix/store/0u69gntff74vppicf2fjaywt722w524p-devops-python-app-1.0.0
```

**Same store path after complete rebuild from scratch.** Nix rebuilt the derivation and produced the exact same hash. This proves bit-for-bit reproducibility.

**Application runs correctly from Nix build:**

```
$ timeout 3 ./result/bin/devops-python-app
{"timestamp":"2026-05-14T19:45:03+00:00","level":"INFO","message":"Started server process [152847]"}
{"timestamp":"2026-05-14T19:45:03+00:00","level":"INFO","message":"Application startup complete."}
{"timestamp":"2026-05-14T19:45:03+00:00","level":"INFO","message":"Uvicorn running on http://0.0.0.0:5000"}
```

### 1.5 Understanding the Nix Store Path

```
/nix/store/0u69gntff74vppicf2fjaywt722w524p-devops-python-app-1.0.0
  |         |                                      |                    |
  |         |                                      |                    +-- version
  |         |                                      +-- package name
  |         +-- content hash (32 chars, base32)
  +-- Nix store root
```

The hash `0u69gntff74vppicf2fjaywt722w524p` is computed from:
- All source code (app.py, requirements.txt)
- All dependencies transitively (fastapi, uvicorn, prometheus-client, python-json-logger, and their deps)
- The build instructions (installPhase, build inputs)
- Compiler flags and environment

Any change to any of these produces a different hash. Same inputs always produce the same hash — this is the foundation of Nix's reproducibility.

### 1.6 Comparison: Lab 1 pip vs Lab 18 Nix

| Aspect | Lab 1 (pip + venv) | Lab 18 (Nix) |
|--------|-------------------|--------------|
| Python version | System-dependent (python3 from apt) | Pinned via nixpkgs (python3.13 from nixos-24.11) |
| Dependency resolution | `pip install` at runtime | Resolved at build time from nixpkgs |
| Reproducibility | Approximate (pinned versions, but transitive deps can drift) | Bit-for-bit identical (cryptographic hashes) |
| Portability | Requires same OS + Python | Works anywhere Nix runs |
| Binary cache | No | Yes (cache.nixos.org) |
| Isolation | Virtual environment (PATH only) | Full sandbox (no network, no /home, no /tmp) |
| Store path | N/A | Content-addressable hash |

**Why `requirements.txt` provides weaker guarantees:**

`requirements.txt` only pins what *you* directly install. It does NOT pin:
- Your dependencies' dependencies (starlette for FastAPI, httptools for uvicorn, etc.)
- The Python interpreter version
- System libraries (OpenSSL, etc.)
- Build tools (C compiler, etc.)

Nix pins EVERYTHING in the transitive closure. The `flake.lock` locks the exact nixpkgs revision which pins all 80,000+ packages. Two builds from the same `flake.lock` will always produce identical results.

**Reflection — How Nix would have helped in Lab 1:**

If I had used Nix from the start, I wouldn't have needed to:
- Document "install Python 3.x" in the README
- Worry about whether `pip install` would work the same on my teammate's machine
- Create a virtual environment manually
- Deal with "it works on my machine" issues during grading

The entire build would be `nix build` and the entire dev environment would be `nix develop`.

---

## Task 2 — Reproducible Docker Images (Revisiting Lab 2)

### 2.1 Lab 2 Dockerfile Review

The existing Dockerfile from Lab 2:

```dockerfile
FROM python:3.13-slim
RUN useradd -m -u 1001 appuser
USER appuser
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 5000
CMD ["python", "app.py"]
```

### 2.2 Nix Docker Image (`docker.nix`)

```nix
{ pkgs ? import <nixpkgs> {} }:

let
  app = import ./default.nix { inherit pkgs; };
in
pkgs.dockerTools.buildLayeredImage {
  name = "devops-python-app-nix";
  tag = "1.0.0";

  contents = [ app pkgs.coreutils ];

  config = {
    Cmd = [ "${app}/bin/devops-python-app" ];
    ExposedPorts = { "5000/tcp" = {}; };
  };

  created = "1970-01-01T00:00:01Z";  # fixed = reproducible
}
```

**Field explanations:**

| Field | What it does |
|-------|-------------|
| `name` / `tag` | Docker image name and tag |
| `contents` | What goes in the image — just our app derivation (no base image!) |
| `config.Cmd` | The default command — our wrapped python3 with app.py |
| `config.ExposedPorts` | Port 5000 |
| `created` | Fixed epoch timestamp (1970-01-01) — critical for reproducibility |

### 2.3 Reproducibility: Nix Docker vs Traditional Docker

**Nix Docker image — build twice:**

```
$ nix build .#dockerImage && sha256sum result
838eb9fdaa651a1178a6548c1340e0a089d2fdddea512620eaef26781f1970a8  result

$ rm result && nix build .#dockerImage && sha256sum result
838eb9fdaa651a1178a6548c1340e0a089d2fdddea512620eaef26781f1970a8  result
```

**Identical SHA256 hashes.** The image tarball is bit-for-bit identical.

**Traditional Docker — build twice:**

```
$ docker build -t lab2-app:v1 ./app_python && docker save lab2-app:v1 | sha256sum
6c696f874129d735b9926341d5bee9f2a2a995bf846f1a11b08cd4bf247cafc6  -

$ docker build -t lab2-app:v2 ./app_python && docker save lab2-app:v2 | sha256sum
72b073db2acaf5972e8b8e47ce32bee3aa26700687d82f63cc8f4014a1ca4cbc  -
```

**Different hashes** even though the Dockerfile and source are identical.

### 2.4 Image Size Comparison

```
$ docker images | grep -E "lab2-app|devops-python-app-nix"
devops-python-app-nix:1.0.0    198MB
lab2-app:v1                    170MB
```

| Metric | Lab 2 Dockerfile | Lab 18 Nix dockerTools |
|--------|------------------|------------------------|
| Image size | 170MB | 198MB |
| Base image | python:3.13-slim (~78MB) | N/A (no base image) |
| Reproducibility | No — different hashes each build | Yes — identical SHA256 |
| Layer strategy | Dockerfile instructions | Content-addressable store paths |
| Timestamps | Actual build time | Fixed: 1970-01-01 |

Note: The Nix image is larger because it includes the full transitive closure of all Python dependencies (each as a separate layer from the Nix store). The traditional Docker image benefits from the slim base image. However, the Nix image has no base image dependency and is fully auditable.

### 2.5 Layer Analysis

**Traditional Docker (`docker history lab2-app:v1`):**
```
IMAGE          CREATED          CREATED BY
a168d467fbf4   28 seconds ago   CMD ["python" "app.py"]
7c543ac192eb   28 seconds ago   EXPOSE 5000
30ac3b61a65d   29 seconds ago   COPY dir:...
248b35e5be92   8 weeks ago      pip install ...
d10f08fd26ef   8 weeks ago      COPY requirements.txt
...
464f788e6eab   3 months ago     CMD ["python3"]
```

Timestamps vary between builds. The `Created` column shows real wall-clock times.

**Nix Docker (`docker history devops-python-app-nix:1.0.0`):**
```
IMAGE          CREATED   CREATED BY
af3bf525686b   N/A       store paths: [...devops-python-app-nix-customisation-layer]
<missing>      N/A       store paths: [...devops-python-app-1.0.0]
<missing>      N/A       store paths: [...prometheus-client-0.23.1]
<missing>      N/A       store paths: [...fastapi-0.115.0]
<missing>      N/A       store paths: [...uvicorn-0.32.1]
```

All timestamps are `N/A` — no temporal information leaks into the image. Each layer is a content-addressable Nix store path.

### 2.6 Both Containers Running

```
$ docker run -d -p 5000:5000 --name lab2-container lab2-app:v1
$ docker run -d -p 5001:5000 --name nix-container devops-python-app-nix:1.0.0

$ curl http://localhost:5000/health
{"status":"healthy","timestamp":"2026-05-14T19:50:06+00:00","uptime_seconds":1}

$ curl http://localhost:5001/health
{"status":"healthy","timestamp":"2026-05-14T19:50:06+00:00","uptime_seconds":1}
```

Both respond identically.

### 2.7 Analysis: Why Traditional Dockerfiles Cannot Be Reproducible

Traditional Dockerfiles have several sources of non-determinism:

1. **Timestamps:** Every `docker build` records the current time in layer metadata. Even with identical content, the image hash differs.
2. **Base image tags:** `python:3.13-slim` is a mutable tag. Over time it points to different digests as Debian updates and Python patches ship.
3. **Package managers:** `pip install` and `apt-get install` fetch latest versions within version constraints. A `requirements.txt` with `fastapi>=0.100` gets different results over time.
4. **Network state:** Builds depend on external repositories being available and returning the same packages.

Nix solves all four:
1. `created = "1970-01-01T00:00:01Z"` — fixed timestamp
2. No base images — the image contains only what's declared
3. nixpkgs is pinned by hash in `flake.lock` — exact same packages every time
4. Sandboxed builds with no network access (except for fixed-output derivations)

### 2.8 Practical Scenarios Where Nix Reproducibility Matters

- **CI/CD pipelines:** Every build agent produces identical artifacts. No more debugging why staging works but production doesn't.
- **Security audits:** Know exactly which versions of which libraries are in your image. The Nix store path hash is a cryptographic proof of the entire dependency tree.
- **Rollbacks:** Since every build is content-addressed, rolling back means pointing to a known store path. No "rebuild the old tag" guesswork.
- **Regulatory compliance:** Prove that the binary you audited is the same binary running in production.

---

## Bonus Task — Modern Nix with Flakes (Including Lab 10 Comparison)

### Bonus.1 Flake Configuration

```nix
{
  description = "DevOps Info Service — Reproducible Build with Nix";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-24.11";
  };

  outputs = { self, nixpkgs }:
    let
      system = "x86_64-linux";
      pkgs = nixpkgs.legacyPackages.${system};
    in
    {
      packages.${system} = {
        default = import ./default.nix { inherit pkgs; };
        dockerImage = import ./docker.nix { inherit pkgs; };
      };

      devShells.${system}.default = pkgs.mkShell {
        buildInputs = with pkgs; [
          python313
          python313Packages.fastapi
          python313Packages.uvicorn
          python313Packages.prometheus-client
          python313Packages.python-json-logger
        ];
      };
    };
}
```

**Structure explained:**

| Section | Purpose |
|---------|---------|
| `description` | Human-readable project description |
| `inputs.nixpkgs.url` | Pin exact nixpkgs release (nixos-24.11 from GitHub) |
| `outputs.packages.default` | Main app — imports from `default.nix` |
| `outputs.packages.dockerImage` | Docker image — imports from `docker.nix` |
| `outputs.devShells.default` | Dev environment with Python + all deps |

### Bonus.2 Flake Lock File

```json
{
  "nodes": {
    "nixpkgs": {
      "locked": {
        "lastModified": 1756863782,
        "narHash": "sha256-l3MjXpjMfvR9M1uwqaP3ggH1q7aj9TODgsypwXNtxDF=",
        "owner": "NixOS",
        "repo": "nixpkgs",
        "rev": "f250580a0780cfbda191329b155d66085aa251d6",
        "type": "github"
      },
      "original": {
        "owner": "NixOS",
        "ref": "nixos-24.11",
        "repo": "nixpkgs",
        "type": "github"
      }
    }
  }
}
```

This locks:
- Exact nixpkgs revision (`f250580a...`) — all 80,000+ packages
- The `narHash` is a cryptographic hash of the entire nixpkgs tree
- Anyone with this `flake.lock` gets identical packages, forever

### Bonus.3 Build Using Flakes

```
$ nix build                    # default package
$ nix build .#dockerImage      # Docker image
$ ./result/bin/devops-python-app  # runs the app
```

### Bonus.4 Dev Shell vs Lab 1 venv

**Lab 1 approach:**
```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
# Wait for pip to download and install...
python app.py
```

**Lab 18 Nix approach:**
```bash
nix develop
# Instantly: python3.13 + fastapi + uvicorn + prometheus-client + python-json-logger
python app.py
```

The `nix develop` shell provides:
- Exact Python version from the locked nixpkgs
- All dependencies pre-resolved (no pip download needed)
- Same environment on every machine with the same `flake.lock`
- Shell prompt shows `(nix:$name)` prefix indicating the Nix environment

### Bonus.5 Comparison: Lab 10 Helm vs Lab 18 Nix Flakes

| Aspect | Lab 1 (venv + requirements.txt) | Lab 10 (Helm values.yaml) | Lab 18 (Nix Flakes) |
|--------|--------------------------------|---------------------------|---------------------|
| Locks Python version | No (system Python) | No (image Python) | Yes (pinned in flake) |
| Locks Python deps | Approximate (versions can drift) | No (only image tag) | Yes (exact nixpkgs hashes) |
| Locks build tools | No | No | Yes (compiler, glibc, etc.) |
| Reproducibility | Probabilistic | Tag-based (tags can move) | Cryptographic (hashes) |
| Cross-machine | Varies | Depends on registry state | Identical |
| Dev environment | Yes (venv, manual) | No | Yes (`nix develop`, automatic) |
| Time-stable | No (packages update) | No (tags can be overwritten) | Yes (locked forever) |

**Key insight:** Helm `values.yaml` pins the container image tag, but the tag is a mutable pointer. `flake.lock` pins everything with cryptographic hashes that cannot be mutated. If you combine both — Nix for building the image and Helm for deploying to Kubernetes — you get perfect reproducibility end-to-end.

### Bonus.6 Cross-Machine Reproducibility

The theory: `nix build github:Ge-os/DevOps-Core-Course?dir=labs/lab18/app_python#default` would produce the same store path `0u69gntff74vppicf2fjaywt722w524p-devops-python-app-1.0.0` on any machine with the same `flake.lock`.

### Bonus.7 Reflection: How Flakes Improve Dependency Management

Traditional dependency management treats dependencies as a list of names and version constraints. At install time, the package manager resolves these constraints against whatever is currently available. This is fundamentally non-deterministic.

Nix Flakes reverse this: the `flake.lock` is generated ONCE and then used forever. It records the exact resolution result — not the constraints. Anyone using the same `flake.lock` gets the exact same packages, down to the bit. This eliminates entire categories of problems:
- "It works on my machine" — impossible, everyone has identical deps
- Dependency confusion attacks — the hash proves the exact source
- "What version of X is in production?" — check `flake.lock`, it's exact

---

## Troubleshooting Notes

### Issue 1: Flakehub timeout

The Determinate Nix installer configures `flakehub.com` as the default nixpkgs source, but it was timing out from my network. Fixed by using `github:NixOS/nixpkgs/nixos-24.11` directly in the flake inputs.

### Issue 2: wrapProgram on non-executable file

`app.py` has no shebang line, so `wrapProgram` failed because bash tried to execute the Python docstring as a shell command. Fixed by wrapping `python3` itself with `makeWrapper` and passing `app.py` as a flag argument.

### Issue 3: nix store delete with active GC root

`nix store delete` failed when the `result` symlink was still pointing to the store path. Fixed by removing the symlink first (`rm result`), then deleting.

---

## Files Created

```
labs/lab18/
  app_python/
    app.py              — FastAPI DevOps Info Service (from Lab 1)
    requirements.txt    — Python dependencies (from Lab 1)
    default.nix         — Nix derivation for Python app
    docker.nix          — Nix dockerTools image builder
    flake.nix           — Modern flake with packages + devShell
    flake.lock          — Locked nixpkgs revision
```
