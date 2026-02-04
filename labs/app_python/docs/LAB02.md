# Lab 2 — Docker Containerization Report

## 1. Docker Best Practices Applied

### Non-Root User
```dockerfile
RUN groupadd --gid 1000 appgroup && \
    useradd --uid 1000 --gid appgroup --shell /bin/bash --create-home appuser
USER appuser
```
**Why it matters:** Running containers as root is a security risk. If an attacker compromises the application, they would have root privileges inside the container. Using a non-root user limits the potential damage and follows the principle of least privilege.

### Specific Base Image Version
```dockerfile
FROM python:3.13-slim
```
**Why it matters:** Using a specific version (not `latest`) ensures reproducible builds. The `slim` variant is much smaller than the full image (~150MB vs ~900MB) while still including all necessary components for Python applications.

### Layer Caching Optimization
```dockerfile
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app.py .
```
**Why it matters:** Dependencies change less frequently than application code. By copying and installing requirements first, Docker caches this layer. When only `app.py` changes, Docker reuses the cached dependency layer, making rebuilds much faster.

### .dockerignore File
Excludes: `__pycache__/`, `*.pyc`, `.git/`, `venv/`, `.venv/`, `.idea/`, `.vscode/`, `docs/`, `tests/`, `*.md`

**Why it matters:**
- **Faster builds:** Less data sent to Docker daemon
- **Smaller build context:** Reduces network overhead
- **Security:** Prevents sensitive files (like .git history) from ending up in image
- **Cleaner images:** No development artifacts in production

### Health Check
```dockerfile
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:5000/health')" || exit 1
```
**Why it matters:** Enables container orchestrators (like Kubernetes or Docker Swarm) to detect unhealthy containers and automatically restart or replace them.

---

## 2. Image Information & Decisions

### Base Image Choice: `python:3.13-slim`

| Consideration | Decision |
|---------------|----------|
| Image size | 157MB final (slim variant) |
| Python version | 3.13 (latest stable) |
| Components | glibc, pip, essential system libs |
| Alternative considered | `python:3.13-alpine` - smaller but musl libc can cause compatibility issues |

**Justification:** The slim variant provides the best balance between size and compatibility. It's ~6x smaller than the full image while avoiding Alpine's musl libc issues with some Python packages.

### Layer Structure

| Layer | Purpose | Size Impact |
|-------|---------|-------------|
| Base | Python runtime | ~125MB |
| User creation | Security | ~1KB |
| Dependencies | pip packages | ~30MB |
| Application | app.py | ~4KB |

### Optimization Choices
- `--no-cache-dir` in pip: Reduces image size by not storing pip cache
- No dev dependencies: Only runtime packages included
- Single `app.py` copy: Minimal application layer

---

## 3. Build & Run Process

### Build Output
```
$ docker build -t devops-info-service:python .

[+] Building 30.5s (12/12) FINISHED
 => [1/7] FROM docker.io/library/python:3.13-slim
 => [2/7] WORKDIR /app
 => [3/7] RUN groupadd --gid 1000 appgroup && useradd --uid 1000 --gid appgroup --shell /bin/bash --create-home appuser
 => [4/7] COPY requirements.txt .
 => [5/7] RUN pip install --no-cache-dir -r requirements.txt
 => [6/7] COPY app.py .
 => [7/7] RUN chown -R appuser:appgroup /app
 => exporting to image
 => => naming to docker.io/library/devops-info-service:python
```

### Container Running
```
$ docker run -d -p 5000:5000 --name test-python devops-info-service:python
b2c23be42db89ac6402deeaeb48c18a2392cad10fc6ba065bac0a84733a153e2

$ docker ps
CONTAINER ID   IMAGE                          PORTS                    STATUS
b2c23be42db8   devops-info-service:python     0.0.0.0:5000->5000/tcp   Up 5 seconds
```

### Endpoint Testing
```
$ curl http://localhost:5000/
{"service":{"name":"devops-info-service","version":"1.0.0","description":"DevOps course info service","framework":"FastAPI"},"system":{"hostname":"b2c23be42db8","platform":"Linux","platform_version":"Linux-6.14.0-37-generic-x86_64-with-glibc2.41","architecture":"x86_64","cpu_count":12,"python_version":"3.13.11"},...}

$ curl http://localhost:5000/health
{"status":"healthy","timestamp":"2026-02-04T17:51:44.282959Z","uptime_seconds":7}
```

### Non-Root Verification
```
$ docker exec test-python whoami
appuser
```

### Image Size
```
$ docker images devops-info-service:python
REPOSITORY            TAG       SIZE
devops-info-service   python    157MB
```

### Docker Hub Repository
> `https://hub.docker.com/r/blxxdclxud/devops-info-service`

---

## 4. Technical Analysis

### Why This Dockerfile Works

1. **Layer ordering maximizes cache hits:** Dependencies are installed before app code, so code changes don't invalidate the dependency cache.

2. **Non-root user is created early:** Creating the user before copying files allows us to set proper ownership.

3. **Minimal attack surface:** Only essential files are copied, reducing potential vulnerabilities.

### What If Layer Order Changed?

If we copied `app.py` before installing dependencies:
```dockerfile
# BAD - breaks caching
COPY app.py .
COPY requirements.txt .
RUN pip install -r requirements.txt
```

**Impact:** Every code change would invalidate the dependency installation cache, making builds ~20 seconds slower.

### Security Considerations

| Measure | Risk Mitigated |
|---------|----------------|
| Non-root user | Privilege escalation |
| Specific base version | Supply chain attacks |
| .dockerignore | Credential leakage |
| Health checks | Service availability |

### .dockerignore Benefits

Without .dockerignore, the build context would include:
- `venv/` (~200MB of redundant Python packages)
- `.git/` (commit history, potentially sensitive)
- `docs/` and `tests/` (not needed in production)

This would slow builds and bloat the image significantly.

---

## 5. Challenges & Solutions

### Challenge 1: Port Already in Use
**Problem:** `docker run` failed with "port is already allocated"

**Solution:** Used alternate port mapping `-p 5001:5000` or stopped conflicting service

### Challenge 2: Choosing Base Image
**Problem:** Deciding between `alpine`, `slim`, and full Python images

**Solution:** Chose `slim` as it balances size (~150MB vs ~900MB full) with glibc compatibility. Alpine's musl libc can cause issues with some packages.

### Challenge 3: Layer Caching Strategy
**Problem:** Initial builds were slow on every code change

**Solution:** Restructured Dockerfile to copy and install requirements before application code, leveraging Docker's layer caching.

### Lessons Learned

1. **Always use specific image tags** - `python:3.13-slim` instead of `python:latest`
2. **Non-root is non-negotiable** - Security should never be optional
3. **Layer order matters** - Think about what changes frequently vs rarely
4. **Test the container** - Run `whoami` and verify endpoints work as expected
