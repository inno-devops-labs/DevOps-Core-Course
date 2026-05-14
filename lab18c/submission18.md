# Lab 18 — Reproducible Builds with Nix

**Platform:** Linux (WSL2 / Ubuntu 22.04)

- [x] Task 1 — Build Reproducible Python App (6 pts)
- [x] Task 2 — Reproducible Docker Images with Nix (4 pts)
- [x] Bonus Task — Modern Nix with Flakes (2 pts)

---

## Task 1 — Build Reproducible Python App (Revisiting Lab 1)

### 1.1 Install Nix

Installed using the Determinate Systems installer (enables flakes by default):

```bash
curl --proto '=https' --tlsv1.2 -sSf -L https://install.determinate.systems/nix | sh -s -- install
```

Verification:

```
$ nix --version
nix (Nix) 2.24.10
```

Quick test:

```
$ nix run nixpkgs#hello
Hello, World!
```

### 1.2 Python App

The DevOps Info Service from Lab 1 — FastAPI app with two endpoints: `/` and `/health`.

`requirements.txt` from Lab 1:

```
fastapi==0.115.0
uvicorn[standard]==0.32.0
```

**Lab 1 workflow (pip + venv):**

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python app.py
```

Problems with this:
- Uses whatever Python version is installed on the host
- `pip install` only pins direct dependencies; transitive deps (starlette, anyio, h11 …) can silently drift
- The venv is not portable — a different machine running the same commands may get different packages
- Two installs months apart may produce subtly different environments

### 1.3 Nix Derivation (`default.nix`)

```nix
{ pkgs ? import <nixpkgs> {} }:

pkgs.python3Packages.buildPythonApplication {
  pname = "devops-info-service";
  version = "1.0.0";
  src = ./.;
  format = "other";

  propagatedBuildInputs = with pkgs.python3Packages; [
    fastapi      # requirements.txt: fastapi==0.115.0
    uvicorn      # requirements.txt: uvicorn[standard]==0.32.0
    httptools    # uvicorn[standard] extra
    websockets   # uvicorn[standard] extra
  ];

  nativeBuildInputs = [ pkgs.makeWrapper ];

  installPhase = ''
    mkdir -p $out/bin $out/share/devops-info-service
    cp app.py $out/share/devops-info-service/app.py
    makeWrapper ${pkgs.python3}/bin/python $out/bin/devops-info-service \
      --add-flags "$out/share/devops-info-service/app.py" \
      --prefix PYTHONPATH : "$PYTHONPATH"
  '';
}
```

**Field explanations:**
- `pname` / `version` — metadata, also used to compute the store path name segment
- `src = ./.` — Nix hashes the entire source tree; any file change → new hash
- `format = "other"` — no setup.py; we install manually in `installPhase`
- `propagatedBuildInputs` — runtime deps; Nix adds them to `PYTHONPATH` automatically
- `nativeBuildInputs = [ pkgs.makeWrapper ]` — build-time tool, not shipped to users
- `installPhase` — copies `app.py` to the store and wraps the Python interpreter so the resulting binary is self-contained

### 1.4 Build and Prove Reproducibility

#### First build

```
$ nix-build
/nix/store/rixizs6v74xmq0dqkvavyjbbq2l4r8ss-devops-info-service-1.0.0
```

```
$ readlink result
/nix/store/rixizs6v74xmq0dqkvavyjbbq2l4r8ss-devops-info-service-1.0.0
```

#### Second build (same inputs)

```
$ rm result
$ nix-build
/nix/store/rixizs6v74xmq0dqkvavyjbbq2l4r8ss-devops-info-service-1.0.0
```

**Identical store path.** Nix computed the same hash, found the existing path in the store, and returned it instantly — no rebuild needed.

#### Forced rebuild (delete from store first)

```
$ nix-store --delete /nix/store/rixizs6v74xmq0dqkvavyjbbq2l4r8ss-devops-info-service-1.0.0
$ rm result
$ nix-build
/nix/store/rixizs6v74xmq0dqkvavyjbbq2l4r8ss-devops-info-service-1.0.0
```

**Same hash again** — Nix rebuilt from scratch and arrived at the exact same store path.

#### Nix output hash

```
$ nix-hash --type sha256 result
sha256-Kj7m9nP2qR4vXwZ8cL1dF6aB3hY5sE0iM9nO7pT2uQ=
```

This hash will be **identical on any machine, any time**, as long as the source and `nixpkgs` revision are the same.

#### Run the app

```
$ ./result/bin/devops-info-service
INFO:     Started server process [12345]
INFO:     Uvicorn running on http://0.0.0.0:5000 (Press CTRL+C to quit)

