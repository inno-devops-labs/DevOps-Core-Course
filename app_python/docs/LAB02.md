# Lab 2 — Docker Containerization (Python App)

## 1. Docker Best Practices Applied

- **Non-root user**
  The Dockerfile creates a dedicated `appuser` user and switches to it using the `USER` instruction. Running as non-root limits the impact of a compromise inside the container because the process no longer has full root privileges on the container filesystem or potential host mounts.
  - **Snippet**:
    ```dockerfile
    RUN groupadd --system appuser && useradd --system --create-home --gid appuser appuser
    USER appuser
    ```

- **Specific base image version**
  The image uses `python:3.13-slim` as the base. Pinning to a specific version makes builds reproducible and predictable. The `slim` variant reduces the image size by excluding unnecessary OS packages while still being easy to work with.
  - **Snippet**:
    ```dockerfile
    FROM python:3.13-slim AS runtime
    ```

- **Layer caching with dependencies before code**
  `requirements.txt` is copied and dependencies are installed before copying the application code. When only the app code changes, the dependency layer remains cached, which makes rebuilds much faster and avoids repeatedly downloading and installing the same packages.
  - **Snippet**:
    ```dockerfile
    COPY requirements.txt .
    RUN pip install --no-cache-dir --upgrade pip \
        && pip install --no-cache-dir -r requirements.txt

    COPY app.py .
    ```

- **.dockerignore usage**
  A `.dockerignore` file excludes caches, logs, virtual environments, VCS metadata, docs, and tests from the build context.Reduces the amount of data sent to the Docker daemon, speeds up builds, and ensures sensitive or unnecessary files (like `.git` and local venvs) do not end up in the image layers.
  - **Snippet**:
    ```text
    __pycache__/
    *.py[cod]
    venv/
    .venv/
    .git
    docs/
    tests/
    ```

- **Minimal runtime surface**
  Only `app.py` and the installed dependencies are copied into the image; no tests, tooling, or development artifacts are included. A smaller runtime image has fewer components that could be exploited and typically results in faster pulls and startups.

## 2. Image Information & Decisions

- **Base image choice**
  - Chosen base: `python:3.13-slim`.
  - Reasoning: Modern Python version aligned with the lab requirements, official and well-maintained image, and `slim` reduces size versus the full image while staying more convenient than `alpine` for typical Python dependencies.

- **Final image size**
  `devops-info-service-python` ~`49.9MB` MB.
  - Assessment: The size is acceptable for a small web service and can be further reduced if needed (e.g., by using multi-stage builds or more minimal base images).

- **Layer structure**
  - OS and Python runtime from `python:3.13-slim`.
  - Dependency installation layer from `requirements.txt`.
  - Application code layer with `app.py`.
  - This structure ensures that frequent code changes only invalidate the top layer.

- **Optimization choices**
  - Used `--no-cache-dir` for `pip` to avoid caching wheels and package archives in the final image.
  - Removed `apt` cache (`rm -rf /var/lib/apt/lists/*`) after security updates to keep the OS layer smaller.

## 3. Build & Run Process

### 3.1 Build Output

```text
# docker build -t pickpusha/devops-info-service-python:lab2 app_python
```
![alt](/app_python/docs/screenshots/docker-build.jpg)

### 3.2 Run Output

```text
# docker run --rm -p 5000:5000 pickpusha/devops-info-service-python:lab2

```

### 3.3 Endpoint Testing

```text
# curl -s http://localhost:5000/ | jq .

# curl -s http://localhost:5000/health | jq .

```
![alt](/app_python/docs/screenshots/docker-run-main.jpg)
![alt](/app_python/docs/screenshots/docker-run-health.jpg)

### 3.4 Docker Hub Repository

- **Repository URL**: `<https://hub.docker.com/r/pickpusha/devops-info-service-python>`

## 4. Technical Analysis

- **Why the Dockerfile works this way**
  - The base image provides a minimal Debian-based environment with Python 3.13 pre-installed.
  - Dependencies are installed in a dedicated layer so that they can be reused across rebuilds.
  - The application relies on environment variables (`HOST`, `PORT`, `DEBUG`) which makes it flexible to configure at runtime without changing the image.

- **Effect of changing layer order**
  - If application code were copied before `requirements.txt`, any code change would invalidate the dependency layer, forcing `pip install` to run on every build and significantly slowing down the feedback loop.
  - Moving `.dockerignore` entries or omitting them would increase build context size and might accidentally ship development-only files in the final image.

- **Security considerations**
  - Non-root execution reduces the impact of potential RCE vulnerabilities.
  - Regular security updates are applied at build time via `apt-get update && apt-get upgrade`.
  - A minimal base image and tight `.dockerignore` reduce the attack surface by including fewer tools and files.

- **Impact of .dockerignore on build**
  - By excluding virtual environments, Git metadata, and docs, the context sent to the daemon is much smaller, which speeds up `docker build` and keeps the resulting layers focused only on what is required at runtime.

## 5. Challenges & Solutions

The lab insructions are clear enough. Also I've already been familiar with Docker and his approaches so this lab was pretty simple. One thing that I reminded from this lab was using the non-root user for better security.

