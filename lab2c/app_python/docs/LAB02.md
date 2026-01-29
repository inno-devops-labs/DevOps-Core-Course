# LAB02 - Docker Containerization (Python)

## Docker Best Practices Applied
- **Pinned base image**: `python:3.13-slim` keeps the image small and reproducible.
- **Non-root user**: the container runs as `appuser`, so the service does not run as root.
- **Layer caching**: dependencies are installed before copying the app so rebuilds are faster.
- **Minimal copy**: only `requirements.txt` and `app.py` are copied into the image.
- **.dockerignore**: excluded tests, docs, and virtualenvs to keep the build context small.

Dockerfile snippet:
```dockerfile
FROM python:3.13-slim
WORKDIR /app
RUN useradd -m -u 10001 appuser
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY --chown=appuser:appuser app.py .
USER appuser
```

## Image Information and Decisions
- **Base image choice**: `python:3.13-slim` is a good balance of size and compatibility.
- **Final image size**: `<fill in after build>`
- **Layer structure**: dependencies are installed in their own layer to benefit from caching.
- **Optimization choices**: small base image, no extra build tools, only required files copied.

Image size output:
```text
tsixphoenix/devops-info-python                beta              04eec5e16beb   5 minutes ago       228MB
```

## Build and Run Process
Build output:
```text
docker build -t tsixphoenix/devops-info-python:beta .
[+] Building 16.7s (11/11) FINISHED                                                                                                                                                                      docker:desktop-linux
 => [internal] load build definition from Dockerfile                                                                                                                                                                     0.0s
 => => transferring dockerfile: 332B                                                                                                                                                                                     0.0s
 => [internal] load metadata for docker.io/library/python:3.13-slim                                                                                                                                                      2.3s
 => [internal] load .dockerignore                                                                                                                                                                                        0.0s
 => => transferring context: 133B                                                                                                                                                                                        0.0s
 => [1/6] FROM docker.io/library/python:3.13-slim@sha256:51e1a0a317fdb6e170dc791bbeae63fac5272c82f43958ef74a34e170c6f8b18                                                                                                2.4s
 => => resolve docker.io/library/python:3.13-slim@sha256:51e1a0a317fdb6e170dc791bbeae63fac5272c82f43958ef74a34e170c6f8b18                                                                                                0.0s
 => => sha256:8843ea38a07e15ac1b99c72108fbb492f737032986cc0b65ed351f84e5521879 1.29MB / 1.29MB                                                                                                                           0.5s
 => => sha256:36b6de65fd8d6bd36071ea9efa7d078ebdc11ecc23d2426ec9c3e9f092ae824d 249B / 249B                                                                                                                               0.6s
 => => sha256:0bee50492702eb5d822fbcbac8f545a25f5fe173ec8030f57691aefcc283bbc9 11.79MB / 11.79MB                                                                                                                         1.5s
 => => extracting sha256:8843ea38a07e15ac1b99c72108fbb492f737032986cc0b65ed351f84e5521879                                                                                                                                0.3s
 => => extracting sha256:0bee50492702eb5d822fbcbac8f545a25f5fe173ec8030f57691aefcc283bbc9                                                                                                                                0.8s 
 => => extracting sha256:36b6de65fd8d6bd36071ea9efa7d078ebdc11ecc23d2426ec9c3e9f092ae824d                                                                                                                                0.0s
 => [internal] load build context                                                                                                                                                                                        0.0s
 => => transferring context: 4.60kB                                                                                                                                                                                      0.0s
 => [2/6] WORKDIR /app                                                                                                                                                                                                   0.1s 
 => [3/6] RUN useradd -m -u 10001 appuser                                                                                                                                                                                0.6s
 => [4/6] COPY requirements.txt .                                                                                                                                                                                        0.0s
 => [5/6] RUN pip install --no-cache-dir -r requirements.txt                                                                                                                                                             8.8s 
 => [6/6] COPY --chown=appuser:appuser app.py .                                                                                                                                                                          0.1s
 => exporting to image                                                                                                                                                                                                   2.1s
 => => exporting layers                                                                                                                                                                                                  1.4s
 => => exporting manifest sha256:89257312508e9a26af1f7400253d9556816a0fc9230a414836bcedb8a4881c86                                                                                                                        0.0s
 => => exporting config sha256:a7d85cde725e6fdfb1dfbccbb9daadb4138561a5698ac01f5f6e2780b62994f3                                                                                                                          0.0s
 => => exporting attestation manifest sha256:82c962563c14aaa47813d2f1b62afb9806c83dbb0519256fd9954a50ea14fd3f                                                                                                            0.0s
 => => exporting manifest list sha256:04eec5e16beb90a39cdac694238e9c6301410b6fa987d7b7788c03287ed57da0                                                                                                                   0.0s
 => => naming to docker.io/tsixphoenix/devops-info-python:beta                                                                                                                                                           0.0s
 => => unpacking to docker.io/tsixphoenix/devops-info-python:beta
```

Run output (container start):
```text
docker run --rm -p 5000:5000 --name devops-info tsixphoenix/devops-info-python:beta
2026-01-29 12:23:57,799 - INFO - Starting DevOps Info Service on 0.0.0.0:5000
INFO:     Started server process [1]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:5000 (Press CTRL+C to quit)
```

Endpoint checks:
```text
curl http://localhost:5000/
{"service":{"name":"devops-info-service","version":"1.0.0","description":"DevOps course info service","framework":"FastAPI"},"system":{"hostname":"d65d9dfde3f9","platform":"Linux","platform_version":"6.6.87.2-microsoft-standard-WSL2","architecture":"x86_64","cpu_count":12,"python_version":"3.13.11"},"runtime":{"uptime_seconds":98,"uptime_human":"0 hours, 1 minute","current_time":"2026-01-29T12:25:35.964833Z","timezone":"UTC"},"request":{"client_ip":"172.17.0.1","user_agent":"curl/8.16.0","method":"GET","path":"/"},"endpoints":[{"path":"/","method":"GET","description":"Service information"},{"path":"/health","method":"GET","description":"Health check"}]}

curl http://localhost:5000/health
{"status":"healthy","timestamp":"2026-01-29T12:25:56.660917Z","uptime_seconds":118}

2026-01-29 12:25:35,964 - INFO - Request: GET /
2026-01-29 12:25:35,965 - INFO - Response: GET / -> 200
INFO:     172.17.0.1:54462 - "GET / HTTP/1.1" 200 OK
2026-01-29 12:25:56,659 - INFO - Request: GET /health
2026-01-29 12:25:56,661 - INFO - Response: GET /health -> 200
INFO:     172.17.0.1:57328 - "GET /health HTTP/1.1" 200 OK
```

Docker Hub repository URL:
```
https://hub.docker.com/repository/docker/tsixphoenix/devops-info-python/general
```

Tagging strategy:
```
version tag
```

## Technical Analysis
- The Dockerfile copies `requirements.txt` first so dependency layers are cached between builds.
- If I copied the whole project before installing dependencies, every code change would bust the cache.
- Running as a non-root user reduces risk if a container is compromised.
- `.dockerignore` keeps the build context small, which speeds up the build and reduces image size.

## Challenges and Solutions
- I verified the app binds to `0.0.0.0` so it is reachable from outside the container.
- I double-checked that only the needed files are copied into the image to avoid bloating it.
