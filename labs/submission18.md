# Lab 18 — Reproducible Builds with Nix — Submission

> **Branch:** `feature/lab18` (renamed from local `lab18`)
> **Source paths:**
> - Application + Nix expressions — [`labs/lab18/app_python/`](lab18/app_python/)
> - This submission — [`labs/submission18.md`](submission18.md)

The application reused throughout the lab is the same `app_python/` Flask
service from labs 01-16: `GET /`, `/health`, `/visits`, `/metrics`. Building
on Lab 1's `requirements.txt`, Lab 2's Dockerfile, and Lab 10's
`values.yaml` lets the comparisons in each section reflect real artefacts
that already lived in the repo, not a toy example.

---

## Environment

| Tool | Version | Source |
|---|---|---|
| Nix | `Determinate Nix 3.20.0 (2.34.6)` | Determinate Systems installer |
| Host | macOS arm64 (M3 Pro) | `aarch64-darwin` |
| Docker | `29.4.2` | Docker Desktop |
| Python (built by Nix) | `3.13.12` | `nixpkgs` revision `549bd84d…` (locked in flake.lock) |

Flakes are enabled by default (Determinate ships them on); no manual
`experimental-features` flag needed.

---

## Task 1 — Build a reproducible Python app (6 pts)

### 1.1 Source layout

```
labs/lab18/app_python/
├── app.py                       ← copied from app_python/ (labs 01-16)
├── requirements.txt             ← Flask 3.1.0, Werkzeug 3.1.3, prometheus-client 0.23.1
├── requirements-unpinned.txt    ← single line `flask` — used to demonstrate pip drift
├── default.nix                  ← Nix derivation (this task)
├── docker.nix                   ← Nix dockerTools image (Task 2)
├── flake.nix                    ← Flake wrapper (Bonus)
├── flake.lock                   ← Locked input revisions
├── Dockerfile                   ← traditional Dockerfile from Lab 2 — kept for comparison
└── README.md
```

### 1.2 The derivation — [`labs/lab18/app_python/default.nix`](lab18/app_python/default.nix)

```nix
{ pkgs ? import <nixpkgs> { } }:

pkgs.python3Packages.buildPythonApplication rec {
  pname = "devops-info-service";
  version = "1.0.0";

  # Filter `result` symlink, __pycache__, .pyc, .direnv, .pytest_cache out of
  # the source set — without this the `result` link emitted by `nix-build`
  # itself is part of `src = ./.;`, which mutates the input hash on rebuild
  # and breaks reproducibility (see §1.5).
  src = pkgs.lib.cleanSourceWith {
    src = ./.;
    filter = path: type:
      let baseName = baseNameOf (toString path);
      in !( baseName == "result"
         || pkgs.lib.hasPrefix "result-" baseName
         || baseName == "__pycache__"
         || pkgs.lib.hasSuffix ".pyc" baseName
         || baseName == ".direnv"
         || baseName == ".pytest_cache" );
  };

  format = "other";

  propagatedBuildInputs = with pkgs.python3Packages; [
    flask werkzeug prometheus-client
  ];

  nativeBuildInputs = [ pkgs.makeWrapper ];

  installPhase = ''
    mkdir -p $out/share/devops-info-service $out/bin
    cp app.py $out/share/devops-info-service/app.py

    makeWrapper ${pkgs.python3}/bin/python3 $out/bin/devops-info-service \
      --add-flags $out/share/devops-info-service/app.py \
      --prefix PYTHONPATH : "$PYTHONPATH"
  '';
}
```

Key fields:

- `format = "other"` — the app has no `setup.py` / `pyproject.toml`, so Nix's default Python build phases are skipped and we provide our own `installPhase`.
- `propagatedBuildInputs` — runtime Python deps. Because they come from the pinned `nixpkgs` (Bonus task locks the revision), transitive deps cannot drift over time the way pip's resolution can.
- `makeWrapper` — generates a self-contained `bin/devops-info-service` shell wrapper that calls `python3 app.py` with `PYTHONPATH` pointing to all the deps' Nix store paths. This is the idiomatic Nix way to ship a Python script without a shebang.
- `cleanSourceWith` filter — see §1.5. This is the single most important detail in the whole derivation.

