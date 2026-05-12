# Lab 18 submission — Reproducible builds with Nix

---

## Task 1 — Reproducible Python app (revisiting Lab 1)

### 1.1 Installation and verification

Nix was installed with the Determinate Systems installer (multi-user). After opening a shell that loads Nix:

```text
$ nix --version
nix (Determinate Nix 3.20.0) 2.34.6
```

FlakeHub-backed `nixpkgs` (Determinate `extra-nix-path`) can be warmed if the first `nix-build` stalls on redirects; this prefetch uses a plain HTTPS URL (quote the `*` so the shell does not glob):

```text
$ nix flake prefetch "https://flakehub.com/f/DeterminateSystems/nixpkgs-weekly/*.tar.gz"
Downloaded 'https://api.flakehub.com/f/pinned/DeterminateSystems/nixpkgs-weekly/0.1.995785%2Brev-c6e5ca3c836a5f4dd9af9f2c1fc1c38f0fac988a/019e1ade-fee0-7492-a2aa-51f76ee770f8/source.tar.gz?narHash=sha256-cY07EsdhBJ8tFXPzDYevgqxRev9ZLxFonuq9wmq5kwg%3D' to '/nix/store/2z7ris6v1f11jqidj1iaw1iwafr7lv5x-source' (hash 'sha256-cY07EsdhBJ8tFXPzDYevgqxRev9ZLxFonuq9wmq5kwg=').
```

```text
$ nix run nixpkgs#hello
Hello, world!
```

### 1.2 Application layout

Lab artifacts live under `labs/lab18/app_python/` (copy of `app_python/` from the repo): `app.py` (FastAPI service from Lab 1) and `requirements.txt`.

### 1.3 `default.nix` (full file)

```nix
{ pkgs ? import <nixpkgs> { } }:

let
  lib = pkgs.lib;
  srcRoot = ./.;
  appSrc = builtins.path {
    name = "devops-info-service-src";
    path = srcRoot;
    filter = path: _type:
      let
        rel = lib.removePrefix ((toString srcRoot) + "/") (toString path);
      in
      rel != "venv"
      && !(lib.hasPrefix "venv/" rel)
      && !(lib.hasPrefix ".pytest_cache" rel)
      && (baseNameOf path != "result");
  };
in
pkgs.python3Packages.buildPythonApplication {
  pname = "devops-info-service";
  version = "1.0.0";
  src = appSrc;

  format = "other";

  propagatedBuildInputs = with pkgs.python3Packages; [
    fastapi
    uvicorn
    prometheus-client
  ];

  nativeBuildInputs = [ pkgs.makeWrapper ];

  # No packaged pytest suite wired for this layout; runtime app only.
  doCheck = false;

  installPhase = ''
    mkdir -p $out/share/devops-info-service
    cp app.py $out/share/devops-info-service/app.py

    makeWrapper ${pkgs.python3Packages.python}/bin/python3 $out/bin/devops-info-service \
      --prefix PYTHONPATH : "$PYTHONPATH" \
      --add-flags "$out/share/devops-info-service/app.py"
  '';
}
```

**Field notes (short):**


| Piece                                 | Role                                                                                                                        |
| ------------------------------------- | --------------------------------------------------------------------------------------------------------------------------- |
| `pkgs ? import <nixpkgs> { }`         | Default package set (here from Determinate FlakeHub `nixpkgs-weekly` via `extra-nix-path`).                                 |
| `builtins.path` + `filter`            | Clean source tree: drop `venv/`, `.pytest_cache`, and `result` so they never affect the input hash.                         |
| `buildPythonApplication`              | Nixpkgs helper for Python apps.                                                                                             |
| `format = "other"`                    | No `pyproject.toml` / `setup.py` install; we install manually.                                                              |
| `propagatedBuildInputs`               | Runtime Python deps (versions come from pinned nixpkgs, not PyPI).                                                          |
| `nativeBuildInputs = [ makeWrapper ]` | Supplies `makeWrapper` in the build.                                                                                        |
| `makeWrapper … python3 … app.py`      | FastAPI entry is a `.py` file: run the interpreter explicitly (wrapping the file alone would execute it as shell and fail). |
| `doCheck = false`                     | Tests under `tests/` are not wired as a Nix `checkPhase` for this layout.                                                   |


