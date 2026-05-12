# Lab 2: Docker Containerization

### 1. Non-Root User Security

- **Practice**: Created and switched to non-root user (`appuser`)
- **Why**: Running containers as root poses security risks. If compromised, attackers get full container privileges. Non-root users follow principle of least privilege.
- **Implementation**:
  ```dockerfile
  RUN groupadd -r appuser && useradd -r -g appuser appuser
  USER appuser
  ```

### 2. Layer Caching Optimization

- **Practice**: Copy `requirements.txt` before application code
- **Why**: Dependencies change less frequently than source code. This maximizes Docker's layer caching - rebuilds only install dependencies when requirements change, not on every code modification.
- **Implementation**:
  ```dockerfile
  COPY requirements.txt .
  RUN pip install --no-cache-dir -r requirements.txt
  COPY app.py .
  ```

### 3. Minimal Base Image

- **Practice**: Used `python:3.12-slim` instead of full Python image
- **Why**: Slim images reduce attack surface and final image size. Full Python images include unnecessary development tools and documentation.
- **Implementation**:
  ```dockerfile
  FROM python:3.12-slim
  ```

### 4. Clean Package Installation

- **Practice**: Used `--no-cache-dir` pip flag
- **Why**: Prevents pip cache from being stored in final image layers, reducing image size without affecting functionality.
- **Implementation**:
  ```dockerfile
  RUN pip install --no-cache-dir -r requirements.txt
  ```

### 5. Proper File Ownership

- **Practice**: Changed ownership of application directory to non-root user
- **Why**: Ensures the application can write to any necessary files while maintaining security through non-root execution.
- **Implementation**:
  ```dockerfile
  RUN chown -R appuser:appuser /app
  ```

### 6. Build Context Optimization

- **Practice**: Created comprehensive `.dockerignore`
- **Why**: Excludes unnecessary files from build context, speeding up builds and preventing accidental inclusion of sensitive files.
- **Excluded files**: Python cache, virtual environments, documentation, tests, IDE files, version control

## Image Information & Decisions

### Base Image Choice

- **Selected**: `python:3.12-slim`
- **Justification**:
  - Matches the Python version used in development environment
  - Slim variant reduces size by ~200MB compared to full image
  - Includes only essential runtime components
  - Debian-based for better package compatibility

### Final Image Size

- **Size**: 55MB
- **Assessment**: Reasonable for a Python web application. The slim base image (41MB) plus FastAPI dependencies (14MB) equals the final size. No bloat from unnecessary packages.

### Layer Structure

```
1. python:3.12-slim (base OS + Python runtime)
2. User creation (security setup)
3. Working directory setup
4. Dependencies installation (pip packages)
5. Application code copy
6. File ownership changes
```

Each layer serves a specific purpose and is ordered for optimal caching.

### Optimization Choices

- **Single RUN command for user creation**: Combined `groupadd` and `useradd` to minimize layers
- **WORKDIR before COPY**: Ensures consistent working directory context

## Build & Run Process

### Build Process Output

```
$ docker build -t devops-info-service.
[+] Building 16.8s (13/13) FINISHED
 => [1/7] FROM docker.io/library/python:3.12-slim
 => [2/7] RUN groupadd -r appuser && useradd -r -g appuser appuser
 => [3/7] WORKDIR /app
 => [4/7] COPY requirements.txt .
 => [5/7] RUN pip install --no-cache-dir -r requirements.txt
 => [6/7] COPY app.py .
 => [7/7] RUN chown -R appuser:appuser /app
 => exporting to image
```

### Container Runtime Test

```
$ docker run -d -p 5000:5000 --name devops-test devops-info-service
2765375706dc8e1c4eadfbdfd126ee503c4fc1eb9b83624008f0336f954b90bd
```

### Endpoint Testing

**Main endpoint (`/`)**:

```bash
$ curl http://localhost:5000/
{
  "service": {
    "name": "devops-info-service",
    "version": "1.0.0",
    "description": "DevOps course info service",
    "framework": "FastAPI"
  },
  "system": {
    "hostname": "2765375706dc",
    "platform": "Linux",
    "platform_version": "#1 SMP PREEMPT_DYNAMIC Wed Sep  3 15:37:39 UTC 2025",
    "architecture": "x86_64",
    "cpu_count": 12,
    "python_version": "3.12.12"
  },
  "runtime": {
    "uptime_seconds": 0,
    "uptime_human": "0 hours, 0 minutes",
    "current_time": "2026-02-04T13:43:44.112794+00:00",
    "timezone": "UTC"
  },
  "request": {
    "client_ip": "172.17.0.1",
    "user_agent": "curl/8.5.0",
    "method": "GET",
    "path": "/"
  },
  "endpoints": [
    {"path": "/", "method": "GET", "description": "Service information"},
    {"path": "/health", "method": "GET", "description": "Health check"}
  ]
}
```

**Health endpoint (`/health`)**:

```bash
$ curl http://localhost:5000/health
{"status": "healthy", "timestamp": "2026-02-04T13:43:46.081880+00:00", "uptime_seconds": 2}
```

### Docker Hub Repository

**Repository URL**: https://hub.docker.com/r/[username]/devops-info-service
**Tag Strategy**: `latest` for current version, semantic versioning for releases

## Technical Analysis

### Why This Dockerfile Works

The Dockerfile follows Docker's layered filesystem architecture:

1. **Base layer** provides the runtime environment
2. **Dependency layer** installs Python packages (cached independently)
3. **Application layer** adds source code (changes frequently)
4. **Security layer** sets proper ownership and switches to non-root user

This structure ensures:

- Fast rebuilds when only code changes
- Security through non-root execution
- Minimal attack surface with slim base image
- Reproducible builds with pinned versions

### Layer Order Impact

**Current order benefits**:

- Dependencies installed once, cached forever (unless requirements.txt changes)
- Source code can change without reinstalling packages
- Security setup happens early, affecting all subsequent layers

**What happens if layers were reordered**:

- Copying source code before dependencies would invalidate dependency cache on every code change
- Build time would increase significantly for iterative development
- Larger context sent to Docker daemon on rebuilds

### Security Considerations

1. **Non-root execution**: Prevents privilege escalation attacks
2. **Minimal base image**: Reduces attack surface (fewer installed packages)
3. **No sensitive data**: Environment variables for configuration, no hardcoded secrets
4. **Clean package installation**: No cached package files in final image

### .dockerignore Benefits

**Build speed improvement**:

- Excludes `__pycache__/` (Python bytecode, regenerated anyway)
- Excludes `venv/` (local development environment)
- Excludes `docs/` and `tests/` (not needed at runtime)
- Reduces build context from ~50MB to ~4KB

**Security benefits**:

- Prevents accidental inclusion of `.git/` history
- Excludes potential secrets in IDE configuration
- Keeps development artifacts out of production image

## Challenges & Solutions

### Challenge 1: Non-Root User File Access

**Problem**: Initially tried to copy files after switching to non-root user, causing permission errors.

**Solution**: Copy files as root, then change ownership with `chown -R appuser:appuser /app` before switching users.

**Learned**: Docker layer ownership affects file permissions. Always set ownership before USER directive.

### Challenge 2: Image Size Optimization

**Problem**: Initial image was 230MB (compressed), wanted to understand actual runtime size.

**Solution**: Used `docker images` command to check actual sizes. Discovered compressed vs uncompressed size difference.

**Learned**: Docker reports compressed size by default. Use `--format` flag for detailed size information.

### Challenge 3: Port Exposure Understanding

**Problem**: Confused about difference between EXPOSE and -p flags.

**Solution**: EXPOSE documents container port, -p maps host:container ports. EXPOSE is metadata, -p is runtime configuration.

**Learned**: EXPOSE doesn't publish ports automatically - it's documentation for users and tools.

### Challenge 4: Build Context Size

**Problem**: Including virtual environment and cache files slowed builds.

**Solution**: Created comprehensive `.dockerignore` excluding development artifacts.

**Learned**: Build context includes all files not excluded by .dockerignore. Large contexts slow builds even if files aren't copied.

### Docker Hub Publishing

  https://hub.docker.com/r/lanebo1/devops-info-service
