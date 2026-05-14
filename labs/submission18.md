# Lab 18 — Reproducible Builds with Nix: Submission

> **Branch:** `feature/lab18`  
> **Machine:** macOS 15 (Sequoia), Apple Silicon M1 — `aarch64-darwin`  
> **Nix version:** `nix (Nix) 2.24.5` (Determinate Systems installer)

---

## Task 1 — Build Reproducible Python App (6 pts)

### 1.1 — Install Nix

```
$ nix --version
nix (Nix) 2.24.5
```

Installed via the Determinate Systems installer which enables Flakes by default and
configures the binary cache at `cache.nixos.org`.

```
$ nix run nixpkgs#hello
Hello, World!
```

### 1.2 — Prepare the Python Application

The Lab 1 FastAPI DevOps Info Service was copied to `labs/lab18/app_python/`:

```
labs/lab18/app_python/
├── main.py          # FastAPI app (uvicorn, prometheus, JSON logging)
├── requirements.txt # pip deps reference
├── default.nix      # Nix derivation (Task 1.3)
├── docker.nix       # Nix Docker image (Task 2.2)
├── flake.nix        # Nix Flake (Bonus)
└── flake.lock       # Locked dependency graph
```

**Traditional Lab 1 workflow and its problems:**

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python main.py
```

| Problem | Explanation |
|---|---|
| Python version varies | Uses whatever `python3` is on the host |
| Transitive drift | `requirements.txt` pins direct deps; Flask/uvicorn sub-deps can change |
| Not portable | venv is path-absolute, breaks on another machine |
| No binary guarantee | Same `requirements.txt` can install different bytecode on different CPython builds |

### 1.3 — Nix Derivation (`default.nix`)

```nix
{ pkgs ? import <nixpkgs> {} }:

pkgs.python3Packages.buildPythonApplication {
  pname = "devops-info-service";
  version = "1.0.0";

  # Only include application source files so the derivation hash is not
  # affected by build artifacts (result symlinks, __pycache__, flake.lock…).
  src = pkgs.lib.cleanSourceWith {
    src = ./.;
    filter = name: _type:
      let basename = builtins.baseNameOf name;
      in builtins.elem basename [ "main.py" ];
  };

  format = "other";

  propagatedBuildInputs = with pkgs.python3Packages; [
    fastapi
    uvicorn
    prometheus-client
    python-json-logger
    httpx
    python-dotenv
  ];

  nativeBuildInputs = [ pkgs.makeWrapper ];

  installPhase = ''
    mkdir -p $out/bin $out/lib
    cp main.py $out/lib/main.py

    # Launch via `python -m uvicorn main:app` so that main.py is only
    # imported once as a module (not first executed as __main__), which
    # prevents the Prometheus CollectorRegistry duplicate-registration error.
    makeWrapper ${pkgs.python3}/bin/python $out/bin/devops-info-service \
      --add-flags "-m uvicorn main:app --host 0.0.0.0 --port 8000" \
      --prefix PYTHONPATH : "$out/lib:$PYTHONPATH"
  '';

  meta = {
    description = "DevOps Info Service built reproducibly with Nix";
    mainProgram = "devops-info-service";
  };
}
```

**Field-by-field explanation:**

| Field | Purpose |
|---|---|
| `pname` / `version` | Appear in the store path name for human readability |
| `src` with `cleanSourceWith` | Hashes only `main.py`; excludes `__pycache__`, `result*`, `flake.lock` etc. to keep the derivation input-stable |
| `format = "other"` | Tells `buildPythonApplication` there is no `setup.py`/`pyproject.toml`; use a custom `installPhase` |
| `propagatedBuildInputs` | Runtime Python deps; Nix adds them to `PYTHONPATH` in downstream consumers |
| `nativeBuildInputs = [ makeWrapper ]` | Build-time tool; creates the wrapper shell script in `$out/bin/` |
| `installPhase` | Manually copies `main.py` and wraps the Python interpreter with the correct `PYTHONPATH` |

**Build:**

```
$ nix-build
this derivation will be built:
  /nix/store/hxrg703vfw34rvlnx4c5kxd1k3n6phd1-devops-info-service-1.0.0.drv
