# Lab 18 — Reproducible builds (Nix)

Application copy and Nix expressions live under **`app_python/`** (same DevOps Info Service as Labs 1–2).

## Quick commands (from `labs/lab18/app_python/`)

**Classic nix-build (needs `<nixpkgs>` channel or `NIX_PATH`):**

```bash
nix-build
readlink result
./result/bin/devops-info-service
# open http://127.0.0.1:5000/health
```

**Flake (pins `nixpkgs` via `flake.lock`; generate lock once):**

```bash
nix flake lock
nix build .#default
./result/bin/devops-info-service
```

**Docker image (Linux; needs Docker for `load`/`run`):**

```bash
nix-build docker.nix
docker load < result
docker run --rm -p 5001:5000 devops-info-service-nix:1.0.0
curl -sS http://127.0.0.1:5001/health
```

Compare with Lab 2 (**repository root**, not `lab18/`):

```bash
docker build -t lab2-app:lab18-compare ./app_python
```

Fill **`../submission18.md`** with store paths, `sha256sum` outputs, `docker history`, and screenshots under **`screenshots/`**.
