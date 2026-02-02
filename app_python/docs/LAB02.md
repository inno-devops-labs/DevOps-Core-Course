# Lab 02 — Docker Containerization (Python)

## Docker Best Practices Applied

### 1. Non-Root User

**Implementation:**
```dockerfile
RUN groupadd -r appuser && useradd -r -g appuser appuser
USER appuser
```

**Why It Matters:** Running as root inside containers is a security risk. If an attacker compromises the application, they would have root privileges inside the container, which could lead to container escape or host system compromise. Non-root user limits damage from potential security breaches.

### 2. Specific Base Image Version

**Implementation:**
```dockerfile
FROM python:3.12-slim
```

**Why It Matters:** Using specific versions (not `latest`) ensures reproducible builds. The `slim` variant is 40% smaller than the full image while including everything needed for Python apps, reducing attack surface and download time.

### 3. Layer Caching Optimization

**Implementation:**
```dockerfile
# Copy requirements first
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy code after
COPY app.py .
```

**Why It Matters:** Docker caches each layer. Since dependencies change rarely but code changes often, copying requirements first means pip install only runs when dependencies change. This dramatically speeds up rebuilds during development.

### 4. Minimal File Copying

**Implementation:**
```dockerfile
COPY requirements.txt .
COPY app.py .
```

**Why It Matters:** Only copying necessary files keeps image size small and reduces attack surface. No tests, docs, or development files in production image.

### 5. .dockerignore File

**Implementation:**
```dockerignore
venv/
__pycache__/
tests/
docs/
.git/
```

**Why It Matters:** Excludes unnecessary files from build context, making builds faster and preventing accidental inclusion of sensitive files or large directories. Build context is sent to Docker daemon before build starts.

### 6. No pip Cache

**Implementation:**
```dockerfile
RUN pip install --no-cache-dir -r requirements.txt
```

**Why It Matters:** `--no-cache-dir` prevents pip from storing package cache, reducing image size by 10-20MB without affecting functionality.

## Image Information & Decisions

### Base Image: python:3.12-slim

**Justification:**
- **Version 3.12** matches development environment (Python 3.12.3)
- **slim variant** is ~50MB smaller than full image
- Includes everything needed: Python runtime, pip, essential libraries
- More secure than full image (fewer packages = smaller attack surface)

**Alternatives Considered:**
- `python:3.12-alpine` - smaller but uses musl instead of glibc, can cause compatibility issues
- `python:3.12` - full image ~350MB+ with unnecessary build tools

### Final Image Size

**Actual size: 223 MB** (compressed: 48.4 MB)

**Size Breakdown:**
- Base python:3.12-slim: ~195 MB
- Dependencies (Flask, Werkzeug): ~28 MB
- Application code: <1 MB

**Assessment:** Standard size for Python containerized application. The slim variant significantly reduces size compared to full Python image (~900+ MB).

### Layer Structure

1. Base image (python:3.12-slim)
2. User creation
3. Working directory setup
4. Requirements copy
5. Dependency installation
6. Application code copy
7. Permission changes
8. User switch
9. Environment variables
10. CMD definition

**Optimization:** Dependencies installed before code copy enables layer caching.

## Build & Run Process

### Building the Image

```bash
cd app_python
docker build -t devops-info-service-python:latest .
```

**Actual Output:**
```
#1 [internal] load build definition from Dockerfile
#1 transferring dockerfile: 841B done
#1 DONE 0.0s

#2 [internal] load metadata for docker.io/library/python:3.12-slim
#2 DONE 1.6s

#3 [internal] load .dockerignore
#3 transferring context: 434B done
#3 DONE 0.0s

#4 [1/7] FROM docker.io/library/python:3.12-slim@sha256:5e2dbd4bbdd9c0e67412aea9463906f74a22c60f89eb7b5bbb7d45b66a2b68a6
#4 CACHED

#5 [2/7] RUN groupadd -r appuser && useradd -r -g appuser appuser
#5 CACHED

#6 [3/7] WORKDIR /app
#6 CACHED

#7 [4/7] COPY requirements.txt .
#7 CACHED

#8 [5/7] RUN pip install --no-cache-dir -r requirements.txt
#8 CACHED

#9 [6/7] COPY app.py .
#9 CACHED

#10 [7/7] RUN chown -R appuser:appuser /app
#10 CACHED

#11 exporting to image
#11 exporting layers done
#11 exporting manifest sha256:a58a958ecd82e446c590402b9cd7392bc0d4bddff26a3c22e80b91aa91055f49 done
#11 naming to docker.io/library/devops-info-service-python:latest done
#11 DONE 0.0s
```

**Build Time:** ~4.5 seconds (with cache)

### Running the Container

```bash
docker run -p 8080:8080 devops-info-service-python:latest
```

**Actual Output:**
```
2026-02-02 15:12:07,860 - __main__ - INFO - Starting DevOps Info Service on 0.0.0.0:8080
2026-02-02 15:12:07,860 - __main__ - INFO - Debug mode: False
 * Serving Flask app 'app'
 * Debug mode: off
WARNING: This is a development server. Do not use it in a production deployment.
 * Running on all addresses (0.0.0.0)
 * Running on http://127.0.0.1:8080
 * Running on http://172.17.0.2:8080
Press CTRL+C to quit
```

**Container Stats:**
- Memory usage: 39.4 MiB
- CPU usage: ~0.04%
- Startup time: <1 second

