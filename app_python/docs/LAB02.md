# Lab 2 Submission: Docker Containerization (Python App)

## 1. Docker Best Practices Applied

### 1.1 Use a Specific Base Image Version

**Practice:** Pin the base image to a specific, slimmed-down Python version.

**Implementation (Dockerfile):**

```Dockerfile
FROM python:3.13-slim
```

**Why it matters:**
- Ensures reproducible builds (same Python version everywhere).
- `slim` variant removes unnecessary tools, reducing image size and attack surface.
- Easier to reason about compatibility and security updates.

---

### 1.2 Non-Root User

**Practice:** Do not run the application as `root` inside the container.

**Implementation:**

```Dockerfile
RUN addgroup --system app && adduser --system --ingroup app app
USER app
```

**Why it matters:**
- Limits the blast radius if the application is compromised.
- Follows the principle of least privilege.
- Many security scanners and platforms now *require* non-root containers.

---

### 1.3 Layer Caching & Dependency Installation

**Practice:** Install dependencies in a separate layer before copying application code.

**Implementation:**

```Dockerfile
WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app.py .
```

**Why it matters:**
- Docker caches layers. Dependencies change less frequently than source code.
- When only `app.py` changes, Docker reuses the dependency layer and rebuilds much faster.
- `--no-cache-dir` avoids storing wheel caches inside the image, reducing size.

---

### 1.4 Minimize What You Copy

**Practice:** Only copy the files needed at runtime.

**Implementation:**

```Dockerfile
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app.py .
```

**Why it matters:**
- Keeps the image smaller by excluding tests, docs, virtualenvs, and git metadata.
- Reduces the attack surface (less code and tools inside the container).
- Faster image distribution and startup times.

This is reinforced by `.dockerignore`, which excludes unnecessary files from the build context.

---

### 1.5 .dockerignore

**Practice:** Use `.dockerignore` to avoid sending unnecessary files to the Docker daemon.

**Implementation (`app_python/.dockerignore`):**

```dockerignore
__pycache__/
*.py[cod]
*.pyo
*.pyd

venv/
.venv/

.git
.gitignore

.vscode/
.idea/

tests/
docs/

*.log
*.md
```

**Why it matters:**
- Smaller build context → faster uploads to the Docker daemon → faster builds.
- Avoids accidentally copying secrets, virtual environments, and dev tooling into the image.
- Mirrors many patterns from `.gitignore`, following common DevOps practice.

---

### 1.6 Environment Configuration & Logging

**Practice:** Configure runtime via environment variables and ensure unbuffered logs.

**Implementation:**

```Dockerfile
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

ENV HOST=0.0.0.0 \
    PORT=5000
```

**Why it matters:**
- `PYTHONUNBUFFERED=1` ensures logs appear immediately in container logs (important for monitoring).
- `PYTHONDONTWRITEBYTECODE=1` avoids `.pyc` files and reduces filesystem noise.
- Environment variables make the same image reusable across environments (dev/stage/prod).

---

## 2. Image Information & Decisions

### 2.1 Base Image Choice

**Chosen image:** `python:3.13-slim`

**Justification:**
- Matches the course requirement for Python 3.13.
- `slim` variant is significantly smaller than the full image while still being easy to work with.
- Based on Debian, which has familiar package management and good security support.

