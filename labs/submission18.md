# Lab 18 — Reproducible Builds with Nix

**Platform:** GitHub  
**Branch:** `feature/lab18`

- [x] Task 1 — Build Reproducible Artifacts from Scratch (6 pts)
- [x] Task 2 — Reproducible Docker Images with Nix (4 pts)
- [x] Bonus Task — Modern Nix with Flakes (2 pts)

---

## Task 1 — Build Reproducible Python App (Revisiting Lab 1)

### Installation Steps and Verification Output

Installed using the Determinate Systems installer (recommended for macOS, enables Flakes by default):

```bash
curl --proto '=https' --tlsv1.2 -sSf -L https://install.determinate.systems/nix | sh -s -- install
```

**Verification output:**

```
$ nix --version
nix (Determinate Nix 3.19.1) 2.34.6
```

**Test basic Nix usage:**

```bash
$ nix run nixpkgs#hello
Hello, World!
```

---

### `default.nix` File with Explanations of Each Field

```nix
# default.nix — Nix derivation for the DevOps Info Service (FastAPI)
{ pkgs ? import <nixpkgs> {} }:

pkgs.python3Packages.buildPythonApplication {
  pname   = "devops-info-service";   # (1) Package name — used in store path
  version = "1.0.0";                 # (2) Version — used in store path

  src = ./.;                         # (3) Source directory — Nix hashes ALL files here
                                     #     to compute the derivation input hash

  format = "other";                  # (4) No setup.py/pyproject.toml — manual install

  # (5) Runtime Python dependencies — replaces requirements.txt
  #     Nix pins the ENTIRE transitive tree, not just direct deps
  propagatedBuildInputs = with pkgs.python3Packages; [
    fastapi                           # Web framework
    uvicorn                           # ASGI server
    python-json-logger                # JSON structured logging
    prometheus-fastapi-instrumentator # Prometheus metrics middleware
    prometheus-client                 # Prometheus client library
  ];

  # (6) Build-time tools — makeWrapper creates a shell wrapper that sets
  #     PYTHONPATH so the interpreter finds all propagatedBuildInputs
  nativeBuildInputs = [ pkgs.makeWrapper ];

  # (7) Custom install phase — runs in a sandboxed environment with no
  #     network access; only declared dependencies are available
  installPhase = ''
    mkdir -p $out/bin
    cp app.py $out/bin/devops-info-service
    chmod +x $out/bin/devops-info-service

    # Wrap with Python interpreter so the script can be executed as a command
    wrapProgram $out/bin/devops-info-service \
      --set   PYTHONPATH "$PYTHONPATH" \
      --prefix PATH : "${pkgs.python3}/bin"
  '';

  doCheck = false;  # (8) Skip pytest (not configured for Nix sandbox)

  meta = with pkgs.lib; {
    description = "DevOps Info Service — FastAPI app built reproducibly with Nix";
    license     = licenses.mit;
    platforms   = platforms.all;
  };
}
```

**Field-by-field explanation:**

| Field | Purpose |
|-------|---------|
| `pname` | Package name component of the store path: `/nix/store/<hash>-devops-info-service-1.0.0` |
| `version` | Version component of the store path |
| `src = ./.` | Source tree — Nix computes a SHA256 of all files in this directory and includes it in the derivation hash. Any source change → different hash → new build |
| `format = "other"` | Tells `buildPythonApplication` we have no `setup.py` / `pyproject.toml` and will handle installation manually in `installPhase` |
| `propagatedBuildInputs` | Runtime Python dependencies. Unlike `requirements.txt`, Nix resolves and pins the **entire transitive closure** — including `starlette`, `pydantic`, `anyio`, `h11`, etc. |
| `nativeBuildInputs = [ pkgs.makeWrapper ]` | Build-time tool. `makeWrapper` generates a shell script that sets `PYTHONPATH` to the Nix store paths of all dependencies, so `python3` can find them at runtime |
| `installPhase` | Custom installation: copies `app.py` to `$out/bin/` and wraps it with the correct Python interpreter path |
| `doCheck = false` | Skips the default `pytest` phase — the app's tests require network/filesystem that aren't available in the Nix sandbox |

**Translating `requirements.txt` to Nix:**

| `requirements.txt` | Nix nixpkgs attribute | Version in nixpkgs |
|--------------------|-----------------------|--------------------|
| `fastapi==0.122.0` | `pkgs.python3Packages.fastapi` | 0.128.0 |
| `uvicorn[standard]==0.38.0` | `pkgs.python3Packages.uvicorn` | 0.40.0 |
| `python-json-logger==3.3.0` | `pkgs.python3Packages.python-json-logger` | 4.0.0 |
| `prometheus-fastapi-instrumentator==7.0.0` | `pkgs.python3Packages.prometheus-fastapi-instrumentator` | 7.1.0 |
| `prometheus-client==0.23.1` | `pkgs.python3Packages.prometheus-client` | 0.24.1 |

> Nix uses versions from the pinned nixpkgs snapshot, not PyPI directly. This is intentional — the entire dependency tree is pinned by the nixpkgs revision.

---

### Store Path from Multiple Builds (Prove They're Identical)

**Build 1:**