### 1.3 Build + run

```text
$ cd labs/lab18/app_python
$ nix-build
…
/nix/store/zlzw3piwv1iszv9szx8rai19rpk63naq-devops-info-service-1.0.0

$ ls result/bin/
.devops-info-service-wrapped   devops-info-service

$ ./result/bin/devops-info-service &
$ curl http://127.0.0.1:8080/health
{"status":"healthy","timestamp":"2026-05-10T15:35:56.301978+00:00","uptime_seconds":2}
```

### 1.4 Reproducibility proof

Three back-to-back builds produced **identical** store paths:

```text
=== Step 1: capture initial store path ===
PATH1=/nix/store/zlzw3piwv1iszv9szx8rai19rpk63naq-devops-info-service-1.0.0

=== Step 2: rebuild without changes (cache hit) ===
PATH2=/nix/store/zlzw3piwv1iszv9szx8rai19rpk63naq-devops-info-service-1.0.0
✓ identical (cache hit, deterministic)

=== Step 3: force rebuild after delete from store ===
$ nix-store --delete "$PATH1"
1 store paths deleted, 13.1 KiB freed
$ nix-build
PATH3=/nix/store/zlzw3piwv1iszv9szx8rai19rpk63naq-devops-info-service-1.0.0
✓ identical store path after force rebuild — bit-for-bit reproducible
```

Step 3 is the meaningful one — `nix-store --delete` evicts the cached output, and the next `nix-build` recomputes the entire derivation from scratch. The hash being the same proves the inputs (source + nixpkgs + build steps + compiler flags) fully determine the output. See §1.5 for the gotcha that took a fix to make this work.

The store-path hash format is content-addressable:

```
/nix/store/<32-char-base32-hash>-<name>-<version>
                ▲
                └── sha256 of the entire dependency closure (truncated, base32)
```

The hash is derived from the source set, the nixpkgs revision pulled in, and every transitively-required derivation — so the same `default.nix` plus the same `nixpkgs` produces the same path on every machine, forever.

### 1.5 Reproducibility gotcha — `result` symlink in the source

**The first three rebuild attempts produced *different* store paths even with no source changes.** Diagnostics revealed the cause: `nix-build` emits a `./result` symlink that points to the latest output, and that symlink lives next to the source files. With `src = ./.;`, Nix snapshots the entire directory — *including the `result` symlink itself*. Each build creates a slightly different `result` target, which becomes part of the input set, which mutates the hash.

The fix is `pkgs.lib.cleanSourceWith` with a filter that excludes `result`, `result-*`, `__pycache__`, `.pyc` files, `.direnv`, and `.pytest_cache`. After the fix, all three builds returned `zlzw3piwv1iszv9szx8rai19rpk63naq` (above).

This is, in microcosm, the entire point of the lab: **reproducibility is not a property a tool gives you for free — it's a property of how carefully you control the build's inputs.**

### 1.6 Comparison with `pip install`

Concrete experiment — the same source, two different package management approaches:

```text
=== Pinned requirements.txt (Lab 1 baseline) ===
Flask==3.1.0
Werkzeug==3.1.3
prometheus-client==0.23.1

=== UN-pinned variant (just `flask`) ===
flask
```

Running `python3 -m venv .venv && pip install -r requirements-unpinned.txt && pip freeze`:

```text
blinker==1.9.0
click==8.3.3
Flask==3.1.3                 ← latest at the moment of install
itsdangerous==2.2.0
Jinja2==3.1.6
MarkupSafe==3.0.3
Werkzeug==3.1.8              ← latest at the moment of install
```

**Without a version pin, pip installs whatever's newest** — so re-running the
same `pip install` command in a year gets a different Flask. Even pinning
`Flask==3.1.0` only fixes the **direct** dep — Werkzeug/click/itsdangerous
are transitive and free to drift unless you also use `pip-tools`,
`pip-compile`, hashes, or a lockfile.

