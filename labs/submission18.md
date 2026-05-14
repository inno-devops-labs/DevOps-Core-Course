# Lab 18 Submission: Reproducible Builds with Nix

## Environment

The builds below were validated with the official `nixos/nix:latest` Docker image and a persistent Docker volume mounted at `/nix`.

Nix version used for validation:

```text
nix (Nix) 2.34.7
```

Validation command shape:

```bash
docker volume create lab18-nix-store
docker run --rm \
  -v lab18-nix-store:/nix \
  -v /Users/hikariatama/iu/devops/devops:/workspace \
  -w /workspace/labs/lab18/app_python \
  nixos/nix:latest \
  sh -lc 'nix-build'
```

## Task 1: Reproducible Python App

The Lab 1 Python service was copied into `labs/lab18/app_python`. The copied files are:

```text
app.py
requirements.txt
Dockerfile
config/config.json
default.nix
docker.nix
flake.nix
flake.lock
```

The original `requirements.txt` pins direct dependencies:

```text
Flask==3.1.0
Werkzeug==3.1.3
gunicorn==23.0.0
prometheus-client==0.23.1
```

That is useful, but it does not fully lock the Python interpreter, build tools, operating system libraries, or every transitive package source. Nix locks the full build input graph through the selected nixpkgs revision and Nix store paths.

### `default.nix`

```nix
{ pkgs ? import <nixpkgs> {} }:

pkgs.python3Packages.buildPythonApplication {
  pname = "devops-info-service";
  version = "1.0.0";
  src = ./.;
  format = "other";

  propagatedBuildInputs = with pkgs.python3Packages; [
    flask
    gunicorn
    prometheus-client
    werkzeug
  ];

  nativeBuildInputs = [
    pkgs.makeWrapper
  ];

  installPhase = ''
    runHook preInstall

    mkdir -p $out/bin $out/share/devops-info-service
    cp app.py $out/share/devops-info-service/app.py
    cp -r config $out/share/devops-info-service/config

    makeWrapper ${pkgs.python3.interpreter} $out/bin/devops-info-service \
      --add-flags "$out/share/devops-info-service/app.py" \
      --prefix PYTHONPATH : "$PYTHONPATH" \
      --set APP_CONFIG_PATH "$out/share/devops-info-service/config/config.json" \
      --set-default VISITS_FILE_PATH "/tmp/devops-info-service-visits"

    runHook postInstall
  '';
}
```

Field explanations:

| Field | Purpose |
| --- | --- |
| `pname` and `version` | Define the package identity in the Nix store path. |
| `src = ./.` | Uses the lab app directory as the source input. |
| `format = "other"` | Builds an application without `setup.py` or `pyproject.toml`. |
| `propagatedBuildInputs` | Adds Flask, Gunicorn, Werkzeug, and Prometheus client to the Python environment. |
| `nativeBuildInputs` | Adds `makeWrapper` so the final command can run through the pinned Python interpreter. |
| `installPhase` | Copies the app into `$out` and creates the executable wrapper. |

### Build Output

Repeated `nix-build` calls produced identical store paths and output hashes:

```text
path1=/nix/store/7xd6w032kzkj5na90y8269k3qs4060qy-devops-info-service-1.0.0
path2=/nix/store/7xd6w032kzkj5na90y8269k3qs4060qy-devops-info-service-1.0.0
hash1=d42db926310a3c9087305db9fe6a46c3195db699a2d2ebec74306b15a8dd5bf4
hash2=d42db926310a3c9087305db9fe6a46c3195db699a2d2ebec74306b15a8dd5bf4
```

The app starts from the Nix-built wrapper:

