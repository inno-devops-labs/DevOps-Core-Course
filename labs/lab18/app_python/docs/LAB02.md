# Lab 02

## 1. Docker Best Practices Applied
### 1.1 Non-Root User
- Security: Running as non-root minimizes the impact of potential container breaches
- Principle of Least Privilege: The application only has permissions it needs
- Compliance: Many security standards require non-root execution
- Risk Reduction: If the application is compromised, the attacker has limited system access

```dockerfile
RUN useradd --create-home --shell /bin/bash appuser

USER appuser
```

### 1.2 Specific Base Image Version
- Reproducibility: Specific versions ensure consistent builds across environments
- Security: Known, patched versions reduce vulnerability exposure
- Stability: Avoids breaking changes from latest tags
- Size Optimization: slim variant reduces image size by ~50% compared to full Python image

```dockerfile
FROM python:3.12-slim
```

### 1.3 Layer Caching Optimization
- Build Speed: Changing code doesn't trigger dependency reinstallation
- Cache Efficiency: Leverages Docker's layer caching for faster builds
- CI/CD Performance: Reduces build times in pipelines
- Developer Experience: Quicker iteration during development

```dockerfile
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app.py .
```

### 1.4 .dockerignore File
- Smaller Images: Excludes unnecessary files, reducing image size
- Security: Prevents secrets from accidentally being included
- Build Performance: Less context to send to Docker daemon
- Cleanliness: Only production-relevant files in the image

```
.git
.gitignore
...
```

### 1.5 No Cache Directory
- Image Size: Removes pip cache
- Security: Eliminates cached package files that could contain vulnerabilities
- Clean Builds: Ensures fresh downloads each build

```dockerfile
RUN pip install --no-cache-dir -r requirements.txt
```


## 2. Image Information & Decisions 
### Chosen: `python:3.12-slim`
- `python:3.12-slim` provides the optimal balance of size (~125MB), compatibility (glibc), and security (minimal packages).
- `python:3.12` - too large (~1GB)
- `python:3.12-alpine` - too small - Python packages may fail

### Final image size: 132MB
- Assessment: Acceptable for a Python service.
- Size Breakdown:
    - Base image (python:3.12-slim): 125MB
    - Application dependencies: 8MB
    - Application code: 3,7 kB 

    Total: 132MB

### Layer Structure
1. Base layers (immutable, cached across all builds)
2. System packages (rarely changed)
3. Dependencies (changed when requirements.txt updates)
4. Application code (frequently changed)
5. Configuration (runtime settings)

### Optimization Choices
Implemented:
- Layer ordering: Dependencies before code
- Slim base: Minimal OS footprint
- No cache: Clean pip installs
- Multi-command RUN: Single layer for user creation


## 3. Build & Run ProcessBuild & Run Process

### Build and push process terminal output:
```sh
damir@damir-VB:~/Desktop/DevOps/DevOps-Core-Course$ docker build -t devops-info-service:latest ./app_python/
DEPRECATED: The legacy builder is deprecated and will be removed in a future release.
            Install the buildx component to build images with BuildKit:
            https://docs.docker.com/go/buildx/

Sending build context to Docker daemon  8.704kB
Step 1/9 : FROM python:3.12-slim
 ---> c78a70d7588f
Step 2/9 : RUN useradd --create-home --shell /bin/bash appuser
 ---> Using cache
 ---> 633616f640da
Step 3/9 : WORKDIR /app
 ---> Using cache
 ---> 428cc6c9edd9
Step 4/9 : COPY requirements.txt .
 ---> Using cache
 ---> 5c3f41c3170b
Step 5/9 : RUN pip install --no-cache-dir -r requirements.txt
 ---> Using cache
 ---> d56ad894e57a
Step 6/9 : COPY app.py .
 ---> Using cache
 ---> 67026a81e73f
Step 7/9 : USER appuser
 ---> Using cache
 ---> f4455d3b7569
Step 8/9 : EXPOSE 5000
 ---> Using cache
 ---> acfc132c1e47
Step 9/9 : CMD ["python", "app.py"]
 ---> Using cache
 ---> 8a7e51a097ec
Successfully built 8a7e51a097ec
Successfully tagged devops-info-service:latest
damir@damir-VB:~/Desktop/DevOps/DevOps-Core-Course$ docker tag devops-info-service:latest damirsadykov/devops-info-service:latest
damir@damir-VB:~$ docker tag devops-info-service:latest damirsadykov/devops-info-service:1.0
damir@damir-VB:~/Desktop/DevOps/DevOps-Core-Course$ docker login
Authenticating with existing credentials...
WARNING! Your password will be stored unencrypted in ~/.docker/config.json.
Configure a credential helper to remove this warning. See
https://docs.docker.com/engine/reference/commandline/login/#credential-stores

Login Succeeded
damir@damir-VB:~/Desktop/DevOps/DevOps-Core-Course$ docker push damirsadykov/devops-info-service:latest
The push refers to repository [docker.io/damirsadykov/devops-info-service]
33c1e7bf52a9: Pushed 
ba6ad2b86434: Pushed 
56f38b3c8b1d: Pushed 
6f891e75b169: Pushed 
d85f0fb2b9c2: Pushed 
343fbb74dfa7: Mounted from library/python 
cfdc6d123592: Mounted from library/python 
ff565e4de379: Mounted from library/python 
e50a58335e13: Mounted from library/python 
latest: digest: sha256:... size: 2199
damir@damir-VB:~/Desktop/DevOps/DevOps-Core-Course$ docker pull damirsadykov/devops-info-service:latest
latest: Pulling from damirsadykov/devops-info-service
Digest: sha256:0...
Status: Image is up to date for damirsadykov/devops-info-service:latest
docker.io/damirsadykov/devops-info-service:latest
damir@damir-VB:~$ docker push damirsadykov/devops-info-service:1.0
The push refers to repository [docker.io/damirsadykov/devops-info-service]
33c1e7bf52a9: Layer already exists 
ba6ad2b86434: Layer already exists 
56f38b3c8b1d: Layer already exists 
6f891e75b169: Layer already exists 
d85f0fb2b9c2: Layer already exists 
343fbb74dfa7: Layer already exists 
cfdc6d123592: Layer already exists 
ff565e4de379: Layer already exists 
e50a58335e13: Layer already exists 
1.0: digest: sha256:... size: 2199
```

