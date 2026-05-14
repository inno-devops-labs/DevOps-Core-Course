# lab 18: reproducible builds with nix

## 1. nix installation

### installation method

used the determinate systems installer (enables flakes by default):

```bash
curl --proto '=https' --tlsv1.2 -sSf -L https://install.determinate.systems/nix | sh -s -- install
```

### verification

```
$ nix --version
nix (Nix) 2.24.12

$ nix run nixpkgs#hello
Hello, world!
```

[screenshot: nix version and hello world](lab18/app_python/screenshots/nix-install.png)

---

## 2. task 1 — build reproducible python app

### 2.1 default.nix derivation

```nix
{ pkgs ? import <nixpkgs> {} }:

pkgs.python312Packages.buildPythonApplication {
  pname = "devops-info-service";
  version = "1.0.0";
  src = ./.;

  format = "other";

  propagatedBuildInputs = with pkgs.python312Packages; [
    fastapi
    uvicorn
    pydantic
    python-json-logger
    prometheus-client
  ];

  nativeBuildInputs = [ pkgs.makeWrapper ];

  installPhase = ''
    mkdir -p $out/lib $out/bin
    cp app.py $out/lib/app.py
    cp metrics.py $out/lib/metrics.py

    makeWrapper ${pkgs.python312}/bin/python3 $out/bin/devops-info-service \
      --prefix PYTHONPATH : "$out/lib:$PYTHONPATH" \
      --add-flags "-m" \
      --add-flags "uvicorn" \
      --add-flags "app:app" \
      --add-flags "--host" \
      --add-flags "0.0.0.0" \
      --add-flags "--port" \
      --add-flags "5000"
  '';
}
```

### field explanations

| field | purpose |
|-------|---------|
| `pname` | package name, used in store path |
| `version` | package version, used in store path |
| `src` | source directory (`./.` = current directory) |
| `format = "other"` | no setup.py/pyproject.toml — we handle install manually |
| `propagatedBuildInputs` | runtime python dependencies (fastapi, uvicorn, etc.) |
| `nativeBuildInputs` | build-time tools (`makeWrapper` wraps binary with interpreter) |
| `installPhase` | copies source files to `$out/lib`, creates wrapper script using nix python3.12 |
| `makeWrapper` | creates a wrapper that calls `${pkgs.python312}/bin/python3 -m uvicorn app:app` with correct PYTHONPATH |

### why makeWrapper instead of wrapProgram

`wrapProgram` patches an existing executable, but our `app.py` is a python source file — it cannot be executed directly as a shell script. instead, `makeWrapper` creates a new wrapper script that invokes the nix-provided python3.12 interpreter with the correct arguments, avoiding the system python version mismatch.

### 2.2 building the application

```bash
cd labs/lab18/app_python
nix-build -I nixpkgs=https://github.com/NixOS/nixpkgs/archive/nixos-24.11.tar.gz
```

output:

```
/nix/store/1kyvpdr7q5cn9yviqrp74wz5r40y8hax-devops-info-service-1.0.0
```

```bash
$ readlink result
/nix/store/1kyvpdr7q5cn9yviqrp74wz5r40y8hax-devops-info-service-1.0.0
```

[screenshot: nix-build output](lab18/app_python/screenshots/nix-build.png)

### 2.3 running the nix-built app

```bash
./result/bin/devops-info-service
```

```
INFO:     Started server process [37240]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:5000 (Press CTRL+C to quit)
```

[screenshot: app running from nix-built binary in browser](lab18/app_python/screenshots/nix-app-running.png)

### 2.4 proving reproducibility

#### test 1: rebuild and compare store paths

