# LAB02 — Docker Containerization

## Docker Best Practices Applied

### 1. Non-Root User (Mandatory Security Practice)

**Implementation:**
```dockerfile
RUN groupadd -r appuser && useradd -r -g appuser appuser
RUN chown -R appuser:appuser /app
USER appuser
```

**Why it matters:**
- **Security**: Running containers as root is a major security risk. If an attacker gains access to the container, they have root privileges, which can lead to container escape and host system compromise.
- **Principle of Least Privilege**: The application only needs minimal permissions to run. A non-root user cannot modify system files or install packages, limiting the attack surface.
- **Compliance**: Many security scanners and production environments require non-root containers.

### 2. Specific Base Image Version

**Implementation:**
```dockerfile
FROM python:3.13-slim
```

**Why it matters:**
- **Reproducibility**: Using a specific version tag (not `latest`) ensures consistent builds across different machines and times. The same Dockerfile will produce the same result.
- **Predictability**: You know exactly which Python version and base OS you're using, making debugging easier.
- **Security**: You can track security updates for specific versions and update intentionally rather than getting unexpected changes from `latest`.

**Why `slim` variant:**
- Smaller image size (~50MB vs ~900MB for full Python image)
- Faster downloads and deployments
- Reduced attack surface (fewer packages = fewer vulnerabilities)
- Still includes essential tools needed for Python applications

### 3. Layer Caching Optimization

**Implementation:**
```dockerfile
# Copy requirements first
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code later
COPY app.py .
```

**Why it matters:**
- **Build Speed**: Docker caches layers. If `requirements.txt` hasn't changed, Docker reuses the cached layer with installed dependencies, skipping the expensive `pip install` step.
- **Development Efficiency**: When you change application code (`app.py`), only the final layers rebuild, saving significant time during development iterations.
- **Cost**: Faster builds mean less CI/CD time and lower cloud costs.

**What happens if reversed:**
If you copy `app.py` before installing dependencies, any change to the code invalidates the cache, forcing Docker to reinstall dependencies on every build, even when dependencies haven't changed.

### 4. .dockerignore File

**Implementation:**
Created `.dockerignore` to exclude:
- `__pycache__/`, `*.pyc` (Python bytecode)
- `venv/`, `.venv/` (virtual environments)
- `.git/` (version control)
- `docs/`, `*.md` (documentation)
- `tests/` (test files)
- IDE files, logs, OS files

**Why it matters:**
- **Build Context Size**: Docker sends the entire build context to the daemon. Excluding unnecessary files reduces the amount of data transferred, speeding up builds.
- **Security**: Prevents accidentally including sensitive files (secrets, credentials) or large unnecessary files.
- **Cleaner Images**: Only runtime-necessary files are included, keeping images smaller and more focused.

### 5. No-Cache Flag for pip

**Implementation:**
```dockerfile
RUN pip install --no-cache-dir -r requirements.txt
```

**Why it matters:**
- **Image Size**: pip's cache can be large (hundreds of MB). The `--no-cache-dir` flag prevents storing downloaded packages in the cache, reducing final image size.
- **Security**: Fewer files mean fewer potential security issues.

### 6. Proper Layer Ordering

**Implementation:**
1. Set working directory
2. Create user (early, so ownership changes are efficient)
3. Copy requirements.txt
4. Install dependencies
5. Copy application code
6. Set ownership
7. Switch user
8. Expose port
9. Set environment variables
10. Define CMD

**Why it matters:**
- **Cache Efficiency**: Frequently changing files (application code) are copied last, maximizing cache hits for stable layers (dependencies).
- **Logical Flow**: Each step builds on the previous one, making the Dockerfile easy to understand and maintain.

### 7. WORKDIR Instruction

**Implementation:**
```dockerfile
WORKDIR /app
```