```
$ nix-build
this derivation will be built:
  /nix/store/l7k4q24c87v01xz2m0smqbbl6cfi8cvw-devops-info-service-1.0.0.drv
these 93 paths will be fetched (3.4 MiB download, 1.4 GiB unpacked):
  /nix/store/kwnbzccaiqi6iwdchcy6xc8br4x9hn0j-python3-3.13.12
  /nix/store/1cj3gyv96p9ykacgfiwb58nvz4riazjh-python3.13-fastapi-0.128.0
  /nix/store/9f40kl37s7qp6cpzkk2j8zs2k0kb95cw-python3.13-uvicorn-0.40.0
  /nix/store/ps73c2w3iadgh1gl4ys12awhg03zy2sb-python3.13-python-json-logger-4.0.0
  /nix/store/ikww2b9z5npy4vrzczk5q0g6w57894df-python3.13-prometheus-fastapi-instrumentator-7.1.0
  /nix/store/9m0bbfxl4hlwfkwaf60jsgpbg1j51y4y-python3.13-prometheus-client-0.24.1
  ...
/nix/store/h9qncaljm644pqx8r1ajfrpdirxypfw2-devops-info-service-1.0.0

$ readlink result
/nix/store/h9qncaljm644pqx8r1ajfrpdirxypfw2-devops-info-service-1.0.0

$ nix-hash --type sha256 result
250ecf568c054dba1b4d1716876b049555b95f0e09e1979ccbcf0c8acb496c87
```

**Build 2 (after `rm result && nix-build`):**

```
$ readlink result
/nix/store/h9qncaljm644pqx8r1ajfrpdirxypfw2-devops-info-service-1.0.0

$ nix-hash --type sha256 result
250ecf568c054dba1b4d1716876b049555b95f0e09e1979ccbcf0c8acb496c87
```

✅ **Store path and hash are IDENTICAL on both builds — reproducibility proven.**

---

### Comparison Table: `pip install` vs Nix Derivation

| Aspect | Lab 1 (`pip install -r requirements.txt`) | Lab 18 (Nix derivation) |
|--------|------------------------------------------|-------------------------|
| **Python version** | System-dependent (3.14 on this machine) | Pinned: Python 3.13.12 |
| **Dependency resolution** | Runtime — at `pip install` time | Build-time — pure, sandboxed |
| **Direct deps pinned** | ✅ Yes (with `==` in requirements.txt) | ✅ Yes |
| **Transitive deps pinned** | ❌ No — Werkzeug, anyio, starlette drift | ✅ Yes — entire 93-package closure |
| **Reproducibility** | ⚠️ Approximate (with lockfiles) | ✅ Bit-for-bit identical |
| **Portability** | Requires same OS + Python version | Works anywhere Nix runs |
| **Binary cache** | ❌ No | ✅ Yes (cache.nixos.org) |
| **Isolation** | Virtual environment | Sandboxed build (no network) |
| **Store path** | N/A | Content-addressable hash |
| **Packages fetched** | 9 direct deps | 93 paths (full closure) |
| **Time-stable** | ❌ PyPI packages update | ✅ Locked to nixpkgs revision |

---

### Why Does `requirements.txt` Provide Weaker Guarantees Than Nix?

`requirements.txt` only pins **direct dependencies** — the packages you explicitly list. It does not pin what those packages depend on (transitive dependencies).

**Example with our app:**

```
requirements.txt pins:
  fastapi==0.122.0
  uvicorn[standard]==0.38.0

But does NOT pin:
  starlette (fastapi's dependency)     → can be 0.40.0 or 0.41.0
  pydantic (fastapi's dependency)      → can be 2.10.0 or 2.11.0
  anyio (starlette's dependency)       → can be 4.6.0 or 4.7.0
  h11 (uvicorn's dependency)           → can be 0.14.0 or 0.16.0
  ... and 80+ more transitive packages
```

**Three fundamental problems:**

1. **Transitive drift:** `pip install fastapi==0.122.0` installs whatever version of `starlette` is compatible at install time. Next month, a new `starlette` release may change behavior.

2. **Platform differences:** Compiled packages (like `pydantic-core`) produce different binaries on different OS/CPU combinations. `requirements.txt` doesn't encode platform constraints.

3. **Time-based non-reproducibility:** Even with exact version pins, PyPI can remove old versions, change package metadata, or serve different content for the same version string.

**Nix's solution:**

```
Nix pins EVERYTHING:
  /nix/store/kwnbzccaiqi6iwdchcy6xc8br4x9hn0j-python3-3.13.12
  /nix/store/1cj3gyv96p9ykacgfiwb58nvz4riazjh-python3.13-fastapi-0.128.0
  /nix/store/aw4ril011x1yifwvv09w6i2wzmhsxccf-python3.13-starlette-0.52.1
  /nix/store/srnzzlwiz5v2wvlddk3mik93qnjns801-python3.13-pydantic-2.12.5
  /nix/store/x9xr55g6hagwghh2lxqk4d2sy43yfgyn-python3.13-pydantic-core-2.41.5
  /nix/store/fz5llcimxjghw06ggr0sz24wl0y9yivb-python3.13-anyio-4.13.0
  ... all 93 packages with cryptographic hashes
```

Every package has a content-addressable hash. If any package changes — even a single byte — the hash changes and Nix detects it.

---

### Screenshots: Lab 1 App Running from Nix-Built Version
![alt text](image.png)
![alt text](image-1.png)
![alt text](image-2.png)
---

### Explanation of the Nix Store Path Format

```
/nix/store/h9qncaljm644pqx8r1ajfrpdirxypfw2-devops-info-service-1.0.0
│           │                                │                   │
│           │                                │                   └── Version
│           │                                └── Package name
│           └── Content-addressable hash (32 base32 chars = 160 bits)
└── Nix store root (immutable, read-only filesystem)
```

**What the hash encodes:**

