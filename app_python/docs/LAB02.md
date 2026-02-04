# Lab 2 — Docker Containerization

## 1. Docker Best Practices Applied

### 1.1 Non-Root User (Security)

**Implementation:**
```dockerfile
RUN useradd -r -s /bin/bash -u 1000 appuser && \
    chown -R appuser:appuser /app
...
USER appuser
```

**Why it matters:**
- **Security principle of least privilege:** Running as root inside a container means that if an attacker compromises the application, they have root privileges within the container
- **Container escape risks:** While Docker provides isolation, running as root increases the impact of potential container escape vulnerabilities
- **Host security:** On some systems, root in container can map to root on host
- **Compliance:** Many security standards require non-root containers (PCI DSS, CIS benchmarks)

### 1.2 Specific Base Image Version

**Implementation:**
```dockerfile
FROM python:3.13-slim
```

**Why it matters:**
- **Reproducibility:** Using `latest` tag means builds can vary over time; specific version ensures consistent builds
- **Security:** You know exactly which base image version you're using, making vulnerability scanning reliable
- **Stability:** Prevents unexpected breakages from base image updates
- **Audit trail:** Clear documentation of what software versions are in production

**Why `slim` variant:**
- **Size:** `python:3.13-slim` (~130MB) vs `python:3.13` (~1GB)
- **Attack surface:** Fewer packages = fewer potential vulnerabilities
- **Performance:** Smaller images download and start faster
- **Sufficient:** Includes everything needed for pure Python applications

### 1.3 Layer Caching Optimization

**Implementation:**
```dockerfile
# Copy requirements first
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code after
COPY app.py .
```

**Why it matters:**
- **Build speed:** Docker caches each layer; unchanged layers are reused
- **Development workflow:** Code changes frequently, dependencies rarely change
- **CI/CD efficiency:** Cached dependency layer saves minutes on every build
- **Bandwidth:** No need to re-download packages if requirements haven't changed

**Example impact:**
- First build: ~30 seconds (install dependencies)
- Rebuild after code change: ~2 seconds (use cached dependency layer)
- Rebuild after adding dependency: ~30 seconds (rebuild from requirements.txt layer)

### 1.4 `.dockerignore` File

**Implementation:**
```
venv/
.git/
__pycache__/
*.md
tests/
docs/
```

**Why it matters:**
- **Build speed:** Smaller build context = faster upload to Docker daemon
- **Image size:** Prevents accidental inclusion of large files (like venv/ which could be 100s of MB)
- **Security:** Prevents leaking sensitive files (.env, .git history, credentials)
- **Cleanliness:** Only production-necessary files in the image

**Real impact in our case:**
- Without `.dockerignore`: Build context ~23MB (includes venv/)
- With `.dockerignore`: Build context ~4.3KB (only requirements.txt 110B and app.py 4.2KB)

### 1.5 No Cache for pip

**Implementation:**
```dockerfile
RUN pip install --no-cache-dir -r requirements.txt
```

**Why it matters:**
- **Image size:** pip cache can add 50-100MB to image
- **Unnecessary in containers:** Cache is only useful for repeated installs, but containers are immutable
- **Best practice:** Official Python Docker image documentation recommends this

### 1.6 HEALTHCHECK Instruction

**Implementation:**
```dockerfile
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:5000/health')"
```

**Why it matters:**
- **Monitoring:** Docker can automatically check if container is healthy
- **Orchestration:** Kubernetes/Docker Swarm can restart unhealthy containers
- **Debugging:** Easy to see if app is actually running, not just the container
- **Production readiness:** Standard practice for production containers

### 1.7 Single Responsibility per RUN

**Implementation:**
```dockerfile
RUN useradd -r -s /bin/bash -u 1000 appuser && \
    chown -R appuser:appuser /app
```

**Why it matters:**
- **Layer optimization:** Multiple commands in one RUN = one layer (reduces image layers)
- **Atomicity:** Related operations grouped together
- **Cache efficiency:** Changes to one part don't invalidate unrelated layers

