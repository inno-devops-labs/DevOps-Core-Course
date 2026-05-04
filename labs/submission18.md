# Lab 18 — Reproducible Builds with Nix

**Student:** Ostapenko Artem  
**Branch:** `feature/lab18`  
**Main deliverables:**  
- `labs/lab18/app_python/`
- `labs/lab18/app_python/default.nix`
- `labs/lab18/app_python/docker.nix`
- `labs/submission18.md`

---

## Overview

The goal of this lab was to learn how Nix can provide reproducible builds and compare it with the traditional tools used in previous labs.

This lab revisits:

- Lab 1: Python DevOps Info Service built with `pip` and `requirements.txt`
- Lab 2: Docker containerization using a traditional `Dockerfile`

In Lab 18, the same Python application was rebuilt with Nix and then containerized using Nix `dockerTools`.

---

# Task 1 — Build Reproducible Python App

## 1.1 Nix Installation and Verification

Nix was installed using the Determinate Systems installer.

Verification command:

```bash
nix --version
```

Output:

```text
nix (Determinate Nix 3.19.0) 2.34.6
```

Basic Nix test command:

```bash
nix run nixpkgs#hello
```

Output:

```text
Hello, world!
```

This confirms that Nix is installed correctly and can fetch and run packages from nixpkgs.

---

## 1.2 Application Preparation

The Python application from previous labs was copied into the Lab 18 directory:

```bash
mkdir -p labs/lab18/app_python
cp -r app_python/* labs/lab18/app_python/
cd labs/lab18/app_python
```

The copied application contains:

```text
Dockerfile
README.md
app.py
requirements.txt
docker-compose.yml
docs/
tests/
data/
```

The application is a Flask-based DevOps Info Service with endpoints such as:

- `/`
- `/health`
- `/metrics`
- `/visits`

---

## 1.3 Nix Derivation

The following `default.nix` was created in `labs/lab18/app_python/`.

```nix
{ pkgs ? import <nixpkgs> {} }:

pkgs.python3Packages.buildPythonApplication {
  pname = "devops-info-service";
  version = "1.0.0";
  src = ./.;

  format = "other";

  propagatedBuildInputs = with pkgs.python3Packages; [
    flask
    prometheus-client
  ];

  nativeBuildInputs = [ pkgs.makeWrapper ];

  installPhase = ''
    mkdir -p $out/bin
    cp app.py $out/bin/devops-info-service
    chmod +x $out/bin/devops-info-service

    wrapProgram $out/bin/devops-info-service \
      --prefix PYTHONPATH : "$PYTHONPATH"
  '';
}
```

### Explanation of fields

| Field | Explanation |
|---|---|
| `pname` | Package name used in the Nix store path |
| `version` | Application version |
| `src = ./.` | Uses the current directory as source |
| `format = "other"` | Used because the app does not have a standard Python package structure with `setup.py` or `pyproject.toml` |
| `propagatedBuildInputs` | Python runtime dependencies required by the app |
| `nativeBuildInputs` | Build-time tools, including `makeWrapper` |
| `installPhase` | Copies the app into `$out/bin` and wraps it with the correct Python environment |

The application required:

```nix
flask
prometheus-client
```

because the app imports Flask and Prometheus client metrics.

---

## 1.4 Fixes Required During Nix Build

### Missing executable permission

The first build failed because the copied `app.py` was not executable.

Fix:

```nix
chmod +x $out/bin/devops-info-service
```

### Missing Python shebang

The app initially executed as a shell script instead of Python.

Fix added to `app.py`:

```python
#!/usr/bin/env python3
```

After this, Nix correctly rewrote the interpreter path to the pinned Python interpreter from the Nix store.

### Missing dependency

The app initially failed with:

```text
ModuleNotFoundError: No module named 'prometheus_client'
```

Fix:

```nix
propagatedBuildInputs = with pkgs.python3Packages; [
  flask
  prometheus-client
];
```

### Read-only Nix store

The application originally tried to write runtime data into the Nix store path, which is read-only.

Error:

```text
PermissionError: [Errno 13] Permission denied
```

Fix during execution:

```bash
mkdir -p /tmp/devops-info-service-data
DATA_DIR=/tmp/devops-info-service-data ./result/bin/devops-info-service
```

This keeps the immutable build artifact in `/nix/store` while placing mutable runtime data in `/tmp`.

---

## 1.5 Nix Build Execution

Build command:

```bash
nix-build
```

Successful output included:

```text
/nix/store/0i2ip0ghbp4vrg4k7xslj0r9rzkvk8iw-devops-info-service-1.0.0
```

After cleanup and final rebuilds, the stable reproducible store path was:

```text
/nix/store/5qmkaxmbh1q9...-devops-info-service-1.0.0
```

The shortened hash is shown here for readability, but the repeated builds produced the same full store path locally.

---

## 1.6 Running the Nix-built Application

Run command:

```bash
DATA_DIR=/tmp/devops-info-service-data ./result/bin/devops-info-service
```

The Flask app started successfully:

```text
Starting app on 0.0.0.0:5000
Running on http://127.0.0.1:5000
```

Health endpoint test:

```bash
curl http://localhost:5000/health
```

Output:

```json
{
  "status": "healthy",
  "timestamp": "2026-05-04T06:04:30.373412+00:00",
  "uptime_seconds": 14
}
```

Main endpoint test:

```bash
curl http://localhost:5000/
```

Output included:

```json
{
  "service": {
    "description": "DevOps course info service",
    "framework": "Flask",
    "name": "devops-info-service",
    "version": "1.0.0"
  },
  "system": {
    "architecture": "arm64",
    "platform": "Darwin",
    "python_version": "3.13.12"
  },
  "visits": 2
}
```

This proves that the Nix-built application runs correctly.

---

## 1.7 Reproducibility Proof

The build was repeated multiple times.

Commands:

```bash
rm -rf venv __pycache__ result
find . -name "__pycache__" -type d -prune -exec rm -rf {} +
nix-build
readlink result

rm result
nix-build
readlink result
```

Observed result:

```text
/nix/store/5qmkaxmbh1q9...-devops-info-service-1.0.0
/nix/store/5qmkaxmbh1q9...-devops-info-service-1.0.0
/nix/store/5qmkaxmbh1q9...-devops-info-service-1.0.0
/nix/store/5qmkaxmbh1q9...-devops-info-service-1.0.0
```

The same store path appeared repeatedly.

This proves that, with the same declared inputs, Nix produces the same output path.

---

## 1.8 Nix Store Path Explanation

A Nix store path has this structure:

```text
/nix/store/<hash>-<package-name>-<version>
```

Example:

```text
/nix/store/5qmkaxmbh1q9...-devops-info-service-1.0.0
```

| Part | Meaning |
|---|---|
| `/nix/store` | Immutable global Nix store |
| `5qmkaxmbh1q9...` | Hash derived from build inputs |
| `devops-info-service` | Package name |
| `1.0.0` | Package version |

The hash is based on the declared build inputs, including:

- source code
- dependencies
- Python interpreter
- Nix build instructions
- build tools

If the inputs do not change, the output path does not change.

---

## 1.9 Lab 1 pip/venv vs Lab 18 Nix

| Aspect | Lab 1: pip + venv | Lab 18: Nix |
|---|---|---|
| Python version | Depends on system Python | Pinned by Nix |
| Dependencies | Installed at runtime by pip | Declared in Nix derivation |
| Transitive dependencies | Resolved by pip | Fixed through nixpkgs |
| Reproducibility | Approximate | Deterministic |
| Environment isolation | Virtual environment | Nix sandbox and store |
| Output identity | No content-addressed output | Store path includes hash |
| Binary cache | No | Yes |
| Long-term stability | Can drift | Stable if inputs are pinned |

### Why `requirements.txt` is weaker than Nix

A `requirements.txt` file can pin direct Python dependencies, but it does not fully describe the entire build environment.

It does not fully control:

- system Python version
- OS-level libraries
- compiler/toolchain versions
- environment variables
- build tools
- timestamps
- all transitive dependencies unless strictly locked with hashes

Nix describes the build more completely. It produces an immutable output in the Nix store and gives every build result a hash-based identity.

---

## 1.10 Reflection for Task 1

If Nix had been used from Lab 1, the app would have had:

- a pinned Python interpreter
- reproducible dependency resolution
- a build artifact with a stable store path
- less dependence on local virtual environments
- easier debugging of environment differences

The main practical benefit is that another developer could build the same app from the same Nix expression and obtain the same result.

---

# Task 2 — Reproducible Docker Images with Nix

## 2.1 Traditional Dockerfile Review

The original Dockerfile from Lab 2 uses a traditional Docker-based workflow:

```dockerfile
# syntax=docker/dockerfile:1

FROM python:3.13.1-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

RUN groupadd --system app && useradd --system --gid app --uid 10001 --create-home app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY --chown=app:app app.py .

RUN mkdir -p /data && chown -R app:app /data

EXPOSE 5000

USER app

ENV HOST=0.0.0.0 \
    PORT=5000 \
    DATA_DIR=/data

CMD ["python", "app.py"]
```

This Dockerfile is good from a containerization perspective because it:

- uses a slim Python base image
- creates a non-root user
- installs dependencies
- exposes port 5000
- runs the Flask app

However, it is not fully reproducible by default.

---

## 2.2 Nix Docker Image Definition

The following `docker.nix` was created in `labs/lab18/app_python/`.

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
    Env = [ "DATA_DIR=/tmp/devops-info-service-data" ];
    ExposedPorts = {
      "5000/tcp" = {};
    };
  };

  created = "1970-01-01T00:00:01Z";
}
```

### Explanation of fields

| Field | Explanation |
|---|---|
| `app = import ./default.nix` | Reuses the reproducible Nix-built app |
| `buildLayeredImage` | Creates a Docker image from Nix store paths |
| `name` | Docker image name |
| `tag` | Docker image tag |
| `contents` | Adds the Nix application closure into the image |
| `Cmd` | Default command for the container |
| `Env` | Sets writable runtime data directory |
| `ExposedPorts` | Documents exposed container port |
| `created` | Fixed timestamp for reproducibility |

The fixed `created` timestamp is important. If `created = "now"` were used, each build would include a new timestamp and the image would not be reproducible.

---

## 2.3 Nix Docker Image Reproducibility

The Nix Docker image was built twice.

Commands:

```bash
rm -f result
nix-build docker.nix
shasum -a 256 result

rm -f result
nix-build docker.nix
shasum -a 256 result
```

Output:

```text
72dbcc11fd3429ca91d674696b8721f0ba11da8e6e64bd3fa0768e49a68f37b2  result
72dbcc11fd3429ca91d674696b8721f0ba11da8e6e64bd3fa0768e49a68f37b2  result
```

The hashes are identical.

This proves that the Nix-built Docker tarball is reproducible.

---

## 2.4 Traditional Dockerfile Reproducibility Test

The traditional Dockerfile image was built twice.

Commands:

```bash
docker build -t lab2-app:test1 ./app_python
docker save lab2-app:test1 | shasum -a 256

sleep 2

docker build -t lab2-app:test2 ./app_python
docker save lab2-app:test2 | shasum -a 256
```

Output:

```text
f69c5f62a04e25971bc151a23d547b6d26185a6420ffe7e5c9338a008d6df4f0  -
5445ea20df9b548c99b6e42b2a245d05ab7600f9baaca0c30e707206c99cbd6a  -
```

The hashes are different.

This proves that the traditional Docker build is not bit-for-bit reproducible by default, even though the source code and Dockerfile did not intentionally change.

---

## 2.5 Loading and Running the Nix Docker Image

The first local macOS-generated Nix Docker image produced a runtime problem:

```text
exec format error
```

This happened because the initial image included a platform-specific closure from the macOS/Darwin build environment, while Docker containers expect Linux executables.

To solve this properly, the Nix Docker image was rebuilt inside a Linux Nix container:

```bash
docker run --rm \
  -v "$PWD":/workspace \
  -w /workspace/labs/lab18/app_python \
  nixos/nix:latest \
  sh -lc '
    nix-build docker.nix
    sha256sum result
    cp -L result devops-info-service-nix-linux.tar.gz
  '
