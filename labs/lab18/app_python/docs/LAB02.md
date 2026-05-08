# Lab 2 — Docker Containerization

## Docker Best Practices Applied

### 1. Non-Root User

```dockerfile
RUN groupadd -r appuser && useradd -r -g appuser appuser
USER appuser
```

By default, Docker containers run as `root`, which is dangerous since an attacker who breaks out of the application gains root privileges inside the container. Running as a non-root user significantly reduces the attack surface and follows Docker security best practices. This is especially important for production-grade containers.

### 2. Specific Base Image Version

```dockerfile
FROM python:3.13-slim
```

Using a specific version of the base image ensures that builds are reproducible and consistent. It prevents unexpected breakages when the `latest` tag changes. The `slim` variant is chosen to reduce image size while maintaining compatibility with Python dependencies.

### 3. Proper Layer Ordering (Layer Caching)

```dockerfile
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt
COPY app.py .
```

Docker caches layers. By copying `requirements.txt` **before** application code, we ensure that dependencies are only reinstalled when `requirements.txt` changes. If we copied application code first, any code change would invalidate the cache and trigger a full reinstall of dependencies, making builds slow and inefficient.

### 4. Copy Only What Is Needed

```dockerfile
COPY app.py .
```

Only the necessary files (`app.py` and `requirements.txt`) are copied into the image. This keeps the image clean and small, and prevents accidental inclusion of unnecessary files (e.g., tests, documentation, local configuration) that could increase the attack surface or cause confusion.

## Image Information & Decisions

I selected the `python:3.13-slim` base image for this project since it matches the local development environment, is officially maintained, and is smaller than the full Python image. This choice balances compatibility with a reduced attack surface and faster download times.

The final Docker image size is **245 MB**, as reported by the Docker CLI:

```bash
gleb-pp@gleb-mac iu-devops-course % docker images | grep "app_python"
WARNING: This output is designed for human readability. For machine-readable output, please use --format.
app_python:latest       0ab8403d7d0b        245MB         53.5MB        
glebpp/app_python:1.0   0ab8403d7d0b        245MB         53.5MB        
```

This size is appropriate for a production-ready Python web application and significantly smaller than the full python:3.13 base image. The image size was optimized by:

* Using the python:3.13-slim base image instead of the full variant
* Avoiding installation of unnecessary system packages
* Installing Python dependencies without pip cache (--no-cache-dir)
* Copying only required application files into the image

### Layer Structure Explanation

1. Base Python runtime
2. User creation (rarely changes)
3. Dependency installation (cached)
4. Application code
5. Runtime configuration

This structure optimizes rebuild speed and keeps layers logically separated.

## Build & Run Process

### Image Build

```bash
gleb-pp@gleb-mac app_python % docker build -t app_python .

DEPRECATED: The legacy builder is deprecated and will be removed in a future release.
            Install the buildx component to build images with BuildKit:
            https://docs.docker.com/go/buildx/

Sending build context to Docker daemon  8.192kB
Step 1/9 : FROM python:3.13-slim
 ---> 51e1a0a317fd
Step 2/9 : RUN groupadd -r appuser && useradd -r -g appuser appuser
 ---> Using cache
 ---> 382716d6cec2
Step 3/9 : WORKDIR /app
 ---> Using cache
 ---> 7cfaf7f61014
Step 4/9 : COPY requirements.txt .
 ---> Using cache
 ---> 8ae4cd950450
Step 5/9 : RUN pip install --no-cache-dir --upgrade pip     && pip install --no-cache-dir -r requirements.txt
 ---> Using cache
 ---> fb56170d6b2c
Step 6/9 : COPY app.py .
 ---> Using cache
 ---> 1b8c44eed82f
Step 7/9 : USER appuser
 ---> Using cache
 ---> 5ccd18746e9f
Step 8/9 : EXPOSE 5000
 ---> Using cache
 ---> fa49cfbd3350
Step 9/9 : CMD ["python", "app.py"]
 ---> Using cache
 ---> 0ab8403d7d0b
Successfully built 0ab8403d7d0b
Successfully tagged app_python:latest
```

The build completed successfully using cached layers where applicable.

### Running the Container

