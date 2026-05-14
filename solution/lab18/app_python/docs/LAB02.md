# Lab 02 — Dockerized Python Application

## 1. Docker Best Practices Applied

### 1. Non-root User

```dockerfile
RUN apk add --no-cache shadow  \
    && groupadd -r appgroup \
    && useradd -r -g appgroup -m appuser
USER appuser
```

**Why it matters:**
Running containers as root increases the blast radius of a potential exploit.
By creating and switching to a dedicated non-root user, the container follows the **principle of least privilege**, reducing security risks if the application is compromised.

---

### 2. Minimal Base Image (Alpine)

```dockerfile
FROM python:3.14.2-alpine3.23
```

**Why it matters:**
Alpine images are significantly smaller than Debian-based images, which:

* Reduces attack surface
* Decreases image size
* Improves pull and startup times

---

### 3. Layer Caching Optimization

```dockerfile
COPY requirements.txt ./requirements.txt
RUN pip install -r requirements.txt
```

**Why it matters:**
Dependencies change less frequently than application code.
By copying `requirements.txt` before the source code, Docker can reuse cached layers and avoid reinstalling dependencies on every build, significantly speeding up rebuilds.

---

### 4. `.dockerignore` Usage

```dockerignore
__pycache__/
*.py[cod]
venv/
tests/
.env
.git/
docs/
```

**Why it matters:**
Excluding unnecessary files:

* Reduces build context size
* Speeds up Docker builds
* Prevents secrets and local artifacts from being copied into the image
* Keeps the final image clean and deterministic

---

### 5. No Cache Package Installation

```dockerfile
RUN apk add --no-cache shadow
```

**Why it matters:**
Using `--no-cache` prevents package index files from being stored in the image, keeping layers smaller and reducing image bloat.
---
### 7. Strict versions of base image
```dockerfile
FROM python:3.14.2-alpine3.23
```

**Why it matters:**
Ensure stability without unexpected bugs, tailored with the newer version of python or alpine

---
### 8. Environment variables documented in the dockerfile, according official styleguide 
```dockerfile
# OPTIONAL: PORT {5000}, HOST {0.0.0.0}, DEBUG {false}
```
**Why it matters:**
Person, that will use that image do not required to search in the docs how to configure the program. Only `Dokerfile` will enough to know valuable run config 
---
## 2. Image Information & Decisions

### Base Image Selection

**Chosen image:** `python:3.14.2-alpine3.23`

**Justification:**

* Python 3.14 ensures forward compatibility with modern language features
* Alpine 3.23 provides a lightweight and secure Linux base
* Official Python image guarantees consistent builds and security updates

---

### Final Image Size

**Final image size:** 33.3 MB

**Assessment:**
For a Python web application with dependencies installed, this is a compact and efficient result. Alpine significantly reduces size compared to Debian-based images (~150–200 MB).

---

### Layer Structure

1. Base Python runtime
2. OS user and group creation
3. Dependency installation
4. Application source code
5. Runtime configuration

This structure maximizes cache reuse while keeping runtime layers minimal.

---

### Optimization Choices

* Alpine base image
* Single responsibility per layer
* Dependency caching
* `.dockerignore` exclusions
* No package manager cache retention

---

## 3. Build & Run Process

### Build Command

```ps
docker build -t devops-i-lobazov:0.1.0 .
```

### Build Output

