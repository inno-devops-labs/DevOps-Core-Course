# Lab 2 — Docker Containerization Documentation

## Overview

This document describes the Docker containerization implementation for the DevOps Info Service Python application, following Docker best practices for production-ready containers.

---

## 1. Docker Best Practices Applied

### 1.1 Non-Root User

**Implementation:**
```dockerfile
RUN groupadd -r appuser && useradd -r -g appuser appuser
...
RUN chown -R appuser:appuser /app
USER appuser
```

**Why it matters:**
Running containers as root is a significant security risk. If an attacker gains access to the container, they would have root privileges, potentially allowing them to:
- Modify system files
- Install malicious software
- Access host system resources
- Escalate privileges

By running as a non-root user (`appuser`), we follow the principle of least privilege, minimizing the attack surface and potential damage from security breaches.

### 1.2 Specific Base Image Version

**Implementation:**
```dockerfile
FROM python:3.13-slim
```

**Why it matters:**
- **Reproducibility**: Using a specific version ensures consistent builds across different environments and times
- **Predictability**: Avoids unexpected changes from base image updates
- **Security**: Allows controlled updates and vulnerability assessments
- **Size optimization**: `slim` variant is smaller than full Python images while maintaining compatibility

The `slim` variant excludes many development tools and documentation, resulting in a smaller image size (~50MB base vs ~900MB for full Python image).

### 1.3 Layer Caching Optimization

**Implementation:**
```dockerfile
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
...
COPY app.py .
```

**Why it matters:**
Docker caches layers that haven't changed. By copying `requirements.txt` and installing dependencies **before** copying application code:
- Dependencies are cached separately from code
- Code changes don't invalidate the dependency installation layer
- Faster rebuilds during development (only code layer rebuilds)
- Reduced bandwidth and build time in CI/CD pipelines

If we copied everything first, any code change would invalidate the dependency cache, forcing a full reinstall on every build.

### 1.4 .dockerignore File

**Implementation:**
Created `.dockerignore` to exclude:
- Python cache files (`__pycache__/`, `*.pyc`)
- Virtual environments (`venv/`, `.venv/`)
- IDE files (`.vscode/`, `.idea/`)
- Git files (`.git/`)
- Documentation and test files

**Why it matters:**
- **Faster builds**: Smaller build context sent to Docker daemon
- **Smaller images**: Unnecessary files don't end up in layers
- **Security**: Prevents accidentally including sensitive files (like `.env` with secrets)
- **Cleaner images**: Only runtime-necessary files are included

### 1.5 No-Cache Package Installation

**Implementation:**
```dockerfile
RUN pip install --no-cache-dir -r requirements.txt
```

**Why it matters:**
The `--no-cache-dir` flag prevents pip from storing downloaded packages in cache, reducing image size by avoiding duplicate storage of package files.

### 1.6 Proper Working Directory

**Implementation:**
```dockerfile
WORKDIR /app
```

**Why it matters:**
- Sets a consistent working directory for all subsequent commands
- Makes paths relative and cleaner
- Ensures files are organized in a predictable location
- Avoids cluttering the root filesystem

### 1.7 Environment Variables

**Implementation:**
```dockerfile
ENV HOST=0.0.0.0 \
    PORT=5000 \
    DEBUG=false
```

**Why it matters:**
- Provides sensible defaults
- Documents expected configuration
- Can be overridden at runtime without rebuilding
- Follows 12-factor app principles

---

## 2. Image Information & Decisions

### 2.1 Base Image Choice

**Selected:** `python:3.13-slim`

**Justification:**
- **Latest stable Python**: Python 3.13 provides latest features and security updates
- **Slim variant**: Significantly smaller than full Python images (~50MB vs ~900MB)
- **Production-ready**: Includes essential runtime libraries without development tools
- **Official image**: Maintained by Docker, regularly updated with security patches
- **Compatibility**: FastAPI and uvicorn work perfectly with Python 3.13

**Alternatives considered:**
- `python:3.13-alpine`: Even smaller (~15MB), but potential compatibility issues with some Python packages due to musl libc
- `python:3.13`: Full image too large for production use
- `python:3.12-slim`: Older version, less optimal but still acceptable

### 2.2 Final Image Size

**Actual sizes (measured):**
- **Docker Hub (compressed):** `55.3 MB`
- **Local image size (uncompressed):** `189.36 MB`

**Assessment:**
- Reasonable size for a Python application with FastAPI and uvicorn
- Could be further optimized with multi-stage builds, but not necessary for this application
- Acceptable trade-off between size and maintainability
- Base image layers are efficiently shared when pulled from Docker Hub (mounted layers)

### 2.3 Layer Structure

The Dockerfile creates **19 layers** total (9 base image layers + 10 application layers):