```bash
# build 1
$ nix-build -I nixpkgs=https://github.com/NixOS/nixpkgs/archive/nixos-24.11.tar.gz
$ readlink result
/nix/store/1kyvpdr7q5cn9yviqrp74wz5r40y8hax-devops-info-service-1.0.0

# delete from store and rebuild from scratch
$ rm result
$ nix-store --delete /nix/store/1kyvpdr7q5cn9yviqrp74wz5r40y8hax-devops-info-service-1.0.0
deleting '/nix/store/1kyvpdr7q5cn9yviqrp74wz5r40y8hax-devops-info-service-1.0.0'
1 store paths deleted, 24.5 KiB freed

# build 2 (full rebuild, not cached)
$ nix-build -I nixpkgs=https://github.com/NixOS/nixpkgs/archive/nixos-24.11.tar.gz
$ readlink result
/nix/store/1kyvpdr7q5cn9yviqrp74wz5r40y8hax-devops-info-service-1.0.0
```

**result**: identical store path `1kyvpdr7q5cn9yviqrp74wz5r40y8hax` after full rebuild from scratch.

[screenshot: reproducibility proof — identical store paths](lab18/app_python/screenshots/nix-reproducibility.png)

#### test 2: pip vs nix comparison

**pip's limitation** — unpinned dependencies:

```bash
echo "flask" > requirements-unpinned.txt
python -m venv venv1 && source venv1/bin/activate
pip install -r requirements-unpinned.txt
pip freeze | grep -i flask > freeze1.txt
deactivate

python -m venv venv2 && source venv2/bin/activate
pip install -r requirements-unpinned.txt
pip freeze | grep -i flask > freeze2.txt
deactivate

diff freeze1.txt freeze2.txt
# likely identical NOW, but could differ weeks from now
```

even with pinned `requirements.txt`, only direct dependencies are pinned. transitive dependencies (werkzeug, click, etc. under flask) can drift.

**nix's guarantee**: every dependency in the entire tree is pinned by its content hash.

### 2.5 nix store path format

```
/nix/store/1kyvpdr7q5cn9yviqrp74wz5r40y8hax-devops-info-service-1.0.0
         ────────────────────────────────────── ────────────────────────
         content hash (sha256)                   name-version
```

- `1kyvpdr7q5cn9yviqrp74wz5r40y8hax` — hash computed from: all source code, all dependencies (transitively), build instructions, compiler flags
- same inputs → same hash → reuse existing build (cache hit)
- different inputs → different hash → new build required

### 2.6 why requirements.txt provides weaker guarantees than nix

1. **only pins direct dependencies**: `requirements.txt` pins what YOU install, not what those packages install (transitive deps)
2. **no python version pinning**: different python versions can produce different behavior
3. **no build isolation**: pip uses system libraries, network, and local cache
4. **no content verification**: pip trusts PyPI to serve the same package for the same version string
5. **time-dependent**: same `pip install -r requirements.txt` can produce different environments months apart

nix solves all of these: every transitive dependency is locked by content hash, python version is pinned, builds are sandboxed, and the same derivation always produces the same output.

### 2.7 lab 1 vs lab 18 comparison

| aspect | lab 1 (pip + venv) | lab 18 (nix) |
|--------|-------------------|--------------|
| python version | system-dependent (3.14 on this machine) | pinned in derivation (3.12) |
| dependency resolution | runtime (`pip install`) | build-time (pure) |
| reproducibility | approximate (with lockfiles) | bit-for-bit identical |
| portability | requires same OS + python | works anywhere nix runs |
| binary cache | no | yes (cache.nixos.org) |
| isolation | virtual environment | sandboxed build |
| store path | N/A | content-addressable hash |

### 2.8 reflection

if nix had been used from the start in lab 1:
- no `python -m venv` and `pip install` dance — `nix-build` produces a ready-to-run binary
- no "works on my machine" — same derivation produces identical output on any machine
- no dependency drift — transitive dependencies are locked by content hash
- no python version confusion — nix pins the exact interpreter
- the `pydantic_core._pydantic_core` import error we hit would never happen — nix guarantees the python version matches the compiled C extensions

---

## 3. task 2 — reproducible docker images

### 3.1 docker.nix

```nix
{ pkgs ? import <nixpkgs> {} }:

let
  app = import ./default.nix { inherit pkgs; };
in
pkgs.dockerTools.buildImage {
  name = "devops-info-service-nix";
  tag = "1.0.0";

  copyToRoot = [ app pkgs.coreutils ];

  config = {
    Cmd = [ "${app}/bin/devops-info-service" ];
    ExposedPorts = {
      "5000/tcp" = {};
    };
  };

  created = "1970-01-01T00:00:01Z";
}
```

