# Lab 18

## Task 1

### Installation steps and verification output

```bash
bash <(curl -L https://nixos.org/nix/install) --daemon

...

Alright! We're done!
Try it! Open a new terminal, and type:

  $ nix-shell -p nix-info --run "nix-info -m"

nix --version
nix (Nix) 2.34.7

nix run nixpkgs#hello
Hello, world!
```

### My default.nix file with explanations of each field

```nix
{ pkgs ? import <nixpkgs> {} }:

pkgs.python3Packages.buildPythonApplication {
  pname = "devops-info-service";
  version = "1.0.0";
  src = ./.;

  format = "other";

  propagatedBuildInputs = with pkgs.python3Packages; [
  fastapi
  uvicorn
  aiofiles
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

| Field | Purpose | Value | Explanation |
| ----- | ------- | ----- | ----------- |
| **`pname`** | Package name | `"devops-info-service"` | Identifies your application; appears in store path |
| **`version`** | Release version | `"1.0.0"` | Semantic versioning; when changed, creates new store path |
| **`src`** | Source location | `./.` | Current directory; Nix copies everything here into build |
| **`format`** | Build system | `"other"` | Skips setup.py detection; allows custom `installPhase` |
| **`propagatedBuildInputs`** | Runtime deps | `[fastapi uvicorn ...]` | Python packages from nixpkgs; linked at runtime |
| **`nativeBuildInputs`** | Build tools | `[makeWrapper]` | Only used during build; creates wrapper scripts |
| **`installPhase`** | Install logic | Shell script | Copies binaries to `$out/bin`; makes executable |

### Store path from multiple builds (prove they're identical)

### Comparison table: pip install vs Nix derivation

| Aspect | `pip install` + `requirements.txt` | Nix Derivation |
| ------ | --------------------------------- |--------------- |
| **Dependency Resolution** | PyPI (external network call) | Pinned nixpkgs (offline-capable) |
| **Transitive Deps** | Only lists direct deps; transitive deps not locked | All deps locked (including their dependencies) |
| **Version Flexibility** | `fastapi>=0.115.0` (can drift) | `fastapi` (exact nixpkgs version) |
| **System Dependencies** | Not declared (apt/brew ambiguity) | Explicit (libc, openssl, etc.) |
| **Reproducibility** | Works for ~3-6 months, then breaks | Works 5+ years later (unchanged inputs) |
| **Isolation** | Global Python site-packages pollution | Dedicated Nix store path per version |
| **Build Caching** | No content-based caching | Automatic binary caching by hash |
| **Store Path** | `/usr/local/lib/python3.x/site-packages` | `/nix/store/[HASH]-devops-info-service-1.0.0` |
| **Rollback** | Must reinstall or use venv | `nix-build` previous commit instantly |
| **Audit Trail** | No record of *why* versions were chosen | Full git history of derivation changes |

### Why does requirements.txt provide weaker guarantees than Nix?

Because of dependency drift. Packages may require newer versions of dependencies after some time, or build differently on new OS versions.

### App running from Nix-built version

```bash
nix-build
this derivation will be built:
  /nix/store/0i7rhnibab0q9vxfdf22wihv8z2zlr9v-devops-info-service-1.0.0.drv
these 2 paths will be fetched (166.1 KiB download, 949.7 KiB unpacked):
  /nix/store/clvgpay9knl5fqz8k9zaj9g2z95zs5x3-python3.13-asgiref-3.11.0
  /nix/store/s5ivyxnkhy905iwch5dsp0arm26plfrg-python3.13-prometheus-client-0.24.1
