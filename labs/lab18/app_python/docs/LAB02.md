## 1. Docker Best Practices Applied

### Non-root user
I used a non-root user inside the container to reduce security risks. If the application is compromised it will not have root privileges inside the container.

### Specific base image
I chose `python:3.13-slim` because it's the official python image with minimal size it makes the container smaller and faster to download.

### Layer caching
I copied `requirements.txt` before the application code. This allows Docker to cache the dependencies layerr so when I change only my code, Docker doesn't need to reinstall dependencies.

### .dockerignore file
This file prevents unnecessary files from being copied into the Docker image, which makes builds faster.

## 2. Image Information & Decisions

### Base image choice
**Image**: `python:3.13-slim`
**Why**: This is the official Python image that includes only essential packages. The slim version is much smaller than the full Python image.

### Final image size
REPOSITORY TAG IMAGE ID CREATED SIZE
nadiaa02/lab02-python-app latest b232497fb2bb 20 minutes ago 184MB

text

### Layer order importance
The order matters for Docker caching. If I copy all files first and then install dependencies, every code change would cause Docker to reinstall all dependencies, which takes much longer.

## 3. Build & Run Process

### Docker build output
[+] Building 38.9s (12/12) FINISHED
=> [internal] load build definition from Dockerfile
=> => transferring dockerfile: 348B
=> [internal] load metadata for docker.io/library/python:3.13-slim
=> [1/7] FROM docker.io/library/python:3.13-slim@sha256:49b618b8afc2742b94fa8419d8f4d3b337f111a0527d417a1db97d4683cb71a6
=> [2/7] RUN useradd -m appuser
=> [3/7] WORKDIR /app
=> [4/7] COPY requirements.txt .
=> [5/7] RUN pip install --no-cache-dir -r requirements.txt
=> [6/7] COPY . .
=> [7/7] RUN chown -R appuser:appuser /app
=> exporting to image
=> => naming to docker.io/library/nadia-lab02-app:latest
Successfully built b232497fb2bb
Successfully tagged nadia-lab02-app:latest

text

### Docker run output
CONTAINER ID IMAGE COMMAND CREATED STATUS PORTS NAMES
bb4d98bd9722 nadia-lab02-app "python app.py" 12 seconds ago Up 12 seconds 0.0.0.0:5000->5000/tcp my-app

text

### Application testing
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
"user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 YaBrowser/25.12.0.0 Safari/537.36"
},
"runtime": {
"current_time": "2026-02-05T10:35:17.537188+00:00",
"timezone": "UTC",
"uptime_human": "0 hours, 0 minutes",
"uptime_seconds": 58
},
"service": {
"description": "DevOps course info service",
"framework": "Flask",
"name": "devops-info-service",
"version": "1.0.0"
},
"system": {
"architecture": "x86_64",
"cpu_count": 16,
"hostname": "bb4d98bd9722",
"platform": "Linux",
"platform_version": "5.15.167.4-microsoft-standard-WSL2",
"python_version": "3.13.12"
}
}

text

### Docker Hub repository
https://hub.docker.com/r/nadiaa02/lab02-python-app

## 4. Technical Analysis

### What happens if layer order changes?
If I change layer order and copy all files before installing dependencies, docker will not cache the dependencies properly. Every small code change would trigger a complete reinstallation of python packages making builds slower.

### Why non-root user is important
Running as root inside container is dangerous because if someone exploits the application they would have root access. Using a non-root user limits potential damage.

### How .dockerignore improves builds
The .dockerignore file tells Docker which files to skip when building the image. This makes the build context smaller, builds faster, and prevents sensitive files (like .env) from accidentally being included.

## 5. Challenges & Solutions

### Challenge 1: Understanding Docker layer caching
At first, I didn't understand why my builds were slow. I realized I was copying all files before installing dependencies.

**Solution**: I reordered the Dockerfile to copy `requirements.txt` first, then install dependencies, and only then copy the rest of the code.

### Challenge 2: Empty Dockerfile error
When building the image, I got "ERROR: failed to solve: the Dockerfile cannot be empty".

**Solution**: I checked the Dockerfile and found it was empty. I recreated it with proper content using PowerShell's Out-File command.

#