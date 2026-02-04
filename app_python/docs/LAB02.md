# LAB02 — Docker Containerization (Python)

This document explains how the Lab 1 Python application was containerized using Docker best practices and published to Docker Hub. 

---

## Docker Best Practices Applied

### 1) Pinning a specific base image version

**What I did:**  
Used a pinned slim Python image: `python:3.13.1-slim`.

**Why it matters:**  
Pinning a specific image version guarantees reproducible builds and protects the application from unexpected breaking changes introduced by upstream image updates.

**Snippet:**

```dockerfile
FROM python:3.13.1-slim
```

---

### 2) Running as a non-root user

**What I did:**  
Created a dedicated system user and switched to it using the `USER` directive.

**Why it matters:**  
Running containers as non-root significantly reduces the impact of a potential container compromise by following the principle of least privilege.

**Snippet:**

```dockerfile
RUN groupadd --system app && useradd --system --gid app --uid 1000 app USER app
```

---

### 3) Proper layer ordering (cache optimization)

**What I did:**  
Copied `requirements.txt` first, installed dependencies, and only then copied the application source code.

**Why it matters:**  
Docker caches layers. Since dependencies change less frequently than application code, this approach speeds up rebuilds by reusing cached dependency layers.

**Snippet:**

```dockerfile
COPY requirements.txt . RUN pip install --no-cache-dir -r requirements.txt COPY --chown=app:app app.py .
```

---

### 4) Copying only necessary files + `.dockerignore`

**What I did:**  
Copied only required files (`requirements.txt`, `app.py`) and excluded unnecessary files using `.dockerignore`.

**Why it matters:**  
A smaller build context leads to faster builds, smaller images, and prevents accidental inclusion of sensitive or irrelevant files.

**`.dockerignore` excerpt:**

```
venv/
tests/
docs/
.git/
__pycache__/
```

---

### 5) Minimal runtime image

**What I did:**  
Used the `slim` Python image and disabled pip cache during dependency installation.

**Why it matters:**  
Smaller images reduce download time, storage usage, and overall attack surface.

---

## Image Information & Decisions

- **Base image:** `python:3.13.1-slim`  
    **Justification:** Official Python image with minimal footprint while fully supporting Flask.
    
- **Exposed port:** `5000` (matches application default)
    
- **Final image size:** `214 MB`
    
- **Layer structure:**
    
    1. Base image
        
    2. Dependency installation
        
    3. Application source code
        

---

## Build & Run Process

### Build output

```shell
docker build -t lab02-python -f app_python/Dockerfile app_python
```

```
Successfully built 4e71b36e52d3
Successfully tagged lab02-python:latest
```

---

### Run output

```shell
docker run --rm -p 5000:5000 lab02-python Running on http://0.0.0.0:5000
```

---

### Endpoint tests

```shell
curl http://localhost:5000/ HTTP/1.1 200 OK
```

```shell
curl http://localhost:5000/health {"status":"healthy"}
```

---

## Docker Hub

- **Repository URL:**  
    https://hub.docker.com/r/ostxxp/devops-lab02-python
    

### Tagging strategy

The image was tagged using the pattern:

`<dockerhub-username>/<repository-name>:<tag>`

For this lab, the image was published as:

`ostxxp/devops-lab02-python:latest`

This strategy ensures global uniqueness in Docker Hub and allows future versioned releases alongside the `latest` tag.

---

## Technical Analysis

### Why does this Dockerfile work the way it does?

The Dockerfile installs dependencies first to leverage caching, runs the application as a non-root user for security, and exposes the correct port to allow access via Docker port mapping.

### What would happen if the layer order changed?

If application code were copied before installing dependencies, Docker would invalidate the cache on every code change, forcing a full reinstall of dependencies and slowing down rebuilds.

### Security considerations implemented

- Non-root container user
    
- Minimal base image
    
- Limited copied files
    
- No pip cache retained
    

### How does `.dockerignore` improve the build?

It reduces the build context size, speeds up the build process, and prevents unnecessary or sensitive files from being included in the image.

---

## Challenges & Solutions

- **Issue:** Understanding Docker image caching behavior.
    
- **Solution:** Reordered layers and tested rebuild performance.
    
- **What I learned:** Proper Dockerfile structure directly impacts performance, security, and maintainability.