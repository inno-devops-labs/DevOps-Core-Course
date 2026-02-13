# Lab 02 — Docker Containerization

## Docker Best Practices Applied

### 1. Non-root user

```dockerfile
RUN useradd --create-home --shell /bin/bash appuser
USER appuser
```

**Why:** Running as root means container escape = root on host. Non-root user limits damage if compromised.

### 2. Specific base image version

```dockerfile
FROM python:3.13-slim
```

**Why:** `python:latest` can change unexpectedly. Pinning `3.13-slim` ensures reproducible builds. Slim is ~150 MB vs ~1 GB for full image.

### 3. Layer ordering (dependencies before code)

```dockerfile
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
```

**Why:** Dependencies change rarely, code changes often. This order caches dependency layer, making rebuilds fast (seconds vs minutes).

### 4. .dockerignore

**Why:** Excludes `venv/`, `.git/`, docs from build context. Faster builds, prevents secrets from entering image.

### 5. --no-cache-dir for pip

```dockerfile
RUN pip install --no-cache-dir -r requirements.txt
```

**Why:** No reinstalls in Docker, cache just wastes space. Reduces image size.

---

## Image Information & Decisions

**Base image:** `python:3.13-slim` — Debian-based minimal Python image. Chosen over Alpine (musl libc compatibility issues). Good balance of size (~150 MB) and compatibility.

**Final image size:** ~170-200 MB (check with `docker images roma3213/info_service:1.0`)

**Layer structure:**

1. Base image (python:3.13-slim)
2. Create user
3. Set working directory
4. Copy requirements.txt
5. Install dependencies (cached separately)
6. Copy application code
7. Switch to non-root user

---

## Build & Run Process

### Build

```bash
cd app_python
docker build -t roma3213/info_service:1.0 .
```

**Terminal output:**

```
[+] Building 31.3s (11/11) FINISHED                                                                                               docker:desktop-linux
 => [internal] load build definition from Dockerfile                                                                                              0.2s
 => => transferring dockerfile: 281B                                                                                                              0.0s
 => [internal] load metadata for docker.io/library/python:3.13-slim                                                                               2.0s
 => [internal] load .dockerignore                                                                                                                 0.1s
 => => transferring context: 289B                                                                                                                 0.0s
 => [1/6] FROM docker.io/library/python:3.13-slim@sha256:3de9a8d7aedbb7984dc18f2dff178a7850f16c1ae7c34ba9d7ecc23d0755e35f                        10.1s
 => => resolve docker.io/library/python:3.13-slim@sha256:3de9a8d7aedbb7984dc18f2dff178a7850f16c1ae7c34ba9d7ecc23d0755e35f                         0.1s
 => => sha256:03af238a5946948d06e8485bb27b05831c5d13f0b3781a01fe347aaf847c2400 1.29MB / 1.29MB                                                    0.8s
 => => sha256:0c8d55a45c0dc58de60579b9cc5b708de9e7957f4591fc7de941b67c7e245da0 29.78MB / 29.78MB                                                  8.8s
 => => sha256:f1cadbd7abd229d3d8c50b4aa381724025f6bfe89783a8d2bfd6fa751a75946b 252B / 252B                                                        1.0s
 => => sha256:686599c79c8709aa5d9f1abf19c75b1760ae0a0ea0335206fe1db9a8793e09f6 11.80MB / 11.80MB                                                  6.2s
 => => extracting sha256:0c8d55a45c0dc58de60579b9cc5b708de9e7957f4591fc7de941b67c7e245da0                                                         0.7s
 => => extracting sha256:03af238a5946948d06e8485bb27b05831c5d13f0b3781a01fe347aaf847c2400                                                         0.1s
 => => extracting sha256:686599c79c8709aa5d9f1abf19c75b1760ae0a0ea0335206fe1db9a8793e09f6                                                         0.4s
 => => extracting sha256:f1cadbd7abd229d3d8c50b4aa381724025f6bfe89783a8d2bfd6fa751a75946b                                                         0.0s
 => [internal] load build context                                                                                                                 0.1s
 => => transferring context: 4.89kB                                                                                                               0.0s
 => [2/6] WORKDIR /app                                                                                                                            0.3s
 => [3/6] RUN useradd --create-home --shell /bin/bash appuser                                                                                     1.0s
 => [4/6] COPY requirements.txt .                                                                                                                 0.1s
 => [5/6] RUN pip install --no-cache-dir -r requirements.txt                                                                                     13.1s
 => [6/6] COPY . .                                                                                                                                0.1s
 => exporting to image                                                                                                                            3.8s
 => => exporting layers                                                                                                                           2.4s
 => => exporting manifest sha256:b218227291f74e8761d0df79e23c22fae99f0311107901b5e76cb89c72a1a55e                                                 0.1s
 => => exporting config sha256:f2ef2715b0f7271a2011dcc48f2375f243776b5a3330bbdfaba7f34b8ebc3b7d                                                   0.1s
 => => exporting attestation manifest sha256:9c55cad9161240ac44ab4ca9a11105878271afcfe5245d94f27ef097c0effa65                                     0.1s
 => => exporting manifest list sha256:9fb3c79f5a1e50a7a91bb55d089095581954ffc37b3236163b3b76b037bf8ab5                                            0.1s
 => => naming to docker.io/library/info_service:1.0                                                                                               0.0s
 => => unpacking to docker.io/library/info_service:1.0                                                                                            0.9s
```

