# Lab 2 — Containerization with Docker

## Docker Best Practices Applied

### 1. Multi-Stage Build
**Implementation:**
```dockerfile
FROM python:3.13-slim AS builder
# ... build stage with dependencies
FROM python:3.13-slim
COPY --from=builder /opt/venv /opt/venv
```

**Importance:** Separates the build environment from the runtime environment, reducing the final image size by excluding build tools and intermediate files.

### 2. Non-Root User
**Implementation:**
```dockerfile
RUN groupadd -r appgroup && useradd -r -g appgroup appuser
USER appuser
```

**Importance:** Enhances security by following the principle of least privilege, minimizing potential damage if the container is compromised.

### 3. Layer Caching Optimization
**Implementation:**
```dockerfile
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
```

**Importance:** Docker caches layers. By copying requirements.txt first and installing dependencies, this layer is cached and only rebuilt when requirements change, speeding up subsequent builds.

### 4. .dockerignore File
**Implementation:** Created a comprehensive `.dockerignore` file to exclude unnecessary files (development artifacts, IDE files, git, etc.).

**Importance:** Reduces build context size, speeding up the build process and preventing sensitive or irrelevant files from being included.

### 5. Specific Base Image Version
**Implementation:** `python:3.13-slim` (instead of `python:latest` or `python:3.13`)

**Importance:** Ensures reproducible builds and avoids unexpected changes from base image updates.

### 6. Clean Package Installation
**Implementation:**
```dockerfile
RUN pip install --no-cache-dir -r requirements.txt
```

**Importance:** The `--no-cache-dir` flag prevents pip from caching packages, reducing image size.

### 7. System Dependency Cleanup
**Implementation:**
```dockerfile
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*
```

**Importance:** Removes the package lists after installation, reducing image size and keeping the image clean.

### 8. Virtual Environment Isolation
**Implementation:**
```dockerfile
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
```

**Importance:** Isolates application dependencies from the system Python, avoiding conflicts and making the environment reproducible.

## Image Information & Decisions

### Base Image Choice
**Selected:** `python:3.13-slim`

**Justification:**
- **slim variant** provides a minimal Python runtime without unnesecary extra tools
- **Specific version (3.13)** ensures reproducibility and avoids breaking changes from future updates
- **Alternative considered:** `python:3.13-alpine` (about 45MB) was rejected due to potential compatibility issues with some Python packages that require compiled binaries.

### Final Image Size
- **Final image size:** ~199MB

**Assessment:** The image size is reasonable for a Python application. The multi-stage build helps keep it minimal by excluding build tools. Further reduction could be achieved by using Alpine, but at the cost of potential compatibility issues.

### Layer Structure
The layer structure (from bottom to top):
1. **Base image layer:** `python:3.13-slim`
2. **System dependencies layer:** Installs gcc (builder stage)
3. **Python dependencies layer:** Creates virtual environment and installs packages (cached separately)
4. **Application code layer:** Copies the rest of the application
5. **Configuration layer:** Sets permissions, user, environment variables, and command

### Optimization Choices Made
1. **Multi-stage build:** Separates build and runtime, removing build tools from final image.
2. **Dependency layer caching:** Requirements are installed in a separate layer that caches well.
3. **Cleanup:** Removal of apt lists and pip cache.
4. **Non-root user:** Added for security without significant overhead.
5. **Virtual environment:** Ensures dependency isolation and easier path management.

## Build & Run Process

### Complete Terminal Output from Build Process
```bash
s3rap1s in ~/devops/DevOps-Core-Course/app_python on lab01 ● λ docker build -t devops-info-service:python .                              
[+] Building 2.1s (17/17) FINISHED                                                                                                                        docker:default
 => [internal] load build definition from Dockerfile                                                                                                                0.0s
 => => transferring dockerfile: 1.41kB                                                                                                                              0.0s
 => [internal] load metadata for docker.io/library/python:3.13-slim                                                                                                 1.9s
 => [auth] library/python:pull token for registry-1.docker.io                                                                                                       0.0s
 => [internal] load .dockerignore                                                                                                                                   0.0s
 => => transferring context: 321B                                                                                                                                   0.0s
 => [internal] load build context                                                                                                                                   0.0s
 => => transferring context: 63B                                                                                                                                    0.0s
 => [builder 1/6] FROM docker.io/library/python:3.13-slim@sha256:51e1a0a317fdb6e170dc791bbeae63fac5272c82f43958ef74a34e170c6f8b18                                   0.0s
 => => resolve docker.io/library/python:3.13-slim@sha256:51e1a0a317fdb6e170dc791bbeae63fac5272c82f43958ef74a34e170c6f8b18                                           0.0s
 => CACHED [stage-1 2/6] RUN groupadd -r appgroup && useradd -r -g appgroup appuser                                                                                 0.0s
 => CACHED [stage-1 3/6] WORKDIR /app                                                                                                                               0.0s
 => CACHED [builder 2/6] RUN apt-get update && apt-get install -y --no-install-recommends     gcc     && rm -rf /var/lib/apt/lists/*                                0.0s
 => CACHED [builder 3/6] WORKDIR /app                                                                                                                               0.0s
 => CACHED [builder 4/6] RUN python -m venv /opt/venv                                                                                                               0.0s
 => CACHED [builder 5/6] COPY requirements.txt .                                                                                                                    0.0s
 => CACHED [builder 6/6] RUN pip install --no-cache-dir --upgrade pip &&     pip install --no-cache-dir -r requirements.txt                                         0.0s
 => CACHED [stage-1 4/6] COPY --from=builder /opt/venv /opt/venv                                                                                                    0.0s
 => CACHED [stage-1 5/6] COPY . .                                                                                                                                   0.0s
 => CACHED [stage-1 6/6] RUN chown -R appuser:appgroup /app && chmod -R 755 /app                                                                                    0.0s
 => exporting to image                                                                                                                                              0.1s
 => => exporting layers                                                                                                                                             0.0s
 => => exporting manifest sha256:d9c4d5bbff6c71a63a4664b6176a7cf8d5738ea116827f910b356d290148a06f                                                                   0.0s
 => => exporting config sha256:0cea5c6e8fea36e6da7112c67af628d9a5ecaca41edfd9f12b32a6ebf2f6c9b2                                                                     0.0s
 => => exporting attestation manifest sha256:45c2bd60bc20c64827da237a0a245707051321a55ecbac6b03d1001102cc86d2                                                       0.0s
 => => exporting manifest list sha256:4b08b6e2f06333a4d7781a83bcebcdb3303c99ef310af40ae3e0e85e2a020d3e                                                              0.0s
 => => naming to docker.io/library/devops-info-service:python                                                                                                       0.0s
 => => unpacking to docker.io/library/devops-info-service:python 
```

