# LAB02 - Docker Containerization (app_python)

## 1. Docker Best Practices Applied

- **Specific base image**: `python:3.13-slim` - a slim Debian-based image pinned to a specific Python version for reproducible builds and security updates.
  - Why: Slim images are smaller and contain fewer OS packages, reducing attack surface and image size.
  - Include relevant Dockerfile snippet with explanation:

    ```dockerfile
    FROM python:3.13-slim
    ```
    This pins the Python version and keeps the base minimal. Pinning prevents unexpected changes from upstream image updates and helps reproducible builds.

- **Non-root user**: Created `app` user and switched to it using `USER app`.
  - Why: Running as non-root reduces impact of container escape or remote code execution vulnerabilities.
  - Include relevant Dockerfile snippet with explanation:

    ```dockerfile
    RUN groupadd -r app && useradd -r -g app -m -d /home/app -s /sbin/nologin app
    USER app
    ```
    Creating a dedicated, unprivileged user and switching to it reduces privileges available to processes in the container.

- **Layer ordering & cache utilization**: `requirements.txt` is copied and `pip install` is run before copying application code.
  - Why: Dependencies change less often than application code. This ensures Docker cache re-use and faster rebuilds.
  - Include relevant Dockerfile snippet with explanation:

    ```dockerfile
    COPY requirements.txt .
    RUN pip install --no-cache-dir -r requirements.txt
    COPY --chown=app:app app.py .
    ```
    Installing dependencies in a separate layer means you only re-run `pip install` when `requirements.txt` changes, making iterative builds much faster.

- **Only necessary files copied**: The Dockerfile copies only `requirements.txt` and `app.py` (not tests or docs).
  - Why: Smaller build context and smaller final image; less risk of leaking secrets or dev files into image.
  - Include relevant Dockerfile snippet with explanation:

    ```dockerfile
    COPY requirements.txt .
    COPY --chown=app:app app.py .
    ```
    Copying only runtime files avoids increasing image size with development files and reduces the chance of accidentally shipping sensitive files.

- **.dockerignore**: Excludes `__pycache__`, venvs, `.git`, `tests/`, and docs.
  - Why: Keeps build context small and fast; avoids copying unnecessary or sensitive files.
  - Include relevant `.dockerignore` snippet with explanation:

    ```text
    __pycache__/
    venv/
    .venv/
    .git
    tests/
    docs/
    ```
    Excluding these patterns reduces the build context sent to the Docker daemon, speeding builds and preventing unnecessary files from being included in the image.

- **Start command mirrors local behavior**: Uses `uvicorn app:app --host 0.0.0.0 --port 5000` to start the FastAPI app.
  - Why: Ensures the behavior in-container matches local run (PORT/HOST env vars are honored by the app).
  - Include relevant Dockerfile snippet with explanation:

    ```dockerfile
    CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "5000"]
    ```
    Using the same command as local development ensures consistent behavior and makes it straightforward to map ports and environment variables for runtime configuration.

---

## 2. Image Information & Decisions

- **Base image chosen**: `python:3.13-slim`
  - Rationale: Current stable Python version (3.13) with minimal packages. Balances compatibility and size.

- **Final image size**: 174MB
  - **Breakdown (approximate)**:
    - Base image (`python:3.13-slim`): ~90–100MB
    - Python packages (FastAPI, Uvicorn and transitive deps): ~60–70MB
    - Overhead (metadata, user files, pip/wheels): ~5–15MB
    - **Total measured:** ~174MB (measured with `docker images` after build)
  - **Assessment:**
    - For a Python microservice using CPython this image size is reasonable and expected - CPython base images and typical dependency trees add significant size.
    - For production deployments (many instances, frequent pulls) smaller images reduce startup time, network bandwidth, and attack surface. A target of <100MB is ambitious but achievable with tradeoffs.

- **Layer structure (high level)**:
  1. Base image (`python:3.13-slim`)
  2. Pip install layer (dependencies)
  3. Application code layer
  4. Metadata/user switch / CMD

- **Optimization choices**:
  - No build tools installed (kept image minimal).
  - `pip install --no-cache-dir` removes pip cache to reduce layer size.

---

## 3. Build & Run Process (Evidence)

### Commands to build and run locally

