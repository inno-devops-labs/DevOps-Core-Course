# DevOps Info Service

A FastAPI-based web service providing detailed information about the service, system, and runtime environment.

## Overview

This service is part of the DevOps course and provides:
- Comprehensive system information
- Health check endpoint for monitoring
- Runtime statistics
- Automatic OpenAPI documentation

## Prerequisites

- Python 3.11 or higher
- pip (Python package manager)

## Installation

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd app_python
   ```

2. Create and activate virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Running the Application

### Basic usage:
```bash
python app.py
```

### With custom configuration:
```bash
# Custom port
PORT=8080 python app.py

# Custom host and port
HOST=127.0.0.1 PORT=3000 python app.py

# Enable debug mode
DEBUG=true python app.py
```

### Using uvicorn directly:
```bash
uvicorn app:app --host 0.0.0.0 --port 5000 --reload
```

### Testing

Test the endpoints using curl:

```bash
# Get service info
curl http://localhost:5000/

# Health check
curl http://localhost:5000/health

# Pretty-print JSON output
curl http://localhost:5000/ | python -m json.tool
```

## API Endpoints

### GET `/`
Returns comprehensive service and system information.

**Example Response:**
```json
{
  "service": {
    "name": "devops-info-service",
    "version": "1.0.0",
    "description": "DevOps course info service",
    "framework": "FastAPI"
  },
  "system": {
    "hostname": "my-laptop",
    "platform": "Linux",
    "platform_version": "Ubuntu 24.04",
    "architecture": "x86_64",
    "cpu_count": 8,
    "python_version": "3.13.1"
  },
  "runtime": {
    "uptime_seconds": 3600,
    "uptime_human": "1 hour, 0 minutes",
    "current_time": "2026-01-07T14:30:00.000Z",
    "timezone": "UTC"
  },
  "request": {
    "client_ip": "127.0.0.1",
    "user_agent": "curl/7.81.0",
    "method": "GET",
    "path": "/"
  },
  "endpoints": [
    {"path": "/", "method": "GET", "description": "Service information"},
    {"path": "/health", "method": "GET", "description": "Health check"}
  ]
}
```

### GET `/health`
Health check endpoint for monitoring and Kubernetes probes.

**Example Response:**
```json
{
  "status": "healthy",
  "timestamp": "2024-01-15T14:30:00.000Z",
  "uptime_seconds": 3600
}
```

## Configuration

The application can be configured using environment variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `HOST` | `0.0.0.0` | Host to bind the server to |
| `PORT` | `5000` | Port to listen on |
| `DEBUG` | `False` | Enable debug mode and hot reload |

## Docker Containerization

This application is containerized and available on Docker Hub.

### Building Locally

```bash
# Clone the repository
git clone <repository-url>
cd app_python

# Build Docker image
docker build -t devops-info-service:latest .
```

### Running the Container

```bash
# Basic run (maps host port 5000 to container port 5000)
docker run -d -p 5000:5000 --name devops-app devops-info-service:latest

# With custom port mapping (host:container)
docker run -d -p 8080:5000 --name devops-app devops-info-service:latest

# With environment variables
docker run -d \
  -p 5000:5000 \
  -e PORT=5000 \
  -e HOST=0.0.0.0 \
  -e DEBUG=false \
  --name devops-app \
  devops-info-service:latest

# Mount host directory for logs (optional)
docker run -d \
  -p 5000:5000 \
  -v $(pwd)/logs:/app/logs \
  --name devops-app \
  devops-info-service:latest
```

### Using Docker Hub

```bash
# Pull from Docker Hub
docker pull acecution/devops-info-service:latest

# Run from Docker Hub
docker run -d -p 5000:5000 acecution/devops-info-service:latest

# Run specific version
docker run -d -p 5000:5000 acecution/devops-info-service:v1.0.0
```

### Container Management

```bash
# List running containers
docker ps

# List all containers (including stopped)
docker ps -a

# View container logs
docker logs devops-app

# Follow logs in real-time
docker logs -f devops-app

# Execute commands inside container
docker exec -it devops-app sh
docker exec devops-app python -c "import fastapi; print(fastapi.__version__)"

# Inspect container details
docker inspect devops-app

# Stop container
docker stop devops-app

# Remove container
docker rm devops-app

# Force remove running container
docker rm -f devops-app

# Remove image
docker rmi devops-info-service:latest

