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

**Docker image (needs Docker for `load`/`run`):**

On **Linux** (or NixOS):

```bash
nix build .#docker
docker load < result
docker run --rm -p 5001:5000 devops-info-service-nix:1.0.0
curl -sS http://127.0.0.1:5001/health
```

On **macOS**, `nix build .#docker` often fails inside `dockerTools` with **`fakeroot` / `dyld` (`_fstat$INODE64`)** — this is a known limitation, not a mistake in `docker.nix`. Build the same derivation **inside Linux via Docker**:

```bash
cd labs/lab18/app_python
chmod +x nix-docker-linux.sh
./nix-docker-linux.sh
docker load -i devops-info-service-nix.tar.gz
```

(`result` points into the container’s `/nix/store`; on macOS that path is often missing — the script copies **`devops-info-service-nix.tar.gz`** into this directory for `docker load`.)

Then compare hashes / run containers as in **`submission18.md`**.

Compare with Lab 2 (**repository root**, not `lab18/`):

```bash
docker build -t lab2-app:lab18-compare ./app_python
```

Fill **`../submission18.md`** with store paths, `sha256sum` outputs, `docker history`, and screenshots under **`screenshots/`**.