### 1.4 Reproducibility — store paths and rebuilds

From `labs/lab18/app_python/`:

```text
$ rm -f result && nix-build -Q
/nix/store/zdf8dpwb4a14w7h4ji21aw9jmnrg8bkk-devops-info-service-1.0.0

$ readlink result
/nix/store/zdf8dpwb4a14w7h4ji21aw9jmnrg8bkk-devops-info-service-1.0.0

$ rm -f result && nix-build -Q
/nix/store/zdf8dpwb4a14w7h4ji21aw9jmnrg8bkk-devops-info-service-1.0.0

$ readlink result
/nix/store/zdf8dpwb4a14w7h4ji21aw9jmnrg8bkk-devops-info-service-1.0.0
```

Two rebuilds without changing inputs → **identical store path** (binary cache / same derivation output).

**Forced rebuild note:** `sudo nix-store --delete` must use the Nix profile binary on `PATH` for root, e.g. `/nix/var/nix/profiles/default/bin/nix-store`. Even then, delete can be refused if another process still references the path (e.g. live `/proc/...` GC root). Equivalent check mandated:

```text
$ nix-build --check -Q
checking outputs of '/nix/store/945y873pllk84qylg7z4ms4zikdvm3gz-devops-info-service-1.0.0.drv'...
/nix/store/zdf8dpwb4a14w7h4ji21aw9jmnrg8bkk-devops-info-service-1.0.0
```

**Output hash (Nix store path contents):**

```text
$ nix-hash --type sha256 result
1ad0af7b653914dbd1e8af51edfadad5c44b0e6cddbc7c0166e045f1ddd524f7
```

### 1.5 Pip vs Nix — weaker guarantees of `requirements.txt`

**Unpinned direct dependency (lab-style demo):** with only `flask` in `requirements-unpinned.txt`, two fresh venvs on the same machine can still resolve the same line in `pip freeze` for Flask on a given day; the lab’s point stands: **without pins you accept “whatever PyPI considers current”**, and **even with pins you only constrain direct deps unless you use full lockfiles** — transitive wheels can still shift when upstream metadata or resolver behavior changes. Nix pins the **entire closure** via nixpkgs.

**Illustrative** `pip freeze` **snippet:**

```text
--- freeze1 ---
Flask==3.1.3
--- freeze2 ---
Flask==3.1.3
--- diff freeze1 vs freeze2 ---
(no diff)
```

For a stronger demonstration, compare full `pip freeze` outputs or repeat after months / on another OS — Nix store paths stay fixed until `nixpkgs` or your expression changes.

### 1.6 Run the Nix-built binary 

Port 5000 was busy (Docker from Task 2); the FastAPI app respects `PORT`:

```text
$ PORT=5002 ./result/bin/devops-info-service &
$ sleep 2
$ curl -sS http://127.0.0.1:5002/health
{"status":"healthy","timestamp":"2026-05-12T22:04:58.436614+00:00","uptime_seconds":1}
```

**Screenshot (Task 1):** Nix-built binary only (`PORT=5002`), Chrome headless capture of `http://127.0.0.1:5002/health` (Pretty-printed JSON in the browser viewport).

Nix-built DevOps Info Service — /health on port 5002

### 1.7 Nix store path format

Example: `/nix/store/zdf8dpwb4a14w7h4ji21aw9jmnrg8bkk-devops-info-service-1.0.0`

- `/nix/store/` — global store root.  
- `zdf8dpwb4a14w7h4ji21aw9jmnrg8bkk` — cryptographic hash of **all build inputs** (sources, deps, flags, builder).  
- `devops-info-service-1.0.0` — human-readable `pname-version`.

Same inputs → same hash → same path → shareable substitutes.

### 1.8 Reflection — Nix in Lab 1 from day one

Using Nix early would have pinned **Python + every library** to one closure, given identical builds across laptops and CI, and avoided “works in my venv” drift when classmates pulled different transitive versions from PyPI.

### 1.9 Comparison table (Lab 1 vs Lab 18)