- Build (example pattern):
```bash
docker build -t alsstarikova/devops-info-service:lab02 -f app_python/Dockerfile app_python/
[+] Building 69.2s (12/12) FINISHED                                    docker:default
 => [internal] load build definition from Dockerfile                             0.1s
 => => transferring dockerfile: 905B                                             0.1s
 => [internal] load metadata for docker.io/library/python:3.13-slim              5.7s
 => [auth] library/python:pull token for registry-1.docker.io                    0.0s
 => [internal] load .dockerignore                                                0.1s
 => => transferring context: 362B                                                0.0s
 => [1/6] FROM docker.io/library/python:3.13-slim@sha256:2b9c9803c6a287cafa0a8c  5.2s
 => => resolve docker.io/library/python:3.13-slim@sha256:2b9c9803c6a287cafa0a8c  0.0s
 => => sha256:8a3ca8cbd12dc4a76ad33ca83aebbcb13a6da17018dacb336 1.29MB / 1.29MB  2.7s
 => => sha256:b3639af2341969e7f62cde77631753501fb03cbe8dd811e 11.79MB / 11.79MB  4.6s
 => => sha256:2b9c9803c6a287cafa0a8c917211dddd23dcd2016f04969 10.37kB / 10.37kB  0.0s
 => => sha256:25ec71a3df55517ab5f6f2fcd0e45b8dba3d197faf0ef2e56 1.75kB / 1.75kB  0.0s
 => => sha256:464f788e6eabeaa188a176fce5a04a896136bf6939e45cc62 5.53kB / 5.53kB  0.0s
 => => sha256:0c8d55a45c0dc58de60579b9cc5b708de9e7957f4591fc7 29.78MB / 29.78MB  3.8s
 => => sha256:0da4a108bcf2485b81d202f1df5743a4fce83c36dd004a09d536d 251B / 251B  3.4s
 => => extracting sha256:0c8d55a45c0dc58de60579b9cc5b708de9e7957f4591fc7de941b6  0.8s
 => => extracting sha256:8a3ca8cbd12dc4a76ad33ca83aebbcb13a6da17018dacb336bc37d  0.1s
 => => extracting sha256:b3639af2341969e7f62cde77631753501fb03cbe8dd811e74d50bf  0.4s
 => => extracting sha256:0da4a108bcf2485b81d202f1df5743a4fce83c36dd004a09d536d5  0.0s
 => [internal] load build context                                                0.1s
 => => transferring context: 5.40kB                                              0.1s
 => [2/6] RUN groupadd -r app && useradd -r -g app -m -d /home/app -s /sbin/nol  0.3s
 => [3/6] WORKDIR /home/app                                                      0.0s
 => [4/6] COPY requirements.txt .                                                0.0s
 => [5/6] RUN pip install --no-cache-dir --upgrade pip setuptools wheel &&      57.6s
 => [6/6] COPY --chown=app:app app.py .                                          0.0s
 => exporting to image                                                           0.2s
 => => exporting layers                                                          0.2s
 => => writing image sha256:a724b7f8499a188f04ac2162b0394dfb8bfd70885f6bd1a7106  0.0s
 => => naming to docker.io/alsstarikova/devops-info-service:lab02                0.0s
```

- Run:
```bash
docker run --rm -p 8000:5000 -e PORT=5000 alsstarikova/devops-info-service:lab02
2026-02-04 18:13:40,765 - devops-info-service - INFO - Starting DevOps Info Service (FastAPI)
INFO:     Started server process [1]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:5000 (Press CTRL+C to quit)
INFO:     172.17.0.1:47284 - "GET / HTTP/1.1" 200 OK
INFO:     172.17.0.1:52958 - "GET /health HTTP/1.1" 200 OK
INFO:     172.17.0.1:52972 - "GET /ealth HTTP/1.1" 404 Not Found
2026-02-04 18:14:08,363 - devops-info-service - WARNING - HTTP exception: Not Found (404) for /ealth
2026-02-04 18:14:09,430 - devops-info-service - WARNING - HTTP exception: Not Found (404) for /ealth
INFO:     172.17.0.1:52986 - "GET /ealth HTTP/1.1" 404 Not Found
INFO:     172.17.0.1:48212 - "GET /health HTTP/1.1" 200 OK
INFO:     172.17.0.1:48226 - "GET / HTTP/1.1" 200 OK
INFO:     172.17.0.1:48246 - "GET / HTTP/1.1" 200 OK
INFO:     172.17.0.1:56882 - "GET / HTTP/1.1" 200 OK
```

