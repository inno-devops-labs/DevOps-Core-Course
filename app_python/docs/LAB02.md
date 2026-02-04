# Lab 2 — Docker Containerization

This document details the implementation of Docker containerization for the DevOps Info Service.

## Docker Best Practices Applied

### 1. Non-Root User

**Practice:** The container runs as a non-root user named `appuser`.

**Why This Matters:**
Running containers as root is a significant security risk. If an attacker compromises the application, they gain root access to the container filesystem. While containers provide isolation, it's not perfect—container escape vulnerabilities exist. By running as a non-root user, we:
- Limit the damage potential of a compromised application
- Follow the principle of least privilege
- Prevent the app from modifying system files or configurations
- Meet security requirements for production deployments

**Dockerfile Snippet:**
```dockerfile
# Create non-root user and group
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Set proper ownership
RUN chown -R appuser:appuser /app

# Switch to non-root user
USER appuser
```

### 2. Specific Base Image Version

**Practice:** Using `python:3.13-slim` instead of `python:latest` or `python:3`.

**Why This Matters:**
- **Reproducibility:** Using `latest` means the image can change unexpectedly, breaking builds
- **Security:** We know exactly which base image we're using and can track vulnerabilities
- **Predictability:** Team members get identical builds regardless of when they pull
- **Debugging:** Easier to trace issues to specific base image versions

**Dockerfile Snippet:**
```dockerfile
FROM python:3.13-slim
```

The `slim` variant provides a minimal Debian Linux base with Python pre-installed, reducing the image size significantly compared to the full `python` image while still being compatible with most Python packages.

### 3. Layer Caching Optimization

**Practice:** Copying `requirements.txt` separately from application code.

**Why This Matters:**
Docker builds images in layers, and each layer is cached. When rebuilding, Docker only rebuilds layers that changed. By copying `requirements.txt` first and installing dependencies before copying the application code:
- Dependency installation is cached if `requirements.txt` doesn't change
- Code changes don't trigger reinstallation of all dependencies
- Build times are significantly faster during development

**Dockerfile Snippet:**
```dockerfile
# Copy requirements first
COPY requirements.txt .

# Install dependencies (cached layer)
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code (changes frequently)
COPY app.py .
```

**What Happens If We Change the Order:**
If we copy all files first and then install dependencies, any code change would invalidate the cache for the dependency installation layer, causing all packages to be reinstalled every time—even if `requirements.txt` didn't change.

### 4. Python Environment Variables

**Practice:** Setting `PYTHONDONTWRITEBYTECODE` and `PYTHONUNBUFFERED`.

**Why This Matters:**
- `PYTHONDONTWRITEBYTECODE=1`: Prevents Python from writing `.pyc` files. These aren't needed in containers (the code doesn't change after build) and would just waste space and potential permission issues since the user might not have write access.
- `PYTHONUNBUFFERED=1`: Forces stdout/stderr to be unbuffered. This ensures logs appear immediately when viewing container logs, which is critical for monitoring and debugging.

**Dockerfile Snippet:**
```dockerfile
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1
```

### 5. .dockerignore File

**Practice:** Excluding unnecessary files from the build context.