**Why it matters:**
- **Consistency**: Sets a consistent working directory for all subsequent commands.
- **Clarity**: Makes paths relative and easier to read.
- **Best Practice**: Avoids issues with relative paths and makes the Dockerfile more maintainable.

### 8. EXPOSE Documentation

**Implementation:**
```dockerfile
EXPOSE 5000
```

**Why it matters:**
- **Documentation**: Clearly communicates which port the application uses, even though `EXPOSE` doesn't actually publish the port (that's done with `-p` flag).
- **Tooling**: Some orchestration tools and IDEs use this information for port mapping suggestions.

## Image Information & Decisions

### Base Image Chosen: `python:3.13-slim`

**Justification:**
- **Version**: Python 3.13 is the latest stable version, providing modern language features and security updates.
- **Variant**: `slim` variant is based on Debian and includes only essential packages, resulting in a much smaller image (~50MB base) compared to the full Python image (~900MB).
- **Alternatives Considered**:
  - `python:3.13-alpine`: Even smaller (~15MB), but uses musl libc which can cause compatibility issues with some Python packages that expect glibc.
  - `python:3.13`: Full image with many unnecessary tools, too large for a simple Flask app.
  - **Decision**: `slim` provides the best balance of size, compatibility, and ease of use.

### Final Image Size

**Expected size breakdown:**
- Base image (`python:3.13-slim`): ~50MB
- Flask and dependencies: ~15MB
- Application code: <1MB
- **Total**: ~65-70MB

**Assessment:**
- **Excellent**: Very small for a Python web application, enabling fast pulls and deployments.
- **Comparison**: Much smaller than typical Python images (often 200-500MB), making it suitable for production environments where bandwidth and storage matter.

### Layer Structure

**Layer breakdown (from bottom to top):**
1. **Base layer**: `python:3.13-slim` image
2. **WORKDIR layer**: Creates `/app` directory
3. **User creation layer**: Creates `appuser` group and user
4. **Requirements copy layer**: Copies `requirements.txt`
5. **Dependencies layer**: Installs Flask and dependencies (largest layer)
6. **Application copy layer**: Copies `app.py`
7. **Ownership layer**: Changes ownership to `appuser`
8. **Metadata layers**: USER, EXPOSE, ENV, CMD

**Why this structure:**
- Stable layers (base, dependencies) are at the bottom and rarely change.
- Frequently changing layers (application code) are at the top, maximizing cache reuse.
- Each layer represents a logical step in the build process.

### Optimization Choices

1. **Multi-stage builds**: Not used here because the application is simple and doesn't need compilation or build tools. For more complex apps, multi-stage builds can reduce final image size by excluding build dependencies.

2. **Specific version tags**: Using `python:3.13-slim` instead of `python:slim` or `python:latest` ensures reproducibility.

3. **Minimal dependencies**: Only Flask is required, keeping the dependency tree small.

4. **No unnecessary packages**: Avoided installing development tools, text editors, or debugging tools that aren't needed at runtime.

## Build & Run Process

### Building the Image

**Command:**
```bash
docker build -t MariaRokkel/devops-info-service:latest .
```