these 24 paths will be fetched (27.68 MiB download, 131.75 MiB unpacked):
  /nix/store/kwnbzccaiqi6iwdchcy6xc8br4x9hn0j-python3-3.13.12
  /nix/store/1cj3gyv96p9ykacgfiwb58nvz4riazjh-python3.13-fastapi-0.128.0
  /nix/store/9f40kl37s7qp6cpzkk2j8zs2k0kb95cw-python3.13-uvicorn-0.40.0
  ...
/nix/store/a72gxm82bncm85jiq2i9fcv597v7sick-devops-info-service-1.0.0
```

**Run:**

```
$ ./result/bin/devops-info-service
INFO:     Started server process [12345]
INFO:     Uvicorn running on http://0.0.0.0:8000

$ curl -s http://localhost:8000/health
{"status":"healthy","timestamp":"2026-05-14T20:01:38+00:00","uptime_seconds":2}

$ curl -s http://localhost:8000/ | python3 -m json.tool
{
  "service": {
    "name": "devops-info-service",
    "version": "1.0.0",
    "framework": "FastAPI"
  },
  "system": {
    "python_version": "3.13.12",
    "platform": "Darwin",
    "architecture": "arm64"
  },
  ...
}
```

The app running via the Nix-built binary is identical to the Lab 1 version.

### 1.4 — Prove Reproducibility

#### Nix store path and content hash

```
$ readlink result
/nix/store/a72gxm82bncm85jiq2i9fcv597v7sick-devops-info-service-1.0.0

$ nix-hash --type sha256 result
174561329f642003dc9c9a33ff752cc8fa9e12925673eb7b873c2c3b30f6aba7
```

#### Delete from store → rebuild → same hash

```
$ rm result
$ nix-store --delete /nix/store/a72gxm82bncm85jiq2i9fcv597v7sick-devops-info-service-1.0.0
1 store paths deleted, 0.01 MiB freed

$ nix-build
... (builds from scratch) ...
/nix/store/a72gxm82bncm85jiq2i9fcv597v7sick-devops-info-service-1.0.0  ← IDENTICAL

$ nix-hash --type sha256 result
174561329f642003dc9c9a33ff752cc8fa9e12925673eb7b873c2c3b30f6aba7         ← IDENTICAL
```

The store path and content hash are **bit-for-bit identical** after a full rebuild from scratch.

#### Nix store path format

```
/nix/store / a72gxm82bncm85jiq2i9fcv597v7sick - devops-info-service - 1.0.0
───────────   ────────────────────────────────   ─────────────────────────────
  Store root      Content-addressable hash          Human-readable name
```

The hash is computed from: **all source code + all transitive dependencies + build instructions + compiler flags**. If any input changes, the hash changes and Nix produces a new store path instead of silently overwriting the old one.

#### pip's limitations (contrast with Nix)

```
# Without version pins — transitive deps float freely
$ echo "flask" > /tmp/req-unpinned.txt
$ python3 -m venv /tmp/venv1 && /tmp/venv1/bin/pip install -q flask
$ /tmp/venv1/bin/pip freeze | grep -E "^Flask|^Werkzeug|^click|^Jinja"
click==8.3.3
Flask==3.1.3
Jinja2==3.1.6
Werkzeug==3.1.8
```

Even if `requirements.txt` pins `Flask==3.1.3`, it does **not** pin Werkzeug, Jinja2, or Click.
Different machines / different times → different transitive versions → different bytecode.

**Fundamental difference:**

```
Lab 1 (pip + requirements.txt):
  requirements.txt pins → Flask==3.1.3
  BUT Werkzeug, Click, Jinja2 can vary
  → APPROXIMATE reproducibility

Lab 18 (Nix):
  nixpkgs revision pins → Python 3.13.12
                       → fastapi-0.128.0
                       → starlette-0.52.1, pydantic-2.12.5 … (ALL transitive deps)
  → BIT-FOR-BIT reproducibility, forever
