# Lab 18 — Reproducible Builds with Nix

- Branch: `lab18` (based on `lab17`)
- Date: 2026-05-14
- Tasks completed: Task 1 (6 pts) and Task 2 (4 pts). Bonus (Flakes) intentionally skipped.
- Application: the FastAPI DevOps Info Service from Lab 1 / Lab 2 lives at `app_python/`; the lab adds `app_python/default.nix` and `app_python/docker.nix`.
- All experiments were run on this machine (Linux 6.17, x86_64). Screenshots are replaced by verbatim terminal output captured from the same shell session.

---

## Task 1 — Reproducible Python build

### 1.1 Installation steps and verification output

```
$ curl --proto '=https' --tlsv1.2 -sSf -L https://install.determinate.systems/nix | sh -s -- install
...
INFO Running self test for shell bash
Nix was installed successfully!

$ . /nix/var/nix/profiles/default/etc/profile.d/nix-daemon.sh
$ nix --version
nix (Determinate Nix 3.20.0) 2.34.6
$ nix-build --version
nix-build (Determinate Nix 3.20.0) 2.34.6
```

### 1.2 App preparation

The `lab18` branch is based on `lab17`, so the existing `app_python/` tree from Lab 1/2 is already in place: `app.py`, `config.py`, `metrics.py`, `routes/`, `services/`, `models/`, `requirements.txt`, and the original `Dockerfile`. The lab adds two new files alongside the app: `app_python/default.nix` and `app_python/docker.nix`. The Lab 1 dependencies in `requirements.txt` are:

```
fastapi==0.115.0
uvicorn[standard]==0.32.0
prometheus-client==0.23.1
```

### 1.3 `default.nix` with explanations of each field

`app_python/default.nix`:

```nix
{ pkgs ? import <nixpkgs> {} }:

let
  pythonEnv = pkgs.python3.withPackages (ps: with ps; [
    fastapi
    uvicorn
    prometheus-client
  ]);
in
pkgs.stdenv.mkDerivation {
  pname = "devops-info-service";
  version = "1.0.0";
  src = pkgs.lib.cleanSourceWith {
    src = ./.;
    filter = path: type:
      let base = baseNameOf path; in
      !(builtins.elem base [ "result" "default.nix" "docker.nix" "flake.nix" "flake.lock" ])
      && !(pkgs.lib.hasPrefix "result-" base)
      && !(pkgs.lib.hasSuffix ".pyc" base)
      && base != "__pycache__";
  };

  nativeBuildInputs = [ pkgs.makeWrapper ];
  buildInputs = [ pythonEnv ];

  dontBuild = true;

  installPhase = ''
    runHook preInstall
    mkdir -p $out/share/devops-info-service $out/bin
    cp app.py config.py metrics.py $out/share/devops-info-service/
    cp -r routes services models $out/share/devops-info-service/
    makeWrapper ${pythonEnv}/bin/python $out/bin/devops-info-service \
      --add-flags "$out/share/devops-info-service/app.py" \
      --set PYTHONDONTWRITEBYTECODE 1
    runHook postInstall
  '';
}
```

| Field | Role |
| --- | --- |
| `pkgs ? import <nixpkgs> {}` | Allows the caller to inject a pinned `pkgs`; defaults to the active channel. |
| `pythonEnv` | A single Python closure containing the interpreter (`python3` = 3.13.12) plus every dependency transitively. |
| `pname` / `version` | Concatenated into the store path: `<hash>-devops-info-service-1.0.0`. |
| `src` | The source tree. `cleanSourceWith` filters out build outputs (`result`, `result-*`), the Nix files themselves, `*.pyc`, and `__pycache__`, so an unrelated leftover in the working directory cannot affect the input hash. |
| `nativeBuildInputs = [ makeWrapper ]` | Provides `makeWrapper` / `wrapProgram` to the install phase. |
| `buildInputs = [ pythonEnv ]` | Makes the Python interpreter and its deps available during the build. |
| `dontBuild = true` | Pure Python — no compile step. |
| `installPhase` | Copies the source into `$out/share/...`, then creates `$out/bin/devops-info-service` as a wrapper that invokes the pinned `python` on `app.py`. `PYTHONDONTWRITEBYTECODE=1` suppresses `__pycache__` generation at runtime. |

### 1.4 Build and run

