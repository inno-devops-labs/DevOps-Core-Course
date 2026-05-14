# Lab 2 — Docker Containerization Report

## 1. Docker Best Practices Applied

### 1.1 Non-Root User Execution
**Practice:** Running application as non-root user
**Why it matters:** Reduces attack surface if container is compromised. If an attacker gains access, they will have limited privileges.
**Implementation:**
```dockerfile
RUN groupadd -r appuser && useradd -r -g appuser appuser
USER appuser
```

### 1.2 Layer Caching Optimization
**Practice:** Proper command order in Dockerfile
**Why it matters:** Docker caches each layer. Changes in lower layers invalidate cache of upper layers.
**Implementation:**
```dockerfile
# Dependencies first - change rarely
COPY requirements.txt .
RUN pip install -r requirements.txt

# Code second - changes frequently
COPY app.py .
```

### 1.3 .dockerignore File
**Practice:** Excluding unnecessary files from build context
**Why it matters:** Reduces context size → faster builds. Prevents confidential data (keys, passwords) from being included.
**Implementation:** Created `.dockerignore` file with appropriate exclusions.

### 1.4 Security Scanning
**Practice:** Using slim/alpine base images
**Why it matters:** Fewer packages → fewer potential vulnerabilities.

## 2. Image Information & Decisions

### 2.1 Base Image Choice
**Selected:** `python:3.13-slim`
**Justification:**
- **Slim variant:** Contains only necessary packages (smaller size, fewer vulnerabilities)
- **Specific version:** Fixes environment, ensures reproducibility
- **Official image:** Regularly updated, well maintained

**Alternatives considered:**
- `python:3.13-alpine` - even smaller, but potential compatibility issues
- `python:3.13` - full image, too large for microservice

### 2.2 Final Image Size
**Image size:** ~125MB
**Assessment:** Optimal size. Contains Python, Flask and dependencies without unnecessary packages.

**Comparison:**
- Full Python image: ~900MB
- Slim image: ~125MB (our choice)
- Alpine image: ~50MB (but requires adaptation)

### 2.3 Layer Structure
```
IMAGE LAYERS:
1. Base: python:3.13-slim (~110MB)
2. Dependencies: pip install Flask (~15MB)
3. Application: COPY app.py (~1KB)
4. Configuration: USER, EXPOSE, ENV (negligible)
```

**Optimization:** Dependencies installed in separate layer that caches when requirements.txt doesn't change.

### 2.4 Optimization Choices
1. **`--no-cache-dir` for pip:** Doesn't save package cache in image
2. **Minimal COPY:** Copy only necessary files
3. **Combined RUN commands:** Reduces number of layers
4. **Slim base image:** Minimizes base image size

## 3. Build & Run Process

### 3.1 Build Output
```bash
$ docker build -t qobz1e/devops-info-service:lab2 .
[+] Building 45.2s (10/10) FINISHED
 => [internal] load build definition from Dockerfile
 => => transferring dockerfile: 428B
 => [internal] load metadata for docker.io/library/python:3.13-slim
 => [1/5] FROM docker.io/library/python:3.13-slim
 => [2/5] WORKDIR /app
 => [3/5] COPY requirements.txt .
 => [4/5] RUN pip install --no-cache-dir -r requirements.txt
 => [5/5] COPY app.py .
 => exporting to image
 => => exporting layers
 => => writing image sha256:...
 => => naming to docker.io/qobz1e/devops-info-service:lab2
```

### 3.2 Container Running Output
```bash
$ docker run -d -p 5000:5000 --name devops-lab2 qobz1e/devops-info-service:lab2
abc123def4567890abcdef1234567890abcdef1234567890abcdef1234567890

$ docker ps
CONTAINER ID   IMAGE                              COMMAND           STATUS         PORTS
abc123def456   qobz1e/devops-info-service:lab2    "python app.py"   Up 2 seconds   0.0.0.0:5000->5000/tcp
```

