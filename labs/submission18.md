# Lab 18 Submission - Reproducible Builds with Nix

## Environment Notes

The Lab 18 work lives in `labs/lab18/app_python`

This lab was completed on macOS Apple Silicon with Determinate Nix installed. That host choice matters for Task 2: the Nix-built application closure is Darwin-native, while Docker Desktop runs Linux containers.

## Task 1 - Reproducible Python App

### 1.1 Installation Steps

Recommended install command:

```bash
curl --proto '=https' --tlsv1.2 -sSf -L https://install.determinate.systems/nix | sh -s -- install
```

Actual verification:

```text
nix (Determinate Nix 3.17.3) 2.33.3
Hello, world!
```

Commands used:

```bash
nix --version
nix run nixpkgs#hello
```

### 1.2 Lab 1 Application Prepared for Nix

The Lab 1 Python service was copied into:

- `labs/lab18/app_python/app.py`
- `labs/lab18/app_python/requirements.txt`
- `labs/lab18/app_python/tests/test_app.py`

The real app in this repository uses:
- Flask
- `prometheus-client`
- `python-json-logger`
- port `8000`

### 1.3 `default.nix`

File: `labs/lab18/app_python/default.nix`

```nix
{ pkgs ? import <nixpkgs> {} }:

let
  python = pkgs.python3;
  runtimeDeps = with python.pkgs; [
    flask
    prometheus-client
    python-json-logger
  ];
in
python.pkgs.buildPythonApplication {
  pname = "devops-info-service";
  version = "1.0.0";
  format = "other";
  src = pkgs.lib.cleanSource ./.;

  propagatedBuildInputs = runtimeDeps;

  nativeBuildInputs = [ pkgs.makeWrapper ];

  installPhase = ''
    runHook preInstall

    mkdir -p $out/bin $out/share/devops-info-service
    cp app.py $out/share/devops-info-service/app.py

    makeWrapper ${python}/bin/python $out/bin/devops-info-service \
      --add-flags "$out/share/devops-info-service/app.py" \
      --prefix PYTHONPATH : "${python.pkgs.makePythonPath runtimeDeps}" \
      --set PYTHONDONTWRITEBYTECODE 1 \
      --set PYTHONUNBUFFERED 1

    runHook postInstall
  '';

  checkPhase = ''
    runHook preCheck
    export PYTHONPATH=$PWD:${python.pkgs.makePythonPath runtimeDeps}
    ${python.pkgs.pytest}/bin/pytest tests -q
    runHook postCheck
  '';

  nativeCheckInputs = with python.pkgs; [
    pytest
  ];

  doCheck = true;
}
```

### 1.4 Explanation of Fields

| Field | Purpose |
| --- | --- |
| `pkgs ? import <nixpkgs> {}` | Imports the active `nixpkgs` set |
| `python = pkgs.python3` | Uses Nix-managed Python |
| `runtimeDeps` | Collects the real runtime Python dependencies |
| `buildPythonApplication` | Builds an executable Python app |
| `pname` / `version` | Defines the package identity |
| `format = "other"` | Used because this app has no `setup.py` / `pyproject.toml` build backend |
| `src = pkgs.lib.cleanSource ./.` | Builds from the local source while filtering noise |
| `propagatedBuildInputs` | Declares runtime Python packages |
| `nativeBuildInputs = [ pkgs.makeWrapper ]` | Provides the wrapper tool for the launcher |
| `installPhase` | Copies the source and creates the runnable wrapper |
| `--prefix PYTHONPATH` | Makes the built executable find Flask and the other Python deps |
| `checkPhase` | Runs the test suite as part of the Nix build |
| `nativeCheckInputs` | Adds `pytest` to the check environment |
| `doCheck = true` | Enforces tests during the derivation build |

### 1.5 Reproducibility Proof

Commands used:

```bash
nix-build >/dev/null
FIRST=$(readlink result)
rm result
nix-build >/dev/null
SECOND=$(readlink result)
nix-hash --type sha256 result
```

Actual output:

```text
FIRST=/nix/store/6jilb1b86mxx3lszvsnrni2g3vs7prl6-devops-info-service-1.0.0
SECOND=/nix/store/6jilb1b86mxx3lszvsnrni2g3vs7prl6-devops-info-service-1.0.0
e41ca1d8592550d06a49551c8d3bb7b758d6b385d3e8a5abdb973800a100daa8
```

