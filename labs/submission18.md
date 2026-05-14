## Build Reproducible Python App (Revisiting Lab 1)

### 1.1 Nix Installation

```bash
curl --proto '=https' --tlsv1.2 -sSf -L https://install.determinate.systems/nix | \
  sh -s -- install linux --init none --no-confirm
```

**Verification output:**

```
$ nix --version
nix (Determinate Nix 3.20.0) 2.34.6
```

**Testing basic Nix usage:**

```
$ nix run nixpkgs#hello
Hello, world!
```

The Determinate Systems installer was chosen because it enables flakes by default and provides better defaults for modern Nix usage.

---

### 1.2 Python Application

The existing DevOps Info Service from Lab 1 is located at `labs/lab18/app_python/`. It is a **FastAPI** application with the following runtime dependencies:

```
uvicorn==0.40.0
fastapi==0.128.0
colorlog==6.10.1
python-json-logger==3.3.0
pydantic==2.12.5
pydantic-settings==2.12.0
prometheus-client==0.23.1
```

**Lab 1 traditional workflow:**
```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python -m uvicorn app:app
```

**Problems with the Lab 1 approach:**
- Python version is system-dependent (different machines may have 3.11, 3.12, 3.13)
- `pip install` resolves transitive dependencies at runtime - versions can drift
- `requirements.txt` pins only **direct** dependencies; transitive deps (e.g., what `fastapi` depends on) are not pinned
- The virtual environment is not portable; it contains absolute paths
- Over time, re-running `pip install -r requirements.txt` can yield different environments

---

### 1.3 Nix Derivation (`default.nix`)

```nix
{ pkgs ? import <nixpkgs> {} }:

let
  # Create a Python environment with all runtime dependencies
  # Nix pins exact versions from nixpkgs, ensuring bit-for-bit reproducibility
  pythonEnv = pkgs.python3.withPackages (ps: with ps; [
    fastapi           # Web framework (0.128.0 in nixpkgs)
    uvicorn           # ASGI server (0.40.0 in nixpkgs)
    colorlog          # Colored logging (6.10.1 in nixpkgs)
    python-json-logger # JSON structured logging (4.0.0 in nixpkgs)
    pydantic          # Data validation (dependency of fastapi)
    pydantic-settings # Settings management (2.12.0 in nixpkgs)
    prometheus-client # Metrics endpoint
  ]);
in

pkgs.stdenv.mkDerivation {
  pname = "devops-info-service";
  version = "1.0.0";

  # Source: current directory, excluding venv and build artifacts
  src = builtins.filterSource
    (path: type:
      let baseName = baseNameOf path;
      in !(builtins.elem baseName [
        "venv" "result" ".git" "__pycache__" ".env"
        "default.nix" "docker.nix" "flake.nix" "flake.lock"
        "tests" "docs"
      ]))
    ./.;

  nativeBuildInputs = [ pkgs.makeWrapper ];

  dontBuild = true;

  installPhase = ''
    runHook preInstall

    mkdir -p $out/lib/devops-info-service $out/bin

    # Copy all Python source modules
    cp app.py config.py visits.py $out/lib/devops-info-service/
    [ -f __init__.py ] && cp __init__.py $out/lib/devops-info-service/ || true
    cp -r core routes $out/lib/devops-info-service/

    # Create an executable wrapper that:
    # 1. Changes to the app directory (required for uvicorn module discovery)
    # 2. Prepends PYTHONPATH so Python finds all local modules
    # 3. Invokes python -m uvicorn with the correct app target
    makeWrapper ${pythonEnv}/bin/python $out/bin/devops-info-service \
      --add-flags "-m uvicorn app:app --host 0.0.0.0 --port 5000" \
      --run "cd $out/lib/devops-info-service" \
      --prefix PYTHONPATH : "$out/lib/devops-info-service"

    runHook postInstall
  '';

  meta = with pkgs.lib; {
    description = "DevOps Info Service built with Nix for reproducible builds";
    platforms = platforms.linux;
  };
}
```

**Key field explanations:**