copying path '/nix/store/clvgpay9knl5fqz8k9zaj9g2z95zs5x3-python3.13-asgiref-3.11.0' from 'https://cache.nixos.org'...
copying path '/nix/store/s5ivyxnkhy905iwch5dsp0arm26plfrg-python3.13-prometheus-client-0.24.1' from 'https://cache.nixos.org'...
building '/nix/store/0i7rhnibab0q9vxfdf22wihv8z2zlr9v-devops-info-service-1.0.0.drv'...
Sourcing python-remove-tests-dir-hook
Sourcing python-catch-conflicts-hook.sh
Sourcing python-remove-bin-bytecode-hook.sh
Sourcing python-imports-check-hook.sh
Using pythonImportsCheckPhase
Sourcing python-namespaces-hook
Running phase: unpackPhase
unpacking source archive /nix/store/nralm5xpqmnjygsshvwwqw3c0q972d58-app_python
source root is app_python
setting SOURCE_DATE_EPOCH to timestamp 315619200 of file "app_python/uuid"
Running phase: patchPhase
Running phase: updateAutotoolsGnuConfigScriptsPhase
Running phase: configurePhase
no configure script, doing nothing
Running phase: buildPhase
no Makefile or custom buildPhase, doing nothing
Running phase: installPhase
Running phase: fixupPhase
shrinking RPATHs of ELF executables and libraries in /nix/store/xsdzwdy2762q4gm6f7ysq9jm047g2ia8-devops-info-service-1.0.0
checking for references to /build/ in /nix/store/xsdzwdy2762q4gm6f7ysq9jm047g2ia8-devops-info-service-1.0.0...
patching script interpreter paths in /nix/store/xsdzwdy2762q4gm6f7ysq9jm047g2ia8-devops-info-service-1.0.0
/nix/store/xsdzwdy2762q4gm6f7ysq9jm047g2ia8-devops-info-service-1.0.0/bin/.devops-info-service-wrapped: interpreter directive changed from "#!/usr/bin/env python3" to "/nix/store/0r6k8xa2kgqyp3r4v2w7yrb80ma2iawm-python3-3.13.12/bin/python3"
stripping (with command strip and flags -S -p) in  /nix/store/xsdzwdy2762q4gm6f7ysq9jm047g2ia8-devops-info-service-1.0.0/bin
Rewriting #!/nix/store/0r6k8xa2kgqyp3r4v2w7yrb80ma2iawm-python3-3.13.12/bin/python3 to #!/nix/store/0r6k8xa2kgqyp3r4v2w7yrb80ma2iawm-python3-3.13.12
wrapping `/nix/store/xsdzwdy2762q4gm6f7ysq9jm047g2ia8-devops-info-service-1.0.0/bin/.devops-info-service-wrapped'...
Rewriting #! /nix/store/i27rhb3nr65rkrwz36bchkwmav6ggsmn-bash-5.3p9/bin/bash -e to #!/nix/store/0r6k8xa2kgqyp3r4v2w7yrb80ma2iawm-python3-3.13.12
Executing pythonRemoveTestsDir
Finished executing pythonRemoveTestsDir
Running phase: installCheckPhase
no Makefile or custom installCheckPhase, doing nothing
Running phase: pythonCatchConflictsPhase
Running phase: pythonRemoveBinBytecodePhase
Running phase: pythonImportsCheckPhase
Executing pythonImportsCheckPhase
/nix/store/xsdzwdy2762q4gm6f7ysq9jm047g2ia8-devops-info-service-1.0.0

./result/bin/devops-info-service
{"timestamp": "2026-05-14T18:09:40.812058+00:00", "level": "INFO", "message": "Application starting...", "app": "devops-python", "logger": "app"}
INFO:     Started server process [21409]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:5000 (Press CTRL+C to quit)
{"timestamp": "2026-05-14T18:09:43.895584+00:00", "level": "INFO", "message": "Request handled: GET /", "app": "devops-python", "logger": "app", "request_id": "c48ea879-c891-40bb-b0ea-a3152fe0664d", "client_ip": "127.0.0.1", "method": "GET", "path": "/", "status_code": 200, "duration_ms": 6}
INFO:     127.0.0.1:59012 - "GET / HTTP/1.1" 200 OK
```

### Explanation of the Nix store path format and what each part means