**Why This Matters:**
The Docker build context includes all files in the directory when sending to the Docker daemon. Without `.dockerignore`:
- Large files slow down builds (even if they're not used in the image)
- Development artifacts (`.venv`, `__pycache__`) get copied unnecessarily
- Sensitive files might accidentally be included
- Build context transfer takes longer

**Excluded Files:**
- Virtual environments (`venv/`, `.venv/`) — not needed in container
- Python cache (`__pycache__/`, `*.pyc`) — generated at runtime
- Git data (`.git/`) — not needed in container
- IDE files (`.vscode/`, `.idea/`) — development only
- Documentation (`docs/`, `README.md`) — not needed at runtime
- Test files (`tests/`, `.pytest_cache/`) — not running tests in container
- OS files (`.DS_Store`) — unnecessary

**Impact on Build Speed:**
Without `.dockerignore`, the build context would include gigabytes of data (especially `.venv/`). With it, only the essential files (`app.py`, `requirements.txt`) are sent, making builds nearly instantaneous.

### 6. Health Check

**Practice:** Implementing a `HEALTHCHECK` directive.

**Why This Matters:**
- Docker can track container health status
- Orchestrators (Kubernetes, Docker Swarm) can restart unhealthy containers
- Provides automated monitoring beyond just "is the process running?"
- The `/health` endpoint is specifically designed for this purpose

**Dockerfile Snippet:**
```dockerfile
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:5000/health')" || exit 1
```

Parameters:
- `--interval=30s`: Check health every 30 seconds
- `--timeout=3s`: Fail if check takes longer than 3 seconds
- `--start-period=5s`: Wait 5 seconds before starting checks (gives app time to start)
- `--retries=3`: Mark as unhealthy only after 3 consecutive failures

### 7. Minimal File Copying

**Practice:** Only copying necessary files (`app.py` and `requirements.txt`).

**Why This Matters:**
- Smaller image size (faster pulls, less storage)
- Clearer dependency tracking (we know exactly what's in the image)
- Faster builds (less context to transfer)
- Security (fewer files means smaller attack surface)

### 8. No Cache for pip

**Practice:** Using `--no-cache-dir` with pip install.

**Why This Matters:**
- pip caches downloaded packages by default
- This cache is unnecessary in the final image
- Removing it reduces image size
- We can always redownload packages if needed during rebuild

## Image Information & Decisions

### Base Image Choice

**Selected:** `python:3.13-slim`

**Justification:**

| Option | Size | Pros | Cons | Decision |
|--------|------|------|------|----------|
| `python:latest` | ~1GB | Always newest | Unpredictable, breaks builds | ❌ Avoided |
| `python:3.13` | ~1GB | Full tools included | Large, includes build tools | ❌ Unnecessary |
| `python:3.13-slim` | ~208MB | Good size, Debian base | Still has some extras | ✅ **Chosen** |
| `python:3.13-alpine` | ~50MB | Very small | musl libc, can break packages | ❌ Compatibility risk |

**Why slim over alpine:**
- Alpine uses musl libc instead of glibc, which can cause issues with some Python packages (especially those with C extensions)
- `slim` is based on Debian, providing better compatibility
- The size difference (208MB vs ~50MB) is acceptable for the compatibility gain
- `slim` images are well-tested and widely used in production

### Final Image Size

**Final Size:** 208MB

**Assessment:** This is a reasonable size for a Python web service. The breakdown:
- Base python:3.13-slim image: ~190MB
- Flask + Werkzeug: ~18MB
- Our application code: <1MB

**Optimization Choices Made:**
1. Used `slim` variant instead of full image (saves ~400MB)
2. Used `--no-cache-dir` for pip (saves ~10-20MB)
3. `.dockerignore` prevents unnecessary files from being copied (saves build context time)
4. Single-stage build is appropriate here since Python doesn't need compilation

### Layer Structure

The Dockerfile creates the following layers (in order):

1. **Base image layer** (190MB) — `FROM python:3.13-slim`
2. **Working directory** — `WORKDIR /app`
3. **User creation** — `RUN groupadd... && useradd...`
4. **Requirements copy** — `COPY requirements.txt .`
5. **Dependency installation** — `RUN pip install...` (~18MB, cached)
6. **Application copy** — `COPY app.py .`
7. **Ownership change** — `RUN chown -R appuser:appuser /app`
8. **User switch** — `USER appuser`
9. **Metadata** — `EXPOSE 5000`, `ENV`, `HEALTHCHECK`, `CMD`

**Layer Order Strategy:**
- Frequently changing layers (code copy) are placed last
- Rarely changing layers (base image, dependencies) are placed first
- This maximizes cache utilization during development

## Build & Run Process

### Building the Image

```bash
$ docker build -t devops-info-service:latest .
[+] Building 10.6s (12/12) FINISHED          docker:desktop-linux
 => [internal] load build definition from Dockerfile         0.0s
 => => transferring dockerfile: 1.44kB                       0.0s
 => [internal] load metadata for docker.io/library/python:3  4.7s
 => [internal] load .dockerignore                            0.0s
 => => transferring context: 625B                            0.0s
 => [1/7] FROM docker.io/library/python:3.13-slim@sha256:2b  2.4s
 => => resolve docker.io/library/python:3.13-slim@sha256:2b  0.0s
 => => sha256:97fc85b49690b12f13f53067a3190e231 250B / 250B  0.4s
 => => sha256:a6866fe8c3d2436d6a24f7d829ac 7.34MB / 11.72MB  5.8s
 => => sha256:fe9a90620d58e0d94bd1a536412e6 1.27MB / 1.27MB  0.9s
 => => sha256:3ea009573b472d108af9af31ec35a06fe3 30.14MB / 30.14MB  1.9s
 => => extracting sha256:3ea009573b472d108af9af31ec35a06fe3  0.3s
 => => extracting sha256:fe9a90620d58e0d94bd1a536412e60ddaf  0.0s
 => => extracting sha256:a6866fe8c3d2436d6a24f7d829aca83497  0.1s
 => => extracting sha256:97fc85b49690b12f13f53067a3190e2317  0.0s
 => [internal] load build context                            0.0s
 => => transferring context: 3.86kB                          0.0s
 => [2/7] WORKDIR /app                                       0.1s
 => [3/7] RUN groupadd -r appuser && useradd -r -g appuser   0.1s
 => [4/7] COPY requirements.txt .                            0.0s
 => [5/7] RUN pip install --no-cache-dir -r requirements.tx  2.9s
 => [6/7] COPY app.py .                                      0.0s
 => [7/7] RUN chown -R appuser:appuser /app                  0.1s
 => exporting to image                                       0.2s
 => => exporting layers                                      0.1s
 => => exporting manifest sha256:29b12cb1f0da2e3787a13c7775  0.0s
 => => exporting config sha256:1654f3599de7eb438585ff6fbdfb  0.0s
 => => exporting attestation manifest sha256:da002a7481854d  0.0s
 => => exporting manifest list sha256:69bf22bf11c5ef5ebd929  0.0s
 => => naming to docker.io/library/devops-info-service:late  0.0s
 => => unpacking to docker.io/library/devops-info-service:l  0.0s

View build details: docker-desktop://dashboard/build/desktop-linux/desktop-linux/vhcdnf0871muo18440xrk00zn
```

**Key Observations:**
- Build context transfer: only 3.86kB (thanks to `.dockerignore`)
- Build time: ~10 seconds (mostly pulling base image and installing dependencies)
- Successfully created image: `devops-info-service:latest`

### Checking Image Size

```bash
$ docker images devops-info-service:latest
REPOSITORY            TAG       IMAGE ID       CREATED         SIZE
devops-info-service   latest    69bf22bf11c5   7 seconds ago   208MB
```

### Running the Container

```bash
$ docker run -d -p 5000:5000 --name devops-info-test devops-info-service:latest
b806048178bb4454b614a9622a8279f0900e3d76021eb7a14aaef85837b0772b
```

### Testing Endpoints

**Main Endpoint (/):**

```bash
$ curl -s http://localhost:5000/ | python3 -m json.tool
{
    "endpoints": [
        {
            "description": "Service information",
            "method": "GET",
            "path": "/"
        },
        {
            "description": "Health check",
            "method": "GET",
            "path": "/health"
        }
    ],
    "request": {
        "client_ip": "151.101.128.223",
        "method": "GET",
        "path": "/",
        "user_agent": "curl/8.7.1"
    },
    "runtime": {
        "current_time": "2026-02-04T16:27:13.602670+00:00",
        "timezone": "UTC",
        "uptime_human": "8 seconds",
        "uptime_seconds": 8
    },
    "service": {
        "description": "DevOps course info service",
        "framework": "Flask",
        "name": "devops-info-service",
        "version": "1.0.0"
    },
    "system": {
        "architecture": "aarch64",
        "cpu_count": 10,
        "hostname": "b806048178bb",
        "platform": "Linux",
        "platform_version": "#1 SMP Thu Aug 14 19:26:13 UTC 2025",
        "python_version": "3.13.11"
    }
}
```

**Health Endpoint (/health):**

```bash
$ curl -s http://localhost:5000/health | python3 -m json.tool
{
    "status": "healthy",
    "timestamp": "2026-02-04T16:27:20.201348+00:00",
    "uptime_seconds": 14
}
```

### Verifying Non-Root User

```bash
$ docker exec devops-info-test whoami
appuser
```

**Important:** The container runs as `appuser`, not root. This is critical for security.

### Checking Container Health

```bash
$ docker inspect --format='{{.State.Health.Status}}' devops-info-test
healthy
```

## Docker Hub Repository

**Repository URL:** https://hub.docker.com/r/ellilin/devops-info-service

**Push Commands Used:**

```bash
# Tag the image for Docker Hub
docker tag devops-info-service:latest ellilin/devops-info-service:v1.0.0
docker tag devops-info-service:latest ellilin/devops-info-service:latest

# Push to Docker Hub
docker push ellilin/devops-info-service:v1.0.0
docker push ellilin/devops-info-service:latest
```

**Push Output:**

```bash
$ docker push ellilin/devops-info-service:v1.0.0
The push refers to repository [docker.io/ellilin/devops-info-service]
0197f7661442: Pushed
6c2f88562e39: Pushed
4f7de82a0eba: Pushed
45976a94ef4e: Pushed
d7628310951d: Pushed
e1268eaa0427: Pushed
a6866fe8c3d2: Pushed
3ea009573b47: Pushed
e09d9b48765c: Pushed
fe9a90620d58: Pushed
97fc85b49690: Pushed
v1.0.0: digest: sha256:69bf22bf11c5ef5ebd929647ac00e52c9d31a6a3fface8405595b1be764b945d size: 856
```

**Tagging Strategy:**
- `v1.0.0` — Specific version tag for reproducibility
- `latest` — Latest stable version for convenience
- Always push versioned tags alongside `latest` for production use

**Pulling the Image:**

To pull and run the image from Docker Hub:

```bash
# Pull the image
docker pull ellilin/devops-info-service:v1.0.0

# Run the container
docker run -d -p 5000:5000 --name devops-info ellilin/devops-info-service:v1.0.0

# Test it
curl http://localhost:5000/
```

## Technical Analysis

### Why Does This Dockerfile Work the Way It Does?

**The Build Process:**

1. **Base Layer Selection:** We start with `python:3.13-slim` which gives us Python 3.13 on a minimal Debian base. This provides everything needed to run a Flask application.

2. **Environment Setup:** Setting `PYTHONDONTWRITEBYTECODE` and `PYTHONUNBUFFERED` optimizes Python for containerized environments by preventing `.pyc` file generation and ensuring immediate log output.

3. **User Creation:** We create a dedicated `appuser` before copying any application files. This is important because we need root privileges to create users, but we want the application to run without them.

4. **Layer Ordering (Critical):** 
   - `requirements.txt` is copied and installed first
   - This creates a dedicated layer for dependencies
   - Only changes to `requirements.txt` invalidate this layer
   - Code changes don't trigger expensive pip installs

5. **Ownership Transfer:** After copying application files, we change ownership to `appuser:appuser`. This is critical because the next step switches to the non-root user, who needs read access to the files.

6. **User Switch:** The `USER appuser` directive makes all subsequent commands (including the `CMD` that runs the app) execute as the non-root user.

7. **Health Check:** The `HEALTHCHECK` directive tells Docker how to verify the container is healthy. It runs periodically in the container and updates the container's health status.

### What Would Happen If We Changed Layer Order?

**Scenario 1: Copy all files before installing dependencies**

```dockerfile
# BAD: Don't do this
COPY . .
RUN pip install -r requirements.txt
```

**Consequences:**
- Any change to `app.py` would invalidate the pip install layer
- Every code change would trigger reinstallation of all dependencies
- Build times would increase from seconds to minutes during development
- Docker cache would be ineffective

**Scenario 2: Switch to non-root user before setting ownership**

```dockerfile
# BAD: Don't do this
USER appuser
COPY app.py .
```

**Consequences:**
- Build would fail because `appuser` doesn't have permission to copy files
- Files copied as root would be unreadable by `appuser`
- Application would crash on startup due to permission denied errors

**Scenario 3: Use `latest` tag instead of specific version**

```dockerfile
# BAD: Don't do this
FROM python:latest
```

**Consequences:**
- Builds today use Python 3.13, tomorrow might use 3.14
- Application could break when new Python versions are released
- Impossible to reproduce exact build environment
- Security updates would be unpredictable

### Security Considerations Implemented

1. **Non-Root User:** The application runs as `appuser` with limited privileges. If an attacker exploits a vulnerability in the Flask app, they cannot:
   - Modify system files
   - Install new packages
   - Access sensitive system resources
   - Escalate privileges within the container

2. **Minimal Base Image:** Using `slim` instead of full image reduces:
   - Attack surface (fewer installed packages = fewer vulnerabilities)
   - Image size (faster deployment, smaller attack surface)
   - Unnecessary tools that could be exploited

3. **No Sensitive Data in Image:** The Dockerfile doesn't include:
   - Credentials or API keys
   - SSH keys
   - Development configurations
   - Environment-specific settings

4. **Read-Only Considerations:** For production, we could add:
   ```dockerfile
   # Make app directory read-only (app user can still read)
   # This prevents the app from modifying its own code
   ```

5. **Health Check:** Enables automated monitoring and recovery:
   - Orchestrators can restart unhealthy containers
   - Detects hung or deadlocked processes
   - Provides visibility into application health

### How Does .dockerignore Improve the Build?

**Before .dockerignore:**
```bash
$ docker build -t test .
[+] Building 30s (15/15) FINISHED
 => => transferring context: 150MB  # Takes 5-10 seconds
```

The build context would include:
- Virtual environment (~50-100MB)
- `.git` directory (~10MB)
- IDE files (~5MB)
- Python cache (~20MB)
- Documentation and tests (~5MB)

**After .dockerignore:**
```bash
$ docker build -t test .
[+] Building 10s (12/12) FINISHED
 => => transferring context: 3.86kB  # Nearly instant!
```

**Benefits:**
1. **Faster builds:** Build context transfer goes from 5-10 seconds to <0.1 seconds
2. **Smaller transfer bandwidth:** Important in CI/CD with frequent builds
3. **Cleaner builds:** Only necessary files are considered for the image
4. **Security:** Prevents accidental inclusion of sensitive files
5. **Cache efficiency:** Docker doesn't need to hash unnecessary files

**Real-World Impact:**
During development, you might build 50-100 times per day. With `.dockerignore`, you save 5-10 seconds per build = 250-1000 seconds (4-16 minutes) saved per developer per day.

## Challenges & Solutions

### Challenge 1: Choosing the Right Base Image

**Problem:** I initially considered using `python:3.13-alpine` for its tiny size (~50MB), but was concerned about compatibility.

**Research:**
- Compared size vs compatibility trade-offs
- Read about musl vs glibc issues
- Checked Flask and Werkzeug compatibility with Alpine
- Considered future dependency additions

**Solution:** Chose `python:3.13-slim` because:
- Sufficient size reduction (208MB vs 1GB for full image)
- Better compatibility (Debian base with glibc)
- Widely used and well-tested
- Worth the extra ~150MB for reliability

**Lesson:** Don't optimize for size at the cost of stability. The "slim" variants hit the sweet spot for most Python applications.

### Challenge 2: Permission Errors with Non-Root User

**Problem:** Initially, I tried to switch to the non-root user before copying files, which caused permission issues.

**Debugging Steps:**
1. Build failed with "permission denied" errors
2. Realized that `USER` directive affects subsequent COPY commands
3. Tested switching user at different points in the Dockerfile
4. Used `docker exec <container> whoami` to verify

**Solution:** Copy files as root, change ownership, then switch user:
```dockerfile
COPY app.py .
RUN chown -R appuser:appuser /app
USER appuser
```

**Lesson:** In Dockerfiles, order matters. Think about which user needs to execute each command.

### Challenge 3: Understanding Layer Caching

**Problem:** Builds were slow during development because every change triggered dependency reinstallation.

**Debugging Steps:**
1. Noticed builds took ~30 seconds even for small code changes
2. Read Docker documentation on layer caching
3. Analyzed Dockerfile to see what invalidated the cache
4. Realized I was copying all files before installing dependencies

**Solution:** Separate requirements installation from code copy:
```dockerfile
# Before (slow)
COPY . .
RUN pip install -r requirements.txt

# After (fast)
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY app.py .
```

**Impact:** Build time for code changes went from ~30 seconds to ~3 seconds.

**Lesson:** Structure Dockerfiles to maximize cache utilization. Put frequently changing content last.

### Challenge 4: Health Check Implementation

**Problem:** Needed a way to verify the container was actually running correctly, not just that the process hadn't crashed.

**Research:**
- Examined Flask application structure
- Found the `/health` endpoint
- Tested different health check approaches
- Considered using curl vs python urllib

**Solution:** Used Python's built-in urllib to avoid dependency on curl:
```dockerfile
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:5000/health')" || exit 1
```

**Lesson:** Use tools that are already available in your image. Adding curl just for health checks increases image size unnecessarily.

### What I Learned

1. **Docker is more than "package your app":** It requires thinking about:
   - Security (non-root users, minimal images)
   - Performance (layer caching, build context)
   - Operations (health checks, logging)
   - Reproducibility (specific versions, pinned dependencies)

2. **Small decisions have big impacts:**
   - Layer ordering affects build times
   - Base image choice affects size and compatibility
   - `.dockerignore` can save hours of build time over weeks

3. **Security is built-in, not added-on:**
   - Design for security from the start (non-root user)
   - Don't run as root "just to make it work"
   - Fewer files in image = smaller attack surface

4. **Docker images are layered file systems:**
   - Each RUN/COPY/ADD creates a new layer
   - Layers are cached and reused
   - Order affects which layers get invalidated

5. **Testing is critical:**
   - Verify the container runs as non-root
   - Test all endpoints
   - Check health status
   - Validate the image can be pulled and run

## Conclusion

This lab provided hands-on experience with production-ready Docker containerization. The implemented Dockerfile follows industry best practices including:

- Security (non-root user, minimal base image)
- Performance (layer caching, .dockerignore)
- Operations (health check, proper logging)
- Maintainability (clear comments, specific versions)

The final image is 208MB—a reasonable size for a Python web service with good compatibility. The container runs securely as a non-root user and can be deployed to any environment that supports Docker.

This containerized application is now ready for:
- **Lab 3:** CI/CD pipeline automation
- **Lab 7-8:** Deployment with docker-compose for logging/monitoring
- **Lab 9:** Kubernetes deployment
- **Lab 13:** GitOps with ArgoCD

The Docker knowledge gained here will be essential throughout the rest of the DevOps course.