### 1.8 Environment Variables

**Implementation:**
```dockerfile
ENV HOST=0.0.0.0 \
    PORT=5000 \
    PYTHONUNBUFFERED=1
```

**Why it matters:**
- **Configuration:** Easy to override at runtime with `docker run -e`
- **Logging:** `PYTHONUNBUFFERED=1` ensures logs appear immediately (crucial for Docker logs)
- **Documentation:** Makes default values explicit

---

## 2. Image Information & Decisions

### 2.1 Base Image Selection

**Chosen:** `python:3.13-slim`

**Alternatives considered:**

| Image | Size | Pros | Cons | Decision |
|-------|------|------|------|----------|
| `python:3.13` | ~1GB | All packages included | Massive, slow pulls, large attack surface | ❌ Too large |
| `python:3.13-slim` | ~130MB | Balanced size, has essentials | Slightly larger than alpine | ✅ **Selected** |
| `python:3.13-alpine` | ~50MB | Smallest | musl libc incompatibilities, build issues | ❌ Complexity not worth it |

**Justification for `slim`:**
1. **Compatibility:** Uses glibc like most Linux systems, fewer compatibility issues
2. **Build time:** No need to compile C extensions (alpine often requires build tools)
3. **Maintenance:** More straightforward, less debugging
4. **Size:** Still small enough 
5. **Community:** More commonly used, better documentation

### 2.2 Final Image Size

```
REPOSITORY                SIZE
devops-python-app        226MB
└─ Base layers           ~207MB (Debian 109MB + Python layers)
   Flask + deps           18.9MB
   Application code       4.3KB
```

**Analysis:**
- **Base image layers:** ~207MB (Debian 109MB + Python 3.13 installation ~98MB)
- **Our additions:** 18.9MB (Flask, Werkzeug, requests and their dependencies)
- **Application code:** 4.3KB (app.py 4.2KB + requirements.txt 110 bytes)
- **Total:** 226MB

**Assessment:**
- ✅ **Good** for a Python web application with full Python 3.13 runtime
- Production-grade size (not bloated, includes all necessary tools)
- Could optimize further with alpine base (~100MB smaller) but would sacrifice compatibility
- Reasonable pull time (~60-90 seconds on decent connection)

### 2.3 Layer Structure

```
[Layer 1] FROM python:3.13-slim          - Base OS + Python
[Layer 2] WORKDIR /app                   - Working directory setup
[Layer 3] RUN useradd                    - Non-root user creation
[Layer 4] COPY requirements.txt          - Dependencies manifest
[Layer 5] RUN pip install                - Installed packages (Flask + deps)
[Layer 6] COPY app.py                    - Application code
[Layer 7] Metadata (USER, EXPOSE, etc.)  - Configuration
```

**Optimization notes:**
- Layers 1-5 rarely change -> excellent caching
- Layer 6 changes frequently -> minimal impact on rebuilds
- Proper ordering means 99% of build time is cached during development
- When only code changes: rebuild takes ~2 seconds instead of ~30 seconds

### 2.4 Optimization Choices

1. **Minimal file copying:** Only `requirements.txt` and `app.py` (no tests, docs, venv)
2. **No build tools:** Pure Python app doesn't need gcc, build-essential, etc.
3. **Single-stage build:** Multi-stage unnecessary for interpreted languages
4. **Pip without cache:** Keeps dependencies layer clean at 18.9MB (cache would add ~5-10MB)
5. **Specific user UID:** UID 1000 for compatibility across systems
6. **Proper layer ordering:** Code changes don't trigger dependency reinstall (saves ~25 seconds per rebuild)

---

## 3. Build & Run Process

### 3.1 Build Terminal Output

