# Lab 02 - Docker Containerization (Python)

## Docker Best Practices Applied

- Specific base image version: `python:3.13-slim`.
Why it matters: pinning to a specific version reduces unexpected changes and keeps images reproducible.

- Non-root user: created `app` system user and switched to `USER app`.
Why it matters: lowers blast radius if the container is compromised and avoids running as root.

- Layer caching: copied `requirements.txt` and installed dependencies before copying `app.py`.
Why it matters: dependency layers are reused across rebuilds when only source code changes.

- Minimal copy: only `requirements.txt` and `app.py` are copied into the image.
Why it matters: smaller image and reduced attack surface.

- `.dockerignore`: excluded venvs, caches, tests, docs, git metadata.
Why it matters: smaller build context and faster builds.

Dockerfile snippets used:

```Dockerfile
FROM python:3.13-slim

WORKDIR /app

RUN groupadd --system app && useradd --system --gid app --home /app --shell /usr/sbin/nologin app

COPY --chown=app:app requirements.txt ./
RUN python -m pip install --no-cache-dir -r requirements.txt

COPY --chown=app:app app.py ./

USER app

EXPOSE 5000

CMD ["python", "app.py"]
```

## Image Information & Decisions

- Base image: `python:3.13-slim`.
Reason: slim keeps image size lower than full images while remaining compatible with common Python wheels.

- Final image size: `149MB`.
Assessment: acceptable for a Python + Flask runtime image. Further reductions are possible with slimmer dependency sets.

- Layer structure explanation:
Base image, working directory, user creation, dependency install, application copy, user switch, runtime command. This order maximizes cache reuse and keeps runtime layers minimal.

- Optimization choices:
`--no-cache-dir` for pip, `.dockerignore` to reduce context size, and only copying runtime files.

## Build & Run Process

Docker build output:

```
#0 building with "orbstack" instance using docker driver

#1 [internal] load build definition from Dockerfile
#1 transferring dockerfile: 67B 0.0s
#1 transferring dockerfile: 449B 0.0s done
#1 DONE 0.2s

#2 [internal] load metadata for docker.io/library/python:3.13-slim
#2 ...

#3 [auth] library/python:pull token for registry-1.docker.io
#3 DONE 0.0s

#2 [internal] load metadata for docker.io/library/python:3.13-slim
#2 DONE 2.7s

#4 [internal] load .dockerignore
#4 transferring context: 207B done
#4 DONE 0.1s

#5 [internal] load build context
#5 DONE 0.0s

#6 [1/6] FROM docker.io/library/python:3.13-slim@sha256:2b9c9803c6a287cafa0a8c917211dddd23dcd2016f049690ee5219f5d3f1636e
#6 resolve docker.io/library/python:3.13-slim@sha256:2b9c9803c6a287cafa0a8c917211dddd23dcd2016f049690ee5219f5d3f1636e
#6 ...

#5 [internal] load build context
#5 transferring context: 8.03kB done
#5 DONE 0.1s

#6 [1/6] FROM docker.io/library/python:3.13-slim@sha256:2b9c9803c6a287cafa0a8c917211dddd23dcd2016f049690ee5219f5d3f1636e
#6 resolve docker.io/library/python:3.13-slim@sha256:2b9c9803c6a287cafa0a8c917211dddd23dcd2016f049690ee5219f5d3f1636e 0.0s done
#6 sha256:ba184f3e0dc36fd0d4e1e0dd9db9686ec55cc1587c2604fe036c475365f16b9f 5.54kB / 5.54kB done
#6 sha256:fe9a90620d58e0d94bd1a536412e60ddaff85c045f729197536cb8a382e1c5a2 0B / 1.27MB 0.1s
#6 sha256:97fc85b49690b12f13f53067a3190e231790ff42832ff5f39e97042fc4d4ede6 0B / 250B 0.1s
#6 sha256:2b9c9803c6a287cafa0a8c917211dddd23dcd2016f049690ee5219f5d3f1636e 10.37kB / 10.37kB done
#6 sha256:ad85520ecc7e2ffa676441417d0a4731dbb9084909d93ef2028054ad019fe595 1.75kB / 1.75kB done
#6 sha256:a6866fe8c3d2436d6a24f7d829aca8349726c5c198725f763a40e2e4263a53e6 0B / 11.72MB 0.3s
#6 sha256:fe9a90620d58e0d94bd1a536412e60ddaff85c045f729197536cb8a382e1c5a2 1.27MB / 1.27MB 0.6s done
#6 extracting sha256:fe9a90620d58e0d94bd1a536412e60ddaff85c045f729197536cb8a382e1c5a2
#6 sha256:97fc85b49690b12f13f53067a3190e231790ff42832ff5f39e97042fc4d4ede6 250B / 250B 0.8s done
#6 extracting sha256:fe9a90620d58e0d94bd1a536412e60ddaff85c045f729197536cb8a382e1c5a2 0.3s done
#6 sha256:a6866fe8c3d2436d6a24f7d829aca8349726c5c198725f763a40e2e4263a53e6 2.10MB / 11.72MB 1.2s
#6 sha256:a6866fe8c3d2436d6a24f7d829aca8349726c5c198725f763a40e2e4263a53e6 4.19MB / 11.72MB 1.4s
#6 sha256:a6866fe8c3d2436d6a24f7d829aca8349726c5c198725f763a40e2e4263a53e6 5.24MB / 11.72MB 1.5s
#6 sha256:a6866fe8c3d2436d6a24f7d829aca8349726c5c198725f763a40e2e4263a53e6 7.34MB / 11.72MB 1.7s
#6 sha256:a6866fe8c3d2436d6a24f7d829aca8349726c5c198725f763a40e2e4263a53e6 10.49MB / 11.72MB 1.9s
#6 sha256:a6866fe8c3d2436d6a24f7d829aca8349726c5c198725f763a40e2e4263a53e6 11.72MB / 11.72MB 2.0s
#6 sha256:a6866fe8c3d2436d6a24f7d829aca8349726c5c198725f763a40e2e4263a53e6 11.72MB / 11.72MB 2.0s done
#6 extracting sha256:a6866fe8c3d2436d6a24f7d829aca8349726c5c198725f763a40e2e4263a53e6 0.1s
#6 extracting sha256:a6866fe8c3d2436d6a24f7d829aca8349726c5c198725f763a40e2e4263a53e6 1.5s done
#6 extracting sha256:97fc85b49690b12f13f53067a3190e231790ff42832ff5f39e97042fc4d4ede6
#6 extracting sha256:97fc85b49690b12f13f53067a3190e231790ff42832ff5f39e97042fc4d4ede6 done
#6 DONE 3.9s

#7 [2/6] WORKDIR /app
#7 DONE 0.5s

#8 [3/6] RUN groupadd --system app && useradd --system --gid app --home /app --shell /usr/sbin/nologin app
#8 DONE 0.5s

#9 [4/6] COPY --chown=app:app requirements.txt ./
#9 DONE 0.1s

#10 [5/6] RUN python -m pip install --no-cache-dir -r requirements.txt
#10 1.908 Collecting Flask==3.1.0 (from -r requirements.txt (line 1))
#10 2.319   Downloading flask-3.1.0-py3-none-any.whl.metadata (2.7 kB)
#10 2.474 Collecting Werkzeug==3.1.3 (from -r requirements.txt (line 2))
#10 2.545   Downloading werkzeug-3.1.3-py3-none-any.whl.metadata (3.7 kB)
#10 2.633 Collecting gunicorn==23.0.0 (from -r requirements.txt (line 3))
#10 2.707   Downloading gunicorn-23.0.0-py3-none-any.whl.metadata (4.4 kB)
#10 2.805 Collecting Jinja2>=3.1.2 (from Flask==3.1.0->-r requirements.txt (line 1))
#10 2.873   Downloading jinja2-3.1.6-py3-none-any.whl.metadata (2.9 kB)
#10 2.955 Collecting itsdangerous>=2.2 (from Flask==3.1.0->-r requirements.txt (line 1))
#10 3.022   Downloading itsdangerous-2.2.0-py3-none-any.whl.metadata (1.9 kB)
#10 3.106 Collecting click>=8.1.3 (from Flask==3.1.0->-r requirements.txt (line 1))
#10 3.174   Downloading click-8.3.1-py3-none-any.whl.metadata (2.6 kB)
#10 3.258 Collecting blinker>=1.9 (from Flask==3.1.0->-r requirements.txt (line 1))
#10 3.322   Downloading blinker-1.9.0-py3-none-any.whl.metadata (1.6 kB)
#10 3.500 Collecting MarkupSafe>=2.1.1 (from Werkzeug==3.1.3->-r requirements.txt (line 2))
#10 3.566   Downloading markupsafe-3.0.3-cp313-cp313-manylinux2014_aarch64.manylinux_2_17_aarch64.manylinux_2_28_aarch64.whl.metadata (2.7 kB)
#10 3.654 Collecting packaging (from gunicorn==23.0.0->-r requirements.txt (line 3))
#10 3.725   Downloading packaging-26.0-py3-none-any.whl.metadata (3.3 kB)
#10 3.806 Downloading flask-3.1.0-py3-none-any.whl (102 kB)
#10 4.036 Downloading werkzeug-3.1.3-py3-none-any.whl (224 kB)
#10 4.169 Downloading gunicorn-23.0.0-py3-none-any.whl (85 kB)
#10 4.244 Downloading blinker-1.9.0-py3-none-any.whl (8.5 kB)
#10 4.311 Downloading click-8.3.1-py3-none-any.whl (108 kB)
#10 4.389 Downloading itsdangerous-2.2.0-py3-none-any.whl (16 kB)
#10 4.458 Downloading jinja2-3.1.6-py3-none-any.whl (134 kB)
#10 4.544 Downloading markupsafe-3.0.3-cp313-cp313-manylinux2014_aarch64.manylinux_2_17_aarch64.manylinux_2_28_aarch64.whl (24 kB)
#10 4.613 Downloading packaging-26.0-py3-none-any.whl (74 kB)
#10 4.651 Installing collected packages: packaging, MarkupSafe, itsdangerous, click, blinker, Werkzeug, Jinja2, gunicorn, Flask
#10 5.441 
#10 5.447 Successfully installed Flask-3.1.0 Jinja2-3.1.6 MarkupSafe-3.0.3 Werkzeug-3.1.3 blinker-1.9.0 click-8.3.1 gunicorn-23.0.0 itsdangerous-2.2.0 packaging-26.0
#10 5.448 WARNING: Running pip as the 'root' user can result in broken permissions and conflicting behaviour with the system package manager, possibly rendering your system unusable. It is recommended to use a virtual environment instead: https://pip.pypa.io/warnings/venv. Use the --root-user-action option if you know what you are doing and want to suppress this warning.
#10 5.851 
#10 5.851 [notice] A new release of pip is available: 25.3 -> 26.0
#10 5.851 [notice] To update, run: pip install --upgrade pip
#10 DONE 6.2s

#11 [6/6] COPY --chown=app:app app.py ./
#11 DONE 0.1s

#12 exporting to image
#12 exporting layers 0.1s done
#12 writing image sha256:b1d2653e70b76a6982ac3f779eb5fec093a85b413622757772c1b4cfee25976c done
#12 naming to docker.io/library/devops-info-service-python:lab02 0.0s done
#12 DONE 0.2s

View build details: docker-desktop://dashboard/build/orbstack/orbstack/8y7rhyhn2eyjq4t7nbrcf6d88
```

