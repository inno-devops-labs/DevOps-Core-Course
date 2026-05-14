# Lab 18 Submission - Reproducible Builds with Nix

## Environment

Repository branch:

```text
lab18
```

Local platform:

```text
macOS arm64
```

Docker CLI:

```text
Docker version 28.0.4, build b8034c0
```

Nix verification command:

```bash
nix --version
```

Current status before installation:

```text
nix (Determinate Nix 3.20.0) 2.34.6
```

Nix was installed with the Determinate Systems installer.

## Task 1 - Reproducible Python App

The Lab 1 Python service was copied into:

```text
lab18/app_python/
```

The copied application contains:

```text
app.py
requirements.txt
Dockerfile
default.nix
docker.nix
flake.nix
```

Original Lab 1 dependency file:

```text
Flask==3.1.0
prometheus-client==0.23.1
```

The application uses Flask and exposes the same operational endpoints used in earlier labs:

- `/`
- `/health`
- `/ready`
- `/metrics`
- `/visits`

The service listens on port `5002`.

### Nix Derivation

File: `lab18/app_python/default.nix`

```nix
{ pkgs ? import <nixpkgs> {} }:

let
  source = pkgs.lib.cleanSourceWith {
    src = ./.;
    filter = path: type:
      let
        name = baseNameOf path;
      in
      ! (
        name == "result"
        || name == ".git"
        || name == "__pycache__"
        || pkgs.lib.hasSuffix ".pyc" name
      );
  };

  pythonEnv = pkgs.python313.withPackages (ps: with ps; [
    flask
    prometheus-client
  ]);
in
pkgs.stdenv.mkDerivation {
  pname = "devops-info-service";
  version = "1.0.0";
  src = source;

  nativeBuildInputs = [ pkgs.makeWrapper ];

  installPhase = ''
    runHook preInstall

    mkdir -p $out/bin $out/share/devops-info-service
    cp app.py $out/share/devops-info-service/app.py

    makeWrapper ${pythonEnv}/bin/python $out/bin/devops-info-service \
      --add-flags "$out/share/devops-info-service/app.py" \
      --set PORT 5002 \
      --set VISITS_FILE /tmp/devops-info-service-visits

    runHook postInstall
  '';
}
```

Field explanations:

- `pkgs.python313.withPackages` creates a Python 3.13 environment with Flask and `prometheus-client`.
- `pname` and `version` define the package identity used in the Nix store path.
- `source = pkgs.lib.cleanSourceWith ...` makes the current application directory the source input while excluding generated files such as `result`.
- `makeWrapper` creates an executable command called `devops-info-service`.
- `VISITS_FILE=/tmp/devops-info-service-visits` avoids writing runtime state into the immutable Nix store.

### Build Commands

Run after installing Nix:

```bash
cd lab18/app_python
nix-build
readlink result
./result/bin/devops-info-service
```

Expected verification:

```bash
curl http://localhost:5002/health
```

Expected response shape:

```json
{
  "status": "healthy",
  "timestamp": "...",
  "uptime_seconds": 1
}
```

### Reproducibility Proof Commands

Build and record the first store path:

```bash
cd lab18/app_python
nix-build
readlink result
```

Rebuild and compare:

```bash
rm result
nix-build
readlink result
```

Force a real rebuild:

```bash
STORE_PATH=$(readlink result)
echo "Original store path: $STORE_PATH"
nix-store --delete "$STORE_PATH"
rm result
nix-build
readlink result
```

Hash the output:

```bash
nix-hash --type sha256 result
```

Result to record after running:

```text
First store path:  /nix/store/qqzlwjiawh40apjrdjiq8sdikzlqyryn-devops-info-service-1.0.0
Second store path: /nix/store/qqzlwjiawh40apjrdjiq8sdikzlqyryn-devops-info-service-1.0.0
Forced rebuild path: /nix/store/qqzlwjiawh40apjrdjiq8sdikzlqyryn-devops-info-service-1.0.0
Output sha256: c3bf0e6b5a564b4392712060e6170224cdbe8105680863dbbb77674209877f1c
```

The expected result is that all three store paths are identical because the source, dependencies, build instructions, and interpreter are identical.

Important fix found during testing: `src = ./.` originally included the generated `result` symlink in the source tree, which changed the input hash after the first build. The final derivation uses `pkgs.lib.cleanSourceWith` to exclude generated files, making repeated builds stable.

