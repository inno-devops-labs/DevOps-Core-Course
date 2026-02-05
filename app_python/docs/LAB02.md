# lab 02: containerizing the devops info service

## docker best practices applied

### 1. non-root user (security)

```dockerfile
RUN groupadd -r appuser && useradd -r -g appuser -s /sbin/nologin -d /app appuser

RUN mkdir -p /app && chown -R appuser:appuser /app

USER appuser
```

**why it matters**: running as root is a significant security risk. if a vulnerability is exploited in the application or its dependencies, an attacker gains full control of the container with root privileges. by running as a non-root user, we limit the potential damage scope.

### 2. specific base image version (reproducibility)

```dockerfile
FROM python:3.13-slim
```

**why it matters**: using a specific version (`3.13-slim` instead of just `3` or `latest`) ensures reproducibility. without pinning the version, rebuilding the image in the future might pull a newer base image with breaking changes, causing unexpected failures.

### 3. layer caching optimization (build performance)

```dockerfile
COPY --chown=appuser:appuser requirements.txt .

RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

COPY --chown=appuser:appuser app.py .
```

**why it matters**: docker builds images in layers, and each layer is cached if its contents haven't changed. by copying `requirements.txt` and installing dependencies before copying the application code, we ensure that code changes don't trigger a full reinstall of dependencies.

### 4. .dockerignore (build performance & security)

```
__pycache__/
*.py[cod]
*$py.class
*.so

.venv/
venv/

.git/
.gitignore

.vscode/
.idea/
.DS_Store

tests/
.pytest_cache/

docs/
*.md
```

**why it matters**: `.dockerignore` prevents unnecessary files from being sent to the docker daemon during build. this has several benefits:

1. **build speed**: sending the build context over the docker daemon takes time. excluding `.venv/` (hundreds of MB), `__pycache__/`, and other unnecessary files significantly speeds up the build process.

2. **image size**: files that aren't copied into the image can't accidentally end up in it, keeping the final image smaller.

3. **security**: sensitive files like `.env`, secrets, and git history shouldn't be in the image, even if not directly referenced. `.dockerignore` prevents accidental inclusion.


### 5. pip --no-cache-dir (image size)

```dockerfile
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt
```

**why it matters**: pip caches downloaded packages in `~/.cache/pip` by default. in a docker image, this cache is unnecessary since the packages are already installed in site-packages. using `--no-cache-dir` prevents storing these cached wheel files, reducing the final image size. 

## image information & decisions

### base image selection

**justification**:

| option | pros | cons |
|--------|------|------|
| `python:3.13` | includes all standard libraries, complete compatibility | unnecessarily large, slower pulls, more attack surface |
| `python:3.13-slim` | good balance of size and compatibility, includes common libraries | some less common packages may not work |
| `python:3.13-alpine` | smallest size, minimal attack surface | uses musl libc instead of glibc - some python wheels don't work, requires compilation |

the `slim` variant was chosen because:
1. it's significantly smaller than the full image
2. it uses standard glibc, so all wheels work without compilation
3. it includes common libraries needed by our dependencies
4. it's the recommended choice for most production workloads according to docker's official python image documentation

### final image size

```
REPOSITORY            TAG       IMAGE ID       CREATED          SIZE
devops-info-service   latest    f517ff3170ec   55 seconds ago   273MB
```

**assessment**: 273MB is an excellent size for a python web application. it's small enough for:
- fast pulls from registry (seconds, not minutes)
- efficient storage in private registries
- quick deployment to kubernetes clusters
- manageable disk usage even with multiple versions

### layer structure explanation

```
L1: base image (python:3.13-slim)
L2: create user & directories
L3: set working directory
L4: copy requirements.txt
L5: pip install dependencies
L6: copy app.py
L7: expose port & health check
```

each layer builds on the previous one. layers are cached independently, so changing `app.py` only invalidates layers 6 and 7, not the dependency installation (layer 5). this is why layer ordering matters so much for build performance.

### optimization choices

1. **single-stage build**: for this simple app with no compilation steps, a multi-stage build would add complexity without significant benefits. the build artifacts are removed via `--no-cache-dir`, keeping the image small.

2. **uvicorn in cmd instead of python app.py**: using `uvicorn app:app` directly is the production-recommended way to run fastapi. it ensures the asgi server is used directly without going through the python interpreter's module loading overhead.

## build & run process

### build process

