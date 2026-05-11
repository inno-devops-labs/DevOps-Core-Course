# Lab 18 App Python

This directory contains the Lab 1 DevOps Info Service repackaged for Lab 18 reproducible builds with Nix.

## Files

| File | Purpose |
|---|---|
| `app.py` | Flask DevOps Info Service copied for Lab 18 work |
| `requirements.txt` | Original pip dependency list used for comparison |
| `Dockerfile` | Traditional Lab 2 Docker workflow used for comparison |
| `default.nix` | Reproducible Nix derivation for the Python app |
| `docker.nix` | Reproducible Docker image built with `dockerTools` |
| `flake.nix` | Modern flake entry point and dev shell |

## Commands

```bash
# Build the app derivation.
nix-build

# Run the Nix-built service.
./result/bin/devops-info-service

# Build the reproducible Docker image tarball.
nix-build docker.nix

# Load the image into Docker.
docker load < result

# Build through the flake.
nix build
nix build .#dockerImage

# Enter the pinned development environment.
nix develop
```

The Nix wrapper sets writable defaults under `/tmp/devops-info-service` so the persistent visits counter works without writing into `/nix/store`.
