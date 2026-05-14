# Lab 18 — Reproducible Builds with Nix

## Task 1 — Build Reproducible Python App

### 1.1 Nix Installation

Nix was installed using the Determinate Systems installer.

Verification commands:

```bash
nix --version
nix run nixpkgs#hello
```

Output:

```text
nix (Determinate Nix 3.20.0) 2.34.6
Hello, world!
```

This confirms that Nix was installed successfully and can run packages from `nixpkgs`.

---

### 1.2 Application Preparation

The Lab 1 Python application was copied to:

```text
labs/lab18/app_python
```

Files copied from the original Lab 1/Lab 2 application:

```text
app.py
requirements.txt
Dockerfile
```

The application is a FastAPI-based DevOps Info Service with the following main dependencies:

```text
fastapi>=0.115.6
uvicorn[standard]==0.32.0
prometheus-client==0.23.1
```

---

### 1.3 Nix Derivation

The Nix derivation was created in:

```text
labs/lab18/app_python/default.nix
```

The derivation builds the FastAPI application and creates a wrapped executable called:

```text
devops-info-service
```

The wrapper starts the application with `uvicorn`.

```nix
{ pkgs ? import <nixpkgs> {} }:

let
  python = pkgs.python313;
  pythonPackages = pkgs.python313Packages;

  pythonPath = pythonPackages.makePythonPath [
    pythonPackages.fastapi
    pythonPackages.uvicorn
    pythonPackages.prometheus-client
  ];
in
pkgs.stdenv.mkDerivation {
  pname = "devops-info-service";
  version = "1.0.0";

  src = ./.;

  nativeBuildInputs = [
    pkgs.makeWrapper
  ];

  installPhase = ''
    mkdir -p $out/lib/devops-info-service
    mkdir -p $out/bin

    cp app.py $out/lib/devops-info-service/app.py

    makeWrapper ${pythonPackages.uvicorn}/bin/uvicorn $out/bin/devops-info-service \
      --add-flags "app:app --host 0.0.0.0 --port 5001 --no-access-log" \
      --set PYTHONPATH "$out/lib/devops-info-service:${pythonPath}" \
      --set DATA_DIR "/tmp/devops-info-service-data" \
      --set CONFIG_PATH "/tmp/devops-info-service-config/config.json" \
      --set APP_ENV "nix" \
      --set LOG_LEVEL "info" \
      --set RELEASE_VERSION "1.0.0"
  '';

  meta = {
    description = "DevOps Info Service built reproducibly with Nix";
    mainProgram = "devops-info-service";
  };
}
```

Field explanation:

| Field               | Meaning                                                                       |
| ------------------- | ----------------------------------------------------------------------------- |
| `pname`             | Package name in the Nix derivation                                            |
| `version`           | Application version                                                           |
| `src = ./.`         | Use the current directory as the source                                       |
| `nativeBuildInputs` | Build-time tools, here `makeWrapper`                                          |
| `pythonPath`        | Python dependency path containing FastAPI, Uvicorn, and Prometheus client     |
| `installPhase`      | Custom installation commands                                                  |
| `makeWrapper`       | Creates an executable script that starts Uvicorn with the correct environment |
| `DATA_DIR`          | Runtime data directory for the visits counter                                 |
| `CONFIG_PATH`       | Runtime config path                                                           |
| `APP_ENV`           | Application environment marker                                                |
| `RELEASE_VERSION`   | Application version exposed at runtime                                        |

The application was run on port `5001` because port `5000` was already used on the macOS machine.

---

### 1.4 Build Output

Command:

```bash
nix-build
```

Output:

```text
/nix/store/dj4mpz4p29ndg8yn00x5n3nf7qgw7flb-devops-info-service-1.0.0
```

Store path check:

```bash
readlink result
```

Output:

```text
/nix/store/dj4mpz4p29ndg8yn00x5n3nf7qgw7flb-devops-info-service-1.0.0
```

This path has the format:

```text
/nix/store/<hash>-<name>-<version>
```

In this build:

| Part         | Value                              |
| ------------ | ---------------------------------- |
| Store root   | `/nix/store`                       |
| Hash         | `dj4mpz4p29ndg8yn00x5n3nf7qgw7flb` |
| Package name | `devops-info-service`              |
| Version      | `1.0.0`                            |

The hash is derived from the build inputs, dependencies, and build instructions.

---

### 1.5 Running the Nix-built Application

Command:

```bash
./result/bin/devops-info-service
```

Output:

```text
INFO:     Started server process [89110]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:5001 (Press CTRL+C to quit)
```

Health check:

```bash
curl -s http://localhost:5001/health | python3 -m json.tool
```

Output:

```json
{
    "status": "healthy",
    "timestamp": "2026-05-14T16:36:09.198765+00:00",
    "uptime_seconds": 498
}
```

Visits endpoint:

```bash
curl -s http://localhost:5001/visits | python3 -m json.tool
```

Output:

```json
{
    "visits": 0,
    "file": "/tmp/devops-info-service-data/visits"
}
```

This confirms that the Nix-built version of the Lab 1 application works correctly.

Screenshot of the Nix-built application running locally:

![Nix-built application running](lab18/screenshots/nix-built-app-running.png)

---

### 1.6 Reproducibility Check

First, the current store path was recorded:

```bash
FIRST_PATH=$(readlink result)
echo "First build path: $FIRST_PATH"
```

Output:

```text
First build path: /nix/store/dj4mpz4p29ndg8yn00x5n3nf7qgw7flb-devops-info-service-1.0.0
```

Then the `result` symlink was removed and the app was built again:

```bash
rm result
nix-build

SECOND_PATH=$(readlink result)
echo "Second build path: $SECOND_PATH"
```

Output:

```text
/nix/store/dj4mpz4p29ndg8yn00x5n3nf7qgw7flb-devops-info-service-1.0.0
Second build path: /nix/store/dj4mpz4p29ndg8yn00x5n3nf7qgw7flb-devops-info-service-1.0.0
```

Both paths are identical.

To prove that Nix can reproduce the output after deletion, the store path was deleted and rebuilt:

```bash
STORE_PATH=$(readlink result)
echo "Original store path: $STORE_PATH"

rm result
nix-store --delete "$STORE_PATH"

nix-build

REBUILT_PATH=$(readlink result)
echo "Rebuilt store path: $REBUILT_PATH"
```

Output:

```text
Original store path: /nix/store/dj4mpz4p29ndg8yn00x5n3nf7qgw7flb-devops-info-service-1.0.0
deleting '/nix/store/dj4mpz4p29ndg8yn00x5n3nf7qgw7flb-devops-info-service-1.0.0'
1 store paths deleted, 13.6 KiB freed
/nix/store/dj4mpz4p29ndg8yn00x5n3nf7qgw7flb-devops-info-service-1.0.0
Rebuilt store path: /nix/store/dj4mpz4p29ndg8yn00x5n3nf7qgw7flb-devops-info-service-1.0.0
```

The store path after forced rebuild is identical to the original one.

Output hash:

```bash
nix-hash --type sha256 result
```

Output:

```text
239fe04a9187e8e2697fc55466be15b5cdae5388a947eec191ed89e9993b9f51
```

This confirms that the Nix build is reproducible for the same source code, Nix package set, dependencies, and build instructions.

---

### 1.7 Traditional pip Environment Comparison

To compare the Nix approach with the traditional Lab 1 workflow, a Python virtual environment was created and dependencies were installed with `pip`.

Commands:

```bash
python3 -m venv pip-venv
source pip-venv/bin/activate

pip install -r requirements.txt
pip freeze | sort > pip-freeze.txt

cat requirements.txt
cat pip-freeze.txt

wc -l requirements.txt pip-freeze.txt

deactivate
```

The original `requirements.txt` contains only direct dependency declarations:

```text
fastapi>=0.115.6
uvicorn[standard]==0.32.0
prometheus-client==0.23.1
```

However, `pip freeze` produced the full resolved environment:

```text
PyYAML==6.0.3
annotated-doc==0.0.4
annotated-types==0.7.0
anyio==4.13.0
click==8.3.3
fastapi==0.136.1
h11==0.16.0
httptools==0.7.1
idna==3.15
prometheus_client==0.23.1
pydantic==2.13.4
pydantic_core==2.46.4
python-dotenv==1.2.2
starlette==1.0.0
typing-inspection==0.4.2
typing_extensions==4.15.0
uvicorn==0.32.0
uvloop==0.22.1
watchfiles==1.1.1
websockets==16.0
```

This demonstrates that the traditional `requirements.txt` file only describes the direct dependencies of the application. The actual Python environment contains many transitive dependencies.

For example, `fastapi>=0.115.6` allowed pip to install:

```text
fastapi==0.136.1
```

This means that the exact installed version can change over time if the package index changes and the dependency is not fully pinned.

Nix provides stronger reproducibility guarantees because the Python interpreter, direct dependencies, transitive dependencies, and build instructions are all part of the Nix derivation and its dependency closure.

| Aspect                  | Lab 1 pip + venv                         | Lab 18 Nix                              |
| ----------------------- | ---------------------------------------- | --------------------------------------- |
| Direct dependencies     | Listed in `requirements.txt`             | Declared in `default.nix`               |
| Transitive dependencies | Resolved by pip during install           | Included in the Nix dependency closure  |
| Python version          | Depends on local system                  | Provided by Nix                         |
| Output identity         | No content-addressed output              | Store path in `/nix/store`              |
| Rebuild result          | Can change if package resolution changes | Same inputs produce the same store path |
| Binary cache            | No built-in binary cache                 | Nix can reuse cached store paths        |

---

### 1.8 Reflection

If Nix had been used from the start of Lab 1, the application would have had a reproducible Python runtime, reproducible dependencies, and a consistent startup command. This would reduce "works on my machine" problems because every developer and CI environment could build the same derivation and get the same store path.

---



## Task 2 — Reproducible Docker Images

### 2.1 Lab 2 Dockerfile Review

The original Lab 2 Dockerfile was located at:

```text
app_python/Dockerfile
```

Dockerfile:

```dockerfile
FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DATA_DIR=/data \
    CONFIG_PATH=/config/config.json

RUN useradd -m -u 10001 appuser

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app.py .

RUN mkdir -p /data /config \
    && chown -R appuser:appuser /app /data /config

USER appuser

EXPOSE 5000

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "5000", "--no-access-log"]
```

This Dockerfile follows common containerization practices: it uses a Python base image, installs dependencies with `pip`, creates a non-root user, exposes port `5000`, and starts the application with `uvicorn`.

However, it is not fully reproducible because it depends on a mutable base image tag, runtime package installation, `apt-get update`, and build timestamps.

---

### 2.2 Traditional Dockerfile Reproducibility Test

The Lab 2 Docker image was built twice with the same Dockerfile and source code.

Commands:

```bash
docker build --no-cache -t lab2-app:v1 ./app_python
docker inspect -f 'Created={{.Created}} ID={{.Id}}' lab2-app:v1

sleep 5

docker build --no-cache -t lab2-app:v2 ./app_python
docker inspect -f 'Created={{.Created}} ID={{.Id}}' lab2-app:v2
```

Output:

```text
Created=2026-05-14T17:13:15.58579275Z ID=sha256:626c75275bf8499d2fdbb97f74f7a345daf461005491b01c238330233ef26b74

Created=2026-05-14T17:13:54.694386546Z ID=sha256:134244af6e376114c036cfa4995e170a53cdb9c05aeac45b71d2683c27fe8cf6
```

The creation timestamps and image IDs are different.

The saved image hashes were also different:

```bash
docker save lab2-app:v1 | shasum -a 256
docker save lab2-app:v2 | shasum -a 256
```

Output:

```text
76b48ffb1336a6f30d430830eecfbc515e633509c278009dbf7f1fcaeccc05b9  -
73b310959e4f2299c618c0710d5cfaa5b1003e3b375adea89774a2434e9fb4ac  -
```

