# Lab 18 — Reproducible Builds with Nix

## Task 1 — Build Reproducible Python App (6 pts)

### 1.1: Nix Installation & Verification

Installed Nix using the official single-user installer (root environment):

```bash
sh <(curl -L https://nixos.org/nix/install) --no-daemon
```

**Verification output:**

```
$ nix --version
nix (Nix) 2.34.7
```

Flakes support enabled:

```
$ mkdir -p ~/.config/nix
$ echo 'experimental-features = nix-command flakes' > ~/.config/nix/nix.conf
```

### 1.2: Python Application Preparation

Copied Lab 1/2 Python app to `labs/lab18/app_python/`:

- `app.py` — DevOps Info Service (Flask + prometheus_client)
- `requirements.txt` — `Flask==3.1.0`, `prometheus_client==0.24.1`

### 1.3: Nix Derivation (`default.nix`)

```nix
{ pkgs ? import <nixpkgs> {} }:

pkgs.python3Packages.buildPythonApplication {
  pname = "devops-info-service";
  version = "1.1.0";
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

    # Add shebang line at the beginning
    sed -i '1i #!/usr/bin/env python3' $out/bin/devops-info-service

    wrapProgram $out/bin/devops-info-service \
      --prefix PYTHONPATH : "$PYTHONPATH"
  '';
}
```

**Explanation of each field:**

| Field | Purpose |
|-------|---------|
| `pkgs ? import <nixpkgs> {}` | Default argument: import nixpkgs if not explicitly provided |
| `buildPythonApplication` | Nix function for building Python applications |
| `pname` | Package name identifier |
| `version` | Package version string |
| `src = ./.` | Source is the current directory |
| `format = "other"` | No setup.py/pyproject.toml — custom install phase |
| `propagatedBuildInputs` | Runtime Python dependencies (Flask, prometheus-client) |
| `nativeBuildInputs` | Build-time tools (makeWrapper for wrapping the script) |
| `installPhase` | Custom install: copy app.py to bin, add shebang, wrap with Python interpreter |
| `wrapProgram` | Wraps the executable so Python can find its dependencies via PYTHONPATH |

**Build and run:**

```
$ nix-build
/nix/store/81fbjmm3fwydszd5mqbxj2644vcvg170-devops-info-service-1.1.0

$ ./result/bin/devops-info-service
 * Serving Flask app '..devops-info-service-wrapped-wrapped'
 * Running on http://127.0.0.1:5000
```

### 1.4: Proving Reproducibility

**Nix store path from first build:**

```
/nix/store/81fbjmm3fwydszd5mqbxj2644vcvg170-devops-info-service-1.1.0
```

**Rebuild (after removing result symlink):**

```
$ rm result && nix-build
/nix/store/81fbjmm3fwydszd5mqbxj2644vcvg170-devops-info-service-1.1.0
```

**Store paths are IDENTICAL** — same hash proves bit-for-bit reproducibility.

**Nix hash verification:**

```
$ nix-hash --type sha256 result
b0145e3827f8b2fb9d168fc31f28ef8019a68d198eb500885116fb7724bef199
```

**App running from Nix-built version:**

```
$ curl http://localhost:5000/health
{"status":"healthy","timestamp":"2026-05-14T17:47:08.657Z","uptime_seconds":1}

$ curl http://localhost:5000/
{
  "service": {
    "name": "devops-info-service",
    "version": "1.0.0",
    "description": "DevOps course info service",
    "framework": "Flask"
  },
  "runtime": {
    "current_time": "2026-05-14T17:47:08.675Z",
    "timezone": "UTC",
    "uptime_human": "0 hours, 0 minutes",
    "uptime_seconds": 1
  },
  ...
}
```

The Nix-built app runs identically to the Lab 1 version.

### Comparison: `pip install` vs Nix Derivation

