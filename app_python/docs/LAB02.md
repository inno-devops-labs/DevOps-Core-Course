# Lab 2 — Docker Containerization

## Docker Best Practices Applied
- **Specific Base Image:** Using python:3.12-slim specifying the version ensures predictable environment
```
FROM python:3.12-slim AS builder
...
FROM python:3.12-slim
```
- **Layer Ordering:** Dockerfile is written with such layer, that Docker won't change layers, unless it's neccessary. So changing code in app.py, wont require to reinstall dependencies, unless the dependencies changes.
```
# Dependencies install layer
FROM python:3.12-slim AS builder
...
COPY app_python/requirements.txt .

RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Running programm
FROM python:3.12-slim
...
CMD ["python", "app.py"]
```
- **Non-Root User:** Using non-root user decreases security risks of breakout, and possibility of it.
```
RUN groupadd -r appuser && useradd -r -g appuser appuser
...
RUN chown -R appuser:appuser /app
...
USER appuser
...

```
- **Copying only necessary:** Dockerfile don't copy any files, which excessive for running app.py, so image remain small in size. 
```
COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

COPY app_python/app.py .
```
## Image Information & Decisions
- **Base image:** python:3.12-slim used, to decrease the image size.
- **Image size:** final image size is 199mb, which mostly comes from basic `python:3.12-slim` image size
- **Layer structure explanation:** - If any action at some layer starts to produce different result, all layers below computed again, so current layer order first import requirements, which changes not frequently. Then creates user and uses it instead of root, this is almost-never changing layers, but requirements install frequently needs root privileges, so user creation happens after. Then it's just copying actual code and running it, this part changing almost every time, so those layers are the last
- **Optimization choices:** follow best practices, use small slim base image, copy only neccessary files, use proper layer ordering.

## Build & Run Process
- **Complete terminal output from build process:**
```
$ docker build -t devops-info-service .
DEPRECATED: The legacy builder is deprecated and will be removed in a future release.
            Install the buildx component to build images with BuildKit:
            https://docs.docker.com/go/buildx/

Sending build context to Docker daemon  927.7kB
Step 1/16 : FROM python:3.12-slim AS builder
 ---> 87b49ee9d18d
Step 2/16 : ENV PYTHONDONTWRITEBYTECODE=1     PYTHONUNBUFFERED=1
 ---> Using cache
 ---> 07011a084c7f
Step 3/16 : WORKDIR /app
 ---> Using cache
 ---> 77152fff0ae8
Step 4/16 : COPY app_python/requirements.txt .
 ---> Using cache
 ---> 55913bacbad6
Step 5/16 : RUN pip install --no-cache-dir --upgrade pip &&     pip install --no-cache-dir -r requirements.txt
 ---> Using cache
 ---> c326bfd9e275
Step 6/16 : FROM python:3.12-slim
 ---> 87b49ee9d18d
Step 7/16 : WORKDIR /app
 ---> Using cache
 ---> 27090590b024
Step 8/16 : RUN groupadd -r appuser && useradd -r -g appuser appuser
 ---> Using cache
 ---> c42c4931ec5a
Step 9/16 : COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
 ---> Using cache
 ---> fb1db854b117
Step 10/16 : COPY --from=builder /usr/local/bin /usr/local/bin
 ---> Using cache
 ---> cb02a27cc5be
Step 11/16 : COPY app_python/app.py .
 ---> Using cache
 ---> 137688dba132
Step 12/16 : RUN chown -R appuser:appuser /app
 ---> Using cache
 ---> 11a49be0286d
Step 13/16 : USER appuser
 ---> Using cache
 ---> 6939ead36931
Step 14/16 : EXPOSE 5000
 ---> Using cache
 ---> 8fc6c2ddeea1
Step 15/16 : ENV HOST=0.0.0.0     PORT=5000
 ---> Using cache
 ---> ee8d4cbbdd7b
Step 16/16 : CMD ["python", "app.py"]
 ---> Using cache
 ---> e1e286cbcbbe
Successfully built e1e286cbcbbe
Successfully tagged devops-info-service:latest

```
- **Terminal output showing container running:**
```
docker ps
CONTAINER ID   IMAGE                       COMMAND           CREATED         STATUS         PORTS      NAMES
3da1dbdf4144   devops-info-service:1.0.0   "python app.py"   4 seconds ago   Up 3 seconds   5000/tcp   sad_proskuriakova
```
- **Terminal output from testing endpoints (curl/httpie):**
```
$ curl -s http://localhost:5000/ | jq .
{
  "endpoints": [
    {
      "description": "Service information",
      "method": "GET",
      "path": "/"
    },
    {
      "description": "Health check",
      "method": "GET",
      "path": "/health"
    }
  ],
  "request": {
    "client_ip": "172.17.0.1",
    "method": "GET",
    "path": "/",
    "user_agent": "curl/8.18.0"
  },
  "runtime": {
    "current_time": "2026-02-04T12:09:53.157Z",
    "timezone": "UTC",
    "uptime_human": "0 hours, 0 minutes",
    "uptime_seconds": 45
  },
  "service": {
    "description": "DevOps course info service",
    "framework": "Flask",
    "name": "devops-info-service",
    "version": "1.0.0"
  },
  "system": {
    "architecture": "x86_64",
    "cpu_count": 8,
    "hostname": "292ee90a8d4c",
    "platform": "Linux",
    "platform_version": "Linux-6.17.13-hardened1-2-hardened-x86_64-with-glibc2.41",
    "python_version": "3.12.12"
  }
}

$ curl -s http://localhost:5000/health | jq .
{
  "status": "healthy",
  "timestamp": "2026-02-04T12:09:58.563Z",
  "uptime_seconds": 51
}
```
- **Docker Hub repository URL:** https://hub.docker.com/repository/docker/saddogsec/devops-info-service

## Technical Analysis
- **Why does your Dockerfile work the way it does?** Because water is wet, sky is blue, and people who made Docker, made that it works the way it does
- **What would happen if you changed the layer order?** Depends on how. One good idea is to move user creation above requirements install, which after some tweaks make image more hardened, but introduce more complexity. Moving requirements install below the copying app file, would force to compute again requirements install layer, even if requirements havent changed.
- **What security considerations did you implement?** Use non-root user for running the app.
- **How does .dockerignore improve your build?** It ensures that unneccessary files wont be copied into image, reducing image size.

## Challenges & Solutions
- **Issues encountered during implementation. How you debugged and resolved them** No issues were encountered during implementation.
- **What you learned from the process** It's not my first time doing this, so actually nothing new.
