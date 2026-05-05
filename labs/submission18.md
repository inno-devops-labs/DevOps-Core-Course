# Lab 18 — Reproducible Builds with Nix

## Task 1 — Build Reproducible Python App (6 pts)

### 1.1 Installation

```bash
curl --proto '=https' --tlsv1.2 -sSf -L https://install.determinate.systems/nix | sh -s -- install
```

```
nix (Determinate Nix 3.19.1) 2.34.6
```

Determinate Systems installer enables flakes by default.

### 1.2 Application

`labs/lab18/app_python/` contains the DevOps Info Service from Lab 1 (`app.py`, `requirements.txt`).

### 1.3 Nix Derivation (`default.nix`)

```nix
{ pkgs ? import <nixpkgs> {} }:

pkgs.python3Packages.buildPythonApplication {
  pname = "devops-info-service";
  version = "1.0.0";
  src = ./.;
  format = "other";

  propagatedBuildInputs = with pkgs.python3Packages; [
    flask
  ];

  nativeBuildInputs = [ pkgs.makeWrapper ];

  installPhase = ''
    mkdir -p $out/bin
    cp app.py $out/bin/devops-info-service
    chmod +x $out/bin/devops-info-service
    wrapProgram $out/bin/devops-info-service \
      --prefix PYTHONPATH : "${pkgs.python3Packages.flask}/${pkgs.python3.sitePackages}" \
      --set PYTHONPATH "$PYTHONPATH" \
      --prefix PATH : "${pkgs.python3}/bin"
  '';
}
```

**Fields explained:**
- `pname`, `version` — package identity
- `src = ./.` — use current directory as source
- `format = "other"` — no setup.py, so use custom installPhase
- `propagatedBuildInputs` — runtime dependencies (Flask), transitively pinned by nixpkgs
- `nativeBuildInputs` — build-time tools (makeWrapper creates the wrapper script)
- `installPhase` — copies `app.py` and wraps with correct Python path

**Build:**
```bash
nix-build
```

Store path: `/nix/store/f3il34mrcf8ks122k4p70asj02c2b9yz-devops-info-service-1.0.0`

### 1.4 Proving Reproducibility

**Same store path on every build:**
```
First build:  /nix/store/f3il34mrcf8ks122k4p70asj02c2b9yz-devops-info-service-1.0.0
Second build: /nix/store/f3il34mrcf8ks122k4p70asj02c2b9yz-devops-info-service-1.0.0
✅ IDENTICAL — reproducible!
```

**Output hash:**
```
nix-hash --type sha256 result
→ b8b91ceb5a11c051f934682c3d864ffdb1c9e2ffc39f7b34ec0dc0afc7ac4347
```

This hash is identical on any machine with the same nixpkgs revision.

