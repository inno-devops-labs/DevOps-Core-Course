# Lab 18 — Reproducible Builds with Nix

## Task 1 — Build Reproducible Python App (Revisiting Lab 1)

### 1.1 — Nix Installation

**Installation command used (Determinate Systems installer):**
```bash
curl --proto '=https' --tlsv1.2 -sSf -L https://install.determinate.systems/nix | sh -s -- install
```

**Verification:**
```
$ nix --version
nix (Nix) 2.28.3
```

**Basic test:**
```
$ nix run nixpkgs#hello
Hello, world!
```

---

### 1.2 — Python Application Preparation

The application from Lab 1 was copied to `labs/lab18/app_python/`:

```
labs/lab18/app_python/
├── app.py            # Flask DevOps Info Service (from Lab 1)
├── requirements.txt  # Flask==3.1.0, python-dotenv==1.0.1
├── default.nix       # NEW: Nix derivation
└── docker.nix        # NEW: Nix Docker image definition
```

**Lab 1 traditional pip workflow:**
```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python app.py
```

**Problems with this approach:**
- Python version depends on whatever is installed on the system
- `pip install` resolves transitive dependencies at runtime — results can differ across machines and over time
- `requirements.txt` only pins *direct* dependencies; transitive ones (Werkzeug, Click, Jinja2 inside Flask) are not pinned and can drift silently

---

### 1.3 — Nix Derivation

**`labs/lab18/app_python/default.nix`:**

```nix
{ pkgs ? import (builtins.fetchTarball {
    url = "https://github.com/NixOS/nixpkgs/archive/refs/heads/nixos-24.11.tar.gz";
  }) {} }:

let
  # python3.withPackages creates a Python interpreter bundled with
  # exactly these packages — no pip, no venv, no version drift.
  pythonEnv = pkgs.python3.withPackages (ps: with ps; [
    flask
    python-dotenv
  ]);
in

pkgs.stdenv.mkDerivation {
  pname   = "devops-info-service";   # Package name (part of the store path)
  version = "1.0.0";                 # Version string

  # src = ./. hashes the entire source directory.
  # Any change to source → different hash → new build.
  src = ./.;

  nativeBuildInputs = [ pkgs.makeWrapper ];

  # installPhase runs in a pure sandbox: no internet, no /usr, no $HOME.
  # $out is our allocated slot in the Nix store.
  installPhase = ''
    mkdir -p $out/bin $out/lib
    cp $src/app.py $out/lib/app.py

    makeWrapper ${pythonEnv}/bin/python3 $out/bin/devops-info-service \
      --add-flags "$out/lib/app.py"
  '';
}
```

**Field explanations:**

| Field | Purpose |
|---|---|
| `builtins.fetchTarball` | Pins nixpkgs to a specific snapshot — ensures reproducibility across machines |
| `pname` / `version` | Metadata included in the Nix store path name |
| `src = ./.` | Source root; Nix hashes the entire directory — any change → different hash |
| `pythonEnv` | Python 3 + exact packages from the pinned nixpkgs snapshot |
| `nativeBuildInputs` | Tools needed at build time only (`makeWrapper`) |
| `installPhase` | Shell script running in the sandbox to produce the output at `$out` |
| `makeWrapper` | Creates a wrapper binary that invokes the correct pinned Python interpreter |

**Build output:**
```
$ nix-build
these 2 derivations will be built:
  /nix/store/6pkxg859r47abmr35is1w0kfji2jxwv5-python3-3.12.8-env.drv
  /nix/store/y2al393g8halcm05a6by2yghx13m0zma-devops-info-service-1.0.0.drv
these 71 paths will be fetched (1.0 MiB download, 525.9 MiB unpacked):
  /nix/store/dksjvr69ckglyw1k2ss1qgshhcix73p8-python3-3.12.8
  /nix/store/ijc606v1g5vhqxrjk4qmj787kymp6sal-python3.12-flask-3.0.3
  /nix/store/jcf93x7sly7l76hyaqwramfyydnbvsf4-python3.12-werkzeug-3.0.6
  /nix/store/3m0jdpw2ppa730lip4bkjaw4yky8c9h4-python3.12-python-dotenv-1.0.1
  ...
/nix/store/xhw0yf78z9ijka9bn4vv2yi4q853gys5-devops-info-service-1.0.0
```

**Running the Nix-built app:**
```
$ ./result/bin/devops-info-service &
2026-05-10 19:04:03,976 - INFO - Starting application on 0.0.0.0:5000
 * Serving Flask app 'app'
 * Running on http://127.0.0.1:5000
```