```text
/nix/store/7xd6w032kzkj5na90y8269k3qs4060qy-devops-info-service-1.0.0
{"timestamp": "2026-05-07T18:58:56.185537+00:00", "level": "INFO", "logger": "devops-info-service", "message": "runtime_initialized", "config_path": "/nix/store/7xd6w032kzkj5na90y8269k3qs4060qy-devops-info-service-1.0.0/share/devops-info-service/config/config.json", "environment": "local", "visits_file_path": "/tmp/devops-info-service-visits", "visits_count": 0}
{"timestamp": "2026-05-07T18:58:56.185604+00:00", "level": "INFO", "logger": "devops-info-service", "message": "application_starting", "service": "devops-info-service", "version": "1.0.0", "host": "0.0.0.0", "port": 5000, "debug": false}
```

### Lab 1 Compared With Nix

| Aspect | Lab 1: pip and venv | Lab 18: Nix |
| --- | --- | --- |
| Python version | Depends on local interpreter or base image | Comes from nixpkgs |
| Direct dependencies | Pinned in `requirements.txt` | Selected from pinned nixpkgs |
| Transitive dependencies | Resolved by pip at install time | Locked by nixpkgs closure |
| Build tools | Local system dependent | Nix store paths |
| Output identity | No content-addressed output path | Store path includes input hash |
| Rebuild result | Approximate repeatability | Same path and same hash |

`requirements.txt` is weaker because it mainly describes Python packages. It does not describe the complete machine state needed to build and run the program. Nix includes the interpreter, native libraries, wrappers, build hooks, and package graph in the derivation inputs.

If Nix had been used in Lab 1, every student and CI runner would have used the same Python environment instead of depending on the local Python installation, virtualenv state, and pip resolution at that moment.

## Task 2: Reproducible Docker Images

### Traditional Lab 2 Dockerfile

The original Dockerfile uses a mutable base tag and installs packages at image build time:

```dockerfile
FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

RUN groupadd --system app \
    && useradd --system --gid app --home /app --shell /usr/sbin/nologin app \
    && mkdir -p /data /config \
    && chown -R app:app /app /data /config

COPY --chown=app:app requirements.txt ./
RUN python -m pip install --no-cache-dir -r requirements.txt

COPY --chown=app:app app.py ./

USER app

EXPOSE 5000

CMD ["python", "app.py"]
```

### `docker.nix`

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
    pkgs.bash
    pkgs.coreutils
  ];
  config = {
    Cmd = [ "${app}/bin/devops-info-service" ];
    Env = [
      "HOST=0.0.0.0"
      "PORT=5000"
      "VISITS_FILE_PATH=/tmp/devops-info-service-visits"
    ];
    ExposedPorts = {
      "5000/tcp" = {};
    };
  };
  created = "1970-01-01T00:00:01Z";
}
```

Field explanations:

| Field | Purpose |
| --- | --- |
| `app` | Reuses the exact derivation from Task 1. |
| `buildLayeredImage` | Creates a Docker image from Nix store paths. |
| `contents` | Places the app and required runtime tools into the image closure. |
| `config.Cmd` | Runs the Nix-built service wrapper. |
| `config.Env` | Sets the host, port, and writable visits file path. |
| `created` | Uses a fixed timestamp to avoid timestamp-based image drift. |

### Nix Docker Reproducibility

Repeated Docker image builds with Nix produced the same tarball path and SHA256:

```text
docker_path1=/nix/store/9d8b2nxza22q28hb94pca78rxzq26r8b-devops-info-service-nix.tar.gz
docker_path2=/nix/store/9d8b2nxza22q28hb94pca78rxzq26r8b-devops-info-service-nix.tar.gz
docker_hash1=c8cc7bf3b33508f84c1875b54978af6dd90d51541083c0b9bdeeaa101a14fdb9
docker_hash2=c8cc7bf3b33508f84c1875b54978af6dd90d51541083c0b9bdeeaa101a14fdb9
```

The image loaded successfully:

```text
Loaded image: devops-info-service-nix:1.0.0
```

### Traditional Docker Rebuild Comparison

Two uncached Dockerfile builds had different creation timestamps and different saved image hashes:

```text
lab2-app:nocache1 Created: 2026-05-07T22:02:28.009939197+03:00
lab2-app:nocache2 Created: 2026-05-07T22:02:37.708635601+03:00
```

```text
583e01d1bd3d44b19ecb752efae440e097e13a3f87d9c58dd989567189c0e52a  -
3ba260c92aebb03561b74e3cda1c3bdf836ea41a59ab7320e8f829cd364dc2ab  -
```

The traditional Docker build also resolved Python transitive dependencies at build time:

```text
Successfully installed Flask-3.1.0 Jinja2-3.1.6 MarkupSafe-3.0.3 Werkzeug-3.1.3 blinker-1.9.0 click-8.3.3 gunicorn-23.0.0 itsdangerous-2.2.0 packaging-26.2 prometheus-client-0.23.1
```

The direct packages were pinned, but `Jinja2`, `MarkupSafe`, `blinker`, `click`, `itsdangerous`, and `packaging` were still resolved by pip during the image build.

### Running Both Containers

The traditional Docker image and Nix-built image both passed `/health`:

```text
lab2-container: http://localhost:15000/health
{"status":"healthy","timestamp":"2026-05-07T19:06:15.244304+00:00","uptime_seconds":1}

