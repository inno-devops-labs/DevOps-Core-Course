# Lab 2 - Docker Containerization

## Docker Best Practices Applied

**Non-root user**

```Dockerfile
RUN useradd -m appuser
USER appuser
```

Running the app as a non-root user limits the impact of a potential compromise inside the container and follows security best practices.

**Slim official base image**

```
FROM python:3.13-slim AS runtime
```

The python:3.13-slim image is an official, actively maintained Python base with a minimal Debian userland, which keeps the image smaller and reduces the attack surface.

**Layer caching for dependencies**

```
COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY app.py .
COPY README.md ./README.md
```

Dependencies are installed in a separate layer based only on requirements.txt, so changing application code does not force reinstalling all Python packages, which speeds up rebuilds.

**.dockerignore usage**

A .dockerignore file is used to exclude venv/, .git, IDE configs and so on

## Image Information & Decisions

- **Base image: python:3.13-slim:**
  Official Python image with a slim Debian base, suitable for lightweight production containers.
- **Final image size**
  plaffyyy9/devops-info-service                                         lab2                       e5675a8ee0d9   3 hours ago     221M
- The app listens on port 5001 inside the container, and the Dockerfile exposes this port for clarity.

## Build & Run Process

**Build**

```
docker build -t devops-info-service:lab2 .
```

**Example build output (excerpt):**

[+] Building 2.3s (13/13) FINISHED
 => [internal] load build definition from Dockerfile
 => [internal] load metadata for docker.io/library/python:3.13-slim
 => [internal] load .dockerignore
 => [1/7] FROM docker.io/library/python:3.13-slim@sha256:2b9c9803c6a287cafa0a8c917211dddd23dcd2016f049690ee5219f5d3f1636e
 => [internal] load build context
 => CACHED [2/7] WORKDIR /app
 => CACHED [3/7] COPY requirements.txt .
 => CACHED [4/7] RUN pip install --no-cache-dir -r requirements.txt
 => CACHED [5/7] RUN useradd -m appuser
 => CACHED [6/7] COPY app.py .
 => CACHED [7/7] COPY README.md ./README.md
 => exporting to image
 => naming to docker.io/library/devops-info-service:lab2

**Run**

```
docker run --rm -p 8081:5001 devops-info-service:lab2
```

**Container logs**

```
2026-02-04 11:54:41,025 - __main__ - INFO - Starting DevOps Info Service on 0.0.0.0:5001 (debug=False)
 * Serving Flask app 'app'
 * Debug mode: off
2026-02-04 11:54:41,026 - werkzeug - INFO - WARNING: This is a development server. Do not use it in a production deployment. Use a production WSGI server instead.
 * Running on all addresses (0.0.0.0)
 * Running on http://127.0.0.1:5001
 * Running on http://172.17.0.2:5001
2026-02-04 11:55:04,723 - __main__ - INFO - Request: GET / from 151.101.64.223
2026-02-04 11:55:04,724 - werkzeug - INFO - 151.101.64.223 - - [04/Feb/2026 11:55:04] "GET / HTTP/1.1" 200 -
2026-02-04 11:59:00,966 - __main__ - INFO - Request: GET / from 151.101.64.223
2026-02-04 11:59:00,966 - werkzeug - INFO - 151.101.64.223 - - [04/Feb/2026 11:59:00] "GET / HTTP/1.1" 200 -
2026-02-04 11:59:01,037 - werkzeug - INFO - 151.101.64.223 - - [04/Feb/2026 11:59:01] "GET /favicon.ico HTTP/1.1" 404 -
```

**Endpoint Testing**

```
curl http://localhost:8081/
curl http://localhost:8081/health
```

**Pull and run from Docker Hub:**

```
docker pull plaffyyy9/devops-info-service:lab2
docker run --rm -p 8081:5001 plaffyyy9/devops-info-service:lab2
```

## Technical Analysis

The Dockerfile is structured so that dependency installation is separated from application code. As long as requirements.txt does not change, the pip install layer can be reused from cache and rebuilds after code changes are very fast.

Running the application as a non-root user (appuser) improves security by limiting what an attacker can do if the web service is compromised.

The .dockerignore file keeps the build context small by excluding virtual environments, Python bytecode, Git metadata, IDE configuration, documentation, and tests. This reduces build time and prevents unnecessary files from ending up in the final image.

## Challenges & Solutions

**Base image pull timeouts**

**Problem:** At one point, pulling python:3.13-slim failed due to a transient TLS handshake timeout.

**Solution:** Re-ran the build later; the base image was pulled successfully and reused by Docker cache afterward.

**Port already in use on host**

**Problem:** Mapping -p 5000:5000 failed because port 5000 was already occupied on the host.

**Solution:** Switched to a different host port (8081) and mapped it to the internal port 5001.