```bash
cd app_python
docker build -t devops-python-app:latest .
```
Output: 
```bash
[+] Building 1.3s (12/12) FINISHED                                                                                                                                                                                   docker:desktop-linux
 => [internal] load build definition from Dockerfile                                                                                                                                                                                 0.0s
 => => transferring dockerfile: 1.06kB                                                                                                                                                                                               0.0s
 => [internal] load metadata for docker.io/library/python:3.13-slim                                                                                                                                                                  1.2s
 => [auth] library/python:pull token for registry-1.docker.io                                                                                                                                                                        0.0s
 => [internal] load .dockerignore                                                                                                                                                                                                    0.0s
 => => transferring context: 524B                                                                                                                                                                                                    0.0s
 => [1/6] FROM docker.io/library/python:3.13-slim@sha256:51e1a0a317fdb6e170dc791bbeae63fac5272c82f43958ef74a34e170c6f8b18                                                                                                            0.0s
 => => resolve docker.io/library/python:3.13-slim@sha256:51e1a0a317fdb6e170dc791bbeae63fac5272c82f43958ef74a34e170c6f8b18                                                                                                            0.0s
 => [internal] load build context                                                                                                                                                                                                    0.0s
 => => transferring context: 137B                                                                                                                                                                                                    0.0s
 => CACHED [2/6] WORKDIR /app                                                                                                                                                                                                        0.0s
 => CACHED [3/6] RUN useradd -r -s /bin/bash -u 1000 appuser &&     chown -R appuser:appuser /app                                                                                                                                    0.0s
 => CACHED [4/6] COPY requirements.txt .                                                                                                                                                                                             0.0s
 => CACHED [5/6] RUN pip install --no-cache-dir -r requirements.txt                                                                                                                                                                  0.0s
 => CACHED [6/6] COPY app.py .                                                                                                                                                                                                       0.0s
 => exporting to image                                                                                                                                                                                                               0.0s
 => => exporting layers                                                                                                                                                                                                              0.0s
 => => exporting manifest sha256:12e7d332a24c7d29a163c6c4b5a68c4e177d899bf9f7614778f6190bf6aa54e4                                                                                                                                    0.0s
 => => exporting config sha256:d847ae664cfdf1546ebedc383fa3194388a1e7705e7e2284bb30a4a73ab3263c                                                                                                                                      0.0s
 => => exporting attestation manifest sha256:db8532683bf8f8c483af034bdd40b4a56ad23b053845a902939c792a618fb852                                                                                                                        0.0s
 => => exporting manifest list sha256:1e8efee1d597eca2c04e7428d0f8169cde6f7c2228b227119819999000a0c017                                                                                                                               0.0s
 => => naming to docker.io/library/devops-python-app:latest                                                                                                                                                                          0.0s
 => => unpacking to docker.io/library/devops-python-app:latest                                                                                                                                                                       0.0s

View build details: docker-desktop://dashboard/build/desktop-linux/desktop-linux/wcz1qjmkchlwt0gvk8zfisna6
```
**Check the image size:**
```bash
docker images
```
Output: 
```bash
REPOSITORY          TAG       IMAGE ID       CREATED       SIZE
devops-python-app   latest    1e8efee1d597   5 hours ago   226MB
```

### 3.2 Run Container Terminal Output