Nix-built app health check:

```text
{"status":"healthy","timestamp":"2026-05-14T13:42:17.889436+00:00","uptime_seconds":4}
```

### Lab 1 pip vs Lab 18 Nix

| Aspect | Lab 1 pip + venv | Lab 18 Nix |
| --- | --- | --- |
| Python version | Depends on local system | Defined by nixpkgs input |
| Direct dependencies | Listed in `requirements.txt` | Declared in `default.nix` |
| Transitive dependencies | Resolved by pip at install time | Fixed by nixpkgs closure |
| Build isolation | Virtual environment | Nix sandbox and immutable store |
| Rebuild output | Environment can drift | Same inputs produce same store path |
| Binary cache | Not content-addressed | Content-addressed Nix store |

`requirements.txt` gives weaker guarantees because it describes Python packages only. It does not pin the whole build environment: interpreter, system libraries, build tools, package indexes, and transitive dependency resolution can still vary. Nix fixes the complete dependency closure.

## Task 2 - Reproducible Docker Images

### Lab 2 Dockerfile

Original Dockerfile:

```dockerfile
FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN groupadd --gid 1000 appgroup \
    && useradd --uid 1000 --gid appgroup --create-home --home-dir /home/appuser --shell /bin/bash appuser \
    && mkdir -p /app /data \
    && chown -R appuser:appgroup /app /data

WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY app.py ./

RUN chown -R appuser:appgroup /app /data
USER appuser

EXPOSE 5002

CMD ["python", "app.py"]
```

Docker CLI was available, but the daemon was not running during this preparation step:

```text
Docker version 28.0.4
Docker daemon: Docker Desktop, Linux aarch64
```

After starting Docker Desktop, run:

```bash
docker build -t lab2-app:lab18-test1 ./app_python
docker inspect lab2-app:lab18-test1 | grep Created
sleep 5
docker build -t lab2-app:lab18-test2 ./app_python
docker inspect lab2-app:lab18-test2 | grep Created
```

Expected observation: the `Created` timestamps differ between builds.

Actual Docker metadata:

```text
lab2-app:lab18-test1 Created: 2026-05-14T13:54:42.352524422Z
lab2-app:lab18-test1 ID: sha256:4d03939b81234f12681a87fa22bb852d0a59b368e917e132788aa09ab8809501

lab2-app:lab18-test2 Created: 2026-05-14T13:54:42.352524422Z
lab2-app:lab18-test2 ID: sha256:a7a9e5a326f7a1a0fecbf3ec14c3277facfba4c5f59779a1928e56d309e6b6d8
```

The second Docker build reused the cache, so the `Created` timestamp stayed the same. However, the final image IDs and saved image hashes still differed because BuildKit produced different manifest/attestation metadata.

### Nix Docker Image

File: `lab18/app_python/docker.nix`

```nix
{ pkgs ? import <nixpkgs> {} }:

let
  app = import ./default.nix { inherit pkgs; };
in
pkgs.dockerTools.buildLayeredImage {
  name = "devops-info-service-nix";
  tag = "1.0.0";

  contents = [
    app
    pkgs.bashInteractive
    pkgs.coreutils
  ];

  config = {
    Cmd = [ "${app}/bin/devops-info-service" ];
    Env = [
      "HOST=0.0.0.0"
      "PORT=5002"
      "VISITS_FILE=/tmp/devops-info-service-visits"
    ];
    ExposedPorts = {
      "5002/tcp" = {};
    };
  };

  created = "1970-01-01T00:00:01Z";
}
```

Important reproducibility choices:

- The image is built from the Nix-built application derivation.
- The image does not depend on a mutable base image tag such as `python:3.13-slim`.
- `created = "1970-01-01T00:00:01Z"` avoids changing timestamps in the image metadata.
- On this macOS machine, `dockerTools` can build a reproducible tarball from the local Nix closure. A runnable Linux container from macOS requires a Linux builder or extra Nix cross-system configuration.

Build and load:

```bash
cd lab18/app_python
nix-build docker.nix
docker load < result
```

On macOS, the direct `nix-build docker.nix` created a reproducible tarball, but it contained a Darwin closure and failed inside Linux Docker with:

```text
exec /nix/store/qqzlwjiawh40apjrdjiq8sdikzlqyryn-devops-info-service-1.0.0/bin/devops-info-service: exec format error
```