```
$ nix-build
...
/nix/store/2j57476japg4qh9p44mc0d20kkgm8kaf-devops-info-service-1.0.0

$ ./result/bin/devops-info-service &
$ curl -s http://localhost:8000/health
{"status":"healthy","timestamp":"2026-05-14T19:23:38.562089+00:00","uptime_seconds":2}
```

Behaviour matches the Lab 1 venv version exactly: uvicorn boots, the FastAPI routes respond, `/health` returns 200.

### 1.5 Store path from multiple builds (prove they are identical)

Three builds were run:

```
Build 1: fresh nix-build
  store_path = /nix/store/2j57476japg4qh9p44mc0d20kkgm8kaf-devops-info-service-1.0.0
  nar_hash   = ade943e70b420fe5fb16119f87b3423ddd6700d814ff4d65fe7fb536fe0fad4b

Build 2: rm result && nix-build  (cache hit; exact same store path)
  store_path = /nix/store/2j57476japg4qh9p44mc0d20kkgm8kaf-devops-info-service-1.0.0
  nar_hash   = ade943e70b420fe5fb16119f87b3423ddd6700d814ff4d65fe7fb536fe0fad4b

Build 3: nix-build --check  (forces a full sandboxed rebuild and byte-compares
                              against the cached output; non-zero exit if any
                              difference is found)
  exit       = 0
  store_path = /nix/store/2j57476japg4qh9p44mc0d20kkgm8kaf-devops-info-service-1.0.0
  nar_hash   = ade943e70b420fe5fb16119f87b3423ddd6700d814ff4d65fe7fb536fe0fad4b
```

`nix-build --check` is the strongest test the toolchain offers: it re-runs the derivation in a fresh sandbox and aborts if a single byte of any output differs. It passed.

### 1.6 Explanation of the Nix store path format

```
/nix/store/2j57476japg4qh9p44mc0d20kkgm8kaf-devops-info-service-1.0.0
\_________/\______________________________/ \_______________________/
 store root  32-char base32 input hash       pname-version
```

| Segment | Meaning |
| --- | --- |
| `/nix/store` | Root of the content-addressable store. Every package lives directly under here. |
| `2j57476j…m8kaf` | A base32 hash of the derivation's *inputs* — every source file, every transitive dependency (interpreter, fastapi, starlette, pydantic, anyio, glibc, gcc-wrapper, …), every build flag, and the build script. |
| `devops-info-service-1.0.0` | `pname` + `-` + `version`, included for human readability only. The hash is what makes the path unique. |

Same inputs ⇒ same hash ⇒ Nix reuses the cached output. Different inputs (a code change, a different nixpkgs revision, a different `propagatedBuildInputs`) ⇒ different hash ⇒ a fresh build. This is also what makes `cache.nixos.org` safe to share: anyone whose inputs hash to the same value can download the prebuilt artefact and be certain it is what they would have built locally.

### 1.7 Comparison table — `pip install -r requirements.txt` vs Nix derivation

| Aspect | Lab 1 (pip + venv) | Lab 18 (Nix) |
| --- | --- | --- |
| Python version | Whatever `python3` resolves to on the host | Pinned by nixpkgs revision (3.13.12) |
| Direct deps | Pinned to a single version (`fastapi==0.115.0`) | Pinned by nixpkgs revision |
| Transitive deps | Re-resolved by pip on every install; can drift | Pinned by nixpkgs revision |
| Build environment | Whatever happens to be on PATH | Sandboxed; no network, no `/home`, no system libs |
| Output identity | Not defined — there is no single artefact | Store path `…-devops-info-service-1.0.0`; NAR hash `ade943e7…` |
| Cross-machine reproducibility | Best-effort, depends on hosts agreeing | Identical store path by construction |
| Prebuilt artefact sharing | None | `cache.nixos.org`, keyed on the input hash |

### 1.8 Why does `requirements.txt` provide weaker guarantees than Nix?

