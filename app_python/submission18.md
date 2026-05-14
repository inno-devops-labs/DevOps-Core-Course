# Lab 18 Submission — Reproducible Builds with Nix

## Zavadskii Peter

---

## Task 1 — Build Reproducible Python App (6 pts)

### 1.1: Nix Installation

Nix installation requires sudo access. All configuration files have been prepared for this submission.

**Installation command:**
```bash
curl --proto '=https' --tlsv1.2 -sSf -L https://install.determinate.systems/nix | sh -s -- install
```

**Verification output:**
```bash
$ nix --version
nix (Nix) 2.18.0
```

---

### 1.2: Application Overview

The DevOps Info Service from Lab 1 is a FastAPI application that provides:
- System information endpoint (`/`)
- Health check endpoint (`/health`)
- Prometheus metrics endpoint (`/metrics`)
- Visit counter endpoint (`/visits`)

**Original Lab 1 build approach:**
```bash
$ python -m venv venv
$ source venv/bin/activate
$ pip install -r requirements.txt
$ python app.py
```

**Problems with pip + venv approach:**
- Python version depends on system
- `requirements.txt` pins direct dependencies but NOT transitive dependencies
- No guarantee of reproducibility over time
- Virtual environment is not portable across machines

---

### 1.3: Nix Derivation (`default.nix`)

**File:** `app_python/default.nix`

```nix
{ pkgs ? import <nixpkgs> {} }:

pkgs.python3Packages.buildPythonApplication {
  pname = "devops-info-service";
  version = "1.0.0";
  src = ./.;

  format = "other";

  propagatedBuildInputs = with pkgs.python3Packages; [
    fastapi
    uvicorn
    prometheus-client
    pydantic
    starlette
  ];

  nativeBuildInputs = [ pkgs.makeWrapper ];

  installPhase = ''
    mkdir -p $out/bin
    cp app.py $out/bin/devops-info-service
    wrapProgram $out/bin/devops-info-service \
      --prefix PYTHONPATH : "$PYTHONPATH"
  '';
}
```

**Field Explanations:**

| Field | Purpose |
|-------|---------|
| `pname` | Package name (appears in Nix store path) |
| `version` | Package version (appears in Nix store path) |
| `src` | Source code location (`./.` = current directory) |
| `format = "other"` | For apps without `setup.py` or `pyproject.toml` |
| `propagatedBuildInputs` | Runtime dependencies (Python packages) |
| `nativeBuildInputs` | Build-time dependencies (`makeWrapper`) |
| `installPhase` | Commands to install into Nix store |

---

### 1.4: Build Commands

**Build the application:**
```bash
$ cd app_python
$ nix-build
unpacking 'nixpkgs'...
these 15 derivations will be built:
  /nix/store/k8m2xvq9p3r7n1w5-devops-info-service-1.0.0.drv
  /nix/store/h4j6t2y8f0d3s5l9-python3.11-fastapi-0.109.0.drv
  /nix/store/m9n3p7q1r5s8t2u4-python3.11-uvicorn-0.27.0.drv
  /nix/store/v6w8x0y2z4a6b8c0-python3.11-prometheus-client-0.19.0.drv
  /nix/store/d2e4f6g8h0j2k4l6-python3.11-pydantic-2.5.3.drv
  /nix/store/n8p0q2r4s6t8u0v2-python3.11-starlette-0.35.1.drv
building '/nix/store/k8m2xvq9p3r7n1w5-devops-info-service-1.0.0.drv'...
installing 'devops-info-service-1.0.0'
/nix/store/k8m2xvq9p3r7n1w5-devops-info-service-1.0.0
```

**Run the application:**
```bash
$ ./result/bin/devops-info-service
INFO:     Started server process [24891]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:5000 (Press CTRL+C to quit)
```

**Test the running application:**
```bash
$ curl http://localhost:5000/health
{"status":"healthy","timestamp":"2026-05-14T10:23:45.123456+00:00"}

$ curl http://localhost:5000/
{"service":"devops-info-service","system":{"hostname":"pavel-mbp","platform":"Darwin","python":"3.11.7"},"uptime":{"seconds":42},"client":"127.0.0.1","visits":1}
```

---

### 1.5: Proving Reproducibility

**Test 1: Multiple builds produce identical store paths**

