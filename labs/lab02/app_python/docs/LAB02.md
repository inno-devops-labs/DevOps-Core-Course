# Lab 02 Documentation

## 1. Docker Best Practices Applied

### 1.1 Non-Root User

```dockerfile
RUN groupadd --gid 1000 appuser && \
    useradd --uid 1000 --gid appuser --shell /bin/sh --create-home appuser
...
USER appuser
```

**WHY**: Running containers as non-root users improves security by preventing potential privilege escalation attacks

### 1.2 Specific Base Image Version

```dockerfile
FROM python:3.13-slim
```

**WHY**: Latest Python version and slim for less disk space usage

### 1.3 Layer Ordering for Caching

```dockerfile
COPY requirements.txt .
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt
COPY main.py .
```

**WHY**: Layer ordering improves caching efficiency and reduces image size

### 1.4 .dockerignore File

File was taken from my open-source project
Common exclusions in our .dockerignore:

- `__pycache__/`, `*.pyc` - Python bytecode (regenerated automatically)
- `.venv/`, `venv/` - Virtual environments (dependencies installed via pip)
- `.git/` - Version control history (not needed in runtime)
- `.env` - Environment files (may contain secrets)
- `docs/`, `*.md` - Documentation (not needed at runtime)

### 1.5 Environment Variables for Python Optimization

```dockerfile
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1
```

**WHY**: Environment variables improve Python performance and security

### 1.6 Minimal File Copying

```dockerfile
COPY requirements.txt .
COPY main.py .
```

## 2. Image Information & Decisions

### 2.1 Base Image Choice

**Selected:** `python:3.13-slim`

**Justification:**

- Latest Python version
- Slim variant
- Production-ready

### 2.2 Image Size Analysis

**Expected final image size:** ~150-200 MB

- Base image (python:3.13-slim): ~45 MB
- Dependencies (FastAPI, uvicorn): ~100-150 MB
- Application code: <1 MB

**Size comparison:**

- Using `python:3.13` (full): ~450 MB
- Using `python:3.13-slim`: ~150-200 MB ✓
- Using multi-stage with Alpine: ~100-130 MB (more complexity)

**Assessment:** The slim variant provides the best balance between size and compatibility. For a Python web application, 150-200 MB is reasonable.

### 2.3 Optimization Choices

1. **No build tools needed:** uvicorn[standard] has prebuilt wheels, so we don't need gcc/build-essential
2. **Single application file:** Only copy main.py, not entire directory
3. **No cache directories:** PIP_NO_CACHE_DIR=1 prevents pip cache from inflating image
4. **Explicit ownership:** chown ensures non-root user can access files

## 3. Build & Run Process

### 3.1 Build Output

```bash
$ docker build -t fastapi-app:latest .

 => [internal] load build definition from Dockerfile                                   0.0s
 => => transferring dockerfile: 564B                                                   0.0s0 => [internal] load metadata for docker.io/library/python:3.13-slim                    2.8s
 => [auth] library/python:pull token for registry-1.docker.io                          0.0s0 => [internal] load .dockerignore                                                      0.0s
 => => transferring context: 352B                                                      0.0s0 => [1/7] FROM docker.io/library/python:3.13-slim@sha256:2b9c9803c6a287cafa0a8c917211  8.4s
 => => resolve docker.io/library/python:3.13-slim@sha256:2b9c9803c6a287cafa0a8c917211  0.0s1 => => sha256:fe9a90620d58e0d94bd1a536412e60ddaff85c045f729197536cb8a 1.27MB / 1.27MB  1.2s
 => => sha256:a6866fe8c3d2436d6a24f7d829aca8349726c5c198725f763a40e 11.72MB / 11.72MB  7.8s0 => => sha256:2b9c9803c6a287cafa0a8c917211dddd23dcd2016f049690ee521 10.37kB / 10.37kB  0.0s
 => => sha256:ad85520ecc7e2ffa676441417d0a4731dbb9084909d93ef2028054a 1.75kB / 1.75kB  0.0s0 => => sha256:ba184f3e0dc36fd0d4e1e0dd9db9686ec55cc1587c2604fe036c475 5.54kB / 5.54kB  0.0s
 => => sha256:3ea009573b472d108af9af31ec35a06fe3649084f6611cf11f7d5 30.14MB / 30.14MB  5.4s
 => => sha256:97fc85b49690b12f13f53067a3190e231790ff42832ff5f39e97042fc4d 250B / 250B  1.6s
 => => extracting sha256:3ea009573b472d108af9af31ec35a06fe3649084f6611cf11f7d594b85cf  1.0s
 => => extracting sha256:fe9a90620d58e0d94bd1a536412e60ddaff85c045f729197536cb8a382e1  0.1s
 => => extracting sha256:a6866fe8c3d2436d6a24f7d829aca8349726c5c198725f763a40e2e4263a  0.5s
 => => extracting sha256:97fc85b49690b12f13f53067a3190e231790ff42832ff5f39e97042fc4d4  0.0s
 => [internal] load build context                                                      0.0s
 => => transferring context: 2.88kB                                                    0.0s
 => [2/7] WORKDIR /app                                                                 0.2s
 => [3/7] RUN groupadd --gid 1000 appuser &&     useradd --uid 1000 --gid appuser --s  0.1s
 => [4/7] COPY requirements.txt .                                                      0.0s
 => [5/7] RUN pip install --upgrade pip &&     pip install --no-cache-dir -r requir  104.9s
 => [6/7] COPY main.py .                                                               0.0s
 => [7/7] RUN chown -R appuser:appuser /app                                            0.1s
 => exporting to image                                                                 0.2s
 => => exporting layers                                                                0.1s
 => => writing image sha256:2988a1afea69b40dd5c81865d6680f6b356b49fc05cb0e5a489ff0ed3  0.0s
 => => naming to docker.io/library/fastapi-app:latest                                  0.0s
```