### field explanations

| field | purpose |
|-------|---------|
| `buildImage` | creates a docker image tarball |
| `name` | image name |
| `tag` | image tag |
| `copyToRoot` | packages to include in the image (our app + coreutils for debugging) |
| `config.Cmd` | default command to run when container starts |
| `config.ExposedPorts` | ports to expose |
| `created = "1970-01-01T00:00:01Z"` | reproducible timestamp (epoch +1s) — never use `"now"` |

### 3.2 building and loading

```bash
nix-build docker.nix -I nixpkgs=https://github.com/NixOS/nixpkgs/archive/nixos-24.11.tar.gz
docker load < result
```

[screenshot: nix-build docker.nix and docker load output](lab18/app_python/screenshots/nix-docker-build.png)

### 3.3 nix docker image on macos

**problem**: on macOS ARM, the nix-built docker image produces "exec format error" because nix packages macOS (darwin) binaries, but docker containers run linux.

**workaround**: the nix docker image was built successfully and loaded into docker, demonstrating the concept. for a working container on macOS, cross-compilation to `aarch64-linux` is needed, which requires nixpkgs `allowUnsupportedSystem = true` or using a linux builder.

the traditional lab 2 dockerfile works because it uses `FROM python:3.13-slim` which is a pre-built linux image.

### 3.4 lab 2 traditional dockerfile — running and testing

```bash
docker build -t lab2-app:v1 /path/to/app_python/
docker run -d -p 5000:5000 --name lab2-container lab2-app:v1
curl http://localhost:5000/health
```

[screenshot: lab2 container running and health check response](lab18/app_python/screenshots/docker-lab2-running.png)

### 3.5 reproducibility proof — nix derivation

the nix derivation itself (not the docker image) proves reproducibility. we already demonstrated this in task 1:

```
Build 1: /nix/store/1kyvpdr7q5cn9yviqrp74wz5r40y8hax-devops-info-service-1.0.0
Build 2: /nix/store/1kyvpdr7q5cn9yviqrp74wz5r40y8hax-devops-info-service-1.0.0
```

identical hash after full rebuild from scratch. the docker image built from this derivation inherits the same guarantee — if the derivation is reproducible, the image is reproducible.

### 3.6 traditional dockerfile — reproducibility failure

```bash
docker build -t lab2-app:test1 /path/to/app_python/
docker save lab2-app:test1 | shasum -a 256

sleep 2

docker build -t lab2-app:test2 /path/to/app_python/
docker save lab2-app:test2 | shasum -a 256
# different hashes! (timestamps differ)
```

[screenshot: traditional dockerfile sha256 comparison showing different hashes](lab18/app_python/screenshots/dockerfile-sha256.png)

### 3.7 docker history — timestamp comparison

```bash
docker history lab2-app:v1
# shows varying CREATED timestamps
```

[screenshot: docker history for lab2-app showing real timestamps](lab18/app_python/screenshots/docker-history-lab2.png)

nix docker images use `created = "1970-01-01T00:00:01Z"` — deterministic epoch timestamps instead of real build times. this ensures identical layer hashes across rebuilds.

### 3.8 comparison table

| metric | lab 2 dockerfile | lab 18 nix dockertools |
|--------|------------------|------------------------|
| reproducibility | ❌ different hashes each build | ✅ identical hashes |
| build caching | layer-based (timestamp-dependent) | content-addressable |
| base image dependency | yes (`python:3.13-slim`) | no base image needed |
| timestamps | real build time (varies) | deterministic (epoch) |
| dependency pinning | pip (approximate) | nix store (exact) |

### 3.9 why traditional dockerfiles can't achieve bit-for-bit reproducibility

1. **timestamps**: docker embeds creation timestamps in every layer
2. **base image drift**: `python:3.13-slim` can point to different content over time
3. **non-deterministic installs**: `pip install` resolves dependencies at build time, which can change
4. **file ordering**: `COPY . .` depends on filesystem ordering, which varies
5. **metadata**: docker stores build metadata (build context, labels) that differs between builds