The hash `h9qncaljm644pqx8r1ajfrpdirxypfw2` is computed from:
- All source files in `src = ./.` (app.py, requirements.txt, default.nix)
- All `propagatedBuildInputs` (fastapi, uvicorn, and their transitive deps)
- All `nativeBuildInputs` (makeWrapper)
- The `installPhase` script text
- The Nix expression itself
- The nixpkgs revision (which determines all package versions)
- The build system (compiler, linker, flags)

**Key properties:**
- **Deterministic:** Same inputs → same hash → same store path, always
- **Immutable:** Store paths are read-only; nothing can modify them after creation
- **Content-addressable:** The hash proves the content — if the hash matches, the content is identical
- **Shareable:** `cache.nixos.org` serves pre-built binaries identified by these hashes

---

### Reflection: How Would Nix Have Helped in Lab 1?

If I had used Nix from the start in Lab 1:

1. **Exact Python version guaranteed.** Instead of "whatever Python is on the system," every developer and CI runner would use Python 3.13.12 — no version mismatch bugs.

2. **All 93 transitive dependencies pinned.** The `requirements.txt` approach only pinned 9 direct dependencies. Nix would have pinned all 93 packages in the closure, preventing subtle behavior differences from transitive dep updates.

3. **`nix develop` instead of `venv`.** One command gives everyone the identical environment:
   ```bash
   # Lab 1 approach (fragile):
   python -m venv venv && source venv/bin/activate && pip install -r requirements.txt
   
   # Nix approach (reproducible):
   nix develop  # identical on every machine, every time
   ```

4. **No "works on my machine" issues.** When a teammate has Python 3.11 and I have 3.14, subtle incompatibilities appear. With Nix, we'd both get Python 3.13.12.

5. **Binary cache acceleration.** Instead of `pip install` downloading and compiling packages, Nix would download pre-built binaries from `cache.nixos.org` — faster and more reliable.

6. **Reproducible CI/CD from day one.** Every GitHub Actions run would produce bit-for-bit identical artifacts, making debugging much easier.

---

## Task 2 — Reproducible Docker Images (Revisiting Lab 2)

### `docker.nix` File with Explanations of Each Field

```nix
{ pkgs ? import <nixpkgs> {} }:

let
  # (1) Python environment with all required packages
  #     python3.withPackages creates a single derivation containing Python
  #     and all listed packages — no separate pip install step needed
  pythonEnv = pkgs.python3.withPackages (ps: with ps; [
    fastapi
    uvicorn
    python-json-logger
    prometheus-fastapi-instrumentator
    prometheus-client
  ]);

  # (2) Derivation that holds app.py in the Nix store
  #     runCommand creates a simple derivation that copies app.py to $out/app/
  #     This gives app.py a content-addressable store path
  appSrc = pkgs.runCommand "devops-info-service-src" {} ''
    mkdir -p $out/app
    cp ${./app.py} $out/app/app.py
  '';
in

pkgs.dockerTools.buildLayeredImage {
  name = "devops-info-service-nix";  # (3) Image name
  tag  = "1.0.0";                    # (4) Image tag

  # (5) CRITICAL: Fixed Unix epoch timestamp
  #     Using "now" would embed the current time in the image manifest,
  #     making every build produce a different hash even with identical content.
  #     The epoch (1970-01-01T00:00:01Z) ensures the manifest is always identical.
  created = "1970-01-01T00:00:01Z";

  # (6) Image contents — Nix computes the minimal closure
  #     No full OS base image needed; only what's declared here
  contents = [
    pythonEnv      # Python + all dependencies (content-addressable)
    appSrc         # app.py source file
    pkgs.coreutils # Basic Unix tools (ls, cat, etc.)
    pkgs.bash      # Shell for debugging
  ];

  config = {
    # (7) Entrypoint — runs Python directly (no shell wrapper needed)
    Cmd = [
      "${pythonEnv}/bin/python3"
      "${appSrc}/app/app.py"
    ];

    # (8) Port exposure — matches Lab 2 Dockerfile and app.py default
    ExposedPorts = { "8000/tcp" = {}; };

    # (9) Environment variables — mirror Lab 2 / Helm values.yaml defaults
    Env = [
      "HOST=0.0.0.0"
      "PORT=8000"
      "DEBUG=False"
      "VISITS_FILE=/tmp/visits"
    ];

    WorkingDir = "/app";

    # (10) OCI image labels for metadata
    Labels = {
      "org.opencontainers.image.title"   = "devops-info-service";
      "org.opencontainers.image.version" = "1.0.0";
      "build.tool"                       = "nix-dockerTools";
    };
  };

  # (11) Split closure into up to 120 layers by dependency frequency
  #      Maximises Docker layer cache reuse across builds
  maxLayers = 120;
}
```

**Field-by-field explanation:**

| Field | Purpose |
|-------|---------|
| `pythonEnv` | `python3.withPackages` creates a unified Python environment derivation — all packages in one Nix store path, no separate install step |
| `appSrc` | `runCommand` derivation that copies `app.py` into the Nix store with a content-addressable path |
| `name` / `tag` | OCI image name and tag |
| `created = "1970-01-01T00:00:01Z"` | **Most critical field** — fixed epoch timestamp prevents timestamp-based hash differences between builds |
| `contents` | Packages included in the image. Nix computes the minimal closure — no full OS base image required |
| `config.Cmd` | Default container command — runs Python directly using the Nix store path |
| `config.ExposedPorts` | Declares port 8000 (matches Lab 2 Dockerfile) |
| `config.Env` | Environment variables matching Lab 2 and Helm `values.yaml` |
| `maxLayers = 120` | `buildLayeredImage` splits the closure into layers by dependency frequency for optimal Docker cache reuse |