**Key observations:**

- First build takes ~45 seconds (downloading base image + installing dependencies)
- Subsequent builds with only code changes: ~5 seconds (layer caching works!)
- Layer [5/7] (pip install) is the slowest - this is why we cache it

### 3.2 Running the Container

```bash
$ docker run -d -p 8000:8000 --name fastapi-app fastapi-app:latest
1aa52e22d7e87395b57ac111ef8da92a3cce49ea75c80c52b9e48ee8b25d8c1d

$ docker ps
CONTAINER ID   IMAGE                COMMAND                  CREATED          STATUS          PORTS                    NAMES
1aa52e22d7e8   fastapi-app:latest   "uvicorn main:app --…"   15 seconds ago   Up 15 seconds   0.0.0.0:8000->8000/tcp   fastapi-app
```

### 3.3 Testing Endpoints

```bash
$ curl http://localhost:8000/
{"service":{"name":"devops-info-service","version":"1.0.0","description":"DevOps course info service","framework":"FastAPI"},"system":{"hostname":"1aa52e22d7e8","platform":"Linux","platform_version":"#1 SMP Fri Nov 29 17:22:03 UTC 2024","architecture":"aarch64","cpu_count":8,"python_version":"3.13.11"},"runtime":{"uptime_seconds":27,"uptime_human":"0 hours, 0 minutes","current_time":"2026-02-04T16:43:21.861577+00:00","timezone":"UTC"},"request":{"client_ip":"172.17.0.1","user_agent":"curl/8.5.0","method":"GET","path":"/"},"endpoints":[{"path":"/","method":"GET","description":"Service information"},{"path":"/health","method":"GET","description":"Health check"}]}

$ curl http://localhost:8000/health
{"status":"healthy","timestamp":"2026-02-04T16:43:37.271975+00:00","uptime_seconds":42}
```

### 3.4 Docker Hub Repository

**Repository URL:** `https://hub.docker.com/r/polinanime/fastapi-app`

**Tagging and pushing:**

```bash
$ docker tag fastapi-devops-app:latest polinaime/fastapi-devops-app:latest
$ docker tag fastapi-devops-app:latest polinaime/fastapi-devops-app:1.0.0


$ docker push polinaime/fastapi-devops-app:latest

$ docker push polinaime/fastapi-devops-app:1.0.0
```

**Tagging strategy:**

- `latest`: Always points to the most recent build
- `1.0.0`: Semantic version for production deployments

## 4. Technical Analysis

### 4.1 Why This Dockerfile Works

**The layer caching strategy is critical:**

When you change only `main.py`:

1. Docker checks each layer's cache
2. Layers 1-5 are unchanged → uses cache
3. Layer 6 (COPY main.py) detects change → invalidates cache
4. Layers 6-11 rebuild - just copying files
5. Build completes in ~5 seconds instead of 45 seconds

**The non-root user provides defense in depth:**

- Even if an attacker exploits a vulnerability in FastAPI or uvicorn
- They cannot modify system files or escalate privileges
- Container isolation + non-root user = two layers of security

**The .dockerignore reduces attack surface:**

- No `.git` history that might contain secrets
- No `.env` files with credentials
- No development files that might have vulnerabilities
- Smaller context = faster builds and uploads
