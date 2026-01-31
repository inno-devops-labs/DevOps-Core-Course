# DevOps Info Service

A comprehensive FastAPI-based service providing system information and health status for DevOps monitoring and course demonstrations.

## Features

- **System Information**: Hostname, platform, architecture, CPU count, and Python version
- **Runtime Metrics**: Service uptime and current timestamp
- **Request Details**: Client IP, user agent, HTTP method, and path information
- **Health Monitoring**: Dedicated health check endpoint for orchestration systems
- **Interactive Documentation**: Auto-generated Swagger UI and ReDoc interfaces

## Endpoints

- `GET /` - Comprehensive service and system information
- `GET /health` - Health check endpoint (for Kubernetes probes, load balancers)
- `GET /docs` - Interactive API documentation (Swagger UI)
- `GET /redoc` - Alternative API documentation (ReDoc)

## Requirements

- Python 3.13+
- FastAPI
- Uvicorn
- See `requirements.txt` for complete dependencies

## Local Development

### Installation

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Linux/Mac:
source venv/bin/activate
# On Windows:
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Running the Service

```bash
# Run with default settings (port 8000)
python app.py

# Run with custom port
PORT=8080 python app.py

# Run in debug mode
DEBUG=true python app.py
```

The service will be available at:
- Main endpoint: http://localhost:8000/
- API docs: http://localhost:8000/docs
- Health check: http://localhost:8000/health

## Docker

This application is containerized and available as a Docker image for easy deployment across different environments.

### Building the Image

To build the Docker image locally:

```bash
docker build -t <your-username>/devops-info-service:<tag> .
```

**Example:**
```bash
docker build -t myuser/devops-info-service:1.0.0 .
docker build -t myuser/devops-info-service:latest .
```

### Running a Container

To run the containerized application:

```bash
docker run -d -p <host-port>:8000 --name <container-name> <image-name>:<tag>
```

**Example:**
```bash
# Run in detached mode on port 8000
docker run -d -p 8000:8000 --name devops-info myuser/devops-info-service:latest

# Run on a different port (e.g., 8080)
docker run -d -p 8080:8000 --name devops-info myuser/devops-info-service:latest

# Run with environment variables
docker run -d -p 8000:8000 -e DEBUG=true --name devops-info myuser/devops-info-service:latest
```

### Pulling from Docker Hub

To pull and run the pre-built image from Docker Hub:

```bash
docker pull <username>/devops-info-service:<tag>
docker run -d -p <host-port>:8000 <username>/devops-info-service:<tag>
```

**Example:**
```bash
# Pull specific version
docker pull myuser/devops-info-service:1.0.0

# Pull latest version
docker pull myuser/devops-info-service:latest

# Run the pulled image
docker run -d -p 8000:8000 myuser/devops-info-service:latest
```

### Verifying the Container

Once running, verify the service is working:

```bash
# Check container status
docker ps

# View container logs
docker logs <container-name>

# Test the health endpoint
curl http://localhost:8000/health

# Test the main endpoint
curl http://localhost:8000/
```

### Docker Image Features

- **Multi-stage build** for optimized image size
- **Non-root user** for enhanced security
- **Health checks** built into the image
- **Layer caching** optimized for faster builds
- **Minimal base image** (python:3.13-slim)

For detailed Docker implementation documentation, see `docs/LAB02.md`.

## Environment Variables

- `HOST` - Server host (default: `0.0.0.0`)
- `PORT` - Server port (default: `8000`)
- `DEBUG` - Enable debug mode (default: `false`)

## Testing

```bash
# Test main endpoint
curl http://localhost:8000/

# Test health endpoint
curl http://localhost:8000/health

# Using httpie (alternative)
http http://localhost:8000/
http http://localhost:8000/health
```

## Production Deployment

### With Docker Compose

```yaml
version: '3.8'
services:
  devops-info:
    image: <username>/devops-info-service:latest
    ports:
      - "8000:8000"
    environment:
      - DEBUG=false
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "python", "-c", "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')"]
      interval: 30s
      timeout: 3s
      retries: 3
```


## License

Educational project for DevOps course demonstrations.

## Contributing

This is an educational project. Feel free to use it as a reference for learning Docker and FastAPI basics.