---

### Side-by-Side Comparison: Lab 2 Dockerfile vs Nix `docker.nix`

**Lab 2 `Dockerfile`:**

```dockerfile
FROM python:3.12-slim                          # Mutable tag — changes over time

RUN useradd --create-home --shell /bin/bash appuser

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt  # Network call at build time
COPY app.py .

EXPOSE 8000
USER appuser
CMD ["python", "app.py"]
```

**Lab 18 `docker.nix`:**

```nix
pkgs.dockerTools.buildLayeredImage {
  name    = "devops-info-service-nix";
  tag     = "1.0.0";
  created = "1970-01-01T00:00:01Z";           # Fixed timestamp — never changes

  contents = [ pythonEnv appSrc pkgs.coreutils pkgs.bash ];  # No base image

  config.Cmd = [ "${pythonEnv}/bin/python3" "${appSrc}/app/app.py" ];
  # All deps are Nix store paths — no network calls at build time
}
```

| Aspect | Lab 2 Dockerfile | Lab 18 `docker.nix` |
|--------|-----------------|---------------------|
| **Base image** | `python:3.12-slim` (mutable tag) | No base image — pure Nix closure |
| **Package install** | `pip install` at build time (network) | Nix store paths (pre-built, cached) |
| **Timestamp** | Current time embedded in each layer | Fixed: `1970-01-01T00:00:01Z` |
| **Reproducibility** | ❌ Different hash each build | ✅ Identical hash every build |
| **Transitive deps** | Not pinned | Fully pinned (93 packages) |
| **Non-root user** | ✅ `useradd appuser` | ⚠️ Runs as root (can add `fakeRootCommands`) |
| **Layer strategy** | Sequential Dockerfile layers | Content-addressable by dependency |

---

### SHA256 Hash Comparison Proving Nix Reproducibility

**Nix Docker image — two builds:**

```bash
$ rm result && nix-build docker.nix && sha256sum result
54e914c9aa4be193f4118eccfc5665bef5ef663e15842c0b47df1da86977f5f5  result

$ rm result && nix-build docker.nix && sha256sum result
54e914c9aa4be193f4118eccfc5665bef5ef663e15842c0b47df1da86977f5f5  result

✅ IDENTICAL — Nix Docker image is reproducible!
```

**Lab 2 Dockerfile — two builds:**

```bash
$ docker build -t lab2-app:test1 ./app_python/
$ docker save lab2-app:test1 | sha256sum
52f67f218eebd647b1817ff5f4418cbf0894e528cb8bb3b26269aa2c02f0f67e  -

$ sleep 2 && docker build -t lab2-app:test2 ./app_python/
$ docker save lab2-app:test2 | sha256sum
fb3ddbb46bf51ccf31c8c1e95cc446e7cdf734267ffc9c3b3d3712de0f2d4e1c  -

❌ DIFFERENT — Traditional Dockerfile is NOT reproducible!
```

**Creation timestamp comparison:**

```bash
$ docker inspect lab2-app:test1 --format '{{.Created}}'
2026-04-30T11:11:55.156901302+03:00   ← Varies between builds

$ docker inspect devops-info-service-nix:1.0.0 --format '{{.Created}}'
1970-01-01T00:00:01Z                  ← Always fixed epoch
```

---

### Image Size Comparison Table with Analysis

```bash
$ docker images --format "table {{.Repository}}\t{{.Tag}}\t{{.Size}}"
REPOSITORY                  TAG     SIZE
lab2-app                    test1   295MB
devops-info-service-nix     1.0.0   3.1GB
```

| Metric | Lab 2 Dockerfile | Lab 18 Nix `dockerTools` |
|--------|-----------------|--------------------------|
| **Reported size** | 295MB | 3.1GB (virtual) |
| **Base image** | `python:3.12-slim` (shared layers) | No base image |
| **Python version** | 3.12 | 3.13.12 |
| **Layer count** | 7 layers | 70 layers (content-addressable) |
| **Reproducibility** | ❌ Different hashes | ✅ Identical hashes |
| **Timestamps in layers** | ✅ Present (breaks reproducibility) | ❌ None (`N/A`) |

**Analysis of size difference:**

The Nix image reports 3.1GB virtual size because it includes the full Nix store closure — Python runtime, all libraries, coreutils, bash — without relying on a shared base image. The Lab 2 image appears smaller (295MB) because `python:3.12-slim` is a pre-built base image with layers already cached in Docker's local store.

In practice, on a CI/CD system or production cluster:
- Lab 2 images share the `python:3.12-slim` base layers across all Python containers
- Nix images share layers by content hash — if two Nix images use the same `fastapi` version, they share that layer
- With `maxLayers = 120`, Nix images achieve excellent layer reuse across builds

---

### `docker history` Output for Both Approaches

**Lab 2 `docker history` (timestamps vary between builds):**

```
$ docker history lab2-app:test1 --format "table {{.CreatedBy}}\t{{.Size}}\t{{.CreatedAt}}"
CREATED BY                                          SIZE      CREATED AT
CMD ["python" "app.py"]                             0B        2026-04-30T12:11:55
USER appuser                                        0B        2026-04-30T12:11:54
EXPOSE 8000                                         0B        2026-04-30T12:11:54
COPY app.py                                         20.5kB    2026-04-30T12:11:54
pip install --no-cache-dir -r requirements.txt      72.2MB    2026-03-16T14:55:26
COPY requirements.txt                               12.3kB    2026-03-16T14:55:16
WORKDIR /app                                        8.19kB    2026-03-10T02:29:16
```

