# Python Web Server

## Overview

This web server provides information about itself and its environment.

## Prerequisites

- Python 3.14.0
- pip
- git
## Installation

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Running the Application

You can create `.env` file storing all enviroment values. To run application simply type:

```bash
python app.py
```

## Docker Support

### Building from Source

Create a Docker image locally from the application code:

```bash
docker build -t <image-name>:<tag> .
```

### Container Execution

Run the application in an isolated container environment:

```bash
docker run --rm -p <host-port>:<container-port> --name <container-name> <image-name>:<tag>
```


### Using Pre-built Images

The service is also available on Docker Hub for immediate deployment:

```bash
# Download the published image
docker pull abrahambarrett228/lab02

# Run the downloaded image
docker run --rm -p 5000:5000 abrahambarrett228/lab02
```

### Container Management

Basic operations for container lifecycle management:

```bash
# List running containers
docker ps

# Stop a running container
docker stop <container-name>

# View container logs
docker logs <container-name>

# Interactive shell access
docker exec -it <container-name> /bin/sh
```

## API Endpoints

- `GET /` - service data 
- `GET /health` - Health check

## Configuration

Supported enviroment values:

- `HOST` - address of the application
- `PORT` - port of the application
- `DEBUG` - `[true/false]` do/don't enable debug features