Observation:
- Two separate `nix-build` runs produced the exact same Nix store path.
- The output hash remained stable.
- This is the reproducibility guarantee the lab is asking for.

I also attempted the explicit delete-and-rebuild sequence with `nix-store --delete`, but after building the Docker image the app output had active references from the image derivations in `/nix/store`, so Nix refused to delete it. That is expected safety behavior.

### 1.6 Runtime Verification

Command used:

```bash
APP=$(nix-build)
"$APP/bin/devops-info-service"
```

Actual health response:

```json
{"status":"healthy","timestamp":"2026-04-19T14:34:14.039708+00:00","uptime_seconds":63}
```

This confirms the Nix-built executable actually runs correctly on the host machine.

### 1.7 Comparison - Lab 1 vs Nix

Traditional Lab 1 workflow:

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python app.py
```

| Aspect | Lab 1 (`pip` + `venv`) | Lab 18 (Nix) |
| --- | --- | --- |
| Python version | Host-dependent | Provided by Nix |
| Direct dependencies | `requirements.txt` | In derivation |
| Transitive dependencies | Can drift | Locked by Nix inputs |
| Build isolation | Virtualenv | Sandboxed derivation |
| Binary caching | No | Yes |
| Output identity | No content address | `/nix/store/<hash>-name-version` |
| Reproducibility | Approximate | Strong and repeatable |

Why `requirements.txt` gives weaker guarantees than Nix:
- It usually pins only top-level packages.
- It does not fully lock transitive dependencies.
- The Python interpreter itself is outside the file unless managed separately.
- Install results can vary by platform, wheel availability, and index state.
- Nix captures the entire dependency graph plus the build instructions.

### 1.8 Nix Store Path Format

Example from this lab:

```text
/nix/store/6jilb1b86mxx3lszvsnrni2g3vs7prl6-devops-info-service-1.0.0
```

Meaning:
- `/nix/store` is the immutable Nix store
- `6jilb1b86mxx3lszvsnrni2g3vs7prl6` is the content-derived hash
- `devops-info-service` is the package name
- `1.0.0` is the package version

If inputs change, Nix creates a different store path instead of mutating the old one.

### 1.9 Reflection

If Nix had been used from the start in Lab 1:
- local and CI builds would have matched much more closely
- Python version drift would have been eliminated
- reinstalling the project later would be predictable
- debugging environment-specific issues would be easier

## Task 2 - Reproducible Docker Images

### 2.1 Traditional Dockerfile from Lab 2

File: `app_python/Dockerfile`

```dockerfile
FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN useradd --uid 1000 --create-home --shell /bin/bash appuser

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN mkdir -p /data && chown -R appuser:appuser /app /data

USER appuser

EXPOSE 8000

CMD ["python", "app.py"]
```

This works, but it is not bit-for-bit reproducible because:
- `python:3.13-slim` is an external mutable base image reference
- image metadata and tarball layout can vary
- `pip install` happens at build time
- Docker rebuilds can produce different exported tarball hashes

### 2.2 `docker.nix`

File: `labs/lab18/app_python/docker.nix`

```nix
{ pkgs ? import <nixpkgs> {} }:

let
  app = import ./default.nix { inherit pkgs; };
