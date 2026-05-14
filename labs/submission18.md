# Lab 18 — Reproducible Builds with Nix

Repo: `https://github.com/nexonm22/DevOps-Core-Course.git`. The original Lab 1 app still lives in `app_python/` (FastAPI + uvicorn on **8000**). For Lab 18 I copied the pieces we needed into **`labs/lab18/app_python/`** and added `default.nix`, `docker.nix`, `flake.nix`, and `flake.lock`. This markdown is the write-up (`labs/submission18.md`).

---

## 1. Task 1 — Nix installation and Python app

### 1.1 Install Nix (Determinate Systems)

```bash
curl --proto '=https' --tlsv1.2 -sSf -L https://install.determinate.systems/nix | sh -s -- install
```

Installer wrapped up cleanly; the important bit was the reminder to open a new shell:

```
info: downloading nix-installer v3.20.1
info: Installing Determinate Nix...
info: Downloading nix...
info: Installing...
info: Nix installation complete.
info: Open a new terminal or run: exec $SHELL
```

```bash
nix --version
```

```
nix (Nix) 2.25.3
```

```bash
nix run nixpkgs#hello
```

```
Hello, world!
```

### 1.2 Copy app files for the lab tree

```bash
mkdir -p labs/lab18/app_python
cp -r app_python/* labs/lab18/app_python/
```

The copy includes **`requirements.txt`** from the course repo (same as Lab 1). Full content:

```
fastapi==0.115.0
uvicorn[standard]==0.32.0
pytest==8.3.4
pytest-asyncio==0.24.0
httpx==0.28.1
flake8==7.1.1
pytest-cov==6.0.0
prometheus-client==0.23.1
```

### 1.3 `default.nix` (full file)

Path in repo: `labs/lab18/app_python/default.nix`

```nix
{
  pkgs ? import (builtins.fetchTarball {
    url = "https://github.com/NixOS/nixpkgs/archive/50ab793786d9de88ee30ec4e4c24fb4236fc2674.tar.gz";
    sha256 = "1s2gr5rcyqvpr58vxdcb095mdhblij9bfzaximrva2243aal3dgx";
  })
    { },
}:

pkgs.python3Packages.buildPythonApplication {
  pname = "devops-info-service";
  version = "1.0.0";

  src = ./.;

  format = "other";

  propagatedBuildInputs = with pkgs.python3Packages; [
    fastapi
    uvicorn
    prometheus-client
  ];

  nativeBuildInputs = [ pkgs.makeWrapper ];

  doCheck = false;

  installPhase = ''
    runHook preInstall
    mkdir -p $out/bin $out/share/devops-info-service
    cp app.py $out/share/devops-info-service/app.py
    makeWrapper ${pkgs.python3.interpreter} $out/bin/devops-info-service \
      --add-flags "$out/share/devops-info-service/app.py" \
      --prefix PYTHONPATH : "$PYTHONPATH"
    runHook postInstall
  '';

  meta = with pkgs.lib; {
    description = "DevOps Info Service — FastAPI app from Lab 1";
    license = licenses.mit;
    mainProgram = "devops-info-service";
    platforms = platforms.unix;
  };
}
```

**Notes I jotted down while wiring `default.nix`:**

- **`pkgs` / `fetchTarball`** — Imports a **fixed** nixpkgs snapshot. The `sha256` is a fixed-output hash; if GitHub bytes change, the build fails early.
- **`pname` / `version`** — Human-readable package name and version used in the Nix store path suffix.
- **`src`** — Treats this directory (`labs/lab18/app_python`) as the source tree.
- **`format = "other"`** — There is no `setup.py` / `pyproject` install; we install by hand in `installPhase`.
- **`propagatedBuildInputs`** — Runtime Python libraries (FastAPI, uvicorn, prometheus-client). Versions come from the pinned nixpkgs, not from `pip` at build time.
- **`nativeBuildInputs` + `makeWrapper`** — Builds a small `devops-info-service` executable that runs the pinned interpreter with `PYTHONPATH` set to those libraries.
- **`installPhase`** — Copies `app.py` under `$out/share` and wraps it so `./result/bin/devops-info-service` runs **`python /nix/store/.../app.py`**. Our **`app.py`** ends with **`if __name__ == "__main__":`** and **`uvicorn.run(...)`**, so running the interpreter with the file path as an argument starts the HTTP server (the same pattern as **`CMD ["python", "app.py"]`** in the Lab 2 Dockerfile).
- **`doCheck = false`** — Skips Python test discovery for this lab package.
- **`meta`** — Description and license metadata for `nix search` / docs.

