# Lab 18 Submission: Reproducible Builds with Nix

## Summary

This submission rebuilds the Python DevOps Info Service from Labs 1 and 2 using Nix, creates a reproducible Docker image with `dockerTools`, and adds a modern Flake setup with a locked `nixpkgs` revision.

Implemented files:

| File | Purpose |
|---|---|
| `solution/lab18/app_python/default.nix` | Reproducible Nix build for the Python service |
| `solution/lab18/app_python/docker.nix` | Reproducible Docker image built by Nix |
| `solution/lab18/app_python/flake.nix` | Flake entry point for package, Docker image, and dev shell |
| `solution/lab18/app_python/flake.lock` | Locked `nixpkgs` input for time-stable builds |
| `solution/lab18/docs/evidence/` | Command outputs, hashes, runtime checks, and comparisons |

The original Lab 1 and Lab 2 application was copied from `solution/app_python` into `solution/lab18/app_python`.

## Environment

WSL2 Ubuntu was available after reboot, but native installer endpoints were not reachable from this network path:

```text
Determinate Systems installer: install.determinate.systems:443 timed out
Official Nix installer: nixos.org:443 timed out
```

The lab builds were executed in the official `nixos/nix:latest` Linux container. This provides the same Nix CLI and nixpkgs build semantics used by a native Linux installation.

Nix verification:

```text
nix (Nix) 2.34.7
Hello, world!
```

Docker verification:

```text
Docker Engine 28.5.1
```

## Task 1: Reproducible Python App

### Nix Derivation

The Python service is built with `python313Packages.buildPythonApplication`. The application does not use `setup.py` or `pyproject.toml`, so the derivation uses `format = "other"` and installs `app.py` directly.

```nix
{ pkgs ? import <nixpkgs> {} }:

let
  python = pkgs.python313;
  pythonPackages = python.pkgs;
  pythonEnv = python.withPackages (ps: with ps; [
    fastapi
    prometheus-client
    uvicorn
  ]);
  source = pkgs.lib.cleanSourceWith {
    src = ./.;
    filter = path: type:
      let
        base = baseNameOf path;
      in
        !(base == "result"
          || base == ".pytest_cache"
          || base == "__pycache__"
          || base == "venv"
          || base == ".venv");
  };
in
pythonPackages.buildPythonApplication {
  pname = "devops-info-service";
  version = "1.0.0";
  src = source;

  format = "other";

  propagatedBuildInputs = with pythonPackages; [
    fastapi
    prometheus-client
    uvicorn
  ];

  nativeBuildInputs = [ pkgs.makeWrapper ];

  installPhase = ''
    runHook preInstall

    mkdir -p $out/bin $out/share/devops-info-service
    cp app.py $out/share/devops-info-service/app.py

    makeWrapper ${pythonEnv}/bin/python $out/bin/devops-info-service \
      --add-flags "$out/share/devops-info-service/app.py" \
      --set HOST "0.0.0.0" \
      --set PORT "5000" \
      --set RELEASE_VERSION "nix-1.0.0" \
      --set VISITS_FILE "/tmp/devops-info-service/visits"

    runHook postInstall
  '';
}
```

Field notes:

| Field | Reason |
|---|---|
| `python313` | Pins the Python major and minor runtime through nixpkgs |
| `python.withPackages` | Creates a runtime Python environment containing FastAPI, Uvicorn, and Prometheus client |
| `cleanSourceWith` | Excludes local build artifacts such as `result` so they do not change the build input hash |
| `format = "other"` | Fits this app because it is a plain `app.py`, not an installable Python package |
| `makeWrapper` | Creates a stable executable called `devops-info-service` |

### Reproducibility Evidence

Two clean builds produced the same store path:

```text
Build 1: /nix/store/r9cmihjxf2cksxlgzl0z8lkbp5d2rp82-devops-info-service-1.0.0
Build 2: /nix/store/r9cmihjxf2cksxlgzl0z8lkbp5d2rp82-devops-info-service-1.0.0
```

The output hash also stayed identical:

```text
Build 1 hash: 0f65999d2ff40f7248879bb167540d37317147d1770506e04fc0323e602e8f69
Build 2 hash: 0f65999d2ff40f7248879bb167540d37317147d1770506e04fc0323e602e8f69
```

The Nix-built application runs successfully:

```json
{"status":"healthy","timestamp":"2026-05-14 18:41:05","uptime_seconds":4}
```

### Lab 1 vs Lab 18

