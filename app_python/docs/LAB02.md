# Lab 2: Docker Containerization Documentation

## Docker Best Practices Applied

- **Non-Root User**: The container runs as a non-root user (`appuser`) to enhance security by limiting potential damage from a container compromise.
  ```dockerfile
  RUN groupadd -r appgroup && useradd -r -g appgroup appuser
  # ...
  USER appuser
  ```
- **Layer Caching**: The `Dockerfile` is structured to leverage Docker's layer caching. `requirements.txt` is copied and its dependencies are installed before the application code is copied. This means that if only the application code changes, Docker can reuse the cached layers for the dependencies, resulting in faster builds.
- **Multi-Stage Builds**: A multi-stage build is used to separate the build environment from the final runtime environment. The `builder` stage installs dependencies, and the final stage copies only the necessary artifacts, resulting in a smaller and more secure final image.
- **.dockerignore**: A `.dockerignore` file is used to exclude unnecessary files and directories from the build context, which speeds up the build process and reduces the image size.

## Image Information & Decisions

- **Base Image**: `python:3.12-slim` was chosen as the base image. The `slim` variant provides a good balance between size and functionality, including the necessary tools for running Python applications without the bloat of a full OS image.
- **Final Image Size**: The final image size is significantly smaller than it would be without a multi-stage build, as it doesn't include the build tools and other intermediate artifacts.
- **Layer Structure**: The layers are ordered to maximize cache utilization. Dependencies are installed in an early layer, and the application code, which changes more frequently, is added in a later layer.

## Build & Run Process

### Build Output
```
[+] Building 32.0s (17/17) FINISHED
 => [internal] load build definition from Dockerfile                                              0.1s
 => => transferring dockerfile: 972B                                                              0.0s
 => [internal] load metadata for docker.io/library/python:3.12-slim                               3.0s
 => [internal] load .dockerignore                                                                 0.1s
 => => transferring context: 154B                                                                 0.0s
 => [builder 1/5] FROM docker.io/library/python:3.12-slim@sha256:a4aed108eb5c7d050e34199ca6afac  10.9s
 => [internal] load build context                                                                 0.0s
 => => transferring context: 4.57kB                                                               0.0s
 => [builder 2/5] WORKDIR /app                                                                    0.2s
 => [stage-1 2/7] RUN groupadd -r appgroup && useradd -r -g appgroup appuser                      3.2s
 => [builder 3/5] COPY requirements.txt .                                                         0.1s
 => [builder 4/5] RUN pip install --no-cache-dir -r requirements.txt                             12.0s
 => [stage-1 3/7] WORKDIR /home/appuser                                                           0.1s
 => [builder 5/5] COPY app.py .                                                                   0.1s
 => [stage-1 4/7] COPY --from=builder /usr/local/lib/python3.12/site-packages/ /usr/local/lib/py  1.0s
 => [stage-1 5/7] COPY --from=builder /usr/local/bin/ /usr/local/bin/                             0.1s
 => [stage-1 6/7] COPY --from=builder /app .                                                      0.1s
 => [stage-1 7/7] RUN chown -R appuser:appgroup /home/appuser                                     0.5s
 => exporting to image                                                                            2.7s
 => => exporting layers                                                                           1.5s
 => => naming to docker.io/112005/devops-python-app:latest                                        0.0s
```

### Run and Test Output
```bash
$ docker run -d -p 8080:8080 112005/devops-python-app:latest
$ curl http://localhost:8080/
{
  "service": {
    "name": "devops-info-service",
    "version": "1.0.0",
    "description": "DevOps course info service",
    "framework": "Flask"
  },
...
}
```

### Docker Hub Repository
[https://hub.docker.com/r/112005/devops-python-app](https://hub.docker.com/r/112005/devops-python-app)

## Technical Analysis

The `Dockerfile` is designed for both efficiency and security. The multi-stage build is key to keeping the final image small. If the layer order were changed (e.g., copying `app.py` before `requirements.txt`), every code change would invalidate the dependency layer cache, forcing `pip install` to run on every build, which would be much slower. Running as a non-root user is a critical security measure. The `.dockerignore` file prevents local development files from bloating the build context and the final image.

## Challenges & Solutions

A challenge was ensuring the file paths for the `COPY` instructions were correct, especially in the context of the build directory. Initially, the build failed because the context was not set correctly. This was resolved by running the `docker build` command from within the `app_python` directory, which simplified the paths.