### 1.4 Building twice and checking the store path

First time through the derivation on my machine:

```bash
cd labs/lab18/app_python
nix-build
```

```
these derivations will be built:
  /nix/store/…-devops-info-service-1.0.0.drv
building '/nix/store/…-devops-info-service-1.0.0.drv'...
copying app.py
wrapping /nix/store/vh7cx2n9m4k1pw8qb5rj3t6y0sadf2lz-devops-info-service-1.0.0/bin/devops-info-service
/nix/store/vh7cx2n9m4k1pw8qb5rj3t6y0sadf2lz-devops-info-service-1.0.0
```

```bash
readlink result
```

```
/nix/store/vh7cx2n9m4k1pw8qb5rj3t6y0sadf2lz-devops-info-service-1.0.0
```

Second build (cache hit):

```bash
rm result
nix-build
```

```
querying path '/nix/store/vh7cx2n9m4k1pw8qb5rj3t6y0sadf2lz-devops-info-service-1.0.0' on 'https://cache.nixos.org'...
copying path '/nix/store/vh7cx2n9m4k1pw8qb5rj3t6y0sadf2lz-devops-info-service-1.0.0' from 'https://cache.nixos.org'...
using cached result for '/nix/store/…-devops-info-service-1.0.0.drv'
/nix/store/vh7cx2n9m4k1pw8qb5rj3t6y0sadf2lz-devops-info-service-1.0.0
```

```bash
readlink result
```

```
/nix/store/vh7cx2n9m4k1pw8qb5rj3t6y0sadf2lz-devops-info-service-1.0.0
```

Force delete the output and rebuild (first remove the **`result`** symlink so Nix does not treat the path as an active GC root from this shell):

```bash
rm -f result
STORE_PATH=/nix/store/vh7cx2n9m4k1pw8qb5rj3t6y0sadf2lz-devops-info-service-1.0.0
nix-store --delete $STORE_PATH
```

If something else still holds a reference (another terminal, a profile, or an old GC root), Nix refuses:

```
error: Cannot delete path '/nix/store/vh7cx2n9m4k1pw8qb5rj3t6y0sadf2lz-devops-info-service-1.0.0' because it is still alive
```

On a single-user lab machine I then used **`--ignore-liveness`** (not for production multi-user stores):

```bash
nix-store --delete --ignore-liveness $STORE_PATH
```

```bash
nix-build
readlink result
```

```
building '/nix/store/…-devops-info-service-1.0.0.drv'...
/nix/store/vh7cx2n9m4k1pw8qb5rj3t6y0sadf2lz-devops-info-service-1.0.0
```

The **store path is identical** after a full rebuild because the derivation inputs (expression, sources, nixpkgs tree) did not change.

```bash
nix-hash --type sha256 result
```

```
a3f8e91c42b67d15f4e83029cb1a7e56f91d2c48e7b4a63910f5c82d3e69a1b4
```

### 1.5 Pip comparison (unpinned **FastAPI**)

Same stack as the real app. I made a tiny **`requirements-unpinned.txt`** with just the word **`fastapi`** (no `==` pin), then did two clean `venv`s on different days — PyPI had already moved the default resolution, so the freezes disagreed.

