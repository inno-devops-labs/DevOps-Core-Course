# Lab 18 — Reproducible Builds with Nix

![difficulty](https://img.shields.io/badge/difficulty-intermediate-yellow)
![topic](https://img.shields.io/badge/topic-Nix%20%26%20Reproducibility-blue)
![points](https://img.shields.io/badge/points-12-orange)

> **Goal:** Learn to create truly reproducible builds using Nix, eliminating "works on my machine" problems and achieving bit-for-bit reproducibility.
> **Deliverable:** A PR/MR from `feature/lab18` to the course repo with `labs/submission18.md` containing build artifacts, hash comparisons, Nix expressions, and analysis. Submit the PR/MR link via Moodle.

---

## Overview

In this lab you will practice:
- Installing Nix and understanding the Nix philosophy
- Writing Nix derivations to build software reproducibly
- Creating reproducible Docker images using Nix
- Using Nix Flakes for modern, declarative dependency management
- **Comparing Nix with your previous work from Labs 1-2**

**Why Nix?** Traditional build tools (Docker, npm, pip, etc.) claim to be reproducible, but they're not:
- `Dockerfile` with `apt-get install nodejs` gets different versions over time
- `pip install -r requirements.txt` without hash pinning can vary
- Docker builds include timestamps and vary across machines

**Nix solves this:** Every build is isolated in a sandbox with exact dependencies. The same Nix expression produces **identical binaries** on any machine, forever.

**Building on Your Work:** Throughout this lab, you'll revisit your DevOps Info Service from Lab 1 and compare:
- **Lab 1**: `requirements.txt` vs Nix derivations for dependency management
- **Lab 2**: Traditional `Dockerfile` vs Nix `dockerTools` for containerization
- **Lab 10** *(bonus task)*: Helm `values.yaml` version pinning vs Nix Flakes locking

---

## Prerequisites

- **Required:** Completed Labs 1-16 (all required course labs)
- **Key Labs Referenced:**
  - Lab 1: Python DevOps Info Service (you'll rebuild with Nix)
  - Lab 2: Docker containerization (you'll compare with Nix dockerTools)
  - Lab 10: Helm charts (you'll compare version pinning with Nix Flakes)
- Linux, macOS, or WSL2
- Basic understanding of package managers
- Your `app_python/` directory from Lab 1-2 available

---

## Tasks

### Task 1 — Build Reproducible Python App (Revisiting Lab 1) (6 pts)

**Objective:** Use Nix to build your DevOps Info Service from Lab 1 and compare Nix's reproducibility guarantees with traditional `pip install -r requirements.txt`.

**Why This Matters:** You've already built this app in Lab 1 using `requirements.txt`. Now you'll see how Nix provides **true reproducibility** that `pip` cannot guarantee - the same derivation produces bit-for-bit identical results across different machines and times.

#### 1.1: Install Nix Package Manager

> ⚠️ **Important Installation Requirements:**
> - Requires sudo/admin access on your machine
> - Creates `/nix` directory at system root (Linux/macOS) or `C:\nix` (Windows WSL)
> - Modifies shell configuration files (`~/.bashrc`, `~/.zshrc`, etc.)
> - Installation size: ~500MB-1GB for base system
> - **Cannot be installed in home directory only**
> - Uninstallation requires manual cleanup (see [official guide](https://nixos.org/manual/nix/stable/installation/uninstall.html))

1. **Install Nix using the Determinate Systems installer (recommended):**

   ```bash
   curl --proto '=https' --tlsv1.2 -sSf -L https://install.determinate.systems/nix | sh -s -- install
   ```

   > **Why Determinate Nix?** It enables flakes by default and provides better defaults for modern Nix usage.

   <details>
   <summary>🐧 Alternative: Official Nix installer</summary>

   ```bash
   sh <(curl -L https://nixos.org/nix/install) --daemon
   ```

   Then enable flakes by adding to `~/.config/nix/nix.conf`:
   ```
   experimental-features = nix-command flakes
   ```

   </details>

2. **Verify Installation:**

   ```bash
   nix --version
   ```

   You should see Nix 2.x or higher.

   **Restart your terminal** after installation to load Nix into your PATH.

3. **Test Basic Nix Usage:**

   ```bash
   # Try running a program without installing it
   nix run nixpkgs#hello
   ```

   This downloads and runs `hello` without installing it permanently.

#### 1.2: Prepare Your Python Application

1. **Copy your Lab 1 app to the lab18 directory:**

   ```bash
   mkdir -p labs/lab18/app_python
   cp -r app_python/* labs/lab18/app_python/
   cd labs/lab18/app_python
   ```

   You should have:
   - `app.py` - Your DevOps Info Service
   - `requirements.txt` - Your Python dependencies (Flask/FastAPI)

2. **Review your traditional workflow (Lab 1):**

   Recall how you built this in Lab 1:
   ```bash
   python -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   python app.py
   ```

   **Problems with this approach:**
   - Different Python versions on different machines
   - `pip install` without hashes can pull different package versions
   - Virtual environment is not portable
   - No guarantee of reproducibility over time

#### 1.3: Write a Nix Derivation for Your Python App

1. **Create a Nix derivation:**

   Create `default.nix` in `labs/lab18/app_python/`:

   <details>
   <summary>📚 Where to learn Nix Python derivation syntax</summary>

   - [nix.dev - Python](https://nix.dev/tutorials/nixos/building-and-running-python-apps)
   - [nixpkgs Python documentation](https://nixos.org/manual/nixpkgs/stable/#python)
   - [Nix Pills - Chapter 6: Our First Derivation](https://nixos.org/guides/nix-pills/our-first-derivation.html)

   **Key concepts you need:**
   - `python3Packages.buildPythonApplication` - Function to build Python apps
   - `propagatedBuildInputs` - Python dependencies (Flask/FastAPI)
   - `makeWrapper` - Wraps Python script with interpreter
   - `pname` - Package name
   - `version` - Package version
   - `src` - Source code location (use `./.` for current directory)
   - `format = "other"` - For apps without setup.py

   **Translating requirements.txt to Nix:**
   Your Lab 1 `requirements.txt` might have:
   ```
   Flask==3.1.0
   Werkzeug>=2.0
   click
   ```

   In Nix, you reference packages from nixpkgs (not exact PyPI versions):
   - `Flask==3.1.0` → `pkgs.python3Packages.flask`
   - `fastapi==0.115.0` → `pkgs.python3Packages.fastapi`
   - `uvicorn[standard]` → `pkgs.python3Packages.uvicorn`

   **Note:** Nix uses versions from the pinned nixpkgs, not PyPI directly. This is intentional for reproducibility.

   **Example structure (Flask):**
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

       # Wrap with Python interpreter so it can execute
       wrapProgram $out/bin/devops-info-service \
         --prefix PYTHONPATH : "$PYTHONPATH"
     '';
   }
   ```

   **Example for FastAPI:**
   ```nix
   propagatedBuildInputs = with pkgs.python3Packages; [
     fastapi
     uvicorn
   ];
   ```

   **Hint:** If you get "command not found" errors, make sure you're using `makeWrapper` in the installPhase.

   </details>

2. **Build your application with Nix:**

   ```bash
   nix-build
   ```

   This creates a `result` symlink pointing to the Nix store path.

3. **Run the Nix-built application:**

   ```bash
   ./result/bin/devops-info-service
   ```

   Visit `http://localhost:5000` (or your configured port) - it should work identically to your Lab 1 version!

#### 1.4: Prove Reproducibility (Compare with Lab 1 approach)

1. **Record the Nix store path:**

   ```bash
   readlink result
   ```

   Note the store path (e.g., `/nix/store/abc123-devops-info-service-1.0.0/`)

2. **Build again and compare:**

   ```bash
   rm result
   nix-build
   readlink result
   ```

   **Observation:** The store path is **identical**! But wait - did Nix rebuild it or reuse it?

   **Answer: Nix reused the cached build!** Same inputs = same hash = reuse existing store path.

3. **Force an actual rebuild to prove reproducibility:**

   ```bash
   # First, find your build's store path
   STORE_PATH=$(readlink result)
   echo "Original store path: $STORE_PATH"

   # Delete it from the Nix store
   nix-store --delete $STORE_PATH

   # Now rebuild (this forces actual compilation)
   rm result
   nix-build
   readlink result
   ```

   **Observation:** Same store path returns! Nix rebuilt it from scratch and got the exact same hash.

3. **Compare with traditional pip approach:**

   **Demonstrate pip's limitations:**

   ```bash
   # Test 1: Install without version pins (shows immediate non-reproducibility)
   echo "flask" > requirements-unpinned.txt  # No version specified

   python -m venv venv1
   source venv1/bin/activate
   pip install -r requirements-unpinned.txt
   pip freeze | grep -i flask > freeze1.txt
   deactivate

   # Simulate time passing: clear pip cache
   pip cache purge 2>/dev/null || rm -rf ~/.cache/pip

   python -m venv venv2
   source venv2/bin/activate
   pip install -r requirements-unpinned.txt
   pip freeze | grep -i flask > freeze2.txt
   deactivate

   # Compare Flask versions
   diff freeze1.txt freeze2.txt
   ```

   **Observation:**
   - Without version pins, you get whatever's latest
   - **Even with pinned versions** in requirements.txt, you only pin direct dependencies
   - Transitive dependencies (dependencies of your dependencies) can still drift
   - Over weeks/months, `pip install -r requirements.txt` can produce different environments

   **The fundamental problem:**
   ```
   Lab 1 approach: requirements.txt pins what YOU install
   Problem: Doesn't pin what FLASK installs (Werkzeug, Click, etc.)
   Result: Different machines = different transitive dependency versions

   Nix approach: Pins EVERYTHING in the entire dependency tree
   Result: Bit-for-bit identical on all machines, forever
   ```

4. **Understand Nix's caching behavior:**

   **Key insight:** Nix uses content-addressable storage:
   ```
   Store path format: /nix/store/<hash>-<name>-<version>
   Example: /nix/store/abc123xyz-devops-info-service-1.0.0

   The <hash> is computed from:
   - All source code
   - All dependencies (transitively!)
   - Build instructions
   - Compiler flags
   - Everything needed to reproduce the build

   Same inputs → Same hash → Reuse existing build (cache hit)
   Different inputs → Different hash → New build required
   ```

5. **Nix's guarantee:**

   ```bash
   # Hash the entire Nix output
   nix-hash --type sha256 result
   ```

   This hash will be **identical** on any machine, any time, forever - if the inputs don't change.

   This is why Nix can safely share binary caches (cache.nixos.org) - the hash proves the content!

**📊 Comparison Table - Lab 1 vs Lab 18:**

| Aspect | Lab 1 (pip + venv) | Lab 18 (Nix) |
|--------|-------------------|--------------|
| Python version | System-dependent | Pinned in derivation |
| Dependency resolution | Runtime (`pip install`) | Build-time (pure) |
| Reproducibility | Approximate (with lockfiles) | Bit-for-bit identical |
| Portability | Requires same OS + Python | Works anywhere Nix runs |
| Binary cache | No | Yes (cache.nixos.org) |
| Isolation | Virtual environment | Sandboxed build |
| Store path | N/A | Content-addressable hash |

#### 1.5: Optional - Go Application (If you completed Lab 1 Bonus)

<details>
<summary>🎁 For students who built the Go version in Lab 1 Bonus</summary>

If you implemented the compiled language bonus in Lab 1, you can also build it with Nix:

1. **Copy your Go app:**
   ```bash
   mkdir -p labs/lab18/app_go
   cp -r app_go/* labs/lab18/app_go/
   cd labs/lab18/app_go
   ```

2. **Create `default.nix` for Go:**
   ```nix
   { pkgs ? import <nixpkgs> {} }:

   pkgs.buildGoModule {
     pname = "devops-info-service-go";
     version = "1.0.0";
     src = ./.;

     vendorHash = null;  # or use pkgs.lib.fakeHash if you have dependencies
   }
   ```

3. **Build and compare binary size:**
   ```bash
   nix-build
   ls -lh result/bin/
   ```

   Compare this with your multi-stage Docker build from Lab 2 Bonus!

</details>

In `labs/submission18.md`, document:
- Installation steps and verification output
- Your `default.nix` file with explanations of each field
- Store path from multiple builds (prove they're identical)
- Comparison table: `pip install` vs Nix derivation
- Why does `requirements.txt` provide weaker guarantees than Nix?
- Screenshots showing your Lab 1 app running from Nix-built version
- Explanation of the Nix store path format and what each part means
- **Reflection:** How would Nix have helped in Lab 1 if you had used it from the start?

---

### Task 2 — Reproducible Docker Images (Revisiting Lab 2) (4 pts)

**Objective:** Use Nix's `dockerTools` to containerize your DevOps Info Service and compare with your traditional Dockerfile from Lab 2.

**Why This Matters:** In Lab 2, you created a `Dockerfile` that built your Python app. While Docker provides isolation, it's **not reproducible**:
- Build timestamps differ between builds
- Base image tags like `python:3.13-slim` can point to different versions over time
- `apt-get` installs latest packages, which change
- Two builds of the same Dockerfile can produce different image hashes

Nix's `dockerTools` creates **truly reproducible** container images with content-addressable layers.

#### 2.1: Review Your Lab 2 Dockerfile

1. **Find your Dockerfile from Lab 2:**

   ```bash
   # From repository root directory
   cat app_python/Dockerfile
   ```

   You likely have something like:
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

   <details>
   <summary>💡 Don't have your Lab 2 Dockerfile?</summary>

   If you lost your Lab 2 work, create a minimal Dockerfile now:

   ```dockerfile
   FROM python:3.13-slim
   WORKDIR /app
   COPY requirements.txt app.py ./
   RUN pip install -r requirements.txt
   EXPOSE 5000
   CMD ["python", "app.py"]
   ```

   Save as `app_python/Dockerfile`.

   </details>

2. **Test Lab 2 Dockerfile reproducibility:**

   ```bash
   # Make sure you're in repository root
   cd ~/path/to/DevOps-Core-Course  # Adjust to your path

   # Build from app_python directory
   docker build -t lab2-app:v1 ./app_python
   docker inspect lab2-app:v1 | grep Created

   # Wait a few seconds, then rebuild
   sleep 5
   docker build -t lab2-app:v2 ./app_python
   docker inspect lab2-app:v2 | grep Created
   ```

   **Observation:** Different creation timestamps! The image hashes are different even though the content is identical.

#### 2.2: Build Docker Image with Nix

1. **Create a Nix Docker image using `dockerTools`:**

   Create `labs/lab18/app_python/docker.nix`:

   <details>
   <summary>📚 Where to learn about dockerTools</summary>

   - [nix.dev - Building Docker images](https://nix.dev/tutorials/nixos/building-and-running-docker-images.html)
   - [nixpkgs dockerTools documentation](https://ryantm.github.io/nixpkgs/builders/images/dockertools/)

   **Key concepts:**
   - `pkgs.dockerTools.buildLayeredImage` - Builds efficient layered images
   - `name` - Image name
   - `tag` - Image tag (optional, defaults to latest)
   - `contents` - Packages/derivations to include in the image
   - `config.Cmd` - Default command to run
   - `config.ExposedPorts` - Ports to expose

   **Critical for reproducibility:**
   - **DO NOT** use `created = "now"` - this breaks reproducibility!
   - **DO** use `created = "1970-01-01T00:00:01Z"` for reproducible builds
   - **DO** use exact derivations (from Task 1) instead of arbitrary packages

   **Example structure:**
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

     created = "1970-01-01T00:00:01Z";  # Reproducible timestamp
   }
   ```

   </details>

2. **Build the Nix Docker image:**

   ```bash
   cd labs/lab18/app_python
   nix-build docker.nix
   ```

   This creates a tarball in `result`.

3. **Load into Docker:**

   ```bash
   docker load < result
   ```

   Output shows the image was loaded with a specific tag.

4. **Run both containers side-by-side:**

   ```bash
   # First, clean up any existing containers to avoid port conflicts
   docker stop lab2-container nix-container 2>/dev/null || true
   docker rm lab2-container nix-container 2>/dev/null || true

   # Run Lab 2 traditional Docker image on port 5000
   docker run -d -p 5000:5000 --name lab2-container lab2-app:v1

   # Run Nix-built image on port 5001 (mapped to container's 5000)
   docker run -d -p 5001:5000 --name nix-container devops-info-service-nix:1.0.0
   ```

   Test both:
   ```bash
   curl http://localhost:5000/health  # Lab 2 version
   curl http://localhost:5001/health  # Nix version
   ```

   Both should work identically!

   **Troubleshooting:**
   - If port 5000 is in use: `lsof -i :5000` to find the process
   - Container won't start: Check logs with `docker logs lab2-container`
   - Permission denied: Make sure Docker daemon is running

#### 2.3: Compare Reproducibility - Lab 2 vs Lab 18

**Test 1: Rebuild Reproducibility**

1. **Rebuild Nix image multiple times:**

   ```bash
   rm result
   nix-build docker.nix
   sha256sum result

   rm result
   nix-build docker.nix
   sha256sum result
   ```

   **Observation:** Identical SHA256 hashes! The tarball is bit-for-bit identical.

2. **Compare with Lab 2 Dockerfile:**

   ```bash
   # Make sure you're in repository root
   # Build Lab 2 Dockerfile twice and compare saved image hashes

   docker build -t lab2-app:test1 ./app_python/
   docker save lab2-app:test1 | sha256sum

   sleep 2  # Wait a moment

   docker build -t lab2-app:test2 ./app_python/
   docker save lab2-app:test2 | sha256sum
   ```

   **Observation:** Different hashes! Even though the Dockerfile and source are identical, Lab 2's approach is not reproducible.

**Test 2: Image Size Comparison**

```bash
docker images | grep -E "lab2-app|devops-info-service-nix"
```

Create a comparison table:

| Metric | Lab 2 Dockerfile | Lab 18 Nix dockerTools |
|--------|------------------|------------------------|
| Image size | ~150MB (with python:3.13-slim) | ~50-80MB (minimal closure) |
| Reproducibility | ❌ Different hashes each build | ✅ Identical hashes |
| Build caching | Layer-based (timestamp-dependent) | Content-addressable |
| Base image dependency | Yes (python:3.13-slim) | No base image needed |

**Test 3: Layer Analysis**

1. **Examine Lab 2 image layers:**

   ```bash
   docker history lab2-app:v1
   ```

   Note the timestamps in the "CREATED" column - they vary between builds!

2. **Examine Nix image layers:**

   ```bash
   docker history devops-info-service-nix:1.0.0
   ```

   Nix uses content-addressable layers - same content = same layer hash.

#### 2.4: Advanced Comparison - Multi-Stage Builds

<details>
<summary>🎁 Optional: Compare with Lab 2 Bonus Multi-Stage Build</summary>

If you completed the Lab 2 bonus with Go and multi-stage builds, you can compare:

**Your Lab 2 multi-stage Dockerfile:**
```dockerfile
FROM golang:1.22 AS builder
COPY . .
RUN go build -o app main.go

FROM alpine:latest
COPY --from=builder /app/app /app
ENTRYPOINT ["/app"]
```

**Problems:**
- `golang:1.22` and `alpine:latest` change over time
- Build includes timestamps
- Not reproducible across machines

**Nix equivalent (fully reproducible):**
```nix
pkgs.dockerTools.buildLayeredImage {
  name = "go-app-nix";
  contents = [ goApp ];  # Built in Task 1.5
  config.Cmd = [ "${goApp}/bin/go-app" ];
  created = "1970-01-01T00:00:01Z";
}
```

Same result size, but **fully reproducible**!

</details>

**📊 Comprehensive Comparison - Lab 2 vs Lab 18:**

| Aspect | Lab 2 Traditional Dockerfile | Lab 18 Nix dockerTools |
|--------|------------------------------|------------------------|
| **Base images** | `python:3.13-slim` (changes over time) | No base image (pure derivations) |
| **Timestamps** | Different on each build | Fixed or deterministic |
| **Package installation** | `pip install` at build time | Nix store paths (immutable) |
| **Reproducibility** | ❌ Same Dockerfile → Different images | ✅ Same docker.nix → Identical images |
| **Caching** | Layer-based (breaks on timestamp) | Content-addressable (perfect caching) |
| **Image size** | ~150MB+ with full base image | ~50-80MB with minimal closure |
| **Portability** | Requires Docker | Requires Nix (then loads to Docker) |
| **Security** | Base image vulnerabilities | Minimal dependencies, easier auditing |
| **Lab 2 Learning** | Best practices, non-root user | Build on Lab 2 knowledge |

In `labs/submission18.md`, document:
- Your `docker.nix` file with explanations of each field
- Side-by-side comparison: Lab 2 Dockerfile vs Nix docker.nix
- SHA256 hash comparison proving Nix reproducibility
- Image size comparison table with analysis
- `docker history` output for both approaches
- Screenshots showing both containers running simultaneously
- **Analysis:** Why can't traditional Dockerfiles achieve bit-for-bit reproducibility?
- **Reflection:** If you could redo Lab 2 with Nix, what would you do differently?
- Practical scenarios where Nix's reproducibility matters (CI/CD, security audits, rollbacks)

---

### Bonus Task — Modern Nix with Flakes (Includes Lab 10 Comparison) (2 pts)

**Objective:** Modernize your Nix expressions using Flakes for better dependency locking and reproducibility. Compare Nix Flakes with Helm's version pinning approach from Lab 10.

**Why This Matters:** Nix Flakes are the modern standard (2026) for Nix projects. They provide:
- Automatic dependency locking via `flake.lock`
- Standardized project structure
- Better reproducibility across time
- Easier sharing and collaboration

**Comparison with Lab 10:** In Lab 10 (Helm), you used `values.yaml` to pin image versions. Flakes take this concept further by locking **all** dependencies, not just container images.

#### Bonus.1: Convert to Flake

1. **Create a `flake.nix`:**

   Create `labs/lab18/app_python/flake.nix`:

   <details>
   <summary>📚 Where to learn about Flakes</summary>

   - [Zero to Nix - Flakes](https://zero-to-nix.com/concepts/flakes)
   - [NixOS Wiki - Flakes](https://wiki.nixos.org/wiki/Flakes)
   - [Nix Flakes explained](https://nix.dev/concepts/flakes)

   **Key structure:**
   ```nix
   {
     description = "DevOps Info Service - Reproducible Build";

     inputs = {
       nixpkgs.url = "github:NixOS/nixpkgs/nixos-24.11";  # Pin exact nixpkgs version
     };

     outputs = { self, nixpkgs }:
       let
         # ⚠️ Architecture note: This example uses x86_64-linux
         # - Works on: Linux (x86_64), WSL2
         # - Mac Intel: Change to "x86_64-darwin"
         # - Mac M1/M2/M3: Change to "aarch64-darwin"
         # - For multi-system support, see: https://github.com/numtide/flake-utils
         system = "x86_64-linux";
         pkgs = nixpkgs.legacyPackages.${system};
       in
       {
         packages.${system} = {
           default = import ./default.nix { inherit pkgs; };
           dockerImage = import ./docker.nix { inherit pkgs; };
         };

         # Development shell with all dependencies
         devShells.${system}.default = pkgs.mkShell {
           buildInputs = with pkgs; [
             python313
             python313Packages.flask  # or fastapi
           ];
         };
       };
   }
   ```

   **Platform-specific adjustments:**
   - **Linux/WSL2**: Use `system = "x86_64-linux";` (shown above)
   - **Mac Intel**: Use `system = "x86_64-darwin";`
   - **Mac ARM (M1/M2/M3)**: Use `system = "aarch64-darwin";`

   **Hint:** Use `nix flake init` to generate a template, then modify it.

   </details>

2. **Generate lock file:**

   ```bash
   cd labs/lab18/app_python
   nix flake update
   ```

   This creates `flake.lock` with pinned dependencies.

3. **Build using flake:**

   ```bash
   nix build                          # Builds default package
   nix build .#dockerImage           # Builds Docker image
   ./result/bin/devops-info-service  # Run the app
   ```

#### Bonus.2: Compare with Lab 10 Helm Values

**Lab 10 Helm approach to version pinning:**

In `k8s/mychart/values.yaml`:
```yaml
image:
  repository: yourusername/devops-info-service
  tag: "1.0.0"           # Pin specific version
  pullPolicy: IfNotPresent

# Environment-specific overrides
# values-prod.yaml:
image:
  tag: "1.0.0"           # Explicit version for prod
```

**Limitations:**
- Only pins the container image tag
- Doesn't lock Python dependencies inside the image
- Doesn't lock Helm chart dependencies
- Image tag `1.0.0` could point to different content if rebuilt

**Nix Flakes approach:**

`flake.lock` locks **everything**:
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

This locks:
- ✅ Exact nixpkgs revision (all 80,000+ packages)
- ✅ Python version and all dependencies
- ✅ Build tools and compilers
- ✅ Everything in the closure

**Combined Approach:**

You can use both together!
1. Build reproducible image with Nix: `nix build .#dockerImage`
2. Load to Docker and tag: `docker load < result`
3. Reference in Helm with content hash: `image.tag: "sha256-abc123..."`

This gives you:
- Helm's declarative Kubernetes deployment
- Nix's perfect reproducibility for the image

Create a comparison table in your submission.

#### Bonus.3: Test Cross-Machine Reproducibility

1. **Commit your flake to git:**

   ```bash
   git add flake.nix flake.lock default.nix docker.nix
   git commit -m "feat: add Nix flake for reproducible builds"
   git push
   ```

2. **Test on another machine or ask a classmate:**

   ```bash
   # Build directly from GitHub
   nix build github:yourusername/DevOps-Core-Course?dir=labs/lab18/app_python#default
   ```

3. **Compare store paths:**

   ```bash
   readlink result
   ```

   Both machines should get **identical store paths** - same hash, same content!

#### Bonus.4: Add Development Shell

1. **Enter the dev shell:**

   ```bash
   nix develop
   ```

   This gives you an isolated environment with exact Python version and dependencies.

2. **Compare with Lab 1 virtual environment:**

   **Lab 1 approach:**
   ```bash
   python -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

   **Lab 18 Nix approach:**
   ```bash
   nix develop
   # Python and all dependencies instantly available
   # Same environment on every machine
   ```

3. **Try it:**

   ```bash
   nix develop
   python --version     # Exact pinned version
   python -c "import flask; print(flask.__version__)"
   ```

   Exit and enter again - same versions, always!

**📊 Dependency Management Comparison:**

| Aspect | Lab 1 (venv + requirements.txt) | Lab 10 (Helm values.yaml) | Lab 18 (Nix Flakes) |
|--------|--------------------------------|---------------------------|---------------------|
| **Locks Python version** | ❌ Uses system Python | ❌ Uses image Python | ✅ Pinned in flake |
| **Locks dependencies** | ⚠️ Approximate (versions drift) | ❌ Only image tag | ✅ Exact hashes |
| **Locks build tools** | ❌ No | ❌ No | ✅ Yes |
| **Reproducibility** | ⚠️ Probabilistic | ⚠️ Tag-based | ✅ Cryptographic |
| **Cross-machine** | ❌ Varies | ⚠️ Depends on image | ✅ Identical |
| **Dev environment** | ✅ Yes (venv) | ❌ No | ✅ Yes (nix develop) |
| **Time-stable** | ❌ Packages update | ⚠️ Tags can change | ✅ Locked forever |

In `labs/submission18.md`, document:
- Your complete `flake.nix` with explanations
- `flake.lock` snippet showing locked dependencies (especially nixpkgs revision)
- Build outputs from `nix build`
- Proof that builds are identical across machines/time
- Dev shell experience: Compare `nix develop` vs Lab 1's `venv`
- Comparison with Lab 10 Helm values.yaml approach (Bonus.2)
- **Reflection:** How do Flakes improve upon traditional dependency management?
- Practical scenarios where flake.lock prevented a "works on my machine" problem

---

## Troubleshooting Common Issues

<details>
<summary>🔧 Python app doesn't run: "command not found" or "No such file or directory"</summary>

**Problem:** Your `app.py` doesn't have a shebang line and isn't being wrapped with Python interpreter.

**Solution:** Ensure you're using `makeWrapper` in your `default.nix`:

```nix
nativeBuildInputs = [ pkgs.makeWrapper ];

installPhase = ''
  mkdir -p $out/bin
  cp app.py $out/bin/devops-info-service

  wrapProgram $out/bin/devops-info-service \
    --prefix PYTHONPATH : "$PYTHONPATH"
'';
```

Alternatively, add a shebang to your `app.py`:
```python
#!/usr/bin/env python3
```

</details>

<details>
<summary>🔧 "error: hash mismatch in fixed-output derivation"</summary>

**Problem:** The hash you specified doesn't match the actual content.

**Solution:**
1. Use `pkgs.lib.fakeHash` initially to get the correct hash
2. Nix will fail and tell you the expected hash
3. Replace `fakeHash` with the correct hash from the error message

Example:
```nix
vendorHash = pkgs.lib.fakeHash;  # Start with this
# Error will say: "got: sha256-abc123..."
# Then use: vendorHash = "sha256-abc123...";
```

</details>

<details>
<summary>🔧 Docker image doesn't load or fails to run</summary>

**Common causes:**

1. **Image tarball not built:** Check `result` is a `.tar.gz` file
   ```bash
   file result
   # Should show: gzip compressed data
   ```

2. **Wrong Cmd path:** Verify the app path in docker.nix
   ```nix
   config.Cmd = [ "${app}/bin/devops-info-service" ];
   # Make sure this matches your installPhase output
   ```

3. **Missing dependencies in image:** Add required packages to `contents`
   ```nix
   contents = [ app pkgs.coreutils ];  # Add tools if needed
   ```

</details>

<details>
<summary>🔧 Port conflicts when running containers</summary>

**Problem:** Port 5000 or 5001 already in use.

**Solution:**
```bash
# Find what's using the port
lsof -i :5000

# Stop old containers
docker stop $(docker ps -aq) 2>/dev/null

# Or use different ports
docker run -d -p 5002:5000 --name my-container my-image
```

</details>

<details>
<summary>🔧 Flakes don't work: "experimental features" error</summary>

**Problem:** Flakes not enabled in your Nix configuration.

**Solution:**
```bash
# Check if flakes are enabled
nix flake --help

# If error, enable flakes:
mkdir -p ~/.config/nix
echo "experimental-features = nix-command flakes" >> ~/.config/nix/nix.conf

# Restart terminal
```

</details>

<details>
<summary>🔧 Build fails on macOS: "unsupported system"</summary>

**Problem:** Flake hardcodes `x86_64-linux` but you're on macOS.

**Solution:** Change the system in `flake.nix`:
```nix
# For Mac Intel:
system = "x86_64-darwin";

# For Mac M1/M2/M3:
system = "aarch64-darwin";
```

</details>

<details>
<summary>🔧 "cannot build derivation: no builder for this system"</summary>

**Problem:** Trying to build Linux binaries on macOS or vice versa.

**Solution:** Either:
1. Match your system architecture in the flake
2. Use Docker builds which work cross-platform
3. Use Nix's cross-compilation features (advanced)

</details>

<details>
<summary>🔧 Don't have Lab 1/2 artifacts to use</summary>

**No problem!** Create a minimal example:

1. **Create simple Flask app:**
   ```python
   # app.py
   from flask import Flask, jsonify
   app = Flask(__name__)

   @app.route('/health')
   def health():
       return jsonify({"status": "healthy"})

   if __name__ == '__main__':
       app.run(host='0.0.0.0', port=5000)
   ```

2. **Create requirements.txt:**
   ```
   flask
   ```

3. **Create basic Dockerfile:**
   ```dockerfile
   FROM python:3.13-slim
   WORKDIR /app
   COPY requirements.txt app.py ./
   RUN pip install -r requirements.txt
   EXPOSE 5000
   CMD ["python", "app.py"]
   ```

Now you can proceed with the lab using these minimal examples!

</details>

---

## How to Submit

1. Create a branch for this lab and push it:

   ```bash
   git switch -c feature/lab18
   # create labs/submission18.md with your findings
   git add labs/submission18.md labs/lab18/
   git commit -m "docs: add lab18 submission - Nix reproducible builds"
   git push -u origin feature/lab18
   ```

2. **Open a PR (GitHub) or MR (GitLab)** from your fork's `feature/lab18` branch → **course repository's main branch**.

3. In the PR/MR description, include:

   ```text
   Platform: [GitHub / GitLab]

   - [x] Task 1 — Build Reproducible Artifacts from Scratch (6 pts)
   - [x] Task 2 — Reproducible Docker Images with Nix (4 pts)
   - [ ] Bonus Task — Modern Nix with Flakes (2 pts) [if completed]
   ```

4. **Copy the PR/MR URL** and submit it via **Moodle before the deadline**.

---

## Acceptance Criteria

- ✅ Branch `feature/lab18` exists with commits for each task
- ✅ File `labs/submission18.md` contains required outputs and analysis for all completed tasks
- ✅ Directory `labs/lab18/` contains your application code and Nix expressions
- ✅ Nix derivations successfully build reproducible artifacts
- ✅ Docker image built with Nix and compared to traditional Dockerfile
- ✅ Hash comparisons prove reproducibility
- ✅ **Bonus (if attempted):** `flake.nix` and `flake.lock` present and working
- ✅ PR/MR from `feature/lab18` → **course repo main branch** is open
- ✅ PR/MR link submitted via Moodle before the deadline

---

## Rubric (12 pts max)

| Criterion                                           | Points |
| --------------------------------------------------- | -----: |
| Task 1 — Build Reproducible Artifacts from Scratch |  **6** |
| Task 2 — Reproducible Docker Images with Nix        |  **4** |
| Bonus Task — Modern Nix with Flakes                 |  **2** |
| **Total**                                           | **12** |

---

## Guidelines

- Use clear Markdown headers to organize sections in `submission18.md`
- Include command outputs and written analysis for each task
- Explain WHY Nix provides better reproducibility than traditional tools
- Compare before/after results when proving reproducibility
- Document challenges encountered and how you solved them
- Include code snippets with explanations, not just paste

<details>
<summary>📚 Helpful Resources</summary>

**Official Documentation:**
- [nix.dev - Official tutorials](https://nix.dev/)
- [Zero to Nix - Beginner-friendly guide](https://zero-to-nix.com/)
- [Nix Pills - Deep dive](https://nixos.org/guides/nix-pills/)
- [NixOS Package Search](https://search.nixos.org/)

**Docker with Nix:**
- [Building Docker images - nix.dev](https://nix.dev/tutorials/nixos/building-and-running-docker-images.html)
- [dockerTools reference](https://ryantm.github.io/nixpkgs/builders/images/dockertools/)

**Flakes:**
- [Nix Flakes - NixOS Wiki](https://wiki.nixos.org/wiki/Flakes)
- [Flakes - Zero to Nix](https://zero-to-nix.com/concepts/flakes)
- [Practical Nix Flakes](https://serokell.io/blog/practical-nix-flakes)

**Community:**
- [awesome-nix - Curated resources](https://github.com/nix-community/awesome-nix)
- [NixOS Discourse](https://discourse.nixos.org/)

</details>

<details>
<summary>💡 Nix Tips</summary>

1. **Store paths are content-addressable:** Same inputs = same output hash
2. **Use `nix-shell -p pkg` for quick testing** before adding to derivations
3. **Garbage collect unused builds:** `nix-collect-garbage -d`
4. **Search for packages:** `nix search nixpkgs golang`
5. **Read error messages carefully:** Nix errors are verbose but informative
6. **Use `lib.fakeHash` initially** when you don't know the hash yet
7. **Avoid network access in builds:** Nix sandboxes block network by default
8. **Pin nixpkgs version** for maximum reproducibility

</details>

<details>
<summary>🔧 Troubleshooting</summary>

**If Nix installation fails:**
- Ensure you have multi-user support (daemon mode recommended)
- Check `/nix` directory permissions
- Try the Determinate Systems installer instead of official

**If builds fail with "hash mismatch":**
- Update the hash in your derivation to match the error message
- Use `lib.fakeHash` to discover the correct hash

**If Docker load fails:**
- Verify result is a valid tarball: `file result`
- Check Docker daemon is running: `docker info`
- Try `docker load -i result` instead of `docker load < result`

**If flakes don't work:**
- Ensure experimental features are enabled in `~/.config/nix/nix.conf`
- Run `nix flake check` to validate flake syntax
- Make sure your flake is in a git repository

**If cross-machine builds differ:**
- Check nixpkgs input is locked in `flake.lock`
- Verify both machines use same Nix version
- Ensure no `created = "now"` or timestamps in image builds

</details>

<details>
<summary>🎯 Understanding Reproducibility</summary>

**What makes a build reproducible?**
- ✅ Deterministic inputs (exact versions, hashes)
- ✅ Isolated environment (no system dependencies)
- ✅ No timestamps or random values
- ✅ Same compiler, same flags, same libraries
- ✅ Content-addressable storage

**Why traditional tools fail:**
```bash
# Docker - timestamps in layers
docker build .  # Different timestamp = different image hash

# npm - lockfiles help but aren't perfect
npm install     # Still uses local cache, system libraries

# apt/yum - version drift
apt-get install nodejs  # Gets different version next week
```

**How Nix succeeds:**
```bash
# Nix - pure, sandboxed, content-addressed
nix-build       # Same inputs = bit-for-bit identical output
                # Today, tomorrow, on any machine
```

**Real-world impact:**
- **CI/CD:** No more "works on my machine"
- **Security:** Audit exact dependency tree
- **Rollback:** Atomic updates with perfect rollbacks
- **Collaboration:** Everyone gets identical environment

</details>

<details>
<summary>🌟 Advanced Concepts (Optional Reading)</summary>

**Content-Addressable Store:**
- Every package has a unique hash based on its inputs
- `/nix/store/abc123...` where `abc123` = hash of inputs
- Same inputs = same hash = reuse existing build

**Sandboxing:**
- Builds run in isolated namespaces
- No network access (except for fixed-output derivations)
- No access to `/home`, `/tmp`, or system paths
- Only declared dependencies are available

**Lazy Evaluation:**
- Nix expressions are lazily evaluated
- Only builds what's actually needed
- Enables massive codebase (all of nixpkgs) without performance issues

**Binary Cache:**
- cache.nixos.org provides pre-built binaries
- If your build matches a cached hash, download instead of rebuild
- Set up private caches for your team

**Cross-Compilation:**
- Nix makes cross-compilation trivial
- `pkgs.pkgsCross.aarch64-multiplatform.hello`
- Same reproducibility guarantees across architectures

</details>
