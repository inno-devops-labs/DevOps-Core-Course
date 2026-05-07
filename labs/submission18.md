# Lab 18

## Task 1

### 1.1 Nix Installation
- Command used: `curl --proto '=https' --tlsv1.2 -sSf -L https://install.determinate.systems/nix | sh -s -- install`
- Version: `nix --version` → `nix (Nix) 2.24.9` (replace with yours)
- Enabled flakes by adding `experimental-features = nix-command flakes` to `~/.config/nix/nix.conf`

### 1.2 Nix Derivation (`default.nix`)
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
    prometheus-client
    starlette
  ];

  nativeBuildInputs = [ pkgs.makeWrapper ];

  installPhase = ''
    install -Dm755 app.py $out/bin/devops-info-service
    wrapProgram $out/bin/devops-info-service \
      --prefix PYTHONPATH : "$PYTHONPATH"
  '';
}
```

- buildPythonApplication creates a Python environment with exactly the listed dependencies.

- install -Dm755 sets the executable bit, required for wrapProgram.

- wrapProgram ensures the wrapped script finds all Python packages via PYTHONPATH.

- No network access during build (pure sandbox).

### 1.3 Proving Reproducibility


```bash
$ nix-build
warning: Nix search path entry '/nix/var/nix/profiles/per-user/vexell/channels/nixpkgs' does not exist, ignoring
warning: Nix search path entry '/nix/var/nix/profiles/per-user/vexell/channels' does not exist, ignoring
...
/nix/store/0jaffnl12fkx7yvbrq0i7r48bqzrdm4p-devops-info-service-1.0.0

$ rm result
nix-store --delete /nix/store/abc123...-devops-info-service-1.0.0
nix-build
readlink result

warning: Nix search path entry '/nix/var/nix/profiles/per-user/vexell/channels/nixpkgs' does not exist, ignoring
warning: Nix search path entry '/nix/var/nix/profiles/per-user/vexell/channels' does not exist, ignoring
...
/nix/store/0jaffnl12fkx7yvbrq0i7r48bqzrdm4p-devops-info-service-1.0.0
```

### 1.4 Comparison: pip vs Nix

| Aspect | pip + requirements.txt | Nix Derivation |
|--------|------------------------|----------------|
| **Reproducibility guarantee** | Approximate – `pip` installs packages at runtime; even with pinned versions, transitive dependencies can drift over time. | Bit‑for‑bit identical – all inputs (source, dependencies, build instructions) are hashed; same hash = same output forever. |
| **Dependency resolution** | At runtime via `pip` (network access). Transitive dependencies are not locked and may differ between installs. | At build time in a **pure sandbox** – no network, no system libraries. Every dependency is pinned down to its exact store path. |
| **Python version** | System‑dependent (user must install the correct Python). | Explicitly pinned in the derivation (e.g., `python3Packages` from a specific nixpkgs revision). |
| **Isolation** | Virtual environment only isolates Python packages; still uses system libraries and compilers. | Builds run in an isolated sandbox with no access to `/home`, `/tmp`, or the network. Only declared inputs are visible. |
| **Build environment** | Identical on different machines only if OS, Python version, and system libraries match. | Same on any machine that runs Nix – the entire build environment is defined and locked. |
| **Caching** | No binary cache; `pip` re‑downloads and re‑builds wheels every time. | Global binary cache (`cache.nixos.org`); if a build output matches a cached hash, it is reused instantly. |
| **Store path** | N/A (files scattered in `venv/` or system). | Content‑addressed: `/nix/store/<hash>-<name>-<version>`. The hash changes only when inputs change. |
| **Portability** | Works only on systems with the same Python version and OS. | Works anywhere Nix runs (Linux, macOS, WSL2) – same hash, same result. |
| **Upgradability** | No single command to upgrade all dependencies safely; often leads to “works on my machine” problems. | Atomic upgrades – switch to a new generation instantly; rollback is just as easy. |
| **Security** | No built‑in integrity checking beyond PyPI signatures; dependency chains are hard to audit. | Every dependency is hashed and verified; entire closure can be audited by inspecting `/nix/store`. |

**Conclusion:**  
`requirements.txt` provides a *description* of what to install; Nix provides a *recipe* for a fully‑reproducible build. With Nix, the same source code and locked nixpkgs revision will produce **exactly** the same binary output on any machine, at any point in time – something `pip` cannot guarantee.

## Task 2

### 2.1 docker.nix

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
  };

  created = "1970-01-01T00:00:01Z";   # fixed for reproducibility
}
```
- buildLayeredImage creates a minimal image with only the app and its runtime closure.

