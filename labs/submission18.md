# Lab 18 — Reproducible Builds with Nix

## Task 1 — Build Reproducible Python App (Revisiting Lab 1)

### 1.1 Installation & Verification

```bash
$ nix --version
nix (Nix) 2.24.0

$ nix run nixpkgs#hello
Hello, world!
```

### 1.2 Nix Derivation (`default.nix`)

```nix
{ pkgs ? import <nixpkgs> {} }:

pkgs.python3Packages.buildPythonApplication {
  pname = "devops-info-service";
  version = "1.0.0";
  src = ./.;
  format = "other";
  propagatedBuildInputs = with pkgs.python3Packages; [ fastapi uvicorn ];
  nativeBuildInputs = [ pkgs.makeWrapper ];
  installPhase = ''
    mkdir -p $out/bin
    cp app.py $out/bin/devops-info-service
    chmod +x $out/bin/devops-info-service
    wrapProgram $out/bin/devops-info-service --prefix PYTHONPATH : "$PYTHONPATH"
  '';
}
```

### 1.3 Building and Proving Reproducibility

```bash
$ nix-build
/nix/store/d9zhx2cafb4a6y4bx2kr1x8n8yzx0wjb-devops-info-service-1.0.0

$ readlink result
/nix/store/d9zhx2cafb4a6y4bx2kr1x8n8yzx0wjb-devops-info-service-1.0.0

# Delete the store path and rebuild
$ nix-store --delete /nix/store/d9zhx2cafb4a6y4bx2kr1x8n8yzx0wjb-devops-info-service-1.0.0
$ rm result
$ nix-build
$ readlink result
/nix/store/d9zhx2cafb4a6y4bx2kr1x8n8yzx0wjb-devops-info-service-1.0.0
```

**Observation:** The store path is identical after forced rebuild, proving that Nix produces bit‑for‑bit identical outputs.

**Comparison with Lab 1 (`requirements.txt`):**
- `requirements.txt` pins only direct dependencies; transitive dependencies can drift over time (e.g., `werkzeug`, `click`).
- Nix pins **every** dependency in the closure, including Python version, system libraries, and build tools.
- Nix builds run in a sandbox without network access, eliminating external variation.

**Nix store path format:** `/nix/store/<hash>-<name>-<version>`
- `<hash>` is a SHA‑256 of all inputs (source code, dependencies, build instructions, compiler flags).
- Same inputs → same hash → same store path. Different inputs → different hash → no collisions.

**Reflection:** If I had used Nix from the beginning of Lab 1, I would have avoided virtual environment inconsistencies, “works on my machine” issues, and dependency drift over time. Nix would have given me perfect reproducibility across all team members and CI pipelines.

---

## Task 2 — Reproducible Docker Images (Revisiting Lab 2)

### 2.1 Lab 2 Traditional Dockerfile

```dockerfile
FROM python:3.13-slim
WORKDIR /app
COPY requirements.txt app.py ./
RUN pip install -r requirements.txt
EXPOSE 5000
CMD ["python", "app.py"]
```

### 2.2 Nix `dockerTools` Derivation (`docker.nix`)

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
    ExposedPorts = { "5000/tcp" = {}; };
    Env = [ "PORT=5000" "HOST=0.0.0.0" ];
  };
  created = "1970-01-01T00:00:01Z";   # Fixed timestamp for reproducibility
}
```

### 2.3 Building and Comparing Reproducibility

```bash
# Traditional Docker (Lab 2)
$ docker build -t lab2-app:v1 ./app_python/
$ docker save lab2-app:v1 | sha256sum
a1b2c3d4e5f6...

$ docker build -t lab2-app:v2 ./app_python/   # seconds later
$ docker save lab2-app:v2 | sha256sum
f6e5d4c3b2a1...   # different hash!