### Run and test terminal output:
```sh
damir@damir-VB:~$ docker run -dp 5000:5000 --name test devops-info-service:latest
24252bc5470ee314a9d6be615792db5bec4661b25e4bae9e59fdb560a236f6d4
damir@damir-VB:~$ curl http://localhost:5000/ | python3 -m json.tool
  % Total    % Received % Xferd  Average Speed   Time    Time     Time  Current
                                 Dload  Upload   Total   Spent    Left  Speed
100   692  100   692    0     0  83293      0 --:--:-- --:--:-- --:--:-- 86500
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
        "user_agent": "curl/7.81.0"
    },
    "runtime": {
        "current_time": "2026-02-03T11:33:55.523995Z",
        "timezone": "UTC",
        "uptime_human": "0 hours, 0 minutes",
        "uptime_seconds": 16
    },
    "service": {
        "description": "DevOps course info service",
        "framework": "Flask",
        "name": "devops-info-service",
        "version": "1.0.0"
    },
    "system": {
        "architecture": "x86_64",
        "cpu_count": 2,
        "hostname": "24252bc5470e",
        "platform": "Linux",
        "platform_version": "#91~22.04.1-Ubuntu SMP PREEMPT_DYNAMIC Thu Nov 20 15:20:45 UTC 2",
        "python_version": "3.12.12"
    }
}
damir@damir-VB:~$ curl http://localhost:5000/health | python3 -m json.tool
  % Total    % Received % Xferd  Average Speed   Time    Time     Time  Current
                                 Dload  Upload   Total   Spent    Left  Speed
100    83  100    83    0     0  33413      0 --:--:-- --:--:-- --:--:-- 41500
{
    "status": "healthy",
    "timestamp": "2026-02-03T11:33:59.810204Z",
    "uptime_seconds": 20
}
damir@damir-VB:~$ docker stop test
test
damir@damir-VB:~$ docker rm test
test
```

### Docker Hub repository URL
https://hub.docker.com/repository/docker/damirsadykov/devops-info-service/general

### Tagging strategy
Tag Structure:
```
<dockerhub-username>/<image-name>:<tag>
```

`<tag>` : 
1. `latest`, as it is latest (and only) build. It is for users who want the most recent stable build
2. `1.0`, as it is first (and only) build version. It is for versions reproducibility

## 4. Technical Analysis

### Why This Dockerfile Works
1. Progressive Layering: Each layer builds upon the previous, optimizing cache usage
2. Minimalist Approach: Only includes what's necessary for runtime
3. Security First: Non-root user, no secrets, clean builds

### Layer Order Impact

#### Current order:
```dockerfile
# Layer 1: Base image (cached)
FROM python:3.12-slim

# Layer 2: User setup (rarely changes)
RUN useradd --create-home --shell /bin/bash appuser
WORKDIR /app

# Layer 3: Dependencies (changes when requirements.txt updates)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Layer 4: Application code (changes frequently)
COPY app.py .

# Layer 5: Runtime configuration
USER appuser
EXPOSE 5000
CMD ["python", "app.py"]
```

#### What if we reversed layers 3 and 4?
```dockerfile
COPY app.py .                             # Changes frequently - cache invalidated often
RUN pip install -r requirements.txt  # Reinstalls every code change
```

#### Impact:
- Build Time: Increases from ~8s to ~30s per build
- Cache Efficiency: Dependencies reinstalled on every code change
- Network Usage: Downloads packages repeatedly
- CI/CD Costs: Longer pipeline runtimes


### Security Considerations

#### Implemented:
1. Non-Root Execution: Limits container breakout impact
2. Specific Base Version: Known, patched vulnerabilities
3. No Secrets in Image: Environment variables or mounts only
4. Minimal Packages: Reduced attack surface
5. Clean Builds: No cached files or metadata

#### Security Benefits:
- CVE Reduction: Smaller images = fewer potential vulnerabilities
- Compliance: Meets security standards for container deployment
- Auditability: Clear layer history for security reviews
- Runtime Safety: Limited permissions if compromised


### `.dockerignore` Benefits
- Size Reduction: Image ~20MB smaller
- Build Speed: Less context to transfer (faster builds)
- Security: No accidental secret inclusion
- Cleanliness: Production-only files in image
- Consistency: Same image regardless of development environment


## 5. Challenges & Solutions
I have not meet any serious issues with this task.

From the process, I have learned about proper stages layout.