# Clean up unused resources
docker system prune -a
```

### Image Information

- **Base Image**: Python 3.13-slim
- **Image Size**: ~123MB
- **Non-root User**: Runs as `appuser` for security
- **Health Checks**: Built-in health monitoring via `/health` endpoint
- **Port**: 5000 (configurable via `PORT` environment variable)
- **Architecture**: Multi-platform compatible (amd64, arm64)

### Dockerfile Features

- **Security**: Non-root user execution
- **Optimization**: Layer caching for faster builds
- **Minimal**: Only necessary packages installed
- **Production-ready**: Health checks, proper logging, environment variables
- **Reproducible**: Pinned Python version (3.13)

### Docker Hub

The image is available on Docker Hub: `acecution/devops-info-service`

**Tags**:
- `latest` - Most recent stable version
- `v1.0.0` - Version 1.0.0 (semantic versioning)

**Access**: 
- **Public Repository**: https://hub.docker.com/repository/docker/acecution/devops-info-service
- **Pull Count**: Automatically tracked by Docker Hub
- **Build History**: View previous builds and tags

### Security Features

1. **Non-root User**: Container runs as unprivileged `appuser`
2. **Minimal Base Image**: Reduced attack surface with Python slim
3. **No Build Tools**: Production image excludes compilers and dev tools
4. **Health Monitoring**: Built-in health checks for orchestration
5. **Environment Segregation**: Configuration via environment variables
6. **Immutable Infrastructure**: Container contents don't change at runtime

### Development Workflow

```bash
# 1. Build and test locally
docker build -t devops-info-service:latest .
docker run -d -p 5000:5000 --name test devops-info-service:latest
curl http://localhost:5000/health

# 2. Tag for Docker Hub
docker tag devops-info-service:latest acecution/devops-info-service:latest
docker tag devops-info-service:latest acecution/devops-info-service:v1.0.0

# 3. Push to registry
docker push acecution/devops-info-service:latest
docker push acecution/devops-info-service:v1.0.0

# 4. Deploy anywhere
docker pull acecution/devops-info-service:latest
docker run -d -p 5000:5000 acecution/devops-info-service:latest
```

### Troubleshooting

#### Container won't start
```bash
# Check logs
docker logs devops-app

# Check container status
docker ps -a | grep devops-app

# Run interactively to debug
docker run -it --rm devops-info-service:latest sh
```

#### Port already in use
```bash
# Find what's using the port
lsof -i :5000

# Use different port
docker run -d -p 8080:5000 --name devops-app devops-info-service:latest
```

#### Permission issues
```bash
# Build with --no-cache if permission issues
docker build --no-cache -t devops-info-service:latest .
```

#### Docker Hub authentication
```bash
# Login to Docker Hub
docker login

# Check current auth
docker info | grep Username
```

### Environment Variables Reference

| Variable | Default | Description | Required |
|----------|---------|-------------|----------|
| `PORT` | `5000` | Application port | No |
| `HOST` | `0.0.0.0` | Bind address | No |
| `DEBUG` | `false` | Enable debug mode | No |
| `PYTHONUNBUFFERED` | `1` | Python output unbuffered | No (set in Dockerfile) |

### Example Deployment Scenarios

#### Development
```bash
docker run -d \
  -p 5000:5000 \
  -e DEBUG=true \
  --name devops-app-dev \
  devops-info-service:latest
```

#### Production
```bash
docker run -d \
  -p 80:5000 \
  --restart unless-stopped \
  --name devops-app-prod \
  -e PORT=5000 \
  -e HOST=0.0.0.0 \
  -e DEBUG=false \
  devops-info-service:latest
```

#### With Docker Compose
Create `docker-compose.yml`:
```yaml
version: '3.8'
services:
  devops-app:
    image: devops-info-service:latest
    container_name: devops-app
    ports:
      - "5000:5000"
    environment:
      - PORT=5000
      - HOST=0.0.0.0
      - DEBUG=false
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:5000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 10s
```

### Best Practices Implemented

1. **✅ Non-root user**: Security first approach
2. **✅ .dockerignore**: Excludes unnecessary files
3. **✅ Layer caching**: Optimized build performance
4. **✅ Health checks**: Container orchestration ready
5. **✅ Environment variables**: Configurable at runtime
6. **✅ Minimal image**: Small footprint (~123MB)
7. **✅ Specific versions**: Reproducible builds
8. **✅ Proper logging**: Structured application logs

## Visits Counter

The application now tracks how many times the root endpoint (`/`) has been accessed.

- **Endpoint:** `GET /visits` returns the current visit count.
- **Persistence:** The counter is stored in a file at `/data/visits`.
- When running with Docker Compose, a local directory is mounted to preserve the counter across restarts.
- In Kubernetes, a PersistentVolumeClaim is used to store the data.

**Example response:**
```json
{"visits": 42}
```

### Testing Locally

```bash
mkdir data
docker compose up -d
curl http://localhost:8000/          # increments
curl http://localhost:8000/visits
docker compose restart
curl http://localhost:8000/visits    # value preserved
```

### In Kubernetes

After deploying the Helm chart, access the service and check:

```bash
curl http://$(minikube ip):30080/visits
```