Docker run output:

```
f9b54b4a72e2f8eedabc4e17646a81de1d108f5c141862d39f6322430a01f84d
```

Container running:

```
CONTAINER ID   IMAGE                              COMMAND           CREATED         STATUS         PORTS                                       NAMES
f9b54b4a72e2   devops-info-service-python:lab02   "python app.py"   3 seconds ago   Up 2 seconds   0.0.0.0:5000->5000/tcp, :::5000->5000/tcp   devops-info-service-python
```

Endpoint test output:

```
{"endpoints":[{"description":"Service information","method":"GET","path":"/"},{"description":"Health check","method":"GET","path":"/health"}],"request":{"client_ip":"192.168.215.1","method":"GET","path":"/","user_agent":"curl/8.7.1"},"runtime":{"current_time":"2026-02-04T11:30:24.730816+00:00","timezone":"UTC","uptime_human":"0 hours, 0 minutes","uptime_seconds":5},"service":{"description":"DevOps course info service","framework":"Flask","name":"devops-info-service","version":"1.0.0"},"system":{"architecture":"aarch64","cpu_count":11,"hostname":"f9b54b4a72e2","platform":"Linux","platform_version":"#104 SMP Mon Mar 17 06:15:48 UTC 2025","python_version":"3.13.11"}}
```