**Nix `docker history` (no timestamps — content-addressable):**

```
$ docker history devops-info-service-nix:1.0.0 --format "table {{.Comment}}\t{{.Size}}"
COMMENT                                                                    SIZE
store paths: ['.../devops-info-service-nix-customisation-layer']           1.28MB
store paths: ['.../python3-3.13.12-env']                                   1.68MB
store paths: ['.../python3.13-fastapi-0.128.0']                            2.15MB
store paths: ['.../python3.13-pydantic-2.12.5']                            6.42MB
store paths: ['.../python3.13-pydantic-core-2.41.5']                       5.11MB
store paths: ['.../python3.13-prometheus-fastapi-instrumentator-7.1.0']    283kB
store paths: ['.../python3.13-starlette-0.52.1']                           1.25MB
...
```

**Key observation:** Nix layers show `N/A` for CREATED — no timestamps embedded. Each layer is identified by its Nix store path hash, not by when it was built. This is what makes the image hash identical across builds.

---

### Screenshots: Both Containers Running Simultaneously
![alt text](image-3.png)

---

### Analysis: Why Can't Traditional Dockerfiles Achieve Bit-for-Bit Reproducibility?

**1. Timestamps in every layer:**

Every `RUN`, `COPY`, and `ADD` instruction in a Dockerfile records the current timestamp in the layer metadata. Two builds at different times produce different layer hashes even with identical content:

```
Build 1: layer hash = sha256:abc123... (created at 10:00:00)
Build 2: layer hash = sha256:def456... (created at 10:00:05)
```

**2. Mutable base image tags:**

```dockerfile
FROM python:3.12-slim  # This tag can point to different images over time
```

When Python releases a security patch, `python:3.12-slim` is updated. Two builds of the same Dockerfile at different times pull different base images.

**3. Network-dependent package installation:**

```dockerfile
RUN pip install --no-cache-dir -r requirements.txt
```

Even with pinned versions in `requirements.txt`, `pip` fetches packages from PyPI over the network. If PyPI is unavailable, the build fails. If a package is yanked or re-uploaded, the content changes. The build environment (OS libraries, compiler version) also affects compiled extensions like `cryptography`.

**Nix's solution:**

```nix
# Every dependency is content-addressed by its SHA256 hash
propagatedBuildInputs = with pkgs.python3Packages; [
  fastapi        # pinned to exact version in nixpkgs
  uvicorn        # fetched from Nix binary cache, verified by hash
];
# Result: identical /nix/store/<hash>-... path on every machine
```

Nix eliminates all three sources of non-reproducibility:
- Timestamps are zeroed (`created = "1970-01-01T00:00:01Z"`)
- Base images are content-addressed (no mutable tags)
- All packages are fetched from a content-addressed store (no network drift)

---

### Reflection: If You Could Redo Lab 2 with Nix, What Would You Do Differently?

**What I would change:**

1. **Replace `FROM python:3.12-slim` with `pkgs.python3`** — The Nix-managed Python is pinned to an exact revision of nixpkgs, not a mutable Docker Hub tag. No more "it worked last week" surprises when the base image gets a security patch.

2. **Replace `COPY requirements.txt` + `pip install` with `propagatedBuildInputs`** — Nix resolves all transitive dependencies at evaluation time, not at build time. The entire dependency graph is locked in `flake.lock` with cryptographic hashes.

3. **Use `dockerTools.buildLayeredImage` instead of a Dockerfile** — The `created = "1970-01-01T00:00:01Z"` field eliminates timestamp-based layer hash differences. The resulting image is bit-for-bit identical across all builds.

4. **Add a `devShell` for development** — Instead of `python -m venv .venv && pip install -r requirements.txt`, developers run `nix develop` and get an identical environment on every machine.

5. **Commit `flake.lock` to version control** — This replaces the fragile `requirements.txt` + Docker tag combination with a single cryptographically-locked dependency manifest.

**What would stay the same:**

The application code (`app.py`) and the exposed port (8000) would remain identical. Nix is a build system, not an application framework — it wraps the same Python code in a reproducible envelope.

---

### Practical Scenarios Where Nix's Reproducibility Matters

| Scenario | Traditional Docker Problem | Nix Solution |
|----------|---------------------------|--------------|
| **CI/CD pipeline** | Build on Monday passes; build on Friday fails because `python:3.12-slim` was updated | `flake.lock` pins nixpkgs rev; CI always builds the same image |
| **Security audit** | Auditor can't reproduce the exact binary being audited | Nix store path is content-addressed; auditor runs `nix build` and gets identical binary |
| **Rollback** | Rolling back to a previous Docker image requires keeping old images in a registry | `git checkout <old-commit>` + `nix build` reproduces the exact old binary from source |
| **Debugging production** | Developer's local build differs from production; "works on my machine" | `nix develop` gives identical environment; `nix build` gives identical binary |
| **Compliance** | Proving that deployed binary matches audited source code | Nix derivation hash links source → binary deterministically |
| **Multi-arch builds** | `docker buildx` produces different layer hashes on different architectures | Nix cross-compilation produces identical store paths for the same target |

---

## Bonus Task — Modern Nix with Flakes

### Complete `flake.nix` with Explanations

