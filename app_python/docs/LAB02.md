# Lab 02 — Docker Containerization

## Docker Best Practices Applied

### 1. Non-root user

```dockerfile
RUN groupadd -r appuser && useradd -r -g appuser -d /app -s /sbin/nologin appuser
USER appuser
```

**Why:** Running as root inside a container means a container escape vulnerability gives the attacker root on the host. A non-root user limits the blast radius — even if the container is compromised, the attacker has restricted permissions.

### 2. Specific base image version

```dockerfile
FROM python:3.13-slim
```

**Why:** Using `python:latest` or `python:3` means your image can change without warning when a new version is released. Pinning `3.13-slim` ensures reproducible builds — the same Dockerfile produces the same image every time.

**Why slim:** The full `python:3.13` image is ~1 GB (includes gcc, build tools). The `slim` variant is ~150 MB — it has everything needed to run Python apps but strips build tools we don't need.

### 3. Layer ordering (dependencies before code)

```dockerfile
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
```

**Why:** Docker caches each layer. Dependencies change rarely, application code changes often. By copying `requirements.txt` first and installing dependencies in a separate layer, Docker reuses the cached dependency layer on every code change. This makes rebuilds take seconds instead of minutes.

### 4. .dockerignore

**Why:** Without `.dockerignore`, Docker sends the entire directory as build context to the daemon — including `venv/` (hundreds of MBs), `.git/`, docs, tests. This slows down builds and can leak secrets into the image. The `.dockerignore` keeps the build context minimal.

### 5. --no-cache-dir for pip

```dockerfile
RUN pip install --no-cache-dir -r requirements.txt
```

**Why:** pip caches downloaded packages by default for faster reinstalls. Inside a Docker image, there are no reinstalls — the cache just wastes space. `--no-cache-dir` keeps the image smaller.

## Image Information & Decisions

- **Base image:** `python:3.13-slim` — Debian-based minimal Python image. Chosen over `alpine` because alpine uses musl libc which can cause compatibility issues with some Python packages. Slim provides a good balance of size and compatibility.
- **Final image size:** ~170 MB (run `docker images` to verify)
- **Layer structure:**
  1. Base image (python:3.13-slim)
  2. User creation
  3. Working directory
  4. Copy requirements.txt
  5. Install dependencies (cached unless requirements change)
  6. Copy application code
  7. Set ownership and switch to non-root user

## Build & Run Process

### Build

```bash
cd app_python
docker build -t devops-info-service .
```

### Run

```bash
docker run -p 8000:8000 devops-info-service
```

### Test

```bash
curl http://localhost:8000/
curl http://localhost:8000/health
```

### Docker Hub

```bash
docker tag devops-info-service 4hellboy4/devops-info-service:latest
docker login
docker push 4hellboy4/devops-info-service:latest
```

**Docker Hub URL:** `https://hub.docker.com/r/4hellboy4/devops-info-service`

## Technical Analysis

**Why this layer order works:** The most frequently changing layers (application code) are at the bottom. When you change `app.py`, Docker rebuilds from `COPY . .` onwards — the dependency installation layer above it is cached. If dependencies were copied together with code, every code change would reinstall all packages.

**What if layer order changed:** If we did `COPY . .` before `pip install`, changing any source file would invalidate the pip install cache. Every build would re-download and install all dependencies from scratch.

**Security considerations:**
- Non-root user prevents privilege escalation
- Slim base image has fewer packages = smaller attack surface
- `.dockerignore` prevents secrets and unnecessary files from entering the image
- No shell login for the app user (`/sbin/nologin`)

**How .dockerignore helps:**
- Excludes `venv/` (~100+ MB) from build context
- Excludes `.git/` (repository history, potentially large)
- Faster `docker build` since less data is sent to the daemon

## Challenges & Solutions

1. **Choosing between slim and alpine** — Alpine images are smaller (~50 MB) but use musl libc, which can cause issues with Python packages that depend on glibc. Chose slim for reliability.
2. **File permissions** — Application files are copied as root, so `chown` is needed before switching to the non-root user, otherwise the app can't read its own files.
