# Lab 18 — Reproducible Builds with Nix

## 1. Overview

This submission documents Lab 18 without the optional Flakes bonus task.

The lab uses the Python DevOps Info Service from the previous Docker/Python lab and rebuilds it using Nix. The main goal is to compare traditional development and containerization workflows with Nix-based reproducible builds.

Completed tasks:

- Task 1 — Build Reproducible Python App with Nix
- Task 2 — Build Reproducible Docker Image with Nix `dockerTools`
- Bonus Task — Not attempted

Application used:

```text
DevOps Info Service
Framework: FastAPI
Port: 5000
Health endpoint: /health
```

The application was taken from the previous Lab 2 `app_python` directory and contains:

```text
app_python/
├── app.py
├── requirements.txt
├── Dockerfile
├── default.nix
└── docker.nix
```

---

## 2. Task 1 — Build Reproducible Python App

### 2.1 Nix Installation and Verification

Nix was installed on macOS using the Determinate Systems installer. On macOS, the installer created a separate Nix store volume mounted at `/nix` and installed Determinate Nix.

Nix binary location check:

```text
/nix/var/nix/profiles/default/bin/nix
```

Nix version:

```text
nix (Determinate Nix 3.19.1) 2.34.6
```

Basic Nix functionality was verified with:

```bash
nix run nixpkgs#hello
```

Expected output:

```text
Hello, world!
```

This confirmed that Nix was installed and usable.

---

### 2.2 Traditional Lab 1 / Lab 2 Python Workflow

The original Python workflow used a virtual environment and `requirements.txt`:

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python app.py
```

The application dependencies from `requirements.txt` are:

```text
fastapi==0.116.1
uvicorn[standard]==0.35.0
```

This workflow is easy to use, but its reproducibility is limited:

- the Python interpreter version depends on the local machine;
- the operating system and system libraries are not pinned;
- build tools are not pinned;
- `requirements.txt` only describes Python packages, not the whole runtime closure;
- unpinned requirements can drift over time.

---

### 2.3 Nix Derivation

The Python application was rebuilt with Nix using `buildPythonApplication`.

File: `app_python/default.nix`

```nix
{ pkgs ? import <nixpkgs> {} }:

let
  cleanAppSource = pkgs.lib.cleanSourceWith {
    src = ./.;

    # Keep only files that are real application inputs.
    # This prevents __pycache__, result symlinks, virtualenvs,
    # evidence files, and temporary files from changing the Nix output hash.
    filter = path: type:
      let
        base = baseNameOf path;
      in
        base == "app.py" || base == "requirements.txt";
  };