| Field | Purpose |
|-------|---------|
| `pkgs.python3.withPackages` | Creates a Python environment with exact versions from the pinned nixpkgs snapshot |
| `builtins.filterSource` | Filters source files, excluding `venv/`, build artifacts, and Nix files themselves |
| `pkgs.stdenv.mkDerivation` | Standard Nix build function; runs in a sandboxed environment |
| `dontBuild = true` | Skip the default `make` build phase (not a compiled project) |
| `makeWrapper` | Generates a shell wrapper script that sets up env vars and working directory |
| `--run "cd ..."` | Changes to the app directory before invoking Python (required by uvicorn) |
| `--prefix PYTHONPATH` | Ensures all local modules are importable |

**Build output:**
```
$ nix-build
these 81 paths will be fetched (12.9 MiB download, 582.3 MiB unpacked):
  /nix/store/c6k21wz193fxj8hnaag8vdzjb4s5klrh-python3.13-fastapi-0.128.0
  /nix/store/4dfqs545z25rzsvwpsxzk4s0cxwpl0wb-python3.13-uvicorn-0.40.0
  ...
building '/nix/store/6kj0kw7wxcd2f81qmh7ysxvc5jn6nabq-devops-info-service-1.0.0.drv'...
Running phase: installPhase
/nix/store/zppzgblrybczmwpd7mji3h9wgbzf3xsr-devops-info-service-1.0.0
```

---

### 1.4 Proving Reproducibility

**Step 1 - Record initial store path and hash:**

```
$ readlink result
/nix/store/zppzgblrybczmwpd7mji3h9wgbzf3xsr-devops-info-service-1.0.0

$ nix-hash --type sha256 result
a29cf14bcd82797dcef7c5ddd1a93281c8be7b2eb2036606d5b2b84f4de62494
```

**Step 2 - Force delete from the Nix store:**

```
$ sudo /nix/var/nix/profiles/default/bin/nix-store --delete --ignore-liveness \
    /nix/store/zppzgblrybczmwpd7mji3h9wgbzf3xsr-devops-info-service-1.0.0
deleting '/nix/store/zppzgblrybczmwpd7mji3h9wgbzf3xsr-devops-info-service-1.0.0'
1 store paths deleted, 11.9 KiB freed
```

**Step 3 - Rebuild from scratch:**

```
$ nix-build
this derivation will be built:
  /nix/store/6kj0kw7wxcd2f81qmh7ysxvc5jn6nabq-devops-info-service-1.0.0.drv
building '/nix/store/6kj0kw7wxcd2f81qmh7ysxvc5jn6nabq-devops-info-service-1.0.0.drv'...
Running phase: installPhase
/nix/store/zppzgblrybczmwpd7mji3h9wgbzf3xsr-devops-info-service-1.0.0
```

**Step 4 - Compare:**

```
$ readlink result
/nix/store/zppzgblrybczmwpd7mji3h9wgbzf3xsr-devops-info-service-1.0.0

$ nix-hash --type sha256 result
a29cf14bcd82797dcef7c5ddd1a93281c8be7b2eb2036606d5b2b84f4de62494
```

**Result: store paths match - Build is reproducible**  
Both the store path and SHA256 hash are identical after a full rebuild from scratch.

---

### Nix Store Path Format

The store path `/nix/store/zppzgblrybczmwpd7mji3h9wgbzf3xsr-devops-info-service-1.0.0` consists of:

| Part                               | Meaning                                                                                        |
|------------------------------------|------------------------------------------------------------------------------------------------|
| `/nix/store/`                      | The Nix store root - all packages live here, read-only                                         |
| `zppzgblrybczmwpd7mji3h9wgbzf3xsr` | SHA256-based hash of ALL inputs: source code, dependencies, build instructions, compiler flags |
| `devops-info-service`              | Human-readable package name                                                                    |
| `1.0.0`                            | Package version                                                                                |

This content-addressable design means:
- **Same inputs -> Same hash -> Same output** (guaranteed)
- Two machines with the same `default.nix` will always produce **identical** paths
- The hash proves the content; this is how `cache.nixos.org` safely distributes pre-built binaries

---

### Comparison: `pip install` vs Nix Derivation

