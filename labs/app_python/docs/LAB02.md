## Docker Practices ##

#### 1. Non-root user ####

Running commands as non-root users assures that user will not do harmful operations on the computer, and intruder will not get root rights through container.

```bash
RUN groupadd -r appuser && useradd -r -g appuser appuser
```

#### 2. Specific base image version ####

This practice need for stability and reproducibility of the build.

```bash
FROM python:3.12-slim
```

#### 3. Necessary files copying ####

Getting rid of extra data will make a container more lightweight.

```bash
COPY requirements.txt .

COPY --chown=appuser:appuser app.py .
COPY --chown=appuser:appuser requirements.txt .
COPY --chown=appuser:appuser tests/ tests/
```

#### 4. Proper layer ordering ####

Proper layer ordering will improve caching and reduce build time.

```bash
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY --chown=appuser:appuser app.py .
COPY --chown=appuser:appuser requirements.txt .
COPY --chown=appuser:appuser tests/ tests/
```

#### 5. .dockerignore ####

.dockerignore needed for redcing build time and controlling build context.

```bash
# Git
.git
.gitignore

# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
env/
venv/
.env
.venv

# Virtual environments
ENV/
env.bak/
venv.bak/

# IDE
.vscode/
.idea/
*.swp
*.swo

# Docker
Dockerfile
docker-compose.yml
docker-compose*.yml

# Logs
*.log
logs/

# Docs
docs/screenshots/*.png

```

## Image ##

I chose python:3.12-slim because it was lowest version by requirements and I prefer lower requirements so more people could launch the program.

Image size is 215.19 Mb. I think it is fine, however I suppose it could take less space.

It is good practice to copy requirements.txt first to install dependencies so they will be cached, and only then copy other files.

Finally, I didn't copy any docs and system file to improve build time.

## Build & Run ##

#### Build: ####

```bash
[+] Building 1.6s (14/14) FINISHED                                                                                                         docker:desktop-linux
 => [internal] load build definition from Dockerfile                                                                                                       0.0s
 => => transferring dockerfile: 458B                                                                                                                       0.0s 
 => [internal] load metadata for docker.io/library/python:3.12-slim                                                                                        1.1s 
 => [auth] library/python:pull token for registry-1.docker.io                                                                                              0.0s 
 => [internal] load .dockerignore                                                                                                                          0.0s
 => => transferring context: 374B                                                                                                                          0.0s 
 => [1/8] FROM docker.io/library/python:3.12-slim@sha256:5e2dbd4bbdd9c0e67412aea9463906f74a22c60f89eb7b5bbb7d45b66a2b68a6                                  0.0s 
 => => resolve docker.io/library/python:3.12-slim@sha256:5e2dbd4bbdd9c0e67412aea9463906f74a22c60f89eb7b5bbb7d45b66a2b68a6                                  0.0s 
 => [internal] load build context                                                                                                                          0.0s 
 => => transferring context: 122B                                                                                                                          0.0s
 => CACHED [2/8] RUN groupadd -r appuser && useradd -r -g appuser appuser                                                                                  0.0s 
 => CACHED [3/8] WORKDIR /app                                                                                                                              0.0s 
 => CACHED [4/8] COPY requirements.txt .                                                                                                                   0.0s 
 => CACHED [5/8] RUN pip install --no-cache-dir -r requirements.txt                                                                                        0.0s 
 => CACHED [6/8] COPY --chown=appuser:appuser app.py .                                                                                                     0.0s 
 => CACHED [7/8] COPY --chown=appuser:appuser requirements.txt .                                                                                           0.0s 
 => CACHED [8/8] COPY --chown=appuser:appuser tests/ tests/                                                                                                0.0s 
 => => exporting layers                                                                                                                                    0.0s 
 => => exporting manifest sha256:9285a6c6031b057a33819a013800e65ca5b61c1e9e70692b985e746be9d38c48                                                          0.0s 
 => => exporting config sha256:9d8e608d2633c3aa97c30ba74301ab9a1b77342e8acc14a0c28e2689e830a95f                                                            0.0s 
 => => exporting attestation manifest sha256:a5242d192d7e2367b5c375b7c57071edbe9b9ba17b74ebbc2314dd262744f7e5                                              0.0s 
 => => exporting manifest list sha256:05eb1953f23f24e715476184648636f51ff1dd63904e2bec231a455680a34f3e                                                     0.0s 
 => => naming to docker.io/library/simple-app:latest                                                                                                       0.0s 
 => => unpacking to docker.io/library/simple-app:latest                                                                                                    0.3s 

View build details: docker-desktop://dashboard/build/desktop-linux/desktop-linux/kgpcohcuglsmmgb7ta3l3cbb6
```