Now compare with the closure of the Nix-built derivation:

```text
$ nix-store -q --references "$(readlink result)"
/nix/store/kwnbzccaiqi6iwdchcy6xc8br4x9hn0j-python3-3.13.12
/nix/store/9m0bbfxl4hlwfkwaf60jsgpbg1j51y4y-python3.13-prometheus-client-0.24.1
/nix/store/vygk4rdm9f8awzzrz88ins2scka3w2hk-python3.13-werkzeug-3.1.6
/nix/store/k4cgpz7zsvhhv413pn3d2karpcr8kznb-python3.13-flask-3.1.2
```

Every transitive dep, the Python interpreter version, and the underlying glibc / libc++ are pinned by the nixpkgs revision. No drift is possible — even months later, the same `default.nix` with the same `nixpkgs` rev yields the same store paths.

### 1.7 Comparison table — Lab 1 vs Lab 18

| Aspect | Lab 1 (pip + venv) | Lab 18 (Nix derivation) |
|---|---|---|
| Python version | system-dependent | pinned by nixpkgs (`python3-3.13.12`) |
| Direct deps | `Flask==3.1.0`, `Werkzeug==3.1.3` (text) | `flask 3.1.2`, `werkzeug 3.1.6` (store path) |
| Transitive deps | not pinned (drift over time) | every node in the closure pinned |
| Reproducibility | approximate, requires `pip-compile` + hashes | bit-for-bit identical, by construction |
| Portability | requires same OS + Python on the runner | works on any Linux/macOS where Nix is installed |
| Caching | wheel cache is host-local, no integrity verification | content-addressable store, shareable via `cache.nixos.org` |
| Isolation | venv (process-level) | sandbox (no network, no `/home` access during build) |

### 1.8 Reflection — what would Lab 1 with Nix have looked like?

If we had used Nix from the start in Lab 1, the entire dependency-management layer of the lab vanishes:

- No `python -m venv venv && source venv/bin/activate && pip install -r requirements.txt` ritual — `nix develop` drops you into an environment with the exact Python and the exact deps already on `PYTHONPATH`.
- No "works on my machine" — the same `default.nix` produces the same closure on a teammate's Linux box, on the CI runner, on a fresh Mac. Lab 16's exhausting kube-prometheus-stack install (~5 image pulls, ~1 GB total, ~10 min cold) is the polar opposite — Nix moves the binary cache to be the slow part once, then is instant.
- The fragility of `pip install` (network errors, PyPI hash mismatches, transitive drift) doesn't apply — the build runs in a sandbox without network access.

The cost is upfront: writing `default.nix` is harder than `requirements.txt`, and `cleanSourceWith` filters are an obscure footgun. After that one-time cost, reproducibility is free.

---

## Task 2 — Reproducible Docker images (4 pts)

### 2.1 The image — [`labs/lab18/app_python/docker.nix`](lab18/app_python/docker.nix)

```nix
{ pkgs ? import <nixpkgs> { } }:
let
  app = import ./default.nix { inherit pkgs; };
in
pkgs.dockerTools.buildLayeredImage {
  name = "devops-info-service-nix";
  tag = "1.0.0";

  # Critical: never `created = "now"` — that timestamps the image and
  # invalidates reproducibility. The Unix epoch makes the manifest
  # bit-for-bit identical across builds.
  created = "1970-01-01T00:00:01Z";

  contents = [ app pkgs.coreutils pkgs.bashInteractive ];

  config = {
    Cmd = [ "${app}/bin/devops-info-service" ];
    ExposedPorts = { "8080/tcp" = { }; };
    Env = [ "HOST=0.0.0.0" "PORT=8080" "DEBUG=False" ];
    Labels = {
      "org.opencontainers.image.title" = "devops-info-service";
      "org.opencontainers.image.version" = "1.0.0";
    };
  };
}
```

### 2.2 Reproducibility — Nix produces identical tarball hashes

