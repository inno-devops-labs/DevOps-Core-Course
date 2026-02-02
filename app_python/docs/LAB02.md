# Lab 02

## Docker Best Practices Applied

### Run container as non root user

```dockerfile
RUN groupadd -g 1000 nonroot
RUN useradd -r --no-create-home -u 1000 -g nonroot nonroot

USER nonroot
```

- Non-root users enhances security by limiting access and potential damage from vulnerabilities.

### Added .dockerignore file

```dockerignore
.venv
docs
tests
*.md
```

It allows as easy exclude files not relevant to build to optimize size of image.

## Image Information & Decisions

Choice: python:3.12-slim

I use slim version because it smaller than default and compatible with choosen packages.

Using --no-cache-dir ensures that pip doesn't keep a copy of the downloaded .whl files inside the image, saving significant space.

By copying requirements.txt before the rest of code, I take advantage of layer caching. If I change a line of code but don't change my dependencies, Docker skips the "pip install" step entirely during the next build.

## Build & Run Process

### Complete terminal output from your build process

```bash
docker build -t python_app .
[+] Building 0.9s (11/11) FINISHED                                                                                             docker:default
 => [internal] load build definition from Dockerfile                                                                                     0.0s
 => => transferring dockerfile: 380B                                                                                                     0.0s
 => [internal] load metadata for docker.io/library/python:3.12-slim                                                                      0.0s
 => [internal] load .dockerignore                                                                                                        0.0s
 => => transferring context: 121B                                                                                                        0.0s
 => [1/6] FROM docker.io/library/python:3.12-slim                                                                                        0.0s
 => [internal] load build context                                                                                                        0.0s
 => => transferring context: 743B                                                                                                        0.0s
 => CACHED [2/6] WORKDIR /app                                                                                                            0.0s
 => CACHED [3/6] COPY requirements.txt ./                                                                                                0.0s
 => CACHED [4/6] RUN pip install --no-cache-dir -r requirements.txt                                                                      0.0s
 => [5/6] COPY . .                                                                                                                       0.1s
 => [6/6] RUN groupadd -g 1000 nonroot     && useradd -r --no-create-home -u 1000 -g nonroot nonroot                                     0.4s
 => exporting to image                                                                                                                   0.1s
 => => exporting layers                                                                                                                  0.1s
 => => writing image sha256:e34a5c972799ab8ab3c86fd60e0b0fd91912494464fba6bbd6521e3c46298526                                             0.0s
 => => naming to docker.io/library/python_app                              
 ```

### Terminal output showing container running

 ```bash
docker run -p 5000:5000 python_app
2026-02-02 18:24:03,704 - __main__ - INFO - Application starting...
INFO:     Started server process [1]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:5000 (Press CTRL+C to quit)
 ```

### Terminal output from testing endpoints

```bash
curl --location http://localhost:5000
{"service":{"name":"devops-info-service","version":"1.0.0","description":"DevOps course info service","framework":"FastAPI"},"system":{"hostname":"d61873a43283","platform":"Linux","platform_version":"6.15.4-200.fc42.x86_64","architecture":"x86_64","cpu_count":12,"python_version":"3.12.12"},"runtime":{"uptime_seconds":49,"uptime_human":"0 hours, 0 minutes","current_time":"2026-02-02T18:24:53.274476+00:00","timezone":"UTC"},"request":{"client_ip":"172.17.0.1","user_agent":"curl/8.11.1","method":"GET","path":"/"},"endpoints":[{"path":"/openapi.json","description":"openapi","methods":["HEAD","GET"]},{"path":"/docs","description":"swagger_ui_html","methods":["HEAD","GET"]},{"path":"/docs/oauth2-redirect","description":"swagger_ui_redirect","methods":["HEAD","GET"]},{"path":"/redoc","description":"redoc_html","methods":["HEAD","GET"]},{"path":"/","description":"read_root","methods":["GET"]},{"path":"/health","description":"health","methods":["GET"]}]}
```

```bash
curl --location http://localhost:5000/health
{"status":"healthy","timestamp":"2026-02-02T18:27:13.027683+00:00","uptime_seconds":189}
```

### Docker Hub repository URL

[Link](https://hub.docker.com/r/bulatgazizov/python_app)

Push proccess:

```bash
docker tag python_app:latest bulatgazizov/python_app:0.0.1
docker push bulatgazizov/python_app:0.0.1
The push refers to repository [docker.io/bulatgazizov/python_app]
ac161dc8739d: Pushed 
c3601a0c9997: Pushed 
033958171c9f: Pushed 
d554fa84f977: Pushed 
1a543660baf1: Pushed 
7770fbb416af: Mounted from library/python 
acbbee3380a1: Mounted from library/python 
16dffb6a6636: Mounted from library/python 
d7c97cb6f1fe: Mounted from library/python 
0.0.1: digest: sha256:c5d9d35cb04d651178aa2f478ef8cea2c745de712aefc50aebd16b8234b596be size: 2200
```

## Technical Analysis

Why does your Dockerfile work the way it does?

- Docker builds images line-by-line. If a line hasn’t changed since the last build, Docker reuses the "cached" version of that layer.

What would happen if you changed the layer order?

- If I move COPY . . to the top of the file, I may break the cache. So, every time then I make small changes in code, It would re-run "pip install".

What security considerations did you implement?

- Non-root user inside container, slim version of image

How does .dockerignore improve your build?

- It exludes files not related to build which makes image size smaller.

## Challenges & Solutions

### Issues encountered during implementation

No issues

### What you learned from the process

nothinc