```bash
docker run -d -p 8080:5000 --name devops-app devops-python-app:latest
```
Output: 
```bash
9b6e43d92d3b6465d953f5a6b786543700a471627a6e05f69450d77eb177f051
```
**Check running containers:**
```bash
docker ps
```
Output: 
```bash
CONTAINER ID   IMAGE                      COMMAND           CREATED         STATUS                   PORTS                    NAMES
9b6e43d92d3b   devops-python-app:latest   "python app.py"   3 minutes ago   Up 3 minutes (healthy)   0.0.0.0:8080->5000/tcp   devops-app
```
**View container logs:**
```bash
docker logs devops-app
```
Output: 
```bash
2026-02-02 21:21:44,062 - __main__ - INFO - Starting DevOps Info Service...
2026-02-02 21:21:44,062 - __main__ - INFO - Host: 0.0.0.0, Port: 5000, Debug: False
2026-02-02 21:21:44,062 - __main__ - INFO - Visit: http://0.0.0.0:5000/
 * Serving Flask app 'app'
 * Debug mode: off
2026-02-02 21:21:44,066 - werkzeug - INFO - WARNING: This is a development server. Do not use it in a production deployment. Use a production WSGI server instead.
 * Running on all addresses (0.0.0.0)
 * Running on http://127.0.0.1:5000
 * Running on http://172.17.0.2:5000
2026-02-02 21:21:44,066 - werkzeug - INFO - Press CTRL+C to quit
2026-02-02 21:21:48,955 - werkzeug - INFO - 127.0.0.1 - - [02/Feb/2026 21:21:48] "GET /health HTTP/1.1" 200 -
2026-02-02 21:22:19,042 - werkzeug - INFO - 127.0.0.1 - - [02/Feb/2026 21:22:19] "GET /health HTTP/1.1" 200 -
2026-02-02 21:22:49,157 - werkzeug - INFO - 127.0.0.1 - - [02/Feb/2026 21:22:49] "GET /health HTTP/1.1" 200 -
2026-02-02 21:23:19,262 - werkzeug - INFO - 127.0.0.1 - - [02/Feb/2026 21:23:19] "GET /health HTTP/1.1" 200 -
2026-02-02 21:23:49,346 - werkzeug - INFO - 127.0.0.1 - - [02/Feb/2026 21:23:49] "GET /health HTTP/1.1" 200 -
2026-02-02 21:24:19,447 - werkzeug - INFO - 127.0.0.1 - - [02/Feb/2026 21:24:19] "GET /health HTTP/1.1" 200 -
2026-02-02 21:24:49,565 - werkzeug - INFO - 127.0.0.1 - - [02/Feb/2026 21:24:49] "GET /health HTTP/1.1" 200 -
2026-02-02 21:25:19,647 - werkzeug - INFO - 127.0.0.1 - - [02/Feb/2026 21:25:19] "GET /health HTTP/1.1" 200 -
2026-02-02 21:25:49,733 - werkzeug - INFO - 127.0.0.1 - - [02/Feb/2026 21:25:49] "GET /health HTTP/1.1" 200 -
2026-02-02 21:26:19,844 - werkzeug - INFO - 127.0.0.1 - - [02/Feb/2026 21:26:19] "GET /health HTTP/1.1" 200 -
2026-02-02 21:26:49,941 - werkzeug - INFO - 127.0.0.1 - - [02/Feb/2026 21:26:49] "GET /health HTTP/1.1" 200 -
```

### 3.3 Testing Endpoints
**Test endpoint /health:**
```bash
curl http://localhost:8080/health
```
Output: 
```bash
{"status":"healthy","timestamp":"2026-02-02T21:28:35.927945+00:00","uptime_seconds":411}
```
**Test the main endpoint /:**
```bash
curl http://localhost:8080/ | python3 -m json.tool
```
Output: 
```bash
  % Total    % Received % Xferd  Average Speed   Time    Time     Time  Current
                                 Dload  Upload   Total   Spent    Left  Speed
100   663  100   663    0     0  83166      0 --:--:-- --:--:-- --:--:-- 94714
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
        "client_ip": "192.168.65.1",
        "method": "GET",
        "path": "/",
        "user_agent": "curl/8.7.1"
    },
    "runtime": {
        "current_time": "2026-02-02T21:30:34.929665+00:00",
        "timezone": "UTC",
        "uptime_human": "8 minutes",
        "uptime_seconds": 530
    },
    "service": {
        "description": "DevOps course info service",
        "framework": "Flask",
        "name": "devops-info-service",
        "version": "1.0.0"
    },
    "system": {
        "architecture": "aarch64",
        "cpu_count": 11,
        "hostname": "9b6e43d92d3b",
        "platform": "Linux",
        "platform_version": "#1 SMP Tue Apr 15 16:00:54 UTC 2025",
        "python_version": "3.13.11"
    }
}
```

### 3.4 Docker Hub Repository

**Repository URL:** `https://hub.docker.com/repository/docker/karishka1222/devops-python-app`