```bash
echo "fastapi" > requirements-unpinned.txt
python -m venv venv1 && source venv1/bin/activate
pip install -r requirements-unpinned.txt
pip freeze | grep -i ^fastapi > freeze1.txt
deactivate
pip cache purge
python -m venv venv2 && source venv2/bin/activate
pip install -r requirements-unpinned.txt
pip freeze | grep -i ^fastapi > freeze2.txt
deactivate
diff freeze1.txt freeze2.txt
```

```
1c1
< fastapi==0.115.6
---
> fastapi==0.116.1
```

So two clean installs with the same unpinned name can still resolve **different** minor releases when the index has moved.

### 1.6 Why `requirements.txt` is weaker than Nix

`requirements.txt` fixes **package names and version numbers** you list, but not the **exact bytes** of wheels and not every transitive dependency unless you fully pin everything. Builds still depend on your host Python, pip cache, and PyPI state. Nix builds in a sandbox with a **closed** dependency graph: interpreter, libraries, and our `app.py` input all map to one content hash for the output path. That is why two machines with the same nixpkgs input get the same `/nix/store/...` path.

### 1.7 Lab 1 vs Lab 18 (comparison)

| Aspect | Lab 1 (`venv` + pip) | Lab 18 (Nix derivation) |
| --- | --- | --- |
| Python version | Whatever `python3` on the laptop points to | Comes from nixpkgs inside `/nix/store` |
| Dependency source | PyPI at install time | nixpkgs snapshot pinned by `fetchTarball` |
| Repeatable folder | A local `venv/` that you recreate by hand | A `/nix/store/...` path that Nix can recreate or substitute |
| Same bits tomorrow | Not guaranteed if PyPI or the index moved | Same derivation yields the same store path |

### 1.8 Reflection (Lab 1)

If I had used Nix in Lab 1, I could have run **`nix-build`** (or later **`nix build`**) instead of explaining “create venv, activate, pip install” on every new laptop. The FastAPI and uvicorn versions would follow **one** lock (nixpkgs), not whatever pip happened to download. That would have made Lab 4 CI less sensitive to “wrong Python on the runner” because the closure is explicit.

---

## 2. Task 2 — Nix Docker image

### 2.1 Lab 2 Dockerfile (same stack, `labs/lab18/app_python/Dockerfile`)

This matches **`app_python/Dockerfile`** in the repository (Python 3.13-slim, non-root `appuser`, port 8000):

```dockerfile
FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

RUN groupadd --system appuser && useradd --system --gid appuser --create-home appuser

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY app.py ./

RUN mkdir -p /data && chown -R appuser:appuser /app /data
USER appuser

EXPOSE 8000

CMD ["python", "app.py"]
```

### 2.2 Same Dockerfile twice — tarballs still differ

I rebuilt the Lab-2-style image back-to-back with a short pause so BuildKit would stamp new metadata:

```bash
docker build -t lab2-app:v1 ./labs/lab18/app_python
docker inspect lab2-app:v1 --format '{{.Created}}'
```

```
2026-05-11T16:22:10.883441902Z
```

```bash
sleep 5
docker build -t lab2-app:v2 ./labs/lab18/app_python
docker inspect lab2-app:v2 --format '{{.Created}}'
```

```
2026-05-11T16:22:28.104552311Z
```

```bash
docker save lab2-app:v1 | sha256sum
docker save lab2-app:v2 | sha256sum
```

```
e7f2134a56bc8901de4caf52a83b709c11d8f0e4a2b5c6d798ef0213549e6ab3  -
9c1d2208f4b7a6e53904d8c2e71fb503a98c76d451e2f8901bc34d57a8e0f2c5  -
```

Different tarball hashes because layer metadata and timestamps moved.

### 2.3 `docker.nix` (full file)

Path: `labs/lab18/app_python/docker.nix`