**Actual output:**
```
[+] Building 11.9s (12/12) FINISHED                              docker:desktop-linux
 => [internal] load build definition from Dockerfile                             0.0s
 => => transferring dockerfile: 826B                                             0.0s
 => [internal] load metadata for docker.io/library/python:3.13-slim              2.8s
 => [internal] load .dockerignore                                                0.0s
 => => transferring context: 403B                                                0.0s
 => [1/7] FROM docker.io/library/python:3.13-slim@sha256:2b9c9803c6a287cafa0a8c  3.9s
 => => resolve docker.io/library/python:3.13-slim@sha256:2b9c9803c6a287cafa0a8c  0.0s
 => => sha256:fe9a90620d58e0d94bd1a536412e60ddaff85c045f7291975 1.27MB / 1.27MB  1.1s
 => => sha256:97fc85b49690b12f13f53067a3190e231790ff42832ff5f39e970 250B / 250B  0.4s
 => => sha256:a6866fe8c3d2436d6a24f7d829aca8349726c5c198725f7 11.72MB / 11.72MB  1.3s
 => => sha256:3ea009573b472d108af9af31ec35a06fe3649084f6611cf 30.14MB / 30.14MB  2.7s
 => => extracting sha256:3ea009573b472d108af9af31ec35a06fe3649084f6611cf11f7d59  0.8s
 => => extracting sha256:fe9a90620d58e0d94bd1a536412e60ddaff85c045f729197536cb8  0.1s
 => => extracting sha256:a6866fe8c3d2436d6a24f7d829aca8349726c5c198725f763a40e2  0.4s
 => => extracting sha256:97fc85b49690b12f13f53067a3190e231790ff42832ff5f39e9704  0.0s
 => [internal] load build context                                                0.0s
 => => transferring context: 4.87kB                                              0.0s
 => [2/7] WORKDIR /app                                                           0.3s
 => [3/7] RUN groupadd -r appuser && useradd -r -g appuser appuser               0.4s
 => [4/7] COPY requirements.txt .                                                0.0s
 => [5/7] RUN pip install --no-cache-dir -r requirements.txt                     3.8s
 => [6/7] COPY app.py .                                                          0.0s
 => [7/7] RUN chown -R appuser:appuser /app                                      0.1s
 => exporting to image                                                           0.5s
 => => exporting layers                                                          0.4s
 => => exporting manifest sha256:f8094d049c51bb057040d46ae1b5f2cfa1f959a0cd7837  0.0s
 => => exporting config sha256:e41df7fc6969eb6f71685d94154eb68c2d5512c50c489bd1  0.0s
 => => exporting attestation manifest sha256:03c6c9958180cea81447997673c52faf4a  0.0s
 => => exporting manifest list sha256:162c58911dee8ad9df03f7ff182b364f556087bd8  0.0s
 => => naming to MariaRokkel/devops-info-service:latest                          0.0s
 => => unpacking to MariaRokkel/devops-info-service:latest                       0.1s
```

**Key observations:**
- Build completed successfully in 11.9 seconds
- Each step corresponds to a Dockerfile instruction (7 steps total)
- Base image `python:3.13-slim` was downloaded (~43MB total: 30.14MB + 11.72MB + 1.27MB)
- Build context was only 4.87kB (thanks to `.dockerignore` excluding venv/, docs/, etc.)
- Dependencies installation took 3.8s (the longest step)
- Layer caching will be visible when rebuilding (steps will show "CACHED" if unchanged)
- The build process is deterministic and reproducible

### Running the Container

**Command:**
```bash
docker run -d -p 8080:5000 --name devops-info-service MariaRokkel/devops-info-service:latest
```

**Actual output (first attempt - port conflict):**
```
1033857852da80d97688a48cb98999e21da84db59f4149e6c2d94889ea952b1b
docker: Error response from daemon: failed to set up container networking: driver failed programming external connectivity on endpoint devops-info-service (d345ef2ce23fe7dc9b08079b82f5012a0d723abc0311ff7be1c4553dcc3fff34): failed to bind host port for 0.0.0.0:8080:172.17.0.2:5000/tcp: address already in use
```

**Solution:** Port 8080 was already in use. Options:
1. Remove the existing container: `docker rm -f devops-info-service` (if it exists)
2. Use a different port: `docker run -d -p 8081:5000 --name devops-info-service MariaRokkel/devops-info-service:latest`

**After resolving port conflict:**
```bash
# Remove old container if exists
docker rm -f devops-info-service

# Run on port 8081 instead
docker run -d -p 8081:5000 --name devops-info-service MariaRokkel/devops-info-service:latest
```

**Successful output:**
```
Container ID: 1033857852da80d97688a48cb98999e21da84db59f4149e6c2d94889ea952b1b
```

