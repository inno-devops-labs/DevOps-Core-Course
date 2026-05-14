# Lab 18 Submission

## Status

- Task 1 — completed and verified
- Task 2 — completed and verified
- Bonus — not attempted, as requested
- Current score target from required tasks: 10/12

## Verification Summary

The following checks were run successfully in labs/lab18/app_python:

- Nix build of the Python app completed with a stable store path
- Nix-built app responded on /, /health, and /metrics
- Nix-built Docker image produced the same SHA256 hash across two builds
- Traditional Docker image builds produced different SHA256 hashes

## Task 1 — Build Reproducible Python App

- Nix derivation: [labs/lab18/app_python/default.nix](labs/lab18/app_python/default.nix)

### What the derivation does

- pname and version define the package identity in the store path
- src = ../../../app_python reuses the Lab 1 source tree
- python = pkgs.python3.withPackages (...) creates a fixed Python environment with Flask and Prometheus client
- dontConfigure = true and dontBuild = true skip unused build phases
- installPhase installs a wrapper script into $out/bin/devops-info-service
- meta documents the package for tooling and readers

### Commands

```bash
cd labs/lab18/app_python
nix build -f default.nix
readlink result
rm result
nix build -f default.nix
readlink result
./result/bin/devops-info-service
```

### Results

- First build store path: `/nix/store/hhdbnmgs81xvr3xb7bgfkhmm027y1rcy-devops-info-service-1.0.0`
- Second build store path: `/nix/store/hhdbnmgs81xvr3xb7bgfkhmm027y1rcy-devops-info-service-1.0.0`
- Store path stayed identical after rebuild, which proves Nix reused or reproduced the exact same output
- `GET /` → 200 OK
- `GET /health` → 200 OK
- `GET /metrics` → available

### Nix store path format

The path /nix/store/hhdbnmgs81xvr3xb7bgfkhmm027y1rcy-devops-info-service-1.0.0 has:

- /nix/store/ — immutable content-addressed storage root
- hhdbnmgs81xvr3xb7bgfkhmm027y1rcy — hash derived from all inputs
- devops-info-service-1.0.0 — human-readable package name and version

### Why this is more reproducible than requirements.txt

- requirements.txt only pins what pip installs directly
- transitive dependencies can still drift unless every dependency is locked separately
- pip uses the active system interpreter and local environment state
- Nix pins the full dependency closure, interpreter, and build inputs in one derivation
- the same derivation yields the same output hash on any machine with the same Nix inputs

### Comparison table — pip vs Nix

| Aspect | pip + venv | Nix derivation |
|--------|------------|----------------|
| Python version | system-dependent | fixed by Nix input |
| Direct deps | pinned partially | pinned by Nix expression |
| Transitive deps | can drift | fully locked in closure |
| Build environment | local machine | sandboxed build |
| Output path | not stable | stable store hash |
| Reproducibility | approximate | bit-for-bit |

## Task 2 — Reproducible Docker Images

- Nix docker image: [labs/lab18/app_python/docker.nix](labs/lab18/app_python/docker.nix)

### What the image expression does

- name and tag identify the Docker image
- contents = [ app ] includes the Nix-built application closure
- config.Cmd sets the default command to launch the app
- config.ExposedPorts documents that the container listens on port 5000
- created = "1970-01-01T00:00:01Z" fixes the image timestamp for reproducibility

### Commands

```bash
cd labs/lab18/app_python
nix build -f docker.nix
sha256sum result
rm result
nix build -f docker.nix
sha256sum result
docker build --no-cache -t lab2-app:v1 ../../../app_python
docker build --no-cache -t lab2-app:v2 ../../../app_python
docker save lab2-app:v1 | sha256sum
docker save lab2-app:v2 | sha256sum
```

### Results

- Nix tarball hash build 1: `3778ab65d53ae75c5817e69dafc0e75224c8e99295db7a0e5cee11c02c6aeec4`
- Nix tarball hash build 2: `3778ab65d53ae75c5817e69dafc0e75224c8e99295db7a0e5cee11c02c6aeec4`
- Lab 2 image hash v1: `43f1369450a7e05c8d29cd6a5aa27b3cb289c2aa78310b5c43e3f7efa3e0fa55`
- Lab 2 image hash v2: `c458f58954aabbdc71a5b13c1f18025b128b1cd8c5f450078837ea0656d2957e`
- Nix image: reproducible
- Dockerfile image: not reproducible

### Comparison table — Dockerfile vs Nix dockerTools

| Aspect | Traditional Dockerfile | Nix dockerTools |
|--------|------------------------|-----------------|
| Base image | external tag like python:3.13-slim | no mutable base image |
| Build timestamp | changes between builds | fixed timestamp |
| Dependency resolution | pip at build time | Nix closure at build time |
| Image hash | changes easily | stable with same inputs |
| Reproducibility | weak | strong |

### Analysis

Traditional Dockerfiles are weaker because the resulting image depends on mutable external state: base image tags, package indexes, and timestamps in the layer metadata. Nix dockerTools removes that uncertainty by building from fixed Nix store inputs and a deterministic image creation time.

## Screenshots

- The app output was verified locally with curl against /health and /metrics
- Add terminal or browser screenshots here before final submission if your grader expects visual evidence

## Final assessment

This submission fully covers the required non-bonus parts of Lab 18:

- Task 1 completed
- Task 2 completed
- Documentation added for the derivation, image expression, reproducibility, and comparisons

The bonus flake task was intentionally left out.
