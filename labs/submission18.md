# Lab 18 Submission - Reproducible Builds with Nix

Platform: Ubuntu Linux x86_64
Branch used locally: `lab18`
Application: Lab 1 Flask DevOps Info Service copied to `labs/lab18/app_python`

## Task 1 - Reproducible Python App

### Nix Installation

Nix was installed with the Determinate Nix installer. In this terminal session the binary was available through the profile path:

```text
$ /nix/var/nix/profiles/default/bin/nix --version
nix (Determinate Nix 3.20.0) 2.34.6
```

Basic Nix smoke test:

```text
$ /nix/var/nix/profiles/default/bin/nix run nixpkgs#hello
Hello, world!
```

### Application Prepared for Nix

The Lab 1 app was copied into:

```text
labs/lab18/app_python/
```

The copied runtime files are:

```text
app.py
requirements.txt
tests/test_app.py
data/.gitkeep
Dockerfile.lab2
```

The Python service exposes `/`, `/health`, `/metrics`, and `/visits`. The Nix package also runs the app's pytest suite during the build.

### `default.nix`

The app is built with `pythonPackages.buildPythonApplication`:

```nix
{ pkgs ? import <nixpkgs> {} }:

let
  python = pkgs.python3;
  pythonPackages = python.pkgs;
  runtimeDependencies = with pythonPackages; [
    flask
    prometheus-client
  ];
in
pythonPackages.buildPythonApplication {
  pname = "devops-info-service";
  version = "1.0.0";
  src = ./.;

  format = "other";

  propagatedBuildInputs = runtimeDependencies;
  nativeBuildInputs = [ pkgs.makeWrapper ];
  nativeCheckInputs = with pythonPackages; [ pytest ];

  installCheckPhase = ''
    runHook preInstallCheck
    export PYTHONPATH="$PWD:${pythonPackages.makePythonPath runtimeDependencies}"
    export VISITS_FILE="$TMPDIR/visits"
    pytest -q
    runHook postInstallCheck
  '';

  installPhase = ''
    runHook preInstall
    mkdir -p $out/share/devops-info-service $out/bin
    cp app.py $out/share/devops-info-service/app.py
    cp -r data $out/share/devops-info-service/data

    makeWrapper ${python}/bin/python $out/bin/devops-info-service \
      --add-flags "$out/share/devops-info-service/app.py" \
      --prefix PYTHONPATH : "${pythonPackages.makePythonPath runtimeDependencies}" \
      --set PYTHONUNBUFFERED "1"
    runHook postInstall
  '';
}
```

Field explanation:

| Field | Purpose |
| --- | --- |
| `pname`, `version` | Name the immutable Nix output. |
| `src = ./.` | Uses the checked source directory as the build input. |
| `format = "other"` | The app has no `setup.py` or `pyproject.toml`; it is a direct Flask script. |
| `propagatedBuildInputs` | Runtime Python closure: Flask and Prometheus client. |
| `nativeBuildInputs` | Provides `makeWrapper` to create the executable launcher. |
| `nativeCheckInputs` | Provides pytest during the build only. |
| `installCheckPhase` | Runs the Lab 1 test suite inside the Nix build sandbox. |
| `installPhase` | Installs `app.py` plus a wrapped `devops-info-service` executable. |

Build result:

```text
$ nix build .#default --print-build-logs
devops-info-service> Running phase: installCheckPhase
devops-info-service> .......                                                                  [100%]
devops-info-service> 7 passed in 0.44s
```

### Running the Nix-Built App

```text
$ PORT=5055 VISITS_FILE=/tmp/devops-info-service-nix-visits ./result/bin/devops-info-service
{"message": "application_starting", "host": "0.0.0.0", "port": 5055, ...}
```

Health endpoint:

```text
$ curl -s http://127.0.0.1:5055/health
{"status":"healthy","timestamp":"2026-05-12T10:09:24.957Z","uptime_seconds":14}
```

Metrics endpoint proved the pinned Nix Python runtime:

```text
python_info{implementation="CPython",major="3",minor="13",patchlevel="12",version="3.13.12"} 1.0
```

### Reproducibility Proof

First build:

```text
first_store=/nix/store/rmk9f3qi850i75h31lviahjjcaiqqk1l-devops-info-service-1.0.0
```

Second build after deleting only the `result` symlink:

```text
second_store=/nix/store/rmk9f3qi850i75h31lviahjjcaiqqk1l-devops-info-service-1.0.0
nix_hash=97321ec81e044a1b58b26c153555129306766fc0f22a49d6b7fa40fa861be69e
same_store=yes
```

Forced rebuild after deleting the output from `/nix/store`:

```text
delete_store=/nix/store/rmk9f3qi850i75h31lviahjjcaiqqk1l-devops-info-service-1.0.0
1 store paths deleted, 17.6 KiB freed
rebuilt_store=/nix/store/rmk9f3qi850i75h31lviahjjcaiqqk1l-devops-info-service-1.0.0
nix_hash_after_forced_rebuild=97321ec81e044a1b58b26c153555129306766fc0f22a49d6b7fa40fa861be69e
same_after_delete=yes
```

Nix store path format:

```text
/nix/store/rmk9f3qi850i75h31lviahjjcaiqqk1l-devops-info-service-1.0.0
           ^ hash of all build inputs        ^ package name and version
```

The hash includes source code, build recipe, Python, Flask, Prometheus client, pytest, shell tools, and transitive dependencies from the locked `nixpkgs` input. Same inputs produced the same store path even after deleting and rebuilding the package.

### Lab 1 `requirements.txt` vs Nix

| Aspect | Lab 1 pip + venv | Lab 18 Nix |
| --- | --- | --- |
| Python version | Depends on system or base image | Pinned through `nixpkgs`: Python 3.13.12 |
| Direct dependencies | `requirements.txt` pins some packages | `nixpkgs` pins package derivations |
| Transitive dependencies | Resolved by pip at install time | Fixed as part of the Nix closure |
| Build isolation | Virtualenv, host-dependent | Nix sandbox and immutable store |
| Rebuild result | Can drift over time | Same path and same NAR hash |
| Cache safety | No content-addressed proof | Store path encodes dependency graph |

The Lab 2 Docker build showed pip resolving transitive packages live from PyPI:

```text
Successfully installed Flask-3.1.0 ... Werkzeug-3.1.8 click-8.3.3 packaging-26.2 ...
```

Even with direct pins like `Flask==3.1.0`, `requirements.txt` does not pin every artifact hash or the Python interpreter unless extra lock tooling is used. Nix pinned the full build graph through the locked `nixpkgs` revision.

Reflection: using Nix from Lab 1 would have removed hidden assumptions about local Python, virtualenv state, and PyPI state. The service could have been built, tested, and run with one command on every machine.

## Task 2 - Reproducible Docker Images

### Lab 2 Dockerfile Reviewed

The original Dockerfile was copied as `Dockerfile.lab2`. It uses:

```dockerfile
FROM python:3.13-slim
RUN pip install --no-cache-dir -r requirements.txt
CMD ["python", "app.py"]
```

Weak points:

- `python:3.13-slim` is a mutable tag.
- `pip install` resolves packages during the image build.
- Docker config contains build creation timestamps.
- Rebuilding with `--no-cache` produced different image IDs.

### `docker.nix`

The reproducible image is defined with `dockerTools.buildLayeredImage`:

```nix
{ pkgs ? import <nixpkgs> {} }:

let
  app = import ./default.nix { inherit pkgs; };
in
pkgs.dockerTools.buildLayeredImage {
  name = "devops-info-service-nix";
  tag = "1.0.0";

  contents = [ app ];

  extraCommands = ''
    mkdir -m 1777 -p tmp
  '';

  config = {
    Cmd = [ "${app}/bin/devops-info-service" ];
    Env = [
      "HOST=0.0.0.0"
      "PORT=5000"
      "DEBUG=false"
      "VISITS_FILE=/tmp/devops-info-visits"
      "PYTHONUNBUFFERED=1"
    ];
    ExposedPorts = {
      "5000/tcp" = {};
    };
    WorkingDir = "/tmp";
    User = "1000:1000";
  };

  created = "1970-01-01T00:00:01Z";
}
```

The key reproducibility choice is the fixed `created` timestamp. The image also has no mutable base image; it contains the exact Nix store closure for the app.

### Nix Docker Image Reproducibility

```text
first_image_store=/nix/store/xbkylzzi8lr5xmsc5lw05krnaiahmp6v-devops-info-service-nix.tar.gz
first_image_sha256=3e2623750426c114e5ca85127a153c0418ff5d51a67193a3d0d0ea5ec3e97eb7
first_image_size=89M

second_image_store=/nix/store/xbkylzzi8lr5xmsc5lw05krnaiahmp6v-devops-info-service-nix.tar.gz
second_image_sha256=3e2623750426c114e5ca85127a153c0418ff5d51a67193a3d0d0ea5ec3e97eb7
second_image_size=89M
image_same_store=yes
image_same_hash=yes
```