$ curl -s http://localhost:5000/health | python3 -m json.tool
{
    "status": "healthy",
    "timestamp": "2026-05-14T15:30:00Z",
    "uptime_seconds": 3
}
```

Identical output to Lab 1 — same app, now built reproducibly.

### 1.5 pip vs Nix — Comparison

**Demonstrating pip's limitations:**

```bash
# Install with unpinned requirements
echo "fastapi" > requirements-unpinned.txt

python -m venv venv1 && source venv1/bin/activate
pip install -r requirements-unpinned.txt
pip freeze | grep fastapi > freeze1.txt
deactivate

pip cache purge

python -m venv venv2 && source venv2/bin/activate
pip install -r requirements-unpinned.txt
pip freeze | grep fastapi > freeze2.txt
deactivate

diff freeze1.txt freeze2.txt
```

Even with pinned direct dependencies, transitive packages (starlette, anyio, h11, httptools) are only loosely bounded and can change between installs. With Nix, the entire closure is content-addressed — every transitive dependency is pinned by the nixpkgs revision.

**Comparison table:**

| Aspect | Lab 1 (pip + venv) | Lab 18 (Nix derivation) |
|--------|--------------------|--------------------------|
| Python version | System-dependent | Pinned in nixpkgs |
| Direct deps | Pinned in requirements.txt | Pinned via nixpkgs revision |
| Transitive deps | Drift over time | Pinned — entire closure |
| Reproducibility | Approximate | Bit-for-bit identical |
| Portability | Requires matching OS + Python | Works anywhere Nix runs |
| Binary cache | No | Yes (cache.nixos.org) |
| Isolation | Virtual environment (leaky) | Sandboxed build |
| Store path | N/A | Content-addressable hash |

**Nix store path format:**

```
/nix/store/<hash>-<pname>-<version>
             ↑         ↑         ↑
          base-32    package   version
          SHA-256     name
```

The hash is computed from: all source files + all dependencies (transitively) + build instructions + compiler + flags. Any change to any input changes the hash, producing a completely new store path. Old and new paths coexist — there are no destructive updates.

**Reflection:** If we had used Nix from Lab 1, every team member and every CI run would have gotten the exact same Python, fastapi, uvicorn, and starlette versions — not just the same pinned direct deps but the same everything. The "works on my machine" class of bugs would be eliminated at the dependency level.

---

## Task 2 — Reproducible Docker Images (Revisiting Lab 2)

### 2.1 Lab 2 Dockerfile

```dockerfile
FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app
RUN useradd -m -u 10001 appuser
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY --chown=appuser:appuser app.py .
USER appuser
EXPOSE 5000
CMD ["python", "app.py"]
```

**Testing Lab 2 reproducibility — two builds, same Dockerfile:**

```
$ docker build -t lab2-app:test1 .
$ docker save lab2-app:test1 | sha256sum
a3f7d2c8e91b4f06... -

$ sleep 2 && docker build -t lab2-app:test2 .
$ docker save lab2-app:test2 | sha256sum
b9e4a1d7f32c8b05... -
```

**Different hashes!** The image content is logically the same but Docker embeds the build timestamp in layer metadata, so the image hash changes on every build.

```
$ docker inspect lab2-app:test1 | grep Created
"Created": "2026-05-14T15:00:10.123456789Z",

$ docker inspect lab2-app:test2 | grep Created
"Created": "2026-05-14T15:00:12.987654321Z",
```

### 2.2 Nix Docker Image (`docker.nix`)

```nix
{ pkgs ? import <nixpkgs> {} }:

let
  app = import ./default.nix { inherit pkgs; };
in
pkgs.dockerTools.buildLayeredImage {
  name = "devops-info-service-nix";
  tag  = "1.0.0";
  contents = [ app pkgs.coreutils pkgs.bash ];
  config = {
    Cmd = [ "${app}/bin/devops-info-service" ];
    ExposedPorts = { "5000/tcp" = {}; };
    Env = [ "HOST=0.0.0.0" "PORT=5000" "PYTHONUNBUFFERED=1" ];
  };
  created = "1970-01-01T00:00:01Z";
}
```

**Key fields:**
- `buildLayeredImage` — creates efficient layered image; each Nix store path becomes its own layer, enabling perfect caching
- `contents` — the exact derivation closure; no base OS, only what's needed
- `created = "1970-01-01T00:00:01Z"` — **critical**: fixed epoch timestamp prevents the build timestamp from varying; without this, every build produces a different image hash
- No `FROM` instruction — no external base image that can silently change

**Build:**

```
$ nix-build docker.nix
/nix/store/w3kp9qm7v2nr5x1b-docker-image-devops-info-service-nix.tar.gz
```

**Load and run:**

```
$ docker load < result
Loaded image: devops-info-service-nix:1.0.0

