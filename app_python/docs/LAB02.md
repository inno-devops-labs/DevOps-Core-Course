# LAB02 — Docker Containerization

## 1. Docker Best Practices Applied

This project follows several Docker best practices:

### Non-root User
- The container runs under a non-root user to reduce security risks.
- Running as root inside containers can allow privilege escalation.

### Specific Base Image Version
- The image uses `python:3.13-slim`.
- A fixed version ensures reproducible and predictable builds.

### Layer Caching Optimization
- `requirements.txt` is copied before application source code.
- This allows Docker to reuse cached layers when dependencies do not change.

### .dockerignore
- Unnecessary files (venv, .git, cache files) are excluded.
- This reduces build context size and speeds up builds.

---

## 2. Image Information & Decisions

- **Base image:** python:3.13-slim  
- **Reason:** official, stable, minimal size, good compatibility
- **Final image size:** 47.9 MB
- **Optimization choices:**
  - slim image variant
  - minimal OS packages
  - clean layer ordering

---

## 3. Build & Run Process

### Image Build & Running Container

You can see outputs from image building and running container from the terminal in the screenshots:

- `04-docker-build-output.png`

- `05-docker-run-output.png`

### Endpoint Testing
```bash
curl http://localhost:5000/
curl http://localhost:5000/health
```

Also you can see screenshot of the output in `05-curl-output.png`

### Docker Hub

- Repository URL:
https://hub.docker.com/r/amirhan3228/devops-info-service

---

## 4. Technical Analysis

- The Dockerfile works by installing dependencies first and then copying source code.

- Changing layer order would invalidate cache and slow rebuilds.

- Security is improved by running as a non-root user.

- `.dockerignore` reduces build context size and prevents leaking unnecessary files.

---

## 5. Challenges & Solutions

### Issue: Docker build errors

- Cause: incorrect file paths or missing dependencies

- Solution: verified Dockerfile paths and rebuilt image

---

## Conclusion

The application was successfully containerized using Docker best practices.
The image is publicly available on Docker Hub and works identically to the local version.