| Aspect | Lab 1: pip and venv | Lab 18: Nix |
|---|---|---|
| Python version | Depends on host Python | Pinned through nixpkgs |
| Direct dependencies | Listed in `requirements.txt` | Declared in Nix expression |
| Transitive dependencies | Resolved by pip at install time | Locked by the nixpkgs revision |
| Build isolation | Virtual environment only | Nix sandbox and store paths |
| Output identity | No stable output path | Stable `/nix/store/<hash>-name-version` path |
| Binary cache | No native content-addressed cache | Nix can reuse cached store paths |
| Rebuild behavior | Re-runs installer logic | Same inputs produce the same path |

`requirements.txt` is useful, but it is weaker than Nix because it describes Python package intent, not the full build environment. It does not pin the interpreter build, C libraries, build tools, system packages, or every binary input. Nix records the full closure, so the output path changes only when an input changes.

## Task 2: Reproducible Docker Images

### Nix Docker Image

The Docker image is built with `dockerTools.buildLayeredImage`:

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
    pkgs.cacert
  ];

  config = {
    Cmd = [ "${app}/bin/devops-info-service" ];
    Env = [
      "HOST=0.0.0.0"
      "PORT=5000"
      "RELEASE_VERSION=nix-container-1.0.0"
      "VISITS_FILE=/tmp/devops-info-service/visits"
    ];
    ExposedPorts = {
      "5000/tcp" = {};
    };
  };

  created = "1970-01-01T00:00:01Z";
}
```

The fixed `created` timestamp is important. Using `created = "now"` would make the image differ between builds.

### Nix Image Hashes

Two builds of `docker.nix` produced the same tarball path and SHA256:

```text
Build 1: /nix/store/2whnmcrn581dgscg010jhawkccm0s56y-devops-info-service-nix.tar.gz
Build 2: /nix/store/2whnmcrn581dgscg010jhawkccm0s56y-devops-info-service-nix.tar.gz
SHA256:  b583352036368cdcabd3d23cf803aa2e57a68177d184a15b96fb8e9df2c7ff14
```

The image was loaded into Docker:

```text
Loaded image: devops-info-service-nix:1.0.0
```

### Traditional Dockerfile Comparison

The Lab 2 Dockerfile was built twice:

```text
Image 1 ID: sha256:d8933ed5054edeb5385067307cd9593ecb20a487810e7a70b2a7258981d4aab4
Image 2 ID: sha256:5486604f1ac77ff7193a76faab64327c736c68056741f9de20a49721ff46640d
```

The saved image tar hashes were different:

```text
lab2-app:test1 SHA256: 682B5F1D570FAEB6AAD81870AE09422C8F7F5D3325D09B7A1CC10CBEABD6B265
lab2-app:test2 SHA256: 858AEDFE1E6B07E8B9971A35F8C43E0B6D56794C2C4419016DFD0A4342B73138
```

Both images were built from the same Dockerfile and source. The image IDs still differed because Docker/BuildKit image metadata and attestations are not bit-for-bit identical by default.

### Runtime Comparison

Both containers were run at the same time:

```text
NAMES            IMAGE                           STATUS         PORTS
nix-container    devops-info-service-nix:1.0.0   Up 8 seconds   0.0.0.0:5001->5000/tcp
lab2-container   lab2-app:test1                  Up 8 seconds   0.0.0.0:5000->5000/tcp
```

Health checks:

```json
Lab 2 Dockerfile: {"status":"healthy","timestamp":"2026-05-14 18:52:15","uptime_seconds":7}
Nix dockerTools: {"status":"healthy","timestamp":"2026-05-14 18:52:15","uptime_seconds":7}
```

Image sizes:

| Image | Size |
|---|---:|
| `lab2-app:test1` | 142 MB |
| `lab2-app:test2` | 142 MB |
| `devops-info-service-nix:1.0.0` | 419 MB |

The Nix image is larger in this run because it includes the complete Python runtime closure from nixpkgs. The advantage demonstrated here is not size, but reproducibility and dependency traceability. A smaller Nix image could be created with more aggressive closure trimming or a different application packaging strategy.

### Why Dockerfile Builds Differ

Traditional Dockerfiles are practical, but they do not guarantee bit-for-bit reproducibility:

| Source of drift | Dockerfile impact |
|---|---|
| Mutable base tags | A tag can point to different image content over time |
| Build metadata | Created timestamps, provenance, and attestations can differ |
| Package managers | `pip`, `apk`, and `apt` resolve packages at build time |
| External indexes | PyPI or distro mirrors can change |
| Layer metadata | Layer history and export format can vary |

Nix avoids these issues by producing image layers from immutable store paths and fixed metadata.

## Bonus: Flakes

### Flake Configuration

The project includes a Flake with package, Docker image, and dev shell outputs:

```nix
{
  description = "DevOps Info Service reproducible Nix build for Lab 18";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-25.11";
  };

  outputs = { self, nixpkgs }:
    let
      system = "x86_64-linux";
      pkgs = nixpkgs.legacyPackages.${system};
    in
    {
      packages.${system} = {
        default = import ./default.nix { inherit pkgs; };
        dockerImage = import ./docker.nix { inherit pkgs; };
      };

      devShells.${system}.default = pkgs.mkShell {
        packages = with pkgs; [
          python313
          python313Packages.fastapi
          python313Packages.prometheus-client
          python313Packages.uvicorn
        ];
      };
    };
}
```

The lock file pins nixpkgs:

```json
{
  "lastModified": 1778430510,
  "narHash": "sha256-Ti+ZBvW6yrWWAg2szExVTwCd4qOJ3KlVr1tFHfyfi8Q=",
  "owner": "NixOS",
  "repo": "nixpkgs",
  "rev": "8fd9daa3db09ced9700431c5b7ad0e8ba199b575",
  "type": "github"
}
```

Flake builds:

```text
nix build path:$PWD#default
/nix/store/md8qzxsdlll5il8wslzrk0pim0dsh0is-devops-info-service-1.0.0