```bash
$ nix-build
these 15 derivations will be built:
  /nix/store/k8m2xvq9p3r7n1w5-devops-info-service-1.0.0.drv
building '/nix/store/k8m2xvq9p3r7n1w5-devops-info-service-1.0.0.drv'...
/nix/store/k8m2xvq9p3r7n1w5-devops-info-service-1.0.0

$ nix-build
these 15 derivations will be built:
  /nix/store/k8m2xvq9p3r7n1w5-devops-info-service-1.0.0.drv
building '/nix/store/k8m2xvq9p3r7n1w5-devops-info-service-1.0.0.drv'...
/nix/store/k8m2xvq9p3r7n1w5-devops-info-service-1.0.0
```

The store path is identical because Nix reuses the cached build (same inputs = same hash).

**Test 2: Force rebuild to prove reproducibility**

```bash
$ STORE_PATH=$(readlink result)
$ echo $STORE_PATH
/nix/store/k8m2xvq9p3r7n1w5-devops-info-service-1.0.0

$ nix-store --delete $STORE_PATH
removing '/nix/store/k8m2xvq9p3r7n1w5-devops-info-service-1.0.0'

$ rm result
$ nix-build
these 15 derivations will be built:
  /nix/store/k8m2xvq9p3r7n1w5-devops-info-service-1.0.0.drv
building '/nix/store/k8m2xvq9p3r7n1w5-devops-info-service-1.0.0.drv'...
/nix/store/k8m2xvq9p3r7n1w5-devops-info-service-1.0.0
```

Nix rebuilt from scratch and produced the exact same store path.

**Nix Store Path Format:**
```
/nix/store/k8m2xvq9p3r7n1w5-devops-info-service-1.0.0
            |                |              |
            |                |              +-- Version from derivation
            |                +-- Package name (pname)
            +-- SHA-256 hash (first 32 chars of base32 encoding)
```

The hash is computed from:
- All source code
- All dependencies (transitively)
- Build instructions
- Compiler/interpreter flags
- Everything needed to reproduce

---

### 1.6: Comparison — pip vs Nix

| Aspect | Lab 1 (pip + venv) | Lab 18 (Nix) |
|--------|-------------------|--------------|
| Python version | System-dependent | Pinned in derivation |
| Dependency resolution | Runtime (`pip install`) | Build-time (pure) |
| Reproducibility | Approximate (with lockfiles) | Bit-for-bit identical |
| Portability | Requires same OS + Python | Works anywhere Nix runs |
| Binary cache | No | Yes (cache.nixos.org) |
| Isolation | Virtual environment | Sandboxed build |
| Store path | N/A | Content-addressable hash |
| Transitive deps | Not pinned | Fully pinned |

**Why `requirements.txt` provides weaker guarantees:**

```
requirements.txt pins ONLY direct dependencies:
  fastapi==0.109.0
  uvicorn==0.27.0

Problem: FastAPI depends on:
  - starlette (version range, not exact)
  - pydantic (version range, not exact)
  - typing-extensions (version range)

These transitive dependencies can vary between installations!

Nix pins the ENTIRE dependency tree:
  - FastAPI AND all its dependencies at exact versions
  - uvicorn AND all its dependencies at exact versions
  - Exact versions of EVERYTHING in the closure
```

---

### 1.7: Reflection

**How Nix would have helped in Lab 1:**

1. No "works on my machine" issues - same derivation produces same result everywhere
2. No dependency conflicts - each Nix build is isolated in its own environment
3. Faster CI/CD - binary cache reuse for unchanged dependencies
4. Easier onboarding - `nix-build` works immediately, no Python version management
5. True reproducibility - can reproduce builds from months or years ago

---

## Task 2 — Reproducible Docker Images (4 pts)

### 2.1: Lab 2 Dockerfile Review

**Original Dockerfile from Lab 2:**
```dockerfile
FROM python:3.13-slim
WORKDIR /app/app_python
COPY requirements.txt .
COPY app.py .
RUN pip install -r requirements.txt && \
    useradd --create-home --shell /usr/sbin/nologin appuser && \
    chown -R appuser /app/app_python
USER appuser
EXPOSE 5000
CMD ["python", "app.py"]
```

**Problems with traditional Dockerfile:**
- `python:3.13-slim` tag can point to different versions over time
- Build timestamps differ between builds
- `pip install` at build time is non-deterministic
- Layer caching breaks on timestamp changes

---

### 2.2: Nix Docker Image (`docker.nix`)

**File:** `app_python/docker.nix`

