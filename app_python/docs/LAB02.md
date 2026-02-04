# Lab 2 — Docker Containerization

## 1) Docker Best Practices Applied
- **Pinned base image**: `FROM python:3.13-slim` for a current, minimal runtime with security updates and predictable behavior.
- **Layer caching friendly order**: copy `requirements.txt` before app code so dependency installs stay cached when code changes.
- **Minimal copy**: only `requirements.txt` and `app.py` are added; docs/tests stay out of the image.
- **Non-root user**: create `appuser` (`groupadd/useradd`) and run with `USER appuser` to reduce blast radius.
- **Runtime hygiene**: `PYTHONDONTWRITEBYTECODE=1` and `PYTHONUNBUFFERED=1` to keep the image clean and logs unbuffered.
- **Slim install**: `pip install --no-cache-dir` to avoid leftover wheels, keeping layers smaller.
- **.dockerignore**: excludes VCS, envs, caches, docs, and tests to shrink build context.
- **Documented port & command**: `EXPOSE 5000` and `CMD ["python", "app.py"]` so the container behavior matches local runs.

Snippet (core Dockerfile):
```Dockerfile
FROM python:3.13-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app
RUN groupadd --system app && useradd --system --gid app --create-home appuser
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && pip install --no-cache-dir -r requirements.txt
COPY app.py .
USER appuser
EXPOSE 5000
CMD ["python", "app.py"]
```

## 2) Image Information & Decisions
- **Base image choice**: `python:3.13-slim` balances security updates, predictable glibc-based runtime, and smaller footprint than the full image.
- **Final image size**: `142MB` (`docker images devops-info:lab02`); acceptable for a small API with only FastAPI/uvicorn installed.
- **Layer structure**: OS base → workdir/user creation → `requirements.txt` copy → dependency install → `app.py` copy → switch user → expose/cmd. Code changes invalidate only the final layer, keeping rebuilds fast.
- **Optimization choices**: slim base, no pip cache, minimal copy set, and .dockerignore to avoid sending unused files.

## 3) Build & Run Process
Build:
```bash
19:46 $  docker build -t devops-info:lab02 .
[+] Building 3.3s (12/12) FINISHED                                                                docker:default
 => [internal] load build definition from Dockerfile                                                        0.0s
 => => transferring dockerfile: 411B                                                                        0.0s
 => [internal] load metadata for docker.io/library/python:3.13-slim                                         3.2s
 => [auth] library/python:pull token for registry-1.docker.io                                               0.0s
 => [internal] load .dockerignore                                                                           0.0s
 => => transferring context: 163B                                                                           0.0s
 => [1/6] FROM docker.io/library/python:3.13-slim@sha256:2b9c9803c6a287cafa0a8c917211dddd23dcd2016f049690e  0.0s
 => [internal] load build context                                                                           0.0s
 => => transferring context: 2.81kB                                                                         0.0s
 => CACHED [2/6] WORKDIR /app                                                                               0.0s
 => CACHED [3/6] RUN groupadd --system app &&     useradd --system --gid app --create-home appuser          0.0s
 => CACHED [4/6] COPY requirements.txt .                                                                    0.0s
 => CACHED [5/6] RUN pip install --no-cache-dir --upgrade pip &&     pip install --no-cache-dir -r require  0.0s
 => [6/6] COPY app.py .                                                                                     0.0s
 => exporting to image                                                                                      0.0s
 => => exporting layers                                                                                     0.0s
 => => writing image sha256:4b309f8921e56e70c45e4d24ca3b9cfe92e7b89c5ca3a1593f0986924b2674ae                0.0s
 => => naming to docker.io/library/devops-info:lab02        
```

Run:
```bash
19:47 $ docker run -d -p 5000:5000 --name devops-info -e HOST=0.0.0.0 -e PORT=5000 devops-info:lab02
86ac02a770a5466ce77b94596ab36f8991d8fae4f8e912255216faf7f4e05d57

19:47 $ docker ps
CONTAINER ID   IMAGE               COMMAND           CREATED          STATUS          PORTS                    NAMES
86ac02a770a5   devops-info:lab02   "python app.py"   13 seconds ago   Up 12 seconds   0.0.0.0:5000->5000/tcp   devops-info
```

Endpoint test:
```bash
19:48 $ curl http://localhost:5000/health
{"status":"healthy","timestamp":"2026-02-04T16:48:51.541537+00:00","uptime_seconds":54}
```

Image info:
```bash
19:48 $ docker images devops-info:lab02
REPOSITORY    TAG       IMAGE ID       CREATED         SIZE
devops-info   lab02     4b309f8921e5   2 minutes ago   142MB
```

Pushing to Docker Hub:
```bash
19:49 $ docker tag devops-info:lab02 ebortsov/devops-info:lab02

19:49 $ docker push ebortsov/devops-info:lab02
The push refers to repository [docker.io/ebortsov/devops-info]
368ec4d8759e: Pushed 
a70e6e3c043d: Layer already exists 
1209870fb6c4: Layer already exists 
61d4144d89dc: Layer already exists 
7be6921254fd: Layer already exists 
6f3d061c2e62: Layer already exists 
1a619cfa942c: Layer already exists 
c07c86e6f1e8: Layer already exists 
a8ff6f8cbdfd: Layer already exists 
lab02: digest: sha256:912d1ae2281d967366345cb8619c0ac325392d52e636b44e122dca83040fc6db size: 2199
```

Docker Hub link: `ebortsov/devops-info:lab02` at https://hub.docker.com/r/ebortsov/devops-info.

Tagging strategy:
- `lab02` for lab deliverable
- `latest` for current


Pulling from Docker Hub:
```bash
19:54 $ docker pull ebortsov/devops-info:lab02
lab02: Pulling from ebortsov/devops-info
Digest: sha256:912d1ae2281d967366345cb8619c0ac325392d52e636b44e122dca83040fc6db
Status: Downloaded newer image for ebortsov/devops-info:lab02
docker.io/ebortsov/devops-info:lab02
```

## 4) Technical Analysis
- **Why it works**: the slim base already includes Python and pip, so installing `fastapi`/`uvicorn` on top is straightforward. Environment vars keep the image clean, and the CMD mirrors the local `python app.py` run.
- **Layer order impact**: changing app code only rebuilds the final copy layer; moving `COPY app.py` earlier would force dependency re-installs on every code change, slowing builds.
- **Security considerations**: pinned base image version, non-root runtime user, minimal packages (no compilers), and no writable bytecode files.
- **.dockerignore effect**: smaller build context → faster transfers to the daemon and fewer chances of leaking secrets/dev artifacts into the image.

## 5) Challenges & Solutions
- I did not face any difficult challenges while implementing the lab.