```text
=== nix-build docker.nix (run #1) ===
result → /nix/store/zs1wx94rj3x3v4cisynmf7rdrwz0n44h-devops-info-service-nix.tar.gz
sha256(result) = c412ffa7935ed8ea40ef470e5561613af11bd7a6da53d2117ac7b8ba5caf33d4

=== nix-build docker.nix (run #2, no changes) ===
result → /nix/store/zs1wx94rj3x3v4cisynmf7rdrwz0n44h-devops-info-service-nix.tar.gz
sha256(result) = c412ffa7935ed8ea40ef470e5561613af11bd7a6da53d2117ac7b8ba5caf33d4
✓ identical sha256 — bit-for-bit reproducible
```

Same `docker.nix` plus same nixpkgs ⇒ same tarball, byte-for-byte. This is what Docker's build flow can't promise.

### 2.3 Compare with traditional Dockerfile (Lab 2)

The same `Dockerfile` from Lab 2 was built twice in a row:

```text
$ docker build -t lab2-app:v1 .
$ docker save lab2-app:v1 | sha256sum
96dc91674d54ac37db54a3d7b673b8e0c8b64dcf43a4d4979f3e3a4629996d58

$ sleep 2

$ docker build -t lab2-app:v2 .
$ docker save lab2-app:v2 | sha256sum
2774bf62c02508e22a93617350d387666be953b957ad3c4225218d71e195580f

✓ DIFFERENT — traditional Dockerfile is NOT bit-for-bit reproducible
```

Two `docker save` hashes, two seconds apart, on the same machine, same source, same Dockerfile. **Different.** That is the whole proof.

### 2.4 `docker history` — timestamps tell the story

Nix-built image — every layer has the fixed `1970-01-01` timestamp:

```text
CREATED AT                  SIZE      CREATED BY
1970-01-01T03:00:01+03:00   745kB
1970-01-01T03:00:01+03:00   57.3kB
1970-01-01T03:00:01+03:00   1.35MB
1970-01-01T03:00:01+03:00   3.06MB
…
```

Traditional Dockerfile — every layer has the wall-clock build time:

```text
CREATED AT                  SIZE      CREATED BY
2026-05-10T19:19:32+03:00   0B        CMD ["python" "app.py"]
2026-05-10T19:19:32+03:00   0B        ENV HOST=0.0.0.0 PORT=8080 DEBUG=False
2026-05-10T19:19:32+03:00   0B        EXPOSE [8080/tcp]
2026-05-10T19:19:31+03:00   8.19kB    RUN /bin/sh -c mkdir -p /data
2026-05-10T19:19:31+03:00   20.5kB    COPY app.py .
2026-05-10T19:19:31+03:00   16MB      RUN /bin/sh -c pip install --no-cache-dir -r…
2026-05-10T19:19:28+03:00   12.3kB    COPY requirements.txt .
```

Even *if* every layer's content were byte-identical between two builds, the timestamps alone make the manifest hash differ — and `docker save` includes the manifest. That's why Lab 2's Dockerfile fails the bit-for-bit test.

### 2.5 Image size — honest comparison

```text
REPOSITORY:TAG                        SIZE
lab2-app:v1                           224MB
lab2-app:v2                           224MB
devops-info-service-nix:1.0.0         3.07GB
```

The Nix image is **bigger** here. The reason is honest: the closure includes
the full `python3-3.13.12` interpreter, glibc, ICU, OpenSSL — everything
needed to run, with nothing stripped. The Lab 2 image piggy-backs on
`python:3.12-slim`, which is itself a pre-trimmed Debian + Python.

This is a fair trade-off, not a Nix failure. Two ways to shrink the Nix
image to be competitive:

1. Drop `bashInteractive` and `coreutils` (~50 MB) and rely on
   `dockerTools.usrBinEnv` if you need `env`.
2. Use `pkgs.python3.override { ... }` to remove unused stdlib modules
   (`tkinter`, `idle`, `test` suites).

