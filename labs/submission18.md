# Lab 18 Submission

## Task 1 — Build Reproducible Python App

- Nix derivation: [labs/lab18/app_python/default.nix](labs/lab18/app_python/default.nix)

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
- `GET /` → 200 OK
- `GET /health` → 200 OK
- `GET /metrics` → available

## Task 2 — Reproducible Docker Images

- Nix docker image: [labs/lab18/app_python/docker.nix](labs/lab18/app_python/docker.nix)

### Commands

```bash
cd labs/lab18/app_python
nix build -f docker.nix
sha256sum result
rm result
nix build -f docker.nix
sha256sum result
docker build --no-cache -t lab2-app:v1 ../../app_python
docker build --no-cache -t lab2-app:v2 ../../app_python
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