**Push Process:**
```bash
docker login
```
Output: 
```bash
Authenticating with existing credentials... [Username: karishka1222]

i Info → To login with a different account, run 'docker logout' followed by 'docker login'


Login Succeeded
```
**Creating tags:**
```bash
docker tag devops-python-app:latest karishka1222/devops-python-app:latest
```
**Checking that the tags have been created:**
```bash
docker images
```
Output: 
```bash
REPOSITORY                       TAG       IMAGE ID       CREATED        SIZE
karishka1222/devops-python-app   latest    1e8efee1d597   16 hours ago   226MB
devops-python-app                latest    1e8efee1d597   16 hours ago   226MB
```
**Pushing to Docker Hub:**
```bash
docker push karishka1222/devops-python-app:latest
```
Output: 
```bash
The push refers to repository [docker.io/karishka1222/devops-python-app]
ede48e001a80: Pushed 
a7439bac479d: Pushed 
d637807aba98: Pushed 
454d9c816f57: Pushed 
0e8b1219ad2b: Pushed 
3310e4c0a9dc: Pushed 
4cc556234b57: Pushed 
a390baeefb5b: Pushed 
e751b5f6e20a: Pushed 
87b73f9f736b: Pushed 
latest: digest: sha256:1e8efee1d597eca2c04e7428d0f8169cde6f7c2228b227119819999000a0c017 size: 856
```

**Tagging Strategy:**
- `latest`: Always points to the most recent stable build
- Future tags: `1.0.0`, `1.1.0`, `2.0.0`, etc., or `lab2`, `lab3` for course progression

---

## 4. Technical Analysis

### 4.1 Why this Dockerfile works

**Layer-by-layer explanation:**

1. **Base image selection (`FROM python:3.13-slim`)**
   - Provides Python 3.13 runtime
   - Includes essential system libraries (glibc, basic utilities)
   - Excludes unnecessary packages (development tools, documentation)

2. **Working directory (`WORKDIR /app`)**
   - Creates `/app` if it doesn't exist
   - All subsequent commands run in this directory
   - Isolates app files from system files

3. **User creation**
   - Creates system user without login shell privileges
   - UID 1000 is standard first user ID on Linux
   - Changing ownership ensures appuser can read/write in /app

4. **Dependency installation (before code)**
   - Copies only requirements.txt first
   - Installs dependencies in a separate layer
   - This layer is cached and reused unless requirements.txt changes

5. **Application code copy**
   - Copied last because it changes most frequently
   - Doesn't invalidate previous layers when code changes
   - Enables fast rebuilds during development

6. **User switch (`USER appuser`)**
   - All subsequent commands and CMD run as appuser
   - Includes the Python process when container starts
   - Security boundary: even if Flask is compromised, attacker is not root

### 4.2 What would happen if layer order changed?

**Scenario: Copy code before requirements**
```dockerfile
# BAD ORDER
COPY app.py .
COPY requirements.txt .
RUN pip install -r requirements.txt
```

**Impact:**
- Every code change invalidates requirements layer
- Dependencies reinstalled on every build (~30 seconds wasted)
- Terrible developer experience
- CI/CD builds much slower

**Numbers:**
- Good order: 2s rebuild after code change
- Bad order: 32s rebuild after code change
- Over 100 builds: 50 minutes wasted

**Scenario: Switch to USER before installing packages**
```dockerfile
# BAD ORDER
USER appuser
COPY requirements.txt .
RUN pip install -r requirements.txt  # FAILS
```

