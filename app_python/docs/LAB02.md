# LAB02 — Документация по Docker

Дата: 2026-02-05

Цель: документировать решение по контейнеризации `app_python` и объяснить принятые решения.

## 1. Docker Best Practices Applied

- **Non-root user**: в `Dockerfile` создан пользователь `appuser` и используется инструкция `USER appuser`.
  - Почему важно: запуск приложения не от root снижает риск эскалации привилегий в случае уязвимости.
  - Фрагмент Dockerfile:

# LAB02 — Docker documentation

Date: 2026-02-05

Goal: document the containerization of `app_python` and explain implementation decisions.

## 1. Docker Best Practices Applied

- **Non-root user**: the `Dockerfile` creates a dedicated user `appuser` and switches to it with `USER appuser`.
  - Why it matters: running the application as non-root reduces the risk of privilege escalation if the application is compromised.
  - Dockerfile snippet:

```dockerfile
RUN groupadd --gid 1000 appgroup \
    && useradd --uid 1000 --gid appgroup --create-home --home-dir /home/appuser --shell /bin/bash appuser
USER appuser
```

- **Layer caching (layer ordering)**: dependencies are copied and installed first (`COPY requirements.txt` + `RUN pip install ...`), then application code is copied.
  - Why it matters: when code changes, dependency layers remain cached so builds are faster.
  - Dockerfile snippet:

```dockerfile
WORKDIR /app
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY app.py ./
```

- **.dockerignore**: unnecessary files are excluded (`__pycache__`, `tests`, `docs`, `.git`, virtual environments, etc.).
  - Why it matters: reduces build context size, speeds up context upload, and lowers the chance of accidentally including secrets.
  - Example entries: `__pycache__/`, `*.pyc`, `tests/`, `docs/`, `.git`, `venv/`.

- **Minimal files copied into the image**: only `requirements.txt` and `app.py` are copied.
  - Why it matters: reduces image size and attack surface.

- **Documented port**: `EXPOSE 5002` reflects the `PORT` used in `app.py`.
  - Why it matters: clarifies how container port maps to host port.

## 2. Image Information & Decisions

- **Base image:** `python:3.13-slim`
  - Rationale: a recent Python 3.13 base that balances completeness with size; the `-slim` variant reduces unnecessary packages while still being well-supported.

- **Final image size:** locally the image is `208MB` for `sofiakulagina/devops-info:lab2`.
  - Assessment: acceptable for a simple Flask app without compiled dependencies. Options to reduce size further include `python:3.13-alpine` or multi-stage builds, but alpine can require additional work for binary dependencies.

- **Layer structure:**
  1. `FROM python:3.13-slim`
  2. create user and directories (`RUN groupadd && useradd ...`)
  3. `WORKDIR /app`
  4. `COPY requirements.txt` (dependencies layer)
  5. `RUN pip install ...` (installed packages)
  6. `COPY app.py` (application code)
  7. set ownership and switch to non-root user
  8. `EXPOSE` and `CMD`

  - Optimization rationale: place rarely-changed layers (dependencies) before frequently-changed layers (code).

## 3. Build & Run Process

Below is the full build and push output copied from the terminal:

```
[+] Building 13.7s (13/13) FINISHED                           docker:desktop-linux
 => [internal] load build definition from Dockerfile                          0.0s
 => => transferring dockerfile: 762B                                          0.0s
 => [internal] load metadata for docker.io/library/python:3.13-slim           2.2s
 => [auth] library/python:pull token for registry-1.docker.io                 0.0s
 => [internal] load .dockerignore                                             0.0s
 => => transferring context: 127B                                             0.0s
 => [1/7] FROM docker.io/library/python:3.13-slim@sha256:49b618b8afc2742b94f  7.5s
 => => resolve docker.io/library/python:3.13-slim@sha256:49b618b8afc2742b94f  0.0s
 => => sha256:4c4a8dac933699cea1f21584a1e5db68e248aadadfff93ddd7 251B / 251B  0.4s
 => => sha256:14c37da83ac4440d59e5d2c0f06fb6ccd1c771929bd408 1.27MB / 1.27MB  1.0s
 => => sha256:af94c6242df37e8cf3963ed59ccc0252e79a0554a8f1 11.73MB / 11.73MB  3.7s
 => => sha256:3ea009573b472d108af9af31ec35a06fe3649084f661 30.14MB / 30.14MB  6.8s
 => => extracting sha256:3ea009573b472d108af9af31ec35a06fe3649084f6611cf11f7  0.4s
 => => extracting sha256:14c37da83ac4440d59e5d2c0f06fb6ccd1c771929bd4083c0a3  0.0s
 => => extracting sha256:af94c6242df37e8cf3963ed59ccc0252e79a0554a8f18f4555d  0.2s
 => => extracting sha256:4c4a8dac933699cea1f21584a1e5db68e248aadadfff93ddd73  0.0s
 => [internal] load build context                                             0.0s
 => => transferring context: 4.20kB                                           0.0s
 => [2/7] RUN groupadd --gid 1000 appgroup     && useradd --uid 1000 --gid a  0.5s
 => [3/7] WORKDIR /app                                                        0.0s
 => [4/7] COPY requirements.txt ./                                            0.0s
 => [5/7] RUN pip install --no-cache-dir -r requirements.txt                  3.0s
 => [6/7] COPY app.py ./                                                      0.0s
 => [7/7] RUN chown -R appuser:appgroup /app                                  0.1s
 => exporting to image                                                        0.3s 
 => => exporting layers                                                       0.1s 
 => => exporting manifest sha256:c642c1c7aaee4610b39023ffcadbed270e6451b5c9f  0.0s 
 => => exporting config sha256:a9190d3d8c85ae31f27fa2ce1878878d83fce01a98442  0.0s 
 => => exporting attestation manifest sha256:5e06288fb0b759a0d0c0d51a3509877  0.1s
 => => exporting manifest list sha256:2e664e7122e99b89753b34ffa33fad32cf91c2  0.0s
 => => naming to docker.io/library/devops-info:lab2                           0.0s
 => => unpacking to docker.io/library/devops-info:lab2                        0.0s
```

