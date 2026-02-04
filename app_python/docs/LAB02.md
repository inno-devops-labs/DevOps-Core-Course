# LAB02 — Docker Containerization

## Overview

In this lab we containerized DevOps Info Service from 1st lab using Docker.
The goal was to create a production-ready Docker image following best practices
for security, performance, and maintainability, and to publish it to Docker Hub.

---

## 1. Docker Best Practices Applied

### Non-root User

A dedicated non-root user is created and used to run the application.

**Why it matters:**
Running containers as root increases the impact of potential security vulnerabilities.
Using a non-root user follows the principle of least privilege.

**Snippet:**
```dockerfile
RUN useradd -m -u 10001 appuser
USER appuser
```


---

### Layer Caching Optimization

Dependencies are installed before application code is copied.

**Why it matters:**
Docker caches layers. If application code changes but dependencies do not,
Docker can reuse cached layers, significantly speeding up rebuilds.

**Snippet:**

```dockerfile
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app.py .
```

---

### .dockerignore Usage

Unnecessary files are excluded from the build context.

**Why it matters:**
Smaller build context leads to faster builds and smaller images.
It also prevents leaking development artifacts into the container.

**Examples excluded:**

* Virtual environments
* Python cache files
* Git metadata
* IDE configuration files

---

## 2. Image Information & Decisions

### Base Image Choice

**Chosen image:** `python:3.13-slim`

**Justification:**

* Official Python image
* Smaller size than full images
* Matches course requirements

---

### Image Size Assessment

The final image size is reasonably small for a Python web service
and suitable for educational usage.

No unnecessary tools or build dependencies are included.

---

### Layer Structure Explanation

1. Base Python image
2. OS-level dependencies installation
3. Python dependencies installation
4. Application code copy
5. Runtime execution as non-root user

This structure maximizes cache reuse and keeps layers logically separated.

---

### Optimization Choices

* `.dockerignore` excludes unnecessary files (`__pycache__`, `.git`, `venv/`, docs) → smaller build context
* `--no-cache-dir` during `pip install` → avoids storing pip cache inside image
* Only essential system packages installed → reduces attack surface
* Explicit user creation (`appuser`) → security compliance

---

## 3. Build & Run Process

### Build Output

```text
docker build -t devops-info-service:lab2 .
...
[+] Building 5.1s (13/13) FINISHED  
View build details: docker-desktop://.../image-id
```

---

### Running the Container

```text
docker run -p 8080:5000 devops-info-service:lab2
...
INFO:     Started server process [1]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:5000 (Press CTRL+C to quit)

INFO:     192.168.65.1:33652 - "GET / HTTP/1.1" 200 OK
INFO:     192.168.65.1:35043 - "GET /health HTTP/1.1" 200 OK
```

---

### Endpoint Testing

```bash
curl http://localhost:8080/
```

```json
{
  "service": {
    "name": "devops-info-service",
    "version": "1.0.0",
    "description": "DevOps course info service",
    "framework": "FastAPI"
  },
  "system": {
    "hostname": "749c072465da",
    "platform": "Linux",
    "platform_version": "#1 SMP Thu Mar 20 16:32:56 UTC 2025",
    "architecture": "aarch64",
    "cpu_count": 8,
    "python_version": "3.13.11"
  },
  "runtime": {
    "uptime_seconds": 16,
    "uptime_human": "0 hours, 0 minutes",
    "current_time": "2026-02-04T20:18:01.719461+00:00",
    "timezone": "UTC"
  },
  "request": {
    "client_ip": "192.168.65.1",
    "user_agent": "curl/8.7.1",
    "method": "GET",
    "path": "/"
  },
  "endpoints": [
    {
      "path": "/",
      "method": "GET",
      "description": "Service information"
    },
    {
      "path": "/health",
      "method": "GET",
      "description": "Health check"
    }
  ]
}
```
---

```bash
curl http://localhost:8080/health
```

```json
{
  "status": "healthy",
  "timestamp": "2026-02-04T20:19:25.484246+00:00",
  "uptime_seconds": 100
}
```

Both endpoints returned valid JSON responses identical to local execution.

---

### Docker Hub Repository

The image was published to Docker Hub and verified by pulling it publicly.

**Repository URL:**
[https://hub.docker.com/r/egorlazutkin/devops-info-service](https://hub.docker.com/r/egorlazutkin/devops-info-service)

---

## 4. Technical Analysis

### Why This Dockerfile Works

The Dockerfile follows a clear, layered approach:

* Stable base
* Cached dependency installation
* Minimal runtime footprint
* Secure execution context

---

### Effect of Changing Layer Order

If application code were copied before installing dependencies:

* Docker cache would be invalidated on every code change
* Build times would significantly increase

---

### Security Considerations

* Non-root user
* Minimal base image
* No unnecessary packages
* No secrets baked into the image

---

### Impact of .dockerignore

Using `.dockerignore`:

* Reduces image build time
* Decreases context size
* Prevents accidental inclusion of sensitive or irrelevant files

---

## 5. Challenges & Solutions

### Port Conflict on Host

**Issue:**
During container testing, port `5000` was already in use by a macOS system service (Control Center).

**Solution:**
The issue was resolved by mapping the container port `5000` to an alternative host port (`8080`)

---

### Long Build Time During First Build

**Issue:**
Initial build took longer due to dependency installation.

**Solution:**
Leveraged Docker layer caching, which significantly improved rebuild speed.

---

### Key Learnings

* Docker layer ordering has a major impact on performance
* Security best practices are easy to apply early
* Containers provide consistent behavior across environments