in
pkgs.python3Packages.buildPythonApplication {
  pname = "devops-info-service";
  version = "1.0.0";
  src = cleanAppSource;

  format = "other";

  propagatedBuildInputs = with pkgs.python3Packages; [
    fastapi
    uvicorn
  ];

  nativeBuildInputs = [
    pkgs.makeWrapper
  ];

  dontUnpack = false;

  installPhase = ''
    mkdir -p $out/share/devops-info-service
    cp app.py $out/share/devops-info-service/app.py

    mkdir -p $out/bin
    makeWrapper ${pkgs.python3Packages.uvicorn}/bin/uvicorn $out/bin/devops-info-service \
      --add-flags "app:app" \
      --add-flags "--host" \
      --add-flags "0.0.0.0" \
      --add-flags "--port" \
      --add-flags "5000" \
      --set PYTHONPATH "$out/share/devops-info-service:$PYTHONPATH"
  '';
}
```

Explanation of important fields:

| Field | Meaning |
|---|---|
| `pname` | Package name used in the Nix store path |
| `version` | Application version |
| `src` | Source files used as build input |
| `cleanSourceWith` | Restricts the source input to only real application files |
| `format = "other"` | Used because the app does not have `setup.py` or `pyproject.toml` packaging |
| `propagatedBuildInputs` | Runtime Python dependencies |
| `nativeBuildInputs` | Build tools needed during installation |
| `makeWrapper` | Creates an executable wrapper for launching Uvicorn |
| `installPhase` | Copies the app and creates the runnable command |

---

### 2.4 Build the App with Nix

Build command:

```bash
cd app_python
nix-build
```

The build created a `result` symlink pointing to the Nix store.

First successful store path:

```text
/nix/store/p48kbzynj13wmfy9iln8lzfcl9hhiiy8-devops-info-service-1.0.0
```

After improving the derivation with `cleanSourceWith`, the stable reproducible store path became:

```text
/nix/store/ymqp26xh3nq4a559b528s3nxgp82yrkf-devops-info-service-1.0.0
```

Contents of `result/bin`:

```text
total 8
dr-xr-xr-x@ 3 root  wheel    96B Jan  1  1970 .
dr-xr-xr-x@ 5 root  wheel   160B Jan  1  1970 ..
-r-xr-xr-x@ 1 root  wheel   1.7K Jan  1  1970 devops-info-service
```

The timestamps are normalized to deterministic values, which is part of Nix's reproducibility model.

---

### 2.5 Run the Nix-Built Application

The Nix-built application was started with:

```bash
./result/bin/devops-info-service
```

The app started successfully with Uvicorn:

```text
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```

Health check command:

```bash
curl -s http://localhost:5000/health | jq
```

Response:

```json
{
  "status": "healthy",
  "timestamp": "2026-05-05T18:46:19.073860+00:00",
  "uptime_seconds": 22
}
```

This confirms that the Nix-built version of the application works correctly.

---

### 2.6 Store Path Reproducibility

First build store path:

```text
/nix/store/ymqp26xh3nq4a559b528s3nxgp82yrkf-devops-info-service-1.0.0
```

Second build store path:

```text
/nix/store/ymqp26xh3nq4a559b528s3nxgp82yrkf-devops-info-service-1.0.0
```

Commands used:

```bash
readlink result > ../evidence/02-store-path-first.txt
rm result
nix-build
readlink result > ../evidence/05-store-path-second.txt

diff ../evidence/02-store-path-first.txt ../evidence/05-store-path-second.txt
```

The `diff` command produced no output, which means the store paths are identical.

This proves that the same Nix expression and the same declared inputs produced the same output path.

---

### 2.7 Source Filtering Issue and Fix

During the first reproducibility test, the store path changed between builds:

```text
/nix/store/p48kbzynj13wmfy9iln8lzfcl9hhiiy8-devops-info-service-1.0.0
/nix/store/cjlncc1qz06xrhnpx56i2cf4qxzychfc-devops-info-service-1.0.0
```

This happened because the initial derivation used:

```nix
src = ./.;
```

That made the whole `app_python` directory part of the Nix input. After running the app and creating temporary files, the source input changed, so Nix correctly produced a different store hash.

The fix was to use `pkgs.lib.cleanSourceWith` and include only the real application inputs:

```nix
base == "app.py" || base == "requirements.txt";
```

After this fix, repeated builds produced the same store path.

This is an important observation: Nix is reproducible only when the inputs are controlled. If temporary files are included in the source input, they correctly affect the output hash.

---

### 2.8 Nix Output Hash

The Nix output hash was recorded with:

```bash
nix-hash --type sha256 result
```

Evidence file:

```text
evidence/06-nix-output-hash.txt
```

This hash represents the Nix build output. With the same source files, dependencies, and build instructions, the output remains stable.

---

### 2.9 Pip / venv Comparison

To compare with the traditional Python workflow, two virtual environments were created using unpinned requirements:

```bash
echo "fastapi" > requirements-unpinned.txt
echo "uvicorn" >> requirements-unpinned.txt

python3 -m venv venv1
source venv1/bin/activate
pip install -r requirements-unpinned.txt
pip freeze | sort > ../evidence/11-pip-freeze-venv1.txt
deactivate

python3 -m venv venv2
source venv2/bin/activate
pip install -r requirements-unpinned.txt
pip freeze | sort > ../evidence/12-pip-freeze-venv2.txt
deactivate

