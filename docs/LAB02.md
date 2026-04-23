## 1. Docker Best Practices Applied

### 1.1 Specific base image version
**What I did:** Used a pinned Python base image tag (e.g., `python:3.13-slim`).
**Why it matters:** Pinning the version improves reproducibility (same base OS/Python each build) and reduces “works on my machine” issues when grading/CI runs.

### 1.2 Non-root user (mandatory)
**What I did:** Created a dedicated unprivileged user and switched to it using USER.
**Why it matters:** Running as non-root reduces impact if the service is compromised (smaller blast radius inside the container), and it is explicitly required by the lab.

Dockerfile snippet:

```dockerfile
RUN useradd --create-home --shell /usr/sbin/nologin appuser \
    && chown -R appuser:appuser /app
USER appuser
```

### 1.3 Proper layer ordering (dependency caching)
**What I did:** Copied requirements.txt first, installed dependencies, then copied application code.
**Why it matters:** Docker caches layers; when only code changes, dependency layers can be reused, making rebuilds much faster.

Dockerfile snippet:

```dockerfile
COPY requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt
COPY app.py ./app.py
```

### 1.4 Only copy necessary files
**What I did:** Copied only runtime files needed to execute (requirements.txt, app.py) rather than the entire repository.
**Why it matters:** Smaller images, fewer accidental secrets/dev files shipped, and fewer invalidating changes to Docker cache.

### 1.5 .dockerignore file
**What I did:** Added .dockerignore to exclude venv, caches, git metadata, IDE files, docs/tests not needed at runtime.
**Why it matters:** Excluding files reduces build context size (faster builds) and prevents accidental inclusion of unnecessary artifacts.

## 2. Image Information & Decisions
### 2.1 Base image choice
**Chosen base image:** python:3.13-slim.
**Justification:** The lab explicitly suggests slim variants and slim keeps the runtime smaller than full images while staying compatible with typical Python wheels.

### 2.2 Final image size
**Final image size:** 54.6MB

### 2.3 Layer structure explanation

- Layer 1: Base image (python:3.13-slim).
- Layer 2: Dependency install step (cached unless requirements.txt changes).
- Layer 3: Application code copy (changes frequently).

### 2.4 Optimization choices

- Used slim image variant.
- Installed dependencies before copying source to maximize cache reuse.
- Used .dockerignore to reduce build context.

## 3. Build & Run Process

```bash
/mnt/both/ewewe/Innopolis/DevOps-Core-Course lab02*
venv ❯ sudo docker build -t graymansion/devops-info-service:lab02 -f app_python/Dockerfile app_python
DEPRECATED: The legacy builder is deprecated and will be removed in a future release.
            Install the buildx component to build images with BuildKit:
            https://docs.docker.com/go/buildx/

Sending build context to Docker daemon  10.24kB
Step 1/10 : FROM python:3.13-slim
 ---> 2b9c9803c6a2
Step 2/10 : ENV PYTHONDONTWRITEBYTECODE=1     PYTHONUNBUFFERED=1
 ---> Using cache
 ---> 0e2cc88a0917
Step 3/10 : WORKDIR /app
 ---> Using cache
 ---> 6fc6ee55547e
Step 4/10 : COPY requirements.txt ./requirements.txt
 ---> Using cache
 ---> 6013ad21aed2
Step 5/10 : RUN pip install --no-cache-dir -r requirements.txt
 ---> Using cache
 ---> 10cdeb31b886
Step 6/10 : COPY app.py ./app.py
 ---> Using cache
 ---> 401d444fac03
Step 7/10 : RUN useradd --create-home --shell /usr/sbin/nologin appuser     && chown -R appuser:appuser /app
 ---> Using cache
 ---> 21fe52eaa4fd
Step 8/10 : USER appuser
 ---> Using cache
 ---> cf3406c9e1b0
Step 9/10 : EXPOSE 5000
 ---> Using cache
 ---> f161e3ec5949
Step 10/10 : CMD ["python", "app.py"]
 ---> Using cache
 ---> c06e6ce86225
Successfully built c06e6ce86225
Successfully tagged graymansion/devops-info-service:lab02

/mnt/both/ewewe/Innopolis/DevOps-Core-Course lab02*
venv ❯ sudo docker run --rm -p 8080:5000 graymansion/devops-info-service:lab02
2026-02-04 14:58:23,807 - devops-info-service - INFO - Starting app on 0.0.0.0:5000 (debug=False)
INFO:     Started server process [1]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:5000 (Press CTRL+C to quit)
2026-02-04 14:59:23,540 - devops-info-service - INFO - Request: GET /
INFO:     172.17.0.1:43594 - "GET / HTTP/1.1" 200 OK
2026-02-04 14:59:23,727 - devops-info-service - INFO - Request: GET /favicon.ico
INFO:     172.17.0.1:43594 - "GET /favicon.ico HTTP/1.1" 404 Not Found
2026-02-04 14:59:30,500 - devops-info-service - INFO - Request: GET /health
INFO:     172.17.0.1:34642 - "GET /health HTTP/1.1" 200 OK
^CINFO:     Shutting down
INFO:     Waiting for application shutdown.
INFO:     Application shutdown complete.
INFO:     Finished server process [1]
```

## 4. Technical Analysis
### 4.1 Why this Dockerfile works
`WORKDIR` sets a predictable working directory inside the container.

Dependencies are installed from `requirements.txt`, so runtime has all needed packages before starting.

`CMD ["python", "app.py"]` starts the service exactly like local execution (same code path).

### 4.2 What if the layer order changed?
If I copied the entire application code before installing dependencies, then every code change would invalidate the cache for dependency installation, causing slower rebuilds.

### 4.3 Security considerations implemented
- Runs as a non-root user, reducing privileges inside the container (required by lab).
- Copies only needed runtime files, reducing the chance of leaking dev artifacts.

### 4.4 How .dockerignore improves build
It reduces the build context sent to the Docker daemon, making builds faster and preventing unnecessary files from being included or affecting caching.

## 5. Challenges & Solutions

### Challenge 1: Accessing 0.0.0.0 in browser
**Problem:** Container logs show 0.0.0.0:5000, but the host access must use localhost:<published_port>.
**Solution:** Use http://127.0.0.1:8080/ because of -p 8080:5000 port publishing.
**What I learned:** 0.0.0.0 is a bind address; the host-facing port is controlled by Docker port mapping.

### Challenge 2: Docker Hub push authorization failed
**Problem:** In attempt to publish image to Docker Hub, `docker push` failed with an authorization error `insufficient_scope: authorization failed`.
**Solution:** Solved by logging into Docker Hub explicitly as my account using:
```bash
docker login -u graymansion
```
**What I learned:** Docker Hub permissions are tied to the authenticated user and the repository namespace. Even if the image tag looks correct, pushing will fail unless the Docker client is logged in as the account that has write access to that repository.