Alternative options would be:
- `python:3.13` (larger, includes build tools we don't need at runtime).
- `python:3.13-alpine` (smaller, but can cause compatibility issues with some wheels and glibc).

`3.13-slim` is a good balance between size, compatibility, and simplicity.

---

### 2.2 Final Image Size (Example)

After building the image:

```bash
docker images | grep devops-info-service
```

Example output:

```bash
j0cos/devops-info-service   lab02       a98f3b0fd122   56 seconds ago   122MB
```

**Assessment:**
- This is reasonable for a Python + Flask application with `python:3.13-slim` as the base.
- There is still room for optimization (e.g., using `--no-cache-dir`, removing build tools, reducing layers), many of which are already applied.

---

### 2.3 Layer Structure

High-level layer structure:

1. **Base image**: `FROM python:3.13-slim`
2. **System configuration**: Create non-root user
3. **Workdir**: `WORKDIR /app`
4. **Dependencies**: `COPY requirements.txt` + `RUN pip install ...`
5. **Application code**: `COPY app.py .`
6. **Runtime config**: `ENV`, `EXPOSE`, `USER`, `CMD`

**Why this order works well:**
- Dependency installation is separated from application code for better caching.
- User creation happens once and is reused for all subsequent layers.
- Runtime configuration (`ENV`, `EXPOSE`, `CMD`) is unlikely to change often.

---

### 2.4 Optimization Choices

- Used `python:3.13-slim` instead of `python:3.13`.
- Installed dependencies with `--no-cache-dir`.
- Avoided copying tests, docs, and virtualenvs into the image.
- Configured logging to be unbuffered for better observability.

Each choice reduces size, speeds up builds, or improves security/observability.

---

## 3. Build & Run Process

### 3.1 Build Command

From `DevOps-Core-Course/app_python/`:

```bash
docker build -t j0cos/devops-info-service:lab02 .
```

Output (truncated):

```bash
DEPRECATED: The legacy builder is deprecated and will be removed in a future release.
            Install the buildx component to build images with BuildKit:
            https://docs.docker.com/go/buildx/

Sending build context to Docker daemon  9.216kB
Step 1/11 : FROM python:3.13-slim
3.13-slim: Pulling from library/python
0c8d55a45c0d: Pull complete 
8a3ca8cbd12d: Pull complete 
b3639af23419: Pull complete 
0da4a108bcf2: Pull complete 
Digest: sha256:2b9c9803c6a287cafa0a8c917211dddd23dcd2016f049690ee5219f5d3f1636e
Status: Downloaded newer image for python:3.13-slim
 ---> 464f788e6eab
Step 2/11 : ENV PYTHONDONTWRITEBYTECODE=1     PYTHONUNBUFFERED=1
 ---> Running in bbff488f9a3b
 ---> Removed intermediate container bbff488f9a3b
 ---> 927f18f003c3
Step 3/11 : RUN addgroup --system app && adduser --system --ingroup app app
 ---> Running in a14d124dc0b0
 ---> Removed intermediate container a14d124dc0b0
 ---> 43e066430c56
Step 4/11 : WORKDIR /app
 ---> Running in 957da0cf7e7e
 ---> Removed intermediate container 957da0cf7e7e
 ---> d73b1ecfb9fd
Step 5/11 : COPY requirements.txt .
 ---> 3c99e774ec3d
Step 6/11 : RUN pip install --no-cache-dir -r requirements.txt
 ---> Running in 5fdefb26aaa0
Collecting Flask==3.1.0 (from -r requirements.txt (line 2))
  Downloading flask-3.1.0-py3-none-any.whl.metadata (2.7 kB)
Collecting Werkzeug>=3.1 (from Flask==3.1.0->-r requirements.txt (line 2))
  Downloading werkzeug-3.1.5-py3-none-any.whl.metadata (4.0 kB)
Collecting Jinja2>=3.1.2 (from Flask==3.1.0->-r requirements.txt (line 2))
  Downloading jinja2-3.1.6-py3-none-any.whl.metadata (2.9 kB)
Collecting itsdangerous>=2.2 (from Flask==3.1.0->-r requirements.txt (line 2))
  Downloading itsdangerous-2.2.0-py3-none-any.whl.metadata (1.9 kB)
Collecting click>=8.1.3 (from Flask==3.1.0->-r requirements.txt (line 2))
  Downloading click-8.3.1-py3-none-any.whl.metadata (2.6 kB)
Collecting blinker>=1.9 (from Flask==3.1.0->-r requirements.txt (line 2))
  Downloading blinker-1.9.0-py3-none-any.whl.metadata (1.6 kB)
Collecting MarkupSafe>=2.0 (from Jinja2>=3.1.2->Flask==3.1.0->-r requirements.txt (line 2))
  Downloading markupsafe-3.0.3-cp313-cp313-manylinux2014_x86_64.manylinux_2_17_x86_64.manylinux_2_28_x86_64.whl.metadata (2.7 kB)
Downloading flask-3.1.0-py3-none-any.whl (102 kB)
Downloading blinker-1.9.0-py3-none-any.whl (8.5 kB)
Downloading click-8.3.1-py3-none-any.whl (108 kB)
Downloading itsdangerous-2.2.0-py3-none-any.whl (16 kB)
Downloading jinja2-3.1.6-py3-none-any.whl (134 kB)
Downloading markupsafe-3.0.3-cp313-cp313-manylinux2014_x86_64.manylinux_2_17_x86_64.manylinux_2_28_x86_64.whl (22 kB)
Downloading werkzeug-3.1.5-py3-none-any.whl (225 kB)
Installing collected packages: MarkupSafe, itsdangerous, click, blinker, Werkzeug, Jinja2, Flask

Successfully installed Flask-3.1.0 Jinja2-3.1.6 MarkupSafe-3.0.3 Werkzeug-3.1.5 blinker-1.9.0 click-8.3.1 itsdangerous-2.2.0
WARNING: Running pip as the 'root' user can result in broken permissions and conflicting behaviour with the system package manager, possibly rendering your system unusable. It is recommended to use a virtual environment instead: https://pip.pypa.io/warnings/venv. Use the --root-user-action option if you know what you are doing and want to suppress this warning.

[notice] A new release of pip is available: 25.3 -> 26.0
[notice] To update, run: pip install --upgrade pip
 ---> Removed intermediate container 5fdefb26aaa0
 ---> 909712b3944f
Step 7/11 : COPY app.py .
 ---> 51ab146314bd
Step 8/11 : EXPOSE 5000
 ---> Running in 44104e9c0f4b
 ---> Removed intermediate container 44104e9c0f4b
 ---> b5fe80d73d2b
Step 9/11 : USER app
 ---> Running in 18b6c35bf31a
 ---> Removed intermediate container 18b6c35bf31a
 ---> b2e8ac99c380
Step 10/11 : ENV HOST=0.0.0.0     PORT=5000
 ---> Running in e98fa6e4d248
 ---> Removed intermediate container e98fa6e4d248
 ---> b7de34239e76
Step 11/11 : CMD ["python", "app.py"]
 ---> Running in ccab856df5e2
 ---> Removed intermediate container ccab856df5e2
 ---> a98f3b0fd122
Successfully built a98f3b0fd122
Successfully tagged j0cos/devops-info-service:lab02
```

---

### 3.2 Run Command

```bash
docker run \
  -p 5000:5000 \
  -e HOST=0.0.0.0 \
  -e PORT=5000 \
  j0cos/devops-info-service:lab02
```

Logs:

```bash
2026-02-04 11:16:36,870 - __main__ - INFO - Application starting...
2026-02-04 11:16:36,871 - __main__ - INFO - Starting server on 0.0.0.0:5000
 * Serving Flask app 'app'
 * Debug mode: off
2026-02-04 11:16:36,893 - werkzeug - INFO - WARNING: This is a development server. Do not use it in a production deployment. Use a production WSGI server instead.
 * Running on all addresses (0.0.0.0)
 * Running on http://127.0.0.1:5000
 * Running on http://172.17.0.2:5000
2026-02-04 11:16:36,893 - werkzeug - INFO - Press CTRL+C to quit
2026-02-04 11:16:49,994 - __main__ - INFO - Request: GET / from 172.17.0.1
2026-02-04 11:16:50,019 - werkzeug - INFO - 172.17.0.1 - - [04/Feb/2026 11:16:50] "GET / HTTP/1.1" 200 -
2026-02-04 11:16:50,061 - werkzeug - INFO - 172.17.0.1 - - [04/Feb/2026 11:16:50] "GET /favicon.ico HTTP/1.1" 404 -
2026-02-04 11:16:52,220 - __main__ - INFO - Request: GET / from 172.17.0.1
2026-02-04 11:16:52,221 - werkzeug - INFO - 172.17.0.1 - - [04/Feb/2026 11:16:52] "GET / HTTP/1.1" 200 -
```

---

### 3.3 Testing Endpoints

From the host machine:

```bash
# Main endpoint
curl http://localhost:5000/ | jq

# Health endpoint
curl http://localhost:5000/health
```


Main output:

```bash
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
    "client_ip": "172.17.0.1",
    "method": "GET",
    "path": "/",
    "user_agent": "curl/8.5.0"
  },
  "runtime": {
    "current_time": "2026-02-04T11:21:45.950829.000Z",
    "timezone": "UTC",
    "uptime_human": "0 hours, 0 minutes",
    "uptime_seconds": 17
  },
  "service": {
    "description": "DevOps course info service",
    "framework": "Flask",
    "name": "devops-info-service",
    "version": "1.0.0"
  },
  "system": {
    "architecture": "x86_64",
    "cpu_count": 12,
    "hostname": "29d5c4accb0a",
    "platform": "Linux",
    "platform_version": "Linux-6.8.0-58-generic-x86_64-with-glibc2.41",
    "python_version": "3.13.11"
  }
}
```

Health output:

```bash
{
  "status": "healthy",
  "timestamp": "2026-02-04T11:21:57.097297.000Z",
  "uptime_seconds": 28
}
```

---

### 3.4 Docker Hub Repository

After logging in and pushing:

```bash
docker login
docker push j0cos/devops-info-service:lab02
```

```bash
The push refers to repository [docker.io/j0cos/devops-info-service]
44fb1c8fbe87: Pushed 
dea3653b387c: Pushed 
6cb2be6a4910: Pushed 
a10bb9028af7: Pushed 
111dcdd3167b: Pushed 
6f3d061c2e62: Mounted from library/python 
1a619cfa942c: Mounted from library/python 
c07c86e6f1e8: Mounted from library/python 
a8ff6f8cbdfd: Mounted from library/python 
lab02: digest: sha256:26829ce1b6858f8e0b7509639e9581d53be83e151afe1d8a5b29b90a5a3eb85f size: 2199
```

#### Naming Strategy
I use <dockerhub-username>/devops-info-service as the repository name and add descriptive tags like lab02 (for this lab’s version) and latest (for the most recent stable build). This makes it clear who owns the image, what service it contains, and which version or lab iteration it corresponds to.

**Docker Hub URL:** https://hub.docker.com/repository/docker/j0cos/devops-info-service/general


---

## 4. Technical Analysis

### 4.1 Why the Dockerfile Works This Way

- The base image provides Python and OS libraries.
- Environment variables configure Python behavior and runtime defaults.
- Dependency installation is separated for caching efficiency.
- Only the application file is copied, minimizing the image contents.
- The non-root user is used for better security.
- `CMD ["python", "app.py"]` starts the Flask app in the same way as local development.

---

### 4.2 Effect of Changing Layer Order

If we changed the order to copy `app.py` **before** `requirements.txt`:

```Dockerfile
COPY . .
RUN pip install --no-cache-dir -r requirements.txt
```

**Consequences:**
- Any small code change invalidates the cache for the `pip install` layer.
- Builds become much slower because dependencies are reinstalled on every change.
- More data is sent to the Docker daemon because we copy everything by default.

Keeping dependencies in an earlier, more stable layer dramatically speeds up rebuilds.

---

### 4.3 Security Considerations

Security practices implemented:
- Running as a non-root user.
- Using a smaller base image (`slim`) to reduce attack surface.
- Excluding development files and secrets via `.dockerignore`.
- Keeping only runtime dependencies inside the image.

Potential future improvements:
- Add image scanning (e.g., `docker scan` or Snyk).
- Pin dependencies in `requirements.txt` more strictly and update regularly.

---

### 4.4 .dockerignore Impact

Without `.dockerignore`:
- The entire project directory (including `venv/`, `.git/`, and docs) would be sent to the Docker daemon.
- Build context size could be hundreds of megabytes.
- Builds would be slower and images might accidentally contain secrets or dev tools.

With `.dockerignore`:
- Build context stays small and focused.
- Image size is smaller and cleaner.
- Fewer surprises in production environments.

---

## 5. Challenges & Solutions

### Challenge 1: Choosing the Right Base Image

**Problem:** Deciding between `python:3.13`, `python:3.13-slim`, and `python:3.13-alpine`.

**Solution:** Chose `python:3.13-slim` as a balance between size and compatibility. Alpine can cause issues with some Python packages, and the full image is unnecessarily large.

**Lesson:** Base image choice affects size, security, and compatibility. Slim images are a good default for many Python services.

---

### Challenge 2: Designing .dockerignore

**Problem:** Deciding what to exclude without blindly copying a huge template.

**Solution:** Started from `.gitignore` patterns and added:
- Virtual environments
- Docs
- Tests
- IDE configuration

**Lesson:** `.dockerignore` is as important as `.gitignore` for performance and security.

---

## 6. Summary

In this lab, I:
- Containerized the Flask application using a production-ready Dockerfile.
- Applied Docker best practices (non-root, layer caching, minimal image contents, `.dockerignore`).
- Documented how to build, run, and publish the image to Docker Hub.
- Analyzed the technical and security implications of design choices.

The result is a reproducible, portable container image that behaves the same way as the local Python application, but is much easier to run in modern containerized environments.