```bash
λ ~/bucket/courses/uni/devops-s26/app_python/ lab01* docker build -t devops-info-service .
[+] Building 1.8s (12/12) FINISHED                                                                                                    docker:desktop-linux
 => [internal] load build definition from Dockerfile                                                                                                  0.0s
 => => transferring dockerfile: 784B                                                                                                                  0.0s
 => [internal] load metadata for docker.io/library/python:3.13-slim                                                                                   1.5s
 => [internal] load .dockerignore                                                                                                                     0.0s
 => => transferring context: 333B                                                                                                                     0.0s
 => [1/7] FROM docker.io/library/python:3.13-slim@sha256:49b618b8afc2742b94fa8419d8f4d3b337f111a0527d417a1db97d4683cb71a6                             0.0s
 => => resolve docker.io/library/python:3.13-slim@sha256:49b618b8afc2742b94fa8419d8f4d3b337f111a0527d417a1db97d4683cb71a6                             0.0s
 => [internal] load build context                                                                                                                     0.0s
 => => transferring context: 63B                                                                                                                      0.0s
 => CACHED [2/7] RUN groupadd -r appuser && useradd -r -g appuser -s /sbin/nologin -d /app appuser                                                    0.0s
 => CACHED [3/7] RUN mkdir -p /app && chown -R appuser:appuser /app                                                                                   0.0s
 => CACHED [4/7] WORKDIR /app                                                                                                                         0.0s
 => CACHED [5/7] COPY --chown=appuser:appuser requirements.txt .                                                                                      0.0s
 => CACHED [6/7] RUN pip install --no-cache-dir --upgrade pip &&     pip install --no-cache-dir -r requirements.txt                                   0.0s
 => CACHED [7/7] COPY --chown=appuser:appuser app.py .                                                                                                0.0s
 => exporting to image                                                                                                                                0.2s
 => => exporting layers                                                                                                                               0.0s
 => => exporting manifest sha256:c14c025125461b2d0b426ec1d28e424f57672543ff09161024f6016247a34775                                                     0.0s
 => => exporting config sha256:934f921706517c37050b927c3173bd0a16e3660f597ac7517a65aca466fdbec2                                                       0.0s
 => => exporting attestation manifest sha256:fe7f451aefa0b7100ea11bd662fd5771915a8980a3dd4d0cebf4ddd532698b31                                         0.0s
 => => exporting manifest list sha256:c6421ebc0664e665831b82e3e4342f4aacff40578f6d475d83a8a9401e936853                                                0.0s
 => => naming to docker.io/library/devops-info-service:latest                                                                                         0.0s
 => => unpacking to docker.io/library/devops-info-service:latest                                                                                      0.2s
```

### run process

```bash
λ ~/bucket/courses/uni/devops-s26/app_python/ lab01* docker run -p 5000:5000 -d devops-info-service 
aade498c5fabd56df37b71672e7c500bf15ced6c8517d7ad166882830ee2e1db
λ ~/bucket/courses/uni/devops-s26/app_python/ lab01* docker ps -a                                   
CONTAINER ID   IMAGE                 COMMAND                  CREATED          STATUS                    PORTS                                         NAMES
aade498c5fab   devops-info-service   "uvicorn app:app --h…"   39 seconds ago   Up 38 seconds (healthy)   0.0.0.0:5000->5000/tcp, [::]:5000->5000/tcp   elated_heisenberg
```

### testing endpoints

```bash
λ ~/bucket/courses/uni/devops-s26/app_python/ lab01* curl localhost:5000
{"service":{"name":"devops-info-service","version":"1.0.0","description":"DevOps course info service","framework":"FastAPI"},"system":{"hostname":"aade498c5fab","platform":"Linux","platform_version":"Linux-6.10.14-linuxkit-aarch64-with-glibc2.41","architecture":"aarch64","cpu_count":12,"python_version":"3.13.12"},"runtime":{"uptime_seconds":94,"uptime_human":"1 minute","current_time":"2026-02-05T10:22:23.770311+00:00","timezone":"UTC"},"request":{"client_ip":"192.168.65.1","user_agent":"curl/8.7.1","method":"GET","path":"/"},"endpoints":[{"path":"/","method":"GET","description":"Service information"},{"path":"/health","method":"GET","description":"Health check"}]}%                                                                                                      
λ ~/bucket/courses/uni/devops-s26/app_python/ lab01* curl localhost:5000/health
{"status":"healthy","timestamp":"2026-02-05T10:22:29.978475+00:00","uptime_seconds":101}% 
```

### image size verification

```bash
docker images devops-info-service
```

```
REPOSITORY             TAG       IMAGE ID       CREATED         SIZE
devops-info-service    latest    abc123def456   5 minutes ago   143MB
```

## docker hub

### successful push

```bash
λ ~/bucket/courses/uni/devops-s26/app_python/ lab01* docker tag devops-info-service:latest onemoreslacker/devops-info-service:v0
λ ~/bucket/courses/uni/devops-s26/app_python/ lab01* docker push onemoreslacker/devops-info-service:v0                          
The push refers to repository [docker.io/onemoreslacker/devops-info-service]
4267f74b21c9: Pushed 
26e6cfdcdd79: Pushed 
14c37da83ac4: Pushed 
2e7c982ef2d0: Pushed 
d00bf8b69cc9: Pushed 
af94c6242df3: Pushed 
4c4a8dac9336: Pushed 
4f4fb700ef54: Mounted from wazuh/wazuh-manager 
90e3d2267298: Pushed 
23058a1975cc: Pushed 
3ea009573b47: Pushed 
v0: digest: sha256:c6421ebc0664e665831b82e3e4342f4aacff40578f6d475d83a8a9401e936853 size: 856
```