**Base image layers (python:3.13-slim):**
- Debian base, system packages, Python installation, environment variables

**Application layers:**
1. `WORKDIR /app`
2. `RUN groupadd -r appuser && useradd -r -g appuser appuser`
3. `COPY requirements.txt`
4. `RUN pip install --no-cache-dir -r requirements.txt` (largest app layer: 46.48 MB)
5. `COPY app.py`
6. `RUN chown -R appuser:appuser /app`
7. `USER appuser`
8. `EXPOSE 5000`
9. `ENV HOST=0.0.0.0 PORT=5000 DEBUG=false`
10. `CMD ["python", "app.py"]`

**Why this structure:**
- Layers that change frequently (code) are placed after layers that change rarely (dependencies)
- Dependencies are cached separately from code, enabling faster rebuilds when only code changes
- Security changes (user switch) happen after all file operations
- Base image layers are efficiently shared when pushing to Docker Hub (mounted layers)

### 2.4 Optimization Choices

**Decisions made:**
1. **Single-stage build**: Sufficient for Python application (no compilation needed)
2. **Slim base image**: Good balance of size and compatibility
3. **Layer ordering**: Optimized for cache efficiency
4. **No multi-stage**: Not necessary for interpreted language

**Trade-offs:**
- Could use Alpine for smaller size, but risk compatibility issues
- Could use distroless for security, but harder to debug
- Current approach prioritizes maintainability and compatibility

---

## 3. Build & Run Process

### 3.1 Building the Image

**Command:**
```bash
docker build -t devops-info-service:latest .
```

**Terminal Output:**
```
[+] Building 17.1s (13/13) FINISHED                                                                             docker:desktop-linux
 => [internal] load build definition from Dockerfile                                                                            0.0s
 => => transferring dockerfile: 847B                                                                                            0.0s
 => [internal] load metadata for docker.io/library/python:3.13-slim                                                             2.9s
 => [auth] library/python:pull token for registry-1.docker.io                                                                   0.0s
 => [internal] load .dockerignore                                                                                               0.0s
 => => transferring context: 420B                                                                                               0.0s
 => [1/7] FROM docker.io/library/python:3.13-slim@sha256:49b618b8afc2742b94fa8419d8f4d3b337f111a0527d417a1db97d4683cb71a6       4.3s
 => => resolve docker.io/library/python:3.13-slim@sha256:49b618b8afc2742b94fa8419d8f4d3b337f111a0527d417a1db97d4683cb71a6       0.0s
 => => sha256:49b618b8afc2742b94fa8419d8f4d3b337f111a0527d417a1db97d4683cb71a6 10.37kB / 10.37kB                                0.0s
 => => sha256:4b68e5550aece54a6200839fc1b67196ea877952680221cc4992783e9be4c504 1.75kB / 1.75kB                                  0.0s
 => => sha256:a9e0dfbfbc14c13768b5009bfa447e2f8a6c405b39e9ac64dd7431c61ae68716 5.52kB / 5.52kB                                  0.0s
 => => sha256:3ea009573b472d108af9af31ec35a06fe3649084f6611cf11f7d594b85cf7a7c 30.14MB / 30.14MB                                2.2s
 => => sha256:14c37da83ac4440d59e5d2c0f06fb6ccd1c771929bd4083c0a3cc4adf87baa79 1.27MB / 1.27MB                                  1.2s
 => => sha256:af94c6242df37e8cf3963ed59ccc0252e79a0554a8f18f4555d86f5d39116ae7 11.73MB / 11.73MB                                3.3s
 => => sha256:4c4a8dac933699cea1f21584a1e5db68e248aadadfff93ddd730bd53fbc129b5 251B / 251B                                      1.7s
 => => extracting sha256:3ea009573b472d108af9af31ec35a06fe3649084f6611cf11f7d594b85cf7a7c                                       1.2s
 => => extracting sha256:14c37da83ac4440d59e5d2c0f06fb6ccd1c771929bd4083c0a3cc4adf87baa79                                       0.1s
 => => extracting sha256:af94c6242df37e8cf3963ed59ccc0252e79a0554a8f18f4555d86f5d39116ae7                                       0.6s
 => => extracting sha256:4c4a8dac933699cea1f21584a1e5db68e248aadadfff93ddd730bd53fbc129b5                                       0.0s
 => [internal] load build context                                                                                               0.0s
 => => transferring context: 3.28kB                                                                                             0.0s
 => [2/7] WORKDIR /app                                                                                                          0.7s
 => [3/7] RUN groupadd -r appuser && useradd -r -g appuser appuser                                                              0.2s
 => [4/7] COPY requirements.txt .                                                                                               0.1s
 => [5/7] RUN pip install --no-cache-dir -r requirements.txt                                                                    8.6s
 => [6/7] COPY app.py .                                                                                                         0.0s
 => [7/7] RUN chown -R appuser:appuser /app                                                                                     0.1s
 => exporting to image                                                                                                          0.2s
 => => exporting layers                                                                                                         0.2s
 => => writing image sha256:528a2b5b01bc105a00871cc276cd02152325a8624c85bb370a8f664e614af3b1                                    0.0s
 => => naming to docker.io/library/devops-info-service:latest                                                                   0.0s

View build details: docker-desktop://dashboard/build/desktop-linux/desktop-linux/c5pay71fprb029cwajfo5avdy
```