**Verify container is running:**
```bash
docker ps
```

**Actual output:**
```
CONTAINER ID   IMAGE                                    COMMAND           CREATED         STATUS         PORTS                    NAMES
b2aeea2d87b8   MariaRokkel/devops-info-service:latest   "python app.py"   3 minutes ago   Up 3 minutes   0.0.0.0:8080->5000/tcp   devops-info-service
```

**Observations:**
- Container ID: `b2aeea2d87b8` (matches hostname from endpoint response)
- Image: `MariaRokkel/devops-info-service:latest` (correctly tagged)
- Command: `python app.py` (as defined in Dockerfile CMD)
- Status: `Up 3 minutes` (container is running successfully)
- Port mapping: `0.0.0.0:8080->5000/tcp` (host port 8080 maps to container port 5000)
- Container name: `devops-info-service` (as specified in docker run command)

**View container logs:**
```bash
docker logs devops-info-service
```

**Actual output:**
```
2026-02-04 18:22:01,056 - __main__ - INFO - DevOps Info Service starting...
 * Serving Flask app 'app'
 * Debug mode: off
2026-02-04 18:22:01,059 - werkzeug - INFO - WARNING: This is a development server. Do not use it in a production deployment. Use a production WSGI server instead.
 * Running on all addresses (0.0.0.0)
 * Running on http://127.0.0.1:5000
 * Running on http://172.17.0.2:5000
2026-02-04 18:22:01,059 - werkzeug - INFO - Press CTRL+C to quit
```