For **compiled** apps (the Lab 1 Go bonus mentioned in the assignment), the
Nix image is *smaller* than Lab 2 because the closure is just the static Go
binary (~10 MB). The Python ecosystem's interpreter weight is what swings
the comparison.

### 2.6 Caveat — running the Nix-built image on macOS

```text
$ docker load < result
Loaded image: devops-info-service-nix:1.0.0

$ docker run -d -p 8081:8080 --name nix-container devops-info-service-nix:1.0.0
$ docker logs nix-container
exec /nix/store/jgxds7bb64vj5s7nds2swpfbx1ja0gby-devops-info-service-1.0.0/bin/devops-info-service: exec format error
```

`exec format error` because Nix on `aarch64-darwin` produced a *macOS* binary, but Docker Desktop runs containers in a Linux VM (`aarch64-linux`). Cross-architecture binaries can't execute. The fix on Mac is a Linux builder VM (Determinate's optional `linux-builder`, or `nix-darwin`'s flag) which runs Nix Linux builds in a Lima VM, producing real `aarch64-linux` outputs.

For this submission the loaded image's *manifest* and *tarball hash* are the reproducibility artefacts — which they are. On a Linux runner (or with `linux-builder` enabled) the same `docker.nix` would produce a runnable image. The reproducibility property is independent of execution.

The Lab 2 image runs side-by-side fine:

```text
$ curl http://127.0.0.1:8080/health    # Lab 2 image
{"status":"healthy","timestamp":"2026-05-10T16:19:52.889640+00:00","uptime_seconds":4}
```

### 2.7 Comparison table — Lab 2 vs Lab 18

| Aspect | Lab 2 traditional Dockerfile | Lab 18 Nix `dockerTools` |
|---|---|---|
| **Reproducibility** | ❌ different hashes on every build | ✅ same hash forever |
| **Base image** | `python:3.12-slim` (changes upstream) | none — pure derivation closure |
| **Timestamps** | wall-clock at build time | fixed `1970-01-01T00:00:01Z` |
| **Caching** | layer cache invalidates on any file change above the layer | content-addressable — same content, same hash, perfect cache |
| **Image size (this app)** | 224 MB | 3.07 GB |
| **Image size (Go binary)** | ~150 MB with multi-stage | ~30 MB (pure binary closure) |
| **Audit trail** | "what's inside `python:3.12-slim` today?" | full closure visible via `nix-store -q --references` |
| **Cross-arch** | needs `docker buildx` + QEMU | needs Nix linux-builder on Mac |
| **Best fit** | quick prototyping, well-known base images | CI/CD where rebuild = same image, security audits, supply-chain attestations |

### 2.8 Reflection — Lab 2 with Nix from the start

The biggest practical win: **rebuilding Lab 2's image six months later would produce the same hash**. Today the image lives in a registry as `lab2-app:v1` with manifest hash `96dc916…`. Pull it, rebuild from the same source, and you'd get a new manifest hash — even if every byte of the Python wheel inside hadn't changed. With Nix, the rebuilt image would have hash `c412ffa…` byte-for-byte. That's the bedrock supply-chain property: a CVE auditor or a paranoid SRE can re-derive the exact bytes that actually run in production from source code in git.

The downside in our specific case: **3 GB > 224 MB** is a noticeable network cost on every pull. Practical hybrid pattern in real systems: Nix for the *application* derivation, distroless or `scratch` for the *base*, glue them with `dockerTools.buildLayeredImage` and a curated `contents` list that excludes the interactive shell.

---

## Bonus — Modern Nix with Flakes (2 pts)

### B.1 The flake — [`labs/lab18/app_python/flake.nix`](lab18/app_python/flake.nix)