| Aspect                      | Lab 1 (`pip` + `venv`)                               | Lab 18 (Nix Derivation)                              |
|-----------------------------|------------------------------------------------------|------------------------------------------------------|
| **Python version**          | System-dependent (may be 3.11, 3.12, 3.13)           | Pinned: Python 3.13.12 (from nixpkgs)                |
| **Dependency resolution**   | At runtime (`pip install`)                           | At build-time (pure, sandboxed)                      |
| **Transitive dependencies** | Not pinned - can drift over time                     | Fully pinned via nixpkgs snapshot                    |
| **Reproducibility**         | Approximate (only direct deps in `requirements.txt`) | Bit-for-bit identical                                |
| **Portability**             | Requires same OS + Python version                    | Works on any machine with Nix                        |
| **Binary cache**            | No                                                   | Yes (`cache.nixos.org` provides pre-built binaries)  |
| **Isolation**               | Virtual environment (shares OS libraries)            | Sandboxed build (no network access, no system paths) |
| **Store path**              | N/A                                                  | Content-addressable hash                             |
| **Time-stability**          | Packages update on PyPI - breaks in months           | Frozen at nixpkgs revision - works forever           |

**Why does `requirements.txt` provide weaker guarantees than Nix?**

`requirements.txt` only pins **direct** dependencies (e.g., `fastapi==0.128.0`). But `fastapi` itself depends on `starlette`, `pydantic`, `anyio`, etc. - and those are NOT pinned by `requirements.txt`. Over time:
- PyPI packages update their own dependencies
- A new install may pull `starlette==0.53.0` instead of `0.52.1`
- Platform-specific wheels may differ between machines

Nix solves this by deriving a single cryptographic hash over **the entire dependency tree** - including all transitive dependencies, their source code, and the exact compiler used. Any change anywhere in this tree produces a completely different hash and thus a completely different build.

**Reflection:** If Nix had been used from the start of Lab 1, every developer and CI/CD pipeline would have gotten identical Python environments. No "works on my machine" issues. The `nixpkgs` revision would have acted as a global lockfile for all 80,000+ packages simultaneously.

---

### 2.1 Dockerfile Review

```dockerfile
FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    APP_HOST=0.0.0.0 \
    APP_PORT=80

RUN addgroup --system app \
    && adduser --system --ingroup app app

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt
COPY . .
RUN mkdir -p /data && chown -R app:app /app /data

USER app
EXPOSE $APP_PORT
ENTRYPOINT ["sh", "-c"]
CMD ["python -m uvicorn app:app --host $APP_HOST --port $APP_PORT"]
```

**Testing Lab 2 reproducibility - two builds of the same Dockerfile:**

```bash
$ docker build -t lab2-app:test1 --no-cache ./app_python
$ docker save lab2-app:test1 | sha256sum
bee4443465d0f6705f5e0650731d03e886da1a4b53269fe578217cbffe720b06  -

$ sleep 2
$ docker build -t lab2-app:test2 --no-cache ./app_python
$ docker save lab2-app:test2 | sha256sum
639b93d241bf8687d1f47b64e1649d995a1513684fc2922acdf7f86153917542  -
```

**Different hashes from identical Dockerfile.** The images are NOT reproducible.

Timestamp comparison:
```bash
$ docker inspect lab2-app:test1 | grep Created
"Created": "2026-05-14T12:17:47.64120982+03:00"

$ docker inspect lab2-app:test2 | grep Created
"Created": "2026-05-14T12:18:16.7994841+03:00"
```

Different creation timestamps - even identical source -> different image hash.

---

### 2.2 Nix Docker Image (`docker.nix`)

```nix
{ pkgs ? import <nixpkgs> {} }:

let
  # Import the application derivation from default.nix
  app = import ./default.nix { inherit pkgs; };
in

# Build a layered Docker image using Nix's dockerTools
pkgs.dockerTools.buildLayeredImage {
  name = "devops-info-service-nix";
  tag = "1.0.0";

  # Include the app and its minimal runtime dependencies
  # No base OS image needed - Nix provides exactly what's required
  contents = [
    app
    pkgs.coreutils  # For basic shell utilities inside the container
    pkgs.bash       # Required for the wrapper script
  ];

  config = {
    # Full path in the Nix store - reproducible and deterministic
    Cmd = [ "${app}/bin/devops-info-service" ];

    ExposedPorts = {
      "5000/tcp" = {};
    };

    Env = [
      "APP_HOST=0.0.0.0"
      "APP_PORT=5000"
      "DATA_DIR=/data"
    ];

    WorkingDir = "${app}/lib/devops-info-service";
  };

  # CRITICAL: Fixed timestamp makes the image reproducible
  # Using "now" would cause different hashes on each build
  created = "1970-01-01T00:00:01Z";
}
```