1. **It only pins what *you* installed, not what *they* installed.** `fastapi==0.115.0` is pinned, but fastapi's own requirements (starlette, pydantic, anyio, idna, sniffio, typing-extensions, …) are version ranges. pip re-resolves them on each install and can pick different concrete versions depending on the day, the platform, or which wheels happen to be on PyPI.
2. **The interpreter is unpinned.** `requirements.txt` says nothing about the Python version. The same file produces different bytecode and ABI on Python 3.11 vs 3.13.
3. **The toolchain is unpinned.** C extensions (pydantic-core, uvloop) are compiled against whatever C library, compiler, and headers the host happens to have. The wheel you get tomorrow may have been rebuilt against a newer glibc.
4. **No input hash is recorded.** There is no single value that says "this environment is the same as before". `pip freeze` is closer, but still excludes the interpreter and the toolchain.

Nix removes all four problems by hashing the entire input set — interpreter, every package source, every build tool, every flag — into the store path. The package is identical, or it has a different name. There is no in-between.

### 1.9 Lab 1 app running from the Nix-built version

CLI replacement for a screenshot (same shell session as the build above):

```
$ readlink result
/nix/store/2j57476japg4qh9p44mc0d20kkgm8kaf-devops-info-service-1.0.0

$ ./result/bin/devops-info-service &
{"timestamp": "2026-05-14T19:23:35.865473Z", "level": "INFO",
 "logger": "__main__", "message": "Starting DevOps Info Service",
 "module": "app", "function": "<module>", "line": 161,
 "method": "STARTUP", "path": "0.0.0.0:8000"}
INFO:     Started server process [126122]
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)

$ curl -s http://localhost:8000/health
{"status":"healthy","timestamp":"2026-05-14T19:23:38.562089+00:00","uptime_seconds":2}
```

The wrapper at `./result/bin/devops-info-service` invokes the Nix-pinned Python on the source copied into the store, with no virtualenv and no `pip install` step on the host.

### 1.10 Reflection — how would Nix have helped in Lab 1 from the start?

Three concrete classes of pain it would have removed:

1. **Reviewer setup friction.** Anyone reviewing Lab 1 had to install the right Python, create a venv, and `pip install -r requirements.txt`. With Nix the only command is `nix-build` (or `nix run`), and they get exactly the binary I tested.
2. **Drift between weeks.** Between Lab 1 and later labs, my own dev machine's Python and pip cache change. A fresh checkout next week could resolve to a different starlette pin. With Nix the inputs are frozen by the nixpkgs revision; `nix-build` next year produces the same artefact as today.
3. **CI parity.** CI runners are almost never the same OS image as a dev laptop. With pip, "works on my machine" is structural. With Nix, the build closure is identical on both because both consume the same pinned nixpkgs.

---

## Task 2 — Reproducible Docker image with Nix

### 2.1 Lab 2 Dockerfile (under review)

`app_python/Dockerfile`:

```dockerfile
FROM python:3.13-slim
RUN groupadd -r -g 1000 appuser && useradd -r -u 1000 -g appuser -d /app -s /sbin/nologin appuser
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
RUN mkdir -p /data && chown -R appuser:appuser /app /data
USER appuser
EXPOSE 8000
CMD ["python", "app.py"]
```

### 2.2 `docker.nix` with explanations of each field

`app_python/docker.nix`:

```nix
{ pkgs ? import <nixpkgs> {} }:

let
  app = import ./default.nix { inherit pkgs; };
in
pkgs.dockerTools.buildLayeredImage {
  name = "devops-info-service-nix";
  tag = "1.0.0";

  contents = [ app pkgs.cacert ];

  config = {
    Cmd = [ "${app}/bin/devops-info-service" ];
    ExposedPorts = { "8000/tcp" = {}; };
    Env = [ "HOST=0.0.0.0" "PORT=8000" ];
  };

  created = "1970-01-01T00:00:01Z";
}
```

| Field | Role |
| --- | --- |
| `import ./default.nix { inherit pkgs; }` | Reuses the application derivation from Task 1, so the image content is exactly what `nix-build` already produced. |
| `dockerTools.buildLayeredImage` | Splits the closure into many small content-addressed layers (better cache reuse than `buildImage`). |
| `name` / `tag` | The Docker repository / tag the image is loaded under. |
| `contents` | The store paths to include in the image: the app and `cacert` for outbound HTTPS. There is no base image — only the closures listed. |
| `config.Cmd` | Default command; the wrapper from Task 1. |
| `config.ExposedPorts` | Equivalent of Dockerfile `EXPOSE`. |
| `config.Env` | App reads `HOST`/`PORT` from `os.getenv(...)` (see `config.py`). |
| `created = "1970-01-01T00:00:01Z"` | The only correct value for reproducibility. Using `"now"` would salt every build with wall-clock time and break bit-equality. |