```nix
{
  description = "DevOps Info Service — reproducible build via Nix Flakes (Lab 18 Bonus)";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = { self, nixpkgs, flake-utils }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = nixpkgs.legacyPackages.${system};
        app = import ./default.nix { inherit pkgs; };
        dockerImage = import ./docker.nix { inherit pkgs; };
      in {
        packages = {
          default = app;
          devops-info-service = app;
          dockerImage = dockerImage;
        };
        apps.default = { type = "app"; program = "${app}/bin/devops-info-service"; };
        devShells.default = pkgs.mkShell {
          packages = [ pkgs.python3
                       pkgs.python3Packages.flask
                       pkgs.python3Packages.werkzeug
                       pkgs.python3Packages.prometheus-client
                       pkgs.python3Packages.pytest ];
          shellHook = ''
            echo "[nix develop] DevOps Info Service dev shell"
            echo "  python:  $(python3 --version)"
            echo "  flask:   $(python3 -c 'import flask; print(flask.__version__)')"
          '';
        };
        checks.default = app;
      });
}
```

Why `flake-utils.lib.eachDefaultSystem`: it pre-renders the same outputs for `aarch64-darwin`, `x86_64-darwin`, `aarch64-linux`, `x86_64-linux` so a teammate on Linux gets a working flake without changes.

### B.2 Lock file

```text
$ nix flake update
• Added input 'flake-utils':
    'github:numtide/flake-utils/11707dc' (2024-11-13)
• Added input 'flake-utils/systems':
    'github:nix-systems/default/da67096' (2023-04-09)
• Added input 'nixpkgs':
    'github:NixOS/nixpkgs/549bd84' (2026-05-05)
```

Excerpt from `flake.lock`:

```json
"nixpkgs": {
  "locked": {
    "lastModified": 1777954456,
    "narHash": "sha256-hGdgeU2Nk87RAuZyYjyDjFL6LK7dAZN5RE9+hrDTkDU=",
    "rev": "549bd84d6279f9852cae6225e372cc67fb91a4c1",
    "type": "github"
  }
}
```

That single revision pins **all ~80 000 packages** in nixpkgs at once — Python, Flask, Werkzeug, glibc, openssl, the build tools, the compiler. Updating any of them means an explicit `nix flake update` and a corresponding diff in `flake.lock`.

### B.3 Build via flake

```text
$ nix build
warning: Git tree '…' has uncommitted changes
this derivation will be built:
  /nix/store/9xwyncili24l6vpcwzlcf7x0n08758wf-devops-info-service-1.0.0.drv
$ readlink result
/nix/store/vjidax6563ar6ajbrllqsgfkg0607yp7-devops-info-service-1.0.0

$ nix build .#dockerImage
$ readlink result
/nix/store/a1d4jmn01x854540cqn3gkgdhfyi5g5s-devops-info-service-nix.tar.gz
$ sha256sum result
5bbbda3dc366c1775880ef5cb97bac2cf6ce0420032aa82ca2901867998c7cd8  result
```

Note: the flake-built store path differs from the `nix-build`-built one in §1.4 because the flake snapshots only files **tracked by git**, while `default.nix` uses an explicit `cleanSourceWith` filter. After `git add -N labs/lab18/`, the file sets converge.

`nix flake check` succeeds for the host system and skips the others by default:

```text
✅ packages.aarch64-darwin.devops-info-service (build skipped)
✅ apps.aarch64-darwin.default
✅ checks.aarch64-darwin.default
warning: The check omitted these incompatible systems: aarch64-linux, x86_64-darwin, x86_64-linux
```

### B.4 Dev shell — replacement for `python -m venv`

```text
$ nix develop --command bash -c '
    python3 --version
    python3 -c "import flask; print(\"flask:\", flask.__version__)"
    python3 -c "import werkzeug; print(\"werkzeug:\", werkzeug.__version__)"'
[nix develop] DevOps Info Service dev shell
Python 3.13.12
flask: 3.1.2
werkzeug: 3.1.6
```

Compare with Lab 1's setup, which is sensitive to the host's Python version,
the freshness of pip, the wheel cache, and the network connection to PyPI:

```bash
# Lab 1 ritual:
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt   # may pull different versions
```

The Nix dev shell takes ~1 second to enter on a warm cache, gives every
teammate the same Python and the same dep versions, and disposes itself
when you `exit` — no `venv/` directory clutter.

