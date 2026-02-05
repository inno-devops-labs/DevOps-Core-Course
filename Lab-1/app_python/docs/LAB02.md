# LAB02 - Docker Containerization (Python)

## Docker Best Practices Applied
- Non-root user: I created user `app` and run the app with `USER app` to reduce privileges.
- Fixed base image: `python:3.13-slim` gives a smaller and stable image.
- Layer caching: I copy `requirements.txt` first, then install deps so rebuilds are faster.
- Minimal copy: I only copy `requirements.txt` and `app.py`.
- `.dockerignore`: I exclude `venv/`, `tests/`, `docs/`, VCS, and IDE files to keep the context small.

Dockerfile snippets:
```dockerfile
FROM python:3.13-slim
```
Fixed base image keeps builds repeatable and smaller.

```dockerfile
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
```
Install deps before app code so cache works.

```dockerfile
RUN addgroup --system app && adduser --system --ingroup app app
USER app
```
Run as non-root for better security.

## Image Information & Decisions
- Base image: `python:3.13-slim` because it is smaller but still works with `pip` and `glibc`.
- Final image size: `127MB`.
- Layer order: base -> env/workdir -> user -> deps -> app code -> user -> cmd.
- Optimizations: slim image, cached deps, no pip cache.

## Build & Run Process
Build output:
```
docker build -t linktur/devops-lab2:v1 .
[+] Building 29.5s (12/12) FINISHED
 => [internal] load build definition from Dockerfile
 => [internal] load metadata for docker.io/library/python:3.13-slim
 => [internal] load .dockerignore
 => [1/6] FROM docker.io/library/python:3.13-slim
 => [2/6] WORKDIR /app
 => [3/6] RUN addgroup --system app && adduser --system --ingroup app app
 => [4/6] COPY requirements.txt .
 => [5/6] RUN pip install --no-cache-dir -r requirements.txt
 => [6/6] COPY app.py .
 => exporting to image
 => naming to docker.io/linktur/devops-lab2:v1
```

Run output:
```
docker run --rm -p 5000:5000 --name devops-lab2 linktur/devops-lab2:v1
2026-02-05 09:12:25,566 - __main__ - INFO - Application starting...
 * Serving Flask app 'app'
 * Debug mode: off
 * Running on all addresses (0.0.0.0)
 * Running on http://127.0.0.1:5000
 * Running on http://172.17.0.2:5000
Press CTRL+C to quit
2026-02-05 09:13:00,463 - werkzeug - INFO - 172.17.0.1 - - [05/Feb/2026 09:13:00] "GET /health HTTP/1.1" 200 -
2026-02-05 09:13:05,335 - werkzeug - INFO - 172.17.0.1 - - [05/Feb/2026 09:13:05] "GET / HTTP/1.1" 200 -
```

Endpoint tests:
```
curl http://localhost:5000/health
{"status":"healthy","timestamp":"2026-02-05T09:13:00.463Z","uptime_seconds":34}

curl http://localhost:5000/
{"endpoints":[{"description":"Service information","method":"GET","path":"/"},{"description":"Health check","method":"GET","path":"/health"}],"request":{"client_ip":"172.17.0.1","method":"GET","path":"/","user_agent":"curl/8.13.0"},"runtime":{"current_time":"2026-02-05T09:13:05.335Z","timezone":"UTC","uptime_human":"0 hours, 0 minutes","uptime_seconds":39},"service":{"description":"DevOps course info service","framework":"Flask","name":"devops-info-service","version":"1.0.0"},"system":{"architecture":"x86_64","cpu_count":12,"hostname":"99a476249f8","platform":"Linux","platform_version":"Debian GNU/Linux 13 (trixie)","python_version":"3.13.12"}}
```

Docker Hub repository URL:
```
https://hub.docker.com/repository/docker/linktur/devops-lab2
```
Screenshot with proof:
`screenshots/docker-logs.png`
## Technical Analysis
- The Dockerfile installs deps first, then copies app code. This keeps cache when only code changes.
- If I copy code before deps, every change breaks cache and build is slower.
- Security: non-root user, small base image, no extra tools.
- `.dockerignore` makes the build context smaller and faster.

## Challenges & Solutions
- What I learned: `I finally registered in Docker Hub.`