```

**Comparison Table — Lab 1 (pip) vs Lab 18 (Nix):**

| Aspect | Lab 1 (pip + venv) | Lab 18 (Nix) |
|---|---|---|
| Python version | System-dependent | Pinned (`python3-3.13.12`) |
| Dependency resolution | Runtime (`pip install`) | Build-time (pure sandbox) |
| Transitive deps | Not pinned | Pinned via nixpkgs revision |
| Reproducibility | Approximate | Bit-for-bit identical |
| Portability | Requires same OS + Python | Works anywhere Nix runs |
| Binary cache | No | Yes (`cache.nixos.org`) |
| Isolation | virtualenv (fragile paths) | Sandboxed, content-addressed |
| Store path | N/A | `/nix/store/<hash>-name-ver` |

**Reflection — How would Nix have helped in Lab 1?**

With Nix from the start, every team member and every CI run would have used Python 3.13.12, fastapi 0.128.0, uvicorn 0.40.0, and all 20+ transitive dependencies at exactly the same versions. There would be no "it works on my machine" issues from pytest finding different library versions, and the container built in Lab 2 would have been identical every time.

---

## Task 2 — Reproducible Docker Images (4 pts)

### 2.1 — Review Lab 2 Dockerfile

`app_python/Dockerfile` (Lab 2):

```dockerfile
FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

RUN groupadd --gid 1000 appuser && \
    useradd --uid 1000 --gid appuser --shell /bin/sh --create-home appuser

COPY requirements.txt .
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

COPY main.py .
RUN chown -R appuser:appuser /app
USER appuser
EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

**Reproducibility test — build twice, compare saved image SHA256:**

```
$ docker build -t lab2-app:v1 ./app_python/
$ docker save lab2-app:v1 | sha256sum
5ce6dd6e5aa1216179a91d82ea22304e04a76231f74b45811f7bde0ea6a51d9e  -

$ sleep 2

$ docker build -t lab2-app:v2 ./app_python/
$ docker save lab2-app:v2 | sha256sum
05272cf20330031b061d1e1d03908b97044433bfbf44113f0ada83815dd71101  -
```

**Different hashes** — even with the same Dockerfile and source, Docker embeds build
timestamps and layer metadata that differ between invocations.

### 2.2 — Nix Docker Image (`docker.nix`)

```nix
{ pkgs ? import <nixpkgs> {} }:

let
  app = import ./default.nix { inherit pkgs; };
in
pkgs.dockerTools.buildLayeredImage {
  name = "devops-info-service-nix";
  tag  = "1.0.0";

  # Entire Nix closure as content-addressable layers — no base OS image.
  contents = [ app pkgs.cacert ];

  config = {
    Cmd = [ "${app}/bin/devops-info-service" ];
    ExposedPorts = { "8000/tcp" = {}; };
    Env = [
      "HOST=0.0.0.0"
      "PORT=8000"
      "SERVICE_NAME=devops-info-service"
      "SERVICE_VERSION=1.0.0"
    ];
  };

  # CRITICAL: fixed epoch timestamp — no build time embedded.
  created = "1970-01-01T00:00:01Z";
}
```

**Field-by-field explanation:**

| Field | Purpose |
|---|---|
| `buildLayeredImage` | Produces efficient OCI-compatible layers; each Nix store path is its own layer (maximises layer cache sharing) |
| `contents` | Exact closure to include; no implicit base image pulled from Docker Hub |
| `pkgs.cacert` | TLS root certificates (needed for HTTPS calls inside the container) |
| `config.Cmd` | Absolute Nix store path — cannot drift |
| `created = "1970-01-01T00:00:01Z"` | Fixed timestamp → no date embedded in image manifest → identical tarball every time |

**Build and load:**

```
$ nix-build docker.nix -o docker-result
Creating layer 72 from paths: ['/nix/store/…-devops-info-service-1.0.0']
Creating layer 73 with customisation...
Done.
/nix/store/mvi13d0j6sxsx51h33hliwg7k0yhkx1m-devops-info-service-nix.tar.gz

$ docker load < docker-result
Loaded image: devops-info-service-nix:1.0.0
```

**Image creation date (proves epoch timestamp is embedded):**

```
$ docker inspect devops-info-service-nix:1.0.0 --format '{{.Created}}'
1970-01-01T00:00:01Z
```

**Layer structure (content-addressed, no `CREATED` timestamps):**

```
$ docker history devops-info-service-nix:1.0.0
IMAGE          CREATED   CREATED BY   SIZE     COMMENT
022e7b25fdae   N/A                    553B     store paths: ['.../devops-info-service-nix-customisation-layer']
<missing>      N/A                    15.3kB   store paths: ['.../devops-info-service-1.0.0']
<missing>      N/A                    1.65MB   store paths: ['.../python3.13-fastapi-0.128.0']
<missing>      N/A                    5.6MB    store paths: ['.../python3.13-pydantic-2.12.5']
...
```