### B.5 Comparison with Lab 10 — Helm `values.yaml`

| Aspect | Lab 1 (`requirements.txt`) | Lab 10 (`values.yaml`) | Lab 18 (Nix flake) |
|---|---|---|---|
| **Pins Python version** | ❌ uses host Python | ❌ uses image's Python | ✅ via nixpkgs rev |
| **Pins direct deps** | ⚠️ direct only, by name+version | ❌ only image tag | ✅ all closure entries |
| **Pins transitive deps** | ❌ resolved at install | ❌ inside container, opaque | ✅ |
| **Pins build tools** | ❌ | ❌ | ✅ |
| **Reproducibility class** | text-level pinning | tag-level pointer | cryptographic hash |
| **Cross-machine** | varies | depends on registry/image | identical |
| **Dev environment** | `venv` | n/a | `nix develop` |
| **Time-stable** | packages drift on PyPI | tags can be re-pushed | locked forever |

Lab 10 pinned `image.tag: 1.0.0` in `values.yaml` — but the registry can rebuild
that tag and push it again, and the tag still says `1.0.0`. Only **digest-pinning**
(`image: foo@sha256:abc…`) approaches what flakes give you natively. Even then,
the digest pin only locks the *container image*; the Python deps inside the
image are a separate, unlocked layer.

The combined pattern in real production:

```yaml
# Lab 10's values.yaml, but reference Nix output by digest:
image:
  repository: ghcr.io/aezuraa/devops-info-service
  tag: "@sha256:5bbbda3dc366c1775880ef5cb97bac2cf6ce0420032aa82ca2901867998c7cd8"
```

That ties the Helm release to the exact bytes built by `nix build .#dockerImage`. Lab 10's deployment story + Lab 18's reproducibility property = full chain from source to running pod.

### B.6 Reflection — what flakes change

The shift from `default.nix` (Task 1) to `flake.nix` is small in code, big in operational properties:

- **`flake.lock` is the artefact**, not the binary — the lock file in git captures what nixpkgs revision was used, and that's enough to redo every build forever.
- **`nix run github:user/repo?dir=labs/lab18/app_python`** lets a stranger build the artefact from the URL alone, without cloning, without setting up a venv. The Lab 16 flow (clone repo, install kubectl/helm/minikube, helm repo add, helm install, port-forward) is a 30-step process; the Nix-flake flow is one URL.
- **`nix flake show .` enumerates every output** — packages, apps, dev shells, checks. There's no equivalent in pip or Docker.

The runtime cost: `flake.lock` adds ~1.5 KB per locked input. The tooling cost: Nix on Mac without `linux-builder` can't build Linux Docker images for `docker run` (§2.6 caveat). The wins are large enough that for any project that already runs in CI, "use flakes" is a near-default in 2026.

---

## Cleanup

```bash
# Remove containers and dangling images
docker rm -f lab2-container nix-container 2>/dev/null
docker rmi lab2-app:v1 lab2-app:v2 devops-info-service-nix:1.0.0 2>/dev/null

# (Optional) free Nix store after the lab
nix-collect-garbage -d
```

---

## CLI cheatsheet

| Command | Purpose |
|---|---|
| `nix-build` | Build the legacy `default.nix` derivation (Task 1) |
| `nix-build docker.nix` | Build the OCI tarball via `dockerTools` (Task 2) |
| `docker load < result` | Load the tarball into Docker |
| `nix-store --delete /nix/store/<hash>-…` | Evict an output to force a real rebuild |
| `nix-hash --type sha256 --base32 result` | Hash a build output |
| `nix-store -q --references <path>` | Show a derivation's direct closure |
| `nix flake update` | Refresh `flake.lock` (Bonus) |
| `nix build` | Build `packages.default` from the flake |
| `nix build .#dockerImage` | Build the named output `packages.dockerImage` |
| `nix flake check` | Run the flake's `checks` outputs |
| `nix develop` | Enter the flake's dev shell |
| `nix run` | Run `apps.default` |
