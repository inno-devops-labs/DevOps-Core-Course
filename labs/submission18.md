# Lab 18 - Reproducible Builds with Nix

Run date: May 7, 2026

This submission replaces the previous IPFS-based Lab 18 work with the current upstream assignment: Nix reproducible builds for the Lab 1 Python DevOps Info Service and a Nix-built Docker image.

Local limitation: this Windows/PowerShell environment does not have `nix` installed, and WSL does not have `nix` either. The repository now contains the required Nix expressions and commands, but the Nix build outputs must be generated on WSL/Linux/macOS after installing Nix.

## Files

- `labs/lab18/app_python/app.py`
- `labs/lab18/app_python/requirements.txt`
- `labs/lab18/app_python/Dockerfile`
- `labs/lab18/app_python/default.nix`
- `labs/lab18/app_python/docker.nix`
- `labs/lab18/app_python/flake.nix`

The Python app is copied from Lab 1/2 so the Nix build works against the same FastAPI service used throughout the course.

## Task 1 - Nix Python Application

Build:

```bash
cd labs/lab18/app_python
nix-build
./result/bin/devops-info-service
```

The derivation uses:

```nix
pythonPackages.buildPythonApplication {
  pname = "devops-info-service";
  version = "1.0.0";
  src = ./.;
  format = "other";
}
```

Runtime dependencies are declared through Nix packages:

- `fastapi`
- `uvicorn`
- `prometheus-client`
- `python-dotenv`

This is stronger than the Lab 1 `requirements.txt` workflow because Nix pins the full closure: Python, transitive packages, build tools, and wrapper scripts. A `requirements.txt` file pins direct Python packages only and still depends on the system Python, pip behavior, indexes, wheels, and platform details.

Reproducibility commands:

```bash
nix-build
readlink result
nix-hash --type sha256 result

STORE_PATH=$(readlink result)
nix-store --delete "$STORE_PATH"
rm result
nix-build
readlink result
nix-hash --type sha256 result
```

Expected result: the store path and output hash are identical for identical inputs.

## Task 2 - Reproducible Docker Image

Build Nix image tarball:

```bash
cd labs/lab18/app_python
nix-build docker.nix
sha256sum result
docker load < result
docker run --rm -p 8000:8000 devops-info-service-nix:1.0.0
curl http://127.0.0.1:8000/health
```

The Docker image uses:

```nix
pkgs.dockerTools.buildLayeredImage {
  name = "devops-info-service-nix";
  tag = "1.0.0";
  created = "1970-01-01T00:00:01Z";
}
```

The fixed `created` timestamp is important. `created = "now"` would make every image tarball differ even when the source code is unchanged.

Comparison:

| Aspect | Lab 2 Dockerfile | Lab 18 Nix dockerTools |
| --- | --- | --- |
| Base runtime | Mutable image tag such as `python:3.13-slim` | Nix closure from pinned nixpkgs |
| Dependency install | `pip install -r requirements.txt` during Docker build | Nix package graph |
| Timestamps | Docker layers vary by build time | Fixed image timestamp |
| Rebuild hash | Can differ with unchanged source | Expected to be identical |
| Auditability | Image plus pip environment | Nix store closure |

Traditional Dockerfiles are excellent for packaging but do not guarantee bit-for-bit reproducibility by default. Base tags can move, timestamps change, package indexes change, and `pip` can resolve differently over time unless the whole environment is locked.

## Bonus - Flakes

`flake.nix` pins nixpkgs through:

```nix
inputs.nixpkgs.url = "github:NixOS/nixpkgs/nixos-25.11";
```

Generate the lock file and build:

```bash
cd labs/lab18/app_python
nix flake update
nix build
nix build .#dockerImage
nix develop
```

The generated `flake.lock` should be committed after running `nix flake update` in a Nix-enabled environment. It records the exact nixpkgs revision and content hash used for all dependencies.

## Lab 1, Lab 2, Lab 10 Comparison

| Aspect | Lab 1 venv + requirements.txt | Lab 2 Dockerfile | Lab 10 Helm values | Lab 18 Nix |
| --- | --- | --- | --- | --- |
| Python version | Host-dependent | Image tag-dependent | Not controlled | Nix-controlled |
| App dependencies | Direct pins only | pip install during build | Only image tag reference | Full Nix closure |
| Build tools | Host-dependent | Image-dependent | Not controlled | Pinned by nixpkgs |
| Output reproducibility | Approximate | Not bit-for-bit by default | Depends on image immutability | Content-addressed |
| Rollback confidence | Manual | Image tag or digest | Helm release/image tag | Store path or image hash |

Helm values from Lab 10 can pin an image tag, but that tag can still be overwritten unless deployments use immutable digests. Nix can build the image reproducibly, then Helm can deploy it by digest. The strongest workflow combines both: Nix for reproducible image creation and Helm for Kubernetes rollout management.

## Evidence To Capture On Nix-Enabled Host

Required command outputs for final submission screenshots:

```bash
nix --version
nix-build
readlink result
nix-hash --type sha256 result
rm result && nix-build && readlink result
nix-build docker.nix
sha256sum result
docker images | grep devops-info-service-nix
docker history devops-info-service-nix:1.0.0
curl http://127.0.0.1:8000/health
```

Expected app health response:

```json
{
  "status": "healthy"
}
```

## Reflection

Nix would have helped in Lab 1 by removing dependence on whatever Python and pip happened to be installed locally. It would have helped in Lab 2 by producing an image from declared store paths instead of mutable package indexes and timestamped Docker layers. The tradeoff is tooling complexity: Nix has a steeper learning curve and usually needs WSL/Linux/macOS setup before it becomes ergonomic.