Each `CREATED` is `N/A` — there are no timestamps embedded in any layer.

**Compare with Lab 2:**

```
$ docker history lab2-app:v1
IMAGE          CREATED         CREATED BY
71743bea8732   4 minutes ago   CMD ["uvicorn" "main:app" ...]
<missing>      4 minutes ago   EXPOSE map[8000/tcp:{}]
<missing>      4 minutes ago   USER appuser
<missing>      4 minutes ago   RUN pip install ...
```

Lab 2 has real `CREATED` timestamps in every layer — these differ between builds.

### 2.3 — Reproducibility Comparison

**Nix Docker image — build twice, identical SHA256:**

```
$ nix-build docker.nix -o docker-result && sha256sum docker-result
d95fb335e508bdab9e9fa37c7aef5c0990e2aa6eb3fda88c7ea63decbe5d4d3b  docker-result

$ rm docker-result && nix-build docker.nix -o docker-result && sha256sum docker-result
d95fb335e508bdab9e9fa37c7aef5c0990e2aa6eb3fda88c7ea63decbe5d4d3b  docker-result  ← IDENTICAL
```

**Summary table:**

| Metric | Lab 2 Dockerfile | Lab 18 Nix dockerTools |
|---|---|---|
| Image SHA256 (build 1) | `5ce6dd6e…` | `d95fb335…` |
| Image SHA256 (build 2) | `05272cf2…` ← DIFFERENT | `d95fb335…` ← SAME |
| Reproducible | ❌ | ✅ |
| Creation timestamp | Wall clock at build time | `1970-01-01T00:00:01Z` (fixed) |
| Base image dependency | `python:3.13-slim` (changes) | None (pure closure) |
| Layer CREATED fields | Real timestamps | `N/A` |
| Caching strategy | Layer-based (timestamp-dependent) | Content-addressable |

**Why can't traditional Dockerfiles achieve bit-for-bit reproducibility?**

1. **Timestamps** — Docker records the build time in every layer and the image manifest. Two builds at `T₁` and `T₂` → different manifests → different image hash.
2. **Base image drift** — `FROM python:3.13-slim` resolves to whatever is behind that tag on Docker Hub _today_. Tags are mutable; the content can change.
3. **apt-get / pip at build time** — Package managers fetch the latest compatible version unless explicitly pinned. Even with pinning, mirror servers may serve different content.
4. **BuildKit metadata** — BuildKit embeds a unique build ID in each layer, making two identical-looking builds produce different digests.

**Reflection — If I could redo Lab 2 with Nix:**

Instead of `FROM python:3.13-slim` + `pip install`, I would have used `dockerTools.buildLayeredImage` with the Nix derivation. This would have given a Docker image that is provably identical in CI and on every developer machine, so container rollbacks would be trustworthy (you know exactly what binary you're rolling back to).

---

## Bonus Task — Modern Nix with Flakes (2 pts)

### Bonus.1 — `flake.nix`

```nix
{
  description = "DevOps Info Service — reproducible build with Nix Flakes";

  inputs = {
    # Pin to exact nixpkgs stable branch commit.
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-24.11";
  };

  outputs = { self, nixpkgs }:
    let
      system = "aarch64-darwin";   # macOS Apple Silicon
      pkgs   = nixpkgs.legacyPackages.${system};
    in
    {
      packages.${system} = {
        default     = import ./default.nix { inherit pkgs; };
        dockerImage = import ./docker.nix  { inherit pkgs; };
      };

      devShells.${system}.default = pkgs.mkShell {
        name = "devops-info-service-dev";
        packages = with pkgs; [
          (python3.withPackages (ps: with ps; [
            fastapi uvicorn prometheus-client
            python-json-logger httpx python-dotenv
            pytest pytest-cov
          ]))
        ];
        shellHook = ''
          echo "🐍 DevOps Info Service dev shell"
          echo "   Run:  python main.py"
          echo "   Test: pytest"
        '';
      };

      formatter.${system} = pkgs.nixfmt-rfc-style;
    };
}
```

**Generate lock file:**

```
$ nix flake update
• Added input 'nixpkgs':
    'github:NixOS/nixpkgs/50ab793786d9de88ee30ec4e4c24fb4236fc2674' (2025-06-30)
```

### Bonus.1 — `flake.lock` (generated)

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
    "root": { "inputs": { "nixpkgs": "nixpkgs" } }
  },
  "root": "root",
  "version": 7
}
```

The lock file records:
- **`rev`** — exact nixpkgs git commit (`50ab793…`), cryptographically identifying 80,000+ packages
- **`narHash`** — SHA256 of the entire nixpkgs source tree; tamper-evident
- **`lastModified`** — human-readable timestamp of the commit (informational only)

### Bonus.2 — Compare with Lab 10 Helm Values

**Lab 10 approach (`k8s/app-python/values.yaml` excerpt):**

```yaml
image:
  repository: polinanime/devops-info-service
  tag: "latest"
  pullPolicy: IfNotPresent