Authentication and push output:

```
Authenticating with existing credentials... [Username: sofiakulagina]

i Info → To login with a different account, run 'docker logout' followed by 'docker login'

Login Succeeded
The push refers to repository [docker.io/sofiakulagina/devops-info]
fb9638eac157: Pushed 
4c4a8dac9336: Pushed 
3ea009573b47: Pushed 
334e78adf83a: Pushed 
de87663f4206: Pushed 
af94c6242df3: Pushed 
37c0e012c728: Pushed 
004840e29eb7: Pushed 
4f4fb700ef54: Mounted from vulhub/langflow 
de09dc1fb1f3: Pushed 
14c37da83ac4: Pushed 
lab2: digest: sha256:2e664e7122e99b89753b34ffa33fad32cf91c2843be398292fd1d2a97b167558 size: 856
{
   "schemaVersion": 2,
   "mediaType": "application/vnd.oci.image.index.v1+json",
   "manifests": [
      {
         "mediaType": "application/vnd.oci.image.manifest.v1+json",
         "size": 2189,
         "digest": "sha256:c642c1c7aaee4610b39023ffcadbed270e6451b5c9f1019b3c3cc483d6c260df",
         "platform": {
            "architecture": "arm64",
            "os": "linux"
         }
      },
      {
         "mediaType": "application/vnd.oci.image.manifest.v1+json",
         "size": 566,
         "digest": "sha256:5e06288fb0b759a0d0c0d51a35098779dc0b0e8c68ff67b936c7e3f844a25006",
         "platform": {
            "architecture": "unknown",
            "os": "unknown"
         }
      }
   ]
}
```

Below is the output from running the container and testing endpoints locally:

```
de299d26c9701ccf05e8fc8221db02946e058a9a3c8b766ec3d7c9ad38784f05
de299d26c970 sofiakulagina/devops-info:lab2 Up 1 second
2026-02-05 10:40:00,921 - __main__ - INFO - Application starting...
2026-02-05 10:40:00,921 - __main__ - INFO - Starting Flask development server on 0.
0.0.0.0:5002                                                                          * Serving Flask app 'app'
 * Debug mode: off
2026-02-05 10:40:00,926 - werkzeug - INFO - WARNING: This is a development server. 
Do not use it in a production deployment. Use a production WSGI server instead.     * Running on all addresses (0.0.0.0)
 * Running on http://127.0.0.1:5002
 * Running on http://172.17.0.2:5002
2026-02-05 10:40:00,926 - werkzeug - INFO - Press CTRL+C to quit
{"endpoints":[{"description":"Service information","method":"GET","path":"/"},{"description":"Health check","method":"GET","path":"/health"}],"request":{"client_ip":"192.168.65.1","method":"GET","path":"/","user_agent":"curl/8.7.1"},"runtime":{"current_time":"2026-02-05T10:40:01.742865+00:00","timezone":"UTC","uptime_human":"0 hours, 0 minutes","uptime_seconds":0},"service":{"description":"DevOps course info service","framework":"Flask","name":"devops-info-service","version":"1.0.0"},"system":{"architecture":"aarch64","cpu_count":10,"hostname":"de299d26c970","platform":"Linux","platform_version":"Linux-6.10.14-linuxkit-aarch64-with-glibc2.41","python_version":"3.13.12"}}
{"status":"healthy","timestamp":"2026-02-05T10:40:01.753235+00:00","uptime_seconds":0}
```

**Docker Hub repository URL:** https://hub.docker.com/r/sofiakulagina/devops-info

## 4. Technical Analysis

- **Why the Dockerfile works:** instruction ordering minimizes unnecessary layer rebuilds—dependencies are installed before copying frequently-changing application code. The user and permissions are created and fixed before switching to the non-root user.

- **What happens if layer order changes:** copying the entire source first would invalidate the cached dependency layers on every code change, causing slower rebuilds.

- **Security considerations:** running as non-root, limiting copied files, and excluding sensitive files via `.dockerignore`.

- **How `.dockerignore` improves build:** reduces context size, lowers the risk of accidentally including sensitive or unnecessary files, and speeds up `docker build`.

## 5. Challenges & Solutions

- **Issue:** an earlier attempt to run `docker build` failed because the build context `app_python` was not found.
  - **How I debugged:** confirmed the current working directory was the repository root and that the `app_python` folder exists; rerunning the command from the correct directory fixed the issue.

- **Issue:** Flask prints a warning about using the development server.
  - **Resolution/notes:** for production, use a WSGI server like `gunicorn` or `uvicorn`; for lab/testing, the development server is acceptable.

## 6. Improvements to consider

- Switch to a production-ready WSGI server (`gunicorn`) and update `CMD` accordingly.
- Consider multi-stage builds or `python:3.13-alpine` to reduce image size (account for compiling dependencies).
- Add CI to build and push images automatically on releases.

---

Files: `Dockerfile` and `.dockerignore` are in `app_python`.