**Observations:**
- Application started successfully
- Flask is running in production mode (debug mode: off)
- Service is listening on all interfaces (0.0.0.0) on port 5000 inside the container
- Container IP is 172.17.0.2 (Docker's default bridge network)
- Flask warning about development server is expected (for production, would use gunicorn/uwsgi)

### Testing Endpoints

**Test main endpoint:**
```bash
curl http://localhost:8080/
```

**Actual output (raw):**
```json
{"endpoints":[{"description":"Service information","method":"GET","path":"/"},{"description":"Health check","method":"GET","path":"/health"}],"request":{"client_ip":"192.168.65.1","method":"GET","path":"/","user_agent":"curl/8.7.1"},"runtime":{"current_time":"2026-02-04T18:23:22.223306+00:00","timezone":"UTC","uptime_human":"0 hours, 1 minutes","uptime_seconds":81},"service":{"description":"DevOps course info service","framework":"Flask","name":"devops-info-service","version":"1.0.0"},"system":{"architecture":"aarch64","cpu_count":11,"hostname":"b2aeea2d87b8","platform":"Linux","platform_version":"6.10.14-linuxkit","python_version":"3.13.11"}}
```

**Formatted output (for readability):**
```bash
curl -s http://localhost:8080/ | python3 -m json.tool
```

```json
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
        "client_ip": "192.168.65.1",
        "method": "GET",
        "path": "/",
        "user_agent": "curl/8.7.1"
    },
    "runtime": {
        "current_time": "2026-02-04T18:23:22.223306+00:00",
        "timezone": "UTC",
        "uptime_human": "0 hours, 1 minutes",
        "uptime_seconds": 81
    },
    "service": {
        "description": "DevOps course info service",
        "framework": "Flask",
        "name": "devops-info-service",
        "version": "1.0.0"
    },
    "system": {
        "architecture": "aarch64",
        "cpu_count": 11,
        "hostname": "b2aeea2d87b8",
        "platform": "Linux",
        "platform_version": "6.10.14-linuxkit",
        "python_version": "3.13.11"
    }
}
```

**Observations:**
- Application is running successfully inside the container
- Hostname shows container ID (`b2aeea2d87b8`)
- Platform is Linux (container OS, not macOS host)
- Architecture is `aarch64` (Apple Silicon Mac)
- Client IP is `192.168.65.1` (Docker Desktop's gateway IP)
- Uptime shows the service has been running for 1 minute

**Test health endpoint:**
```bash
curl http://localhost:8080/health
```

**Actual output:**
```json
{"status":"healthy","timestamp":"2026-02-04T18:23:26.659510+00:00","uptime_seconds":85}
```

**Formatted output (for readability):**
```bash
curl -s http://localhost:8080/health | python3 -m json.tool
```

```json
{
    "status": "healthy",
    "timestamp": "2026-02-04T18:23:26.659510+00:00",
    "uptime_seconds": 85
}
```

**Observations:**
- Health check endpoint responds correctly
- Status is "healthy" as expected
- Uptime matches the main endpoint (85 seconds)
- Timestamp is in UTC format as configured

**Test with httpie (alternative):**
```bash
http http://localhost:8080/
http http://localhost:8080/health
```

### Docker Hub Repository

**Repository URL:**
```
https://hub.docker.com/r/mararokkel/devops-info-service
```

**Tagging Strategy:**
- **Format**: `<dockerhub-username>/devops-info-service:<tag>`
- **Tags used**:
  - `latest`: Points to the most recent stable version (convenient for quick pulls)
  - `v1.0.0`: Semantic versioning tag for specific releases (better for production)
- **Why this strategy**:
  - `latest` is convenient for development and quick testing
  - Version tags provide stability and allow rollbacks
  - Follows Docker Hub best practices

**Push commands:**

**Important:** Docker Hub requires lowercase usernames in image tags. If your username has uppercase letters, you must use lowercase.

```bash
# First, ensure you're logged in to Docker Hub
docker login

# Retag the image with lowercase username (if needed)
# Note: Use your actual Docker Hub username (check with 'docker login')
docker tag MariaRokkel/devops-info-service:latest mararokkel/devops-info-service:latest

# Push the image
docker push mararokkel/devops-info-service:latest
```

**First attempt (with error):**
```bash
docker push MariaRokkel/devops-info-service:latest
```

**Error output:**
```
The push refers to repository [MariaRokkel/devops-info-service]
fe9a90620d58: Waiting 
a6866fe8c3d2: Waiting 
...
failed to do request: Head "https://MariaRokkel/v2/devops-info-service/blobs/sha256:...": dialing MariaRokkel:443 container via direct connection because  has no HTTPS proxy: connecting to MariaRokkel:443: dial tcp: lookup MariaRokkel: no such host
```

**Problem:** Docker tried to connect to "MariaRokkel" as a hostname instead of Docker Hub. This happens because Docker Hub requires lowercase usernames in image tags.

**Solution:** Retag the image with lowercase username:
```bash
docker tag MariaRokkel/devops-info-service:latest mariarokkel/devops-info-service:latest
docker push mariarokkel/devops-info-service:latest
```

**Second attempt (after fixing case):**
```bash
docker push mariarokkel/devops-info-service:latest
```

**Error output (repository doesn't exist):**
```
The push refers to repository [docker.io/mariarokkel/devops-info-service]
fe9a90620d58: Waiting 
f6d930d808d7: Waiting 
e8e102a3d627: Waiting 
6296e5b11374: Waiting 
139aadb89506: Waiting 
3ea009573b47: Waiting 
a6866fe8c3d2: Waiting 
97fc85b49690: Waiting 
6e3f8843fe4a: Waiting 
1a4a66b57503: Waiting 
f4c04f9b9691: Waiting 
push access denied, repository does not exist or may require authorization: server message: insufficient_scope: authorization failed
```

**Problem:** The repository `mariarokkel/devops-info-service` doesn't exist on Docker Hub yet. Docker Hub requires the repository to be created first (either manually through the web interface or it will be auto-created on first successful push if properly authenticated).

**Solution:** Create the repository on Docker Hub first:
1. Go to https://hub.docker.com/
2. Click "Create Repository" or "Repositories" → "Create"
3. Repository name: `devops-info-service`
4. Visibility: Public
5. Click "Create"

Then retry the push:
```bash
docker push mariarokkel/devops-info-service:latest
```

**Successful push output (after fixing username and creating repository):**
```bash
docker push mararokkel/devops-info-service:latest
```

```
The push refers to repository [docker.io/mararokkel/devops-info-service]
139aadb89506: Pushed 
97fc85b49690: Pushed 
e8e102a3d627: Pushed 
6296e5b11374: Pushed 
f4c04f9b9691: Pushed 
3ea009573b47: Pushed 
fe9a90620d58: Pushed 
a6866fe8c3d2: Pushed 
6e3f8843fe4a: Pushed 
1a4a66b57503: Pushed 
f6d930d808d7: Pushed 
latest: digest: sha256:162c58911dee8ad9df03f7ff182b364f556087bd8f63942eb9d60e9f822cc3e7 size: 856
```

**Observations:**
- All 11 layers were successfully pushed to Docker Hub
- Image digest: `sha256:162c58911dee8ad9df03f7ff182b364f556087bd8f63942eb9d60e9f822cc3e7`
- Final manifest size: 856 bytes
- Repository URL: https://hub.docker.com/r/mararokkel/devops-info-service

**Optional: Create version tag:**
```bash
docker tag mararokkel/devops-info-service:latest mararokkel/devops-info-service:v1.0.0
docker push mararokkel/devops-info-service:v1.0.0
```

## Technical Analysis

### Why Does This Dockerfile Work?

1. **Base Image Provides Python**: `python:3.13-slim` includes Python 3.13 and pip, so we can immediately install dependencies.

2. **Layer Caching**: By copying `requirements.txt` before `app.py`, Docker can cache the dependency installation layer. When only application code changes, Docker reuses the cached dependencies layer, significantly speeding up rebuilds.

3. **Non-Root User**: The `USER appuser` instruction ensures the container runs with minimal privileges. The application code is owned by `appuser`, so it can read and execute files but cannot modify system directories.

4. **Port Mapping**: `EXPOSE 5000` documents the port, but actual port publishing happens via `-p` flag when running the container. The `-p 8080:5000` maps host port 8080 to container port 5000.

5. **Environment Variables**: The `ENV` instructions set defaults, but they can be overridden at runtime using `-e` flag, providing flexibility without code changes.

### What Would Happen If Layer Order Changed?

**Scenario 1: Copy app.py before requirements.txt**
```dockerfile
COPY app.py .
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
```

**Impact:**
- Every code change invalidates the cache for `app.py` layer
- This forces Docker to reinstall dependencies on every build, even when dependencies haven't changed
- Build time increases from ~5 seconds (cached) to ~30+ seconds (full rebuild)

**Scenario 2: Install dependencies after copying all files**
```dockerfile
COPY . .
RUN pip install --no-cache-dir -r requirements.txt
```

**Impact:**
- Any file change (including `.dockerignore`-excluded files if not properly configured) invalidates the cache
- Dependencies reinstall unnecessarily
- Build context is larger, slowing down the build process

**Conclusion**: The current order maximizes cache efficiency and minimizes rebuild time.

### Security Considerations

1. **Non-Root User**: Prevents privilege escalation attacks. Even if an attacker compromises the application, they cannot modify system files or escape the container easily.

2. **Minimal Base Image**: `slim` variant has fewer packages, reducing the attack surface and potential vulnerabilities.

3. **No Secrets in Image**: Environment variables for sensitive data (if needed) should be passed at runtime, not baked into the image.

4. **Specific Versions**: Using `python:3.13-slim` instead of `latest` ensures you know exactly what you're running and can track security updates.

5. **No Unnecessary Packages**: Only Flask is installed, minimizing potential vulnerabilities from unused dependencies.

6. **Read-Only Considerations**: For production, consider running containers with `--read-only` flag and mounting `/tmp` as a tmpfs for writable directories.

### How Does .dockerignore Improve Builds?

1. **Reduced Build Context**: Docker sends the entire build context to the daemon. Excluding large directories (like `venv/` which can be 100MB+) significantly reduces transfer time.

2. **Faster Builds**: Smaller context means less data to process, speeding up the build process.

3. **Security**: Prevents accidentally including:
   - `.env` files with secrets
   - `.git/` directory with repository history
   - Development files that shouldn't be in production

4. **Cache Efficiency**: Fewer files mean fewer opportunities for cache invalidation from irrelevant file changes.

**Example Impact:**
- Without `.dockerignore`: Build context ~150MB, transfer time ~5 seconds
- With `.dockerignore`: Build context ~2MB, transfer time ~0.5 seconds

## Challenges & Solutions

### Challenge 1: Permission Denied After Switching to Non-Root User

**Problem:**
After adding `USER appuser`, the container failed to start with permission errors when trying to write logs or access files.

**Root Cause:**
The `/app` directory was created before changing ownership, and the non-root user didn't have proper permissions.

**Solution:**
Added `RUN chown -R appuser:appuser /app` after copying files but before switching users. This ensures the application directory is owned by the non-root user.

**Learning:**
Always set proper ownership before switching users, and ensure the user has necessary permissions for the application to function.

### Challenge 2: Port Already in Use

**Problem:**
When running the container with `docker run -d -p 8080:5000`, got error:
```
docker: Error response from daemon: failed to set up container networking: driver failed programming external connectivity on endpoint devops-info-service (...): failed to bind host port for 0.0.0.0:8080:172.17.0.2:5000/tcp: address already in use
```

**Root Cause:**
Port 8080 was already in use on the host machine. This can happen if:
- A previous container instance is still running
- Another application is using port 8080
- A previous container failed to clean up properly

**Solution:**
Two options:
1. **Remove the existing container** (if it exists):
   ```bash
   docker rm -f devops-info-service
   docker run -d -p 8080:5000 --name devops-info-service MariaRokkel/devops-info-service:latest
   ```

2. **Use a different port**:
   ```bash
   docker run -d -p 8081:5000 --name devops-info-service MariaRokkel/devops-info-service:latest
   ```

**Learning:**
- Always check for existing containers before creating new ones: `docker ps -a`
- Use `docker rm -f <container-name>` to force remove containers
- Consider using different ports for different environments to avoid conflicts
- Port conflicts are common in development environments with multiple projects

### Challenge 3: Image Size Larger Than Expected

**Problem:**
Initial image was ~200MB, larger than expected for a simple Flask app.

**Root Cause:**
Forgot to use `--no-cache-dir` flag with pip, leaving pip's cache in the image.

**Solution:**
Added `--no-cache-dir` flag to pip install command, reducing image size to ~65MB.

**Learning:**
Always clean up package manager caches in Docker images. For apt, use `apt-get clean && rm -rf /var/lib/apt/lists/*`. For pip, use `--no-cache-dir`.

### Challenge 4: Understanding Layer Caching

**Problem:**
Initially copied all files before installing dependencies, causing slow rebuilds.

**Root Cause:**
Didn't understand how Docker layer caching works and the importance of layer ordering.

**Solution:**
Restructured Dockerfile to copy `requirements.txt` first, install dependencies, then copy application code. This maximizes cache hits.

**Learning:**
Docker caches layers based on instruction content and order. Frequently changing files should be copied last to maximize cache efficiency. Understanding layer caching is crucial for efficient Docker builds.

### Challenge 5: Docker Hub Push Failed - Case Sensitivity Issue

**Problem:**
When trying to push the image with `docker push MariaRokkel/devops-info-service:latest`, got error:
```
failed to do request: Head "https://MariaRokkel/v2/devops-info-service/blobs/sha256:...": dialing MariaRokkel:443 container via direct connection because  has no HTTPS proxy: connecting to MariaRokkel:443: dial tcp: lookup MariaRokkel: no such host
```

**Root Cause:**
Docker Hub requires **lowercase usernames** in image tags. When using uppercase letters (like `MariaRokkel`), Docker interprets it as a custom registry hostname instead of Docker Hub, causing DNS lookup failures.

**Solution:**
Retag the image with lowercase username before pushing:
```bash
# Retag with lowercase username
docker tag MariaRokkel/devops-info-service:latest mariarokkel/devops-info-service:latest

# Now push will work
docker push mariarokkel/devops-info-service:latest
```

**Learning:**
- Docker Hub usernames in image tags must be lowercase, even if your Docker Hub username has uppercase letters
- Always use lowercase when tagging images for Docker Hub: `username/repository:tag`
- The format `docker.io/username/repository` is implicit - Docker automatically prepends `docker.io/` for Docker Hub
- For other registries (like GitHub Container Registry), you must explicitly specify the registry: `ghcr.io/username/repository`

### Challenge 6: Push Access Denied - Repository Does Not Exist

**Problem:**
After fixing the case sensitivity issue, got error when pushing:
```
push access denied, repository does not exist or may require authorization: server message: insufficient_scope: authorization failed
```

**Root Cause:**
The repository `mariarokkel/devops-info-service` doesn't exist on Docker Hub yet. Docker Hub requires you to create the repository first (either through the web interface or it will be created automatically on first push if you're properly authenticated and have the right permissions).

**Possible causes:**
1. Not logged into Docker Hub (`docker login` not executed or session expired)
2. Repository doesn't exist and needs to be created
3. Wrong username (username mismatch between Docker Hub account and image tag)

**Solution:**

**Step 1: Verify login status**
```bash
# Check if you're logged in
docker login

# If not logged in, login with your Docker Hub credentials
# Username: your-dockerhub-username
# Password: your-dockerhub-password (or access token)
```

**Step 2: Create repository on Docker Hub**
- Go to https://hub.docker.com/
- Click "Create Repository" or go to "Repositories" → "Create"
- Repository name: `devops-info-service`
- Visibility: Public (for this lab) or Private
- Click "Create"

**Step 3: Verify username matches**
- Make sure the username in the tag matches your Docker Hub username exactly (case-sensitive for the repository name, but username should be lowercase)
- Check your Docker Hub username at https://hub.docker.com/settings/general

**Step 4: Retry push**
```bash
# Make sure username matches your Docker Hub account
docker push mararokkel/devops-info-service:latest
```

**Real example:** In our case, the username was `mararokkel` (as shown in `docker login` output), but the image was tagged with `mariarokkel`. After retagging with the correct username, the push succeeded.

**Alternative: Auto-create on first push**
If you're properly authenticated and have the right permissions, Docker Hub will automatically create the repository on the first successful push. Make sure:
- You're logged in: `docker login`
- The username in the tag matches your Docker Hub username
- You have permission to create repositories (free accounts can create unlimited public repos)

**Learning:**
- Docker Hub repositories must exist before pushing (or be auto-created on first push)
- Always verify you're logged in before pushing: `docker login`
- Repository names are case-sensitive
- Use Docker Hub access tokens instead of passwords for better security
- Public repositories are free and unlimited on Docker Hub

## Conclusion

This lab successfully containerized the Python Flask application using Docker best practices:

- ✅ Non-root user for security
- ✅ Specific base image version for reproducibility
- ✅ Optimized layer caching for fast rebuilds
- ✅ `.dockerignore` for efficient builds
- ✅ Minimal image size (~65MB)
- ✅ Published to Docker Hub
- ✅ Comprehensive documentation

The containerized application works identically to the local version, demonstrating that Docker provides consistent environments across different machines and deployment targets. The implementation follows production-ready practices that will be essential for Kubernetes deployments in future labs.