```bash
gleb-pp@gleb-mac app_python % docker run -p 5000:5000 app_python:latest 
INFO:     Started server process [1]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:5000 (Press CTRL+C to quit)
```

The application started correctly and was accessible from the host machine.


### Testing Endpoints

```bash
gleb-pp@gleb-mac iu-devops-course % curl -s http://localhost:5000/ | jq .
{
  "service": {
    "name": "Python Web Application",
    "version": "1.0",
    "description": "Simple production-ready Pythonweb service with comprehensive system information",
    "framework": "FastAPI"
  },
  "system": {
    "hostname": "3d30f328c0a2",
    "platform": "Linux",
    "platform_version": "#67-Ubuntu SMP PREEMPT_DYNAMIC Sun Jun 15 20:23:40 UTC 2025",
    "architecture": "aarch64",
    "cpu_count": 2,
    "python_version": "3.13.11"
  },
  "runtime": {
    "uptime_seconds": 40,
    "uptime_human": "0 hours, 0 minutes",
    "current_time": "2026-02-04T12:35:57.538072",
    "timezone": "UTC"
  },
  "request": {
    "client_ip": "172.17.0.1",
    "user_agent": "curl/8.7.1",
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
gleb-pp@gleb-mac iu-devops-course % curl -s http://localhost:5000/health | jq .
{
  "status": "healthy",
  "timestamp": "2026-02-04T12:36:02.779769",
  "uptime_seconds": 45
}
```

Both endpoints returned expected responses, confirming that the application behaves **identically to the local version**.

### Docker Hub

**Repository URL:**
[https://hub.docker.com/r/glebpp/app_python](https://hub.docker.com/r/glebpp/app_python)

**Tagging Strategy:**

* `1.0` — first stable containerized release
* Simple semantic versioning for clarity

**Push Output:**

```bash
gleb-pp@gleb-mac app_python % docker push glebpp/app_python:1.0   
The push refers to repository [docker.io/glebpp/app_python]
d637807aba98: Mounted from library/postgres 
4cc556234b57: Mounted from library/python 
7bbf03d421f0: Pushed 
414df016816e: Pushed 
0df01a779dca: Pushed 
3310e4c0a9dc: Mounted from library/python 
da55684dfe01: Pushed 
031a966f46af: Pushed 
a390baeefb5b: Mounted from library/python 
1.0: digest: sha256:0ab8403d7d0bfddca8de4fc4dc2f2127176f965f1881157d6d8c980b70905f8a size: 2271
```

The image is publicly accessible and can be pulled and run by anyone.

## Technical Analysis

### Why This Dockerfile Works

This Dockerfile works because it uses the correct base image, installs dependencies efficiently, and sets up the application to run properly. 

### What If Layer Order Changed?

If application code was copied **before** dependencies:

* Any code change would invalidate the cache
* Dependencies would reinstall every time
* Builds would become slow and inefficient

Correct layer ordering is essential for productivity and CI/CD pipelines.

### Security Considerations

Implemented security measures:

* Non-root user
* Minimal base image
* No unnecessary packages or tools
* No secrets baked into the image

This reduces the attack surface and follows Docker security guidelines.

### How `.dockerignore` Improves the Build

Using a `.dockerignore` file helps to:

* Reduce build context size
* Prevent accidental file inclusion
* Speed up both local and CI builds

Without `.dockerignore`, Docker would send **everything in the repository** to the daemon, which is inefficient and unsafe.

## Challenges & Solutions

### 1. Invalid Dependency Specification

**Problem:**

```text
ERROR: Invalid requirement: 'fastapi=="0.128.0"'
```

**Cause:**
Incorrect version specifier format in `requirements.txt`.

**Solution:**
Fixed the dependency format to:

```text
fastapi==0.128.0
```

This allowed `pip install` to complete successfully.

### 2. Over-Complex Initial Dockerfile

**Initial Version (Problematic):**

* Copied entire project directory
* Used `--chown` unnecessarily
* Exposed incorrect port (`8000` instead of `5000`)

**Final Version (Improved):**

* Copies only required files
* Correct port exposure
* Simpler and more readable
* Easier to maintain and debug