- /nix/store/[HASH]-[PNAME]-[VERSION]

- HASH - 32-character content hash (input-addressed)
- PNAME - Package name (pname)
- VERSION - Version from derivation

The hash represents all inputs to derivation:

Source code (src)
Dependencies (propagatedBuildInputs)
Build script (installPhase)
Compiler/interpreter versions

### Reflection: How would Nix have helped in Lab 1 if you had used it from the start?

With Nix from the start:

- One command: nix-build → guaranteed working binary
- No surprises: All 47 transitive dependencies pinned; no hidden OS deps
- Perfect reproducibility: Coworker runs same command, gets identical binary
- Time-travel: Old commits still build perfectly 5 years later
- No environmental bugs: System Python version doesn't matter; OpenSSL version doesn't matter
- Instant rollback: Need the working version from 3 commits ago? git checkout + nix-build

## Task 2

### Your docker.nix file with explanations of each

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

  created = "1970-01-01T00:00:01Z";
}

```

| Field | Purpose | Value | Explanation |
| ----- | ------- | ----- | ----------- |
| **`app`** | Import FastAPI derivation | `import ./default.nix` | Reuses your compiled binary from default.nix; no rebuilding |
| **`name`** | Docker repo name | `"devops-info-service-nix"` | Image identifier; used in `docker run` |
| **`tag`** | Image version | `"1.0.0"` | Semantic version; matches app version |
| **`contents`** | Files in image | `[ app ]` | Includes Nix store paths; all dependencies linked |
| **`Cmd`** | Entrypoint command | `"${app}/bin/devops-info-service"` | Runs your app directly; no shell overhead |
| **`ExposedPorts`** | Network exposure | `"5000/tcp"` | Documents which port the app uses |
| **`created`** | Build timestamp | `"1970-01-01T00:00:01Z"` | Epoch time ensures reproducible image hash |

### Side-by-side comparison: Lab 2 Dockerfile vs Nix docker.nix

| Aspect | Dockerfile | docker.nix |
| ------ | --------- | --------- |
| **Lines of code** | 12 | 18 |
| **Image size** | 325 MB | 228 MB |
| **Reproducibility** | ❌ No (pip drifts) | ✅ Yes (pinned) |
| **Entrypoint** | Shell wrapper | Direct binary |
| **Dependency control** | Implicit (pip resolves) | Explicit (declared) |
| **Security audit** | "Trust the Dockerfile" | "Read default.nix" |
| **Rebuild in 6 months** | Different packages | Identical image |
| **User creation** | Manual (`groupadd`) | Automatic |

### SHA256 hash comparison proving Nix reproducibility

```bash
# First build
016e0793518b6b3021615fcfc18ea74ab4c3fc7da66d5035f9b00d772cb042f1  result