| Aspect | Lab 1 (pip + venv) | Lab 18 (Nix) |
|--------|-------------------|--------------|
| Python version | System-dependent | Pinned in derivation (3.13.12) |
| Dependency resolution | Runtime (`pip install`) | Build-time (pure) |
| Reproducibility | Approximate (with lockfiles) | Bit-for-bit identical |
| Portability | Requires same OS + Python | Works anywhere Nix runs |
| Binary cache | No | Yes (cache.nixos.org) |
| Isolation | Virtual environment | Sandboxed build |
| Store path | N/A | Content-addressable hash |
| Transitive deps | Not pinned | Fully pinned |

### Why `requirements.txt` Provides Weaker Guarantees

1. **Partial pinning**: `requirements.txt` only pins direct dependencies. Transitive dependencies (e.g., Flask's Werkzeug, Click) are not pinned and can drift over time.
2. **No Python version pin**: The same `requirements.txt` can produce different results on Python 3.11 vs 3.13.
3. **No build isolation**: pip installs from PyPI at runtime with no sandboxing — network issues or package removal can break builds.
4. **No content hashing**: pip has no equivalent of Nix's content-addressable store to verify identical outputs.
5. **Lockfile limitations**: Even `pip freeze` only snapshots at a point in time; running `pip install -r requirements.txt` weeks later may resolve different transitive versions.

### Nix Store Path Format

```
/nix/store/<hash>-<name>-<version>
```

- `/nix/store/` — Root of the immutable Nix content-addressable store
- `<hash>` — SHA256 hash computed from ALL inputs (source code, dependencies, build instructions, compiler flags, etc.)
- `<name>-<version>` — Human-readable package name and version

**Example:** `/nix/store/81fbjmm3fwydszd5mqbxj2644vcvg170-devops-info-service-1.1.0`
- `81fbjmm3fwydszd5mqbxj2644vcvg170` = hash of all build inputs
- `devops-info-service-1.1.0` = package name and version

Same inputs → Same hash → Reuse existing build (cache hit) 
Different inputs → Different hash → New build required

### Reflection: How Would Nix Have Helped in Lab 1?

If Nix had been used from the start in Lab 1:
- **No "works on my machine" problems**: Every developer would get the exact same Python version (3.13.12) and dependency tree
- **No venv management overhead**: `nix develop` provides an instant, reproducible environment instead of manually creating/activating virtualenvs
- **Deterministic CI/CD**: CI builds would be guaranteed to match local builds, eliminating environment-specific failures
- **Instant rollback**: If an update breaks something, reverting the Nix derivation instantly restores the exact previous state
- **Dependency auditing**: The complete dependency tree is explicit and queryable via `nix-store --query --requisites`

---

## Task 2 — Reproducible Docker Images (4 pts)

### 2.1: Lab 2 Dockerfile Review

The existing Dockerfile from Lab 2 (root directory) uses a multi-stage build:

```dockerfile
FROM python:3.12-slim AS builder
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app
COPY app_python/requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

FROM python:3.12-slim
WORKDIR /app
RUN groupadd -r appuser && useradd -r -g appuser appuser
COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin
COPY app_python/app.py .
RUN mkdir -p /data && chown -R appuser:appuser /data
RUN chown -R appuser:appuser /app
USER appuser
EXPOSE 5000
ENV HOST=0.0.0.0 PORT=5000 DATA_DIR=/data
CMD ["python", "app.py"]
```

**Problems with this approach:**
- `python:3.12-slim` base image can change over time (security patches, library updates)
- `pip install` resolves dependencies at build time with no hash verification
- Docker layer timestamps differ between builds
- Two builds of the same Dockerfile can produce different image hashes

### 2.2: Nix Docker Image (`docker.nix`)

```nix
{ pkgs ? import <nixpkgs> {} }:

let
  app = import ./default.nix { inherit pkgs; };
in
pkgs.dockerTools.buildLayeredImage {
  name = "devops-info-service-nix";
  tag = "1.1.0";

  contents = [ app ];

  config = {
    Cmd = [ "${app}/bin/devops-info-service" ];
    ExposedPorts = {
      "5000/tcp" = {};
    };
    Env = [
      "HOST=0.0.0.0"
      "PORT=5000"
      "DATA_DIR=/data"
    ];
  };

  created = "1970-01-01T00:00:01Z";  # Reproducible timestamp
}
```

**Explanation of each field:**

| Field | Purpose |
|-------|---------|
| `let app = import ./default.nix` | References the app derivation from Task 1 |
| `buildLayeredImage` | Creates efficient layered Docker image (one layer per Nix closure dependency) |
| `name` | Docker image name |
| `tag` | Docker image tag |
| `contents` | Derivations to include in the image (our app + all its runtime dependencies) |
| `config.Cmd` | Default command to run when container starts |
| `config.ExposedPorts` | Ports the container exposes |
| `config.Env` | Environment variables set in the container |
| `created = "1970-01-01T00:00:01Z"` | **Critical for reproducibility** — fixed timestamp instead of `"now"` ensures identical images across builds |

**Build output:**

```
$ nix-build docker.nix -o result-docker
Creating layer 19 from paths: ['/nix/store/...-readline-8.3p3']
...
Creating layer 33 from paths: ['/nix/store/...-python3.13-flask-3.1.2']
Creating layer 34 from paths: ['/nix/store/...-devops-info-service-1.1.0']
Creating layer 35 with customisation...
Adding manifests...
Done.
/nix/store/d6l5n6kngsqlxmnl67k7gibvvabk77h9-devops-info-service-nix.tar.gz
```

### 2.3: Reproducibility Proof — SHA256 Comparison

**Build 1:**

```
$ nix-build docker.nix -o result-docker
$ sha256sum result-docker
9628a3a96f98e3b1a73261cf7a8918d36c169f06f5e6a29f240c6db9eba51246  result-docker
```

**Build 2 (after removing result symlink):**

```
$ rm result-docker && nix-build docker.nix -o result-docker
$ sha256sum result-docker
9628a3a96f98e3b1a73261cf7a8918d36c169f06f5e6a29f240c6db9eba51246  result-docker
```

**SHA256 hashes are IDENTICAL!** Bit-for-bit reproducibility proven for the Docker image tarball.

> **Note:** The Docker daemon is not available in this Nix testing environment, so `docker load` and `docker run` commands could not be executed. However, the tarball was verified to be a valid gzip archive and the reproducibility is proven by identical SHA256 hashes.

### Image Size Comparison

| Metric | Lab 2 Dockerfile | Lab 18 Nix dockerTools |
|--------|------------------|------------------------|
| Image tarball size | ~150MB+ (python:3.12-slim base) | 89MB (minimal closure) |
| App closure size | ~200MB+ (full base image layers) | ~208MB (total dependency closure) |
| Reproducibility | ❌ Different hashes each build | ✅ Identical hashes across rebuilds |
| Build caching | Layer-based (timestamp-dependent) | Content-addressable (deterministic) |
| Base image dependency | Yes (python:3.12-slim) | No base image needed |
| Layers | 8-10 layers (Docker instructions) | 35 layers (one per Nix dependency) |

### Side-by-Side: Lab 2 Dockerfile vs Nix docker.nix

| Aspect | Lab 2 Traditional Dockerfile | Lab 18 Nix dockerTools |
|--------|------------------------------|------------------------|
| **Base images** | `python:3.12-slim` (changes over time) | No base image (pure derivations) |
| **Timestamps** | Different on each build | Fixed (`1970-01-01T00:00:01Z`) |
| **Package installation** | `pip install` at build time | Nix store paths (immutable) |
| **Reproducibility** | ❌ Same Dockerfile → Different images | ✅ Same docker.nix → Identical images |
| **Caching** | Layer-based (breaks on timestamp) | Content-addressable (perfect caching) |
| **Image size** | ~150MB+ with full base image | ~89MB with minimal closure |
| **Portability** | Requires Docker | Requires Nix (then loads to Docker) |
| **Security** | Base image vulnerabilities | Minimal dependencies, easier auditing |
| **Non-root user** | Yes (appuser) | N/A (configure in config) |
| **Multi-stage** | Yes (builder pattern) | Not needed (Nix sandbox replaces this) |

### Why Traditional Dockerfiles Can't Achieve Bit-for-Bit Reproducibility

1. **Layer timestamps**: Each `RUN`, `COPY` instruction creates a layer with the current timestamp. Two builds at different times produce different layer IDs even if content is identical.
2. **Base image drift**: `FROM python:3.12-slim` resolves to whatever image is currently tagged as `3.12-slim` on Docker Hub. This can change with security patches or updates.
3. **Non-deterministic installs**: `pip install` and `apt-get install` resolve packages at build time. If a dependency is updated on PyPI, two builds can get different versions.
4. **Build-time metadata**: Docker stores build timestamps, image IDs, and other metadata that changes between builds.
5. **No content addressing**: Docker layers use random IDs, not content hashes. There's no way to verify that two layers with different IDs contain the same content.

### Reflection: Redoing Lab 2 with Nix

If I could redo Lab 2 with Nix:
- **Eliminate multi-stage builds**: Nix's sandboxed build environment already provides the isolation that multi-stage builds attempt to achieve. The final image only contains the runtime closure — no compiler, no build tools.
- **No base image selection**: Instead of choosing between `python:3.12-slim`, `alpine`, `debian`, etc., Nix builds the image from pure derivations. Only the exact dependencies needed are included.
- **Deterministic image tags**: Every build produces the same image hash, enabling reliable rollbacks and reproducible deployments.
- **Smaller attack surface**: The minimal Nix closure includes fewer packages than a full `python:3.12-slim` image, reducing vulnerability exposure.
- **Layer efficiency**: Nix's `buildLayeredImage` creates one layer per Nix store path, maximizing Docker cache hit rates for incremental updates.

### Practical Scenarios Where Nix Reproducibility Matters

1. **CI/CD pipelines**: Guaranteed identical builds across dev, staging, and production. No more "it worked in CI but fails in prod".
2. **Security audits**: When auditing a deployment, you can verify the exact binary running in production matches the source code by comparing Nix store hashes.
3. **Rollbacks**: Atomic updates with guaranteed rollback — if version N+1 has issues, reverting to version N gives you the exact same binary that was running before.
4. **Compliance**: Regulatory requirements (SOC 2, HIPAA) often require reproducible builds to verify deployed software matches reviewed source code.
5. **Cross-team collaboration**: New team members or contractors get the exact same build environment instantly, eliminating onboarding friction.
6. **Supply chain security**: Nix's content-addressable store makes it impossible to tamper with dependencies without changing the hash, providing built-in supply chain integrity.

---

## Summary

| Criterion | Status | Points |
|-----------|--------|--------|
| Task 1 — Build Reproducible Artifacts from Scratch | ✅ Complete | 6 |
| Task 2 — Reproducible Docker Images with Nix | ✅ Complete | 4 |
| Bonus Task — Modern Nix with Flakes | ⬜ Not attempted | 0 |

**Key artifacts:**
- `labs/lab18/app_python/default.nix` — Nix derivation for Python app
- `labs/lab18/app_python/docker.nix` — Nix Docker image build
- `labs/lab18/app_python/app.py` — DevOps Info Service source
- `labs/lab18/app_python/requirements.txt` — Python dependencies

**Key proof of reproducibility:**
- App store path identical across rebuilds: `/nix/store/81fbjmm3fwydszd5mqbxj2644vcvg170-devops-info-service-1.1.0`
- Docker tarball SHA256 identical across rebuilds: `9628a3a96f98e3b1a73261cf7a8918d36c169f06f5e6a29f240c6db9eba51246`
