## Docker Best Practices Applied
1. Non-Root User
```dockerfile
RUN useradd --create-home --shell /bin/bash appuser
USER appuser
```
Why it matters: Running containers as non-root users reduces security risks if the container is compromised.

2. Layer Caching
```dockerfile
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY app.py .
```
Why it matters: Docker caches each layer. If requirements.txt hasn't changed, Docker uses cache, speeding up builds.

3. Minimal Base Image
```dockerfile
FROM python:3.11.8-slim-bookworm
```
Why it matters: The slim image is smaller than the full image, reducing attack surface and download time.

## Image Information & Decisions

1. Base Image
Chose python:3.11.8-slim-bookworm as a balance between size and functionality.

2. Final image 
263 MB

3. Layer Structure
Python base image

User creation

Python dependencies installation

Source code copy

## Build & Run Process

### Complete terminal output from the build process
docker build -t pythonapp:1.0.0 .

```bash
[+] Building 2.1s (12/12) FINISHED                                                                                           docker:desktop-linux
 => [internal] load build definition from Dockerfile                                                                                         0.0s
 => => transferring dockerfile: 303B                                                                                                         0.0s
 => [internal] load metadata for docker.io/library/python:3.11.8-slim-bookworm                                                               1.6s
 => [auth] library/python:pull token for registry-1.docker.io                                                                                0.0s
 => [internal] load .dockerignore                                                                                                            0.0s
 => => transferring context: 152B                                                                                                            0.0s 
 => [1/6] FROM docker.io/library/python:3.11.8-slim-bookworm@sha256:90f8795536170fd08236d2ceb74fe7065dbf74f738d8b84bfbf263656654dc9b         0.0s 
 => => resolve docker.io/library/python:3.11.8-slim-bookworm@sha256:90f8795536170fd08236d2ceb74fe7065dbf74f738d8b84bfbf263656654dc9b         0.0s 
 => [internal] load build context                                                                                                            0.0s 
 => => transferring context: 64B                                                                                                             0.0s 
 => CACHED [2/6] RUN useradd --create-home --shell /bin/bash appuser                                                                         0.0s 
 => CACHED [3/6] WORKDIR /app                                                                                                                0.0s 
 => CACHED [4/6] COPY requirements.txt .                                                                                                     0.0s
 => CACHED [5/6] RUN pip install --no-cache-dir -r requirements.txt                                                                          0.0s 
 => CACHED [6/6] COPY app.py .                                                                                                               0.0s 
 => exporting to image                                                                                                                       0.2s 
 => => exporting layers                                                                                                                      0.0s 
 => => exporting manifest sha256:ba351c3b5ef9c55d6620c190aeedf9cd4c55660ea671b91cc0bcd04efb6579d1                                            0.0s 
 => => exporting config sha256:ed7914d6951962b12adb087245dc2d62fa66131e3102546b0e0f019c58265967                                              0.0s 
 => => exporting attestation manifest sha256:f7afeb5728bc47c570b62f6860cb40aedd9e76562afb4c33e585100b9ff2d5c1                                0.0s 
 => => exporting manifest list sha256:5a37812502df4a63d16ee75c53e9e7812d727d05ce9ccc7e1b7b5ad38222d0f5                                       0.0s 
 => => naming to docker.io/library/pythonapp:1.0.0                                                                                           0.0s 
 => => unpacking to docker.io/library/pythonapp:1.0.0                                                                                        0.0s 
```

run -d -p 5000:5000 pythonapp:1.0.0
4d6e4c3c34c98dbaa34a9d691b35687703e800e36490ed7916762dfcc611f6af

docker ps
```bash
CONTAINER ID   IMAGE             COMMAND           CREATED         STATUS         PORTS                                         NAMES
4d6e4c3c34c9   pythonapp:1.0.0   "python app.py"   3 minutes ago   Up 3 minutes   0.0.0.0:5000->5000/tcp, [::]:5000->5000/tcp   elastic_hermann
```

curl http://localhost:5000
```bash
{"service":{"name":"devops-info-service","version":"1.0.0","description":"DevOps course info service","framework":"FastAPI"},"system":{"hostname":"4d6e4c3c34c9","platform":"Linux","platform_version":"#1 SMP Tue Nov 5 00:21:55 UTC 2024","architecture":"x86_64","cpu_count":8,"python_version":"3.11.8"},"runtime":{"uptime_seconds":49,"uptime_human":"0 hours, 0 minutes","current_time":"2026-02-04T09:44:00.615006","timezone":"UTC"},"request":{"client_ip":"172.17.0.1","user_agent":"curl/8.13.0","method":"GET","path":"/"},"endpoints":[{"path":"/","method":"GET","description":"Service information"},{"path":"/health","method":"GET","description":"Health check"}]}
```

curl http://localhost:5000/health
```bash
{"status":"healthy","timestamp":"2026-02-04T09:44:50.535310","uptime_seconds":99}
```

docker login
```bash
Authenticating with existing credentials... [Username: aidarsarvartdinov]

i Info → To login with a different account, run 'docker logout' followed by 'docker login'


Login Succeeded
```
docker tag pythonapp:1.0.0 aidarsarvartdinov/pythonapp:1.0.0
docker push aidarsarvartdinov/pythonapp:1.0.0

```bash
The push refers to repository [docker.io/aidarsarvartdinov/pythonapp]
87b8bf94a2ac: Pushed
1103112ebfc4: Pushed
162e5e391d8e: Pushed
b4b80ef7128d: Pushed
e165a9131697: Pushed
cc7f04ac52f8: Pushed
2357907a9de6: Pushed
5b1866afe005: Pushed
feadaf5c4ba6: Pushed
06f372162f15: Pushed
8a1e25ce7c4f: Pushed
1.0.0: digest: sha256:ce016e6e2263bff54be5b138729d6d972d5d0d6e1e16165021c8c5ee2f5971bf size: 856
```

Docker Hub URL:
https://hub.docker.com/layers/aidarsarvartdinov/pythonapp/1.0.0/images/sha256:ba351c3b5ef9c55d6620c190aeedf9cd4c55660ea671b91cc0bcd04efb6579d1?uuid=3A5462CF-AA93-4E88-AFD2-BDB1B602384A


## Technical Analysis
1. Why does this layer order work?
Order matters for caching. Dependencies change less frequently than code, so they're installed first.

2. What if we change the layer order?
If code is copied before dependencies, every code change would trigger dependency reinstallation.

3. Security Measures Implemented
Non-root user

Minimal base image

4. How .dockerignore Helps
Reduces build context, speeds up the process, and prevents secrets from entering the image.

## Challenges & Solutions
What I Learned:
Importance of Docker layer caching

Container security principles

Image size optimization techniques
