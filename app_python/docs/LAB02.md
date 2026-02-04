# LAB02 — Dockerizing Python App

### Docker Best Practices Applied
#### - Layer Caching Optimized

Docker caches layers during image builds. Since dependencies are installed before copying application source code, cached layers are reused when only application code changes

```Dockerfile
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
```

#### - Non-root User

A non-root user was created. This improves security by reducing the impact of a potential container compromise.

```Dockerfile
RUN groupadd -r appuser && useradd -r -g appuser appuser
USER appuser
```

#### - Minimal Base Image

The `python:3.12-slim` image was chosen to reduce image size while maintaining compatibility

```Dockerfile
FROM python:3.12-slim
```

#### - .dockerignore Usage

Unnecessary files such as `.env`, cache, and code env metadata are excluded from the build context to improve build speed and image cleanliness.

### Image Information & Decisions
#### - Base image choice
The `python:3.12-slim` image was selected because it provides a balance between small image size and ease of dependency installation compared to Alpine images
Image Size

#### - Image  size
Final image size: **~150 MB**
This size is acceptable for a Python application and reflects the use of a slim base image and cache-free dependency installation

#### - Layer Structure
- Base image
- System configuration and user creation
- Dependency installation
- Application source code
- Runtime configuration

#### Optimizations
- Reduced number of layers
- Cache-efficient COPY order
- No package manager cache retained

### Build & Run Process
#### Build process
![[screenshots/build.png]]
#### Running dockerized app
![[screenshots/run.png]]

### Technical Analysis
#### Dockerfile Behavior
The Dockerfile is structured to maximize build cache reuse and minimize image size while ensuring secure execution using a non-root user.

#### Layer Order Impact
If application files were copied before dependency installation, every code change would invalidate the cache and force a full dependency reinstall.

#### Security Considerations
- Non-root user execution
- Minimal base image
- No unnecessary or sensitive files included in image

#### .dockerignore Benefits
The .dockerignore file reduces build context size, speeds up builds, and prevents accidental inclusion of sensitive or unnecessary files