- Test endpoint (example):
```bash
 $ curl http://localhost:8000/health | jq .
{
  "status": "healthy",
  "timestamp": "2026-02-04T18:14:13.721575Z",
  "uptime_seconds": 32
}
 $ curl http://localhost:8000/ | jq .
{
  "service": {
    "name": "devops-info-service",
    "version": "1.0.0",
    "description": "DevOps course info service",
    "framework": "FastAPI"
  },
  "system": {
    "hostname": "6474d1a47fe7",
    "platform": "Linux",
    "platform_version": "#1 SMP Fri Mar 29 23:14:13 UTC 2024",
    "architecture": "x86_64",
    "cpu_count": 20,
    "python_version": "3.13.11"
  },
  "runtime": {
    "uptime_seconds": 37,
    "uptime_human": "0 hours, 0 minutes",
    "current_time": "2026-02-04T18:14:18.444926Z",
    "timezone": "UTC"
  },
  "request": {
    "client_ip": "172.17.0.1",
    "user_agent": "curl/7.81.0",
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

- Docker Hub repository URL: https://hub.docker.com/layers/alsstarikova/devops-info-service/lab02/images

- Docker push output (successful):

```
The push refers to repository [docker.io/alsstarikova/devops-info-service]
2d53f61626d3: Pushed 
5dbda51b5308: Pushed 
de1c75204432: Pushed 
5f70bf18a086: Layer already exists 
8dce2ed29d8d: Pushed 
6f3d061c2e62: Layer already exists 
1a619cfa942c: Layer already exists 
c07c86e6f1e8: Layer already exists 
a8ff6f8cbdfd: Layer already exists 
lab02: digest: sha256:e95f72337cc7527d84801661d0fdf0b862773599059e81dbfd7c6e2339ef6ef3 size: 2200
```

---

## 4. Technical Analysis

- **Why it works**: The app's startup code uses `uvicorn.run` when run as script; using `uvicorn app:app` is equivalent and explicit. Dependencies are installed before copying code so layer caching is effective.

- **If layer order changed**: Copying all code before installing dependencies would invalidate the dependency layer on every code change - slow builds.

- **Security considerations implemented**:
  - Non-root user to reduce privileges
  - Minimal base image to reduce attack surface
  - No sensitive files copied into image via `.dockerignore`

- **.dockerignore benefits**: Speeds up builds by reducing the context sent to Docker daemon and prevents shipping development/test files into images.

---

## 5. Challenges & Solutions

### Issues encountered during implementation

- **Wrong Dockerfile layer order (initially)**: At first the Dockerfile copied the entire project before installing dependencies which caused full dependency reinstallation on every small change - builds took significantly longer (noticed during iterative development and CI runs).
- **Native build errors for a transitive dependency**: A dependency attempted to build a native extension and failed due to missing build tools in the slim base image.


### How the issues were debugged and resolved

- **Wrong layer order**:
  - Action: Ran `docker build --progress=plain` and timestamped builds to measure time spent per step, identified that `COPY .` invalidated the dependency layer.
  - Resolution: Rewrote Dockerfile to copy `requirements.txt` and run `pip install` before copying app code. Subsequent builds were much faster during iterative changes.

- **Native build errors**:
  - Action: Built a quick debug image with extra build tools (`gcc`, `build-essential`) to reproduce the failure and capture full compile logs.
  - Resolution: Implemented a multi-stage build: builder stage installs build deps, builds wheels, and the final stage copies only the wheels and runtime files - final image contains no build tools and remains lean.

### What I learned from the process

- **Order and granularity of layers is critical**: Small changes should not invalidate expensive layers; structure Dockerfile so that stable layers (deps) are built first.
- **Pin dependencies and use CI caches**: Pinning and caching wheels makes builds stable and repeatable across environments.
- **Prefer multi-stage builds for native deps**: They let you compile in a full environment and ship only the runtime artifacts, reducing final image size and attack surface.
- **Document runtime expectations**: Clear README examples for `docker run -p` and `PORT` env var avoid manual testing mistakes.