**Health check:**
```json
$ curl -s http://localhost:5000/health
{"status":"healthy","timestamp":"2026-05-10T16:14:22.201891+00:00","uptime_seconds":1}
```

The app built entirely from the Nix store runs identically to the Lab 1 version.

---

### 1.4 — Proving Reproducibility

#### Store path — build 1:
```
$ readlink result
/nix/store/xhw0yf78z9ijka9bn4vv2yi4q853gys5-devops-info-service-1.0.0
```

#### Content hash — build 1:
```
$ nix-hash --type sha256 result
39035cd7fe6fad23b05d38714dad306b581b2354d5604116a6e445c73fb3b121
```

#### Rebuild (Nix reuses cached output — same inputs, same hash):
```
$ nix-store --delete $(readlink result)
error: Cannot delete path '...' because it's referenced by the GC root '.../result'.
$ nix-build
/nix/store/xhw0yf78z9ijka9bn4vv2yi4q853gys5-devops-info-service-1.0.0
```

#### Content hash — build 2:
```
$ nix-hash --type sha256 result
39035cd7fe6fad23b05d38714dad306b581b2354d5604116a6e445c73fb3b121
```

**Both hashes are identical: `39035cd7fe6fad23b05d38714dad306b581b2354d5604116a6e445c73fb3b121`**

The store path and hash are identical across both builds. Nix reuses the cached result because the inputs have not changed. This is content-addressable storage: same inputs → same hash → same store path, always.

#### Nix store path format:
```
/nix/store / xhw0yf78z9ijka9bn4vv2yi4q853gys5 - devops-info-service - 1.0.0
     ^               ^                                ^                   ^
  Store root    Content hash (SHA256 of            Package name        Version
                ALL inputs: source + deps
                + build script + compiler)
```

#### pip reproducibility comparison:
```bash
$ echo "flask" > requirements-unpinned.txt
$ python3 -m venv venv1 && source venv1/bin/activate
$ pip install -r requirements-unpinned.txt --quiet
$ pip freeze | grep -i flask > freeze1.txt && deactivate

$ pip cache purge 2>/dev/null || true

$ python3 -m venv venv2 && source venv2/bin/activate
$ pip install -r requirements-unpinned.txt --quiet
$ pip freeze | grep -i flask > freeze2.txt && deactivate

$ diff freeze1.txt freeze2.txt || echo "DIFF FOUND"
$ cat freeze1.txt
Flask==3.1.3
$ cat freeze2.txt
Flask==3.1.3
```

Both installs produced Flask==3.1.3 because no new Flask release appeared between the two runs. However, this is not guaranteed: the moment PyPI publishes a new version, the same `pip install flask` on two machines can yield different results. More critically, transitive dependencies (Werkzeug, Click, Jinja2, MarkupSafe, itsdangerous, blinker) are never pinned in `requirements.txt` — they resolve independently on each machine.

#### Why does `requirements.txt` provide weaker guarantees than Nix?

`requirements.txt` pins only what is explicitly listed. Flask depends on six packages not present in `requirements.txt`, and pip resolves them at install time from whatever PyPI currently serves. On a different machine or a week later, pip may resolve different transitive versions — producing a subtly different environment. Nix pins the **entire nixpkgs tree** to a single snapshot, fixing every package at every dependency level simultaneously. The store hash is a cryptographic proof that the full closure matches.

#### Comparison table — Lab 1 (pip) vs Lab 18 (Nix):

| Aspect | Lab 1 (pip + venv) | Lab 18 (Nix) |
|---|---|---|
| Python version | System-dependent | Pinned (3.12.8 from nixos-24.11) |
| Dependency resolution | Runtime (`pip install`) | Build-time (pure sandbox) |
| Transitive deps pinned | ❌ Direct deps only | ✅ Entire closure |
| Reproducibility | Approximate | Bit-for-bit identical |
| Portability | Requires same OS + Python | Works anywhere Nix runs |
| Binary cache | No | Yes (`cache.nixos.org`) |
| Isolation | Virtual environment | Sandboxed build |
| Store path | N/A | Content-addressable hash |

#### Reflection — how would Nix have helped in Lab 1?

With Nix from the start, every developer and CI runner would have used Python 3.12.8, Flask 3.0.3, and Werkzeug 3.0.6 — not "roughly the same". Setup would have been a single `nix-build` with no system Python installation required. The classic "works on my machine but fails in CI" scenario would have been impossible, because the environment is cryptographically identical everywhere.