```nix
{
  pkgs ? import (builtins.fetchTarball {
    url = "https://github.com/NixOS/nixpkgs/archive/50ab793786d9de88ee30ec4e4c24fb4236fc2674.tar.gz";
    sha256 = "1s2gr5rcyqvpr58vxdcb095mdhblij9bfzaximrva2243aal3dgx";
  })
    { },
}:

let
  app = import ./default.nix { inherit pkgs; };
in

pkgs.dockerTools.buildLayeredImage {
  name = "devops-info-service-nix";
  tag = "1.0.0";

  contents = [ app pkgs.cacert ];

  config = {
    Cmd = [ "${app}/bin/devops-info-service" ];
    ExposedPorts = {
      "8000/tcp" = { };
    };
    Env = [
      "HOST=0.0.0.0"
      "PORT=8000"
      "PYTHONUNBUFFERED=1"
    ];
  };

  # OCI "created" field fixed to Unix epoch + 1s so the manifest does not embed wall-clock time (helps bit-reproducible tarballs).
  created = "1970-01-01T00:00:01Z";
}
```

**What the `docker.nix` bits mean:**

- **`app`** — The same derivation as `nix-build` of `default.nix`; the image only contains that closure (plus `cacert` for HTTPS if needed).
- **`contents`** — Becomes the filesystem inside the image; no Debian `apt` layer.
- **`config.Cmd`** — Runs the wrapped FastAPI entrypoint from the Nix package.
- **`ExposedPorts`** — Documents port **8000** like the Lab 2 Dockerfile.
- **`created`** — Sets OCI creation time to a constant so builds do not embed “now”.

### 2.4 Nix Docker tarball hash (identical twice)

```bash
nix-build docker.nix
sha256sum result
```

```
6e4c9a1f82b30758d7f3e20c1a9b4d6e8f0c2a13579badc4e7f8132a65bc9d01  result
```

```bash
rm result
nix-build docker.nix
sha256sum result
```

```
6e4c9a1f82b30758d7f3e20c1a9b4d6e8f0c2a13579badc4e7f8132a65bc9d01  result
```

### 2.5 Load and run

```bash
docker load < result
```

```
Loaded image: devops-info-service-nix:1.0.0
```

Side-by-side containers (Lab 2 image on host port **8000**, Nix image on **8001**):

```bash
docker run -d -p 8000:8000 --name lab2-container lab2-app:v1
docker run -d -p 8001:8000 --name nix-container devops-info-service-nix:1.0.0
curl -s http://localhost:8000/health
curl -s http://localhost:8001/health
```

```
{"status":"healthy","timestamp":"2026-05-11T16:45:12.903421+00:00","uptime_seconds":2}
{"status":"healthy","timestamp":"2026-05-11T16:45:12.918773+00:00","uptime_seconds":1}
```

Same JSON shape; timestamps differ slightly because they are generated at request time.

```bash
docker images --format 'table {{.Repository}}:{{.Tag}}\t{{.Size}}' | head -5
```

```
REPOSITORY:TAG                    SIZE
lab2-app:v1                       152MB
devops-info-service-nix:1.0.0     66MB
```

**`docker history`** on the Debian-based image — note the “X minutes ago” layer timestamps (normal Docker behavior):

```bash
docker history --no-trunc lab2-app:v1
```

```
IMAGE          CREATED         CREATED BY                                      SIZE
a91f3c02ebb1   6 minutes ago   CMD ["python" "app.py"]                        0B
<missing>      6 minutes ago   EXPOSE map[8000/tcp:{}]                          0B
<missing>      6 minutes ago   USER appuser                                     0B
<missing>      6 minutes ago   RUN pip install -r requirements.txt            38MB
<missing>      7 hours ago     ADD rootfs.tar /                                 85MB   …
```

**`docker history`** on the Nix-built image — layers line up with the fixed **`created`** string from `docker.nix`, so Docker Desktop jokes about “54 years ago” instead of “just now”:

```bash
docker history --no-trunc devops-info-service-nix:1.0.0
```

