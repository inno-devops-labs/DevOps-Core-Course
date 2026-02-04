# Lab 2 — Docker Containerization

## Docker Best Practices Applied

- **Specific base image version**  
  Used `python:3.12-slim` as a lightweight official Python image. Using a specific version makes builds reproducible and avoids unexpected changes when the latest tag is updated.

- **Layer caching with requirements.txt**  
  `requirements.txt` is copied and dependencies are installed before copying the application code. This allows Docker to reuse the dependency layer when only the code changes, speeding up rebuilds.

- **Non-root user**  
  A dedicated non-root user `appuser` is created and the application is started under this user. Running containers as non-root reduces the impact of potential security vulnerabilities.

- **Minimal file copy**  
  Only the files required at runtime are copied into the image (`requirements.txt` and `app.py`). Test files, documentation, and development artifacts are excluded via `.dockerignore`. This reduces image size and attack surface.

- **Environment variables for Python**  
  `PYTHONDONTWRITEBYTECODE` and `PYTHONUNBUFFERED` are set to prevent `.pyc` creation and to ensure unbuffered output, which is useful for logging in containers.

## Image Information & Decisions

- **Base image:** `python:3.12-slim`  
  Chosen as a good balance between size and compatibility. The slim image is smaller than the full Python image but still based on Debian.

- **Layer structure:**  
  1. Pull base image  
  2. Set environment variables  
  3. Set working directory  
  4. Create non-root user  
  5. Copy `requirements.txt` and install dependencies  
  6. Copy application code  
  7. Switch to non-root user  
  8. Set default command

- **Optimization choices:**  
  - `--no-cache-dir` for pip  
  - `.dockerignore` excludes `venv`, `.git`, `docs`, `tests`, etc.  
  - Running as non-root user

## Build & Run Process

### Build

```bash
docker build -t devops-info-service:lab2 .
```

### Run locally

```bash
docker run --rm -p 5000:5000 devops-info-service:lab2
```

### Test endpoints

```bash
curl http://localhost:5000/
curl http://localhost:5000/health
```

### Docker Hub repository

Image is available at:  
https://hub.docker.com/r/fayzullin/devops-info-service


Tag used:  
```bash
fayzullin/devops-info-service:lab2
```

### Technical Analysis

The Dockerfile installs dependencies before copying the application code. If the order was reversed, any code change would force dependencies to be reinstalled on every build. Running as a non-root user improves security, and .dockerignore reduces the build context size, making builds faster and images smaller. Additionally, running the container as a non-root user reduces the potential impact of container escape vulnerabilities and follows Docker security best practices.  


### Challenges & Solutions

**Challenge:** Understanding how layer caching influences build speed.  
**Solution:** Reordered layers so that dependency installation is separated from application code.

**Challenge:** Running the app as a non-root user.  
**Solution:** Created a dedicated appuser user and switched to it using the USER directive.

**Challenge:** Reducing image size.  
**Solution:** Used python:3.12-slim, disabled pip cache, and excluded unnecessary files via .dockerignore.