```
[+] Building 22.2s (12/12) FINISHED                                                                     docker:desktop-linux
 => [internal] load build definition from Dockerfile                                                                    0.0s
 => => transferring dockerfile: 460B                                                                                    0.0s
 => [internal] load metadata for docker.io/library/python:3.14.2-alpine3.23                                             1.3s
 => [internal] load .dockerignore                                                                                       0.0s
 => => transferring context: 252B                                                                                       0.0s
 => [1/7] FROM docker.io/library/python:3.14.2-alpine3.23@sha256:31da4cb527055e4e3d7e9e006dffe9329f84ebea79eaca0a1f1c2  0.1s
 => => resolve docker.io/library/python:3.14.2-alpine3.23@sha256:31da4cb527055e4e3d7e9e006dffe9329f84ebea79eaca0a1f1c2  0.1s
 => [internal] load build context                                                                                       0.0s
 => => transferring context: 4.69kB                                                                                     0.0s
 => CACHED [2/7] RUN apk add --no-cache shadow      && groupadd -r appgroup     && useradd -r -g appgroup -m appuser    0.0s
 => CACHED [3/7] WORKDIR /app                                                                                           0.0s
 => [4/7] RUN pip install --upgrade pip>=26.0                                                                           7.2s
 => [5/7] COPY requirements.txt ./requirements.txt                                                                      0.1s
 => [6/7] RUN pip install -r requirements.txt                                                                          10.8s
 => [7/7] COPY . .                                                                                                      0.1s
 => exporting to image                                                                                                  2.3s
 => => exporting layers                                                                                                 1.1s
 => => exporting manifest sha256:5c7770b74f0d3045e4c2d2ee3ba85f258b4c6378c9d0a6121a66044639ab9c64                       0.0s
 => => exporting config sha256:42f026b344436bd5f4472e9d0b7a1814d01c3626aeb9603131299056e200df1d                         0.0s
 => => exporting attestation manifest sha256:8c73b05255d8bef7de7d2ce034512ad8a858d234899530bb411fdcbc08b042f7           0.0s
 => => exporting manifest list sha256:b9c9e9fbc2bd31279d286f764d5ba85b786f44956d9285356ab5c99c4128ae13                  0.0s
 => => naming to docker.io/library/devops-i-lobazov:0.1.0                                                               0.0s
 => => unpacking to docker.io/library/devops-i-lobazov:0.1.0                                                            1.1s

What's next:
    View a summary of image vulnerabilities and recommendations → docker scout quickview
```

---

### Ensure same behavior as ran on host
App output
```bash
> docker run -p 5000:5000 devops-i-lobazov:0.1.0
INFO:     Started server process [1]
INFO:     Waiting for application startup.
2026-02-03 21:06:02,878 - __main__ - INFO - Starting up...
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:5000 (Press CTRL+C to quit)
INFO:     172.17.0.1:44890 - "GET /health HTTP/1.1" 200 OK
INFO:     172.17.0.1:39328 - "GET /health HTTP/1.1" 200 OK
INFO:     172.17.0.1:39048 - "GET / HTTP/1.1" 200 OK
```
`curl` call
```ps
PS C:\Users\xzsay\PycharmProjects\DevOps-Core-Course> (curl -UseBasicParsing http://localhost:5000/health).Content | ConvertFrom-Json | ConvertTo-Json
{
    "status":  "healthy",
    "timestamp":  "2026-02-03 21:07:04",
    "uptime_seconds":  61
}
PS C:\Users\xzsay\PycharmProjects\DevOps-Core-Course> (curl -UseBasicParsing http://localhost:5000).Content | ConvertFrom-Json | ConvertTo-Json
{
    "service":  {
                    "name":  "devops-info-service",
                    "version":  "1.0.0",
                    "description":  "DevOps course info service",
                    "framework":  "FastAPI"
                },
    "system":  {
                   "hostname":  "03fe2b761477",
                   "platform":  "Linux",
                   "platform_version":  "6.6.87.2-microsoft-standard-WSL2",
                   "architecture":  "x86_64",
                   "cpu_count":  12,
                   "python_version":  "3.14.2"
               },
    "runtime":  {
                    "uptime_seconds":  73,
                    "uptime_human":  "0 hours, 1 minutes",
                    "current_time":  "2026-02-03 21:07:15",
                    "timezone":  ""
                },
    "request":  {
                    "client_ip":  "172.17.0.1",
                    "user_agent":  "Mozilla/5.0 (Windows NT; Windows NT 10.0; en-US) WindowsPowerShell/5.1.26100.7462",
                    "method":  "GET",
                    "path":  "/"
                },
    "endpoints":  [
                      {
                          "path":  "/openapi.json",
                          "method":  "HEAD",
                          "description":  ""
                      },
                      {
                          "path":  "/openapi.json",
                          "method":  "GET",
                          "description":  ""
                      },
                      {
                          "path":  "/docs",
                          "method":  "HEAD",
                          "description":  ""
                      },
                      {
                          "path":  "/docs",
                          "method":  "GET",
                          "description":  ""
                      },
                      {
                          "path":  "/docs/oauth2-redirect",
                          "method":  "HEAD",
                          "description":  ""
                      },
                      {
                          "path":  "/docs/oauth2-redirect",
                          "method":  "GET",
                          "description":  ""
                      },
                      {
                          "path":  "/redoc",
                          "method":  "HEAD",
                          "description":  ""
                      },
                      {
                          "path":  "/redoc",
                          "method":  "GET",
                          "description":  ""
                      },
                      {
                          "path":  "/",
                          "method":  "GET",
                          "description":  "System and service info about the server"
                      },
                      {
                          "path":  "/health",
                          "method":  "GET",
                          "description":  "Service health-chek"
                      }
                  ]
}
```

