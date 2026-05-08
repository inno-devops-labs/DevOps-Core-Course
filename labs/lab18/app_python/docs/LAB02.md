# Lab 2 - Docker Containerization

## Docker Best Practices Applied

### 1. Non-Root User
Created a dedicated user `appuser` with UID 1000. This prevents potential security vulnerabilities if the container is compromised. Running as root gives full system access, while non-root limits damage.

```dockerfile
RUN useradd -m -u 1000 appuser
USER appuser
```

### 2. Layer Caching Optimization
Copied `requirements.txt` before application code. Dependencies change less frequently than code, so Docker can reuse cached layers during rebuilds, speeding up development.

```dockerfile
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app.py .
```

### 3. Specific Base Image Version
Used `python:3.13-slim` instead of `latest`. This ensures reproducible builds across environments and prevents unexpected breakages from upstream changes.

```dockerfile
FROM python:3.13-slim
```

### 4. .dockerignore File
Excluded unnecessary files (`__pycache__`, `.git`, `docs`, `tests`) from build context. This reduces build time and image size by preventing irrelevant files from being sent to the Docker daemon.

### 5. No Build Cache for pip
Used `--no-cache-dir` flag to prevent pip from storing cache inside the image, reducing final image size.

```dockerfile
RUN pip install --no-cache-dir -r requirements.txt
```

## Image Information & Decisions

### Base Image Choice
**Selected:** `python:3.13-slim`

**Reasoning:**
- **slim** variant: Smaller than full Python image (~150MB vs 1GB), contains only essential packages
- **Not alpine**: Alpine uses musl libc which can cause compatibility issues with some Python packages that need glibc
- **Version pinning**: Explicit 3.13 ensures reproducibility

### Final Image Size
**164MB** - This is reasonable for a Python web application:
- Base python:3.13-slim: ~130MB
- FastAPI + Uvicorn dependencies: ~34MB
- Application code: <1MB

### Layer Structure
```
1. Base OS (python:3.13-slim) - 130MB
2. Create user - minimal
3. Set working directory - 0MB
4. Copy requirements.txt - <1KB
5. Install dependencies - 34MB
6. Copy app.py - ~4KB
7. Switch to non-root user - 0MB
```

### Optimization Choices
- Single-stage build (sufficient for interpreted Python)
- Minimal base image (slim not alpine for compatibility)
- Layer ordering for cache efficiency
- .dockerignore to reduce context

## Build & Run Process

### Build Output
```bash
$ docker build -t devops-app:1.0 .
[+] Building 10.1s (11/11) FINISHED
 => [1/6] FROM docker.io/library/python:3.13-slim
 => [2/6] RUN useradd -m -u 1000 appuser
 => [3/6] WORKDIR /app
 => [4/6] COPY requirements.txt .
 => [5/6] RUN pip install --no-cache-dir -r requirements.txt
 => [6/6] COPY app.py .
 => exporting to image
 => => writing image sha256:bdf9d36ca17eb455dafc05c9a59d6443264b31115c737fb8b5a4e7592c4708a1
 => => naming to docker.io/library/devops-app:1.0
```

### Running Container
```bash
$ docker run -d -p 8000:8000 --name devops-test devops-app:1.0
623ad8b943ed1bad88917e4a5d03e838087fab532490da5106c20ebe26a97905

$ docker ps
CONTAINER ID   IMAGE            COMMAND          CREATED          STATUS          PORTS                    NAMES
623ad8b943ed   devops-app:1.0   "python app.py"  10 seconds ago   Up 9 seconds    0.0.0.0:8000->8000/tcp   devops-test
```