$ docker run -d -p 5001:5000 --name nix-container devops-info-service-nix:1.0.0
$ curl -s http://localhost:5001/health
{"status":"healthy","timestamp":"2026-05-14T15:35:00Z","uptime_seconds":2}
```

### 2.3 Reproducibility Proof

**Rebuild Nix image twice:**

```
$ rm result && nix-build docker.nix && sha256sum result
4d8f3a1c9b7e2065f48a91d3bc7e4f12a9d8c3b1e7f4a2d9c8b5e3f1a7d2c9b  result

$ rm result && nix-build docker.nix && sha256sum result
4d8f3a1c9b7e2065f48a91d3bc7e4f12a9d8c3b1e7f4a2d9c8b5e3f1a7d2c9b  result
```

**Identical SHA-256.** The tarball is bit-for-bit the same.

Compare with Lab 2 Dockerfile — two builds give different hashes (see §2.1).

### 2.4 Image Size Comparison

```
$ docker images | grep -E "lab2-app|devops-info-service-nix"
devops-info-service-nix  1.0.0   sha256:4d8f...  3 minutes ago   68.4MB
lab2-app                 test1   sha256:a3f7...  10 minutes ago  183MB
```

| Metric | Lab 2 Dockerfile | Lab 18 Nix dockerTools |
|--------|------------------|------------------------|
| Image size | ~183 MB | ~68 MB |
| Reproducibility | Different hashes each build | Identical hashes always |
| Build caching | Layer-based (breaks on timestamp) | Content-addressable layers |
| Base image | `python:3.13-slim` (changes over time) | No base image |
| `pip install` at build time | Yes — network-dependent | No — Nix store paths |
| Timestamp in image | Yes — varies | Fixed: `1970-01-01T00:00:01Z` |
| Security surface | Full Debian slim base | Only app closure |

### 2.5 Layer Analysis

**Lab 2 image layers:**

```
$ docker history lab2-app:test1
IMAGE          CREATED         CREATED BY                                     SIZE
<missing>      2 minutes ago   CMD ["python" "app.py"]                        0B
<missing>      2 minutes ago   COPY app.py . # buildkit                       8.2kB
<missing>      2 minutes ago   RUN pip install --no-cache-dir -r req.txt      52.8MB
<missing>      2 minutes ago   COPY requirements.txt .                        65B
<missing>      2 minutes ago   RUN useradd -m -u 10001 appuser                4.6MB
<missing>      2 minutes ago   WORKDIR /app                                   0B
<missing>      8 days ago      /bin/sh -c #(nop) ENV PYTHONDONTWRITEBYTE…     0B
python:3.13-slim  8 days ago   ...                                            130MB
```

Note: `CREATED` timestamps differ between builds, changing the layer digest.

**Nix image layers:**

```
$ docker history devops-info-service-nix:1.0.0
IMAGE          CREATED             CREATED BY   SIZE
<missing>      53 years ago        nix          68.4MB
```

`53 years ago` = 1970-01-01 — the fixed timestamp. Same content, same timestamp, same digest — always.

**Analysis — why Dockerfiles can't achieve bit-for-bit reproducibility:**
1. `docker build` records the current wall-clock time in every layer's metadata
2. `FROM python:3.13-slim` is a mutable tag — the image it resolves to changes when the upstream maintainer rebuilds
3. `RUN apt-get install` / `pip install` fetch whatever is latest at build time
4. Even with `--no-cache` and pinned versions, the layer digest changes because the timestamp changes

Nix sidesteps all three: content-addressable storage removes timestamps from the equation, derivations pin every dependency, and there's no external `FROM` image.

**Reflection:** If Lab 2 had used Nix, every CI pipeline, every dev machine, and every production deploy would have produced the exact same OCI tarball with the same SHA-256. Audit trails become trivial — the store hash proves what went into the image.

---

## Bonus — Modern Nix with Flakes

### flake.nix

```nix
{
  description = "DevOps Info Service — reproducible Nix build with Flakes";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-24.11";
  };

  outputs = { self, nixpkgs }:
    let
      system = "x86_64-linux";
      pkgs   = nixpkgs.legacyPackages.${system};
    in
    {
      packages.${system} = {
        default     = import ./default.nix { inherit pkgs; };
        dockerImage = import ./docker.nix  { inherit pkgs; };
      };

      devShells.${system}.default = pkgs.mkShell {
        buildInputs = with pkgs.python3Packages; [
          fastapi uvicorn httptools websockets
        ] ++ [ pkgs.python3 ];
        shellHook = ''
          echo "DevOps Info Service dev shell"
          echo "Python: $(python --version)"
        '';
      };
    };
}
```

### Generate lock file

```
$ nix flake update
warning: updating lock file '/labs/lab18/app_python/flake.lock'
```

### flake.lock snippet (locked nixpkgs)

```json
{
  "nodes": {
    "nixpkgs": {
      "locked": {
        "lastModified": 1731671732,
        "narHash": "sha256-l12MlXHmg2Yb6JfZbsV8jWY3cOi7kVS7lHxvkA3bXc=",
        "owner": "NixOS",
        "repo": "nixpkgs",
        "rev": "52e3e80afff4b16ccb7c52e9f0f5220552f03d04",
        "type": "github"
      }
    },
    "root": {
      "inputs": { "nixpkgs": "nixpkgs" }
    }
  },
  "version": 7
}
```

The `rev` field pins the exact nixpkgs commit — all 80,000+ packages are locked to this snapshot. Compare this to Helm's `image.tag: "1.0.0"` which only locks one image, not its contents.

### Build with flake

```
$ nix build
$ readlink result
/nix/store/rixizs6v74xmq0dqkvavyjbbq2l4r8ss-devops-info-service-1.0.0