- Fixed created date ensures no timestamp differences.

### 2.3 Proving Docker Image Reproducibility

``` bash
$ rm result
nix-build docker.nix
sha256sum result

rm result
nix-build docker.nix
sha256sum result

/nix/store/jzx8yhryjaf3yl78vxbs14vmaiyakssk-devops-info-service-nix.tar.gz
c4cc9e35a5424c2ae16beee76cbce00fcbb1c44cda84783a577db431e7016db3  result
/nix/store/jzx8yhryjaf3yl78vxbs14vmaiyakssk-devops-info-service-nix.tar.gz
c4cc9e35a5424c2ae16beee76cbce00fcbb1c44cda84783a577db431e7016db3  result

$ docker save lab2-app:v1 | sha256sum
docker save lab2-app:v2 | sha256sum
9cf01c5d41e52f9906b441d489cfd1ade7351fe9f6cdbceb1683d29b4f21541b  -
e7f8a1bc490d2c40d0f0e91f7d0815ecdcd41630b4397a243b592c072807feb3  -
```

### 2.4 Image Size & Layer Analysis


```bash
$ docker images | grep -E "lab2-app|devops-info-service-nix"
lab2-app                      v2         6a86d9d66e82   33 minutes ago   158MB
devops-info-service-nix       1.0.0      a4c2b05ee157   56 years ago     79MB
```

Nix includes only the exact runtime closure, no package manager cache, no unnecessary files.

History:

```bash
$ docker history devops-info-service-nix:1.0.0 
IMAGE          CREATED   CREATED BY   SIZE      COMMENT
a4c2b05ee157   N/A                    411B      store paths: ['/nix/store/lx5anyqpy31l0hrna21z91k5w1d5zraz-devops-info-service-nix-customisation-layer']
<missing>      N/A                    24.8kB    store paths: ['/nix/store/agpz5x1w355mwljc40mr5805kfbp55y9-devops-info-service-1.0.0']
<missing>      N/A                    598kB     store paths: ['/nix/store/a4v5qavdkzip0bnwhmnq2a7m62hpnnpc-python3.12-prometheus-client-0.21.0']
<missing>      N/A                    1.57MB    store paths: ['/nix/store/vjqfw43rxy131adwryhnbkqwm2s9ifrj-python3.12-fastapi-0.115.3']
<missing>      N/A                    959kB     store paths: ['/nix/store/pg6bbpax5gv1lsqdf48ihfkk290z21ck-python3.12-starlette-0.40.0']
<missing>      N/A                    5.19MB    store paths: ['/nix/store/7jr854jfj9d7pvmyri93pqcsikhkgw6f-python3.12-pydantic-2.9.2']
<missing>      N/A                    68.3kB    store paths: ['/nix/store/l7npwl7wpa7nn2dw5x49j8i4k9zhh799-python3.12-fastapi-cli-0.0.5']
<missing>      N/A                    1.71MB    store paths: ['/nix/store/ly16libw5rfv5jp0bkl7k9f23pznbc6k-python3.12-websockets-13.1']
<missing>      N/A                    1.26MB    store paths: ['/nix/store/f4crycjacngszp8f5pc8inmskqql6day-python3.12-watchfiles-0.22.0']
<missing>      N/A                    2.87MB    store paths: ['/nix/store/znyn7lp60ailv21g984gxwxqg14a80ny-python3.12-uvloop-0.21.0']
<missing>      N/A                    741kB     store paths: ['/nix/store/a7wqb0db16ck2difr1sfh8cfwxzmy6bi-python3.12-uvicorn-0.32.0']
<missing>      N/A                    584kB     store paths: ['/nix/store/app2dirpdqlfmps9mprl6lnmw9rwqkh8-python3.12-typer-0.12.5']
<missing>      N/A                    1.01MB    store paths: ['/nix/store/65rmc1i009is7irgvhz2750xygsw2bwb-python3.12-pyyaml-6.0.2']
<missing>      N/A                    147kB     store paths: ['/nix/store/3m0jdpw2ppa730lip4bkjaw4yky8c9h4-python3.12-python-dotenv-1.0.1']
<missing>      N/A                    5.25MB    store paths: ['/nix/store/b452s1h1yllk5n39ajayz69cli05m4ym-python3.12-pydantic-core-2.23.4']
<missing>      N/A                    255kB     store paths: ['/nix/store/bwk7hdxx9czjiyzsq17p9pz6ryba7i9n-python3.12-httptools-0.6.1']
<missing>      N/A                    101kB     store paths: ['/nix/store/1dm8049nng9flvwiywh0agc2lzdbnni8-python3.12-annotated-types-0.7.0']
<missing>      N/A                    139kB     store paths: ['/nix/store/5m4m5wbnx411zsfs6ckgnkidrz672l8k-libyaml-0.2.5']
<missing>      N/A                    57.1kB    store paths: ['/nix/store/wlzx88r2c5w8prbvwi92k58ag98za4lx-python3.12-shellingham-1.5.4']
<missing>      N/A                    3.28MB    store paths: ['/nix/store/dlcl9ck50dhaypc9qxqyvh9ncbdmpj24-python3.12-rich-13.8.1']
<missing>      N/A                    573kB     store paths: ['/nix/store/a3gdgh4z97vkqq82nc3fiq4w3x6vaam1-python3.12-h11-0.14.0']
<missing>      N/A                    1.37MB    store paths: ['/nix/store/2m5ahw91s519zlc4b0rj43y14hw43509-python3.12-anyio-4.6.2']
<missing>      N/A                    430kB     store paths: ['/nix/store/s94x484kb3sz24404y9dr7avgw30318j-python3.12-typing-extensions-4.12.2']
<missing>      N/A                    12MB      store paths: ['/nix/store/hla7ri4a51c83zjqlrdcrgkf8l0f7naq-python3.12-pygments-2.18.0']
<missing>      N/A                    718kB     store paths: ['/nix/store/7w9np3hsypcs3x18skmkwcvads2wzbp7-python3.12-markdown-it-py-3.0.0']
<missing>      N/A                    1.24MB    store paths: ['/nix/store/k1qzmvyvarz0pgjaz06wx0y5vsgwbhbw-python3.12-click-8.1.7']
<missing>      N/A                    38.6kB    store paths: ['/nix/store/jhgpnabwicy7awzaqzn1w234qxs2qcpy-python3.12-sniffio-1.3.1']
<missing>      N/A                    919kB     store paths: ['/nix/store/kf5yhz0pgq2gl3s7qwdxqqfn5ww7dpsl-python3.12-idna-3.10']
<missing>      N/A                    56.6kB    store paths: ['/nix/store/gvzaa6d4bwpf9z1qx4mc012i28dam6pa-python3.12-mdurl-0.1.2']
<missing>      N/A                    113MB     store paths: ['/nix/store/dksjvr69ckglyw1k2ss1qgshhcix73p8-python3-3.12.8']
<missing>      N/A                    837kB     store paths: ['/nix/store/izpczxh0wcm3ra6z0073zf9j0mv2wfl4-xz-5.6.3']
<missing>      N/A                    1.9MB     store paths: ['/nix/store/v87awkhzf3nr7nc5i4gg77xzqv4bqjy3-tzdata-2025b']
<missing>      N/A                    1.58MB    store paths: ['/nix/store/v9smapvfv1z340qs3p7xbw6zb6zplfcf-sqlite-3.46.1']
<missing>      N/A                    473kB     store paths: ['/nix/store/vb3dx18nky7cq63br7x2mi86isli529w-readline-8.2p13']
<missing>      N/A                    7.99MB    store paths: ['/nix/store/qzn96phpnb6c56mlqa1424hfgf5hp67s-openssl-3.3.3']
<missing>      N/A                    220kB     store paths: ['/nix/store/c25k325zh2b9g8s68b7ixbjfh3a916cb-mpdecimal-4.0.0']
<missing>      N/A                    118kB     store paths: ['/nix/store/n4gd4rqkr0p2rkdhklvbx1rnx78m6dkj-mailcap-2.1.54']
<missing>      N/A                    129kB     store paths: ['/nix/store/iissy6zslzyb85rzjgq4waag9dixvv6s-libxcrypt-4.4.36']
<missing>      N/A                    72.3kB    store paths: ['/nix/store/fm7yigp87wq0p58x92iynwscdmspzkrb-libffi-3.4.6']
<missing>      N/A                    443kB     store paths: ['/nix/store/jn8gi3mbjm6b2khxcbm3vf2c1h5wpv17-gdbm-1.24-lib']
<missing>      N/A                    286kB     store paths: ['/nix/store/h08i7wrlqmd48lnaimaz28pny9i8vmr8-expat-2.7.1']
<missing>      N/A                    79.5kB    store paths: ['/nix/store/vrqss3954zk1c52mda3xf1rv7wc5ygba-bzip2-1.0.8']
<missing>      N/A                    9.08MB    store paths: ['/nix/store/hh698a2nnpqr47lh52n26wi8fiah3hid-gcc-13.3.0-lib']
<missing>      N/A                    1.62MB    store paths: ['/nix/store/mjhcjikhxps97mq5z54j4gjjfzgmsir5-bash-5.2p37']
<missing>      N/A                    159kB     store paths: ['/nix/store/mkhhjfg2isjbfx87dz191bzpnwx1bbr9-gcc-13.3.0-libgcc']
<missing>      N/A                    127kB     store paths: ['/nix/store/b6mjyiadysqlh7nps52faznnqmp32604-zlib-1.3.1']
<missing>      N/A                    3.17MB    store paths: ['/nix/store/cn67k729khgnd9i1j7gbyh6lpzz11ci5-ncurses-6.4.20221231']
<missing>      N/A                    30MB      store paths: ['/nix/store/5m9amsvvh2z8sl7jrnc87hzy21glw6k1-glibc-2.40-66']
<missing>      N/A                    159kB     store paths: ['/nix/store/y4d9iir0yqmrcswaqfi368d8m1rkv14s-xgcc-13.3.0-libgcc']
<missing>      N/A                    346kB     store paths: ['/nix/store/c47b963idja6h1d8n91pf28v2jcq96kp-libidn2-2.3.7']
<missing>      N/A                    1.86MB    store paths: ['/nix/store/2745pvn6cv32yn9gp2rlqiqhqgs01pb5-libunistring-1.2']


$ docker history lab2-app:v2 
IMAGE          CREATED             CREATED BY                                      SIZE      COMMENT
6a86d9d66e82   About an hour ago   CMD ["python" "app.py" "--host" "0.0.0.0" "-…   0B        buildkit.dockerfile.v0
<missing>      About an hour ago   EXPOSE map[8000/tcp:{}]                         0B        buildkit.dockerfile.v0
<missing>      About an hour ago   USER appuser                                    0B        buildkit.dockerfile.v0
<missing>      About an hour ago   COPY --chown=appuser:appuser tests/ tests/ #…   580B      buildkit.dockerfile.v0
<missing>      About an hour ago   COPY --chown=appuser:appuser requirements.tx…   222B      buildkit.dockerfile.v0
<missing>      About an hour ago   COPY --chown=appuser:appuser app.py . # buil…   8.2kB     buildkit.dockerfile.v0
<missing>      About an hour ago   RUN /bin/sh -c pip install --no-cache-dir -r…   39.1MB    buildkit.dockerfile.v0
<missing>      About an hour ago   COPY requirements.txt . # buildkit              222B      buildkit.dockerfile.v0
<missing>      About an hour ago   WORKDIR /app                                    0B        buildkit.dockerfile.v0
<missing>      About an hour ago   RUN /bin/sh -c groupadd -r appuser && userad…   4.31kB    buildkit.dockerfile.v0
<missing>      2 weeks ago         CMD ["python3"]                                 0B        buildkit.dockerfile.v0
<missing>      2 weeks ago         RUN /bin/sh -c set -eux;  for src in idle3 p…   36B       buildkit.dockerfile.v0
<missing>      2 weeks ago         RUN /bin/sh -c set -eux;   savedAptMark="$(a…   36.8MB    buildkit.dockerfile.v0
<missing>      2 weeks ago         ENV PYTHON_SHA256=c08bc65a81971c1dd578318282…   0B        buildkit.dockerfile.v0
<missing>      2 weeks ago         ENV PYTHON_VERSION=3.12.13                      0B        buildkit.dockerfile.v0
<missing>      2 weeks ago         ENV GPG_KEY=7169605F62C751356D054A26A821E680…   0B        buildkit.dockerfile.v0
<missing>      2 weeks ago         RUN /bin/sh -c set -eux;  apt-get update;  a…   3.81MB    buildkit.dockerfile.v0
<missing>      2 weeks ago         ENV LANG=C.UTF-8                                0B        buildkit.dockerfile.v0
<missing>      2 weeks ago         ENV PATH=/usr/local/bin:/usr/local/sbin:/usr…   0B        buildkit.dockerfile.v0
<missing>      2 weeks ago         # debian.sh --arch 'amd64' out/ 'trixie' '@1…   78.6MB    debuerreotype 0.17
```

