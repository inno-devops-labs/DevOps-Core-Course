# Lab 18 - Reproducible Builds with Nix

Run date: May 7, 2026

## Summary

I updated Lab 18 to match the current upstream assignment. The previous IPFS/4EVERLAND solution was removed because the lab now requires reproducible builds with Nix.

The solution packages the Lab 1 Python DevOps Info Service with:

- a Nix derivation in `default.nix`
- a reproducible Docker image definition in `docker.nix`
- a modern flake entrypoint in `flake.nix`
- this written submission report

## Environment Note

The repository was prepared and validated from Windows/PowerShell. `nix` is not installed in this local Windows environment, and the available WSL Ubuntu instance also does not have `nix`.

Because of that, I did not fabricate Nix store paths, output hashes, Docker image hashes, or screenshots. The Nix expressions are committed and ready to run on WSL/Linux/macOS after installing Nix.

Checked commands:

```text
nix --version
```

Result:

```text
nix: command not found
```

WSL check:

```powershell
wsl -e sh -lc "command -v nix && nix --version || true"
```

Result: no `nix` binary found.

## Implemented Files

| File | Purpose |
| --- | --- |
| `labs/lab18/app_python/app.py` | Lab 1 FastAPI DevOps Info Service |
| `labs/lab18/app_python/requirements.txt` | Original pip-based dependency list for comparison |
| `labs/lab18/app_python/Dockerfile` | Original Lab 2 Dockerfile for comparison |
| `labs/lab18/app_python/default.nix` | Nix derivation for the Python app |
| `labs/lab18/app_python/docker.nix` | Nix `dockerTools` image definition |
| `labs/lab18/app_python/flake.nix` | Flake entrypoint and dev shell |
| `labs/submission18.md` | Lab 18 report |

Removed obsolete Lab 18 files:

- `labs/lab18/docker-compose.yml`
- `labs/lab18/ipfs-demo/*`

## Local Non-Nix Validation

The copied Python app still passes its test suite from the repository root:

```powershell
py -m pytest app_python\tests
```

Result:

```text
collected 40 items
app_python\tests\test_app.py ........................................ [100%]
40 passed
```

The Kubernetes chart still passes lint after the Lab 17 and Lab 18 branch chain merges:

```powershell
.\.tools\helm.exe lint .\k8s\devops-info-service
```

Result:

```text
1 chart(s) linted, 0 chart(s) failed
```

The inherited Lab 17 Workers project also still builds:

```powershell
cd .\labs\lab17\edge-api
npm run typecheck
npm run deploy:dry-run
```

Result:

```text
tsc --noEmit
wrangler deploy --dry-run --outdir dist
Total Upload: 3.57 KiB / gzip: 1.35 KiB
--dry-run: exiting now.
```

## Task 1 - Nix Python Application

The derivation is in `labs/lab18/app_python/default.nix`.

It uses:

```nix
pythonPackages.buildPythonApplication {
  pname = "devops-info-service";
  version = "1.0.0";
  src = ./.;
  format = "other";
}
```

Runtime dependencies are declared as Nix packages:

- `fastapi`
- `uvicorn`
- `prometheus-client`
- `python-dotenv`

The derivation installs the source into `$out/share/devops-info-service` and creates a wrapped executable:

```nix
makeWrapper ${pythonEnv}/bin/python $out/bin/devops-info-service \
  --set PYTHONPATH "$out/share/devops-info-service" \
  --set HOST "0.0.0.0" \
  --set PORT "8000" \
  --add-flags "-m uvicorn app:app --host 0.0.0.0 --port 8000"
```

Build commands for a Nix-enabled host:

```bash
cd labs/lab18/app_python
nix-build
./result/bin/devops-info-service
curl http://127.0.0.1:8000/health
```

Expected health response:

```json
{
  "status": "healthy"
}
```

Reproducibility proof commands:

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

Expected result: identical store path and identical output hash for identical inputs.

## Task 1 Comparison - Lab 1 vs Nix