in
pkgs.dockerTools.buildLayeredImage {
  name = "devops-info-service-nix";
  tag = "1.0.0";

  contents = [ app ];

  config = {
    Cmd = [ "${app}/bin/devops-info-service" ];
    Env = [
      "HOST=0.0.0.0"
      "PORT=8000"
      "PYTHONDONTWRITEBYTECODE=1"
      "PYTHONUNBUFFERED=1"
    ];
    ExposedPorts = {
      "8000/tcp" = {};
    };
    WorkingDir = "/";
  };

  created = "1970-01-01T00:00:01Z";
}
```

### 2.3 Reproducible Image Hash Proof

Commands used:

```bash
rm -f result
nix-build docker.nix >/dev/null
shasum -a 256 result
rm result
nix-build docker.nix >/dev/null
shasum -a 256 result
```

Actual output:

```text
2bd075b2119b6fcdb55bf195342957926937063ccfd6265a6042f9cf8e656c6a  result
2bd075b2119b6fcdb55bf195342957926937063ccfd6265a6042f9cf8e656c6a  result
```

Observation:
- The Nix-built image tarball hash was identical across rebuilds.
- This demonstrates bit-for-bit reproducible image artifact generation.

### 2.4 Traditional Docker Comparison

Commands used:

```bash
docker build -t lab2-app:test1 ./app_python
docker save lab2-app:test1 | shasum -a 256
sleep 2
docker build -t lab2-app:test2 ./app_python
docker save lab2-app:test2 | shasum -a 256
```

Actual output:

```text
lab2-app:test1 docker save hash: b143420b98c2527acbbfe28bdc5446472c572d736f8b8a2a536a869cf1cbcf1b
lab2-app:test2 docker save hash: 8dad74f8fdf15f05997d4589f0ee74ad22a15b72d21ddd0d3d19ab5f4cd22673
```

Observation:
- The traditional Docker image tarballs differed even though the build inputs were effectively the same.
- This is the non-reproducibility problem Nix avoids.

Traditional Docker build also succeeded normally:

```text
Successfully built image: sha256:ca65584a615621e4192f5665262e5e428fa596d853e71f9bbe0dc07c0af675c4
Tag: lab18-traditional-check
```

### 2.5 Side-by-Side Comparison

| Aspect | Lab 2 Dockerfile | Lab 18 `dockerTools` |
| --- | --- | --- |
| Base image | `python:3.13-slim` | No mutable base image tag |
| Dependency installation | `pip install` at image build time | Reuses the Nix-built app closure |
| Timestamps | Drift in exported artifacts | Fixed with `created` |
| Rebuild result | Different tarball hashes | Identical tarball hashes |
| Caching model | Layer-based | Content-addressable |
| Auditability | Depends on Docker/base image state | Derived from Nix inputs |

### 2.6 Docker Runtime Result on This Machine

The image loaded successfully:

```text
Loaded image: devops-info-service-nix:1.0.0
```

But the container did not start successfully on this macOS machine:

```text
exec /nix/store/6jilb1b86mxx3lszvsnrni2g3vs7prl6-devops-info-service-1.0.0/bin/devops-info-service: exec format error
```

Why this happened:
- the app derivation was built natively for Darwin/macOS
- `dockerTools` produced a Linux container artifact
- Docker Desktop runs Linux containers
- the wrapped executable inside the image referenced Darwin-built runtime paths, which are not executable in the Linux container runtime

So on this host:
- the Docker artifact build was reproducible
- the loaded image existed correctly
- but the container was not runnable without a Linux-targeted build environment

This is an important DevOps lesson in itself: reproducible artifacts still need the correct target platform.

### 2.7 Analysis

Traditional Dockerfiles usually cannot guarantee bit-for-bit reproducibility because container metadata, upstream base images, and package manager behavior introduce changing inputs. Nix improves this by resolving the dependency graph first and then building the final image from immutable store paths.

Practical scenarios where this matters:
- CI/CD pipelines that must reproduce production artifacts exactly
- security audits that need trustworthy provenance
- rollbacks that should restore the same software, not just the same tag
- debugging situations where environment drift causes inconsistent behavior

### 2.8 Reflection

If I were redoing Lab 2 with Nix, I would:
- build the app derivation first with Nix
- generate the image from that derivation
- use Linux builders for Linux container outputs
- deploy by immutable image artifact hash rather than mutable tags

## Verification Performed

Virtualenv test verification:

```text
7 passed, 1 warning in 0.31s
```

Nix derivation test verification:

```text
7 passed, 1 warning in 0.26s
```

The warning came from `python-json-logger` deprecation messaging, not from app failures.

## Final Reflection

This lab showed two complementary things very clearly:

1. Nix gave a truly repeatable application build on this machine.
The app derivation produced the same store path and hash across rebuilds, and the packaged binary ran successfully.

2. Reproducibility does not remove platform constraints.
The `dockerTools` artifact was reproducible, but because the work was done on macOS with a Darwin-native app closure, that artifact was not directly runnable as a Linux container in Docker Desktop. That is a valuable real-world lesson about target platforms, builders, and deployment environments.