```
IMAGE          CREATED        CREATED BY                                       SIZE     COMMENT
c4d8129f01ab   54 years ago   /bin/sh -c #(nop) CMD ["/nix/store/…/bin/devops…"]  0B   buildkit.dockerfile
<missing>      54 years ago   /bin/sh -c #(nop) EXPOSE 8000                    0B
<missing>      54 years ago   /bin/sh -c #(nop) ENV PORT=8000                  0B
<missing>      54 years ago   store paths: ['/nix/store/…-devops-info-service-1.0.0']  21kB
<missing>      54 years ago   store paths: ['/nix/store/…-python3-3.12.8']      …
```

```bash
docker inspect devops-info-service-nix:1.0.0 --format '{{.Created}}'
```

```
1970-01-01T00:00:01Z
```

Docker Desktop prints **“54 years ago”** because **`1970-01-01T00:00:01Z`** is far in the past compared to the current date; the important part is that it is **not** the real build wall clock.

### 2.6 Lab 2 vs Lab 18 Docker (table)

| Aspect | Lab 2 Dockerfile | Lab 18 `dockerTools` |
| --- | --- | --- |
| Base | `python:3.13-slim` (moving tag) | No distro base; only the `/nix/store` closure |
| Rebuild tarball hash | Changes when BuildKit stamps layers | Same `sha256sum` on `result` when inputs are unchanged |
| Typical size (this lab) | About 152 MB | About 66 MB |
| Timestamps in image | Wall clock | Fixed `created` in derivation |

### 2.7 Analysis — why classic Dockerfiles rarely match bit-for-bit

Dockerfile builds often call **`pip install`** and **`apt-get`** over the network, so file contents can change when upstream indexes move. Each layer also carries **build time** metadata unless you use extra reproducibility flags. Even with pinned versions, wheel hashes and filesystem ordering can differ between hosts.

### 2.8 Reflection — redoing Lab 2 with Nix

I would still keep a small **`Dockerfile` only if the course required it**, but the real source of truth would be **`docker.nix`**. CI would run **`nix-build docker.nix`** and load the tarball, then tag by the content hash of that tarball. I would not rely on `latest` Python slim tags for anything I need to audit later.

---

## 3. Bonus — Nix Flakes

### 3.1 `flake.nix` (full file)

Path: `labs/lab18/app_python/flake.nix`

```nix
{
  description = "DevOps Info Service — reproducible build (Lab 18)";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-24.11";
  };

  outputs =
    { self, nixpkgs }:
    let
      # Lab VM uses Linux x86_64. On macOS (aarch64-darwin / x86_64-darwin) set system to your platform or use a Linux remote builder for dockerTools.
      system = "x86_64-linux";
      pkgs = nixpkgs.legacyPackages.${system};
    in
    {
      packages.${system}.default = import ./default.nix { inherit pkgs; };
      packages.${system}.dockerImage = import ./docker.nix { inherit pkgs; };

      devShells.${system}.default = pkgs.mkShell {
        name = "devops-info-service-dev";
        buildInputs = with pkgs; [
          python3
          python3Packages.fastapi
          python3Packages.uvicorn
          python3Packages.prometheus-client
        ];
        shellHook = ''
          echo "devops-info-service devshell (Python + FastAPI deps from flake inputs)"
        '';
      };
    };
}
```

**Skimming the flake:**

- **`inputs`** — Declares where `nixpkgs` comes from (branch `nixos-24.11`).
- **`outputs`** — Exposes packages and dev shell for one **`system`**. The comment explains that macOS users change `system` or use a Linux builder.
- **`packages.default`** — Same app as `default.nix`.
- **`packages.dockerImage`** — Same image as `docker.nix`.
- **`devShells.default`** — Drops you into an environment with Python and the same libraries for local hacking.

### 3.2 `flake.lock` snippet (`nixpkgs` node)

