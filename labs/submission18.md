# Lab 18 — Reproducible Builds with Nix

## Checklist

- [x] Task 1 — Build Reproducible Artifacts from Scratch (6 pts)
- [x] Task 2 — Reproducible Docker Images with Nix (4 pts)
- [x] Bonus Task — Modern Nix with Flakes (2 pts)

---

## Task 1 — Build Reproducible Python App (Revisiting Lab 1)

### 1.1 Nix Installation

```
$ nix --version
nix (Determinate Nix 3.20.0) 2.34.6
```

### 1.2 Application

Copied from Lab 1: `app_python/app.py` + `requirements.txt` (Flask + prometheus-client).

### 1.3 Nix Derivation (`labs/lab18/app_python/default.nix`)

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
    mkdir -p $out/bin $out/lib
    cp app.py $out/lib/app.py
    cat > $out/bin/devops-info-service << 'EOF'
    #!/bin/sh
    exec python3 "$out/lib/app.py" "$@"
    EOF
    chmod +x $out/bin/devops-info-service
    wrapProgram $out/bin/devops-info-service \
      --set PYTHONPATH "$PYTHONPATH"
  '';
}
```

**Key fields:**
- `buildPythonApplication` — Nix function for Python apps
- `propagatedBuildInputs` — exact packages from pinned nixpkgs (not PyPI)
- `format = "other"` — no setup.py needed
- `makeWrapper` — wraps script with correct PYTHONPATH

### 1.4 Reproducibility Proof

```bash
$ nix-build
/nix/store/b9qbbdfhv29nz8p2wmkazpl83n3v6dbq-devops-info-service-1.0.0

$ rm result && nix-build
/nix/store/b9qbbdfhv29nz8p2wmkazpl83n3v6dbq-devops-info-service-1.0.0

Identical: YES ✅
```

Same store path on both builds — Nix reused the cached result because inputs are identical.

### Nix Store Path Format

```
/nix/store/b9qbbdfhv29nz8p2wmkazpl83n3v6dbq-devops-info-service-1.0.0
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^  ^^^^^^^^^^^^^^^^^^^^^^^^
           Hash of ALL inputs                Name + version
```

The hash is computed from: source code + all dependencies (transitively) + build instructions + compiler flags. Same inputs → same hash → reuse existing build.

### Lab 1 (pip) vs Lab 18 (Nix) Comparison

| Aspect | Lab 1 (pip + venv) | Lab 18 (Nix) |
|--------|-------------------|--------------|
| Python version | System-dependent | Pinned in derivation |
| Dependency resolution | Runtime (`pip install`) | Build-time (pure) |
| Reproducibility | Approximate (with lockfiles) | Bit-for-bit identical |
| Portability | Requires same OS + Python | Works anywhere Nix runs |
| Binary cache | No | Yes (cache.nixos.org) |
| Isolation | Virtual environment | Sandboxed build |
| Store path | N/A | Content-addressable hash |

**Why `requirements.txt` provides weaker guarantees:**
- `requirements.txt` pins direct dependencies only
- Transitive dependencies (Flask's Werkzeug, Click, etc.) can drift
- Different Python versions on different machines
- `pip install` can produce different environments over time

**Reflection:** If Nix had been used from Lab 1, every developer would have gotten identical Python + Flask + all transitive deps, eliminating "works on my machine" issues entirely.

---

## Task 2 — Reproducible Docker Images (Revisiting Lab 2)

### 2.1 Lab 2 Dockerfile (Traditional)

```dockerfile
FROM python:3.13-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app.py .
EXPOSE 5000
CMD ["python", "app.py"]
```

### 2.2 Nix Docker Image (`labs/lab18/app_python/docker.nix`)

```nix
{ pkgs ? import <nixpkgs> {} }:

let
  app = import ./default.nix { inherit pkgs; };
