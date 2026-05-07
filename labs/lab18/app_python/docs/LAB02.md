# Docker Implementation Documentation

## Docker Best Practices Applied

### 1. **Non-Root User** (Security)
```dockerfile
RUN useradd --create-home --shell /bin/bash appuser && \
    chown -R appuser:appuser /app
USER appuser
```
**Why it matters:** Running containers as root is a major security risk. If an attacker compromises the container, they have root access to the container environment. By creating a dedicated non-root user, we follow the principle of least privilege.

### 2. **Multi-Stage Build** (Size Optimization)
```dockerfile
FROM python:3.13-slim as builder
# ... build stage ...
FROM python:3.13-slim
COPY --from=builder /opt/venv /opt/venv
```
**Why it matters:** 
The builder stage contains build tools and intermediate files that aren't needed in the final image. By copying only the virtual environment, we keep the final image small and secure.

### 3. **Layer Caching** (Build Speed)
```dockerfile
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app.py .
```
**Why it matters:** 
Docker caches layers. By copying `requirements.txt` first and installing dependencies before copying the application code, we ensure dependency installation is only re-run when requirements change. This speeds up builds dramatically.

### 4. **No Cache for Pip** (Size Reduction)
```dockerfile
RUN pip install --no-cache-dir -r requirements.txt
```
**Why it matters:** 
Pip's cache can be hundreds of MB. The `--no-cache-dir` flag prevents storing downloaded package caches, reducing image size.

### 5. **Explicit Port**
```dockerfile
EXPOSE 5000
```
**Why it matters:** 
Documents which port the application uses, making it clear for users and orchestration systems.

## Image Information & Decisions

### Base Image Choice
**Chosen:** `python:3.13-slim`
```dockerfile
FROM python:3.13-slim as builder
FROM python:3.13-slim
```

**Justification:**
- **Slim variant:** Contains only essential packages (218MB vs 1GB for full Python)
- **Specific version (3.13):** Ensures reproducibility; "latest" tags can break builds
- **Official image:** Security-scanned, maintained by Docker, frequent updates

### Final Image Size
```
REPOSITORY                             TAG       SIZE
poparthur/devops-info-service:latest   latest    49.2MB
```

**Assessment:** 
This service adds minimal overhead to the base image. 
The virtual environment and code add small size because of use of the same base image in both stages.

### Layer Structure Analysis
```bash
docker history arthurdevops/devops-service:latest
```
```
IMAGE          CREATED          CREATED BY                                      SIZE      COMMENT
ebf7ba23cee9   40 minutes ago   CMD ["python" "app.py"]                         0B        buildkit.dockerfile.v0
<missing>      40 minutes ago   HEALTHCHECK &{["CMD-SHELL" "python -c \"impo…   0B        buildkit.dockerfile.v0
<missing>      40 minutes ago   EXPOSE map[5000/tcp:{}]                         0B        buildkit.dockerfile.v0
<missing>      40 minutes ago   USER appuser                                    0B        buildkit.dockerfile.v0
<missing>      40 minutes ago   COPY --chown=appuser:appuser requirements.tx…   235B      buildkit.dockerfile.v0
<missing>      40 minutes ago   COPY --chown=appuser:appuser app.py . # buil…   3.94kB    buildkit.dockerfile.v0
<missing>      40 minutes ago   COPY /opt/venv /opt/venv # buildkit             24.3MB    buildkit.dockerfile.v0
<missing>      40 minutes ago   RUN /bin/sh -c useradd --create-home --shell…   8.92kB    buildkit.dockerfile.v0
<missing>      40 minutes ago   WORKDIR /app                                    0B        buildkit.dockerfile.v0
<missing>      40 minutes ago   ENV PATH=/opt/venv/bin:/usr/local/bin:/usr/l…   0B        buildkit.dockerfile.v0
```

### Optimization Choices
1. **Slim base image:** Saved ~800MB vs full Python
2. **Multi-stage build:** Kept build tools out of final image
3. **Virtual environment in builder:** Clean dependency management
4. **Layer ordering:** Maximized cache utilization

## Build & Run Process