This confirms that the traditional Dockerfile build was not bit-for-bit reproducible.

---

### 2.3 Nix Docker Image with dockerTools

The Nix Docker image was defined in:

```text
labs/lab18/app_python/docker.nix
```

```nix
{ pkgs ? import <nixpkgs> {} }:

let
  app = import ./default.nix { inherit pkgs; };

  pythonPackages = pkgs.python313Packages;

  pythonPath = pythonPackages.makePythonPath [
    pythonPackages.fastapi
    pythonPackages.uvicorn
    pythonPackages.prometheus-client
  ];
in
pkgs.dockerTools.buildLayeredImage {
  name = "devops-info-service-nix";
  tag = "1.0.0";

  contents = [
    app
    pythonPackages.uvicorn
    pythonPackages.fastapi
    pythonPackages.prometheus-client
    pkgs.bash
    pkgs.coreutils
  ];

  config = {
    Cmd = [
      "${pythonPackages.uvicorn}/bin/uvicorn"
      "app:app"
      "--host"
      "0.0.0.0"
      "--port"
      "5000"
      "--no-access-log"
    ];

    ExposedPorts = {
      "5000/tcp" = {};
    };

    Env = [
      "PYTHONPATH=${app}/lib/devops-info-service:${pythonPath}"
      "DATA_DIR=/tmp/devops-info-service-data"
      "CONFIG_PATH=/tmp/devops-info-service-config/config.json"
      "APP_ENV=nix-docker"
      "LOG_LEVEL=info"
      "RELEASE_VERSION=1.0.0"
    ];

    WorkingDir = "/";
  };

  created = "1970-01-01T00:00:01Z";
}
```

Field explanation:

| Field               | Meaning                                                            |
| ------------------- | ------------------------------------------------------------------ |
| `app`               | Imports the reproducible application derivation from `default.nix` |
| `pythonPackages`    | Provides Python packages from Nix                                  |
| `pythonPath`        | Builds a deterministic Python module path                          |
| `buildLayeredImage` | Creates a Docker image using Nix `dockerTools`                     |
| `name`              | Docker image repository name                                       |
| `tag`               | Docker image tag                                                   |
| `contents`          | Nix store paths included in the image                              |
| `config.Cmd`        | Default command executed when the container starts                 |
| `ExposedPorts`      | Documents port `5000/tcp` as exposed                               |
| `Env`               | Runtime environment variables for the application                  |
| `created`           | Fixed image creation timestamp for reproducibility                 |

The fixed `created` value is important because using the current time would make every image build different.

---

### 2.4 Nix Docker Image Reproducibility Test

First, the image was built directly on macOS. The resulting image had a deterministic hash, but it could not run in Docker because it contained Darwin binaries. The runtime error was:

```text
exec /nix/store/.../bin/uvicorn: exec format error
```

Because Docker containers require Linux executables, the image was rebuilt inside a Linux Nix container:

```bash
docker run --rm -it \
  -v "$PWD":/workspace \
  -w /workspace/labs/lab18/app_python \
  nixos/nix:latest \
  bash
```

Inside the Linux Nix container:

```bash
nix --version

nix-build docker.nix -o result-linux-image-1
sha256sum result-linux-image-1

rm result-linux-image-1

nix-build docker.nix -o result-linux-image-2
sha256sum result-linux-image-2
```

Output:

```text
nix (Nix) 2.34.7

67077f07680e6973e90432977c3bc13c525cbb850f136dc2b03b146bae7c16b1  result-linux-image-1
67077f07680e6973e90432977c3bc13c525cbb850f136dc2b03b146bae7c16b1  result-linux-image-2
```

The SHA256 hashes are identical, so the Nix-built Docker image is reproducible.

The final image tarball was copied back to the host and loaded into Docker:

```bash
docker load < devops-info-service-nix-linux.tar.gz
```

Output:

```text
Loaded image: devops-info-service-nix:1.0.0
```

---

### 2.5 Running Traditional and Nix Containers Side-by-Side

Both containers were started simultaneously:

```bash
docker stop lab2-container nix-container 2>/dev/null || true
docker rm lab2-container nix-container 2>/dev/null || true

docker run -d -p 5002:5000 --name lab2-container lab2-app:v1
docker run -d -p 5003:5000 --name nix-container devops-info-service-nix:1.0.0
```

Container status:

```bash
docker ps --filter "name=lab2-container" --filter "name=nix-container"
```

Output:

```text
CONTAINER ID   IMAGE                           COMMAND                  STATUS         PORTS                    NAMES
8887d84c03bc   devops-info-service-nix:1.0.0   "/nix/store/hzrz7530…"   Up 4 seconds   0.0.0.0:5003->5000/tcp   nix-container
a0ae069c497d   lab2-app:v1                     "uvicorn app:app --h…"   Up 4 seconds   0.0.0.0:5002->5000/tcp   lab2-container
```

Health checks:

```bash
curl -s http://localhost:5002/health | python3 -m json.tool
curl -s http://localhost:5003/health | python3 -m json.tool
```

Output:

```json
{
    "status": "healthy",
    "timestamp": "2026-05-14T17:23:00.204988+00:00",
    "uptime_seconds": 6
}
```

```json
{
    "status": "healthy",
    "timestamp": "2026-05-14T17:23:00.267211+00:00",
    "uptime_seconds": 7
}
```

Both containers run the same application successfully.

Screenshot showing both containers running side-by-side:

![Both Docker containers running](lab18/screenshots/docker-containers-running.png)

---

### 2.6 Image Size Comparison

Command:

```bash
docker images --format 'table {{.Repository}}\t{{.Tag}}\t{{.Size}}\t{{.ID}}' | grep -E "lab2-app|devops-info-service-nix"
```

Output:

```text
lab2-app                            v2              275MB     134244af6e37
lab2-app                            v1              275MB     626c75275bf8
devops-info-service-nix             1.0.0           476MB     e98722270a20
```

| Metric             | Lab 2 Dockerfile                | Lab 18 Nix dockerTools                  |
| ------------------ | ------------------------------- | --------------------------------------- |
| Image size         | `275MB`                         | `476MB`                                 |
| Reproducibility    | Different hashes between builds | Identical hashes between builds         |
| Build caching      | Docker layer cache              | Nix content-addressed store             |
| Base image         | `python:3.13-slim`              | No Docker base image; Nix store closure |
| Timestamp behavior | Build timestamps vary           | Fixed timestamp                         |
| Runtime test       | `/health` works                 | `/health` works                         |

The Nix image was larger in this implementation because it included the full Nix closure required by Python, Uvicorn, FastAPI, Prometheus client, Bash, and Coreutils. The goal of this task was reproducibility, not minimal image size. A more optimized Nix expression could reduce the image size by minimizing `contents`.

---

### 2.7 Docker History Comparison

Traditional Dockerfile image history:

```bash
docker history lab2-app:v1 | head -20
```

Output:

```text
IMAGE          CREATED          CREATED BY                                      SIZE      COMMENT
626c75275bf8   9 minutes ago    CMD ["uvicorn" "app:app" "--host" "0.0.0.0" …   0B        buildkit.dockerfile.v0
<missing>      9 minutes ago    EXPOSE map[5000/tcp:{}]                         0B        buildkit.dockerfile.v0
<missing>      9 minutes ago    USER appuser                                    0B        buildkit.dockerfile.v0
<missing>      9 minutes ago    RUN /bin/sh -c mkdir -p /data /config     &&…   32.8kB    buildkit.dockerfile.v0
<missing>      9 minutes ago    COPY app.py . # buildkit                        20.5kB     buildkit.dockerfile.v0
<missing>      9 minutes ago    RUN /bin/sh -c pip install --no-cache-dir -r…   42.3MB    buildkit.dockerfile.v0
<missing>      10 minutes ago   COPY requirements.txt . # buildkit              12.3kB     buildkit.dockerfile.v0
<missing>      10 minutes ago   RUN /bin/sh -c apt-get update     && apt-get…   14.5MB    buildkit.dockerfile.v0
<missing>      10 minutes ago   WORKDIR /app                                    8.19kB    buildkit.dockerfile.v0
<missing>      10 minutes ago   RUN /bin/sh -c useradd -m -u 10001 appuser #…   69.6kB    buildkit.dockerfile.v0
<missing>      10 minutes ago   ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFER…   0B        buildkit.dockerfile.v0
```