| Aspect                | Lab 1 (pip + venv)                                 | Lab 18 (Nix)                                 |
| --------------------- | -------------------------------------------------- | -------------------------------------------- |
| Python version        | Whatever you installed / system                    | From nixpkgs closure                         |
| Dependency resolution | pip / lockfile (if you add one)                    | Pure evaluation + store                      |
| Reproducibility       | Good with discipline; not bit-identical by default | Bit-identical output path for unchanged expr |
| Portability           | OS + Python stack must match                       | Anywhere the same nixpkgs evaluates          |
| Binary cache          | PyPI wheels                                        | cache.nixos.org + vendor caches              |


---

## Task 2 — Reproducible Docker images (revisiting Lab 2)

### 2.1 Lab 2 `Dockerfile` (from `app_python/Dockerfile`)

```dockerfile
FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

RUN groupadd -g 999 appgroup && useradd -r -u 999 -g appgroup appuser

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app.py .

RUN mkdir -p /data && chown -R appuser:appgroup /app /data

USER appuser

EXPOSE 5000

CMD ["python", "app.py"]
```

**Lab 2 “timestamps” sample (`docker inspect` Created):**

```text
2026-05-13T00:59:11.669210111+03:00   # v1
2026-05-13T00:59:11.669210111+03:00   # v2 (same second in this run; not guaranteed across machines)
```

### 2.2 `docker.nix` (full file)

```nix
{ pkgs ? import <nixpkgs> { } }:

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
      "5000/tcp" = { };
    };
  };

  created = "1970-01-01T00:00:01Z";
}
```


| Field                 | Role                                                                        |
| --------------------- | --------------------------------------------------------------------------- |
| `buildLayeredImage`   | Layered OCI layout from store paths (good layer reuse).                     |
| `name` / `tag`        | Image repository name and tag after `docker load`.                          |
| `contents`            | Closure to copy into the image — here only the Nix-built app (minimal-ish). |
| `config.Cmd`          | Default process — must match `$out/bin/devops-info-service` from Task 1.    |
| `config.ExposedPorts` | Metadata for `EXPOSE 5000` equivalent.                                      |
| `created`             | **Fixed** timestamp for reproducibility (never `"now"`).                    |


### 2.3 Nix Docker tarball — identical hashes on rebuild

```text
$ rm -f result && nix-build docker.nix -Q
/nix/store/r4dj99kmz59rm7i4nlxsj6zc6n2ka7qd-devops-info-service-nix.tar.gz

$ sha256sum result
ce8f274e29deef8307620bef8b7730a075943aabc87f07ec445cfb57bec94ab0  result

$ rm -f result && nix-build docker.nix -Q
/nix/store/r4dj99kmz59rm7i4nlxsj6zc6n2ka7qd-devops-info-service-nix.tar.gz

$ sha256sum result
ce8f274e29deef8307620bef8b7730a075943aabc87f07ec445cfb57bec94ab0  result
```

**Observation:** `sha256sum` matches byte-for-byte — reproducible tarball.

### 2.4 Lab 2 image — `docker save` differs between back-to-back builds

Image ID was the same in this session (layer cache), but **exported tar streams still hashed differently** (metadata / ordering / timestamps inside the stream):

```text
sub1: 46d4534cf778e58ba4a27b16c88a6006fd36beddd4880392311ff8e5637b8216
sub2: 01c7fc3811c164a2c3930290e8aea05e18e0827db3e1921a0bfeb24f70feda62
```

So: **same Dockerfile + same source does not imply the same `docker save` digest**, unlike Nix’s tarball above.

### 2.5 Image size (this machine)

```text
$ docker images | grep -E "lab2-app|devops-info-service-nix"
devops-info-service-nix:1.0.0    …   ~228MB
lab2-app:v1                      …   ~163MB
```


| Metric                     | Lab 2 Dockerfile                       | Lab 18 Nix dockerTools                                 |
| -------------------------- | -------------------------------------- | ------------------------------------------------------ |
| Reported size (this build) | ~163 MB                                | ~228 MB                                                |
| `docker save` stream       | **Different** across runs (see hashes) | **Identical** tarball hash when `docker.nix` unchanged |
| Base image                 | `python:3.12-slim` (moving tag)        | No distro “base”; store closure only                   |
| Timestamps                 | Present in normal Docker history       | `created` pinned to epoch in manifest config           |