**Key field explanations:**

| Field                                | Purpose                                                                     |
|--------------------------------------|-----------------------------------------------------------------------------|
| `pkgs.dockerTools.buildLayeredImage` | Creates a layered Docker image with content-addressable layers              |
| `import ./default.nix`               | Reuses the app derivation from Task 1                                       |
| `contents`                           | Packages to include; Nix computes their exact closure (all transitive deps) |
| `config.Cmd`                         | Uses the full Nix store path - deterministic across all machines            |
| `created = "1970-01-01T00:00:01Z"`   | **Critical** - fixed Unix epoch timestamp ensures image hash doesn't change |

**Building the Nix Docker image:**

```bash
$ nix-build docker.nix
Creating layer 48 from paths: ['/nix/store/kwlnx6gdmphh1x8w69p29y9x1a1r5a49-python3-3.13.12-env']
Creating layer 49 from paths: ['/nix/store/zppzgblrybczmwpd7mji3h9wgbzf3xsr-devops-info-service-1.0.0']
Creating layer 50 with customisation...
Done.
/nix/store/7h6p04gdvpr8ws3vq8zmf79nyy8cr111-devops-info-service-nix.tar.gz
```

**Loading into Docker:**
```bash
$ docker load < result
Loaded image: devops-info-service-nix:1.0.0
```

---

### 2.3 Reproducibility Comparison

**Test: Rebuild Nix Docker image after store deletion:**

```bash
# Build 1
$ nix-build docker.nix
$ sha256sum result
99b565ce459bf0cecf86c6c88d1ca14dec162776e9db2335401f7fd0cbf1c688  result
$ readlink result
/nix/store/7h6p04gdvpr8ws3vq8zmf79nyy8cr111-devops-info-service-nix.tar.gz

# Force delete the store path
$ sudo nix-store --delete --ignore-liveness \
    /nix/store/7h6p04gdvpr8ws3vq8zmf79nyy8cr111-devops-info-service-nix.tar.gz
1 store paths deleted, 95.7 MiB freed

# Build 2
$ nix-build docker.nix
$ sha256sum result
99b565ce459bf0cecf86c6c88d1ca14dec162776e9db2335401f7fd0cbf1c688  result
$ readlink result
/nix/store/7h6p04gdvpr8ws3vq8zmf79nyy8cr111-devops-info-service-nix.tar.gz

RESULT: NIX DOCKER HASHES MATCH - Reproducible!
```

**SHA256 hash comparison summary:**

| Build      | Approach               | Hash                                 |
|------------|------------------------|--------------------------------------|
| Lab2 test1 | Traditional Dockerfile | `bee4443465d0f6705f5e0...`           |
| Lab2 test2 | Traditional Dockerfile | `639b93d241bf8687d1f4...` different  |
| Nix Build1 | `docker.nix`           | `99b565ce459bf0cecf86c...`           |
| Nix Build2 | `docker.nix`           | `99b565ce459bf0cecf86c...` identical |

---

**Image size comparison:**

| Metric         | Lab 2 Dockerfile                       | Lab 18 Nix `dockerTools`             |
|----------------|----------------------------------------|--------------------------------------|
| Disk usage     | 283 MB                                 | 520 MB                               |
| Content size   | 68.7 MB                                | 253 MB                               |
| Base image     | `python:3.13-slim` (changes over time) | No base image - pure Nix store paths |
| Python version | 3.13.13 (latest in base image)         | 3.13.12 (pinned in nixpkgs)          |

> **Note on size:** The Nix image is larger because it includes the full Nix Python runtime closure (glibc, openssl, readline, etc.) as separate layers. The Lab 2 image appears smaller because `python:3.13-slim` shares layers with other images already present. The Nix image can be reduced significantly with `pkgs.dockerTools.buildImage` (non-layered) or by trimming optional dependencies.

---

**Docker history comparison:**

Lab 2 `docker history lab2-app:test1` shows **relative timestamps** ("About a minute ago") - which change on every build:
```
IMAGE          CREATED              CREATED BY                        SIZE
6092ab4abe31   About a minute ago   CMD ["python -m uvicorn app..."]  0B
<missing>      About a minute ago   RUN pip install...                81.4MB
<missing>      5 days ago           CMD ["python3"]                   0B
```