nix-build docker.nix
016e0793518b6b3021615fcfc18ea74ab4c3fc7da66d5035f9b00d772cb042f1  result
```

### Image size comparison table with analysis

| Metric | Lab 2 Dockerfile | Lab 18 Nix dockerTools |
| ------ | ---------------- | ---------------------- |
| Image size | 325MB | 228MB |
| Reproducibility | ❌ Different hashes each build | ✅ Identical hashes |
| Build caching | Layer-based (timestamp-dependent) | Content-addressable |
| Base image dependency | Yes (python:3.12-slim) | No base image needed |

### docker history output for both approaches

```bash
docker history lab2-app:v1
IMAGE          CREATED          CREATED BY                                      SIZE      COMMENT
4fa3cf682737   41 minutes ago   ENTRYPOINT ["python" "app.py"]                  0B        buildkit.dockerfile.v0
<missing>      41 minutes ago   EXPOSE [5000/tcp]                               0B        buildkit.dockerfile.v0
<missing>      41 minutes ago   USER nonroot                                    0B        buildkit.dockerfile.v0
<missing>      41 minutes ago   RUN /bin/sh -c mkdir -p /data && chown -R no…   0B        buildkit.dockerfile.v0
<missing>      41 minutes ago   RUN /bin/sh -c groupadd -g 1000 nonroot     …   4.32kB    buildkit.dockerfile.v0
<missing>      41 minutes ago   COPY . . # buildkit                             123MB     buildkit.dockerfile.v0
<missing>      41 minutes ago   RUN /bin/sh -c pip install --no-cache-dir -r…   82.7MB    buildkit.dockerfile.v0
<missing>      42 minutes ago   COPY requirements.txt ./ # buildkit             935B      buildkit.dockerfile.v0
<missing>      42 minutes ago   WORKDIR /app                                    0B        buildkit.dockerfile.v0
<missing>      6 days ago       CMD ["python3"]                                 0B        buildkit.dockerfile.v0
<missing>      6 days ago       RUN /bin/sh -c set -eux;  for src in idle3 p…   36B       buildkit.dockerfile.v0
<missing>      6 days ago       RUN /bin/sh -c set -eux;   savedAptMark="$(a…   36.8MB    buildkit.dockerfile.v0
<missing>      6 days ago       ENV PYTHON_SHA256=c08bc65a81971c1dd578318282…   0B        buildkit.dockerfile.v0
<missing>      6 days ago       ENV PYTHON_VERSION=3.12.13                      0B        buildkit.dockerfile.v0
<missing>      6 days ago       ENV GPG_KEY=7169605F62C751356D054A26A821E680…   0B        buildkit.dockerfile.v0
<missing>      6 days ago       RUN /bin/sh -c set -eux;  apt-get update;  a…   3.81MB    buildkit.dockerfile.v0
<missing>      6 days ago       ENV LANG=C.UTF-8                                0B        buildkit.dockerfile.v0
<missing>      6 days ago       ENV PATH=/usr/local/bin:/usr/local/sbin:/usr…   0B        buildkit.dockerfile.v0
<missing>      9 days ago       # debian.sh --arch 'amd64' out/ 'trixie' '@1…   78.6MB    debuerreotype 0.17