diff ../evidence/11-pip-freeze-venv1.txt ../evidence/12-pip-freeze-venv2.txt > ../evidence/13-pip-freeze-diff.txt || true
```

Both virtual environments produced the same package versions in this run:

```text
annotated-doc==0.0.4
annotated-types==0.7.0
anyio==4.13.0
click==8.3.3
fastapi==0.136.1
h11==0.16.0
idna==3.13
pydantic==2.13.3
pydantic_core==2.46.3
starlette==1.0.0
```

The `diff` file was empty because both environments were created at the same time from the same package index state.

However, this does not provide the same guarantee as Nix. The pip-based workflow still depends on:

- current package index state;
- the system Python version;
- local OS libraries;
- pip resolver behavior;
- build tools available on the machine;
- network/package availability at install time.

Nix pins the full dependency closure through content-addressed store paths. This gives stronger reproducibility guarantees than `pip install` and a virtual environment.

---

### 2.10 Lab 1 vs Lab 18 Comparison

| Aspect | Lab 1 / Lab 2 Python workflow | Lab 18 Nix workflow |
|---|---|---|
| Python version | Depends on local system or base image | Comes from Nix dependency closure |
| Dependency resolution | Runtime `pip install` | Build-time Nix evaluation |
| Transitive dependencies | Resolved by pip at install time | Included in Nix store closure |
| Build isolation | Virtual environment only | Nix sandbox/store isolation |
| Output identity | No content-addressed output path | `/nix/store/<hash>-name-version` |
| Rebuild behavior | Can vary over time | Same inputs produce same store path |
| Binary cache | Not part of basic pip workflow | Built into Nix model |
| Reproducibility | Approximate | Stronger and content-addressed |

---

## 3. Task 2 — Reproducible Docker Images

### 3.1 Traditional Dockerfile from Lab 2

The Lab 2 Dockerfile was used as the baseline.

File: `app_python/Dockerfile`

```dockerfile
FROM python:3.13-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
RUN useradd -m -u 10001 appuser
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app.py .
RUN chown -R appuser:appuser /app
USER appuser
EXPOSE 5000
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "5000"]
```

This Dockerfile follows normal Docker best practices: slim Python base image, non-root user, pinned direct requirements, exposed port, and Uvicorn command.

However, it is not bit-for-bit reproducible. The base image tag can change over time, `pip install` is executed during the Docker build, and Docker image metadata/layers can differ between builds.

---

### 3.2 Traditional Docker Build Test

The traditional Docker image was built twice:

```bash
docker build -t lab2-app:v1 ./app_python
docker inspect lab2-app:v1 | grep Created > evidence/14-docker-v1-created.txt

sleep 5

docker build -t lab2-app:v2 ./app_python
docker inspect lab2-app:v2 | grep Created > evidence/15-docker-v2-created.txt
```

Observed creation timestamps:

```text
"Created": "2026-05-05T18:57:36.607767714Z",
"Created": "2026-05-05T18:57:36.607767714Z",
```

In this run, Docker reused cache, so the `Created` timestamp was the same.

The saved image hashes were still different:

```text
e016326e69d6dabf5116addb7d25a19dc74434698a517eb027221da1f6b2750d
70ecb79806708b0939b2ce8b534dffc93f65a19383102d36b8a760e55cc3754f
```

Diff output:

```text
1c1
< e016326e69d6dabf5116addb7d25a19dc74434698a517eb027221da1f6b2750d  -
---
> 70ecb79806708b0939b2ce8b534dffc93f65a19383102d36b8a760e55cc3754f  -
```

This demonstrates that the traditional Docker image was not bit-for-bit identical when saved as a tar stream, even though the Dockerfile and source were unchanged.

---

### 3.3 Nix Docker Image with `dockerTools`

A Nix Docker image was built using `pkgs.dockerTools.buildLayeredImage`.

File: `app_python/docker.nix`

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
    ExposedPorts = {
      "5000/tcp" = {};
    };
  };

  created = "1970-01-01T00:00:01Z";
}
```

Explanation:

| Field | Meaning |
|---|---|
| `app` | Imports the Nix-built Python application from `default.nix` |
| `buildLayeredImage` | Creates a Docker image from Nix store paths |
| `name` | Docker image name |
| `tag` | Docker image tag |
| `contents` | Nix store paths included in the image |
| `config.Cmd` | Command executed when the container starts |
| `ExposedPorts` | Declares port `5000/tcp` |
| `created` | Fixed timestamp for reproducibility |

The fixed `created` timestamp is important. Using `created = "now"` would break reproducibility because every image build would include a different timestamp.

---