nix-container: http://localhost:15002/health
{"status":"healthy","timestamp":"2026-05-07T19:06:15.259901+00:00","uptime_seconds":1}
```

Container status:

```text
nix-container Up 2 seconds 0.0.0.0:15002->5000/tcp, [::]:15002->5000/tcp
lab2-container Up 2 seconds 0.0.0.0:15000->5000/tcp, [::]:15000->5000/tcp
```

### Image Size

| Image | Size |
| --- | ---: |
| `lab2-app:nocache1` | 150MB |
| `lab2-app:nocache2` | 150MB |
| `devops-info-service-nix:1.0.0` | 218MB |

The Nix image is larger in this run because the wrapper needs a Nix runtime closure that includes Bash, Coreutils, Python, and store-path runtime dependencies. The important reproducibility result is still achieved: the Nix image tarball is bit-for-bit identical across repeated builds.

### Layer History

Traditional Dockerfile layers include build-time Dockerfile steps with recent timestamps:

```text
IMAGE      CREATED          CREATED BY                                                        SIZE
81bcd77    40 seconds ago   CMD ["python" "app.py"]                                           0B
<missing>  40 seconds ago   EXPOSE [5000/tcp]                                                 0B
<missing>  41 seconds ago   RUN /bin/sh -c python -m pip install --no-cache-dir -r requirements.txt  6.68MB
```

Nix image layers are store-path based:

```text
IMAGE      CREATED  CREATED BY  SIZE    COMMENT
d13d20c    N/A                  9.32kB  store paths: ['/nix/store/691ajlns8wxjj2v4h1y2dcaiw181ri4k-devops-info-service-nix-customisation-layer']
<missing>  N/A                  27.2kB  store paths: ['/nix/store/7xd6w032kzkj5na90y8269k3qs4060qy-devops-info-service-1.0.0']
<missing>  N/A                  1.08MB  store paths: ['/nix/store/kxiak4j8k1hz1xqs2fn932mzan0768lb-python3.13-flask-3.1.2']
```

Traditional Dockerfiles struggle to achieve bit-for-bit reproducibility because image metadata, timestamps, mutable tags, package manager resolution, and build host details can enter the output. Nix avoids this by deriving output paths from declared inputs and by using deterministic image metadata.

Practical scenarios where this matters:

| Scenario | Why Nix helps |
| --- | --- |
| CI/CD | Rebuilds can be compared by hash before promotion. |
| Security audits | The complete dependency closure can be inspected. |
| Rollbacks | Store paths and image tarballs identify exact artifacts. |
| Incident response | A production image can be rebuilt and compared to the deployed artifact. |

If I redid Lab 2 with Nix, I would still keep the Dockerfile as a teaching artifact, but use `dockerTools` for release images where reproducibility and auditability matter.

## Bonus Task: Modern Nix With Flakes

### `flake.nix`

```nix
{
  description = "DevOps Info Service reproducible builds";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-24.11";
  };

  outputs = { nixpkgs, ... }:
    let
      systems = [
        "x86_64-linux"
        "aarch64-linux"
        "x86_64-darwin"
        "aarch64-darwin"
      ];
      forAllSystems = f:
        nixpkgs.lib.genAttrs systems (system:
          f nixpkgs.legacyPackages.${system});
    in
    {
      packages = forAllSystems (pkgs: {
        default = import ./default.nix { inherit pkgs; };
        dockerImage = import ./docker.nix { inherit pkgs; };
      });

      devShells = forAllSystems (pkgs: {
        default = pkgs.mkShell {
          buildInputs = [
            pkgs.python3
            pkgs.python3Packages.flask
            pkgs.python3Packages.gunicorn
            pkgs.python3Packages.prometheus-client
            pkgs.python3Packages.werkzeug
          ];
        };
      });
    };
}
```

The flake exports:

| Output | Purpose |
| --- | --- |
| `packages.<system>.default` | Builds the Python application derivation. |
| `packages.<system>.dockerImage` | Builds the reproducible Docker image tarball. |
| `devShells.<system>.default` | Provides the same Python toolchain and dependencies for development. |

### `flake.lock`

The lock file pins nixpkgs to a specific revision:

```json
{
  "lastModified": 1751274312,
  "narHash": "sha256-/bVBlRpECLVzjV19t5KMdMFWSwKLtb5RyXdjz3LJT+g=",
  "owner": "NixOS",
  "repo": "nixpkgs",
  "rev": "50ab793786d9de88ee30ec4e4c24fb4236fc2674",
  "type": "github"
}
```

Flake validation from a non-Git temporary copy passed:

```text
all checks passed!
flake_default=/nix/store/2pbglg0ywxxhdghvwcky85bp8wrng0m9-devops-info-service-1.0.0
flake_docker=/nix/store/yr4n2cykgb9v8g0gm55iik88ydk6fwsi-devops-info-service-nix.tar.gz
```

The temporary copy was used because Nix flakes ignore untracked files inside a Git repository. No files were staged, committed, or pushed.

### Flakes Compared With Lab 10 Helm Pinning

| Aspect | Lab 1: venv and requirements | Lab 10: Helm values | Lab 18: Nix Flakes |
| --- | --- | --- | --- |
| Python version | Uses local or image Python | Hidden inside image | Locked through nixpkgs |
| Python dependencies | Direct pins, transitive resolution still happens | Hidden inside image | Locked in Nix closure |
| Build tools | Host dependent | Image build dependent | Locked through nixpkgs |
| Deployment config | Not covered | Good Kubernetes config model | Build and dev environment model |
| Image identity | Not covered | Tags can move unless digest-pinned | Image tarball hash is deterministic |
| Cross-machine behavior | Varies by interpreter and pip state | Varies by image contents | Same lock file gives same inputs |

Helm and Nix solve different problems. Helm is useful for declaring Kubernetes deployment configuration. Nix is stronger for building the artifact that Helm deploys. A good production workflow can combine both: build the image with Nix, publish it by digest, then reference the digest from Helm values.

## Challenges

The main challenge was host Nix installation. The lab recommends installing Nix directly, but that requires admin-level system changes. I opted to use `nixos/nix:latest` with a persistent Docker volume instead. The Nix expressions, store paths, image builds, flake lock, and container runtime behavior were still validated.

Another observation is that Nix image size is not automatically smaller. Reproducibility and minimality are separate goals. This image can be optimized further by reducing shell and utility dependencies, but the current version prioritizes a reliable wrapper and successful runtime behavior.
