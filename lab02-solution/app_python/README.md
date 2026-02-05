# DevOps Info Service - Containerized

A FastAPI-based microservice providing system and runtime information, containerized using Docker best practices.

## Overview

This application exposes two REST API endpoints:
- `GET /` - Returns comprehensive service, system, and runtime information
- `GET /health` - Health check endpoint for monitoring and liveness probes

## Docker Usage

### Building the Image Locally

Build the image with a specific tag:

```bash
docker build -t devops-info-service:1.0.0 .
```

Or build with your Docker Hub username for pushing later:

```bash
docker build -t <your-docker-username>/devops-info-service:1.0.0 .
```

### Running a Container

Run the container with port mapping to access the service from your host machine:

```bash
docker run -d -p 8000:8000 --name my-service devops-info-service:1.0.0
```

**Parameters explained:**
- `-d` - Run in detached mode (background)
- `-p 8000:8000` - Map port 8000 from container to host
- `--name my-service` - Give the container a friendly name

### Accessing the Service

Once the container is running, access the endpoints:

```bash
# Get service info
curl http://localhost:8000/

# Get health status
curl http://localhost:8000/health
```

### Pulling from Docker Hub

To pull and run the image from Docker Hub:

```bash
docker pull <your-docker-username>/devops-info-service:1.0.0
docker run -d -p 8000:8000 <your-docker-username>/devops-info-service:1.0.0
```

### Viewing Logs

To see the application logs from a running container:

```bash
docker logs -f my-service
```

### Stopping and Removing the Container

Stop a running container:

```bash
docker stop my-service
```

Remove a stopped container:

```bash
docker rm my-service
```

## Docker Best Practices Applied

This Dockerfile implements several production-ready practices:

1. **Specific Base Image Version** - Uses `python:3.13-slim` (not `latest`) for reproducibility
2. **Non-Root User** - Application runs as unprivileged `appuser` (UID 1000) for security
3. **Layer Caching Optimization** - Dependencies copied and installed before application code
4. **Minimal .dockerignore** - Excludes unnecessary files from build context for faster builds
5. **Security Hardening** - No root access, health checks enabled
6. **Slim Base Image** - Uses python:3.13-slim (not full image) to reduce final size

## Image Information

- **Base Image:** python:3.13-slim
- **Final Size:** ~260MB
- **Non-Root User:** appuser (UID: 1000)
- **Port:** 8000

## Development

For local development without Docker:

```bash
pip install -r requirements.txt
python app.py
```

The application will start on `http://localhost:8000` with DEBUG mode enabled by default when running directly.