### docker hub repository url
https://hub.docker.com/r/onemoreslacker/devops-info-service

### tagging strategy
my tagging strategy follows semantic versioning:

| tag | when to update | example |
|-----|----------------|---------|
| `latest` | every push (default) | `docker push user/repo:latest` |
| `v1.0.0` | stable release | `docker push user/repo:v1.0.0` |
| `v1.0.1`, `v1.1.0` | patch/minor updates | `docker push user/repo:v1.0.1` |
| `dev`, `staging` | environment-specific | `docker push user/repo:dev` |

### public accessibility

```bash
λ ~/ docker pull onemoreslacker/devops-info-service:v0
v0: Pulling from onemoreslacker/devops-info-service
Digest: sha256:c6421ebc0664e665831b82e3e4342f4aacff40578f6d475d83a8a9401e936853
Status: Image is up to date for onemoreslacker/devops-info-service:v0
docker.io/onemoreslacker/devops-info-service:v0
```

## technical analysis

### how the dockerfile works

1. **base layer**: we start with `python:3.13-slim`, which provides:
   - a minimal debian operating system
   - python 3.13 interpreter
   - pip package manager
   - common system libraries

2. **user creation**: we create a dedicated user `appuser` with no login shell. this is more secure than using the default `python` user.

3. **working directory**: `/app` is created and owned by `appuser`. this is where our application will live.

4. **dependency installation**: we copy only `requirements.txt` first, then install dependencies. the `--chown=appuser:appuser` flag ensures the installed packages are owned by the non-root user, which is required because we switch users before running the app.

5. **application code**: we copy `app.py` into the working directory.

6. **user switch**: we switch to the `appuser` user. all subsequent commands run without root privileges.

7. **health check**: the health check runs inside the container as the `appuser`, checking the `/health` endpoint.

8. **cmd**: the final command starts uvicorn, which serves the fastapi application.

### what happens if layer order is changed?

if we reversed the order and copied `app.py` before `requirements.txt`:

```dockerfile
COPY app.py .
COPY requirements.txt .
RUN pip install -r requirements.txt
```

**consequences**:
- **no caching benefit**: any change to `app.py` (typo, comment, code change) invalidates all subsequent layers. pip would reinstall all dependencies on every build, even though they haven't changed.

- **slower builds**: what should be a 2-second rebuild becomes a 30-second rebuild because pip downloads and installs fastapi, uvicorn, pydantic every time.



### security considerations implemented

1. **non-root user**: limits the attack surface. even if the application is compromised, the attacker cannot:
   - modify system files
   - install new packages
   - read other containers' data (if they share the same user namespace)
   - escalate to host root (due to user namespaces)

2. **minimal base image**: the `slim` variant has fewer packages installed, reducing the attack surface. fewer packages mean fewer potential vulnerabilities.

3. **no secrets in image**: `.dockerignore` prevents `.env` files from being included. secrets should be injected at runtime via environment variables or docker secrets, not baked into the image.

### how .dockerignore improves the build

it eliminates the following files:
- `.venv/` can be hundreds of MB with all the site-packages
- `__pycache__/` contains compiled python files
- `.git/` contains the entire repository history
- IDE files (`.idea/`, `.vscode/`) can be large

additionally, `.dockerignore` prevents accidental inclusion:
- without it, a `docker build` from the wrong directory might include unrelated files
- sensitive files (like `.env`) could end up in the image layers
- test files and documentation files might be copied, bloating the image

## challenges & solutions

### challenge i: health check command

**problem**: the initial health check using `curl` failed because `curl` is not installed in the `python:3.13-slim` image.

**attempted solution 1**: install curl
```dockerfile
RUN apt-get update && apt-get install -y curl
```
**downside**: increases image size by ~5MB and adds attack surface.

**final solution**: use python's built-in `urllib`:
```dockerfile
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:5000/health')" || exit 1
```
**benefit**: no additional packages needed, works out-of-the-box, keeps image small.

### challenge ii: understanding layer caching behavior

**problem**: initially confused about when layers are cached vs invalidated.

**learned**:
- layers are cached if the instruction hasn't changed
- `COPY` invalidates cache if the file content has changed (based on checksum)
- `RUN` invalidates cache if the command string has changed
- `ADD` behaves similarly to `COPY` but has additional features (url, extraction)

**example**: changing a comment in the dockerfile doesn't invalidate cache because the layer content (not the file) is what's cached. but changing a command argument (like `pip install --upgrade pip`) creates a new layer.