```

Then the image was loaded:

```bash
docker load < labs/lab18/app_python/devops-info-service-nix-linux.tar.gz
```

Output:

```text
Loaded image: devops-info-service-nix:1.0.0
```

The container was started:

```bash
docker run -d -p 5001:5000 --name nix-container devops-info-service-nix:1.0.0
```

Container status:

```bash
docker ps | grep -E "nix-container|lab2-container" || true
```

Output:

```text
1c1b1bfdc7b1   devops-info-service-nix:1.0.0   "/nix/store/fah6nmgb…"   Up 2 minutes   0.0.0.0:5001->5000/tcp   nix-container
```

Health check:

```bash
curl http://localhost:5001/health
```

Output:

```json
{
  "status": "healthy",
  "timestamp": "2026-05-04T06:34:34.488480+00:00",
  "uptime_seconds": 71
}
```

This proves that the Nix-built Docker image works when built for the correct Linux container platform.

---

## 2.6 Image Size Comparison

Command:

```bash
docker images | grep -E "lab2-app|devops-info-service-nix"
```

Output:

```text
lab2-app                    test1   dfdc3c4780a2   271MB
lab2-app                    test2   5777c982f7b5   271MB
devops-info-service-nix     1.0.0   24dc4ea1a438   423MB
```

| Image | Size |
|---|---:|
| Traditional Dockerfile image | 271MB |
| Nix dockerTools image | 423MB |

The Nix image is larger in this build because it includes the dependency closure required by the Nix-built application. The Dockerfile image is smaller because it relies on the shared `python:3.13.1-slim` base image structure.

---

## 2.7 Docker History Comparison

### Traditional Docker image

Command:

```bash
docker history lab2-app:test1
```

Output excerpt:

```text
IMAGE          CREATED              CREATED BY                                      SIZE
dfdc3c4780a2   About a minute ago   CMD ["python" "app.py"]                         0B
<missing>      About a minute ago   ENV HOST=0.0.0.0 PORT=5000 DATA_DIR=/data       0B
<missing>      About a minute ago   USER app                                        0B
<missing>      About a minute ago   EXPOSE [5000/tcp]                               0B
<missing>      About a minute ago   RUN mkdir -p /data && chown -R app:app /data    8.19kB
<missing>      About a minute ago   COPY app.py                                     16.4kB
<missing>      About a minute ago   RUN pip install --no-cache-dir -r requirements  47.3MB
<missing>      15 months ago        python:3.13.1-slim base layers                  ...
```

Observation:

- Docker history contains human time-based timestamps such as `About a minute ago`.
- The image depends on a base image.
- The build uses `pip install` at image build time.
- Rebuilding can change metadata and final image hash.

### Nix Docker image

Command:

```bash
docker history devops-info-service-nix:1.0.0
```

Output excerpt:

```text
IMAGE          CREATED   CREATED BY   SIZE      COMMENT
24dc4ea1a438   N/A                    28.7kB    store paths: [...]
<missing>      N/A                    49.2kB    store paths: [...]
<missing>      N/A                    122MB     store paths: ['/nix/store/...python3-3.13.12']
<missing>      N/A                    1.35MB    store paths: ['/nix/store/...flask-3.1.2']
<missing>      N/A                    1.04MB    store paths: ['/nix/store/...prometheus-client-0.24.1']
```

Observation:

- Nix image layers are based on Nix store paths.
- Layers correspond to content-addressed dependencies.
- The image uses a fixed timestamp from `docker.nix`.
- The final image is reproducible.

---

## 2.8 Lab 2 Dockerfile vs Lab 18 Nix dockerTools

| Aspect | Lab 2 Traditional Dockerfile | Lab 18 Nix dockerTools |
|---|---|---|
| Base image | `python:3.13.1-slim` | No normal base image; built from Nix store paths |
| Dependency installation | `pip install` during Docker build | Dependencies declared in Nix derivation |
| Timestamp behavior | Build metadata changes | Fixed timestamp |
| Hash reproducibility | Different hashes | Identical hashes |
| Image size | 271MB | 423MB |
| Runtime platform | Linux container | Requires Linux-targeted Nix build |
| Dependency closure | Implicit through base image and pip | Explicit through Nix store closure |
| Auditability | Medium | High |
| Rebuild determinism | Not guaranteed | Guaranteed for same inputs |

---

## 2.9 Why Traditional Dockerfiles Are Not Bit-for-Bit Reproducible

Traditional Dockerfiles often fail to be bit-for-bit reproducible because:

1. Build metadata includes timestamps.
2. Base image tags can change over time.
3. Package installation can depend on external repositories.
4. `pip install` resolves dependencies during the build.
5. BuildKit can create different attestation or manifest metadata.
6. The final saved Docker tar can include metadata that changes between builds.

In this lab, the traditional Dockerfile produced different saved-image hashes:

```text
f69c5f62a04e25971bc151a23d547b6d26185a6420ffe7e5c9338a008d6df4f0
5445ea20df9b548c99b6e42b2a245d05ab7600f9baaca0c30e707206c99cbd6a
```

This happened even though the same Dockerfile and source code were used.

---

## 2.10 Why Nix Docker Images Are Reproducible

Nix dockerTools produced identical image tarball hashes:

```text
72dbcc11fd3429ca91d674696b8721f0ba11da8e6e64bd3fa0768e49a68f37b2
72dbcc11fd3429ca91d674696b8721f0ba11da8e6e64bd3fa0768e49a68f37b2
```

This is possible because:

- dependencies are declared in Nix
- Nix store paths are content-addressed
- the image uses fixed creation time
- inputs are deterministic
- the output tarball is generated from the same dependency closure

---

## 2.11 Reflection for Task 2

If Lab 2 were redone with Nix, I would:

- build the Python application using `default.nix`
- build the container image using `dockerTools`
- avoid installing Python dependencies with `pip` inside the Dockerfile
- use fixed timestamps
- build Linux-targeted images explicitly when running containers
- keep Docker only as a runtime/distribution format, not as the main build system

The main lesson is that Docker is excellent for packaging and running applications, but Docker alone does not guarantee bit-for-bit reproducible builds. Nix provides stronger guarantees by making dependencies and build inputs explicit.

---

# Bonus Task — Modern Nix with Flakes

The bonus task was not completed.

This submission focuses on the required 10 points:

- Task 1: Build reproducible Python application with Nix
- Task 2: Build reproducible Docker image with Nix and compare with traditional Docker

---

# Final Summary

## Completed Requirements

| Requirement | Status |
|---|---|
| Nix installed and verified | Completed |
| Lab 1 Python app copied into `labs/lab18/app_python` | Completed |
| `default.nix` created | Completed |
| App builds with Nix | Completed |
| App runs from Nix build | Completed |
| Store path reproducibility demonstrated | Completed |
| Lab 2 Dockerfile reviewed | Completed |
| `docker.nix` created | Completed |
| Nix Docker image built | Completed |
| Nix Docker image hash reproducibility demonstrated | Completed |
| Traditional Dockerfile hash comparison demonstrated | Completed |
| Image size comparison completed | Completed |
| Docker history comparison completed | Completed |
| Nix Docker container successfully run after Linux-targeted build | Completed |
| Bonus flakes | Not attempted |

## Final conclusion

Nix provides stronger reproducibility guarantees than traditional `pip`, `venv`, and Dockerfile workflows.

The Python application built with Nix produced stable store paths across rebuilds. The Nix Docker image produced identical image tarball hashes across rebuilds. In contrast, the traditional Dockerfile produced different image hashes across repeated builds.

Docker remains useful as a container runtime, but Nix is better suited for deterministic builds, dependency pinning, and reproducible DevOps pipelines.

