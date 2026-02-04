# Lab 2 - Docker Containerization

## Docker Best Practices Applied

### Non-root user

```
RUN groupadd -r app && useradd -r -g app app && chown -R app:app /app
```

Created a separate non-root user "app" in the image and switch to this user with `USER app`. This reduces the damage that can be done if the application inside the container is compromised.

### Layer caching

`requirements.txt` is copied and installed before copying the application code so dependency changes and app code changes create different layers and builds reuse the dependency layer when possible.

### Only copy necessary files & Use Dockerignore

Only `requirements.txt` and `app.py` are copied. `.dockerignore` lists unnecessary files. This reduces the image size.

### Specific base image

```
FROM python:3.12-slim
```

The image uses `python:3.12-slim` to get a maintained python3.12 image. Using a specific major python release in the base image helps with predictability.

## Image Information & Decisions

I chose `python:3.12-slim` as a base image since I have previously tested the application with python 3.12 . I chose the slim version to have a smalled build size.

Final image size is 132MB which is only 13MB over the base `python:3.12-slim` image, that is 119MB.

The image layer structure consists of first installing the dependencies, then copying app code. This allows to reuse the dependencies, and not reinstall dependencies on every code change.

For optimization I have used `--no-cache-dir` in the dependency installation command `pip install --no-cache-dir -r requirements.txt`. In order to not cache the dependencies and to make the resulting build smaller.

## Build & Run Process

### Build image

```bash
cd app_python
docker build -t iucapstonead/devops-info-service:lab02 .
```

Terminal output:

```
cirno@t14-devops:~/Documents/DevOps-Core-Course$ cd app_python
cirno@t14-devops:~/Documents/DevOps-Core-Course/app_python$ docker build -t iucapstonead/devops-info-service:lab02 .
[+] Building 29.9s (11/11) FINISHED                                                                                                                                            docker:default
 => [internal] load build definition from Dockerfile                                                                                                                                     0.0s
 => => transferring dockerfile: 286B                                                                                                                                                     0.0s
 => [internal] load metadata for docker.io/library/python:3.12-slim                                                                                                                      0.0s
 => [internal] load .dockerignore                                                                                                                                                        0.0s
 => => transferring context: 113B                                                                                                                                                        0.0s
 => CACHED [1/6] FROM docker.io/library/python:3.12-slim                                                                                                                                 0.0s
 => [internal] load build context                                                                                                                                                        0.0s
 => => transferring context: 63B                                                                                                                                                         0.0s
 => [2/6] WORKDIR /app                                                                                                                                                                   3.7s
 => [3/6] COPY requirements.txt .                                                                                                                                                        0.0s
 => [4/6] RUN pip install --no-cache-dir -r requirements.txt                                                                                                                             5.1s
 => [5/6] COPY app.py .                                                                                                                                                                  5.1s 
 => [6/6] RUN groupadd -r app && useradd -r -g app app && chown -R app:app /app                                                                                                         15.9s 
 => exporting to image                                                                                                                                                                   0.1s 
 => => exporting layers                                                                                                                                                                  0.1s 
 => => writing image sha256:efac5b8d6f81148843d1b713144694aeca62ba8d6cef554d297c4410a64b6b12                                                                                             0.0s 
 => => naming to docker.io/iucapstonead/devops-info-service:lab02
```

### Running image

```bash
docker run -p 5000:5000 iucapstonead/devops-info-service:lab02
```

Terminal Output

```
cirno@t14-devops:~/Documents/DevOps-Core-Course/app_python$ docker run -p 5000:5000 iucapstonead/devops-info-service:lab02
2026-02-04 20:24:09,443 - __main__ - INFO - Starting...
 * Serving Flask app 'app'
 * Debug mode: off
2026-02-04 20:24:09,446 - werkzeug - INFO - WARNING: This is a development server. Do not use it in a production deployment. Use a production WSGI server instead.
 * Running on all addresses (0.0.0.0)
 * Running on http://127.0.0.1:5000
 * Running on http://172.17.0.2:5000
2026-02-04 20:24:09,446 - werkzeug - INFO - Press CTRL+C to quit
2026-02-04 20:24:33,523 - __main__ - INFO - Request: GET / from 172.17.0.1
2026-02-04 20:24:33,525 - werkzeug - INFO - 172.17.0.1 - - [04/Feb/2026 20:24:33] "GET / HTTP/1.1" 200 -
2026-02-04 20:24:42,137 - __main__ - INFO - Request: GET / from 172.17.0.1
2026-02-04 20:24:42,138 - werkzeug - INFO - 172.17.0.1 - - [04/Feb/2026 20:24:42] "GET / HTTP/1.1" 200 -
```

Curl testing the main endpoint

```bash
curl localhost:5000
```

Curl output

```
{"endpoints":[{"description":"Service information","method":"GET","path":"/"},{"description":"Health check","method":"GET","path":"/health"}],"request":{"client_ip":"172.17.0.1","method":"GET","path":"/","user_agent":"curl/8.5.0"},"runtime":{"current_time":"2026-02-04T20:24:42.137455+00:00","timezone":"UTC","uptime_human":"0 hours, 0 minutes","uptime_seconds":32},"service":{"description":"DevOps course info service","framework":"Flask","name":"devops-info-service","version":"1.0.0"},"system":{"architecture":"x86_64","cpu_count":8,"hostname":"bdbdc916a90f","platform":"Linux","platform_version":"Debian GNU/Linux 13 (trixie)","python_version":"3.12.12"}}
```

### Docker Hub repository URL

https://hub.docker.com/r/iucapstonead/devops-info-service


## Technical Analysis

### Why Dockerfile order works

Installing dependencies first produces a layer that is reused when only application code changes. Copying only requirements and installing prevents copying source files that would invalidate the cache.

### If order changed

If order was changed to be copy all application source code and the perform pip install, any change to the source code would invalidate the dependencies cache and require running pip install on every build, slowing down build times.

### Security Considerations

Running application as a dedicated non-root app user reduces the attack surface. Using a minimal base image reduces the attack surface.

### Dockerfile benefits

Excluding venv .git and other files reduces the amount of data sent to the Docker daemon, speeding up build times.

## Challenges

No challenges were faced during this lab. Everything was done without any issues.