Nix `docker history devops-info-service-nix:1.0.0` shows **N/A** for all timestamps:
```
IMAGE          CREATED   CREATED BY   SIZE
e1ce3c37d1b2   N/A                    827kB   store paths: [...-customisation-layer]
<missing>      N/A                    106kB   store paths: [...-devops-info-service-1.0.0]
<missing>      N/A                    2.15MB  store paths: [...-fastapi-0.128.0]
<missing>      N/A                    140MB   store paths: [...-python3-3.13.12]
```

---

**Timestamp comparison:**

| Image                           | Created field                        |
|---------------------------------|--------------------------------------|
| `lab2-app:test1`                | `2026-05-14T12:17:47.64120982+03:00` |
| `lab2-app:test2`                | `2026-05-14T12:18:16.7994841+03:00`  |
| `devops-info-service-nix:1.0.0` | `1970-01-01T00:00:01Z`               |

The Nix image timestamp is the Unix epoch - fixed, deterministic, and identical on every machine.

---

**Both containers running side by side:**

```bash
# Lab 2 container (port 5000)
$ docker run -d -p 5000:80 --name lab2-container lab2-app:test1

# Nix container (port 5001)
$ docker run -d -p 5001:5000 -e DATA_DIR=/tmp --name nix-container devops-info-service-nix:1.0.0

# Lab 2 health check
$ curl http://localhost:5000/health
{"status":"healthy","timestamp":"2026-05-14T09:22:44.867712","uptime_seconds":4}

# Nix health check
$ curl http://localhost:5001/health
{"status":"healthy","timestamp":"2026-05-14T09:22:44.886702","uptime_seconds":4}
```

Both containers return identical responses - the app works identically regardless of build method.

**Root endpoint response from Nix container:**
```json
{
  "service": {"name": "devops-info-service", "version": "1.0.0"},
  "system": {"python_version": "3.13.12", "platform": "Linux"},
  "runtime": {"uptime_seconds": 4}
}
```

---

### Comprehensive Comparison: Lab 2 vs Lab 18

| Aspect                     | Lab 2 Traditional Dockerfile           | Lab 18 Nix `dockerTools`               |
|----------------------------|----------------------------------------|----------------------------------------|
| **Base image**             | `python:3.13-slim` (updates over time) | No base image - pure Nix derivations   |
| **Timestamps**             | Different on each build                | Fixed: `1970-01-01T00:00:01Z`          |
| **Package installation**   | `pip install` at build time            | Nix store paths (immutable, pre-built) |
| **SHA256 reproducibility** | Same Dockerfile -> Different hashes    | Same `docker.nix` -> Identical hashes  |
| **Layer caching**          | Timestamp-dependent (breaks often)     | Content-addressable (perfect caching)  |
| **Image layers**           | Monolithic pip install layer           | One layer per Nix package              |
| **Portability**            | Requires Docker Hub + internet         | Requires Nix + binary cache            |
| **Security auditing**      | Hard (opaque base image)               | Easy (exact closure of all paths)      |

**Why can't traditional Dockerfiles achieve bit-for-bit reproducibility?**

1. **Build timestamps** - Docker embeds the current UTC time in every image layer. Two builds of the same `Dockerfile` at different times always produce different manifest hashes.
2. **Mutable base images** - `python:3.13-slim` is a mutable tag; Docker Hub can update it to a new image digest at any time. Today's build and tomorrow's build use different base layers.
3. **`pip install` variability** - Even with pinned versions, pip may resolve wheel vs. source distribution differently across platforms or pip versions. The binary content of installed packages can vary.
4. **Layer ordering and metadata** - BuildKit includes file modification timestamps, directory metadata, and other entropy sources in layer digests.

**Reflection:** For Lab 2, using Nix would have meant zero dependency on Docker Hub availability and zero "this base image was updated" surprises. The `created = "1970-01-01T00:00:01Z"` alone eliminates an entire class of non-reproducibility bugs in CI/CD pipelines.

**Practical scenarios where Nix's reproducibility matters:**
- **CI/CD:** Identical builds across all agents without shared caches
- **Security audits:** Exact list of every binary in the image, with cryptographic proof
- **Rollbacks:** Nix store paths are immutable - rolling back means just repointing a symlink
- **Compliance:** Reproducible builds are required in some regulated industries (aerospace, medical devices) to verify supply-chain integrity