#### Container running ####

```bash
CONTAINER ID   IMAGE          COMMAND                  CREATED              STATUS                          PORTS     NAMES
03f787632e07   simple-app     "python app.py --hos…"   24 seconds ago       Up 23 seconds                flamboyant_villani
```

#### Image push ####

```bash
The push refers to repository [docker.io/thevex/simple-app]
6a1c31822903: Waiting
671677b67e76: Waiting
671677b67e76: Pushed
3d6ef8a4ce0a: Pushed
d2f59ad9a22a: Pushed
85cf7739df5e: Pushed
dd2b2f57eca4: Pushed
a2558eb4e3f9: Pushed
14547ac34357: Pushed
9ab711bc1d8c: Pushed
latest: digest: sha256:05eb1953f23f24e715476184648636f51ff1dd63904e2bec231a455680a34f3e size: 856
```

#### Endpoints output ####

```bash
StatusCode        : 200     
StatusDescription : OK
Content           : {"service":{"name":"devops-info-service","version":"1.0.0","description":"DevOps course info service","framewor
                    k":"FastAPI"},"system":{"hostname":"b0d9af6f94bc","platform":"Linux","platform_version":"...
RawContent        : HTTP/1.1 200 OK
                    Content-Length: 869
                    Content-Type: application/json
                    Date: Sun, 01 Feb 2026 17:34:12 GMT
                    Server: uvicorn

                    {"service":{"name":"devops-info-service","version":"1.0.0","description":"...
Forms             : {}
Headers           : {[Content-Length, 869], [Content-Type, application/json], [Date, Sun, 01 Feb 2026 17:34:12 GMT], [Server, uvico
                    rn]}
Images            : {}
InputFields       : {}
Links             : {}
ParsedHtml        : mshtml.HTMLDocumentClass
RawContentLength  : 869
```

```bash
StatusCode        : 200
StatusDescription : OK
Content           : {"status":"healthy","timestamp":"2026-02-01T17:34:21.303777","uptime_seconds":117}
RawContent        : HTTP/1.1 200 OK
                    Content-Length: 82
                    Content-Type: application/json
                    Date: Sun, 01 Feb 2026 17:34:21 GMT
                    Server: uvicorn

                    {"status":"healthy","timestamp":"2026-02-01T17:34:21.303777","uptime_second...
Forms             : {}
Headers           : {[Content-Length, 82], [Content-Type, application/json], [Date, Sun, 01 Feb 2026 17:34:21 GMT], [Server, uvicor
                    n]}
Images            : {}
InputFields       : {}
Links             : {}
ParsedHtml        : mshtml.HTMLDocumentClass
RawContentLength  : 82
```

#### Docker Hub Repository ####

Link: https://hub.docker.com/repository/docker/thevex/simple-app/general

## Technical analysis ##

Dockerfile work the way it does because it is written syntactically and semantically correct :D

If I changed layer order, build could start to spend more time, and after completion it might take more space because of absence of optimized caching.

I build as non-root user and didn't include system files inside a build.

.dockerignore not including extra files into my build so it is faster and more secured after completion.

## Challenges & Solutions ##

There were no actual challenges.

I reminded myself how to work with Docker.