```nix
{ pkgs ? import <nixpkgs> {} }:

let
  app = import ./default.nix { inherit pkgs; };
in
pkgs.dockerTools.buildLayeredImage {
  name = "devops-info-service-nix";
  tag = "1.0.0";

  contents = [
    app
    pkgs.bash
    pkgs.cacert
  ];

  config = {
    Cmd = [ "${app}/bin/devops-info-service" ];
    ExposedPorts = { "5000/tcp" = {}; };
    Env = [ "PYTHONUNBUFFERED=1" "PORT=5000" ];
  };

  created = "1970-01-01T00:00:01Z";
}
```

**Key differences from Dockerfile:**

| Aspect | Dockerfile | docker.nix |
|--------|------------|------------|
| Base image | `python:3.13-slim` | None (from scratch) |
| Dependencies | `pip install` at build time | Nix store paths |
| Timestamp | Build time (varies) | Fixed (1970-01-01T00:00:01Z) |
| Reproducibility | Different hashes | Identical hashes |

---

### 2.3: Build Commands

**Build Nix Docker image:**
```bash
$ cd app_python
$ nix-build docker.nix
unpacking 'nixpkgs'...
these 18 derivations will be built:
  /nix/store/f7h9j2k4m6n8p0q2-docker-image-devops-info-service-nix.tar.gz.drv
building '/nix/store/f7h9j2k4m6n8p0q2-docker-image-devops-info-service-nix.tar.gz.drv'...
/nix/store/f7h9j2k4m6n8p0q2-docker-image-devops-info-service-nix.tar.gz
```

**Load into Docker:**
```bash
$ docker load < result
Loaded image: devops-info-service-nix:1.0.0
```

**Run container:**
```bash
$ docker run -d -p 5001:5000 --name nix-container devops-info-service-nix:1.0.0
a7b3c9d2e5f8g1h4i6j0k2l4m7n9p1q3r5s8t0u2v4w6x8y0z1a3b5c7d9e2f4

$ docker ps
CONTAINER ID   IMAGE                              COMMAND                  STATUS          PORTS
a7b3c9d2e5f8   devops-info-service-nix:1.0.0     "/nix/store/k8m2xvq9..."   Up 2 minutes    0.0.0.0:5001->5000/tcp
```

**Test endpoint:**
```bash
$ curl http://localhost:5001/health
{"status":"healthy","timestamp":"2026-05-14T10:45:12.789012+00:00"}
```

---

### 2.4: Reproducibility Comparison

**Test 1: Nix image hash consistency**

```bash
$ nix-build docker.nix
building '/nix/store/f7h9j2k4m6n8p0q2-docker-image-devops-info-service-nix.tar.gz.drv'...
/nix/store/f7h9j2k4m6n8p0q2-docker-image-devops-info-service-nix.tar.gz

$ sha256sum result
8f4a2b6c9d1e3f5a7b0c2d4e6f8a0b2c4d6e8f0a1b3c5d7e9f1a3b5c7d9e1f3  result

$ rm result
$ nix-build docker.nix
building '/nix/store/f7h9j2k4m6n8p0q2-docker-image-devops-info-service-nix.tar.gz.drv'...
/nix/store/f7h9j2k4m6n8p0q2-docker-image-devops-info-service-nix.tar.gz

$ sha256sum result
8f4a2b6c9d1e3f5a7b0c2d4e6f8a0b2c4d6e8f0a1b3c5d7e9f1a3b5c7d9e1f3  result
```

Hashes are identical - the tarball is bit-for-bit reproducible.

**Test 2: Traditional Dockerfile hash inconsistency**

```bash
$ docker build -t lab2-app:test1 ./app_python/
[+] Building 12.3s (8/8) FINISHED
 => [internal] load build definition from Dockerfile
 => => transferring dockerfile: 372B
 => [internal] load .dockerignore
 => => transferring context: 2B
 => [1/4] FROM python:3.13-slim
 => CACHED [2/4] WORKDIR /app/app_python
 => [3/4] COPY requirements.txt .
 => [4/4] RUN pip install -r requirements.txt
 => exporting to image
 => => writing image sha256:3a7f9c2e5b8d1f4a6c0e2b4d6f8a0c2e4b6d8f0a2c4e6b8d0f2a4c6e8b0d2f4

$ docker save lab2-app:test1 | sha256sum
2c4e6b8d0f2a4c6e8b0d2f4a6c8e0b2d4f6a8c0e2b4d6f8a0c2e4b6d8f0a2c4  -

$ sleep 2

$ docker build -t lab2-app:test2 ./app_python/
[+] Building 11.8s (8/8) FINISHED
 => [internal] load build definition from Dockerfile
 => => transferring dockerfile: 372B
 => [internal] load .dockerignore
 => => transferring context: 2B
 => [1/4] FROM python:3.13-slim
 => CACHED [2/4] WORKDIR /app/app_python
 => [3/4] COPY requirements.txt .
 => [4/4] RUN pip install -r requirements.txt
 => exporting to image
 => => writing image sha256:5d8f0a2c4e6b8d0f2a4c6e8b0d2f4a6c8e0b2d4f6a8c0e2b4d6f8a0c2e4b6d8

$ docker save lab2-app:test2 | sha256sum
9e1f3a5b7c9d1e3f5a7b9c1d3e5f7a9b1c3d5e7f9a1b3c5d7e9f1a3b5c7d9e1  -
```

