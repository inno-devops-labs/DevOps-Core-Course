## DevOps Info Service

![Python CI/CD Pipeline](https://github.com/AliyaSag/DevOps-Core-Course/actions/workflows/python-ci.yml/badge.svg)

### Overview

A simple web application built with **Flask** that provides comprehensive system introspection, runtime information, and health status. This project serves as a foundation for learning DevOps practices including CI/CD, containerization, and monitoring.

### Prerequisites

- **Python** 3.10+
- **pip** (Python package manager)

### Installation

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Running the Application

The application runs on `0.0.0.0:5000` by default.

Custom Configuration
You can change the host and port using environment variables.

```bash
$env:PORT=8080; python app.py
```

### API Endpoints

1. System Information
- URL: GET /
- Description: Returns detailed JSON about the service, system, runtime, and current request.
- Example Response:

```json
{
  "service": { "name": "devops-info-service", "version": "1.0.0" },
  "system": { "platform": "Windows", "python_version": "3.12.0" },
  "runtime": { "uptime_human": "0 hour, 5 minutes" }
}
```
2. Health Check
- URL: GET /health
- Description: Lightweight endpoint for liveness/readiness probes.
- Example Response:

```json
{
  "status": "healthy",
  "timestamp": "2026-01-28T16:20:00+00:00",
  "uptime_seconds": 300
}
```
### Configuration

| Variable | Description                     | Default |
| -------- | ------------------------------- | ------- |
| HOST     | Interface to bind the server to | 0.0.0.0 |
| PORT     | Port number to listen on        | 5000    |

## Docker Containerization

### Building the Image Locally
```bash
docker build -t <image-name>:<tag> .

### Running the Container

```bash
# Run with default port mapping
docker run -p <host-port>:<container-port> --name <container-name> <image-name>:<tag>

# Run with environment variables
docker run -p <host-port>:<container-port> -e PORT=<port> -e HOST=<host> --name <container-name> <image-name>:<tag>
```

### Pulling from Docker Hub

```bash
# Pull the image from Docker Hub
docker pull <dockerhub-username>/<repository-name>:<tag>

# Run the pulled image
docker run -p <host-port>:<container-port> <dockerhub-username>/<repository-name>:<tag>
```

### Examples

```bash
# Build locally
docker build -t devops-info-service:latest .

# Run locally built image
docker run -d -p 5000:5000 --name devops-service devops-info-service:latest

# Pull from Docker Hub and run
docker pull aliyasag/devops-info-service:latest
docker run -d -p 8080:5000 --name devops-hub aliyasag/devops-info-service:latest
```

### Container Management

```bash
# List running containers
docker ps

# List all containers
docker ps -a

# View container logs
docker logs <container-name>

# Stop a container
docker stop <container-name>

# Remove a container
docker rm <container-name>

# Remove an image
docker rmi <image-name>:<tag>
```

## Lab 6 Status
[![Ansible Deployment](https://github.com/AliyaSag/DevOps-Core-Course/actions/workflows/ansible-deploy.yml/badge.svg)](https://github.com/AliyaSag/DevOps-Core-Course/tree/lab6-advanced-ansible/.github/workflows)