**Analysis:**
- Build completed successfully in 17.1 seconds
- All 7 layers built successfully
- Base image pulled: `python:3.13-slim` (30.14MB base layer)
- Dependencies installation took 8.6s (longest step, as expected)
- Build context was only 3.28kB (thanks to .dockerignore)
- Final image SHA: `sha256:528a2b5b01bc105a00871cc276cd02152325a8624c85bb370a8f664e614af3b1`

### 3.2 Running the Container

**Command:**
```bash
docker run -d -p 5000:5000 --name devops-service devops-info-service:latest
```

**Terminal Output:**
```
e8054c063b0537d7407bb69768d8d288d5347b1a64558ea91238b78a6353aa00
```

**Verification:**
```bash
docker ps
```

**Output:**
```
CONTAINER ID   IMAGE                        COMMAND           CREATED             STATUS             PORTS                    NAMES
e8054c063b05   devops-info-service:latest   "python app.py"   About an hour ago   Up About an hour   0.0.0.0:5000->5000/tcp   devops-service
```

**Container Stats (from Docker Desktop):**
After running for 31 minutes, the container shows:
- **CPU usage:** ~0.38% (very low, as expected for a simple API)
- **Memory usage:** 34.29 MB out of 7.65 GB limit (minimal memory footprint)
- **Disk I/O:** 0 B read, 8.19 KB written (negligible disk activity)
- **Network I/O:** 4.42 KB received, 3.53 KB sent (minimal network traffic from health checks)

Container started successfully with ID `e8054c063b05` (short form). The application is accessible on port 5000.

**Where to check container stats:**

1. **Docker Desktop UI:**
   - Go to "Containers" tab
   - Click on container name
   - View "Stats" tab for real-time CPU, memory, disk, and network metrics

2. **Command line:**
   ```bash
   docker stats devops-service
   # Shows real-time CPU, memory, network, and disk I/O
   
   docker stats --no-stream devops-service
   # Shows one-time snapshot
   ```

3. **Container inspection:**
   ```bash
   docker inspect devops-service
   # Shows full container configuration and resource limits
   ```

### 3.3 Testing Endpoints

**Main endpoint:**
```bash
curl http://localhost:5000/
```

**Output:**
```json
{
  "service": {
    "name": "devops-info-service",
    "version": "1.0.0",
    "description": "DevOps course info service",
    "framework": "FastAPI"
  },
  "system": {
    "hostname": "e8054c063b05",
    "platform": "Linux",
    "platform_version": "#1 SMP Thu Mar 20 16:32:56 UTC 2025",
    "architecture": "aarch64",
    "cpu_count": 4,
    "python_version": "3.13.12"
  },
  "runtime": {
    "uptime_seconds": 7,
    "uptime_human": "0 hours, 0 minutes",
    "current_time": "2026-02-05T07:05:47.202218+00:00",
    "timezone": "UTC"
  },
  "request": {
    "client_ip": "192.168.65.1",
    "user_agent": "curl/8.7.1",
    "method": "GET",
    "path": "/"
  },
  "endpoints": [
    {"path": "/", "method": "GET", "description": "Service information"},
    {"path": "/health", "method": "GET", "description": "Health check"}
  ]
}
```

**Health endpoint:**
```bash
curl http://localhost:5000/health
```

**Output:**
```json
{
  "status": "healthy",
  "timestamp": "2026-02-05T07:05:47.214674+00:00",
  "uptime_seconds": 7
}
```

**Observations:**
- Application runs correctly in containerized environment
- Hostname matches container ID (`e8054c063b05`)
- Platform correctly identified as Linux
- Architecture is `aarch64` (ARM64, running on Apple Silicon Mac)
- Python version: `3.13.12` (matches base image)
- Both endpoints respond correctly with proper JSON formatting

### 3.4 Docker Hub Repository

**Repository URL:** `https://hub.docker.com/r/mclavrushka/devops-info-service`

**Tagging strategy:**
- `latest`: Most recent stable version
- Version tags: `v1.0.0`, `1.0.0` for specific releases
- Semantic versioning for production deployments

**Push commands:**
```bash
docker tag devops-info-service:latest mclavrushka/devops-info-service:latest
docker login
docker push mclavrushka/devops-info-service:latest
```