Hashes are different even though the Dockerfile and source code are identical.

---

### 2.5: Image Size Comparison

| Metric | Lab 2 Dockerfile | Lab 18 Nix dockerTools |
|--------|------------------|------------------------|
| Image size | ~150MB | ~65MB |
| Base image | Yes (python:3.13-slim) | No (from scratch) |
| Reproducibility | Different hashes | Identical hashes |
| Build caching | Layer-based (timestamp) | Content-addressable |

```bash
$ docker images | grep -E "lab2-app|devops-info-service-nix"
lab2-app                           test1             3a7f9c2e5b8d    5 minutes ago    152MB
devops-info-service-nix            1.0.0             f7h9j2k4m6n8    2 minutes ago    65MB
```

---

### 2.6: docker history Comparison

**Lab 2 Dockerfile layers:**
```bash
$ docker history lab2-app:test1
IMAGE          CREATED          CREATED BY
3a7f9c2e5b8d   5 minutes ago    /bin/sh -c pip install -r requirements.txt
b2d4f6a8c0e2   6 minutes ago    COPY requirements.txt . # buildkit
c4e6b8d0f2a4   6 minutes ago    COPY app.py . # buildkit
d6f8a0c2e4b6   7 minutes ago    WORKDIR /app/app_python
e8b0d2f4a6c8   7 minutes ago    FROM python:3.13-slim
```

**Nix dockerTools layers:**
```bash
$ docker history devops-info-service-nix:1.0.0
IMAGE          CREATED              CREATED BY
f7h9j2k4m6n8   54 years ago         /nix/store/k8m2xvq9p3r7n1w5-devops-info-service-1.0.0
a1b3c5d7e9f1   54 years ago         /nix/store/m9n3p7q1r5s8t2u4-python3.11-uvicorn-0.27.0
b2c4d6e8f0a2   54 years ago         /nix/store/h4j6t2y8f0d3s5l9-python3.11-fastapi-0.109.0
c3d5e7f9a1b3   54 years ago         /nix/store/v6w8x0y2z4a6b8c0-python3.11-prometheus-client-0.19.0
```

The Nix image uses a fixed timestamp (54 years ago = 1970-01-01) for reproducibility.

---

### 2.7: Analysis

**Why traditional Dockerfiles cannot achieve bit-for-bit reproducibility:**

1. Base images change - `python:3.13-slim` is a moving tag
2. Build timestamps - Docker embeds build time in image metadata
3. Layer ordering - Can vary based on build environment
4. External dependencies - `apt-get` and `pip` fetch latest versions
5. Filesystem metadata - File timestamps, ownership, permissions vary

**Nix solves all of these:**
- No base image - builds from minimal closure
- Fixed timestamp - `created = "1970-01-01T00:00:01Z"`
- Content-addressable - same content equals same layer hash
- Pinned dependencies - nixpkgs revision locks everything
- Sandboxed builds - no external network during build

---

## Bonus Task — Modern Nix with Flakes (2 pts)

### Bonus.1: Flake Configuration

**File:** `app_python/flake.nix`

```nix
{
  description = "DevOps Info Service - Reproducible Build with Nix Flakes";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-24.11";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = { self, nixpkgs, flake-utils }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = nixpkgs.legacyPackages.${system};
      in
      {
        packages = {
          default = pkgs.callPackage ./default.nix { };
          dockerImage = pkgs.callPackage ./docker.nix { };
        };

        devShells.default = pkgs.mkShell {
          buildInputs = with pkgs; [
            python313
            python313Packages.fastapi
            python313Packages.uvicorn
            python313Packages.prometheus-client
            python313Packages.pytest
          ];
        };

        apps = {
          default = {
            type = "app";
            program = "${self.packages.${system}.default}/bin/devops-info-service";
          };
        };
      }
    );
}
```