### Complete Build Output
```bashdocker build -t devops-service .                                           
[+] Building 1.0s (15/15) FINISHED                                                                                      docker:desktop-linux
 => [internal] load build definition from Dockerfile                                                                                    0.0s
 => => transferring dockerfile: 827B                                                                                                    0.0s
 => WARN: FromAsCasing: 'as' and 'FROM' keywords' casing do not match (line 1)                                                          0.0s
 => [internal] load metadata for docker.io/library/python:3.13-slim                                                                     1.0s
 => [internal] load .dockerignore                                                                                                       0.0s
 => => transferring context: 2B                                                                                                         0.0s
 => [internal] load build context                                                                                                       0.0s
 => => transferring context: 138B                                                                                                       0.0s
 => [builder 1/5] FROM docker.io/library/python:3.13-slim@sha256:51e1a0a317fdb6e170dc791bbeae63fac5272c82f43958ef74a34e170c6f8b18       0.0s
 => CACHED [stage-1 2/6] WORKDIR /app                                                                                                   0.0s
 => CACHED [stage-1 3/6] RUN useradd --create-home --shell /bin/bash appuser &&     chown -R appuser:appuser /app                       0.0s
 => CACHED [builder 2/5] WORKDIR /build                                                                                                 0.0s
 => CACHED [builder 3/5] COPY requirements.txt .                                                                                        0.0s
 => CACHED [builder 4/5] RUN python -m venv /opt/venv                                                                                   0.0s
 => CACHED [builder 5/5] RUN pip install --no-cache-dir -r requirements.txt                                                             0.0s
 => CACHED [stage-1 4/6] COPY --from=builder /opt/venv /opt/venv                                                                        0.0s
 => CACHED [stage-1 5/6] COPY --chown=appuser:appuser app.py .                                                                          0.0s
 => CACHED [stage-1 6/6] COPY --chown=appuser:appuser requirements.txt .                                                                0.0s
 => exporting to image                                                                                                                  0.0s
 => => exporting layers                                                                                                                 0.0s
 => => writing image sha256:cd9822f1f2d504b26fa22e118a3f2cea5757cf478ccfcfefaeeb0a6a37fd7153                                            0.0s
 => => naming to docker.io/library/devops-service                                                                                       0.0s
```

### Container Running Output
```bashdocker run -p 5001:5000 devops-service

2026-02-02 10:25:05,954 - __main__ - INFO - Starting DevOps Info Service - 0.0.0.0:5000
2026-02-02 10:25:06,023 - __main__ - INFO - Starting server on 0.0.0.0:5000
2026-02-02 10:25:06,023 - __main__ - INFO - Debug mode: False
INFO:     Started server process [1]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:5000 (Press CTRL+C to quit)
2026-02-02 10:25:10,781 - __main__ - INFO - Request: GET / from 192.168.65.1
INFO:     192.168.65.1:41606 - "GET / HTTP/1.1" 200 OK
```

### Endpoint Testing Output
```bash(.venv) arthur@Artur-MacBook-Pro DevOps-Core-Course % curl http://localhost:5001/

{"service":{"name":"devops-info-service","version":"1.0.0","description":"DevOps course info service","framework":"FastAPI"},"system":{"hostname":"8c92056d2e36","platform":"Linux","platform_version":"#1 SMP Thu Mar 20 16:32:56 UTC 2025","architecture":"aarch64","cpu_count":8,"python_version":"3.13.11"},"runtime":{"uptime_seconds":4,"uptime_human":"0 hours, 0 minutes","current_time":"2026-02-02T10:25:10.781555","timezone":"UTC"},"request":{"client_ip":"192.168.65.1","user_agent":"curl/8.7.1","method":"GET","path":"/"},"endpoints":[{"path":"/","method":"GET","description":"Service information"},{"path":"/health","method":"GET","description":"Health check"}]}%    
```

### Docker Hub Repository
**URL:** https://hub.docker.com/r/poparthur/devops-info-service

## Technical Analysis

### Why This Dockerfile Structure Works
The Dockerfile follows a logical flow:
1. **Builder stage:** Creates a clean environment for dependency installation
2. **Final stage:** Starts fresh with minimal base image
3. **Copy artifacts:** Only brings what's needed from builder
4. **Security setup:** Creates non-root user and sets permissions
5. **Runtime configuration:** Sets environment variables and health checks

### Impact of Changing Layer Order
If we reversed lines 19-20:
```dockerfile
# INCORRECT ORDER - breaks caching
COPY app.py .
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
```

**Result:** Every code change would trigger a full `pip install`, even if requirements didn't change. Builds would take 30+ seconds instead of 3 seconds.

### Security Considerations Implemented
1. **Non-root user:** Limits damage from container breakout
2. **No package cache:** Reduces attack surface
3. **No bytecode:** Prevents `.pyc` injection attacks
4. **Minimal base image:** Fewer packages = fewer vulnerabilities
5. **Virtual environment:** Isolates application dependencies

### How .dockerignore Improves Builds
Our `.dockerignore`:
```
__pycache__/
*.pyc
*.pyo
*.pyd
.Python
venv/
env/
.venv/
*.log
.git/
.gitignore
```

**Benefits:**
1. **Smaller context:** Docker only sends relevant files to daemon
2. **Faster builds:** Excluding 500MB of `.git` history speeds transfers
3. **Cleaner images:** No development/test files in production
4. **Security:** Prevents accidental inclusion of secrets

## Challenges & Solutions

### Issue 1: Port Already in Use
**Problem:** `docker: Error response from daemon: Ports are not available: exposing port TCP 0.0.0.0:5000`

**Debugging:**
```bash
lsof -i :5000
# Found Python process already using port
```

**Solution:**
```bash
# Use different port
docker run -p 5001:5000 devops-service
```

**Learning:** Always check for port conflicts before assuming Docker is broken.

### Issue 2: Image Size Optimization
**Problem**: First attempt created ~250MB image using multi-stage but with full Python base.

**Solution**: Switched from python:3.13 to python:3.13-slim, reducing by 60%.

**Learning**: Base image choice has 10x impact on final size. Always consider minimal variants for interpreted languages.