### Terminal Output Showing Container Running
```bash
s3rap1s in ~/devops/DevOps-Core-Course/app_python on lab01 ● λ docker run -d --name devops-python -p 5000:5000 devops-info-service:python
234bff345b8f2c930681218fd9536b405c131b375a4d382a0b28a4f77d067b2c

s3rap1s in ~/devops/DevOps-Core-Course/app_python on lab01 ● λ docker logs devops-python
2026-01-31 18:45:04,632 - __main__ - INFO - Starting DevOps Info Service on 0.0.0.0:5000 (debug=False)
 * Serving Flask app 'app'
 * Debug mode: off
2026-01-31 18:45:04,639 - werkzeug - INFO - WARNING: This is a development server. Do not use it in a production deployment. Use a production WSGI server instead.
 * Running on all addresses (0.0.0.0)
 * Running on http://127.0.0.1:5000
 * Running on http://172.17.0.2:5000
2026-01-31 18:45:04,639 - werkzeug - INFO - Press CTRL+C to quit
```

### Terminal Output from Testing Endpoints
```bash
s3rap1s in ~/devops/DevOps-Core-Course/app_python on lab01 ● λ curl http://localhost:5000/
{"endpoints":[{"description":"Service information","method":"GET","path":"/"},{"description":"Health check","method":"GET","path":"/health"}],"request":{"client_ip":"172.17.0.1","method":"GET","path":"/","user_agent":"curl/8.18.0"},"runtime":{"current_time":"2026-01-31T18:45:48.101588+00:00","timezone":"UTC","uptime_human":"0 hours, 0 minutes","uptime_seconds":43},"service":{"description":"DevOps course info service","framework":"Flask","name":"devops-info-service","version":"1.0.0"},"system":{"architecture":"x86_64","cpu_count":12,"hostname":"234bff345b8f","platform":"Linux","platform_version":"6.18.3-arch1-1","python_version":"3.13.11"}}

s3rap1s in ~/devops/DevOps-Core-Course/app_python on lab01 ● λ curl http://localhost:5000/health
{"status":"healthy","timestamp":"2026-01-31T18:45:54.984116+00:00","uptime_seconds":50}
```

### Docker Hub Repository URL
**URL:** https://hub.docker.com/repository/docker/s3rap1s/devops-info-service/general

## Technical Analysis

### Why Does Your Dockerfile Work the Way It Does?
The Dockerfile uses a multi-stage build to separate concerns:
1. **Builder stage:** Installs system dependencies and Python packages in a virtual environment.
2. **Runtime stage:** Copies only the virtual environment and application code, then sets up a secure non-root user.

This approach ensures that the final image contains only what's necessary to run the application, improving security and reducing size.

### What Would Happen If You Changed the Layer Order?
If the layer order were changed, then every time any file in the project changes, the `COPY` layer would be invalidated, causing the `RUN` layer to also be invalidated (since Docker caches layers based on the previous layer's hash). This would result in a full reinstallation of dependencies on every code change, significantly slowing down builds.

### What Security Considerations Did You Implement?
1. **Non-root user:** The application runs as a dedicated user with minimal privileges.
2. **Minimal base image:** The `slim` variant reduces attack surface.
3. **Virtual environment isolation:** Prevents dependency conflicts and limits access.
4. **No unnecessary services:** Only the Python application runs in the container.
5. **Cleanup of package lists:** Removes sensitive data and reduces image size.
6. **Explicit port exposure:** Only port 5000 is exposed.

### How Does .dockerignore Improve Your Build?
The `.dockerignore` file excludes:
- Development artifacts (`.git`, `__pycache__`, `.venv`)
- IDE files (`.vscode`, `.idea`)
- Logs and temporary files
- Documentation and tests (not needed at runtime)

This reduces the build context sent to the Docker daemon, resulting in:
- **Faster build** - smaller context to transfer
- **Smaller image sizes** - unnecessary files aren't included
- **Improved security** - sensitive files like secrets aren't accidentally included

## Challenges & Solutions

### Challenge: Port Configuration Inside Container
**Problem:** The application inside the container was binding to `localhost`, making it inaccessible from the host.

**Solution:** Set the `HOST` environment variable to `0.0.0.0` in the Dockerfile to bind to all interfaces:
```dockerfile
ENV HOST=0.0.0.0
```

## What I Learned

1. **Layer caching** is crucial for efficient Docker builds
2. **Security** must be considered from the start
3. **`.dockerignore`** is as important as `.gitignore` for Docker projects, affecting both performance and security
4. **Reproducibility** requires pinning specific versions of base images and dependencies
