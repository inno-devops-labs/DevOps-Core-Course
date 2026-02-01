# Docker Best Practices Applied

## 1. Non-root user
**What I did:**
Created a dedicated user (`appuser`) and ran the container as that user.

**Why it matters**:
Running as root in a container increases the impact of a container escape or a vulnerable dependency. A non-root user reduces privileges and limits potential damage.

**Dockerfile snippet:**
```dockerfile
RUN useradd --create-home --shell /bin/bash appuser
USER appuser
```

## 2. Layer caching
**What I did:**
Copied `requirements.txt` first and installed dependencies before copying the rest of the source code.

**Why it matters**:
Docker caches layers. Dependencies change less frequently than application code, so separating them allows rebuilds to reuse the cached dependency layer and rebuild faster.

**Dockerfile snippet:**
```dockerfile
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app.py .
```

## 3. .dockerignore
**What I did:**
Added .dockerignore to exclude local artifacts such as venvs, caches, and IDE folders.

**Why it matters**:
Docker sends the build context to the daemon. Excluding unnecessary files makes builds faster, reduces image bloat, and prevents leaking local secrets/files into the build.

**.dockerignore snippet:**
```.dockerignore
# 🐙 Version control
.git
.gitignore

# 🐍 Python
__pycache__
*.pyc
*.pyo
venv/
.venv/

# 🔐 Secrets (NEVER include!)
.env
*.pem
secrets/

# 📝 Documentation
*.md
docs/

# 🧪 Tests (if not needed in container)
tests/
```

## 4. Minimal base image
**What I did:**
Used `python:3.12-slim`.

**Why it matters**:
Smaller images generally mean fewer packages, fewer vulnerabilities, less bandwidth and faster pulls/deployments.

**dockerfile snippet:**
```dockerfile
FROM python:3.12-slim
```

# Image Information & Decisions
## Base image chosen and justification (why this specific version?)
**Base image**:
`python:3.12-slim`

**Justification**:
- Python 3.12 matches the project runtime requirements.
- slim variant keeps image smaller and reduces OS packages.
- Official Python images are widely used and well maintained.

## Final image size and my assessment
**Image size**:
`195MB`

**My assessment**:
Further optimization is possible (multi-stage build, wheels caching, removing build deps), but for this lab the size is acceptable.

## Layer structure explanation
1. Base image layer (`python:3.12-slim`)
2. User creation layer
3. `WORKDIR` and `requirements.txt` copy layer
4. pip install dependencies layer (largest and most valuable for caching)
5. Application source copy layer
6. EXPOSE, USER, and CMD metadata layers

## Optimization choices
- Used dependency-first copying to maximize caching.
- Used `--no-cache-dir` with pip to reduce layer size.
- Used slim base image to reduce OS footprint.
- Added `.dockerignore` to reduce build context.

# Build & Run Process
## Complete terminal output from build process
```bash
 docker build -t python_app:1.0 .
[+] Building 5.4s (12/12) FINISHED                                                    docker:desktop-linux
 => [internal] load build definition from Dockerfile                                                  0.0s
 => => transferring dockerfile: 277B                                                                  0.0s
 => [internal] load metadata for docker.io/library/python:3.12-slim                                   3.7s
 => [auth] library/python:pull token for registry-1.docker.io                                         0.0s
 => [internal] load .dockerignore                                                                     0.0s
 => => transferring context: 289B                                                                     0.0s
 => [1/6] FROM docker.io/library/python:3.12-slim@sha256:5e2dbd4bbdd9c0e67412aea9463906f74a22c60f89e  0.0s
 => [internal] load build context                                                                     0.1s
 => => transferring context: 62.28kB                                                                  0.1s
 => CACHED [2/6] RUN useradd --create-home --shell /bin/bash appuser                                  0.0s
 => CACHED [3/6] WORKDIR /app                                                                         0.0s
 => CACHED [4/6] COPY requirements.txt .                                                              0.0s
 => CACHED [5/6] RUN pip install --no-cache-dir -r requirements.txt                                   0.0s 
 => [6/6] COPY app.py .                                                                                    0.8s 
 => exporting to image                                                                                0.4s 
 => => exporting layers                                                                               0.3s 
 => => writing image sha256:a3d1dd41a468a1bb53d02edd846964c240eb160f49fd28e9f6ad90fc15677c52          0.0s 
 => => naming to docker.io/library/python_app:1.0                                                     0.0s 

View build details: docker-desktop://dashboard/build/desktop-linux/desktop-linux/djiu836gkk9g7syuakivz5ynt 
```