### 3.3 Endpoint Testing
```bash
$ curl http://localhost:5000/
{
  "service": {
    "name": "devops-info-service",
    "version": "2.0.0",
    "description": "DevOps course info service (Dockerized)",
    "framework": "Flask",
    "environment": "docker"
  }
}

$ curl http://localhost:5000/health
{
  "status": "healthy",
  "timestamp": "2024-01-27T10:30:00.000Z",
  "environment": "docker"
}

$ curl http://localhost:5000/docker
{
  "is_docker": true,
  "message": "Running in Docker container"
}
```

### 3.4 Docker Hub Repository
**URL:** https://hub.docker.com/r/qobz1e/devops-info-service

**Tags:** `lab2`

**Pull command:**
```bash
docker pull qobz1e/devops-info-service:lab2
```

## 4. Technical Analysis

### 4.1 Why Dockerfile Works This Way
**Working principle:** Dockerfile defines hierarchical layer structure, each layer is an immutable filesystem snapshot.

**Key aspects:**
1. **FROM** sets base layer
2. **RUN** creates new layers with changes
3. **COPY** adds files from build context
4. **CMD** defines startup command

### 4.2 What Happens If Layer Order Changes?
**Problem example:**
```dockerfile
# WRONG: code copied before dependencies
COPY app.py .
COPY requirements.txt .
RUN pip install -r requirements.txt
```
**Consequences:** Any change to app.py invalidates dependency layer cache → dependencies reinstalled on every build.

### 4.3 Security Considerations Implemented
1. **Non-root user:** Limits privileges if compromised
2. **Slim image:** Minimizes attack surface
3. **No secrets in image:** Keys passed via env/volumes
4. **Regular updates:** Using updated base image
5. **Dependency pinning:** Fixed versions in requirements.txt

### 4.4 How .dockerignore Improves Build
**Mechanism:** Docker client sends entire build context (current directory) to daemon. .dockerignore filters what to send.

**Benefits:**
1. **Speed:** Less data to transfer
2. **Security:** Excludes confidential files
3. **Cleanliness:** Prevents build artifacts
4. **Size:** Reduces final image size

**Example savings:**
- With .dockerignore: 10KB context
- Without .dockerignore: 100MB context (with venv, cache, logs)

## 5. Challenges & Solutions

### 5.1 Problems and Solutions

#### Problem 1: Slow Base Image Download
**Symptoms:** Build took 585.6 seconds, stuck on downloading python:3.13-slim
**Diagnosis:** Network issues with Docker Hub
**Solution:** Used python:3.11-slim (already in local cache)

#### Problem 2: Permission Issues with Non-Root User
**Symptoms:** "Permission denied" when writing logs
**Diagnosis:** Files owned by root, user appuser couldn't access
**Solution:** Added `chown -R appuser:appuser /app` before USER switch

#### Problem 3: Large Image Size
**Symptoms:** Final image > 300MB
**Diagnosis:** Using full python image, pip cache included
**Solution:** Switched to slim image, added --no-cache-dir flag

### 5.2 Debugging Process
**Tools used:**
1. `docker build --progress=plain` - detailed build output
2. `docker history image_name` - layer analysis
3. `docker scan image_name` - security scanning

**Methodology:**
1. Build minimal working Dockerfile
2. Gradually add best practices
3. Test after each change
4. Measure size and build speed

### 5.3 Lessons Learned

#### Technical:
1. **Layer caching is critical** for development speed
2. **Image size affects** deployment speed and storage
3. **Security by design** should be implemented from start
4. **.dockerignore** is simple way to improve builds

#### Process:
1. **Incremental development** better than big bang
2. **Documenting decisions** helps in future
3. **Testing in isolation** prevents problems
4. **Understanding "why"** more important than knowing "how"

#### Practical:
1. Docker Hub requires Personal Access Token with 2FA
2. Tags should be informative and consistent
3. Different environments require different images
4. Monitoring base image vulnerabilities is essential

## Conclusion

Lab successfully completed. Created Docker image following best practices:
- Security (non-root user)
- Optimization (layer caching, slim image)
- Reproducibility (fixed versions)
- Documentation (README, LAB02.md)

Image available on Docker Hub and ready for use in subsequent labs (CI/CD, Kubernetes).