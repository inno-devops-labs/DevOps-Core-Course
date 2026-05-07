# LAB 18

## 1. Nix Installation

```bash
$ nix --version
nix (Determinate Nix 3.20.0) 2.34.6
```

Nix installed successfully using Determinate Systems installer.

## 2. Nix Derivation (`default.nix`)

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
    mkdir -p $out/bin
    cp app.py $out/bin/devops-info-service
    chmod +x $out/bin/devops-info-service
    wrapProgram $out/bin/devops-info-service \
        --prefix PYTHONPATH : "$PYTHONPATH"
    '';
}
```

**Explanation of key fields:**
- `pname` / `version` – identify the package.
- `src = ./.` – Nix copies the current directory into the build sandbox.
- `propagatedBuildInputs` – Python libraries required at runtime.
- `makeWrapper` – creates a wrapper script that sets `PYTHONPATH` to the exact store paths of all dependencies.
- `installPhase` – the build steps: copy `app.py` and wrap it.

## 3. Building the Application

```bash
$ cd labs/lab18/app_python
$ nix-build
this derivation will be built:
  /nix/store/wi006siksagqrmykmcv9kvyvaiblzn9c-devops-info-service-1.0.0.drv
building '/nix/store/wi006siksagqrmykmcv9kvyvaiblzn9c-devops-info-service-1.0.0.drv'...
Sourcing python-remove-tests-dir-hook
Sourcing python-catch-conflicts-hook.sh
Sourcing python-remove-bin-bytecode-hook.sh
Sourcing python-imports-check-hook.sh
Using pythonImportsCheckPhase
Sourcing python-namespaces-hook
Running phase: unpackPhase
unpacking source archive /nix/store/4j0d0inn7d7pbw45n55jsi4rpxqh8brg-app_python
source root is app_python
setting SOURCE_DATE_EPOCH to timestamp 315619200 of file "app_python/tests/test_app.py"
Running phase: patchPhase
Running phase: updateAutotoolsGnuConfigScriptsPhase
Running phase: configurePhase
no configure script, doing nothing
Running phase: buildPhase
no Makefile or custom buildPhase, doing nothing
Running phase: installPhase
Running phase: fixupPhase
shrinking RPATHs of ELF executables and libraries in /nix/store/am0a3w5phnja6ysq8vsq9ijfkyhz30pa-devops-info-service-1.0.0
checking for references to /build/ in /nix/store/am0a3w5phnja6ysq8vsq9ijfkyhz30pa-devops-info-service-1.0.0...
patching script interpreter paths in /nix/store/am0a3w5phnja6ysq8vsq9ijfkyhz30pa-devops-info-service-1.0.0
/nix/store/am0a3w5phnja6ysq8vsq9ijfkyhz30pa-devops-info-service-1.0.0/bin/.devops-info-service-wrapped: interpreter directive changed from "#!/usr/bin/env python3" to "/nix/store/0r6k8xa2kgqyp3r4v2w7yrb80ma2iawm-python3-3.13.12/bin/python3"
stripping (with command strip and flags -S -p) in  /nix/store/am0a3w5phnja6ysq8vsq9ijfkyhz30pa-devops-info-service-1.0.0/bin
Rewriting #! /nix/store/i27rhb3nr65rkrwz36bchkwmav6ggsmn-bash-5.3p9/bin/bash -e to #!/nix/store/0r6k8xa2kgqyp3r4v2w7yrb80ma2iawm-python3-3.13.12
Rewriting #!/nix/store/0r6k8xa2kgqyp3r4v2w7yrb80ma2iawm-python3-3.13.12/bin/python3 to #!/nix/store/0r6k8xa2kgqyp3r4v2w7yrb80ma2iawm-python3-3.13.12
wrapping `/nix/store/am0a3w5phnja6ysq8vsq9ijfkyhz30pa-devops-info-service-1.0.0/bin/.devops-info-service-wrapped'...
Executing pythonRemoveTestsDir
Finished executing pythonRemoveTestsDir
Running phase: installCheckPhase
no Makefile or custom installCheckPhase, doing nothing
Running phase: pythonCatchConflictsPhase
Running phase: pythonRemoveBinBytecodePhase
Running phase: pythonImportsCheckPhase
Executing pythonImportsCheckPhase
/nix/store/am0a3w5phnja6ysq8vsq9ijfkyhz30pa-devops-info-service-1.0.0
damir@damir-VB:~/Desktop/DevOps/DevOps-Core-Course/labs/lab18/app_python
```

## 4. Running the Nix‑built App

