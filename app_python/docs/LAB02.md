# Lab 2 — Docker Containerization: Implementation Report

**Student:** Danil Fishchenko  
**Date:** January 31, 2026  
**App:** DevOps Info Service (Flask)  
**Base Image:** python:3.13-slim  

---

## 1. Docker Best Practices Applied

### ✅ Non-root user
**Why it matters:** Running as a non-root user reduces the blast radius if the app is compromised.

```dockerfile
RUN addgroup --system app && adduser --system --ingroup app app
USER app
```

### ✅ Pinned base image version
**Why it matters:** Pinning the version ensures reproducible builds and avoids unexpected changes.

```dockerfile
FROM python:3.13-slim
```

### ✅ Layer caching optimization
**Why it matters:** Copying `requirements.txt` first allows Docker to cache dependency installation, speeding up rebuilds.

```dockerfile
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
```

### ✅ Minimal copy set
**Why it matters:** Only app code is included to keep the image small and reduce attack surface.

```dockerfile
COPY app.py ./
```

### ✅ .dockerignore
**Why it matters:** Excludes development artifacts to reduce build context and build time.

```dockerignore
__pycache__/
.venv/
docs/
tests/
*.md
```

### ✅ Runtime environment hygiene
**Why it matters:** Avoids writing .pyc files and ensures logs are flushed immediately.

```dockerfile
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1
```

---

## 2. Image Information & Decisions

**Base image chosen:** `python:3.13-slim`

**Why this image:**
- `slim` keeps the image smaller than full Python
- Official image with security updates
- Compatible with Flask and dependencies

**Final image size:** `214MB`

**Layer structure summary:**
1. Base image
2. Workdir + requirements
3. Python dependencies
4. Non-root user creation
5. Application code

**Optimization choices:**
- `requirements.txt` copied before source code to enable caching
- `--no-cache-dir` to reduce pip cache bloat
- `.dockerignore` excludes docs/tests to reduce context

---

## 3. Build & Run Process

### Build output

```
[+] Building 58.5s (13/13) FINISHED                 docker:desktop-linux
 => [internal] load build definition from Dockerfile                0.1s
 => => transferring dockerfile: 363B                                0.0s
 => [internal] load metadata for docker.io/library/python:3.13-sl  42.8s
 => [auth] library/python:pull token for registry-1.docker.io       0.0s
 => [internal] load .dockerignore                                   0.1s
 => => transferring context: 172B                                   0.0s
 => [1/7] FROM docker.io/library/python:3.13-slim@sha256:51e1a0a31  6.5s
 => => resolve docker.io/library/python:3.13-slim@sha256:51e1a0a31  0.0s
 => => sha256:3310e4c0a9dc07e65205534e74daeee1d6 11.72MB / 11.72MB  1.1s
 => => sha256:4cc556234b57f37a358cdc5528347cb750f2ca9f 248B / 248B  1.0s
 => => sha256:a390baeefb5b4121f252f65d48df6ca3ebee 1.27MB / 1.27MB  1.6s
 => => sha256:d637807aba98f742a62ad9b0146579ceb0 30.13MB / 30.13MB  2.8s
 => => extracting sha256:d637807aba98f742a62ad9b0146579ceb0297a3c8  3.0s
 => => extracting sha256:a390baeefb5b4121f252f65d48df6ca3ebee458cc  0.1s
 => => extracting sha256:3310e4c0a9dc07e65205534e74daeee1d62ca9945  0.5s
 => => extracting sha256:4cc556234b57f37a358cdc5528347cb750f2ca9fb  0.0s
 => [internal] load build context                                   0.0s
 => => transferring context: 4.31kB                                 0.0s
 => [2/7] WORKDIR /app                                              0.1s
 => [3/7] COPY requirements.txt ./                                  0.0s
 => [4/7] RUN pip install --no-cache-dir -r requirements.txt        8.3s
 => [5/7] RUN addgroup --system app && adduser --system --ingroup   0.2s
 => [6/7] COPY app.py ./                                            0.0s 
 => [7/7] RUN chown -R app:app /app                                 0.1s
 => exporting to image                                              0.3s
 => => exporting layers                                             0.2s
 => => exporting manifest sha256:e2d82fdfb198062f182d44ec3a6c64661  0.0s
 => => exporting config sha256:b5b0482b30fff2b43c69204eb59f0e1de84  0.0s
 => => exporting attestation manifest sha256:30c3f6812eab6a0044d71  0.0s
 => => exporting manifest list sha256:f9a928f780020db53a3157045773  0.0s
 => => naming to docker.io/library/devops-info-service:lab02        0.0s
 => => unpacking to docker.io/library/devops-info-service:lab02     0.1s
```

### Run container output

```
docker run -d --rm -p 3000:3000 --name devops-info-service-lab02 devops-info-service:lab02
470c414a347937639f53f662bfa2118f105f1150959ae6c9600d8739af9dc387
```

### Endpoint testing output

**GET /**
```
{
    "endpoints": [
        {
            "description": "Service and system information",
            "method": "GET",
            "path": "/"
        },
        {
            "description": "Health check endpoint",
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
        "current_time": "2026-01-31T10:35:59.902212+00:00",
        "timezone": "UTC",
        "uptime_human": "0 hours, 0 minutes",
        "uptime_seconds": 2
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
        "hostname": "470c414a3479",
        "platform": "Linux",
        "platform_version": "#1 SMP Sat May 17 08:28:57 UTC 2025",
        "python_version": "3.13.11"
    }
}
```

**GET /health**
```
{
    "status": "healthy",
    "timestamp": "2026-01-31T10:36:01.993034+00:00",
    "uptime_seconds": 4
}
```

### Image size

```
devops-info-service:lab02  214MB  f9a928f78002
```

### Docker Hub repository

**URL:** https://hub.docker.com/r/pepegx/devops-info-service

**Tagging strategy:** `pepegx/devops-info-service:lab02` (username/repo:lab version)

---

## 4. Technical Analysis

### Why this Dockerfile works
The Dockerfile uses a slim base image, installs dependencies before copying app code for caching, creates a non-root user, and runs the application as that user. It exposes port 3000 to align with the app’s default configuration.

### What if layer order changed?
If application files were copied before dependencies, any code change would invalidate the cache and force a full dependency reinstall. This would slow rebuilds significantly.

### Security considerations
- Non-root execution reduces privilege escalation risks
- Minimal build context via `.dockerignore`
- Slim base image reduces the number of packages and attack surface

### How .dockerignore improves the build
It keeps build context small and prevents unnecessary files from being sent to the Docker daemon, making builds faster and images smaller.

---

## 5. Challenges & Solutions

**Challenge:** Ensuring build context stays minimal and rebuilds are fast.  
**Solution:** Added a `.dockerignore` and separated dependency installation from source code copying to enable Docker layer caching.

---

## 6. Docker Hub Push Evidence

```
docker push pepegx/devops-info-service:lab02
The push refers to repository [docker.io/pepegx/devops-info-service]
9fa8a093b5d4: Pushed 
d637807aba98: Pushed 
a390baeefb5b: Pushed 
d34c483f4cd9: Pushed 
d28a7afb9026: Pushed 
997cfd2075b7: Pushed 
7954a8943a8c: Pushed 
3310e4c0a9dc: Pushed 
4cc556234b57: Pushed 
b1aae0271f00: Pushed 
92539f6e9932: Pushed 
lab02: digest: sha256:f9a928f780020db53a3157045773ee05571a8dce77c83e8122e5e2518c8ff647 size: 856
```