Docker load:

```text
$ docker load -i result
Loaded image: devops-info-service-nix:1.0.0
```

Loaded image metadata:

```text
[devops-info-service-nix:1.0.0] sha256:2d726f6f60135f721dc8909d74b344a4649ca62a6ab9a1ba3c52113b9e2d6bfe 1970-01-01T00:00:01Z 215862784
```

### Traditional Docker Rebuild Comparison

Two no-cache builds of the Lab 2 Dockerfile:

```text
[lab2-app:lab18-v1] sha256:c17962c7f9ef138ebbfe6fa61ae30874865ac9e85ad2f68b88f4eacc5d3d3ccf 2026-05-12T10:16:15.342360653Z 129407563
[lab2-app:lab18-v2] sha256:786fae569b48a8903a4c841fe5c7299a20dd957c3b2613c24146000e4600e7f8 2026-05-12T10:17:15.141160192Z 129407563
```

Saved tar hashes:

```text
lab2-app:lab18-v1 docker save sha256 = 820db476090d69deb918c22a6c5a1decf878ef609e9af3ad4ce83e13718bf3aa
lab2-app:lab18-v2 docker save sha256 = 4fda0693b2d09e4f23673046136ea177ede0fd8853c677670715448ce6cc5f3e
devops-info-service-nix:1.0.0 docker save sha256 = 8e188b80e70e8f742215bdac0784717386c802cd044bba880a2c100d73e8fb5b
```

Image size comparison:

| Image | ID prefix | Size |
| --- | --- | ---: |
| `lab2-app:lab18-v1` | `c17962c7f9ef` | 129 MB |
| `lab2-app:lab18-v2` | `786fae569b48` | 129 MB |
| `devops-info-service-nix:1.0.0` | `2d726f6f6013` | 216 MB loaded / 89 MB compressed tar |

The Nix image is larger in this run because it contains the full Nix Python runtime closure. Its reproducibility property is stronger: the tarball store path and SHA256 were identical across rebuilds.

### Layer History

Traditional Docker history contains recent timestamps and mutable base image layers:

```text
/bin/sh -c #(nop)  CMD ["python" "app.py"] | 2 minutes ago | 0B
/bin/sh -c pip install --no-cache-dir -r requirements.txt | 2 minutes ago | 11.7MB
CMD ["python3"] | 3 days ago | 0B
# debian.sh --arch 'amd64' out/ 'trixie' '@1777939200' | 7 days ago | 78.6MB
```

Nix image history shows deterministic content layers:

```text
N/A | 132MB
N/A | 34.9MB
N/A | 10.3MB
N/A | 9.3MB
...
```

The Nix image config also printed:

```text
"repo_tag": "devops-info-service-nix:1.0.0"
"created": "1970-01-01T00:00:01+00:00"
"from_image": null
```

### Containers Running Side by Side

```text
$ docker run -d -p 5000:5000 --name lab2-container lab2-app:lab18-v1
$ docker run -d -p 5001:5000 --name nix-container devops-info-service-nix:1.0.0

nix-container devops-info-service-nix:1.0.0 Up 16 seconds 0.0.0.0:5001->5000/tcp
lab2-container lab2-app:lab18-v1 Up 16 seconds 0.0.0.0:5000->5000/tcp
```

Health checks:

```text
$ curl -s http://127.0.0.1:5000/health
{"status":"healthy","timestamp":"2026-05-12T10:18:53.457Z","uptime_seconds":15}

$ curl -s http://127.0.0.1:5001/health
{"status":"healthy","timestamp":"2026-05-12T10:18:53.465Z","uptime_seconds":15}
```

Why traditional Docker is not bit-for-bit reproducible:

- Image config has a `Created` timestamp.
- Mutable tags like `python:3.13-slim` can move.
- `pip install` contacts PyPI during the build.
- Base image, package indexes, and wheel selection may change independently of the Dockerfile.
- Docker layer cache can hide drift locally but does not prove reproducibility.

Reflection: if Lab 2 were redone with Nix, I would build the app once as a derivation, create the image from the derivation, load/push that immutable image, and deploy it by digest instead of relying on mutable tags.

Practical scenarios where this matters:

- CI/CD cache correctness.
- Security audits that require exact dependency provenance.
- Rollbacks to a known artifact.
- Rebuilding after a registry compromise.
- Debugging cross-machine failures.

## Bonus - Nix Flakes

### `flake.nix`

The flake exposes the app, Docker image, app runner, checks, and a dev shell:

```nix
{
  description = "DevOps Info Service - reproducible Nix build for Lab 18";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixpkgs-unstable";
  };

  outputs = { self, nixpkgs }:
    let
      system = "x86_64-linux";
      pkgs = nixpkgs.legacyPackages.${system};
      app = import ./default.nix { inherit pkgs; };
      dockerImage = import ./docker.nix { inherit pkgs; };
    in
    {
      packages.${system} = {
        default = app;
        dockerImage = dockerImage;
      };

      apps.${system}.default = {
        type = "app";
        program = "${app}/bin/devops-info-service";
      };

      checks.${system}.default = app;

      devShells.${system}.default = pkgs.mkShell {
        packages = with pkgs; [
          python3
          python3Packages.flask
          python3Packages.prometheus-client
          python3Packages.pytest
        ];

        shellHook = ''
          export VISITS_FILE="$PWD/data/visits"
          echo "Lab 18 Nix shell: Python $(python --version)"
        '';
      };
    };
}
```

### `flake.lock`

Pinned `nixpkgs` input:

```json
{
  "lastModified": 1778458615,
  "narHash": "sha256-cY07EsdhBJ8tFXPzDYevgqxRev9ZLxFonuq9wmq5kwg=",
  "owner": "NixOS",
  "repo": "nixpkgs",
  "rev": "c6e5ca3c836a5f4dd9af9f2c1fc1c38f0fac988a",
  "type": "github"
}
```

The lock file pins the exact package universe used for Python, Flask, Prometheus client, pytest, Docker image tooling, and all transitive libraries.

### Flake Build and Check Outputs

```text
$ nix flake check --no-build
devShells.x86_64-linux.default (build skipped)
packages.x86_64-linux.dockerImage (build skipped)
packages.x86_64-linux.default (build skipped)
apps.x86_64-linux.default
checks.x86_64-linux.default
```

Development shell:

```text
$ nix develop .#default -c python --version
Lab 18 Nix shell: Python Python 3.13.12
Python 3.13.12

$ nix develop .#default -c python -c 'import importlib.metadata as m; print(m.version("flask")); print(m.version("prometheus-client")); print(m.version("pytest"))'
Lab 18 Nix shell: Python Python 3.13.12
3.1.2
0.24.1
9.0.2
```

### Lab 10 Helm Values vs Nix Flakes

Existing Helm values in `k8s/devops-info/values.yaml`:

```yaml
image:
  repository: j0cos/devops-info-service
  tag: "lab02"
  pullPolicy: IfNotPresent
```

Comparison:

| Aspect | Helm `values.yaml` | Nix Flake |
| --- | --- | --- |
| Pins image tag | Yes, `lab02` | Can produce an image tarball/digest |
| Pins image contents | No, a tag can be retagged | Yes, store path and tarball hash are stable |
| Pins Python | Only indirectly through image | Yes, through locked `nixpkgs` |
| Pins transitive dependencies | No | Yes |
| Pins build tools | No | Yes |
| Dev environment | No | Yes, `nix develop` |

Best combined workflow:

1. Build the image with Nix: `nix build .#dockerImage`.
2. Load and push the generated image.
3. Reference the pushed immutable digest from Helm values.

This keeps Helm for Kubernetes deployment and Nix for artifact reproducibility.

Reflection: flakes improve dependency management because `flake.lock` makes the input package universe explicit, reviewable, and shareable. A teammate can run the same flake and get the same Python and dependency closure instead of rediscovering whatever package indexes provide that day.

## Final Verification Checklist

| Requirement | Status |
| --- | --- |
| `labs/lab18/app_python/default.nix` builds app | Done |
| Nix build runs tests | Done, 7 passed |
| Store path is stable across rebuilds | Done |
| Store path returns after forced delete/rebuild | Done |
| Nix-built app runs and responds | Done |
| `docker.nix` builds image tarball | Done |
| Nix Docker tarball has identical hash across rebuilds | Done |
| Traditional Docker comparison completed | Done |
| Both containers ran side by side | Done |
| `flake.nix` and `flake.lock` present | Done |
| `nix flake check --no-build` passes | Done |
| `nix develop` verified | Done |