### 3.4 macOS Silicon Issue and Linux Builder Fix

The first local `nix-build docker.nix` on macOS Silicon produced a Docker image containing a Darwin Nix store executable. When loaded into Docker, the container failed with:

```text
exec /nix/store/.../bin/devops-info-service: exec format error
```

This happened because Docker containers require Linux binaries, while local Nix on macOS builds Darwin binaries by default.

To fix this, the Nix Docker image was rebuilt inside a Linux Nix builder container:

```bash
docker run --rm -it \
  -v "$PWD":/work \
  -w /work/app_python \
  nixos/nix:latest \
  bash
```

Inside the Linux builder container:

```bash
nix-build docker.nix
cp -L result ../evidence/devops-info-service-nix-linux-second.tar.gz
```

The resulting Linux-compatible tarball was copied back to the macOS host, loaded with Docker, and successfully run as a Linux container.

This platform issue is not an application bug. It is caused by the difference between Darwin binaries and Linux container binaries.

---

### 3.5 Nix Docker Image Reproducibility

The Linux-compatible Nix Docker tarball was built twice and hashed on macOS:

```bash
shasum -a 256 evidence/devops-info-service-nix-linux-first.tar.gz | awk '{print $1}' > evidence/19-nix-docker-sha256-first.txt
shasum -a 256 evidence/devops-info-service-nix-linux-second.tar.gz | awk '{print $1}' > evidence/20-nix-docker-sha256-second.txt

diff evidence/19-nix-docker-sha256-first.txt evidence/20-nix-docker-sha256-second.txt > evidence/21-nix-docker-sha256-diff.txt || true
```

First Nix Docker image hash:

```text
4a6da85381110b77896fa096ef255e25ff25092edeb8d019fdd18f118d692c9f
```

Second Nix Docker image hash:

```text
4a6da85381110b77896fa096ef255e25ff25092edeb8d019fdd18f118d692c9f
```

The diff file was empty, which means the hashes were identical.

This proves that the Nix Docker image tarball was bit-for-bit reproducible.

---

### 3.6 Load Nix Image into Docker

The Linux-compatible Nix image was loaded into Docker:

```bash
docker load < evidence/devops-info-service-nix-linux-second.tar.gz > evidence/22-docker-load-nix-image.txt
```

Output:

```text
Loaded image: devops-info-service-nix:1.0.0
```

Docker images included:

```text
devops-info-service-nix:1.0.0         cddac3092d35       1.46GB             0B        
lab2-app:v1                           0477edae7fe5        181MB             0B   U    
lab2-app:v2                           0477edae7fe5        181MB             0B   U    
```

The Nix image is larger in this environment because the full Linux Nix closure was included in the Docker image. The important result for this lab is reproducibility, not minimal size.

---

### 3.7 Run Traditional and Nix Containers Side by Side

The traditional Docker image was run on port `5000`:

```bash
docker run -d -p 5000:5000 --name lab2-container lab2-app:v1
```

The Nix-built Docker image was run on port `5001` mapped to container port `5000`:

```bash
docker run -d -p 5001:5000 --name nix-container devops-info-service-nix:1.0.0
```

Traditional Docker container health check:

```bash
curl -fS http://localhost:5000/health | jq
```

Response:

```json
{
  "status": "healthy",
  "timestamp": "2026-05-05T19:35:03.928955+00:00",
  "uptime_seconds": 1242
}
```

Nix Docker container health check:

```bash
curl -fS http://localhost:5001/health | jq
```

Response:

```json
{
  "status": "healthy",
  "timestamp": "2026-05-05T19:35:03.919602+00:00",
  "uptime_seconds": 37
}
```

Both containers ran successfully and returned healthy status.

---

### 3.8 Docker History Comparison

Traditional Docker image history:

```text
IMAGE          CREATED          CREATED BY                                      SIZE      COMMENT
0477edae7fe5   34 minutes ago   CMD ["uvicorn" "app:app" "--host" "0.0.0.0" …   0B        buildkit.dockerfile.v0
<missing>      34 minutes ago   EXPOSE [5000/tcp]                               0B        buildkit.dockerfile.v0
<missing>      34 minutes ago   USER appuser                                    0B        buildkit.dockerfile.v0
<missing>      34 minutes ago   RUN /bin/sh -c chown -R appuser:appuser /app…   2.37kB    buildkit.dockerfile.v0
<missing>      34 minutes ago   COPY app.py . # buildkit                        2.33kB    buildkit.dockerfile.v0
<missing>      34 minutes ago   RUN /bin/sh -c pip install --no-cache-dir -r…   38.5MB    buildkit.dockerfile.v0
<missing>      35 minutes ago   COPY requirements.txt . # buildkit              43B       buildkit.dockerfile.v0
<missing>      3 weeks ago      WORKDIR /app                                    0B        buildkit.dockerfile.v0
<missing>      3 weeks ago      RUN /bin/sh -c useradd -m -u 10001 appuser #…   8.92kB    buildkit.dockerfile.v0
```

Nix Docker image history:

```text
IMAGE          CREATED   CREATED BY   SIZE      COMMENT
4a51375c652b   N/A                    300B      store paths: ['/nix/store/qz4bannv2gz2dmswvyni4pvxfx2nnckd-devops-info-service-nix-customisation-layer']
<missing>      N/A                    4.24kB    store paths: ['/nix/store/1aywigi97zxn5hv5hlnvmmh2mrc3k6a1-devops-info-service-1.0.0']
<missing>      N/A                    1.58MB    store paths: ['/nix/store/3s53aywfl0dr45462ck13xi3a9pcp836-python3.13-fastapi-0.116.1']
<missing>      N/A                    5.44MB    store paths: ['/nix/store/5pw9qxdf5p3a6mfxfmn72i8yibbk40cx-python3.13-pydantic-2.11.7']
<missing>      N/A                    4.99MB    store paths: ['/nix/store/3gzx32bqnidawxx7pisvig4lwd10j0wh-python3.13-pydantic-core-2.33.2']
<missing>      N/A                    960kB     store paths: ['/nix/store/ldis6a9vpmbpswg6bmxrhgwm4dz4pzgf-python3.13-starlette-0.47.2']
<missing>      N/A                    1.69MB    store paths: ['/nix/store/gkfrf6jd44cw7ah3kw2f7dyyvjvfnga9-python3.13-anyio-4.11.0']
<missing>      N/A                    802kB     store paths: ['/nix/store/hzrz7530swz537prxl9r3r3hk8qnvbxg-python3.13-uvicorn-0.35.0']
<missing>      N/A                    1.23MB    store paths: ['/nix/store/mv1xhqpfbwimj5v4gfhs1aa79n1dkz7x-python3.13-click-8.2.1']
```

The traditional Docker image history is based on Dockerfile build steps. The Nix image history is based on immutable Nix store paths. This makes the dependency closure more explicit.

---

### 3.9 Lab 2 Dockerfile vs Lab 18 Nix Docker Comparison

| Aspect | Lab 2 Traditional Dockerfile | Lab 18 Nix `dockerTools` |
|---|---|---|
| Base image | Uses `python:3.13-slim` | No traditional base image required |
| Dependency installation | `pip install` during Docker build | Dependencies come from Nix store paths |
| Timestamp behavior | Build metadata can vary | Fixed `created` timestamp |
| Image reproducibility | Saved image hashes differed | Tarball hashes were identical |
| Dependency closure | Less explicit | Explicit Nix store closure |
| Docker history | Dockerfile layer commands | Nix store path layers |
| Platform issue | Native Docker image works directly | On macOS, Linux builder was needed |
| Runtime result | `/health` works | `/health` works |

---

### 3.10 Why Traditional Dockerfiles Are Not Fully Reproducible

Traditional Dockerfiles provide isolation, but they do not guarantee bit-for-bit reproducibility.

Reasons:

- image tags such as `python:3.13-slim` can point to different content over time;
- package installation commands can resolve different package versions later;
- Docker metadata and saved image tar streams can differ;
- build cache behavior can hide underlying changes;
- Python dependencies installed through pip are not part of a content-addressed system;
- the build environment is not described as completely as in Nix.

Nix improves this by describing the build output as a function of declared inputs. The Docker image built by `dockerTools` is made from immutable Nix store paths and a fixed timestamp.

---

## 4. Evidence Files

The following evidence files were generated:

```text
evidence/
├── 00-nix-version.txt
├── 01-nix-hello.txt
├── 02-store-path-first.txt
├── 03-result-bin.txt
├── 04-nix-app-health.json
├── 05-store-path-second.txt
├── 06-nix-output-hash.txt
├── 07-store-path-before-delete.txt
├── 08-nix-store-delete.txt
├── 09-store-path-after-force-rebuild.txt
├── 10-store-path-force-diff.txt
├── 11-pip-freeze-venv1.txt
├── 12-pip-freeze-venv2.txt
├── 13-pip-freeze-diff.txt
├── 14-docker-v1-created.txt
├── 15-docker-v2-created.txt
├── 16-docker-v1-sha256.txt
├── 17-docker-v2-sha256.txt
├── 18-docker-sha256-diff.txt
├── 19-nix-docker-sha256-first.txt
├── 20-nix-docker-sha256-second.txt
├── 21-nix-docker-sha256-diff.txt
├── 22-docker-load-nix-image.txt
├── 23-docker-images.txt
├── 24-lab2-container-health.json
├── 25-nix-container-health.json
├── 26-docker-history-lab2.txt
└── 27-docker-history-nix.txt
```

The most important evidence files are:

| File | Purpose |
|---|---|
| `02-store-path-first.txt` | First Nix app store path |
| `05-store-path-second.txt` | Second Nix app store path |
| `06-nix-output-hash.txt` | Nix output hash |
| `16-docker-v1-sha256.txt` | Traditional Docker image hash, build 1 |
| `17-docker-v2-sha256.txt` | Traditional Docker image hash, build 2 |
| `18-docker-sha256-diff.txt` | Difference between traditional Docker image hashes |
| `19-nix-docker-sha256-first.txt` | First Nix Docker tarball hash |
| `20-nix-docker-sha256-second.txt` | Second Nix Docker tarball hash |
| `21-nix-docker-sha256-diff.txt` | Empty diff proving identical Nix Docker hashes |
| `24-lab2-container-health.json` | Health check from traditional Docker container |
| `25-nix-container-health.json` | Health check from Nix Docker container |
| `26-docker-history-lab2.txt` | Traditional Docker image history |
| `27-docker-history-nix.txt` | Nix Docker image history |

---

## 5. Final Reflection

Nix would have helped in the earlier Python and Docker labs by making the build environment explicit and reproducible. In the original workflow, the project depended on local Python, pip resolution, Docker base image tags, and build-time package installation. Those tools are practical but do not fully describe the entire dependency closure.

With Nix, the application output is identified by a Nix store path. If the source files, dependencies, and build instructions are unchanged, the output path remains the same. When uncontrolled files were accidentally included in `src = ./.`, Nix correctly changed the output hash. After filtering the source with `cleanSourceWith`, repeated builds produced the same store path.

The Docker comparison showed the same pattern. The traditional Docker image ran correctly, but saved image hashes differed between builds. The Nix-built Docker image produced identical tarball hashes when rebuilt from the same inputs. This demonstrates why Nix is useful for CI/CD, reproducible deployment artifacts, security review, and reliable rollback workflows.

The main practical challenge was macOS Silicon. Local Nix builds Darwin binaries, while Docker containers need Linux binaries. Building the Docker image inside a Linux Nix builder container solved that problem and produced a working Linux-compatible image.

---

## 6. Final Checklist

| Requirement | Status |
|---|---|
| Nix installed and verified | Done |
| Lab 1/2 Python app prepared | Done |
| `default.nix` created | Done |
| Python app built with Nix | Done |
| Nix-built app started successfully | Done |
| `/health` endpoint tested | Done |
| Store paths compared | Done |
| Nix output hash recorded | Done |
| pip / venv comparison documented | Done |
| Lab 2 Dockerfile reviewed | Done |
| Traditional Docker image built twice | Done |
| Traditional Docker image hashes compared | Done |
| `docker.nix` created | Done |
| Nix Docker image built | Done |
| Nix Docker image hashes compared | Done |
| Nix Docker image loaded into Docker | Done |
| Traditional and Nix containers run side by side | Done |
| Container health checks saved | Done |
| Docker histories compared | Done |
| Bonus Flakes task | Not attempted |
