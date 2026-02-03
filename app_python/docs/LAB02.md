# LAB 02 — Docker Containerization

## 1. Docker Best Practices Applied

* **Non-root User:** I used ``useradd`` (Python) to create a specific user. Running as root allows a potential attacker to gain full control over the host if the container is compromised.
* **Specific Base Images:** Instead of ``latest``, I used ``python:3.13-slim``. This prevents breaking changes when new versions are released and ensures build reproducibility.
* **Layer Ordering:** I copied ``requirements.txt`` and installed dependencies before copying the application code. This leverages Docker's layer caching; subsequent builds will skip dependency installation unless the files change.
* **Multi-stage Builds (Go):** The Go application is compiled in a heavy image and then moved to a tiny Alpine image. This drastically reduces the attack surface and image size.
* **Small Base Images:** Choosing ``slim`` and ``alpine`` variants reduced the image size by avoiding unnecessary build tools and headers in the final production image.

## 2. Image Information

* **Base image**: `python:3.13-slim` was chosen as a balance between size and compatibility.
* **Optimization**: Used ``.dockerignore`` to keep build context clean and ``--no-cache-dir`` for pip to save space.


## 3. Build & Run Process

**Build image:**

```bash
docker build -t devops-info-service:lab02 .
```

**Run container:**

```bash
docker run -p 8080:8080 devops-info-service:lab02
```

**Test endpoints:**

```bash
curl http://localhost:8080/
curl http://localhost:8080/health
```

**Docker Hub repository:**

```
https://hub.docker.com/r/<your-username>/devops-info-service
```

## 4. Technical Analysis

### What happens if we change the layer order?

If ``COPY . .`` is placed before ``RUN pip install``, every single code change (even a comment) will invalidate the cache for the dependency layer. Docker will be forced to re-download and re-install all libraries every time you build, significantly increasing build time.

**Security Considerations**

* **Non-root user:** Prevents privilege escalation.

* **Minimal Image:** Fewer binaries inside the container means fewer tools for an attacker to use (e.g., ``curl``, ``apt``, ``gcc`` are missing in the final Go image).

## 5. Challenges & Solutions

During testing, the container was initially unreachable due to a port mismatch between the application and Docker port mapping. This was resolved by configuring the application port via an environment variable and updating the exposed port in the Dockerfile.

## 6. Docker Hub
Repository URL: https://hub.docker.com/repository/docker/ray326sq/devops-info-service/general