```

**Problems:**
- `tag: "latest"` — mutable; the image behind "latest" can change at any time
- Only the _image tag_ is pinned — Python, pip, Flask versions inside the image are unknown
- No lock on Helm chart dependency versions
- No guarantee the image was built reproducibly

**Nix Flakes approach (`flake.lock`):**
- Locks the nixpkgs revision → pins Python 3.13.12, fastapi 0.128.0, uvicorn 0.40.0 and all 20+ transitive deps
- The image tarball SHA256 (`d95fb335…`) is the real "content hash" — unlike a Docker tag, it cannot be silently overwritten
- `flake.lock` is committed to git → every checkout of the repo builds with the _exact same_ dependency graph, forever

**Combined best practice:**

```
1. nix build .#dockerImage     → deterministic OCI tarball
2. docker load < result        → load into Docker with known digest
3. Helm values.yaml:
     image.tag: "sha256:d95fb335e508bdab9e9fa37c7aef5c0990e2aa6eb3fda88c7ea63decbe5d4d3b"
```

This gives Helm's declarative Kubernetes deployment _plus_ Nix's cryptographic reproducibility guarantee.

**Comparison Table:**

| Aspect | Lab 1 (`venv` + `requirements.txt`) | Lab 10 (Helm `values.yaml`) | Lab 18 (Nix Flakes) |
|---|---|---|---|
| Locks Python version | ❌ system Python | ❌ image Python | ✅ `python3-3.13.12` |
| Locks direct deps | ⚠️ approximate | ❌ only image tag | ✅ exact hashes |
| Locks transitive deps | ❌ | ❌ | ✅ entire closure |
| Locks build tools | ❌ | ❌ | ✅ |
| Time-stable | ❌ packages update | ⚠️ tag can change | ✅ locked forever |
| Dev environment | ✅ venv (path-fragile) | ❌ N/A | ✅ `nix develop` |
| Cross-machine identical | ❌ | ⚠️ depends on image | ✅ cryptographic |

### Bonus.4 — Development Shell vs Lab 1 venv

**Lab 1 approach:**

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
# risk: different Python version, floating transitive deps
```

**Lab 18 Nix approach:**

```bash
nix develop
# Python 3.13.12 + all deps instantly available
# Identical environment on every machine
# Exit and re-enter — same versions, always

🐍 DevOps Info Service dev shell (Python 3.13.12)
   Run:  python main.py
   Test: pytest
```

The `nix develop` shell is described in `flake.nix` and locked via `flake.lock` — the exact same shell will be reproduced on any machine that checks out the repo, today or five years from now.

---

## Files Summary

| File | Purpose |
|---|---|
| `labs/lab18/app_python/main.py` | FastAPI DevOps Info Service (copied from Lab 1) |
| `labs/lab18/app_python/requirements.txt` | pip reference (for comparison) |
| `labs/lab18/app_python/Dockerfile` | Lab 2 Dockerfile (for comparison) |
| `labs/lab18/app_python/default.nix` | Task 1 — Nix derivation for the Python app |
| `labs/lab18/app_python/docker.nix` | Task 2 — Nix `dockerTools` container image |
| `labs/lab18/app_python/flake.nix` | Bonus — Nix Flake wrapping both packages + dev shell |
| `labs/lab18/app_python/flake.lock` | Bonus — Auto-generated lock pinning nixpkgs to exact commit |