---

### Docker Hub Repository
`Powershell` history:
```ps
PS ~\PycharmProjects\DevOps-Core-Course\solution\app_python> docker login
Authenticating with existing credentials... [Username: xrixis]

i Info → To login with a different account, run 'docker logout' followed by 'docker login'


Login Succeeded
PS ~\PycharmProjects\DevOps-Core-Course\solution\app_python> docker tag devops-i-lobazov:0.1.0 xrixis/devops-i-lobazov:0.1.0
PS ~\PycharmProjects\DevOps-Core-Course\solution\app_python> docker tag devops-i-lobazov:0.1.0 xrixis/devops-i-lobazov:latest
PS ~\PycharmProjects\DevOps-Core-Course\solution\app_python> docker push xrixis/devops-i-lobazov:0.1.0
The push refers to repository [docker.io/xrixis/devops-i-lobazov]
472bf656f1d9: Waiting
a0bd95b0bd18: Waiting
bd701e501660: Waiting
871c57f4ba4f: Waiting
472bf656f1d9: Pushed
a0bd95b0bd18: Pushed
bd701e501660: Pushed
871c57f4ba4f: Pushed
589002ba0eae: Pushed
4d526f9d3e24: Pushing [==================>                                ]  2.097MB/5.604MB
ff83b2b57ff1: Pushed
c636d76d1d07: Pushed
4d526f9d3e24: Pushed
1de815c6e5e1: Pushed
6a6e0b164786: Pushed
0.1.0: digest: sha256:b9c9e9fbc2bd31279d286f764d5ba85b786f44956d9285356ab5c99c4128ae13 size: 856
```
To obtain the image run 
```bash
docker pull xrixis/devops-i-lobazov:0.1.0
```
Also, available at **[https://hub.docker.com/repository/docker/xrixis/devops-i-lobazov/](https://hub.docker.com/repository/docker/xrixis/devops-i-lobazov/)**

---

## 4. Technical Analysis

### Why does your Dockerfile work the way it does?
    
It is technological evolved solution for running applications isolated. 
OS isolate only the main memory for each process, but for other resources here is mutual access 
(files, ports, dependencies). Running separate OS foreach process - too wasteful in some scenarios, so Docker resolve 
conflict and vulnerabilities caused by resources sharing (isolate them for containers), keeping execution on the same 
machine

---

### Impact of Layer Order Changes

If `COPY . .` were placed before installing dependencies:

* Any source code change would invalidate the cache
* Dependencies would reinstall on every build
* Build times would increase significantly

---

### Security Considerations

* Non-root execution
* Minimal OS packages (Alpine)
* No secrets baked into image

---

### Role of `.dockerignore`

`.dockerignore` prevents:

* Accidental inclusion of secrets (`.env`)
* Large unnecessary directories (`.git`, `tests`)
* Local artifacts affecting reproducibility

This results in faster, safer, and more predictable builds.

---

## 5. Challenges & Solutions

### Challenge: Alpine Missing User Management Tools

**Issue:** `useradd` not available by default in alpine

**Solution:** Imported `shadow` package explicitly

---

### Challenge: Port configured via environment variable

**Issue:** `EXPOSE` directive, designed for documentation could not be properly filled, because depend on runtime config 
```Dockerfile
EXPOSE 5000
```
**Solution:** Ignore the problem. Advanced user, that will be configuring the running container via env should get the 
documented and actual port missmatch, but directive `EXPOSE 5000` will be convenient for default run via GUI in 
Docker Desktop  

---
### Key Learnings

* `.dockerignore` is just as important as `.gitignore`
* Security best practices are easy to apply early

---