nix build path:$PWD#dockerImage
/nix/store/ss052vifhisjaj19xidycsb8za5wcrl3-devops-info-service-nix.tar.gz
SHA256: 559aefa1f62b015eaed1cc0b3e3f8a9136389aa688d6e449d3cd0ec93a899cdb
```

Development shell:

```text
Lab 18 Nix shell: Python 3.13.12
Python 3.13.12
FastAPI 0.116.1
```

The flake commands were run with `path:$PWD#...` so Nix evaluates the working tree directly. Once these files are tracked in the submitted branch, the shorter `nix build .#default` form works as the equivalent command.

### Flakes vs Lab 10 Helm Pinning

| Aspect | Lab 1 venv | Lab 10 Helm values | Lab 18 Nix Flakes |
|---|---|---|---|
| Python version | Host-dependent | Hidden inside image | Pinned through nixpkgs |
| Application dependencies | pip resolves at install time | Hidden inside image | Locked through nixpkgs closure |
| Build tools | Host-dependent | Not controlled by Helm | Locked through flake input |
| Deployment artifact | Local environment | Image tag | Store path and image tarball |
| Drift risk | High | Medium if tags are mutable | Low while `flake.lock` is unchanged |
| Cross-machine behavior | Varies | Depends on registry content | Same locked inputs |

Helm values are still useful for Kubernetes deployment, but they mostly pin the artifact reference. Nix Flakes pin the toolchain and build graph used to create that artifact.

## Evidence Index

| Evidence | What it proves |
|---|---|
| `00-nix-install-notes.txt` | Native installer endpoints timed out, containerized Nix was used |
| `01-nix-version.txt`, `02-nix-hello.txt` | Nix CLI and basic package execution work |
| `03` to `08` | Nix package path and output hash are identical across rebuilds |
| `09`, `10` | Nix-built application runs and serves `/health` |
| `11` to `14` | Nix Docker image hash is identical across rebuilds |
| `17`, `18`, `20`, `21` | Traditional Dockerfile builds produce different image IDs and save hashes |
| `22` to `24` | Image size and layer history comparison |
| `25` to `29` | Traditional and Nix containers run side by side |
| `30` to `35` | Flake lock, flake builds, Docker image output, and dev shell |

## Reflection

Nix would have helped in Lab 1 by making the Python runtime and dependency graph explicit from the start. Instead of relying on whichever Python and pip resolver behavior was available on a machine, the service would have had a repeatable store path and a fully declared runtime closure.

For Lab 2, Nix makes the difference between "containerized" and "reproducible" clear. Docker is excellent for packaging and running software, but a Dockerfile alone does not prove that two builds are identical. Nix `dockerTools` can create a Docker image from immutable store paths with fixed metadata, which makes hash comparison meaningful.

The main constraint is operational complexity. Nix expressions require more up-front precision, and the resulting closure may be larger than a hand-tuned Dockerfile if it is not optimized. For CI/CD, release audits, regulated environments, and long-term rollback guarantees, that precision is worth the extra work.

## Checklist

| Requirement | Status |
|---|---|
| Python app copied to `solution/lab18/app_python` | Done |
| `default.nix` builds the app | Done |
| Store paths compared across builds | Done |
| Output hashes compared across builds | Done |
| Nix-built app runs and responds on `/health` | Done |
| `docker.nix` builds a Docker image | Done |
| Nix Docker image hashes match across builds | Done |
| Traditional Dockerfile compared | Done |
| Both containers tested side by side | Done |
| `flake.nix` and `flake.lock` added | Done |
| Flake package, Docker image, and dev shell verified | Done |