**Terminal Output:**
```
Authenticating with existing credentials... [Username: mclavrushka]

Login Succeeded

The push refers to repository [docker.io/mclavrushka/devops-info-service]
2fffa0451cb8: Pushed 
b4ff4bb0e525: Pushed 
399a27704601: Pushed 
bf1c23e5bd13: Pushed 
328902b6a9e3: Pushed 
0cabc7c6d4a9: Pushed 
30eb3ece1498: Mounted from library/python 
ba294b582463: Mounted from library/python 
ad0d17bad9cb: Mounted from library/python 
a0e71ab2b234: Mounted from library/python 
latest: digest: sha256:92806a52aa6b7b81b455324e...
```

**Analysis:**
- Successfully authenticated with Docker Hub as `mclavrushka`
- Image pushed successfully with 6 custom layers
- 4 base image layers were mounted (shared with official Python image, saving space)
- Image is now publicly available at: `docker.io/mclavrushka/devops-info-service:latest`

---

## 4. Technical Analysis

### 4.1 Why This Dockerfile Works

**Layer caching strategy:**
The Dockerfile is structured to maximize cache hits:
1. Base image rarely changes → always cached
2. User creation rarely changes → cached
3. Requirements change less frequently than code → cached separately
4. Code changes frequently → rebuilds only this layer

**Security model:**
- Non-root user prevents privilege escalation
- Minimal base image reduces attack surface
- No unnecessary packages installed
- Proper file ownership prevents unauthorized modifications

**Runtime behavior:**
- Application runs identically to local environment
- Environment variables allow configuration without rebuild
- Port mapping enables host access
- Process runs as non-root, following security best practices

### 4.2 What Would Happen If Layer Order Changed?

**Scenario 1: Copy code before requirements**
```dockerfile
COPY app.py .
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
```

**Impact:**
- Every code change invalidates dependency cache
- Dependencies reinstalled on every build
- Build time increases significantly (from ~15s to ~60s+)
- More bandwidth usage in CI/CD

**Scenario 2: Install dependencies after copying everything**
```dockerfile
COPY . .
RUN pip install --no-cache-dir -r requirements.txt
```

**Impact:**
- Same as Scenario 1, plus:
- `.dockerignore` becomes less effective
- Unnecessary files might be included
- Larger build context

**Conclusion:** Current order optimizes for development workflow and CI/CD efficiency.

### 4.3 Security Considerations

**Implemented:**
1. **Non-root user**: Prevents privilege escalation attacks
2. **Minimal base image**: Reduces attack surface (fewer packages = fewer vulnerabilities)
3. **No cache in pip**: Prevents storing potentially sensitive package data
4. **Specific base version**: Allows vulnerability tracking and controlled updates
5. **.dockerignore**: Prevents accidental inclusion of sensitive files

**Additional considerations:**
- Regular base image updates for security patches
- Dependency scanning (e.g., `docker scan`)
- Secrets management via environment variables or secrets managers (not hardcoded)
- Network policies in orchestration (Kubernetes)

### 4.4 How .dockerignore Improves Build

**Without .dockerignore:**
- Build context includes `venv/` (~200MB+)
- Includes `__pycache__/` files
- Includes `.git/` directory
- Includes documentation files
- **Result:** Large build context, slower uploads to Docker daemon

**With .dockerignore:**
- Build context only includes `app.py` and `requirements.txt` (~5KB)
- Faster context transfer to Docker daemon
- Smaller image layers
- **Result:** Faster builds, smaller images, better security

**Measured impact (from actual build):**
- Build context size: Only 3.28kB transferred (thanks to .dockerignore)
- Without .dockerignore: Would include venv/ (~200MB+), .git/, docs/, etc.
- Build time: 17.1 seconds total, with context transfer taking <0.1s
- Image size: Minimal impact (files weren't copied anyway), but cleaner and faster builds

---

## 5. Challenges & Solutions

### Challenge: Docker Daemon Not Running

**Problem:**
First build attempt failed with error:
```
ERROR: Cannot connect to the Docker daemon at unix:///Users/marinalavrova/.docker/run/docker.sock. 
Is the docker daemon running?
```

**Solution:**
Started Docker Desktop application, which started the Docker daemon. Subsequent builds worked correctly.

**Learning:**
Docker Desktop must be running for Docker commands to work. Always verify Docker daemon is running before building.


### 5.7 What I Learned

1. **Layer caching is critical**: Proper ordering saves significant time in development and CI/CD
2. **Security by default**: Non-root users should be the default, not an afterthought
3. **Size matters**: Smaller images mean faster deployments and lower costs
4. **Documentation helps**: Understanding WHY practices exist is more valuable than copying them
5. **Iterative improvement**: Start simple, optimize based on actual needs
