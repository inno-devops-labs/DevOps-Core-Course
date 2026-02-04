# Lab 2 — Docker Containerization (Python)

## Docker Best Practices Applied
- **Pinned base image**: `python:3.13-slim` to ensure reproducible builds and security updates tracked by digest pinning.
- **Layer caching**: Copied `requirements.txt` before app code so dependency layer is reused when code changes without dependency changes.
- **Non-root user**: Created `app` system user/group and switched with `USER app` to reduce blast radius.
- **Small footprint**: Used `slim` variant and `--no-cache-dir` for pip; kept image minimal by copying only `app.py` and requirements.
- **.dockerignore**: Excludes venvs, VCS, IDE files, tests, docs to shrink build context and avoid leaking secrets.
- **Explicit workdir and CMD**: `WORKDIR /app`, `CMD ["python", "app.py"]` for clarity and predictability.

## Image Information & Decisions
- **Base image**: `python:3.13-slim`—latest GA Python with security patches, balanced size vs compatibility.
- **Final image size**: ~208 MB on arm64 host. Acceptable for Flask + Python runtime.
- **Layer structure**: OS + Python -> requirements install -> user creation -> app code. Keeps mutable layers (code) at the top for cache reuse.
- **Optimizations**: pip cache mount to speed rebuilds; no bytecode files (`PYTHONDONTWRITEBYTECODE=1`).

## Build & Run Process
```bash
igor@cilc DevOps-Core-Course % docker build -t devops_lab02:cilc app_python
[+] Building 4.4s (15/15) FINISHED                                                      docker:desktop-linux
 => [internal] load build definition from Dockerfile                                                    0.0s
 => => transferring dockerfile: 587B                                                                    0.0s
 => resolve image config for docker-image://docker.io/docker/dockerfile:1.7                             2.2s
 => [auth] docker/dockerfile:pull token for registry-1.docker.io                                        0.0s
 => CACHED docker-image://docker.io/docker/dockerfile:1.7@sha256:a57df69d0ea827fb7266491f2813635de6f17  0.0s
 => => resolve docker.io/docker/dockerfile:1.7@sha256:a57df69d0ea827fb7266491f2813635de6f17269be881f69  0.0s
 => [internal] load metadata for docker.io/library/python:3.13-slim                                     2.0s
 => [auth] library/python:pull token for registry-1.docker.io                                           0.0s
 => [internal] load .dockerignore                                                                       0.0s
 => => transferring context: 262B                                                                       0.0s
 => [stage-0 1/6] FROM docker.io/library/python:3.13-slim@sha256:2b9c9803c6a287cafa0a8c917211dddd23dcd  0.0s
 => => resolve docker.io/library/python:3.13-slim@sha256:2b9c9803c6a287cafa0a8c917211dddd23dcd2016f049  0.0s
 => [internal] load build context                                                                       0.0s
 => => transferring context: 63B                                                                        0.0s
 => CACHED [stage-0 2/6] WORKDIR /app                                                                   0.0s
 => CACHED [stage-0 3/6] COPY requirements.txt ./                                                       0.0s
 => CACHED [stage-0 4/6] RUN --mount=type=cache,target=/root/.cache/pip     pip install --no-cache-dir  0.0s
 => CACHED [stage-0 5/6] RUN addgroup --system app     && adduser --system --ingroup app app            0.0s
 => CACHED [stage-0 6/6] COPY --chown=app:app app.py ./                                                 0.0s
 => exporting to image                                                                                  0.0s
 => => exporting layers                                                                                 0.0s
 => => exporting manifest sha256:961953482c4997b5db2bdea8e87f8414f8291cc1b5139c52a5084694991bbaad       0.0s
 => => exporting config sha256:bc381b2a5bb82bd72482cc10e154b7f998d207d1a96c6676529cee6ed5a1197b         0.0s
 => => exporting attestation manifest sha256:7d3b614b171fad7230973774b5f023af954d2d8bd025047683360b9f6  0.0s
 => => exporting manifest list sha256:2e31fce956685f14ff858fd88694181adbe0c05251ba85db70f17fad712cdba4  0.0s
 => => naming to docker.io/library/devops_lab02:cilc                                                    0.0s
 => => unpacking to docker.io/library/devops_lab02:cilc                                                 0.0s

View build details: docker-desktop://dashboard/build/desktop-linux/desktop-linux/e8v6bfb62bbr1g2pua5tww3zs
igor@cilc DevOps-Core-Course % docker run --rm -p 8080:8080 devops_lab02:cilc
2026-02-04 16:06:44,331 INFO [root] Application starting...
 * Serving Flask app 'app'
 * Debug mode: off
2026-02-04 16:08:11,932 INFO [root] GET /health from 192.168.65.1
2026-02-04 16:08:17,775 INFO [root] GET / from 192.168.65.1
```

### Terminal Output 
```text
igor@cilc DevOps-Core-Course % curl -s http://localhost:8080/health
{"status":"healthy","timestamp":"2026-02-04T16:08:11.932722+00:00","uptime_seconds":87}
igor@cilc DevOps-Core-Course % curl -s http://localhost:8080/ | head -c 200
{"endpoints":[{"description":"Service information","method":"GET","path":"/"},{"description":"Health check","method":"GET","path":"/health"}],"request":{"client_ip":"192.168.65.1","method":"GET","path%   
```

## Technical Analysis
- **Layer order**: If code is copied before installing deps, any code change invalidates the heavy pip layer, slowing rebuilds. Current order isolates deps.
- **Security**: Non-root user prevents privilege escalation from app compromise; slim base reduces attack surface; .dockerignore keeps secrets/venvs out.
- **.dockerignore impact**: Smaller context speeds upload to daemon and avoids unnecessary files bloating layers.
- **Why it works**: Flask app binds to `0.0.0.0:8080`; `EXPOSE 8080` documents port; environment defaults mirror local run.

## Docker Hub
- Repository URL (replace with yours): `https://hub.docker.com/r/cilc/devops_lab02`