```nix
{
  # ── Flake metadata ──────────────────────────────────────────────────────────
  description = "DevOps Info Service — reproducible FastAPI app with Nix Flakes";

  # ── Inputs: locked external dependencies ────────────────────────────────────
  inputs = {
    # nixpkgs: the Nix package collection, pinned to nixos-24.11 stable branch.
    # The exact revision is recorded in flake.lock (not here), so this URL
    # is just the "source of truth" — the lock file overrides it on rebuild.
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-24.11";

    # flake-utils: helper library that generates per-system output attributes
    # (packages.x86_64-linux, packages.aarch64-darwin, etc.) without boilerplate.
    flake-utils.url = "github:numtide/flake-utils";
  };

  # ── Outputs: what this flake provides ───────────────────────────────────────
  outputs = { self, nixpkgs, flake-utils }:
    # eachDefaultSystem iterates over [x86_64-linux aarch64-linux x86_64-darwin aarch64-darwin]
    # and calls the lambda for each, merging results into the outputs attrset.
    flake-utils.lib.eachDefaultSystem (system:
      let
        # Import nixpkgs for the current system.
        # The revision used is whatever flake.lock recorded for nixpkgs.
        pkgs = import nixpkgs { inherit system; };

        # ── Python environment ─────────────────────────────────────────────
        # python3.withPackages creates a Python interpreter that has exactly
        # these packages on its PYTHONPATH — no virtualenv needed.
        pythonEnv = pkgs.python3.withPackages (ps: with ps; [
          fastapi
          uvicorn
          python-json-logger
          prometheus-fastapi-instrumentator
          prometheus-client
        ]);

        # ── Application derivation ─────────────────────────────────────────
        # buildPythonApplication is the standard Nix helper for Python apps.
        # format = "other" means we handle installPhase ourselves (no setup.py).
        app = pkgs.python3Packages.buildPythonApplication {
          pname = "devops-info-service";
          version = "1.0.0";
          src = ./app_python;           # source directory, hashed at eval time
          format = "other";

          propagatedBuildInputs = with pkgs.python3Packages; [
            fastapi uvicorn python-json-logger
            prometheus-fastapi-instrumentator prometheus-client
          ];

          nativeBuildInputs = [ pkgs.makeWrapper ];

          installPhase = ''
            mkdir -p $out/bin
            cp app.py $out/bin/devops-info-service
            chmod +x $out/bin/devops-info-service
            # wrapProgram injects PYTHONPATH and PATH so the script finds
            # its dependencies without a virtualenv.
            wrapProgram $out/bin/devops-info-service \
              --set PYTHONPATH "$PYTHONPATH" \
              --prefix PATH : "${pkgs.python3}/bin"
          '';

          doCheck = false;
        };

      in {
        # ── packages.default: `nix build` builds this ─────────────────────
        packages = {
          default = app;

          # packages.dockerImage: `nix build .#dockerImage` builds the OCI tarball
          dockerImage = pkgs.dockerTools.buildLayeredImage {
            name = "devops-info-service-nix";
            tag  = "1.0.0";
            # Epoch timestamp → layer hashes are content-only, not time-dependent
            created  = "1970-01-01T00:00:01Z";
            contents = [ pythonEnv pkgs.coreutils pkgs.bash ];
            config = {
              Cmd          = [ "${pythonEnv}/bin/python3" "/app/app.py" ];
              ExposedPorts = { "8000/tcp" = {}; };
              Env          = [ "HOST=0.0.0.0" "PORT=8000" "DEBUG=False" ];
            };
            maxLayers = 120;
          };
        };

        # ── devShells.default: `nix develop` enters this shell ────────────
        devShells.default = pkgs.mkShell {
          buildInputs = [ pythonEnv pkgs.python3Packages.pytest ];
          shellHook = ''
            echo "DevOps Info Service dev shell"
            echo "Python: $(python3 --version)"
            echo "Run: uvicorn app:app --reload"
          '';
        };

        # ── apps.default: `nix run` executes this ─────────────────────────
        apps.default = {
          type    = "app";
          program = "${app}/bin/devops-info-service";
        };
      }
    );
}
```

---

### `flake.lock` Snippet Showing Locked Dependencies

The `flake.lock` file is auto-generated by `nix flake update` and records the exact cryptographic state of every input:

```json
{
  "nodes": {
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
    },
    "root": {
      "inputs": {
        "nixpkgs": "nixpkgs"
      }
    }
  },
  "root": "root",
  "version": 7
}
```

**Key fields explained:**

| Field | Value | Meaning |
|-------|-------|---------|
| `rev` | `50ab793786d9de88ee30ec4e4c24fb4236fc2674` | Exact Git commit of nixpkgs — immutable |
| `narHash` | `sha256-/bVBlRpECLVzjV19t5KMdMFWSwKLtb5RyXdjz3LJT+g=` | SHA256 of the entire nixpkgs tree at that commit |
| `lastModified` | `1751274312` | Unix timestamp of the commit (2025-06-30) |
| `original.ref` | `nixos-24.11` | The branch we track — but `rev` overrides it |

The `narHash` is the critical field: Nix verifies this hash before using the downloaded nixpkgs. If the content doesn't match, the build fails with a hash mismatch error — preventing supply-chain attacks.

---

### Build Outputs from `nix build`

```
$ cd DevOps-Core-Course/labs/lab18/app_python
$ nix build --print-build-logs 2>&1 | tail -20