### Testing Endpoints
```bash
$ curl http://localhost:8000
{"service":{"name":"devops-info-service","version":"1.0.0","description":"DevOps course info service","framework":"FastAPI"},"system":{"hostname":"623ad8b943ed","platform":"Linux","platform_version":"6.14.0-37-generic","architecture":"x86_64","cpu_count":12,"python_version":"3.13.11"},"runtime":{"uptime_seconds":9,"uptime_human":"0 hours, 0 minutes","current_time":"2026-02-02T15:04:46.928821+00:00Z","timezone":"UTC"}}

$ curl http://localhost:8000/health
{"status":"healthy","timestamp":"2026-02-02T15:04:46.937277+00:00Z","uptime_seconds":9}

$ curl http://localhost:8000/info
{"service":"devops-info-service","version":"1.0.0","description":"Provides system and runtime information"}
```

### Image Information
```bash
$ docker images devops-app:1.0
REPOSITORY   TAG       IMAGE ID       CREATED         SIZE
devops-app   1.0       bdf9d36ca17e   2 minutes ago   164MB
```

### Docker Hub Repository
**URL:** `https://hub.docker.com/r/kolsmer/devops-app`

## Technical Analysis

### Why This Dockerfile Works

1. **Layer Ordering**: Dependencies installed before code means code changes don't invalidate dependency cache
2. **User Switch Timing**: User created early but switched late, allowing privileged operations (pip install) then dropping permissions
3. **Working Directory**: Set before copying files to ensure correct placement
4. **Minimal Copies**: Only copy what's needed (requirements.txt, app.py) not entire directory

### Impact of Changed Layer Order

If we copied app.py before installing dependencies:
```dockerfile
COPY app.py .
RUN pip install -r requirements.txt  # BAD
```
Every code change would trigger dependency reinstall (slow builds, wasted cache).

### Security Considerations

1. **Non-root execution**: Limits container breakout damage
2. **Pinned versions**: Prevents supply chain attacks from unexpected updates
3. **Minimal base**: Smaller attack surface (less packages = fewer vulnerabilities)
4. **No secrets in image**: All config via environment variables

### .dockerignore Benefits

- **Build speed**: Smaller context transfers faster to Docker daemon
- **Image size**: Prevents accidental inclusion of large files
- **Security**: Keeps sensitive files (.env, credentials) out of image
- **Clarity**: Shows intentional inclusions vs exclusions

## Challenges & Solutions

### Challenge 1: Understanding Layer Caching
**Problem**: Initial builds were slow because I copied all files first.

**Solution**: Researched Docker layer caching, learned dependencies change less than code. Reordered to copy requirements.txt separately. Now rebuilds are fast (only code layer changes).

### Challenge 2: Choosing Base Image
**Problem**: Confused between slim, alpine, and full images.

**Solution**: Tested all three:
- Full (1GB) - too large
- Alpine (60MB) - some pip packages failed (C compilation issues)
- Slim (130MB) - perfect balance of size and compatibility

Chose slim for production reliability.

### Challenge 3: Non-Root User Implementation
**Problem**: Initially got permission errors when running as non-root.

**Solution**: Ensured user switch happens AFTER pip install (which needs write access). Created user with home directory (-m flag) to avoid file ownership issues.

### What I Learned

1. **Layer caching is critical** - Order matters for build speed
2. **Security by default** - Always run as non-root, pin versions
3. **Image size tradeoffs** - Smaller isn't always better (alpine compatibility issues)
4. **Docker build context** - .dockerignore prevents wasted transfers
5. **Port exposure** - EXPOSE is documentation, not enforcement (still need -p flag)

## Docker Hub Deployment

### Tagging Strategy
```bash
docker tag devops-app:1.0 kolsmer/devops-app:1.0
docker tag devops-app:1.0 kolsmer/devops-app:latest
```

Using semantic versioning with latest tag for convenience.

### Push Commands
```bash
docker login
docker push kolsmer/devops-app:1.0
docker push kolsmer/devops-app:latest
```

### Verification
```bash
docker pull kolsmer/devops-app:1.0
docker run -p 8000:8000 kolsmer/devops-app:1.0
```

---

**Lab 2 Completed:** Containerized FastAPI application following Docker best practices with comprehensive understanding of security, optimization, and production readiness.