## Terminal output showing container running
```bash
 docker run --rm -p 8000:8000 python_app:1.0     
2026-01-31 18:29:56,977 - __main__ - INFO - Application starting...
INFO:     Will watch for changes in these directories: ['/app']
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
INFO:     Started reloader process [1] using WatchFiles
INFO:     Started server process [8]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```

## Terminal output from testing endpoints
```bash
curl http://localhost:8000/

                                                                                                           StatusCode        : 200                                                                                    
StatusDescription : OK                                                                                     
Content           : {"service":{"name":"devops-info-service","version":"1.0.0","description":"DevOps cours 
                    e info service","framework":"FastAPI"},"system":{"hostname":"3a77a23940f7","platform":
                    "Linux","platform_version":"...
RawContent        : HTTP/1.1 200 OK
                    Content-Length: 755
                    Content-Type: application/json
                    Date: Sat, 31 Jan 2026 18:31:18 GMT
                    Server: uvicorn

Forms             : {}
Headers           : {[Content-Length, 755], [Content-Type, application/json], [Date, Sat, 31 Jan 2026 18:3 
                    1:18 GMT], [Server, uvicorn]}                                                          Images            : {}                                                                                     InputFields       : {}                                                                                     Links             : {}                                                                                     
ParsedHtml        : mshtml.HTMLDocumentClass
RawContentLength  : 755
```

```bash
curl http://localhost:8000/health 


StatusCode        : 200
StatusDescription : OK
Content           : {"status":"healthy","timestamp":"2026-01-31T18:31:26.924513+00:00","uptime_seconds":89 
                    }
RawContent        : HTTP/1.1 200 OK
                    Content-Length: 87
                    Content-Type: application/json
                    Date: Sat, 31 Jan 2026 18:31:26 GMT
                    Server: uvicorn

                    {"status":"healthy","timestamp":"2026-01-31T18:31:26.924513+00:00","uptime_...
Forms             : {}
Headers           : {[Content-Length, 87], [Content-Type, application/json], [Date, Sat, 31 Jan 2026 18:31 
                    :26 GMT], [Server, uvicorn]}
Images            : {}
InputFields       : {}
Links             : {}
ParsedHtml        : mshtml.HTMLDocumentClass
RawContentLength  : 87
```

## Terminal output showing successful push:
```bash
docker push newspec/python_app:1.0

The push refers to repository [docker.io/newspec/python_app]
8422fdf98022: Pushed
56a7b3684a2c: Pushed
410b7369101c: Pushed
4e7298e95b69: Pushed
b68196304589: Pushed
343fbb74dfa7: Pushed
cfdc6d123592: Pushed
ff565e4de379: Pushed
e50a58335e13: Pushed
1.0: digest: sha256:9084f1513bc5af085a268ee9e8b165af82f7224e442da0790cf81f07b67ab10e size: 2203

```

## Docker Hub repository URL
`https://hub.docker.com/repository/docker/newspec/python_app`

## My tagging strategy
`:1.0`(major/minor)

# Technical analysis
## Why does your Dockerfile work the way it does?
- The image is based on a minimal Python runtime.
- Dependencies are installed before application code to leverage Docker layer caching.
- The app runs as a non-root user for better security.

## What would happen if you changed the layer order?
If the Dockerfile copied the entire project (`COPY . .`) before installing requirements, then any code change would invalidate the cache for the dependency install layer. That would force `pip install` to run again on every rebuild, making builds much slower.

## What security considerations did you implement?
- Non-root execution reduces privilege.
- Smaller base image reduces attack surface.
- `.dockerignore` prevents accidentally shipping local files (including potential secrets) into the image.

## How does .dockerignore improve your build?
- Reduces build context size (faster build, less IO).
- Avoids copying local venvs and cache files into the image.
- Prevents leaking IDE configs, git history, logs, and other irrelevant files.

## Challenges & Solutions
# 1. “I cannot open my application” after `docker run`
**Fix**: Published the port with `-p 8000:8000`

# What I Learned
- Containers need explicit port publishing to be accessible from the host.
- Layer ordering dramatically affects build speed due to caching.
- Running as non-root is a simple but important security improvement.
- .dockerignore is crucial to keep images clean and builds fast.