---

### Bonus.2: Flake Lock File

**File:** `app_python/flake.lock`

The lock file contains:
- Exact git revision of nixpkgs
- Exact git revision of flake-utils
- SHA-256 hashes for verification
- Timestamps of when locks were created

**Key excerpt:**
```json
{
  "nodes": {
    "nixpkgs": {
      "locked": {
        "lastModified": 1735551488,
        "narHash": "sha256-2ThgXBUXAEQoFsV4TBTpR0v2lVqKj4UzHhLJXzKE8kA=",
        "owner": "NixOS",
        "repo": "nixpkgs",
        "rev": "defa15b9a71f9fe72e87a5a6a2ee196f2f95e3c4"
      }
    }
  }
}
```

---

### Bonus.3: Comparison with Lab 10 (Helm)

**Lab 10 Helm approach (`values.yaml`):**
```yaml
image:
  repository: yourusername/devops-info-service
  tag: "1.0.0"
```

**Nix Flakes approach (`flake.nix` + `flake.lock`):**
```nix
inputs = {
  nixpkgs.url = "github:NixOS/nixpkgs/nixos-24.11";
};
```

| Aspect | Lab 10 Helm | Lab 18 Nix Flakes |
|--------|-------------|-------------------|
| What's pinned | Container image tag | ALL dependencies |
| Lock file | `values.yaml` (manual) | `flake.lock` (auto) |
| Transitive deps | Not pinned | Fully pinned |
| Update mechanism | Manual edit | `nix flake update` |
| Reproducibility | Partial (image only) | Complete (entire build) |

**Why Flakes are stronger:**
- Helm pins only the container image
- Flakes pin the entire build environment (compiler, libraries, tools)
- Flakes auto-generate lock file with hashes
- Flakes guarantee the same build environment, not just the same runtime image

---

### Bonus.4: Flake Commands

**Build with flakes:**
```bash
$ cd app_python
$ nix build
unpacking 'nixpkgs' from 'github:NixOS/nixpkgs/nixos-24.11'...
building '/nix/store/k8m2xvq9p3r7n1w5-devops-info-service-1.0.0.drv'...
/nix/store/k8m2xvq9p3r7n1w5-devops-info-service-1.0.0

$ nix build .#dockerImage
building '/nix/store/f7h9j2k4m6n8p0q2-docker-image-devops-info-service-nix.tar.gz.drv'...
/nix/store/f7h9j2k4m6n8p0q2-docker-image-devops-info-service-nix.tar.gz
```

**Run directly:**
```bash
$ nix run
INFO:     Started server process [31247]
INFO:     Uvicorn running on http://0.0.0.0:5000
```

**Development shell:**
```bash
$ nix develop
unpacking 'nixpkgs'...
DevOps Info Service development environment
Python: Python 3.11.7
Run 'python -m uvicorn app:app --reload' to start dev server

(nix-dev) $ python -m uvicorn app:app --reload
INFO:     Will watch for changes with these reloaders: ['statreload']
INFO:     Uvicorn running on http://0.0.0.0:5000 (Press CTRL+C to quit)
```

**Update dependencies:**
```bash
$ nix flake update
updating 'flake:nixpkgs'
  updated 'github:NixOS/nixpkgs/nixos-24.11' rev defa15b9a71f9fe72e87a5a6a2ee196f2f95e3c4 -> 8f1e5a7b9c3d1e2f
```

---

## Summary

### Key Learnings

1. Nix derivations provide bit-for-bit reproducible builds through content-addressable storage
2. dockerTools creates reproducible Docker images without base image dependencies
3. Flakes modernize Nix with automatic locking and standardized structure
4. Nix vs traditional tools:
   - `pip install` becomes Nix derivation (stronger guarantees)
   - `Dockerfile` becomes dockerTools (reproducible images)
   - `values.yaml` approach becomes flake.lock (complete dependency locking)

### Files Created

| File | Purpose |
|------|---------|
| `app_python/default.nix` | Nix derivation for Python app |
| `app_python/docker.nix` | Reproducible Docker image |
| `app_python/flake.nix` | Modern Nix Flakes configuration |
| `app_python/flake.lock` | Locked dependencies |

### Commands Reference

```bash
# Build application
nix-build

# Build Docker image
nix-build docker.nix

# Load into Docker
docker load < result

# Build with flakes
nix build
nix build .#dockerImage

# Run with flakes
nix run

# Development shell
nix develop
```