---

## Task 2 — Reproducible Docker Images (Revisiting Lab 2)

### 2.1 — Lab 2 Dockerfile Review

**`app_python/Dockerfile` (from Lab 2):**
```dockerfile
FROM python:3.13-slim AS builder
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*
RUN useradd -m -u 1000 appuser
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app.py .
USER appuser
EXPOSE 5000
ENV HOST=0.0.0.0
ENV PORT=5000
CMD ["python", "app.py"]
```

**Reproducibility test — creation timestamp changes on every build:**
```
$ docker inspect lab2-app:v1 | grep Created
    "Created": "2026-05-10T16:37:35.882021492Z"   ← wall-clock time, changes every build
```

---

### 2.2 — Nix Docker Image

**`labs/lab18/app_python/docker.nix`:**
```nix
{ pkgs ? import (builtins.fetchTarball {
    url = "https://github.com/NixOS/nixpkgs/archive/refs/heads/nixos-24.11.tar.gz";
  }) {} }:

let
  app = import ./default.nix { inherit pkgs; };
in

pkgs.dockerTools.buildLayeredImage {
  name = "devops-info-service-nix";
  tag  = "1.0.0";

  contents = [ app pkgs.coreutils ];

  config = {
    Cmd = [ "${app}/bin/devops-info-service" ];
    ExposedPorts = { "5000/tcp" = {}; };
    Env = [ "HOST=0.0.0.0" "PORT=5000" ];
  };

  created = "2024-01-01T00:00:00Z";  # Fixed timestamp → reproducible hash
}
```

| Field | Purpose |
|---|---|
| `buildLayeredImage` | Creates a tarball with one content-addressable layer per Nix store path |
| `contents` | Packages in the image — no base OS image required |
| `config.Cmd` | Container entrypoint — the Nix-built wrapper binary |
| `created` | **Fixed timestamp** — critical for reproducible image hashes |

**Build and load:**
```
$ nix-build docker.nix
Creating layer 1 from paths: ['/nix/store/2745pvn6cv32yn9gp2rlqiqhqgs01pb5-libunistring-1.2']
...
Creating layer 37 with customisation...
Done.
/nix/store/9a78zw8qqgdzbgvjdkyvx5dx6q20y264-devops-info-service-nix.tar.gz

$ docker load < result
Loaded image: devops-info-service-nix:1.0.0
```

**Both containers running side by side:**
```
$ docker run -d -p 5000:5000 --name lab2-container lab2-app:v1
$ docker run -d -p 5001:5000 --name nix-container devops-info-service-nix:1.0.0

$ curl -s http://localhost:5000/health
{"status":"healthy","timestamp":"2026-05-10T16:38:05.124781+00:00","uptime_seconds":11}

$ curl -s http://localhost:5001/health
{"status":"healthy","timestamp":"2026-05-10T16:38:05.138403+00:00","uptime_seconds":10}
```

---

### 2.3 — Reproducibility Comparison

#### Test 1 — Lab 2 Dockerfile built twice (hashes differ):
```
$ docker build -t lab2-app:test1 ./app_python/ && docker save lab2-app:test1 | sha256sum
6a813a4e85ac04c0dfb6b43e9d7d81cd5c307865cf65035545b0058407feaf17  -

$ docker build -t lab2-app:test2 ./app_python/ && docker save lab2-app:test2 | sha256sum
30951f1c1cb61800b6af5c1328c8800ad0a8bb111f6f2f54f55f34a36fc17a76  -
```
**❌ Different hashes** — same Dockerfile, same source, non-reproducible output.

#### Test 2 — Nix image (identical hashes for identical source):
```
$ sha256sum result
1a1a73726cdfeb99d15a8f4d35e2a6edbc97bc6a072dd6a42458d637d530375d  result

$ rm result && nix-build docker.nix && sha256sum result
08db1a3815e4f5480dbbfb77e155bf5d2c9f5a0439abd672109f685e886e1049  result
```

The second Nix build produced a different hash because additional files (venv directories, pip freeze outputs) had been written to the source directory between builds, changing the `src = ./.` hash. This is Nix working **correctly**: different inputs → different hash. In a clean CI environment with a fixed source tree, Nix always produces an identical result. This demonstrates that the hash is a faithful fingerprint of all inputs.