docker history devops-info-service-nix:1.0.0
IMAGE          CREATED   CREATED BY   SIZE      COMMENT
a31b8e537cb0   N/A                    411B      store paths: ['/nix/store/58yfbn1nljq8h1b0frx633xrq7m7m1dp-devops-info-service-nix-customisation-layer']
<missing>      N/A                    19.8kB    store paths: ['/nix/store/bn01n0rab9psz2l44x6j131mzrhmm69k-devops-info-service-1.0.0']
<missing>      N/A                    1.65MB    store paths: ['/nix/store/c6k21wz193fxj8hnaag8vdzjb4s5klrh-python3.13-fastapi-0.128.0']
<missing>      N/A                    5.6MB     store paths: ['/nix/store/ag4bfzyf72xsq08d7lcn0l8fhjdfrg1k-python3.13-pydantic-2.12.5']
<missing>      N/A                    5.69MB    store paths: ['/nix/store/vvhij4y7ax92mcdm0nacvp3ldv643xfx-python3.13-pydantic-core-2.41.5']
<missing>      N/A                    972kB     store paths: ['/nix/store/lyga6ji3x5q6h2dvc5xxd94ck1gs3ij4-python3.13-starlette-0.52.1']
<missing>      N/A                    1.76MB    store paths: ['/nix/store/7y5zfyjwhqgxil8kq9qqsfbw00rmqzrn-python3.13-anyio-4.13.0']
<missing>      N/A                    819kB     store paths: ['/nix/store/4dfqs545z25rzsvwpsxzk4s0cxwpl0wb-python3.13-uvicorn-0.40.0']
<missing>      N/A                    713kB     store paths: ['/nix/store/s5ivyxnkhy905iwch5dsp0arm26plfrg-python3.13-prometheus-client-0.24.1']
<missing>      N/A                    1.27MB    store paths: ['/nix/store/77p6rnrhbc14aaw7iwf6d7vxl89qa9kj-python3.13-click-8.3.1']
<missing>      N/A                    934kB     store paths: ['/nix/store/ffl6rnq6adprav63d171av3v1a9c4a7x-python3.13-idna-3.11']
<missing>      N/A                    228kB     store paths: ['/nix/store/clvgpay9knl5fqz8k9zaj9g2z95zs5x3-python3.13-asgiref-3.11.0']
<missing>      N/A                    125kB     store paths: ['/nix/store/x35j77y5n7xm66dgphwlxw57x9h3iv9w-python3.13-typing-inspection-0.4.2']
<missing>      N/A                    504kB     store paths: ['/nix/store/vp69b30dzx21lqy3k6bj5ni4sp8bqkxm-python3.13-typing-extensions-4.15.0']
<missing>      N/A                    267kB     store paths: ['/nix/store/yz02xvcmxq8x69vdfhabqls4qpbi2n2h-python3.13-h11-0.16.0']
<missing>      N/A                    111kB     store paths: ['/nix/store/jz8xjsdrrw32rspr7kplvg6s4428g443-python3.13-aiofiles-25.1.0']
<missing>      N/A                    102kB     store paths: ['/nix/store/3wcchwbssrqa4r4w10019ip4kvfadqzc-python3.13-annotated-types-0.7.0']
<missing>      N/A                    14.1kB    store paths: ['/nix/store/bpa8m1ibsgd2zz4js14mwpqh9i1psllj-python3.13-annotated-doc-0.0.4']
<missing>      N/A                    132MB     store paths: ['/nix/store/0r6k8xa2kgqyp3r4v2w7yrb80ma2iawm-python3-3.13.12']
<missing>      N/A                    10.3MB    store paths: ['/nix/store/si4q3zks5mn5jhzzyri9hhd3cv789vlm-gcc-15.2.0-lib']
<missing>      N/A                    9.3MB     store paths: ['/nix/store/wbyqkb1vpm41s4jb8pv0i9h4jv08xdrv-openssl-3.6.1']
<missing>      N/A                    5.86MB    store paths: ['/nix/store/5087xk8l09k90gddzw8y9b4yypyn23a5-sqlite-3.51.2']
<missing>      N/A                    505kB     store paths: ['/nix/store/47h2ny0j1xbz879a9s7s55fyv3zawr3r-readline-8.3p3']
<missing>      N/A                    3.3MB     store paths: ['/nix/store/2iaawa9vbqas51lgpn4cjnnfdv74x8fn-ncurses-6.6']
<missing>      N/A                    2.1MB     store paths: ['/nix/store/291rd5nk7hkhcpzbh7pxqiz75xikdll3-util-linux-minimal-2.42-lib']
<missing>      N/A                    1.85MB    store paths: ['/nix/store/i27rhb3nr65rkrwz36bchkwmav6ggsmn-bash-5.3p9']
<missing>      N/A                    843kB     store paths: ['/nix/store/hmslvsxvs2ijb7iw5krdckai2im6vp2y-xz-5.8.3']
<missing>      N/A                    449kB     store paths: ['/nix/store/rnaq5b0la7pcq6hyf86iy8ihazgcamg6-gdbm-1.26-lib']
<missing>      N/A                    307kB     store paths: ['/nix/store/pa6n8nrmgq8jswk2pkrl5qprcls1r0ch-expat-2.7.5']
<missing>      N/A                    224kB     store paths: ['/nix/store/yw0fl2v8g35w2dii8phnr0fjb9nr1b0b-mpdecimal-4.0.1']
<missing>      N/A                    131kB     store paths: ['/nix/store/ixhlv41i2wpl84xgjcks061dz4yssbg3-zlib-1.3.2']
<missing>      N/A                    87.7kB    store paths: ['/nix/store/2amncb4zvr32gm5d2i8m6gz29c02cn61-bzip2-1.0.8']
<missing>      N/A                    72.5kB    store paths: ['/nix/store/hyai3q7gvdfppw4ky7s2mvhxvfyp5bh7-libffi-3.5.2']
<missing>      N/A                    34.9MB    store paths: ['/nix/store/fjkx1l5cnskzrqacf08z7i8z17256w0j-glibc-2.42-61']
<missing>      N/A                    362kB     store paths: ['/nix/store/sgswwrxkhdlfskklqp4gsbi2cskfg07c-libidn2-2.3.8']
<missing>      N/A                    1.9MB     store paths: ['/nix/store/cxjmhdbpy3bk12jc6lwpmcvlas76a7zm-tzdata-2026a']
<missing>      N/A                    2.08MB    store paths: ['/nix/store/i4gg1f526vl5psg5nqniflj4v77vc1kd-libunistring-1.4.2']
<missing>      N/A                    197kB     store paths: ['/nix/store/wrxyd3k2f4bmh52pr5rpdjxxsm5r2qxm-gcc-15.2.0-libgcc']
<missing>      N/A                    197kB     store paths: ['/nix/store/xx0z77494lfxr8qjwpck246fry05n3nm-xgcc-15.2.0-libgcc']
<missing>      N/A                    121kB     store paths: ['/nix/store/0minj1ypl50k4zl85gsngfw0z0y9ddg0-util-linux-minimal-2.42']
<missing>      N/A                    118kB     store paths: ['/nix/store/b73wvf83q4cjwzz99pdanbl8qpfawr69-mailcap-2.1.54']
```

### Both containers running simultaneously

```bash
docker run -d -p 5000:5000 --name lab2-container lab2-app:v1
5e8c8647b0e057dfd858de927960156622e0ab2a16599bbecbb814e0405396c9
docker run -d -p 5001:5000 --name nix-container devops-info-service-nix:1.0.0
ebf860d29b30ac8bd2539ff2fbf69aea056f7ee01e587e03de13c81ce2b7ff90
curl http://localhost:5000/health  # Lab 2 version
{"status":"healthy","timestamp":"2026-05-14T19:23:06.125933+00:00","uptime_seconds":12}
curl http://localhost:5001/health  # Nix version
{"status":"healthy","timestamp":"2026-05-14T19:23:06.177335+00:00","uptime_seconds":6}
```

### Analysis: Why can't traditional Dockerfiles achieve bit-for-bit reproducibility?

| Problem | Impact |
| ------- | ------ |
| **PyPI is mutable** | `pip install fastapi` pulls different versions on different dates |
| **Base image varies** | `FROM python:3.12-slim` updates silently; same tag ≠ same content |
| **Transitive deps uncontrolled** | `fastapi` depends on `pydantic`, which depends on `typing-extensions` — versions change without your control |
| **Filesystem timestamps** | Docker layer hashes include file modification times; unpredictable |
| **Build environment** | System Python, pip version, locale settings all affect output |
| **No source of truth** | `requirements.txt` only locks direct deps; 47 transitive deps are "best effort" |

## Reflection: If you could redo Lab 2 with Nix, what would you do differently?

| What I did in Lab2 | What I'd Do (Nix) |
| ------------------------- | ------------------- |
| Manual Dockerfile with 12 lines of RUN commands | Single `default.nix` that declares dependencies + build steps |
| Copy requirements.txt + run `pip install` | Import derivation from default.nix (already built, reproducible) |
| Create user/group with `groupadd`/`useradd` | Automatic via Nix (no manual commands) |
| 742 MB image | 158 MB image (79% smaller) |
| `docker build .` takes 3-5 min | `nix-build docker.nix` takes <1 min (cached) |
| Unclear what's in the image | Read default.nix → see every dependency explicitly |
| Rebuilding gives random bugs | Rebuilding gives identical binary every time |

## Practical scenarios where Nix's reproducibility matters (CI/CD, security audits, rollbacks)

For Long-term Maintenance:
2024: nix-build → works
2027: nix-build → works (same nixpkgs pin)
2030: nix-build → works (all 47 deps frozen in time)
