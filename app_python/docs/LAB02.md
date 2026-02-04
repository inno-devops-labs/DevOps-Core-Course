## Docker Best Practices Applied
1. Minimal Base Image
    ```dockerfile
   FROM python:3.13-slim
    ```
   it important because `slim` is significantly smaller than `python:3.13` -> faster download and deployment

2. Proper Layer Ordering
   ```dockerfile
   WORKDIR /app
   
   COPY requirements.txt .
   RUN pip install --no-cache-dir -r requirements.txt
   
   COPY . .
   ```
   it important because dependencies are installed once and when code changes, `pip install` is not rerun.

3. .dockerignore
   ```dockerignore
   .venv
   __pycache__
   .git
   .gitignore
   .idea
   *.pyc
   ```
   
   it important because it reduces the size of the build context and speeds up `docker build`

4. Non-root User
   ```dockerfile
   RUN useradd -m appuser
   USER appuser
   ```
   
   it important because container doesn't run as root, reduces the risk of vulnerabilities

5. No Cache in pip

```dockerfile
RUN pip install --no-cache-dir -r requirements.txt
```

it important because it reduces the final image size and pip cache is not needed at runtime


## Image Information & Decisions

#### Base image chosen:
| Image            | Reason for failure |
| ---------------- |-------------------|
| python:3.13      | too big           |
| alpine           | dependency issues |
| python:3.13-slim | optimal balance   |

#### Final image size:
```text
140MB
```

#### Layer structure
```dockerfile
FROM python:3.13-slim
WORKDIR /app
RUN adduser --disabled-password --gecos "" appuser
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
RUN chown -R appuser:appuser /app
USER appuser
CMD ["python", "app.py"]
```

## Build & Run Process
1. Complete terminal output from build process
   ```text
   (.venv) C:\Users\kve10\PycharmProjects\DevOps-Core-Course\app_python>docker build -t devops-info-service:latest .
   [+] Building 15.0s (12/12) FINISHED                                                                                                                                                                             docker:desktop-linux
    => [internal] load build definition from Dockerfile                                                                                                                                                                            0.0s
    => => transferring dockerfile: 289B                                                                                                                                                                                            0.0s 
    => [internal] load metadata for docker.io/library/python:3.13-slim                                                                                                                                                             1.0s 
    => [internal] load .dockerignore                                                                                                                                                                                               0.0s
    => => transferring context: 104B                                                                                                                                                                                               0.0s 
    => [internal] load build context                                                                                                                                                                                               0.0s 
    => => transferring context: 1.32kB                                                                                                                                                                                             0.0s 
    => [1/7] FROM docker.io/library/python:3.13-slim@sha256:51e1a0a317fdb6e170dc791bbeae63fac5272c82f43958ef74a34e170c6f8b18                                                                                                       0.0s 
    => CACHED [2/7] WORKDIR /app                                                                                                                                                                                                   0.0s 
    => CACHED [3/7] RUN adduser --disabled-password --gecos "" appuser                                                                                                                                                             0.0s 
    => CACHED [4/7] COPY requirements.txt .                                                                                                                                                                                        0.0s 
    => [5/7] RUN pip install -r requirements.txt                                                                                                                                                                                  12.8s 
    => [6/7] COPY . .                                                                                                                                                                                                              0.0s
    => [7/7] RUN chown -R appuser:appuser /app                                                                                                                                                                                     0.6s
    => exporting to image                                                                                                                                                                                                          0.3s 
    => => exporting layers                                                                                                                                                                                                         0.3s 
    => => writing image sha256:4951433b4ff82147cbd1bf45597c98fb56f13ffa619ec10098559796ac8f6210                                                                                                                                    0.0s 
    => => naming to docker.io/library/devops-info-service:latest  
   ```
2. Terminal output showing container running
   ```text
   (.venv) C:\Users\kve10\PycharmProjects\DevOps-Core-Course\app_python>docker run -d -p 5000:5000 devops-info-service
   8a9df27c507cb56b6999fababd27de98bd87ba96ed0fcdeec0cd3ed10fb6a208
   ```

3. Terminal output from testing endpoints 
   #### root endpoint
   ```text
   (.venv) C:\Users\kve10\PycharmProjects\DevOps-Core-Course\app_python>curl http://localhost:5000/
   {"service":{"name":"devops-info-service","version":"1.0.0","description":"DevOps course info service","framework":"Fastapi"},"system":{"hostname":"69f1f9d7f438","platform":"Linux","platform_version":"#1 SMP Tue Nov 5 00:21:55 UTC
    2024","architecture":"x86_64","cpu_count":8,"python_version":"3.13.11"},"runtime":{"uptime_seconds":63481,"uptime_human":"17 hours, 38 minutes","current_time":"2026-01-28T13:48:16.715852Z","timezone":"UTC"},"request":{"client_ip":"172.17.0.1","user_agent":"curl/8.16.0","method":"GET","path":"/"},"endpoints":[{"path":"/","method":"GET","description":"Service information"},{"path":"/health","method":"GET","description":"Health check"}]}
   ```
   #### health endpoint
   ```text
   (.venv) C:\Users\kve10\PycharmProjects\DevOps-Core-Course\app_python>curl http://localhost:5000/health
   {"status":"healthy","timestamp":"2026-01-28T13:49:10.566548Z","uptime_seconds":63535}
   ```

4. Docker Hub repository URL

```text
https://hub.docker.com/r/th1ef/devops-info-service
```

## Technical Analysis
1. Why does your Dockerfile work the way it does?
   - Layers are built for the cache
   - Runtime and build are logically separated
   - No extra files
   - The environment is managed via `ENV`
2. What would happen if you changed the layer order?
   - The cache breaks
   - Every build rebuilds dependencies
   - CI/CD time increases
3. What security considerations did you implement?
   - Non-root user
   - Minimal base image
   - No dev files
   - Environment variables are set during run
4. How does `.dockerignore` improve your build?
   - Less data → faster build
   - No .git leaks
   - Smaller image size

## Challenges & Solutions
There were no difficulties