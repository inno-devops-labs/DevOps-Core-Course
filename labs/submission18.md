# Lab 18 — Reproducible Builds with Nix

## Task 1 — Build Reproducible Python App (Revisiting Lab 1)

### 1.1 Nix Installation

```bash
curl --proto '=https' --tlsv1.2 -sSf -L https://install.determinate.systems/nix | sh -s -- install
# restart terminal
nix --version
```

![nix --version output](../k8s/img/lab18/nix-version.png)

Test basic usage:

```bash
nix run nixpkgs#hello
# Hello, world!
```

### 1.2 Application Preparation

The Lab 1 Python app is copied to `labs/lab18/app_python/`. It uses Flask with these dependencies:

```
Flask==3.1.0
python-json-logger==2.0.7
prometheus-client==0.23.1
```

**Problems with the Lab 1 approach (`pip install -r requirements.txt`):**
- Different Python versions on different machines
- `pip install` without hashes can pull different package versions
- Virtual environment is not portable
- Transitive dependencies (Werkzeug, Click, etc.) are not pinned

### 1.3 Nix Derivation

File: `labs/lab18/app_python/default.nix`

```nix
{ pkgs ? import <nixpkgs> {} }:

pkgs.python3Packages.buildPythonApplication {
  pname = "devops-info-service";
  version = "1.0.0";
  src = ./.;
  format = "other";

  propagatedBuildInputs = with pkgs.python3Packages; [
    flask
    python-json-logger
    prometheus-client
  ];

  nativeBuildInputs = [ pkgs.makeWrapper ];

  installPhase = ''
    mkdir -p $out/bin
    cp app.py $out/bin/devops-info-service
    wrapProgram $out/bin/devops-info-service \
      --set PYTHONPATH "$PYTHONPATH" \
      --prefix PATH : "${pkgs.python3}/bin"
  '';
}
```

**Key fields explained:**
- `buildPythonApplication` — Nix function that builds a Python app and handles PYTHONPATH wrapping
- `format = "other"` — tells Nix there is no `setup.py`; we handle installation in `installPhase`
- `propagatedBuildInputs` — Python packages from nixpkgs (versions pinned to the nixpkgs revision)
- `nativeBuildInputs = [ pkgs.makeWrapper ]` — tool available at build time to wrap the script
- `installPhase` — copies `app.py` to `$out/bin` and wraps it with the Python interpreter

### 1.4 Build and Reproducibility Proof

```bash
cd labs/lab18/app_python
nix-build
readlink result
# /nix/store/abc123xyz-devops-info-service-1.0.0
```

![nix-build output and store path](../k8s/img/lab18/nix-build.png)

**Force rebuild to prove reproducibility:**

```bash
STORE_PATH=$(readlink result)
nix-store --delete $STORE_PATH
rm result
nix-build
readlink result
# /nix/store/abc123xyz-devops-info-service-1.0.0  ← identical hash!
```

![Same store path after forced rebuild](../k8s/img/lab18/nix-rebuild-same-hash.png)

**Hash of output:**

```bash
nix-hash --type sha256 result
# abc123...  ← identical on any machine, any time
```

**Run the Nix-built app:**

```bash
PORT=5001 HOST=0.0.0.0 ./result/bin/devops-info-service
```

![App running from Nix-built binary](../k8s/img/lab18/app-running-nix.png)

### pip vs Nix Reproducibility Comparison

```bash
# Demonstrate pip's limitation with unpinned requirements:
echo "flask" > requirements-unpinned.txt
python -m venv venv1 && source venv1/bin/activate
pip install -r requirements-unpinned.txt
pip freeze | grep -i flask > freeze1.txt
deactivate

pip cache purge
python -m venv venv2 && source venv2/bin/activate
pip install -r requirements-unpinned.txt
pip freeze | grep -i flask > freeze2.txt
deactivate

diff freeze1.txt freeze2.txt
```

![diff showing same or different flask versions depending on pip cache state](../k8s/img/lab18/pip-diff.png)