```
{"status":"healthy","timestamp":"2026-02-04T11:30:29.998403+00:00","uptime_seconds":10}
```

Image size output:

```
REPOSITORY                   TAG       IMAGE ID       CREATED          SIZE
devops-info-service-python   lab02     b1d2653e70b7   43 seconds ago   149MB
```

Docker Hub repository URL:

```
https://hub.docker.com/r/hikariatama/devops-info-service-python
```

Tagging strategy:

- `dockerhub-username/devops-info-service-python:lab02` for the lab submission.
- `dockerhub-username/devops-info-service-python:1.0.0` for a versioned release.
- `dockerhub-username/devops-info-service-python:latest` for the most recent stable build.

Docker push output:

```
The push refers to repository [docker.io/hikariatama/devops-info-service-python]
fee9aaee41bd: Preparing
1123dc1387de: Preparing
6a6833764019: Preparing
39896042f189: Preparing
69fd452f3879: Preparing
083605e5ab90: Preparing
675d3200abe3: Preparing
e6060824c6b0: Preparing
a0e71ab2b234: Preparing
083605e5ab90: Waiting
675d3200abe3: Waiting
e6060824c6b0: Waiting
a0e71ab2b234: Waiting
fee9aaee41bd: Pushed
6a6833764019: Retrying in 5 seconds
39896042f189: Pushed
69fd452f3879: Pushed
6a6833764019: Retrying in 4 seconds
1123dc1387de: Pushed
6a6833764019: Retrying in 3 seconds
083605e5ab90: Mounted from library/python
675d3200abe3: Mounted from library/python
6a6833764019: Retrying in 2 seconds
e6060824c6b0: Mounted from library/python
6a6833764019: Retrying in 1 second
a0e71ab2b234: Mounted from library/python
6a6833764019: Pushed
lab02: digest: sha256:4242b23b5116a8b739fbff8de0a54fe21071b33f4354105dbd65314d8dbb86d5 size: 2199
```

## Technical Analysis

- Why the Dockerfile works: it installs dependencies before copying the app and uses a non-root user for runtime, so the container starts quickly and runs with least privilege.

- If layer order changed: copying app code before dependencies would invalidate the dependency cache on every change and slow rebuilds.

- Security considerations: non-root runtime user, minimized build context, and no extra tooling installed.

- `.dockerignore` improvements: smaller build context reduces build time and prevents accidental inclusion of secrets or local artifacts.

## Challenges & Solutions

- Pip warning about running as root during build.
Solution: keep install at build time and switch to a non-root user for runtime to maintain least privilege.

- Ensuring files are owned by the runtime user.
Solution: use `COPY --chown=app:app` to avoid permission issues at runtime.