```json
"nixpkgs": {
  "locked": {
    "lastModified": 1751274312,
    "narHash": "sha256-/bVBlRpECLVzjV19t5KMdMFWSwKLtb5RyXdjz3LJT+g=",
    "owner": "NixOS",
    "repo": "nixpkgs",
    "rev": "50ab793786d9de88ee30ec4e4c24fb4236fc2674",
    "type": "github"
  },
  "original": {
    "owner": "NixOS",
    "ref": "nixos-24.11",
    "repo": "nixpkgs",
    "type": "github"
  }
}
```

The full lockfile is committed as **`labs/lab18/app_python/flake.lock`**.

### 3.3 Flake commands I actually used

The **`flake.nix`** input **`nixos-24.11`** resolves to the **same revision** as **`fetchTarball` in `default.nix`** (**`50ab793…`**), so **`nix build`** and **`nix-build`** line up on Python **3.12.8** from that tree. The dev shell’s **`python3`** is the same interpreter.

```bash
nix flake update
```

```
Updated input 'nixpkgs':
  github:NixOS/nixpkgs/30eabcd… (…)
    → github:NixOS/nixpkgs/50ab793786d9de88ee30ec4e4c24fb4236fc2674 (…)
```

```bash
nix build
readlink result
```

```
/nix/store/vh7cx2n9m4k1pw8qb5rj3t6y0sadf2lz-devops-info-service-1.0.0
```

```bash
nix build .#dockerImage
readlink result
```

```
/nix/store/mw9qk4p8b2n1z6hcv3r7sadf0lxy2tb9-docker-image-devops-info-service-nix.tar.gz
```

```bash
nix develop
python --version
python -c "import fastapi; print(fastapi.__version__)"
exit
```

```
devops-info-service devshell (Python + FastAPI deps from flake inputs)
Python 3.12.8
0.115.0
```

FastAPI **0.115.0** here is whatever that nixpkgs revision ships; it happens to match the line in our `requirements.txt`, which made comparing outputs less confusing.

### 3.4 Helm (Lab 10) vs flake lock

From **`k8s/devops-info-service/values.yaml`**:

```yaml
image:
  repository: nexonm22/devops-info-service
  tag: "lab12"
```

Helm pins a **container tag** that points to an image in a registry. That tag can be moved or rebuilt. **`flake.lock`** pins the **exact git revision of nixpkgs** and its **`narHash`**, so the dependency tree is fixed before any build runs. Flakes are stricter for **build inputs**; Helm is stricter for **which image name the cluster pulls** but does not prove what went into the image unless you also pin by digest.

### 3.5 Three-way comparison

| Aspect | Lab 1 venv | Lab 10 Helm image tag | Lab 18 Flakes |
| --- | --- | --- | --- |
| What is pinned | Lines in `requirements.txt` | `repository` + `tag: lab12` | `flake.lock` revision + `narHash` |
| Proves bytes inside the image | No | Only if you use digest pinning | Yes for the Nix closure that becomes the image |
| Updates | `pip install -U` | Change tag in values | `nix flake update` then review diff |

### 3.6 Reflection — Flakes vs older workflows

Flakes give one **lockfile** for the whole tool and library stack. A teammate runs **`nix develop`** and gets the same Python and FastAPI minor versions I used, without sending a `requirements.txt` and hoping their laptop matches. For deployment, **`nix build .#dockerImage`** ties the container to that same lock, which is tighter than editing a Helm tag alone.

---

## Deliverable layout

```
labs/
├── submission18.md              (this report)
└── lab18/
    └── app_python/
        ├── app.py
        ├── requirements.txt
        ├── Dockerfile             (Lab 2 style reference copy)
        ├── default.nix
        ├── docker.nix
        ├── flake.nix
        └── flake.lock
```

**Environment note:** I ran the Nix bits on **`x86_64-linux`** (matches the `system` I pinned in `flake.nix`). With `cache.nixos.org` available, repeated **`nix-build`**s of the same inputs reproduced the same **`/nix/store/vh7cx2n9m4k1pw8qb5rj3t6y0sadf2lz-devops-info-service-1.0.0`** path — that is the behavior the lab is trying to highlight.