**Nix store path format:**
```
/nix/store/<hash>-<name>-<version>
            ↑
            SHA256 of: all source code + all dependencies (transitively)
                       + build instructions + compiler flags
```

Same inputs → same hash → reuse cached build. **Guaranteed**, not probabilistic.

### Lab 1 vs Lab 18 Comparison

| Aspect | Lab 1 (pip + venv) | Lab 18 (Nix) |
|--------|-------------------|--------------|
| Python version | System-dependent | Pinned in derivation |
| Dependency resolution | Runtime (`pip install`) | Build-time (pure, sandboxed) |
| Transitive deps | Not pinned | Fully pinned via nixpkgs |
| Reproducibility | Approximate | Bit-for-bit identical |
| Portability | Requires same OS + Python | Works anywhere Nix runs |
| Binary cache | No | Yes (cache.nixos.org) |
| Store path | N/A | Content-addressable hash |

**Reflection:** If Nix had been used from Lab 1, every team member and CI server would have run the exact same Python binary with the exact same Flask version — no "works on my machine" issues, no surprise failures after `pip install` pulled a new Werkzeug version.

---

## Task 2 — Reproducible Docker Images (Revisiting Lab 2)

### 2.1 Lab 2 Dockerfile Reproducibility Test

```bash
docker build -t lab2-app:v1 ./app_python
docker inspect lab2-app:v1 | grep Created

sleep 5

docker build -t lab2-app:v2 ./app_python
docker inspect lab2-app:v2 | grep Created
```

![Different Created timestamps — same Dockerfile, different image hashes](../k8s/img/lab18/docker-timestamps.png)

Different timestamps → different image hashes despite identical source code.

### 2.2 Nix Docker Image

File: `labs/lab18/app_python/docker.nix`

```nix
{ pkgs ? import <nixpkgs> {} }:

let app = import ./default.nix { inherit pkgs; };
in
pkgs.dockerTools.buildLayeredImage {
  name = "devops-info-service-nix";
  tag = "1.0.0";
  contents = [ app pkgs.coreutils ];
  config = {
    Cmd = [ "${app}/bin/devops-info-service" ];
    ExposedPorts = { "5001/tcp" = {}; };
    Env = [ "PORT=5001" "HOST=0.0.0.0" "DEBUG=False" ];
  };
  created = "1970-01-01T00:00:01Z";  # Fixed timestamp — key for reproducibility
}
```

**Key fields:**
- `buildLayeredImage` — creates content-addressable layers; each layer is a Nix store path
- `contents` — the exact derivation from Task 1 (no `pip install` at image build time)
- `created = "1970-01-01T00:00:01Z"` — epoch timestamp eliminates timestamp variance. Using `"now"` would produce a different image hash on every build

```bash
cd labs/lab18/app_python
nix-build docker.nix
docker load < result
```

![docker load output — image loaded with tag](../k8s/img/lab18/docker-load.png)

### 2.3 Reproducibility Comparison

**Nix image — identical hashes on every build:**

```bash
rm result && nix-build docker.nix && sha256sum result
rm result && nix-build docker.nix && sha256sum result
```

![Two identical sha256sums from Nix builds](../k8s/img/lab18/nix-docker-same-hash.png)

**Lab 2 Dockerfile — different hashes:**

```bash
docker build -t lab2-app:test1 ./app_python/ && docker save lab2-app:test1 | sha256sum
sleep 2
docker build -t lab2-app:test2 ./app_python/ && docker save lab2-app:test2 | sha256sum
```

![Different sha256sums from Dockerfile builds](../k8s/img/lab18/lab2-docker-diff-hash.png)

**Both containers running simultaneously:**

```bash
docker run -d -p 5000:5001 --name lab2-container lab2-app:v1
docker run -d -p 5001:5001 --name nix-container devops-info-service-nix:1.0.0

curl http://localhost:5000/health   # Lab 2 version
curl http://localhost:5001/health   # Nix version
```

![Both containers responding to /health](../k8s/img/lab18/both-containers.png)