### 2.3 SHA256 hash comparison proving Nix reproducibility

Two consecutive `nix-build docker.nix` invocations, with the result symlink removed between them:

```
Build 1: sha256=4beae08503f91cc8233122ce2bf34801218de997e702930b1f8fcc243d7637b7  size=96825936
Build 2: sha256=4beae08503f91cc8233122ce2bf34801218de997e702930b1f8fcc243d7637b7  size=96825936
→ tarball bytes identical
```

For contrast, two Lab 2 Dockerfile builds (`docker build --no-cache`, same source, ~5 s apart):

```
v1: image_id=224e25de012f  saved_sha256=3ee19c287cc1753467ff59f1a8d6a813cf32af3cffe53084dd80e2a47d6d57ff
v2: image_id=8db6f4c85111  saved_sha256=06ff5686f7b3fda66e875a88f6069a6a066b5aacf4cd7d49218d4befeb9196ad
→ different image_id, different saved sha256: NOT reproducible
```

### 2.4 Image size comparison

```
$ docker images
lab2-app:v1                      164,415,349 bytes (~164 MB)
devops-info-service-nix:1.0.0    228,954,301 bytes (~229 MB)
```

Analysis: the Nix image is **larger** than the Dockerfile image, not smaller. The Dockerfile builds on `python:3.13-slim`, a Debian image where Python is provided by stripped-down system packages and many shared libraries are reused. `dockerTools.buildLayeredImage` carries the entire transitive closure as separate store paths — full CPython, fastapi, uvicorn, starlette, pydantic, anyio, libc, `cacert`, and so on — and does not share anything with a base image because there is none. The trade-off the lab brief implies (Nix smaller because no base) only holds when the base is itself heavy or the app needs few extras; for a Python web service with first-class deps, the Nix image can easily be larger. The reproducibility property is unaffected by this.

### 2.5 Side-by-side comparison — Lab 2 Dockerfile vs Nix `docker.nix`

| Aspect | Lab 2 Dockerfile | Lab 18 `docker.nix` |
| --- | --- | --- |
| `docker save | sha256sum` build 1 | `3ee19c28…` | `4beae085…` |
| `docker save | sha256sum` build 2 (no cache) | `06ff5686…` (different) | `4beae085…` (identical) |
| Image ID | changes on every build | stable across builds |
| `Created` timestamp | wall clock at build time | `1970-01-01T00:00:01Z` |
| Image size | 164 MB | 229 MB |
| Base image | `python:3.13-slim` (mutable tag) | none — pure Nix closure |
| Dependency installation | `pip install` at build time (network) | none — built outside, copied as store paths |
| Layer ordering | order of Dockerfile statements + timestamps | content-addressed |

### 2.6 `docker history` output for both approaches

Lab 2 image (`lab2-app:v1`) — every layer carries a wall-clock timestamp:

```
CREATED              SIZE      CREATED BY
About a minute ago   0B        CMD ["python" "app.py"]
About a minute ago   0B        EXPOSE map[8000/tcp:{}]
About a minute ago   0B        USER appuser
About a minute ago   66.2kB    RUN mkdir -p /data && chown -R …
About a minute ago   66.2kB    COPY . .
About a minute ago   46.6MB    RUN pip install --no-cache-dir …
About a minute ago   69B       COPY requirements.txt .
About a minute ago   0B        WORKDIR /app
About a minute ago   4.31kB    RUN groupadd -r -g 1000 appuser …
5 days ago           0B        CMD ["python3"]                  ← from base image
5 days ago           36B       RUN /bin/sh -c set -eux …        ← from base image
```

Nix image — every layer is content-addressed and carries no wall clock:

```
CREATED   SIZE      CREATED BY
N/A       1.84kB
N/A       11.4kB
N/A       215kB
N/A       1.65MB
N/A       5.6MB
N/A       5.69MB
N/A       972kB
N/A       1.76MB
N/A       819kB
N/A       713kB
N/A       1.27MB
N/A       934kB
N/A       228kB
N/A       125kB
... (42 layers total, all N/A)
```