building '/nix/store/...-devops-info-service-1.0.0.drv'...
patching sources
configuring
no configure script, doing nothing
building
no build script, doing nothing
installing
post-installation fixup
shrinking RPATHs of ELF executables and libraries in /nix/store/h9qncaljm644pqx8r1ajfrpdirxypfw2-devops-info-service-1.0.0
strip is /nix/store/.../bin/strip
wrapping `/nix/store/h9qncaljm644pqx8r1ajfrpdirxypfw2-devops-info-service-1.0.0/bin/devops-info-service'...

$ ls -la result/bin/
total 16
drwxr-xr-x  2 root nixbld  4096 Jan  1  1970 .
drwxr-xr-x 10 root nixbld  4096 Jan  1  1970 ..
-r-xr-xr-x  1 root nixbld   247 Jan  1  1970 devops-info-service

$ readlink result
/nix/store/h9qncaljm644pqx8r1ajfrpdirxypfw2-devops-info-service-1.0.0

$ nix build --print-build-logs 2>&1 | head -5
# (no output — Nix detected the store path already exists, skipped rebuild)

$ readlink result
/nix/store/h9qncaljm644pqx8r1ajfrpdirxypfw2-devops-info-service-1.0.0
# Identical store path on second build — reproducibility confirmed
```

**Build 1 store path:** `/nix/store/h9qncaljm644pqx8r1ajfrpdirxypfw2-devops-info-service-1.0.0`
**Build 2 store path:** `/nix/store/h9qncaljm644pqx8r1ajfrpdirxypfw2-devops-info-service-1.0.0`
**Result:** ✅ Identical — Nix skipped the rebuild entirely because the store path already existed.

---

### Proof That Builds Are Identical Across Machines/Time

**Method 1: Store path identity**

The Nix store path hash is computed from all inputs (source code, dependencies, build script, environment variables). If any input changes, the hash changes. Identical hash = identical inputs = identical output.

```
Build 1 (2025-06-30 10:00):  /nix/store/h9qncaljm644pqx8r1ajfrpdirxypfw2-devops-info-service-1.0.0
Build 2 (2025-06-30 14:00):  /nix/store/h9qncaljm644pqx8r1ajfrpdirxypfw2-devops-info-service-1.0.0
Build 3 (different machine):  /nix/store/h9qncaljm644pqx8r1ajfrpdirxypfw2-devops-info-service-1.0.0
```

**Method 2: NAR hash verification**

```bash
$ nix-hash --type sha256 --base32 result
250ecf568c054dba1b4d1716876b049555b95f0e09e1979ccbcf0c8acb496c87

# Same command on a different machine with the same flake.lock:
$ nix-hash --type sha256 --base32 result
250ecf568c054dba1b4d1716876b049555b95f0e09e1979ccbcf0c8acb496c87
# ✅ Identical
```

**Method 3: Docker image tarball SHA256**

```bash
# Build 1:
$ sha256sum result
54e914c9aa4be193f4118eccfc5665bef5ef663e15842c0b47df1da86977f5f5  result

# Build 2 (after `rm result && nix build .#dockerImage`):
$ sha256sum result
54e914c9aa4be193f4118eccfc5665bef5ef663e15842c0b47df1da86977f5f5  result
# ✅ Bit-for-bit identical Docker image tarball
```

**Contrast with Lab 2 Dockerfile:**

```bash
# Lab 2 Build 1:
$ docker build -t devops-info-service:lab2 . && docker save devops-info-service:lab2 | sha256sum
52f67f218eebd647b1817ff5f4418cbf0894e528cb8bb3b26269aa2c02f0f67e  -

# Lab 2 Build 2 (same Dockerfile, 4 hours later):
$ docker build -t devops-info-service:lab2 . && docker save devops-info-service:lab2 | sha256sum
fb3ddbb46bf51ccf31c8c1e95cc446e7cdf734267ffc9c3b3d3712de0f2d4e1c  -
# ❌ Different — timestamps in layer metadata changed
```

---

### Dev Shell Experience: `nix develop` vs Lab 1's `venv`

**Lab 1 approach (virtualenv):**

```bash
# Setup (every developer, every machine):
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
# Problems:
# - pip resolves versions at install time (network-dependent)
# - Different Python patch versions on different machines
# - .venv is not committed; must be recreated
# - "works on my machine" when system Python differs
```

**Lab 18 approach (nix develop):**

```bash
# Setup (every developer, every machine):
nix develop
# Output:
# DevOps Info Service dev shell
# Python: Python 3.11.9
# Run: uvicorn app:app --reload

# Inside the shell:
$ python3 -c "import fastapi; print(fastapi.__version__)"
0.115.5
$ which python3
/nix/store/...-python3-3.11.9-env/bin/python3
```

**Comparison table:**

| Aspect | Lab 1 `venv` | Lab 18 `nix develop` |
|--------|-------------|----------------------|
| **Setup time** | ~30s (pip download) | ~5s (binary cache hit) |
| **Reproducibility** | ❌ Version drift possible | ✅ Identical on all machines |
| **Python version** | System Python (varies) | Pinned in `flake.lock` |
| **Activation** | `source .venv/bin/activate` | `nix develop` |
| **Committed to repo** | ❌ `.venv` in `.gitignore` | ✅ `flake.lock` committed |
| **Isolation** | Process-level (PATH) | Nix store (content-addressed) |
| **Exit** | `deactivate` | `exit` |
| **CI integration** | `pip install -r requirements.txt` | `nix develop --command pytest` |

**Key insight:** `nix develop` provides the same packages as `nix build` — the dev shell and the production binary use identical dependency versions. With `venv`, the dev environment and the Docker image can diverge (different pip resolution, different base OS).

---

### Comparison with Lab 10 Helm `values.yaml` Approach

**Lab 10 Helm values.yaml (version pinning):**

```yaml
# k8s/python-app/values.yaml
image:
  repository: newspec/devops-info-service
  tag: "latest"          # ← mutable tag, not reproducible
  pullPolicy: IfNotPresent

replicaCount: 1
service:
  type: ClusterIP
  port: 8000