### 3.10 reflection

if i could redo lab 2 with nix:
- use `dockerTools.buildLayeredImage` instead of a traditional Dockerfile
- set `created = "1970-01-01T00:00:01Z"` for reproducible timestamps
- no base image — only the minimal closure of dependencies
- smaller image size (no full `python:3.13-slim` base)
- guaranteed identical image on every build

practical scenarios where nix reproducibility matters:
- **CI/CD**: cache docker images by content hash, not tag — no false cache misses
- **security audits**: verify the exact dependency tree of a deployed image
- **rollbacks**: redeploy an older version and get the exact same binary, not a rebuilt approximation

---

## 4. bonus — nix flakes

### 4.1 flake.nix

```nix
{
  description = "DevOps Info Service - Reproducible Build";

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
        buildInputs = with pkgs; [
          python312
          python312Packages.fastapi
          python312Packages.uvicorn
          python312Packages.pydantic
          python312Packages.prometheus-client
        ];
      };
    };
}
```

### 4.2 generating lock file

```bash
nix flake update
```

creates `flake.lock` with pinned nixpkgs revision:

```json
{
  "nodes": {
    "nixpkgs": {
      "locked": {
        "lastModified": ...,
        "narHash": "sha256-...",
        "rev": "...",
        "type": "github"
      }
    }
  }
}
```

### 4.3 building with flake

```bash
nix build                    # builds default package
nix build .#dockerImage     # builds docker image
./result/bin/devops-info-service
```

[screenshot: nix build output from flake](lab18/app_python/screenshots/nix-flake-build.png)

### 4.4 development shell

```bash
nix develop
# drops into shell with exact python version and dependencies
python --version
python -c "import fastapi; print(fastapi.__version__)"
```

[screenshot: nix develop shell output](lab18/app_python/screenshots/nix-develop.png)

**compared to lab 1 venv:**

| aspect | lab 1 (venv) | lab 18 (nix develop) |
|--------|-------------|---------------------|
| setup | `python -m venv && pip install` | `nix develop` |
| python version | system-dependent | pinned in flake |
| reproducibility | approximate | exact |
| sharing | share requirements.txt | share flake.lock |

### 4.5 flakes vs helm values (lab 10 comparison)

**lab 10 helm approach:**

```yaml
image:
  repository: devops-info-service
  tag: "1.0.0"
```

- only pins container image tag
- doesn't lock python dependencies inside the image
- image tag `1.0.0` could point to different content if rebuilt

**nix flakes approach:**

`flake.lock` locks everything:
- ✅ exact nixpkgs revision (all 80,000+ packages)
- ✅ python version and all dependencies
- ✅ build tools and compilers
- ✅ everything in the closure

| aspect | lab 1 (venv) | lab 10 (helm values) | lab 18 (nix flakes) |
|--------|-------------|---------------------|---------------------|
| locks python version | ❌ | ❌ | ✅ |
| locks dependencies | ⚠️ approximate | ❌ only image tag | ✅ exact hashes |
| locks build tools | ❌ | ❌ | ✅ |
| reproducibility | ⚠️ probabilistic | ⚠️ tag-based | ✅ cryptographic |
| cross-machine | ❌ varies | ⚠️ depends on image | ✅ identical |
| dev environment | ✅ (venv) | ❌ | ✅ (nix develop) |
| time-stable | ❌ packages update | ⚠️ tags can change | ✅ locked forever |

### 4.6 combined approach

you can use both together:
1. build reproducible image with nix: `nix build .#dockerImage`
2. load to docker and tag: `docker load < result`
3. reference in helm with content hash: `image.tag: "sha256-abc123..."`

this gives you helm's declarative kubernetes deployment + nix's perfect reproducibility for the image.

### 4.7 reflection

flakes improve upon traditional dependency management by:
- locking the **entire** dependency tree, not just direct dependencies
- providing cryptographic proof that builds are identical
- enabling `nix develop` for instant, reproducible dev environments
- making builds shareable via git — anyone can reproduce your exact setup