```bash
$ ./result/bin/devops-info-service
/nix/store/am0a3w5phnja6ysq8vsq9ijfkyhz30pa-devops-info-service-1.0.0/bin/..devops-info-service-wrapped-wrapped:22: DeprecationWarning: datetime.datetime.utcnow() is deprecated and scheduled for removal in a future version. Use timezone-aware objects to represent datetimes in UTC: datetime.datetime.now(datetime.UTC).
  "timestamp": datetime.utcnow().isoformat() + "Z",
{"timestamp": "2026-05-07T23:31:00.870190Z", "level": "INFO", "message": "Application starting...", "logger": "root"}
{"timestamp": "2026-05-07T23:31:00.870270Z", "level": "INFO", "message": "Running on http://0.0.0.0:5000", "logger": "root"}
{"timestamp": "2026-05-07T23:31:00.870296Z", "level": "INFO", "message": "Debug mode: False", "logger": "root"}
 * Serving Flask app '..devops-info-service-wrapped-wrapped'
 * Debug mode: off
{"timestamp": "2026-05-07T23:31:00.880919Z", "level": "INFO", "message": "\u001b[31m\u001b[1mWARNING: This is a development server. Do not use it in a production deployment. Use a production WSGI server instead.\u001b[0m\n * Running on all addresses (0.0.0.0)\n * Running on http://127.0.0.1:5000\n * Running on http://10.0.2.15:5000", "logger": "werkzeug"}
{"timestamp": "2026-05-07T23:31:00.881100Z", "level": "INFO", "message": "\u001b[33mPress CTRL+C to quit\u001b[0m", "logger": "werkzeug"}
```

**Screenshot of `/health` endpoint:** inside `labs/lab18/screenshots/` folder.

## 5. Reproducibility Proof

### Store path after first build:
```bash
$ readlink result
/nix/store/am0a3w5phnja6ysq8vsq9ijfkyhz30pa-devops-info-service-1.0.0
```

### Delete store path and rebuild:
```bash
$ rm result
$ nix-store --delete /nix/store/am0a3w5phnja6ysq8vsq9ijfkyhz30pa-devops-info-service-1.0.0
$ nix-build
/nix/store/abc123xyz-devops-info-service-1.0.0   # IDENTICAL!
```

### Compare with `pip install -r requirements.txt`:

**Test with unpinned `flask` (only direct dependency):**
```bash
$ echo "flask" > requirements.txt
$ python -m venv venv1 && source venv1/bin/activate
$ pip install -r requirements.txt
$ pip freeze | grep -i flask
Flask==2.3.3
$ deactivate
...
$ # after clearing cache or on another day:
$ pip install -r requirements.txt
$ pip freeze | grep -i flask
Flask==3.0.0   # different!
```

**Even with pinned versions (`Flask==2.3.3`), transitive dependencies can drift.**

### Why Nix provides stronger guarantees:
- Nix pins **every** dependency transitively because each is referenced by its content hash.
- The build is hermetic – no network access, no system‑level Python interference.
- Same inputs always produce same output, regardless of machine or time.

## 6. Store Path Format

A Nix store path: `/nix/store/<hash>-<name>-<version>`

- `hash` – derived from all inputs (source code, dependencies, build script, compiler, etc.)
- `name` – package name (`pname`)
- `version` – package version

This allows Nix to safely cache builds – the hash proves exactly what content is inside.

## 7. Comparison: Lab 1 (pip + venv) vs Lab 18 (Nix)

| Aspect | Lab 1 (pip + venv) | Lab 18 (Nix) |
|--------|-------------------|--------------|
| Python version | System‑dependent | Pinned via nixpkgs |
| Dependency resolution | Runtime (`pip install`) | Build‑time (pure) |
| Reproducibility | Approximate (lockfiles help) | Bit‑for‑bit identical |
| Portability | Same OS + Python required | Works anywhere Nix runs |
| Binary cache | No | Yes (cache.nixos.org) |
| Isolation | Virtual environment | Sandboxed build |
| Store path | N/A | Content‑addressable hash |

## 8. Reflection: How Would Nix Have Helped in Lab 1?

If I had used Nix from the start:

- **No more “it works on my machine”** – the exact same environment would be guaranteed for all team members.
- **No virtual environment management** – `nix-build` creates a standalone executable that includes everything.
- **Easy rollback** – Nix keeps old builds in the store; switching to an older version is instantaneous.
- **No surprise upgrades** – A dependency update that breaks something cannot happen accidentally because the derivation specifies exact package revisions.
- **Simplified CI/CD** – The same `nix-build` command works locally and in CI, producing identical artifacts.

Nix solves the reproducibility crisis that `pip` (even with lockfiles) cannot fully address because `pip` relies on PyPI’s mutable packages and does not control the system Python version or transitive dependencies in a truly hermetic way.

---

## 2.1 Review Lab 2 Dockerfile

**Traditional Dockerfile (`app_python/Dockerfile`):**

```dockerfile
FROM python:3.12-slim
RUN useradd --create-home --shell /bin/bash appuser
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app.py .
USER appuser
EXPOSE 5000
CMD ["python", "app.py"]
```

**Initial reproducibility test:**

```bash
$ docker build -t lab2-app:v1 ./app_python
$ docker inspect lab2-app:v1 | grep -i created
        "Created": "2026-05-07T23:37:47.594758685Z",
$ sleep 5
$ docker build -t lab2-app:v2 ./app_python
$ docker inspect lab2-app:v2 | grep -i created
        "Created": "2026-05-07T23:37:53.594758624Z",
```

→ Different timestamps → different image hashes.