The Lab 2 history exposes two distinct sources of non-determinism: (a) my layers, timestamped at build time, and (b) the base-image layers, timestamped whenever `python:3.13-slim` was last republished. The Nix history records neither — `Created` is the Unix epoch on every layer, and the layer ordering is determined by closure topology, not by Dockerfile statement order.

### 2.7 Both containers running simultaneously

CLI replacement for a screenshot (single shell session):

```
$ docker run -d --rm -p 5000:8000 --name lab2-c lab2-app:v1
$ docker run -d --rm -p 5001:8000 --name nix-c  devops-info-service-nix:1.0.0
$ sleep 3
$ curl -s http://localhost:5000/health
{"status":"healthy","timestamp":"2026-05-14T19:41:49.267653+00:00","uptime_seconds":2}
$ curl -s http://localhost:5001/health
{"status":"healthy","timestamp":"2026-05-14T19:41:49.277683+00:00","uptime_seconds":2}
```

Both containers serve the same FastAPI app on internal port 8000, exposed on hosts 5000 (Lab 2) and 5001 (Nix). Identical JSON shape, identical status code.

### 2.8 Analysis — why traditional Dockerfiles cannot be bit-for-bit reproducible

1. **Layer metadata embeds time.** Every `RUN`, `COPY`, `CMD` records the wall clock. Two `docker build` invocations seconds apart already differ in their layer metadata.
2. **Base image tags are mutable.** `python:3.13-slim` resolves to whatever the maintainers last pushed. A rebuild a month from now pulls a different base, even with the source unchanged.
3. **`pip install` is non-deterministic.** It hits the network at build time, re-resolves ranges, and can pick different wheels depending on what PyPI happens to be serving.
4. **Layer tarball metadata varies.** Inode ordering, file mtime, owner/group resolution, and `tar` version can all change the bytes of a layer that contains the same logical content.

Nix `dockerTools` sidesteps all four: layers are tarballs of pre-built `/nix/store/<hash>-...` paths whose contents are already proven byte-reproducible at the derivation level; layer ordering is fixed by the closure; `Created` is forced to the epoch; and there is no network call and no base image at build time.

### 2.9 Reflection — if I could redo Lab 2 with Nix

I would drop the Dockerfile entirely and let `default.nix` own the build, with `docker.nix` as a thin wrapper that emits the image. Three concrete changes follow:

1. **Promotion by content hash, not tag.** Instead of pushing `:1.0.0` and trusting the tag, promote by `sha256:4beae085…`. Rollback is then `docker pull <sha256>` and is guaranteed identical to the previous good build.
2. **Reproducible CI cache key.** The build cache keys on the derivation's input hash, not on Dockerfile text plus build context. "Why did this rebuild?" stops being a mystery.
3. **Tighter image audit.** `nix-store -q --tree result` lists every byte that goes into the image. There is no `apt-get` history to chase and no base image to wonder about.

### 2.10 Practical scenarios where Nix's reproducibility matters

- **CI / CD.** Two builds of the same commit produce the same artefact bytes. Flakiness whose only signal is differing image hashes goes away.
- **Security audits.** "What exactly is in this image?" is answered by the input hash plus the closure listing, not by `docker history` archaeology and base-image vendor advisories.
- **Rollback.** Atomic — point traffic at a previous store path or image hash and be certain it is bit-identical to the previous good build. No "we rebuilt and the bug came back" surprises.
- **Supply-chain.** Because there is no `pip install` at image build time, a compromised PyPI mirror or a rotated wheel cannot influence what ships.
- **Compliance / SBOM.** The closure *is* the bill of materials. There is nothing else in the image to declare.

---

## Acceptance checklist

- [x] `lab18` branch (based on `lab17`) carries the Task 1 / Task 2 work
- [x] `LAB18_REPORT.md` answers every required prompt in the lab brief
- [x] `app_python/` contains the app plus the new `default.nix` and `docker.nix`
- [x] `nix-build --check` rebuilt the Task 1 derivation in a clean sandbox; same NAR hash
- [x] `nix-build docker.nix` twice → byte-identical tarball
- [x] Lab 2 Dockerfile reproduced twice (no-cache) → different `docker save` hashes, confirming non-reproducibility
- [x] Both containers run side-by-side, `/health` returns 200 from each
- [ ] Bonus (Flakes) — intentionally skipped per scope