| Aspect | Lab 1 pip + venv | Lab 18 Nix |
| --- | --- | --- |
| Python version | Depends on host Python | Provided by nixpkgs |
| Direct dependencies | Listed in `requirements.txt` | Declared as Nix packages |
| Transitive dependencies | Resolved by pip/index behavior | Part of Nix closure |
| Build environment | Host-dependent | Isolated Nix environment |
| Rebuild behavior | Can drift over time | Same inputs produce same output |

`requirements.txt` is useful, but it is weaker than Nix because it does not lock the whole build environment. Nix locks Python, libraries, build tools, and runtime closure through the package graph.

## Task 2 - Reproducible Docker Image

The Docker image definition is in `labs/lab18/app_python/docker.nix`.

It uses:

```nix
pkgs.dockerTools.buildLayeredImage {
  name = "devops-info-service-nix";
  tag = "1.0.0";
  created = "1970-01-01T00:00:01Z";
}
```

The fixed `created` timestamp is deliberate. A dynamic timestamp such as `created = "now"` would break bit-for-bit reproducibility.

Build and run commands:

```bash
cd labs/lab18/app_python
nix-build docker.nix
sha256sum result
docker load < result
docker run --rm -p 8000:8000 devops-info-service-nix:1.0.0
curl http://127.0.0.1:8000/health
```

Repeat build proof:

```bash
rm result
nix-build docker.nix
sha256sum result

rm result
nix-build docker.nix
sha256sum result
```

Expected result: identical tarball hashes.

## Task 2 Comparison - Lab 2 Dockerfile vs Nix dockerTools

| Aspect | Lab 2 Dockerfile | Lab 18 Nix dockerTools |
| --- | --- | --- |
| Base runtime | `python:3.13-slim` tag | Nix store closure |
| Dependency install | `pip install -r requirements.txt` | Nix package graph |
| Timestamp behavior | Docker image metadata varies | Fixed timestamp |
| Reproducibility | Not bit-for-bit by default | Designed for identical outputs |
| Auditability | Docker layers and pip environment | Nix closure and store paths |

Traditional Dockerfiles package applications well, but they do not guarantee identical image hashes across rebuilds unless every input is pinned and timestamps are controlled. Nix `dockerTools` builds the image from deterministic store paths.

## Bonus - Flakes

`labs/lab18/app_python/flake.nix` provides:

- default package
- Docker image package
- development shell
- multi-system output structure

Flake input:

```nix
inputs.nixpkgs.url = "github:NixOS/nixpkgs/nixos-25.11";
```

Commands for a Nix-enabled host:

```bash
cd labs/lab18/app_python
nix flake update
nix build
nix build .#dockerImage
nix develop
```

After `nix flake update`, `flake.lock` should be committed. It records the exact nixpkgs revision and content hash used for the build.

## Lab 10 Comparison - Helm Values vs Nix Flakes

| Aspect | Helm values | Nix Flakes |
| --- | --- | --- |
| Main purpose | Kubernetes deployment configuration | Dependency and build reproducibility |
| Image versioning | Can pin tags or digests | Can build reproducible image output |
| Dependency lock | Chart lock and image reference only | Full nixpkgs input lock |
| Runtime dependency control | Outside Helm unless image is immutable | Inside the Nix build |
| Best combined use | Deploy immutable image digest | Produce that immutable image |

The strongest workflow is to build the app image with Nix, publish it by digest, then deploy that digest through Helm.

## Evidence Checklist For Final Nix Run

Run these commands on a Nix-enabled host and add screenshots or output snippets:

```bash
nix --version
cd labs/lab18/app_python
nix-build
readlink result
nix-hash --type sha256 result
rm result && nix-build && readlink result
nix-build docker.nix
sha256sum result
docker load < result
docker images | grep devops-info-service-nix
docker history devops-info-service-nix:1.0.0
docker run --rm -p 8000:8000 devops-info-service-nix:1.0.0
curl http://127.0.0.1:8000/health
nix flake update
nix build
nix build .#dockerImage
```

## Reflection

Nix would have improved Lab 1 by removing dependence on the local Python installation and the behavior of pip at install time. It would have improved Lab 2 by creating the container image from a declared closure instead of a mutable base image tag and timestamped Docker build layers.

The tradeoff is setup complexity. Nix requires a dedicated installation and a different packaging model, but the benefit is much stronger reproducibility and clearer dependency auditing.