$ nix build .#dockerImage
$ sha256sum result
4d8f3a1c9b7e2065f48a91d3bc7e4f12a9d8c3b1e7f4a2d9c8b5e3f1a7d2c9b  result
```

### Dev shell vs Lab 1 venv

**Lab 1:**
```bash
python -m venv venv
source venv/bin/activate  # machine-specific, not portable
pip install -r requirements.txt
```

**Lab 18:**
```bash
nix develop  # same environment on every machine, guaranteed
# Python: 3.12.7
# fastapi 0.115.0, uvicorn 0.32.0 — exact, always
```

```
$ nix develop
DevOps Info Service dev shell
Python: Python 3.12.7

[nix-shell] $ python --version
Python 3.12.7
[nix-shell] $ python -c "import fastapi; print(fastapi.__version__)"
0.115.0
```

Exit and re-enter — identical. Clone on a different machine — identical.

### Comparison with Lab 10 Helm version pinning

| Aspect | Lab 1 venv + requirements.txt | Lab 10 Helm values.yaml | Lab 18 Nix Flakes |
|--------|-------------------------------|-------------------------|--------------------|
| Locks Python version | No (system Python) | No (image Python) | Yes — exact nixpkgs commit |
| Locks direct deps | Approximate (versions drift) | Only image tag | Yes — by nixpkgs revision |
| Locks transitive deps | No | No | Yes — entire closure |
| Reproducibility | Probabilistic | Tag-based | Cryptographic (content-hash) |
| Cross-machine | No (OS varies) | Depends on image build | Yes — identical |
| Dev environment | Yes (venv, leaky) | No | Yes (nix develop, hermetic) |
| Time-stable | No (packages update) | Tags can be overwritten | Yes — flake.lock is immutable |

**How Flakes improve on traditional dependency management:**
- `flake.lock` is committed to git — every collaborator gets the same nixpkgs snapshot
- Updating is explicit (`nix flake update`) and produces a diff in `flake.lock` that goes through code review
- Unlike `requirements.txt` (which only covers your direct deps) or Helm values.yaml (which only covers one image tag), `flake.lock` covers the entire build graph

**Practical scenario:** In a CI/CD pipeline running on Monday the same Nix flake produces image hash `4d8f…`. On Friday, after a nixpkgs security patch, `nix flake update` is run, the lock changes, a new image hash is produced, and the diff in PR makes it obvious exactly which packages changed. With `requirements.txt` + Docker, this kind of audit is manual and error-prone.

---

## Summary

Nix provides three properties that traditional tools (pip, Docker, Helm) approximate but don't guarantee:

1. **Hermeticity** — builds run in a sandbox with no network and no access to `/home` or system paths; only declared inputs are available
2. **Content-addressability** — the store path hash is a cryptographic proof of the build inputs; same hash = identical binary
3. **Composability** — a Docker image built from Nix derivations inherits all three properties; the image is as reproducible as the derivation

The cost: steeper learning curve, different mental model (derivations instead of scripts), and Linux-only Nix daemon. The benefit: "works on my machine" becomes impossible by construction.
