# Lab 2 — Docker Containerization

> This document is written to match the lab requirements and the repository structure used in class.

## 1. Docker Best Practices Applied

| Practice | Why it matters |
|----------|----------------|
| **Non-root user** | Reduces blast radius if the app or image is compromised; limits privileges inside the container. |
| **Specific base version** (`python:3.13-slim`) | Ensures reproducible builds and avoids unexpected breaking changes from base image updates. |
| **Layer order** | Dependencies are installed before copying application code, so Docker can cache layers efficiently. |
| **Only copy necessary files** | Keeps the image smaller and avoids leaking unnecessary files into the container. |
| **`.dockerignore`** | Excludes development artifacts, virtual environments, and documentation from the build context. |
| **`EXPOSE 5001`** | Documents the port used by the application inside the container. |

**Snippet (layer order + non-root):**

```dockerfile
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app.py .
USER appuser

## 2. Image Information & Decisions

Base image: python:3.13-slim — lightweight, predictable, and suitable for production.
Layer structure: base image → non-root user creation → WORKDIR → dependency installation → application code → permissions → runtime command.
Image size: kept moderate by using a slim base image and excluding unnecessary files.

## 3. Build & Run Process

**Build:** (run from `app_python/`):
``` docker build -t devops-course-lab2:local . ```

Result:
``` Successfully built 3ad897364144
Successfully tagged devops-course-lab2:local ```

**Run:**
``` docker run --rm -p 5001:5000 devops-course-lab2:local ```

**Test endpoints:**

```bash
curl http://localhost:5001/
curl http://localhost:5001/health
```

Add screenshots into `docs/screenshots/` (for example: `lab2-check-health.png`).

**Docker Hub:**
- Repository URL: `https://hub.docker.com/repository/docker/darriyan0/devops-course-lab2/general`
- Push result: docker push darriyan0/devops-course-lab2:latest
latest: digest: sha256:3ce7af6e04bae8d66d403e5c23bda2b619f794b7fae59a37468670ad632fef64 size: 2407
- Tagging strategy (recommended): `latest` for newest stable, and semantic version tags like `1.0.0` for releases.

## 4. Technical Analysis

- The service binds to `0.0.0.0:5001`, so it is reachable from host when using `docker run -p 5001:5000 ...`.
- Dependencies are installed in a separate layer. If only `app.py` changes, Docker reuses the cached dependency layer.
- Non-root execution reduces risk compared to running as root.

## 5. Challenges & Solutions

- (Fill in if you faced any issues. Example: port binding, missing dependency, permissions, etc.)