*Nix image can be larger than “slim + pip” here because it embeds a Python closure with FastAPI/Pydantic/etc.; the lab’s learning goal is reproducibility, not always smallest byte size.*

### 2.6 `docker history` 

**Lab 2 (`lab2-app:v1`):** shows `CREATED` times like “6 minutes ago” / “4 days ago” on BuildKit steps — time-varying metadata.

**Nix (`devops-info-service-nix:1.0.0`):** layers list **store paths**; created column shows `N/A` / deterministic layout (example from this host):

```text
IMAGE          CREATED   CREATED BY   SIZE      COMMENT
947be199751e   N/A                    300B      store paths: ['...-devops-info-service-nix-customisation-layer']
<missing>      N/A                    16.7kB    store paths: ['...-devops-info-service-1.0.0']
…
```

### 2.7 Side-by-side containers + `curl /health`

```text
$ docker run -d -p 5000:5000 --name lab2-container lab2-app:v1
$ docker run -d -p 5001:5000 --name nix-container devops-info-service-nix:1.0.0

$ curl -sS http://127.0.0.1:5000/health
{"status":"healthy","timestamp":"2026-05-12T22:05:32.457459+00:00","uptime_seconds":4}

$ curl -sS http://127.0.0.1:5001/health
{"status":"healthy","timestamp":"2026-05-12T22:05:32.483623+00:00","uptime_seconds":6}
```

**Screenshots (Task 2):** same hosts/ports as above, captured while **both** containers were running (`lab2-app:v1` → host `:5000`, `devops-info-service-nix:1.0.0` → host `:5001`).

Individual captures:

Lab 2 Docker — /health on localhost:5000

Nix dockerTools image — /health on localhost:5001

Side-by-side (Lab 2 left, Nix right):

Lab 2 and Nix containers — /health side by side

### 2.8 Analysis — why ordinary Dockerfiles are not bit-for-bit reproducible

- **Moving base tags** (`python:3.12-slim`) can point to new image digests.  
- **BuildKit / layer metadata** includes build times and host-specific details.  
- `**pip install` at image build time** resolves against PyPI / index state unless fully hashed lock + offline install.  
- `**docker save`** is not guaranteed to be a canonical byte stream; even small metadata differences change the digest.

Nix fixes **manifest `created`**, pins **store inputs**, and produces a **deterministic tarball** from `dockerTools` for the same derivation.

### 2.9 Reflection — redoing Lab 2 with Nix

I would build the runtime image from `docker.nix`, load it in CI, and optionally retag by store hash for traceability. Local `docker build` would remain for quick iteration only, not as the source of truth for “what prod runs.”

### 2.10 Practical scenarios

- **CI/CD:** identical tarball → identical deploy artifact.  
- **Security audits:** diff two store paths or tarball hashes instead of guessing layer drift.  
- **Rollbacks:** redeploy exact `/nix/store/...` or matching image tarball.

### 2.11 Comprehensive comparison (from lab handout)


| Aspect                 | Lab 2 traditional Dockerfile                 | Lab 18 Nix dockerTools                          |
| ---------------------- | -------------------------------------------- | ----------------------------------------------- |
| Base images            | Moving tag (e.g. `python:3.12-slim`)         | No distro base; store closure                   |
| Timestamps             | Vary per build / BuildKit                    | `created` fixed in `docker.nix`                 |
| Package install        | `pip` at image build time                    | Pre-built Nix store paths                       |
| Reproducibility        | Same file ≠ same `docker save` digest (§2.4) | Same `docker.nix` → same tarball hash (§2.3)    |
| Caching                | Layer cache, time-stamped steps              | Content-addressed store                         |
| Image size (this repo) | ~163 MB reported                             | ~228 MB reported (closure vs slim+pip tradeoff) |
| Portability            | Docker only                                  | Nix build, then `docker load`                   |
| Security               | Base image + PyPI surface                    | Smaller audited closure possible                |