To produce a runnable Linux image, the same `docker.nix` was built inside the official `nixos/nix` Linux container:

```bash
docker run --rm \
  -v /Users/sofiakulagina/devops-labs/DevOps-Core-Course:/work \
  -w /work/lab18/app_python \
  nixos/nix:latest \
  sh -lc 'out=$(nix-build docker.nix --no-out-link) && cp "$out" /work/lab18/app_python/devops-info-service-nix-linux.tar.gz && sha256sum /work/lab18/app_python/devops-info-service-nix-linux.tar.gz'
```

Linux Nix Docker image hash:

```text
410f96fd872d64db6da9e0a49faa6ec56559a9b538346037b3636359c1094b23  devops-info-service-nix-linux.tar.gz
```

Run traditional and Nix images side by side:

```bash
docker stop lab2-container nix-container 2>/dev/null || true
docker rm lab2-container nix-container 2>/dev/null || true

docker run -d -p 5002:5002 --name lab2-container lab2-app:lab18-test1
docker run -d -p 5003:5002 --name nix-container devops-info-service-nix:1.0.0

curl http://localhost:5002/health
curl http://localhost:5003/health
```

### Docker Reproducibility Comparison Commands

Nix image tarball:

```bash
cd lab18/app_python
rm result
nix-build docker.nix
shasum -a 256 result

rm result
nix-build docker.nix
shasum -a 256 result
```

Traditional Dockerfile:

```bash
docker build -t lab2-app:test1 ./app_python
docker save lab2-app:test1 | shasum -a 256

sleep 2

docker build -t lab2-app:test2 ./app_python
docker save lab2-app:test2 | shasum -a 256
```

Result to record after running:

```text
Nix image hash 1: 80c33bc782f0d3afa2f33414923ea9a48b2120c1a6163d06d56c959fcb556367
Nix image hash 2: 80c33bc782f0d3afa2f33414923ea9a48b2120c1a6163d06d56c959fcb556367
Linux Nix image hash: 410f96fd872d64db6da9e0a49faa6ec56559a9b538346037b3636359c1094b23
Dockerfile image hash 1: 4243a74e8bb7478d3631aa5619beaf186cd7fcffc53348d805ed5f1c31eea3ae
Dockerfile image hash 2: f9cf26def74178ff7b0a94deda8b350b255fbd4ead2d41fccd1e9d308ff05a22
```

Expected observation:

- Nix image hashes should be identical.
- Traditional Docker image hashes usually differ because of image metadata, timestamps, mutable base image tags, and build-time package installation.

### Image Size and Layer Analysis

Commands:

```bash
docker images | grep -E "lab2-app|devops-info-service-nix"
docker history lab2-app:lab18-test1
docker history devops-info-service-nix:1.0.0
```

Result to record:

| Metric | Lab 2 Dockerfile | Lab 18 Nix dockerTools |
| --- | --- | --- |
| Image size | 209MB | 451MB |
| Reproducibility | Different hashes expected | Identical hashes expected |
| Build cache | Docker layer cache | Nix content-addressed store |
| Base image | `python:3.13-slim` | No mutable base image |
| Timestamp behavior | Created timestamp changes | Fixed `created` timestamp |

Container verification:

```text
lab2-container-lab18  lab2-app:lab18-test1            Up 4 minutes  0.0.0.0:5002->5002/tcp
nix-container-lab18   devops-info-service-nix:1.0.0   Up 10 seconds 0.0.0.0:5003->5002/tcp
```

Health checks:

```text
Lab 2 Dockerfile container:
{"status":"healthy","timestamp":"2026-05-14T13:57:16.362682+00:00","uptime_seconds":6}

Nix dockerTools container:
{"status":"healthy","timestamp":"2026-05-14T14:02:04.415531+00:00","uptime_seconds":10}
```

Layer observation:

```text
Lab 2 image history shows Dockerfile instructions such as RUN pip install, COPY app.py, USER, EXPOSE, and CMD.
Nix image history shows Nix store paths for exact packages such as python3, flask, werkzeug, jinja2, prometheus-client, glibc, bash, and the app derivation.
```

## Bonus - Modern Nix with Flakes

File: `lab18/app_python/flake.nix`