**Why the store path format guarantees reproducibility:**
```
/nix/store/<hash>-<name>-<version>
```
The `<hash>` is computed from:
- All source code
- All dependencies (transitively — including Flask's own deps)
- Build instructions, compiler flags, everything

Same inputs → same hash → Nix reuses the existing build (cache hit). If rebuilt from scratch, the hash is still identical.

**Comparison with pip (Lab 1):**

```bash
# pip without pinning — gets whatever's latest
pip install flask
# → Flask==3.1.3 today, could be 3.2.0 next week
```

| Aspect | Lab 1 (pip + venv) | Lab 18 (Nix) |
|--------|-------------------|--------------|
| Python version | System-dependent | Pinned in derivation |
| Dependency resolution | Runtime (`pip install`) | Build-time (pure, sandboxed) |
| Transitive deps pinned | ❌ No (only direct) | ✅ Yes (all 80k+ nixpkgs) |
| Reproducibility | Approximate | Bit-for-bit identical |
| Portability | Requires same OS + Python | Works anywhere Nix runs |
| Binary cache | No | Yes (cache.nixos.org) |
| Store path | N/A | Content-addressable hash |

**Why `requirements.txt` gives weaker guarantees:**
`requirements.txt` pins direct dependencies but not transitive ones. Flask depends on Werkzeug, Click, Jinja2, etc. — these can change version between installs. Nix pins *everything* in the entire dependency closure.

**Reflection:** If we had used Nix from Lab 1, every team member and CI runner would have gotten identical Flask + Werkzeug + Python versions. No more "works on my machine" from a newer Werkzeug that changed a subtle API.

---

## Task 2 — Reproducible Docker Images (4 pts)

### 2.1 Lab 2 Dockerfile vs Nix

**Lab 2 `Dockerfile`** (traditional):
```dockerfile
FROM python:3.13-slim
RUN useradd -m appuser
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY app.py .
USER appuser
EXPOSE 5000
CMD ["python", "app.py"]
```

**Problems with reproducibility:**
- `python:3.13-slim` — base image changes over time (security patches)
- `pip install` — transitive deps not pinned
- Build timestamps are included in layers

### 2.2 Nix Docker Image (`docker.nix`)

```nix
{ pkgs ? import <nixpkgs> {} }:

let
  app = import ./default.nix { inherit pkgs; };
in
pkgs.dockerTools.buildLayeredImage {
  name = "devops-info-service-nix";
  tag = "1.0.0";
  contents = [ app pkgs.coreutils pkgs.bash ];
  config = {
    Cmd = [ "${app}/bin/devops-info-service" ];
    ExposedPorts = { "5000/tcp" = {}; };
    Env = [ "PORT=5000" "HOST=0.0.0.0" ];
  };
  created = "1970-01-01T00:00:01Z";  # Fixed timestamp = reproducible
}
```

**Key: `created = "1970-01-01T00:00:01Z"`** — without this, timestamps would differ between builds, breaking bit-for-bit reproducibility.

### 2.3 Reproducibility Comparison

**Nix image — identical SHA256 on every build:**
```
Build 1: 80590d05e1fdbdf4dc27eccd608d899d0151bd27aaff771413928af5abdc6065
Build 2: 80590d05e1fdbdf4dc27eccd608d899d0151bd27aaff771413928af5abdc6065
✅ Docker image hashes IDENTICAL
```

**Dockerfile — different hashes:**
```
Build 1: 6db08e249fd0baf074c8c30c13cde83be6441aafb8f794e03eae762738b13de4
Build 2: 26256bf5476280d3faca706091de03a93a1778f050de7bfc7339344d15229e13
❌ Different hashes (not reproducible)
```

Even with identical source code and Dockerfile, two builds have different image hashes because of timestamps in the layer metadata.

### Layer Analysis

**Dockerfile layers** (`docker history lab2-app:test1`):
```
CREATED          CREATED BY
38 seconds ago   CMD ["python" "app.py"]
38 seconds ago   COPY app.py .
38 seconds ago   pip install -r requirements.txt   27.8MB
21 hours ago     WORKDIR /app
```
Timestamps vary between builds — content-identical layers get different hashes.

**Nix layers** (`docker history devops-info-service-nix:1.0.0`):
```
CREATED   CREATED BY
N/A                    store paths: ['.../devops-info-service-1.0.0']
N/A                    store paths: ['.../python3.13-flask-3.1.2']
N/A                    store paths: ['.../python3.13-werkzeug-3.1.6']
```
`CREATED: N/A` — timestamp is the Unix epoch (1970), same forever.

### Comparison Table

| Aspect | Lab 2 Dockerfile | Lab 18 Nix dockerTools |
|--------|------------------|------------------------|
| Base images | `python:3.13-slim` (changes) | No base image |
| Timestamps | Different each build | Fixed `1970-01-01T00:00:01Z` |
| Reproducibility | ❌ Same Dockerfile → different images | ✅ Same `.nix` → identical images |
| Caching | Layer-based (timestamp-dependent) | Content-addressable |
| Image size | 237MB | 1.51GB (includes full Nix closure) |
| Security | Unknown base image deps | Exact, auditable deps |

**Note on size:** The Nix image is larger in this demo because it includes the full Nix store closure (Python runtime + all deps individually). In production, `buildLayeredImage` with `pkgs.dockerTools.buildImage` + `nix-tree` to prune the closure can produce minimal images comparable to multi-stage Docker builds.

**Reflection:** If we had used Nix for Lab 2, we would have had cryptographic proof that any deployment uses exactly the same binary as the tested build. This is critical for security audits and incident response.

---

## Bonus — Modern Nix with Flakes (2 pts)

### Flake (`flake.nix`)

```nix
{
  description = "DevOps Info Service - Reproducible Build with Nix Flakes";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-24.11";
  };

  outputs = { self, nixpkgs }:
    let
      system = "aarch64-darwin";
      pkgs = nixpkgs.legacyPackages.${system};
    in
    {
      packages.${system} = {
        default = import ./default.nix { inherit pkgs; };
        dockerImage = import ./docker.nix { inherit pkgs; };
      };

      devShells.${system}.default = pkgs.mkShell {
        buildInputs = with pkgs; [ python313 python313Packages.flask ];
        shellHook = ''
          echo "DevOps Info Service dev shell"
          echo "Python: $(python3 --version)"
        '';
      };
    };
}
```

### `flake.lock` — Exact Lock

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
      }
    }
  }
}
```

`flake.lock` pins the **exact Git revision** of nixpkgs (`50ab793...`). This means all 80,000+ packages are frozen. Anyone building from this flake gets identical results.

### Comparison with Lab 10 Helm Values

**Lab 10 (`values.yaml`):**
```yaml
image:
  repository: merkulovlr05/devops-info
  tag: "1.0.0"   # Only pins container tag
```

**Limitations:**
- Only pins the image tag — not what's *inside* the image
- Doesn't lock Python, Flask, or transitive deps
- `tag: "1.0.0"` can be overwritten (mutable tag)

**Nix Flakes (`flake.lock`):**
- Pins exact nixpkgs commit → all Python packages
- Content-addressed: the `narHash` proves integrity
- Immutable: you can't change what `rev: 50ab793` points to

| Aspect | Lab 1 (requirements.txt) | Lab 10 (Helm values.yaml) | Lab 18 (Nix Flakes) |
|--------|--------------------------|---------------------------|---------------------|
| Locks Python version | ❌ | ❌ | ✅ |
| Locks all transitive deps | ❌ | ❌ | ✅ |
| Cryptographic integrity | ❌ | ❌ | ✅ (narHash) |
| Dev environment | ✅ (venv) | ❌ | ✅ (nix develop) |
| Time-stable | ❌ | ⚠️ (tags can change) | ✅ (rev locked) |

**Combined approach:** Build image with Nix → load to Docker → reference in Helm by SHA digest:
```yaml
image:
  tag: "sha256:80590d05e1fdbdf4dc27eccd608d899d0151bd27aaff771413928af5abdc6065"
```
This gives Helm's declarative K8s management + Nix's perfect reproducibility.

**Reflection:** Flakes eliminate "works on my machine" by locking the entire universe of packages to a single Git commit. The `flake.lock` is the single source of truth — share it, pin it, and every machine gets identical builds. Traditional venvs and Helm values can approximate this but can't guarantee cryptographic integrity of the full dependency tree.