practical scenario where `flake.lock` prevented a "works on my machine" problem:
- a teammate's build fails because `pip install fastapi` resolves to a newer minor version with breaking changes. with flakes, the exact nixpkgs revision is locked, so everyone gets the same fastapi version, guaranteed.

---

## 5. challenges

### flakehub connectivity from russia

**problem**: the determinate nix installer defaults to using flakehub for nixpkgs, which returns HTTP 301 errors from russian networks.

**error**: `unable to download 'https://flakehub.com/f/DeterminateSystems/nixpkgs-weekly/%2A.tar.gz': HTTP error 301`

**solution**: override the nixpkgs source with the `-I` flag:
```bash
nix-build -I nixpkgs=https://github.com/NixOS/nixpkgs/archive/nixos-24.11.tar.gz
```

and pin the registry:
```bash
nix registry add nixpkgs github:NixOS/nixpkgs/nixos-24.11
```

### python 3.13 package compatibility

**problem**: `python313Packages` fails with `mypy-1.11.2 not supported for interpreter python3.13` on nixos-24.11.

**solution**: use `python312Packages` instead — python 3.12 has full package support in the stable nixpkgs channel.

### python interpreter mismatch

**problem**: running `./result/bin/devops-info-service` executes with the system python (3.14 from homebrew) instead of nix python 3.12, causing `ModuleNotFoundError: No module named 'pydantic_core._pydantic_core'`.

**cause**: `wrapProgram` wraps the script but it still uses the system `python3` from PATH. the C extension was compiled for python 3.12 but the system interpreter is 3.14.

**solution**: use `makeWrapper` to create a wrapper that explicitly calls `${pkgs.python312}/bin/python3 -m uvicorn app:app` instead of `wrapProgram` on a python source file.

### missing execute permission

**problem**: `Cannot wrap '/nix/store/.../bin/devops-info-service' because it is not an executable file`.

**cause**: `app.py` copied without execute permission, and python source files aren't executable shell scripts.

**solution**: switched from copying `app.py` as the executable to using `makeWrapper` with the python interpreter directly.

### docker image cross-compilation on macos

**problem**: nix-built docker image produces "exec format error" when run in docker on macOS ARM.

**error**: `exec /nix/store/.../bin/devops-info-service: exec format error`

**cause**: nix on macOS builds `aarch64-darwin` (macOS ARM) binaries, but docker containers require `aarch64-linux` binaries. the nix store packages darwin executables which linux cannot run.

**attempted fix 1**: `pkgs.pkgsCross.aarch64-multiplatform` — fails because `glibc` is not available on `aarch64-apple-darwin` hostPlatform without `allowUnsupportedSystem = true`.

**attempted Fix 2**: `buildLayeredImage` — fails because `fakeroot` on macOS Sequoia has a broken symbol (`_fstat$INODE64`).

**workaround**: used `buildImage` (not `buildLayeredImage`) to avoid fakeroot. the docker image was built and loaded successfully, demonstrating the reproducible image concept. for a runnable container on macOS, the recommended approach is to use a remote linux builder or CI (e.g., github actions) to build the linux image.

**note**: on linux machines (or with a linux builder), `dockerTools.buildLayeredImage` with `pkgsCross` would produce a fully working reproducible container. this is a macOS-specific limitation, not a nix limitation.

---

## 6. key decisions

| question | answer |
|----------|--------|
| why `format = "other"`? | the app has no setup.py/pyproject.toml, so we handle install manually |
| why `makeWrapper` instead of `wrapProgram`? | python source files can't be executed directly; makeWrapper creates a proper wrapper that invokes the nix python interpreter |
| why `created = "1970-01-01T00:00:01Z"`? | reproducible timestamp — using `"now"` would produce different images on each build |
| why include `coreutils` in docker image? | provides basic utilities (`ls`, `cat`, etc.) for debugging inside the container |
| why `nixos-24.11` for flake input? | stable channel with well-tested packages; `nixos-unstable` could have breaking changes |
| why `-I nixpkgs=...` flag? | flakehub (determinate nix default) is blocked in russia; this forces github nixpkgs instead |
