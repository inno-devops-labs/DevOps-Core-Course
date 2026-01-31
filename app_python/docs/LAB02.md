# Lab 02 — Docker Containerization (Python)

## 1. Docker Best Practices Applied

- **Specific base image**: `python:3.13-slim` for reproducible builds and smaller size compared to full images.
- **Non-root user**: created `appuser` and switched to it to reduce container privileges.
- **Layer caching**: copied `requirements.txt` first, installed dependencies, then copied app code so dependency layer is cached when code changes.
- **Minimal copy**: only `requirements.txt` and `app.py` are copied into the image.
- **.dockerignore**: excludes dev files, docs, tests, VCS, and local IDE files to reduce build context and speed up builds.
- **No pip cache**: `pip install --no-cache-dir` reduces image size.

**Relevant Dockerfile snippets:**
```dockerfile
FROM python:3.13-slim
...
RUN groupadd --system appuser && useradd --system --gid appuser --create-home appuser
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY app.py ./
USER appuser
```

## 2. Image Information & Decisions

- **Base image**: `python:3.13-slim` chosen for recent Python version and smaller footprint.
- **Final image size**: `devops-info-service:lab02 254MB` (from `docker images`).
- **Layer structure**:
  1. Base image
  2. User creation
  3. Dependency install
  4. App code copy
  5. Ownership + runtime user
- **Optimization choices**: slim base, caching of deps, no-cache pip, minimal files copied.

## 3. Build & Run Process

**Build output (excerpt):**
```
docker build -t devops-info-service:lab02 .
...
#9 [5/7] RUN pip install --no-cache-dir -r requirements.txt
...
#12 naming to docker.io/library/devops-info-service:lab02 done
```

**Container running (docker ps):**
```
CONTAINER ID   IMAGE                       COMMAND           CREATED         STATUS         PORTS                    NAMES
9a06ac4d2276   devops-info-service:lab02   "python app.py"   8 seconds ago   Up 7 seconds   0.0.0.0:8000->8000/tcp   devops-info-service-lab02
```

**Endpoint tests:**
```
curl -s http://localhost:8000/
{"service":{"name":"devops-info-service","version":"1.0.0","description":"DevOps course info service","framework":"FastAPI"},"system":{"hostname":"9a06ac4d2276","platform":"Linux","platform_version":"#1 SMP Tue Apr 15 16:00:54 UTC 2025","architecture":"aarch64","cpu_count":12,"python_version":"3.13.11"},"runtime":{"uptime_seconds":11,"uptime_human":"0 hours, 0 minutes","current_time":"2026-01-31T10:00:47.866150+00:00","timezone":"UTC"},"request":{"client_ip":"192.168.65.1","user_agent":"curl/8.7.1","method":"GET","path":"/"},"endpoints":[{"path":"/","method":"GET","description":"Service information"},{"path":"/health","method":"GET","description":"Health check"}]}

curl -s http://localhost:8000/health
{"status":"healthy","timestamp":"2026-01-31T10:00:47.877931+00:00","uptime_seconds":11}
```

**Docker Hub repository URL:**
```
https://hub.docker.com/r/nexonm22/devops-info-service
```

**Push output (lab02 tag):**
```
docker push nexonm22/devops-info-service:lab02
...
lab02: digest: sha256:d1fb93a54744bbfde3af86f049e6dd6c87cb5ca042e7136168bbf596ff03fa99 size: 856
```

## 4. Technical Analysis

- **Why this Dockerfile works**: a slim, pinned base + explicit dependencies + minimal app copy results in a predictable, smaller image. The runtime is non-root and uses a fixed entrypoint (`python app.py`) that matches local behavior.
- **Layer order impact**: copying all files before installing dependencies would invalidate cache on each code change, slowing builds and increasing network downloads.
- **Security considerations**: non-root user reduces blast radius; smaller image reduces attack surface.
- **.dockerignore benefits**: reduces build context size and prevents leaking local/dev artifacts into the image.

## 5. Challenges & Solutions

- **Challenge**: docker daemon access blocked in restricted environment.
  - **Solution**: re-ran build with full permissions; build and run succeeded.
- **Challenge**: Docker Hub push requires valid credentials.
  - **Solution**: tag/push commands prepared; pending login and credentials.
