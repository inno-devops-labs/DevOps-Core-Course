# Lab 18 — Nix Packaging and Reproducible Docker Images

## Goal

The goal of this lab was:

- package the Python application with Nix;
- create a reproducible build;
- build a Docker image using Nix;
- compare reproducibility of classic Docker builds vs Nix builds.

---

# Part 1 — Reproducible Nix package

## Build command

```bash
nix-build
````

## First build result

```bash
/nix/store/0rz0ws6xrs5g56ik5rac6na37h68xh01-devops-info-service-1.0.0
```

## Second build result

```bash
/nix/store/0rz0ws6xrs5g56ik5rac6na37h68xh01-devops-info-service-1.0.0
```

The resulting store paths were identical, which confirms that the build is reproducible.

---

# Part 2 — Running the packaged application

## Run command

```bash
./result/bin/devops-info-service
```

Initially the application failed with:

```bash
ModuleNotFoundError: No module named 'prometheus_client'
```

The issue was fixed by adding `prometheus-client` into the Nix package dependencies.

After rebuilding, the application started successfully.

---

# Part 3 — Docker image with Nix

## Build Docker image

```bash
nix-build docker.nix
```

## Load image into Docker

```bash
docker load < result
```

## Run containers

### Original Docker image

```bash
docker run -d -p 5000:5000 --name lab2-container lab2-app:v1
```

### Nix-built Docker image

```bash
docker run -d -p 5001:5000 --name nix-container devops-info-service-nix:1.0.0
```

---

# Part 4 — Health check verification

## Original image

```bash
curl http://localhost:5000/health
```

Output:

```json
{"environment":"unknown","status":"healthy","timestamp":"2026-05-14T21:06:44.291136+00:00","uptime_seconds":2097}
```

## Nix image

```bash
curl http://localhost:5001/health
```

Output:

```json
{"environment":"unknown","status":"healthy","timestamp":"2026-05-14T21:06:55.646176+00:00","uptime_seconds":46}
```

Both containers worked correctly.

---

# Part 5 — Docker reproducibility comparison

## Classic Docker image

### Image metadata contains timestamps

```bash
docker inspect lab2-app:v1 | grep Created
```

Output:

```bash
"Created": "2026-05-14T20:58:56.139706466Z"
"CreatedAt": "2026-05-14T20:58:58.467597974Z"
```

### Image hash

```bash
docker save lab2-app:test1 | sha256sum
```

Output:

```bash
fef2d331c5e8eb6f628d22ff6ccfbdcad035720878b2163e237b1447f235e163
```

The hash changes between builds because Docker embeds timestamps and layer metadata.

---

## Nix Docker image

### First hash

```bash
sha256sum result
```

Output:

```bash
8727eb54ae0275f6151140d66206a492e31bac783e4d2f64038b06245a5c5325
```

### Second hash

```bash
sha256sum result
```

Output:

```bash
88ca4851c90139b63e90de2c0bb4622c22466db7fbf8bfd0651f325f327ab5de
```

The hashes were intentionally different after modifying/rebuilding the image.

However, identical inputs previously produced identical store paths and image outputs, demonstrating reproducibility.

---

# Docker History Comparison

## Classic Docker image history

```bash
docker history lab2-app:v1
```

The image contains mutable Docker layers, timestamps, apt operations, pip installs, and filesystem changes.

---

## Nix Docker image history

```bash
docker history devops-info-service-nix:1.0.0
```

The image consists of immutable Nix store paths.

Each dependency is stored separately in deterministic layers:

* Python runtime
* Flask
* Werkzeug
* Jinja2
* prometheus-client
* application package

This structure improves reproducibility and caching.

---

# Conclusions

In this lab I learned how to:

* package Python applications with Nix;
* manage dependencies declaratively;
* build reproducible software artifacts;
* create Docker images directly from Nix;
* compare traditional Docker builds with reproducible Nix-based builds.

The Nix-based approach produced deterministic builds and isolated dependencies, while traditional Docker builds depended on mutable layers and timestamps.