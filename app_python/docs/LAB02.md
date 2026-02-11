# Lab 02 - Docker Containerization

## Docker best practices applied

### non-root user

- created dedicated appuser with useradd
- switched to appuser before running application
- prevents container escape vulnerabilities and limits damage if app is compromised

### specific base image version

- used python:3.13-slim instead of python:latest
- ensures reproducible builds across environments
- slim variant reduces image size by ~100mb compared to full image

### layer caching optimization

- copied requirements.txt before application code
- pip install runs only when dependencies change
- application code changes dont invalidate dependency layer

### dockerignore usage

- excludes venv, pycache, docs, tests from build context
- reduces build time and context size
- prevents accidental inclusion of development artifacts

### minimal file copying

- only app.py and requirements.txt copied to final image
- no documentation or test files in production container

## Image information and decisions

### base image selection

- chose python:3.13-slim over alpine because:
  - better compatibility with pip packages
  - includes necessary c libraries for common dependencies
  - smaller than full python image (~150mb vs ~1gb)
  - more stable than alpine for python workloads

### final image size

![[image size]](screenshots/python_size.png)

### layer structure

1. base image (python:3.13-slim)
2. workdir creation
3. user creation
4. requirements copy
5. pip install
6. app copy
7. ownership change
8. user switch

## Build and run process

### build output

![[image build]](screenshots/python_build.png)

### run output and endpoint testing

![[run output and endpoint testing]](screenshots/run_curl_python.png)

### docker hub

- repository url: https://hub.docker.com/r/mashfeii/devops-info-service
  ![[screenshot of docker hub repositories page]](screenshots/docker_hub.png)

## Technical analysis

### why layer order matters

- docker caches each layer and reuses unchanged layers
- placing rarely-changing instructions first maximizes cache hits
- requirements.txt changes less often than app.py
- rebuilding after code change only reruns COPY app.py and later layers

### security implications of non-root

- root user in container has root-like privileges on host in some configurations
- non-root user limits blast radius of security vulnerabilities
- follows principle of least privilege
- required for many kubernetes security policies

### dockerignore benefits

- smaller build context means faster builds
- prevents secrets from accidentally being included
- reduces attack surface by excluding unnecessary files
- keeps image focused on runtime requirements only

## Challenges and solutions

### challenge 1: layer caching

- initially copied all files at once, causing full rebuild on every change
- solution: split COPY into requirements.txt first, then app.py

### challenge 2: permissions

- app files owned by root after COPY
- solution: added chown command before switching to appuser