```nix
{
  description = "DevOps Info Service - reproducible Nix build for Lab 18";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-25.05";
  };

  outputs = { nixpkgs, ... }:
    let
      systems = [
        "aarch64-darwin"
        "x86_64-darwin"
        "x86_64-linux"
        "aarch64-linux"
      ];

      forAllSystems = function:
        nixpkgs.lib.genAttrs systems (system:
          function nixpkgs.legacyPackages.${system}
        );
    in
    {
      packages = forAllSystems (pkgs: {
        default = import ./default.nix { inherit pkgs; };
        dockerImage = import ./docker.nix { inherit pkgs; };
      });

      devShells = forAllSystems (pkgs: {
        default = pkgs.mkShell {
          packages = [
            (pkgs.python313.withPackages (ps: with ps; [
              flask
              prometheus-client
            ]))
          ];
        };
      });
    };
}
```

Generate the lock file:

```bash
cd lab18/app_python
nix flake update
```

Build with flakes:

```bash
nix build
nix build .#dockerImage
nix develop
python --version
python -c "import flask; print(flask.__version__)"
```

`flake.lock` will lock the exact nixpkgs revision, including Python, Flask, `prometheus-client`, build tools, and their transitive dependency closure.

Generated `flake.lock` nixpkgs entry:

```json
{
  "lastModified": 1767313136,
  "narHash": "sha256-16KkgfdYqjaeRGBaYsNrhPRRENs0qzkQVUooNHtoy2w=",
  "owner": "NixOS",
  "repo": "nixpkgs",
  "rev": "ac62194c3917d5f474c1a844b6fd6da2db95077d",
  "type": "github"
}
```

Flake build result:

```text
/nix/store/nmy3p4fplm8w76gkjrx1x95h7c6dn2p9-devops-info-service-1.0.0
```

Dev shell verification:

```text
Python 3.13.5
Flask 3.1.0
```

### Flakes vs Helm Values

| Aspect | Lab 10 Helm values | Lab 18 Nix Flakes |
| --- | --- | --- |
| Locks app image | Usually by tag | Can build content-addressed image |
| Locks Python dependencies | No | Yes |
| Locks build tools | No | Yes |
| Locks OS/userland packages | No | Yes through nixpkgs |
| Cross-machine reproducibility | Depends on image tag stability | Exact nixpkgs revision in `flake.lock` |

Helm is good for declaring how Kubernetes should run an image. Nix is better for proving exactly how that image was built. A strong production approach would combine both: build the image with Nix, publish it by digest, then deploy that digest through Helm.

## Reflection

Nix would have improved Lab 1 by removing hidden assumptions about the local Python version and package resolution. Instead of asking every machine to recreate an environment with `venv` and `pip`, the project would provide one deterministic derivation.

Nix would have improved Lab 2 by replacing mutable base images and timestamped Docker layers with a deterministic image build. The Dockerfile taught container packaging, but `dockerTools` gives stronger evidence that two builds from the same inputs produce the same output.

The biggest tradeoff is complexity. Nix requires learning a new language and workflow, and installation changes the machine by adding `/nix` and the Nix daemon. For CI/CD, security audits, release rollback, and long-lived course artifacts, that complexity is justified because reproducibility becomes measurable instead of assumed.

## Evidence Screenshots

Nix installation and version:

![Nix version](<screenshots/Screenshot 2026-05-14 at 17.07.06.png>)

Nix build output and reproducible `readlink result` values:

![Nix build and store path](<screenshots/Screenshot 2026-05-14 at 17.16.54.png>)

Nix-built application running and `/health` endpoint check:

![Nix app health check](<screenshots/Screenshot 2026-05-14 at 17.17.45.png>)

Nix image hash comparison:

![Nix image hash comparison](<screenshots/Screenshot 2026-05-14 at 17.19.16.png>)

Traditional Docker image hash comparison:

![Docker image hash comparison](<screenshots/Screenshot 2026-05-14 at 17.19.22.png>)

Two containers running side by side:

![Docker containers running](<screenshots/Screenshot 2026-05-14 at 17.21.24.png>)

Health checks for Lab 2 Dockerfile container and Nix dockerTools container:

![Container health checks](<screenshots/Screenshot 2026-05-14 at 17.25.07.png>)

Flake lock and flake build verification:

![Flake lock and build](<screenshots/Screenshot 2026-05-14 at 17.25.25.png>)

Nix develop environment verification:

![Nix develop verification](<screenshots/Screenshot 2026-05-14 at 17.25.46.png>)


