# DevOps Course Info Service

## Overview

DevOps Info Service - small Flask based service what return and report system metadata and information.

## Prerequisites
- Python 3.11+
- pip 
-  Linux / macOS / Windows

## Installation guid

1. Clone the repository:
   ```bash
   git clone git@github.com:setterwars/DevOps-Core-Course.git
   
2. Navigate to the project directory:
   ```bash
   cd app_python

3. (Optional) Create and activate a virtual environment:
   ```bash
    python3 -m venv venv

4. Install the required dependencies:
   ```bash
   pip install -r requirements.txt

5. Run the application:
    ```bash
    python3 app.py # in default mode
    PORT=8080 HOST=127.0.0.1 DEBUG=True python3 app.py # in custom mode

## Available Endpoints
- `GET /` - Returns system metadata including hostname, IP address, and current timestamp.
- `GET /health` - Returns the health status of the service.


## Docker 

### Build the image locally (pattern)
```bash
docker build -t ${DOCKER_USER}devops-info-service-python:latest
```

### Run a container (pattern)
```bash
docker run --rm \
   -p 5000:5000 \
   -e HOST=0.0.0.0 \
   -e PORT=5000 \
   -e DEBUG=True \
   ${DOCKER_USER}/devops-info-service-python:latest
```

### Pull from Docker Hub
Link to docker hub: 

https://hub.docker.com/repository/docker/zsalavat/devops-info-service-python/general

```bash
docker pull zsalavat/devops-info-service-python
docker run --rm -p 5000:5000 zsalavat/devops-info-service-python:latest
```