### Testing Endpoints

```bash
# Main endpoint
curl http://localhost:8080/

# Health check
curl http://localhost:8080/health

# Formatted output
curl -s http://localhost:8080/ | python3 -m json.tool
```

**Response from container (main endpoint):**
```json
{
    "service": {
        "name": "devops-info-service",
        "version": "1.0.0",
        "description": "DevOps course info service",
        "framework": "Flask"
    },
    "system": {
        "hostname": "16d981980107",
        "platform": "Linux",
        "platform_version": "#1 SMP Thu Jan 15 14:58:53 UTC 2026",
        "architecture": "aarch64",
        "cpu_count": 11,
        "python_version": "3.12.12"
    },
    "runtime": {
        "uptime_seconds": 35,
        "uptime_human": "0 minutes",
        "current_time": "2026-02-02T15:12:43.167490+00:00",
        "timezone": "UTC"
    }
}
```

### Docker Hub

**Repository URL:** `https://hub.docker.com/r/aezuraa/devops-info-service`

**Tagging Strategy:**

Format: `username/repository:tag`
- `aezuraa` - Docker Hub username (required for push)
- `devops-info-service` - Repository name (consistent across all implementations)
- `python` - Language-specific tag (distinguishes from Go variant)

**Why This Strategy:**
- **Descriptive tags:** `:python` and `:go` clearly identify implementation language
- **Single repository:** Both variants under one repo simplifies management
- **Semantic versioning ready:** Can add version tags later (e.g., `:python-v1.0`)
- **Production pattern:** Mirrors real-world multi-variant container naming

**Tag & Push Commands:**
```bash
docker tag devops-info-service-python:latest aezuraa/devops-info-service:python
docker login
docker push aezuraa/devops-info-service:python
```

**Push Output:**
```
The push refers to repository [docker.io/aezuraa/devops-info-service]
140d16322bf1: Pushed
d4dcd3efa12a: Pushed
5d39345861c8: Pushed
63cf2d5f63ab: Pushed
d637807aba98: Pushed
06e3a4e15303: Pushed
62f081338475: Pushed
1b3d94f08ecc: Pushed
ec212aae491c: Pushed
9f5ca0a479a5: Pushed
9c4374a520cb: Pushed
python: digest: sha256:d6ddca86964d8b2082edf1f285d5b8e072e7bd70f9ea70cb0133df3c911530c4 size: 856
```

**Pull & Test:**
```bash
docker pull aezuraa/devops-info-service:python
docker run -p 8080:8080 aezuraa/devops-info-service:python
```

## Technical Analysis

### Why This Dockerfile Works

1. **Base Image Foundation:** Uses official Python slim image which includes Python runtime and pip pre-configured.

2. **Security Through User Isolation:** Non-root user prevents privilege escalation attacks and follows principle of least privilege.

3. **Build Performance:** Layer caching means only changed layers rebuild. Code changes don't trigger dependency reinstall.

4. **Minimal Attack Surface:** Only production files included, no development tools or documentation.

### What Would Happen If Layer Order Changed?

**Bad Order (dependencies after code):**
```dockerfile
COPY app.py .
COPY requirements.txt .
RUN pip install -r requirements.txt
```

**Problem:** Every code change would invalidate the pip install layer, causing full dependency reinstall on every build. This wastes time and bandwidth.

**Good Order (current):**
```dockerfile
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY app.py .
```

**Benefit:** Code changes don't trigger dependency reinstall. Docker reuses cached pip layer.

### Security Considerations

1. **Non-Root Execution:** Limits damage from application vulnerabilities
2. **Specific Version Tags:** Prevents unexpected base image updates
3. **Minimal Dependencies:** Only Flask and Werkzeug, no unnecessary packages
4. **No Secrets in Image:** Environment variables provided at runtime
5. **Slim Base Image:** Fewer packages = fewer potential vulnerabilities

### How .dockerignore Improves Build

**Without .dockerignore:**
- Docker sends entire directory to daemon (~70MB with venv, docs, tests)
- Slower builds due to large context transfer
- Risk of including sensitive files accidentally

**With .dockerignore:**
- Only sends necessary files (requirements.txt + app.py = ~5KB)
- Faster builds (especially over network)
- Impossible to accidentally include venv or .git

**Impact:** Build context reduced dramatically, improving build speed and security.

## Challenges & Solutions

### Challenge 1: Permission Errors

**Problem:** Application tried to write logs but had no permission as non-root user.

**Solution:** Changed ownership before switching user:
```dockerfile
RUN chown -R appuser:appuser /app
USER appuser
```

### Challenge 2: Choosing Base Image

**Problem:** Multiple Python image variants available - full, slim, alpine.

**Solution:** Chose `python:3.12-slim` because:
- Smaller than full (130MB vs 350MB+)
- More compatible than alpine (uses glibc, not musl)
- Includes pip and essential libraries

### Challenge 3: Layer Ordering

**Problem:** Initial naive ordering caused slow rebuilds on code changes.

**Solution:** Studied Docker layer caching and placed requirements.txt copy before app code copy. Now code changes don't invalidate dependency layer.

## Implementation Summary

Successfully containerized Python DevOps Info Service with:
- Secure non-root execution
- Optimized layer structure for fast rebuilds
- Minimal image size using slim base
- Production-ready Dockerfile following best practices
- Complete .dockerignore for efficient builds

Image can be pulled from Docker Hub and deployed anywhere Docker runs.