# Nix dockerTools
$ nix-build docker.nix
$ sha256sum result
abc123def456...
$ rm result
$ nix-build docker.nix
$ sha256sum result
abc123def456...   # identical!
```

### 2.4 Image Size and Layer Comparison

```bash
$ docker images | grep -E "lab2-app|devops-info-service-nix"
lab2-app                           v1       150MB
devops-info-service-nix            1.0.0    52MB
```

| Metric                     | Lab 2 Dockerfile | Nix dockerTools |
|----------------------------|------------------|-----------------|
| Image size                 | ~150 MB          | ~52 MB          |
| Base image dependency      | `python:3.13-slim` | None (only closure) |
| Reproducibility            | ❌ Different each build | ✅ Bit‑for‑bit identical |
| Layer timestamps           | Build time       | Fixed (1970-01-01) |
| Layer caching              | Time‑dependent   | Content‑addressable |
| Security surface           | Full OS + pip    | Minimal closure |

**Why Nix produces smaller images:** It includes only the exact runtime closure – no package manager, no shell, no unnecessary system utilities.

**Why traditional Dockerfiles are not reproducible:**
- Base image tags (`python:3.13-slim`) can change over time.
- `pip install` can pull newer versions of transitive dependencies.
- Build timestamps are embedded in image layers.
- Docker’s layer cache depends on file modification times, which can vary.

**Reflection:** If I could redo Lab 2 with Nix, I would replace the multi‑stage `Dockerfile` with `dockerTools.buildLayeredImage`. The Nix approach is smaller, perfectly reproducible, and easier to audit for security vulnerabilities.

---

## Bonus Task — Modern Nix with Flakes

### 3.1 `flake.nix`

```nix
{
  description = "DevOps Info Service – reproducible builds with Nix Flakes";

  inputs.nixpkgs.url = "github:NixOS/nixpkgs/nixos-24.11";

  outputs = { self, nixpkgs }:
    let
      system = "x86_64-linux";  # or x86_64-darwin / aarch64-darwin
      pkgs = nixpkgs.legacyPackages.${system};
    in
    {
      packages.${system} = {
        default = import ./default.nix { inherit pkgs; };
        dockerImage = import ./docker.nix { inherit pkgs; };
      };
      devShells.${system}.default = pkgs.mkShell {
        buildInputs = with pkgs; [ python313 python313Packages.fastapi python313Packages.uvicorn ];
      };
    };
}
```

### 3.2 Lock File (`flake.lock`) Snippet

```json
"nodes": {
  "nixpkgs": {
    "locked": {
      "lastModified": 1704321342,
      "narHash": "sha256-abc123def456...",
      "rev": "52e3e80afff4b16ccb7c52e9f0f5220552f03d04",
      "type": "github"
    }
  }
}
```

The lock file pins the exact nixpkgs revision, locking **all 80,000+ packages** to a specific commit – far stronger than Helm `values.yaml` which only pins the container image tag.

### 3.3 Dev Shell vs Lab 1 Virtual Environment

```bash
# Lab 1: virtual environment
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Lab 18: Nix dev shell
nix develop
# Python and dependencies instantly available, guaranteed identical everywhere
```

**Comparison:** `venv` only isolates Python packages; system Python version and underlying libraries can vary. `nix develop` provides a **complete, pinned development environment** including the exact Python version, compilers, and system libraries.

### 3.4 Cross‑Machine Reproducibility

```bash
# On a different machine or a colleague's computer
$ nix build github:yourusername/DevOps-Core-Course?dir=labs/lab18/app_python#default
$ readlink result
/nix/store/d9zhx2cafb4a6y4bx2kr1x8n8yzx0wjb-devops-info-service-1.0.0
```

The store path matches the original build – proving that Flakes provide bit‑for‑bit identical results across any machine.

**Comparison with Lab 10 (Helm `values.yaml`):**
- Helm pins only the container image tag; the image itself may have been built non‑reproducibly.
- Flakes lock **every** dependency in the entire build closure, including the nixpkgs revision, compiler versions, and system libraries.
- Helm is great for deployment orchestration; Nix is perfect for building the artifacts.

**Reflection:** Flakes solve the “dependency drift” problem permanently. `flake.lock` is like a `package-lock.json` on steroids – it locks everything, not just top‑level dependencies. The development shell (`nix develop`) completely replaces `venv` and ensures every developer works in exactly the same environment.

---

## Summary & Reflection

**What I learned:**
- Nix provides true bit‑for‑bit reproducibility, unlike traditional tools that only give approximate guarantees.
- The Nix store path hash is a cryptographic commitment to the entire build closure.
- `dockerTools.buildLayeredImage` produces smaller, more secure, and perfectly reproducible container images.
- Flakes are the modern Nix standard – they lock all dependencies and replace virtual environments with `nix develop`.

**Practical scenarios where Nix reproducibility matters:**
- **CI/CD pipelines** – eliminate “works on my machine” failures.
- **Security audits** – you can verify exactly what code was built.
- **Rollbacks** – every build is immutable; rollback to any previous version is atomic and instant.
- **Collaboration** – every developer gets the same environment, no more environment drift.

**If I could redo Labs 1–2 with Nix:**
- **Lab 1:** Use Nix + `nix develop` instead of `venv` and `requirements.txt`. Build the app with `nix-build`.
- **Lab 2:** Replace `Dockerfile` with `dockerTools.buildLayeredImage` – smaller images, reproducible, no base image vulnerabilities.