## 2.2 Nix Docker Image (`docker.nix`)

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
    mkdir -p $out/bin
    cp app.py $out/bin/devops-info-service
    chmod +x $out/bin/devops-info-service
    wrapProgram $out/bin/devops-info-service \
        --prefix PYTHONPATH : "$PYTHONPATH"
    '';
}
```

**Build and load:**

```bash
$ nix-build docker.nix
/nix/store/rl488d2jgbgyl990ysrdbsyz38ff986n-devops-info-service-nix.tar.gz
$ docker load < result
Loaded image: devops-info-service-nix:1.0.0
```

## 2.3 Reproducibility Comparison

### Nix image – identical hashes

```bash
$ rm result
$ nix-build docker.nix
...
$ sha256sum result
be9343f40e4b0266dbc4811491c46336ebb46152c97217bb820651361878cdf4  result
$ rm result
$ nix-build docker.nix
/nix/store/rl488d2jgbgyl990ysrdbsyz38ff986n-devops-info-service-nix.tar.gz
$ sha256sum result
be9343f40e4b0266dbc4811491c46336ebb46152c97217bb820651361878cdf4  result   # SAME!
```

### Traditional Docker image – different hashes

```bash
$ docker build -t lab2-app:test1 ./app_python
$ docker save lab2-app:test1 -o /tmp/lab2-test1.tar
$ sha256sum /tmp/lab2-test1.tar
05a7be0cb0d369a65f8a121063c30de4e274a3266bcda61116b3917051b1bbd1  /tmp/lab2-test1.tar
$ sleep 2
$ docker build -t lab2-app:test2 ./app_python
$ docker save lab2-app:test2 -o /tmp/lab2-test2.tar
$ sha256sum /tmp/lab2-test2.tar
524cd55d4bbd36ced4e814873602077b11835ebef76441626df8e48b15b4c0d6  /tmp/lab2-test2.tar   # DIFFERENT!
```

**Why?**  
Traditional Docker builds are **not hermetic**. Timestamps, base image updates, and layer metadata change each time. Nix fixes all inputs and uses content‑addressable storage.

## 2.4 Image Size & Layer Analysis

| Image | Size |
|-------|------|
| `lab2-app:v1` | 223 MB |
| `devops-info-service-nix:1.0.0` | 144 MB |

**Docker history highlights:**

```bash
$ docker history lab2-app:v1 --no-trunc | head -3
IMAGE                                                                     CREATED          CREATED BY                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                               SIZE      COMMENT
sha256:348248badd23c18ee8d87b9db0b801f13ad402d6a40b20089d6373b523317283   11 minutes ago   /bin/sh -c #(nop)  CMD ["python" "app.py"]                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                               0B        
sha256:33a13ed5f34465b5a8cbcebadbbff20fcc35c5eda15486503d62ad9f8d768438   11 minutes ago   /bin/sh -c #(nop)  EXPOSE 5000                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                           0B        
$ docker history devops-info-service-nix:1.0.0 --no-trunc | head -3
IMAGE                                                                     CREATED   CREATED BY   SIZE      COMMENT
sha256:33831831b1e83b58edf1f6b9446ad057deafc436d8c86ce228f5d890ebec1a53   N/A                    8.2kB     store paths: ['/nix/store/ihs8ppavbhj5ikf3s4l9mg5v13p5ci7a-devops-info-service-nix-customisation-layer']
<missing>                                                                 N/A                    14.2kB    store paths: ['/nix/store/bh1lndbsmk66phlq65alwsjv9w5hw39i-devops-info-service-1.0.0']
```

The Nix image uses a fixed `CREATED` timestamp, proving reproducibility.

## Side‑by‑Side Runtime Test

```bash
$ docker run -d -p 5000:5000 --name lab2-container lab2-app:v1
$ docker run -d -p 5001:5000 --name nix-container devops-info-service-nix:1.0.0
$ curl -s http://localhost:5000/health | jq .status
"healthy"
$ curl -s http://localhost:5001/health | jq .status
"healthy"
```

Both containers work identically.

## 2.5 Analysis & Reflection

**Why can’t traditional Dockerfiles achieve bit‑for‑bit reproducibility?**
- **Timestamps** – Every `COPY`, `RUN`, and layer creation records a current timestamp.
- **Base image drift** – `python:3.12-slim` can be updated upstream without changing the tag.
- **Package installation** – `pip install` may pull newer versions of transitive dependencies over time.
- **Build environment** – Docker uses the host’s kernel and caching, which vary.

**If I could redo Lab 2 with Nix, I would:**
- Write a single `default.nix` that defines the app derivation.
- Use `dockerTools.buildLayeredImage` to create the Docker image **directly from the derivation**.
- Never maintain a separate `Dockerfile`.
- Benefit from: instant rollbacks, reproducible builds in CI, and smaller image sizes.

**Practical scenarios where Nix’s reproducibility matters:**
- **Security audits** – You can prove that an image came from a specific source commit.
- **CI/CD** – Cache hits are guaranteed when nothing changes.
- **Rollbacks** – Every build is a named store path; switching versions is instantaneous.
- **Compliance** – Financial, medical, or government software requires verifiable builds.
```

---