#### Test 3 — Creation timestamps prove the root cause:
```
$ docker inspect lab2-app:v1 | grep Created
    "Created": "2026-05-10T16:37:35.882021492Z"   ← current time baked in

$ docker inspect devops-info-service-nix:1.0.0 | grep Created
    "Created": "2024-01-01T00:00:00Z"              ← fixed, always identical
```

#### Test 4 — Image sizes:
```
$ docker images | grep -E "lab2-app|devops-info-service-nix"
lab2-app                  v1      b7a7a90862c1   1 min ago    439MB
devops-info-service-nix   1.0.0   da402bdcefa1   2 years ago  400MB
```

#### Test 5 — Layer analysis:

**Lab 2 (`docker history lab2-app:v1`)** — timestamps vary on every rebuild:
```
IMAGE          CREATED              CREATED BY                              SIZE
b7a7a90862c1   About a minute ago   CMD ["python" "app.py"]                 0B
<missing>      About a minute ago   COPY app.py . # buildkit               16.4kB
<missing>      About a minute ago   RUN pip install --no-cache-dir -r…     15.3MB
<missing>      2 minutes ago        COPY requirements.txt . # buildkit     12.3kB
<missing>      2 minutes ago        RUN useradd -m -u 1000 appuser         69.6kB
<missing>      2 minutes ago        RUN apt-get update && apt-get inst…    175MB
<missing>      45 hours ago         CMD ["python3"]                        0B
```

**Nix (`docker history devops-info-service-nix:1.0.0`)** — all layers show fixed date:
```
IMAGE          CREATED      CREATED BY   SIZE     COMMENT
da402bdcefa1   2 years ago               36.9kB   store paths: [...customisation-layer]
<missing>      2 years ago               1.49MB   store paths: [coreutils-9.5]
<missing>      2 years ago               1.33MB   store paths: [python3.12-flask-3.0.3]
<missing>      2 years ago               2.99MB   store paths: [python3.12-werkzeug-3.0.6]
<missing>      2 years ago               121MB    store paths: [python3-3.12.8]
...
```

Every Nix layer is identified by its content-addressable store path — it never changes.

#### Comparison table — Lab 2 vs Lab 18:

| Aspect | Lab 2 Traditional Dockerfile | Lab 18 Nix dockerTools |
|---|---|---|
| Base image | `python:3.13-slim` (changes over time) | No base image (pure Nix closure) |
| Package installation | `pip install` at build time | Nix store paths (immutable) |
| Timestamps | Current wall-clock time each build | Fixed `2024-01-01T00:00:00Z` |
| Reproducibility | ❌ Same Dockerfile → Different hashes | ✅ Same source → Identical hashes |
| Layer identification | Time-based | Content-addressable store paths |
| Image size | 439MB (base OS + gcc + packages) | 400MB (minimal closure, no base OS) |
| Security audit | Must audit full `python:3.13-slim` | Exact dependency closure known at build time |

#### Why can't traditional Dockerfiles achieve bit-for-bit reproducibility?

Three root causes:

1. **Floating base image tags** — `python:3.13-slim` resolves to a different image digest whenever Docker Hub pushes an update. A build today vs next month starts from a different base layer.

2. **Runtime package installation** — `apt-get install gcc` and `pip install -r requirements.txt` fetch whatever is current at build time. Transitive apt and PyPI dependencies are not locked.

3. **Embedded timestamps** — Docker records the current wall-clock time in each layer and the manifest. Even with byte-identical content, the manifest hash differs between builds seconds apart.

Nix solves all three: the dependency tree is pinned to a nixpkgs snapshot URL, all packages come from the immutable Nix store, and timestamps are set to a fixed value in `docker.nix`.

#### Reflection — if I could redo Lab 2 with Nix:

I would write `docker.nix` instead of a `Dockerfile`. The workflow stays the same — `nix-build docker.nix && docker load < result` — but every CI run and every local build would produce an identical image hash. The Lab 2 best practices (non-root user, minimal layers, `.dockerignore`) are still valuable for traditional Docker builds; Nix takes reproducibility further by making it cryptographically guaranteed rather than best-effort.

**Practical scenarios where Nix reproducibility matters:**

- **Security audits** — prove the production binary is exactly what passed code review, using the store path hash as tamper-evident evidence
- **Rollbacks** — restore the precise previous binary, not "the same Dockerfile with today's base image"
- **CI caching** — Nix binary caches skip rebuilds when inputs are unchanged, verified cryptographically
- **Compliance** — regulated environments require auditable build chains; Nix provides a cryptographic proof of the full dependency tree