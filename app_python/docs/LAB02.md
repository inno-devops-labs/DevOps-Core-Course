# Lab 2 — Docker Containerization

## Docker Best Practices Applied

### 1. Non-Root User
**Implementation:**
```dockerfile
RUN groupadd -r appuser && useradd -r -g appuser appuser
USER appuser
```

**Why it matters:** Running containers as root is a security risk. If an attacker exploits a vulnerability in the application, they would have root access to the container and potentially the host system. A non-root user limits the damage an attacker can do, following the principle of least privilege.

### 2. Specific Base Image Version
**Implementation:**
```dockerfile
FROM python:3.13-slim
```

**Why it matters:** Using a specific version (3.13-slim) instead of `latest` ensures reproducibility. The build will produce the same result months from now, avoiding breaking changes from automatic updates. The `slim` variant reduces image size by excluding unnecessary packages.

### 3. Layer Caching with Proper Ordering
**Implementation:**
```dockerfile
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app.py .
```

**Why it matters:** Dependencies change less frequently than application code. By copying `requirements.txt` first and installing packages before copying the app, Docker can cache the expensive dependency installation layer. When you modify `app.py`, only the final COPY layer rebuilds, making subsequent builds much faster.

### 4. .dockerignore File
**Implementation:** Created `.dockerignore` to exclude:
- Python cache files (`__pycache__`, `*.pyc`)
- Virtual environments (`venv`, `.venv`)
- Version control (`.git`)
- Documentation and tests
- IDE configuration files

**Why it matters:** Reducing the build context improves build speed by sending less data to the Docker daemon. It also prevents sensitive files from accidentally being included in the image. Smaller context = faster builds.

### 5. No Cache for Pip Install
**Implementation:**
```dockerfile
RUN pip install --no-cache-dir -r requirements.txt
```

**Why it matters:** The `--no-cache-dir` flag prevents pip from storing downloaded packages in the layer, reducing the final image size by ~5-10MB. Since the image is immutable, we don't need pip's cache.

### 6. Explicit File Copying
**Implementation:** Only copied necessary files (`requirements.txt` and `app.py`) instead of using `COPY . .`

**Why it matters:** This prevents unnecessary files from bloating the image and ensures we only include what's needed for the application to run. Even with `.dockerignore`, explicit copying is more secure and predictable.

### 7. Proper Ownership
**Implementation:**
```dockerfile
RUN chown -R appuser:appuser /app
```

**Why it matters:** After copying files as root, we need to change ownership so the non-root user can read them. Without this, the application would fail to start due to permission errors.

## Image Information & Decisions

### Base Image Choice
**Selected:** `python:3.13-slim`

**Justification:**
- **python:3.13-slim**: Latest stable Python with minimal system packages
- **Size:** ~170MB base vs ~1GB for full python:3.13
- **Security:** Fewer packages = smaller attack surface
- **Alternative considered:** python:3.13-alpine (~50MB base) was rejected because alpine uses musl libc which can cause compatibility issues with some Python packages and has slower builds due to compiling many packages from source

### Final Image Size
- **Disk Usage:** 221MB
- **Content Size:** 48MB
- **Assessment:** Excellent size for a Python web application. The majority is the Python runtime itself (~170MB). Our application layer adds only ~50MB, which includes Flask and its dependencies (~15MB) plus the application code (<1MB).

### Layer Structure
```
Base: python:3.13-slim      ~170MB
WORKDIR /app                   8KB
Create user                   41KB
Copy requirements.txt         12KB
Install dependencies        15.2MB
Copy app.py                   12KB
Change ownership              16KB
Metadata (USER, EXPOSE, CMD)   0B
-----------------------------------
Total                        ~221MB
```

The layer order optimizes for caching: dependencies are installed before application code, so code changes don't trigger dependency reinstallation.

### Optimization Choices
1. **Used python:3.13-slim over full image:** Saved ~800MB
2. **Used --no-cache-dir for pip:** Saved ~8MB
3. **Only copied necessary files:** Prevented bloat from docs, tests, git history
4. **Didn't use alpine:** Avoided build time complexity and potential compatibility issues

## Build & Run Process

### Build Output
```
$ docker build -t devops-info-service:latest app_python/

[+] Building 29.3s (13/13) FINISHED
 => [internal] load build definition from Dockerfile
 => [internal] load metadata for docker.io/library/python:3.13-slim
 => [1/7] FROM docker.io/library/python:3.13-slim
 => [2/7] WORKDIR /app
 => [3/7] RUN groupadd -r appuser && useradd -r -g appuser appuser
 => [4/7] COPY requirements.txt .
 => [5/7] RUN pip install --no-cache-dir -r requirements.txt
 => [6/7] COPY app.py .
 => [7/7] RUN chown -R appuser:appuser /app
 => exporting to image
 => naming to docker.io/library/devops-info-service:latest
```

### Container Running
```
$ docker run -d -p 5001:5000 --name devops-test devops-info-service:latest
81f3f521073ec1e8d1bffb4d4793e02bdee212529e06e6b283d099133f6fbfaf

$ docker ps
CONTAINER ID   IMAGE                          COMMAND           CREATED         STATUS         PORTS                    NAMES
81f3f521073e   devops-info-service:latest     "python app.py"   8 seconds ago   Up 7 seconds   0.0.0.0:5001->5000/tcp   devops-test
```