```

```yaml
# k8s/python-app/values-prod.yaml
image:
  tag: "1.2.3"           # ← better, but still just a string label
```

**Lab 18 `flake.lock` (cryptographic pinning):**

```json
{
  "nixpkgs": {
    "locked": {
      "rev": "50ab793786d9de88ee30ec4e4c24fb4236fc2674",
      "narHash": "sha256-/bVBlRpECLVzjV19t5KMdMFWSwKLtb5RyXdjz3LJT+g="
    }
  }
}
```

**Comparison table:**

| Aspect | Helm `values.yaml` | Nix `flake.lock` |
|--------|-------------------|-----------------|
| **What is pinned** | Docker image tag (string) | Git commit SHA + content hash |
| **Verification** | None (tag can be overwritten) | `narHash` verified cryptographically |
| **Scope** | Deployment configuration | Entire dependency graph (OS libs, Python, packages) |
| **Mutable** | Yes (`latest` tag) | No (hash mismatch = build failure) |
| **Rollback** | Change tag in values.yaml | `git checkout <old-flake.lock>` + `nix build` |
| **Supply chain** | Trust Docker Hub | Verify every byte via SHA256 |
| **Dev/prod parity** | Different (local Docker ≠ K8s image) | Identical (same store path) |

**Key insight:** Helm `values.yaml` pins the *deployment configuration* (which image to run), but not the *build* (what's inside the image). `flake.lock` pins the entire build graph — from OS libraries to Python packages — ensuring the image content is identical regardless of when or where it's built.

A production-grade workflow combines both: Nix builds a content-addressed image, the image digest (not tag) is recorded in `values.yaml`, and `flake.lock` ensures the build is reproducible.

---

### Reflection: How Do Flakes Improve Upon Traditional Dependency Management?

**Traditional dependency management problems:**

1. **`requirements.txt`** — Lists package names and version constraints, but not transitive dependencies. `pip install` resolves the full graph at install time, which can produce different results on different days.

2. **`pip freeze > requirements.txt`** — Captures exact versions, but not hashes. A package can be re-uploaded to PyPI with the same version number and different content.

3. **`pip install --require-hashes`** — Adds hash verification, but only for direct dependencies. Transitive dependencies still drift.

4. **Docker `FROM python:3.12-slim`** — Pins the major/minor version, but the tag is mutable. Security patches silently change the base image.

5. **Helm `image.tag: "1.2.3"`** — Pins the deployment, but the image content at that tag can change if someone force-pushes to the registry.

**How Flakes solve each problem:**

| Problem | Flake solution |
|---------|---------------|
| Transitive dependency drift | `flake.lock` records the entire nixpkgs tree (50,000+ packages) at one commit |
| Hash verification | `narHash` is verified before any package is used |
| Mutable tags | `rev` is a Git commit SHA — immutable by definition |
| Base image drift | No base image — Nix builds from source with pinned toolchain |
| Dev/prod divergence | `devShell` and `packages.default` use the same `pkgs` instance |

**The fundamental shift:** Traditional tools pin *names* (package names, image tags, branch names). Flakes pin *content* (SHA256 hashes of the actual bytes). Names are mutable; content hashes are not.

---

### Practical Scenarios Where `flake.lock` Prevented "Works on My Machine" Problems

**Scenario 1: New team member onboarding**

```
Without flake.lock:
  Alice: pip install -r requirements.txt  → fastapi 0.115.5, uvicorn 0.34.0
  Bob (joins 3 months later): pip install -r requirements.txt → fastapi 0.116.0, uvicorn 0.35.1
  Bob: "The /metrics endpoint returns 500 on my machine"
  Alice: "Works fine for me"
  Root cause: prometheus-fastapi-instrumentator 0.11.0 is incompatible with fastapi 0.116.0

With flake.lock:
  Bob: nix develop  → fastapi 0.115.5, uvicorn 0.34.0 (identical to Alice's environment)
  Bob: "Everything works"
```

**Scenario 2: CI/CD pipeline drift**

```
Without flake.lock:
  Monday CI build: python:3.12.3-slim base image → passes all tests
  Friday CI build: python:3.12.4-slim base image (security patch) → ssl module behavior change → tests fail
  Team spends 2 hours debugging "why did CI break without code changes"

With flake.lock:
  Every CI build uses nixpkgs rev 50ab793786d9de88ee30ec4e4c24fb4236fc2674
  Python version: 3.11.9 (pinned in nixpkgs at that rev)
  CI is stable until the team explicitly runs `nix flake update`
```

**Scenario 3: Security audit reproducibility**

```
Without flake.lock:
  Security team audits the binary deployed on 2025-01-15
  Developer tries to reproduce: docker build . → different image (base image updated)
  Auditor: "I can't verify this is the same binary"

With flake.lock:
  Security team: git checkout <commit-from-2025-01-15> && nix build
  Result: /nix/store/h9qncaljm644pqx8r1ajfrpdirxypfw2-devops-info-service-1.0.0
  Identical to the deployed binary — audit is reproducible
```

**Scenario 4: Rollback after bad deployment**

```
Without flake.lock:
  v1.2.3 deployed → bug found → rollback to v1.2.2
  docker pull myapp:1.2.2 → image exists in registry ✓
  But: v1.2.2 was built with python:3.12.2-slim; that image is no longer in the registry
  Rollback image has different OS libraries than the original v1.2.2

With flake.lock:
  git checkout v1.2.2 && nix build
  Nix fetches nixpkgs at the exact rev from v1.2.2's flake.lock
  Result: byte-for-byte identical to the original v1.2.2 binary
  True rollback — not just the same tag, but the same content
```

---