### 2.5 Side‑by‑Side Comparison

| Aspect | Traditional Dockerfile (Lab 2) | Nix dockerTools (Lab 18) |
|--------|--------------------------------|---------------------------|
| **Base image** | `python:3.12-slim` (mutable tag, changes over time) | No base image – only the exact runtime closure of the app |
| **Reproducibility** | Different image hash every build (timestamps, mutable layers) | Bit‑for‑bit identical tarball hash – same inputs, same output |
| **Timestamps** | Real build time (unpredictable, varies per build) | Fixed epoch (`created = "1970-01-01T00:00:01Z"`) |
| **Dependency installation** | `pip install` at build time (network access, possible drift) | Dependencies come from Nix store – already built, hashed, and cached |
| **Layer caching** | Docker layer cache – invalidated easily by timestamp or order changes | Nix store – perfect cache hit if input hashes match; never rebuilds identical derivations |
| **Image size** | ~158 MB (shared base layers) | ~80 MB with minimal closure |
| **Security** | Potential vulnerabilities in base image layers; hard to audit exact dependency tree | Minimal attack surface – only what's declared; every dependency is hashed and traceable |
| **Portability** | Requires only Docker to run | Requires Nix to build, then loads into any Docker runtime |
| **Atomicity / Rollback** | No built‑in rollback; images must be tagged manually | Nix store paths are immutable; rollback is instant by switching symlinks |
| **Build environment** | Host‑dependent (uses Docker daemon, ambient timestamps) | Pure sandbox – no network, no system files, deterministic build |

### 2.6 working containers
![](lab18screenshots/two%20containers.png)

### 2.7 Technical Analysis
- Nix derivations are reproducible because of: Pure function of inputs; all inputs (source, dependencies, build instructions) are hashed. Nix builds in a sandbox with no network, no system state.

- Dockerfiles aren’t because: Mutable base image tags, timestamps in layers, non‑deterministic package managers (pip, apt).

- Security: Smaller attack surface (fewer packages), no writable attack vectors, binaries can be audited by hash.

- .dockerignore vs Nix: Nix ignores anything not in the derivation’s src automatically; you just need to avoid including large files in the source tree.