### Testing Endpoints
```
$ curl -s http://localhost:5001/ | python3 -m json.tool
{
    "service": {
        "name": "devops-info-service",
        "version": "1.0.0",
        "description": "DevOps course info service",
        "framework": "Flask"
    },
    "system": {
        "hostname": "81f3f521073e",
        "platform": "Linux",
        "platform_version": "Linux-6.12.65-linuxkit-aarch64-with-glibc2.41",
        "architecture": "aarch64",
        "cpu_count": 11,
        "python_version": "3.13.11"
    },
    "runtime": {
        "uptime_seconds": 8,
        "uptime_human": "0 hours, 0 minutes",
        "current_time": "2026-02-04T20:13:05.040693+00:00",
        "timezone": "UTC"
    },
    "request": {
        "client_ip": "151.101.64.223",
        "user_agent": "curl/8.7.1",
        "method": "GET",
        "path": "/"
    }
}

$ curl -s http://localhost:5001/health | python3 -m json.tool
{
    "status": "healthy",
    "timestamp": "2026-02-04T20:13:05.084113+00:00",
    "uptime_seconds": 8
}
```

**Verification:** The application works identically in the container as it did locally. The hostname changed to the container ID, and the platform shows Linux (container OS) instead of the host OS, confirming proper containerization.

### Docker Hub Repository
URL: `https://hub.docker.com/r/<username>/devops-info-service`

*(Will be updated after push)*

## Technical Analysis

### Why This Dockerfile Works

1. **Base Image Selection:** python:3.13-slim provides the Python runtime with minimal overhead. It includes pip and essential libraries but excludes documentation, compilers, and other development tools.

2. **Layer Order Strategy:** 
   - Static/slow-changing layers first (user creation, dependency installation)
   - Dynamic/fast-changing layers last (application code)
   - This maximizes Docker's layer cache effectiveness

3. **Security Through Non-Root:** The application runs as `appuser`, not root. Even if an attacker exploits the Flask app, they can't:
   - Install system packages
   - Modify system files
   - Access other containers with elevated privileges
   - Easily escalate to root access

### What Would Happen If Layer Order Changed?

**Bad Order:**
```dockerfile
COPY app.py .
COPY requirements.txt .
RUN pip install -r requirements.txt
```

**Impact:** Every time you modify `app.py` (which happens frequently), Docker invalidates the cache for all subsequent layers. This means:
- Dependencies reinstall on every code change (~30 seconds wasted)
- Build time increases from <1s to ~30s for simple code changes
- Developer productivity decreases
- CI/CD pipelines run slower

**Current Order:** Changing `app.py` only rebuilds the final COPY layer (<1 second), because the dependency layer is cached.

### Security Considerations Implemented

1. **Non-Root User:** Limits blast radius of potential exploits
2. **Specific Image Version:** Prevents supply chain attacks from malicious `latest` tag updates
3. **Minimal Base Image:** Fewer packages = fewer potential vulnerabilities
4. **No Unnecessary Files:** .dockerignore prevents secrets, keys, or sensitive data from being copied
5. **Read-Only Application:** Non-root user can't modify system files or install malware

### How .dockerignore Improves the Build

**Without .dockerignore:**
- Docker sends entire directory (~10MB+ with venv, git, cache) to daemon
- Unnecessary files could be copied into image
- Build context transfer takes longer
- Risk of including sensitive files

**With .dockerignore:**
- Docker sends only necessary files (~3KB)
- Build context transfer is instant
- Impossible to accidentally include venv or .git
- Cleaner, more predictable builds

**Proof:** Build context in our output shows only necessary files were sent:
```
[internal] load build context
transferring context: 3.15kB done
```

## Challenges & Solutions

### Challenge 1: Port Already in Use
**Issue:** Initial container run failed with "port 5000: bind: address already in use"

**Solution:** Used different host port mapping (`-p 5001:5000`) to avoid conflict with existing service on port 5000. This demonstrates Docker's port mapping flexibility - the container still listens on 5000 internally, but is accessible on the host via 5001.

**Learning:** Always check for port conflicts. Use `docker ps` or `lsof -i :5000` to see what's using a port.

### Challenge 2: Understanding Slim vs Alpine
**Issue:** Debated between python:3.13-slim and python:3.13-alpine

**Solution:** Chose slim after researching trade-offs:
- Alpine is smaller (~50MB) but uses musl libc instead of glibc
- Many Python packages with C extensions need to be compiled from source on Alpine
- Compilation increases build time significantly (minutes vs seconds)
- Some packages have compatibility issues with musl
- Slim provides the best balance of size and compatibility for Python apps

**Learning:** Smaller isn't always better. Alpine is great for statically-compiled languages (Go, Rust) but problematic for Python.

### Challenge 3: Layer Caching Optimization
**Issue:** Initially copied all files together, causing unnecessary rebuilds

**Solution:** Separated dependency installation from code copying:
```dockerfile
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app.py .
```

**Learning:** Think about change frequency when ordering Dockerfile instructions. Put things that change rarely at the top, things that change often at the bottom.

### Challenge 4: Permission Errors with Non-Root User
**Issue:** After switching to non-root user, initially got permission errors

**Solution:** Added `chown` command to give ownership of /app to appuser before switching users:
```dockerfile
RUN chown -R appuser:appuser /app
USER appuser
```

**Learning:** Files copied while root remain root-owned. You must explicitly change ownership before switching users, or the application won't be able to read its own files.

## Conclusion

This lab demonstrated that containerization is not just about "wrapping an app in Docker" - it requires understanding:
- Security principles (least privilege, minimal attack surface)
- Build optimization (layer caching, build context)
- Image size trade-offs (slim vs alpine vs full)
- Runtime considerations (permissions, ports, user management)

The final image is production-ready: secure (non-root), optimized (proper layer ordering), and minimal (221MB). It builds quickly thanks to caching and runs identically regardless of the host environment.
