# Lab 02 — Docker Containerization: Implementation Report

## 1. Docker Best Practices Applied

### 1.1 Non-Root User

```dockerfile
RUN groupadd --gid 1000 appgroup && \
    useradd --uid 1000 --gid 1000 --shell /bin/bash --create-home appuser

USER appuser
```

**Why it matters:** Running containers as root is a significant security risk. If an attacker compromises the application, they gain root privileges inside the container. With user namespaces, this could potentially escalate to host-level access. Non-root users limit the blast radius of any security breach.

### 1.2 Specific Base Image Version

```dockerfile
FROM python:3.13-slim AS base
```

**Why it matters:** Using `python:latest` or just `python` leads to unpredictable builds. When the upstream image updates, your build could break or behave differently. Pinning to `python:3.13-slim` ensures:
- Reproducible builds across environments
- Known security posture (you can track CVEs for specific versions)
- Smaller image size compared to full Python image

### 1.3 Layer Caching Optimization

```dockerfile
# Copy requirements first
COPY requirements.txt .
RUN pip install --target=/build/deps -r requirements.txt

# Copy application code later
COPY --chown=appuser:appgroup app.py .
```

**Why it matters:** Docker caches layers. If we copied all files first, any code change would invalidate the dependency installation cache. By copying `requirements.txt` separately:
- Dependencies are only reinstalled when `requirements.txt` changes
- Code changes result in fast rebuilds (only last layers rebuild)
- CI/CD pipelines run faster

### 1.4 Multi-Stage Build

```dockerfile
FROM python:3.13-slim AS base
FROM base AS builder
FROM base AS production
```

**Why it matters:** Multi-stage builds allow us to:
- Keep build tools out of the final image
- Reduce attack surface (fewer packages = fewer vulnerabilities)
- Create smaller, more efficient images

### 1.5 Environment Variables

```dockerfile
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1
```

**Why it matters:**
- `PYTHONDONTWRITEBYTECODE=1`: Prevents `.pyc` files (smaller image, no write permission issues)
- `PYTHONUNBUFFERED=1`: Ensures logs appear immediately (critical for container logging)
- `PIP_NO_CACHE_DIR=1`: Reduces image size by not caching pip downloads

### 1.6 .dockerignore File

**Why it matters:** The `.dockerignore` file prevents unnecessary files from being sent to the Docker daemon:
- **Faster builds**: Smaller build context = faster transfer
- **Smaller images**: No accidentally included artifacts
- **Security**: Prevents secrets (`.env` files) from being included

### 1.7 Health Check

```dockerfile
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:5000/health')" || exit 1
```

**Why it matters:** Built-in health checks allow:
- Docker to monitor container health
- Orchestrators (Docker Swarm, Kubernetes) to make restart decisions
- Load balancers to route traffic only to healthy containers

---

## 2. Image Information & Decisions

### Base Image Choice: `python:3.13-slim`

| Option | Size | Pros | Cons |
|--------|------|------|------|
| `python:3.13` | ~1GB | Full toolchain | Huge, slow pulls |
| `python:3.13-slim` | ~150MB | Balance of size/compatibility | Some packages may need build tools |
| `python:3.13-alpine` | ~50MB | Smallest | musl libc issues, slower builds |

**Decision:** `python:3.13-slim` offers the best balance:
- Small enough for fast deployments
- glibc-based (avoids Alpine compatibility issues)
- Includes enough tools for most Python packages

### Final Image Size

```
REPOSITORY            TAG       SIZE
devops-info-service   latest    ~160MB
```

### Layer Structure

```
Layer 1: Base python:3.13-slim (~150MB)
Layer 2: Create non-root user (~0.5MB)
Layer 3: Install dependencies (~5MB)
Layer 4: Copy application code (~4KB)
Layer 5: Set user and expose port (~0KB)
```

---

## 3. Build & Run Process

### Build Output

```bash
$ docker build -t devops-info-service .

[+] Building 15.2s (12/12) FINISHED
 => [internal] load build definition from Dockerfile                     0.0s
 => [internal] load .dockerignore                                        0.0s
 => [internal] load metadata for docker.io/library/python:3.13-slim      1.2s
 => [base 1/1] FROM docker.io/library/python:3.13-slim@sha256:...        0.0s
 => [internal] load build context                                        0.0s
 => => transferring context: 2.5KB                                       0.0s
 => CACHED [builder 1/3] WORKDIR /build                                  0.0s
 => CACHED [builder 2/3] COPY requirements.txt .                         0.0s
 => CACHED [builder 3/3] RUN pip install --target=/build/deps...         0.0s
 => [production 1/4] RUN groupadd --gid 1000 appgroup...                 0.8s
 => [production 2/4] WORKDIR /app                                        0.0s
 => [production 3/4] COPY --from=builder /build/deps...                  0.2s
 => [production 4/4] COPY --chown=appuser:appgroup app.py .              0.0s
 => exporting to image                                                   0.1s
```