### Image Comparison

```bash
docker images | grep -E "lab2-app|devops-info-service-nix"
docker history lab2-app:v1
docker history devops-info-service-nix:1.0.0
```

![docker history — timestamps in Lab 2 vs deterministic in Nix](../k8s/img/lab18/docker-history.png)

| Metric | Lab 2 Dockerfile | Lab 18 Nix dockerTools |
|--------|------------------|------------------------|
| Image size | ~180 MB (`python:3.13-slim` base) | ~60–80 MB (minimal closure) |
| Reproducibility | Different hashes each build | Identical hashes always |
| Base image | `python:3.13-slim` (changes over time) | None — pure derivations |
| Layer caching | Timestamp-dependent | Content-addressable |
| Timestamps in history | Vary per build | Fixed `1970-01-01` |

**Why Dockerfiles can't achieve bit-for-bit reproducibility:**
1. `FROM python:3.13-slim` re-resolves the tag on every build (the underlying digest can change)
2. `RUN pip install -r requirements.txt` runs at build time — pip may pull patched packages
3. Build metadata (timestamps, builder ID) is baked into layers
4. `RUN apt-get update` always gets the latest package index

Nix eliminates all of these by using content-addressable store paths with no network access during the build.

**Reflection:** Redoing Lab 2 with Nix would give identical image tarballs across CI runs, making rollbacks auditable by hash rather than by tag.

---

## Bonus Task — Modern Nix with Flakes

### flake.nix

File: `labs/lab18/app_python/flake.nix` (see file for full content).

Key difference from `default.nix`: the nixpkgs input is pinned to a specific Git revision in `flake.lock`:

```bash
cd labs/lab18/app_python
nix flake update
```

![flake.lock generated — nixpkgs pinned to exact revision](../k8s/img/lab18/flake-lock.png)

`flake.lock` snippet:

```json
{
  "nodes": {
    "nixpkgs": {
      "locked": {
        "lastModified": 1704321342,
        "narHash": "sha256-abc123...",
        "owner": "NixOS",
        "repo": "nixpkgs",
        "rev": "52e3e80afff4b16ccb7c52e9f0f5220552f03d04",
        "type": "github"
      }
    }
  }
}
```

### Build with Flake

```bash
nix build              # default package (same as nix-build)
nix build .#dockerImage
./result/bin/devops-info-service
```

### Dev Shell vs Lab 1 venv

```bash
nix develop
python --version       # exact pinned version
python -c "import flask; print(flask.__version__)"
```

![nix develop — shellHook output and python version](../k8s/img/lab18/nix-develop.png)

| Aspect | Lab 1 (`venv + requirements.txt`) | Lab 10 (`Helm values.yaml`) | Flakes (`flake.lock`) |
|--------|-----------------------------------|-----------------------------|-----------------------|
| Locks Python version | No | No | Yes |
| Locks all dependencies | Approximate | Only image tag | Exact hashes |
| Reproducible dev env | No | No | Yes (`nix develop`) |
| Time-stable | No (packages drift) | Partially (tag can change) | Yes (locked forever) |
| Cross-machine | No | Partially | Yes |

### Lab 10 (Helm) vs Nix Flakes

Helm `values.yaml` pins the container image tag (`image.tag: "1.0.0"`) but does not lock:
- Python version inside the image
- Transitive Python dependencies
- Build tools used to create the image

`flake.lock` locks **all 80,000+ packages** in nixpkgs to a single Git commit. The combined approach is ideal:
1. `nix build .#dockerImage` → deterministic image tarball
2. `docker push` with the content hash as the tag
3. Helm `image.tag: "sha256-abc123..."` → Kubernetes pulls the exact bit-for-bit image

**Practical scenarios where `flake.lock` prevents "works on my machine":**
- A colleague upgrades their system Python; `nix develop` gives both of you the identical pinned version
- A new Flask release with a breaking change drops; the locked nixpkgs revision still has the old version
- CI runs on a different OS distribution; Nix sandbox ignores system libraries entirely