The traditional Dockerfile history shows build-time layers with relative creation times such as `9 minutes ago` and `10 minutes ago`.

Nix dockerTools image history:

```bash
docker history devops-info-service-nix:1.0.0 | head -20
```

Output:

```text
IMAGE          CREATED   CREATED BY   SIZE      COMMENT
e98722270a20   N/A                    2.35MB    store paths: ['/nix/store/blk7pmqw9vjp1dqhr4whfabxzwn3q8yk-devops-info-service-nix-customisation-layer']
<missing>      N/A                    45.1kB    store paths: ['/nix/store/ivsnpbddxj6a9nsh1y5m85q102b53gx8-devops-info-service-1.0.0']
<missing>      N/A                    2.06MB    store paths: ['/nix/store/3s53aywfl0dr45462ck13xi3a9pcp836-python3.13-fastapi-0.116.1']
<missing>      N/A                    6.24MB    store paths: ['/nix/store/5pw9qxdf5p3a6mfxfmn72i8yibbk40cx-python3.13-pydantic-2.11.7']
<missing>      N/A                    5.07MB    store paths: ['/nix/store/3gzx32bqnidawxx7pisvig4lwd10j0wh-python3.13-pydantic-core-2.33.2']
<missing>      N/A                    1.23MB    store paths: ['/nix/store/ldis6a9vpmbpswg6bmxrhgwm4dz4pzgf-python3.13-starlette-0.47.2']
<missing>      N/A                    2.05MB    store paths: ['/nix/store/gkfrf6jd44cw7ah3kw2f7dyyvjvfnga9-python3.13-anyio-4.11.0']
<missing>      N/A                    1.23MB    store paths: ['/nix/store/hzrz7530swz537prxl9r3r3hk8qnvbxg-python3.13-uvicorn-0.35.0']
<missing>      N/A                    1.38MB    store paths: ['/nix/store/mv1xhqpfbwimj5v4gfhs1aa79n1dkz7x-python3.13-click-8.2.1']
<missing>      N/A                    1.06MB    store paths: ['/nix/store/x90cc5wyf0l5nnqfkdbb9andwdjisg55-python3.13-idna-3.11']
```

The Nix image history is based on Nix store paths. Each layer corresponds to immutable Nix store content. This makes the image easier to inspect and more deterministic.

---

### 2.8 Analysis

Traditional Dockerfiles cannot easily achieve bit-for-bit reproducibility because several inputs can change between builds:

* base image tags such as `python:3.13-slim` can point to different image digests over time;
* `apt-get update` downloads the current state of package repositories;
* `pip install` resolves Python packages at build time;
* Docker image metadata includes timestamps;
* repeated builds can produce different image IDs and saved image hashes.

Nix `dockerTools` improves this by building the application from Nix store paths. The dependencies are represented as immutable store paths, and the image timestamp was fixed with:

```nix
created = "1970-01-01T00:00:01Z";
```

As a result, rebuilding the Nix image produced identical SHA256 hashes.

---

### 2.9 Reflection

If I could redo Lab 2 with Nix, I would keep the useful Docker concepts from Lab 2, such as exposing the correct port and running the application in an isolated container, but I would build the application and image contents from Nix derivations instead of installing dependencies during the Docker build.

This would make the image more reproducible and easier to audit. It would also make rollbacks safer because the exact build inputs would be represented by Nix store paths.

Practical scenarios where Nix reproducibility matters:

* CI/CD pipelines, where every runner must build the same artifact;
* security audits, where exact dependency versions must be known;
* production rollbacks, where an old version must be rebuilt exactly;
* team development, where different machines should not produce different builds;
* long-term maintenance, where package repositories and base image tags may change over time.