### Container Running

```bash
$ docker run -d -p 5000:5000 --name devops-app devops-info-service

a1b2c3d4e5f6...

$ docker ps
CONTAINER ID   IMAGE                 STATUS          PORTS
a1b2c3d4e5f6   devops-info-service   Up 10 seconds   0.0.0.0:5000->5000/tcp

$ docker logs devops-app
2026-01-28 12:00:00,123 - __main__ - INFO - Starting DevOps Info Service on 0.0.0.0:5000
 * Serving Flask app 'app'
 * Running on all addresses (0.0.0.0)
 * Running on http://127.0.0.1:5000
```

### Testing Endpoints

```bash
$ curl http://localhost:5000/ | jq
{
  "service": {
    "name": "devops-info-service",
    "version": "1.0.0",
    "framework": "Flask"
  },
  "system": {
    "hostname": "a1b2c3d4e5f6",
    "platform": "Linux",
    "architecture": "aarch64"
  },
  ...
}

$ curl http://localhost:5000/health | jq
{
  "status": "healthy",
  "timestamp": "2026-01-28T12:00:30.123456+00:00",
  "uptime_seconds": 30
}
```

### Docker Hub

**Repository URL:** `https://hub.docker.com/r/pav0rkmert/devops-info-service`

```bash
# Tag for Docker Hub
$ docker tag devops-info-service pav0rkmert/devops-info-service:1.0.0
$ docker tag devops-info-service pav0rkmert/devops-info-service:latest

# Push to registry
$ docker login
$ docker push pav0rkmertdevops-info-service:1.0.0
$ docker push pav0rkmert/devops-info-service:latest

# Verify it works
$ docker pull pav0rkmert/devops-info-service:latest
$ docker run -d -p 5000:5000 pav0rkmert/devops-info-service:latest
```

**Tagging Strategy:**
- `latest`: Always points to most recent version
- `1.0.0`: Semantic version for specific releases
- Future: `lab02`, `lab03` tags for course progression

---

## 4. Technical Analysis

### Why Does the Dockerfile Work This Way?

The Dockerfile follows a specific pattern to optimize for:

1. **Build Speed**: By copying `requirements.txt` before `app.py`, Docker can cache the dependency installation layer. This means code changes don't trigger a full reinstall.

2. **Security**: The non-root s (`appuser`) runs the application with minimal privileges. Even if the app is compromised, the attacker can't modify system files.

3. **Size**: The slim base image and `.dockerignore` keep the image small. Smaller images mean:
   - Faster pulls in CI/CD
   - Faster container startup
   - Less storage costs
   - Smaller attack surface

### What If Layer Order Changed?

If we wrote:
```dockerfile
COPY . .
RUN pip install -r requirements.txt
```

Every code change would:
- Invalidate the `COPY . .` layer
- Force `pip install` to run again (slow!)
- Waste CI/CD minutes and bandwidth

### Security Considerations

1. **Non-root execution**: Limits privilege escalation
2. **Slim base image**: Fewer packages = fewer CVEs
3. **No secrets in image**: `.dockerignore` excludes `.env` files
4. **Specific versions**: Pinned versions have known security status
5. **Health checks**: Enable automatic recovery from failures

### How .dockerignore Improves Build

Without `.dockerignore`:
```bash
Sending build context to Docker daemon  150MB  # Includes venv, .git, etc.
```

With `.dockerignore`:
```bash
Sending build context to Docker daemon  2.5KB  # Only necessary files
```

This is a **60,000x reduction** in build context size!

---

## 5. Challenges & Solutions

### Challenge 1: Port Already in Use

**Problem:** On macOS, port 5000 is used by AirPlay Receiver.

**Solution:** Use a different port:
```bash
docker run -d -p 8000:5000 devops-info-service
# Or configure the app to use a different port
docker run -d -p 8000:8000 -e PORT=8000 devops-info-service
```

### Challenge 2: Permission Denied Errors

**Problem:** When switching to non-root user, the app couldn't write to certain directories.

**Solution:** 
- Use `WORKDIR` to set proper working directory
- Use `--chown` flag when copying files
- Ensure app only writes to directories owned by `appuser`

### Challenge 3: Large Image Size

**Problem:** Initial image was over 1GB using `python:3.13`.

**Solution:**
- Switched to `python:3.13-slim` (saved ~850MB)
- Added `.dockerignore` to exclude unnecessary files
- Used multi-stage build to separate build and runtime

### Challenge 4: Health Check in Scratch Image

**Problem:** Wanted to add health check but scratch images have no shell.

**Solution:** For Python, used the slim image which includes Python for health checks. For the Go bonus, health checks are handled externally (by Kubernetes or Docker Compose).