### Run

```bash
docker run -d -p 5000:5000 roma3213/info_service:1.0
```

**Check container status:**
```bash
docker ps
```

```
CONTAINER ID   IMAGE                       COMMAND           CREATED         STATUS         PORTS                                         NAMES
91128e9d6039   roma3213/info_service:1.0   "python app.py"   2 minutes ago   Up 2 minutes   0.0.0.0:5000->5000/tcp, [::]:5000->5000/tcp   epic_elbakyan
```

### Testing

```bash
curl http://localhost:5000/
```

**Output:**
```json
{"service":{"name":"devops-info-service","version":"1.0.0","description":"DevOps course info service","framework":"FastAPI"},"system":{"hostname":"91128e9d6039","platform":"Linux","platform_version":"Linux-5.15.167.4-microsoft-standard-WSL2-x86_64-with-glibc2.41","architecture":"x86_64","cpu_count":12,"python_version":"3.13.12"},"runtime":{"uptime_seconds":186,"uptime_human":"0 hours, 3 minutes","current_time":"2026-02-13T11:01:43.559091+00:00","timezone":"UTC"},"request":{"client_ip":"172.17.0.1","user_agent":"curl/8.8.0","method":"GET","path":"/"},"endpoints":[{"path":"/","method":"GET","description":"Service information"},{"path":"/health","method":"GET","description":"Health check"}]}
```

```bash
curl http://localhost:5000/health
```

**Output:**
```json
{"status":"healthy","timestamp":"2026-02-13T11:02:11.626478+00:00","uptime_seconds":214}
```

### Docker Hub

```bash
docker tag roma3213/info_service:1.0 roma3213/info_service:1.0
docker login
docker push roma3213/info_service:1.0
```

**Docker Hub repository URL:** https://hub.docker.com/r/roma3213/info_service

---

## Technical Analysis

**Why layer order works:** Code changes frequently, dependencies don't. By copying requirements first, dependency layer is cached. Changing code only rebuilds from `COPY . .` onwards.

**If order changed:** `COPY . .` before `pip install` would invalidate cache on every code change → slow rebuilds.

**Security:**

- Non-root user prevents privilege escalation
- Slim image = smaller attack surface
- `.dockerignore` prevents secrets in image

**How .dockerignore helps:** Excludes `venv/`, `.git/` from build context → faster builds, smaller context.

---

## Challenges & Solutions

**Port mapping:** Forgot `-p 5000:5000` flag initially → app wasn't accessible. Always specify port mapping explicitly.

**Docker Hub tagging:** Must use full name `roma3213/info_service:1.0`, not just `info_service:1.0`, otherwise Docker looks in official repo.