**Impact:**
- pip install fails: "Permission denied" (can't write to `/usr/local/lib/python3.13/site-packages`)
- Would need to either:
  - Install to user directory (`pip install --user`) → messier
  - Give appuser sudo → defeats security purpose
  - Stay as root → insecure

### 4.3 Security considerations

**1. Non-root user**
- Implemented: ✅
- Impact: Limits damage from application vulnerabilities
- Example: If Flask has an RCE bug, attacker gets `appuser` privileges, not root

**2. Specific base image version**
- Implemented: ✅
- Impact: Consistent security posture; no surprise vulnerabilities from base image updates
- Practice: Regularly update version (e.g., `python:3.13.1-slim` → `python:3.13.2-slim`)

**3. Minimal attack surface**
- Implemented: ✅ (slim image, no extra packages)
- Impact: Fewer packages = fewer CVEs
- Example: Full python image has gcc, make, etc. (not needed, more vulnerabilities)

**4. No secrets in image**
- Implemented: ✅ (.dockerignore excludes .env)
- Impact: Prevents accidental credential leaks
- Practice: Secrets passed as environment variables at runtime

**5. Read-only filesystem (potential future improvement)**
- Not implemented yet
- Would run with: `docker run --read-only -v /tmp` (tempdir writable)
- Flask doesn't need to write files, so this would work

**6. Security scanning (future improvement)**
- Could add: `docker scan karishka1222/devops-python-app:latest`
- Or use Snyk, Trivy, Clair in CI/CD

### 4.4 How `.dockerignore` improves build

**Without `.dockerignore`:**
```
Sending build context to Docker daemon: ~23 MB (includes venv/)
```

**With `.dockerignore`:**
```
Sending build context to Docker daemon: 4.58 KB
```

**Improvements:**

1. **Speed:** 
   - Less data to transfer to Docker daemon
   - Especially important on slow disks or remote Docker hosts
   - 23MB → 4.58KB = ~5,000x smaller context

2. **Deterministic builds:**
   - Excludes files that change frequently but aren't needed (logs, cache)
   - Build hash is stable for same code

3. **Security:**
   - Prevents accidental inclusion of:
     - `.git` (repository history, potentially sensitive commits)
     - `.env` (environment variables, secrets)
     - IDE configs (potentially revealing internal paths)

4. **Image size:**
   - Can't COPY what's not in build context
   - Guards against `COPY . .` mistakes

**Example impact in our project:**
- Without: venv/ (23MB), .git/, docs/, tests/
- With: Only requirements.txt (110 bytes) and app.py (4.2KB)

---

## 5. Challenges & Solutions

### Challenge 1: Understanding Layer Caching

**Problem:** 
Initially wasn't clear why the order of COPY commands mattered. First Dockerfile copied everything at once:

```dockerfile
COPY . .
RUN pip install -r requirements.txt
```

**Symptom:**
Every code change triggered full dependency reinstall (30+ seconds).

**Solution:**
Read Docker layer caching documentation and realized:
- Each instruction creates a layer
- Layers are cached based on instruction + content
- If any layer changes, all subsequent layers rebuild

**Learning:**
Changed to:
```dockerfile
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY app.py .
```

Now code changes don't invalidate dependency layer.

**Testing:**
```bash
# First build: 30s
docker build -t test .

# Changed app.py, rebuild: 2s (cached dependencies)
docker build -t test .

# Added to requirements.txt, rebuild: 30s (rebuilt from pip install)
docker build -t test .
```

### Challenge 2: Non-Root User Permissions

**Problem:**
Initially created user after COPY, which caused permission issues:

```dockerfile
COPY app.py .
RUN useradd appuser
USER appuser
CMD ["python", "app.py"]  # FAILS: Permission denied
```

**Symptom:**
```
PermissionError: [Errno 13] Permission denied: '/app_python/app.py'
```

**Root cause:**
Files copied as root, owned by root. When switched to appuser, couldn't read them.

**Solution:**
```dockerfile
RUN useradd ... && chown -R appuser:appuser /app
COPY requirements.txt .  # Now owned by root, but readable
RUN pip install ...       # Still as root (need write to /usr/local)
COPY app.py .            # Owned by root
USER appuser             # Switch here
```

**Why this works:**
- Files owned by root but world-readable (default COPY behavior)
- appuser can read files, doesn't need to write them
- Alternative: Could `COPY --chown=appuser:appuser` but unnecessary

**Learning:**
Linux file permissions: read (r) permission sufficient for execution. User doesn't need to own file to use it.