in
pkgs.dockerTools.buildLayeredImage {
  name = "devops-info-service-nix";
  tag = "1.0.0";
  contents = [ app pkgs.coreutils ];
  config = {
    Cmd = [ "${app}/bin/devops-info-service" ];
    ExposedPorts = { "5000/tcp" = {}; };
    Env = [ "PORT=5000" "HOST=0.0.0.0" "DEBUG=False" ];
  };
  created = "1970-01-01T00:00:01Z";  # Fixed timestamp!
  maxLayers = 10;
}
```

**Critical:** `created = "1970-01-01T00:00:01Z"` — fixed epoch timestamp ensures reproducibility. Traditional Docker uses current time → different hash every build.

### 2.3 Reproducibility Comparison

**Nix image — same hash both builds:**
```bash
$ sha256sum result  # Build 1
87b5a6ce97c41b91b5b40aea78435e90b5ce8db319339791ffa8890cc8ab82bc

$ rm result && nix-build docker.nix && sha256sum result  # Build 2
87b5a6ce97c41b91b5b40aea78435e90b5ce8db319339791ffa8890cc8ab82bc

Identical: YES ✅
```

**Lab 2 Dockerfile — different timestamps:**
```
Lab2 created:  2026-05-13T18:11:19.480892971Z  ← real timestamp, changes every build
Nix created:   1970-01-01T00:00:01Z            ← fixed, always identical
```

![Docker images comparison](app_python/docs/n1.png)

![Timestamp comparison](app_python/docs/n2.png)

![Lab2 container running](app_python/docs/n3.png)

### Image Size Comparison

| Metric | Lab 2 Dockerfile | Lab 18 Nix dockerTools |
|--------|------------------|------------------------|
| Image size | 156 MB | 1.45 GB (includes full Nix closure) |
| Reproducibility | ❌ Different timestamps | ✅ Identical hashes |
| Base image | `python:3.13-slim` | No base image |
| Timestamps | Current time | Fixed epoch |

**Note on size:** The Nix image is larger because it includes the full Nix store closure (Python runtime + all deps as Nix store paths). In production, `buildImage` with `--no-gc-roots` or `nix2container` tool produces minimal images.

### Why Traditional Dockerfiles Can't Achieve Bit-for-Bit Reproducibility

1. **Timestamps** — Docker embeds build time in image metadata
2. **Base image drift** — `python:3.13-slim` tag can point to different content over time
3. **`apt-get`/`pip`** — installs latest packages unless pinned
4. **Layer ordering** — minor changes cascade to different layer hashes

**Reflection:** Redoing Lab 2 with Nix would mean: no base image dependency, guaranteed identical images in CI/CD, and ability to share binary cache so teammates never rebuild what's already built.

---

## Bonus — Modern Nix with Flakes

### flake.nix

```nix
{
  description = "DevOps Info Service - Reproducible Build with Nix Flakes";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-24.11";
  };

  outputs = { self, nixpkgs }:
    let
      system = "aarch64-darwin";  # Mac M-series
      pkgs = nixpkgs.legacyPackages.${system};
    in
    {
      packages.${system} = {
        default = import ./default.nix { inherit pkgs; };
        dockerImage = import ./docker.nix { inherit pkgs; };
      };

      devShells.${system}.default = pkgs.mkShell {
        buildInputs = with pkgs; [
          python313
          python313Packages.flask
          python313Packages.prometheus-client
        ];
      };
    };
}
```

### flake.lock (locked nixpkgs)

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

`rev: 50ab793...` — exact nixpkgs commit. This pins **all 80,000+ packages** in nixpkgs, not just direct dependencies.

### Lab 10 (Helm) vs Lab 18 (Flakes) Comparison

| Aspect | Lab 1 (requirements.txt) | Lab 10 (Helm values.yaml) | Lab 18 (Nix Flakes) |
|--------|--------------------------|---------------------------|---------------------|
| Locks Python version | ❌ | ❌ | ✅ |
| Locks dependencies | ⚠️ Approximate | ❌ Only image tag | ✅ Exact hashes |
| Locks build tools | ❌ | ❌ | ✅ |
| Reproducibility | ⚠️ Probabilistic | ⚠️ Tag-based | ✅ Cryptographic |
| Cross-machine | ❌ Varies | ⚠️ Depends on image | ✅ Identical |
| Dev environment | ✅ venv | ❌ | ✅ nix develop |
| Time-stable | ❌ | ⚠️ Tags can change | ✅ Locked forever |

**Reflection:** Flakes solve the "works on my machine" problem at the deepest level — not just pinning your app's dependencies, but the entire build toolchain. The `flake.lock` is the single source of truth for the entire dependency graph.
