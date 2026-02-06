# DevOps Info Service

![Python CI/CD](https://github.com/sayfetik/DevOps-Core-Course/actions/workflows/python-ci.yml/badge.svg)

## Overview

DevOps Info Service is a simple production-ready Python web application that provides detailed information about the running service, system environment, and runtime state. The service is designed for DevOps practices such as monitoring, health checks, and container readiness probes.

## Prerequisites

* Python 3.10 or higher
* pip (Python package manager)
* Git

## Installation

Clone the repository and navigate to the Python application directory:

```bash
cd app_python
```

Create and activate a virtual environment:

```bash
python3 -m venv venv
source venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```


## Running the Application

Run with default configuration:

```bash
python app.py
```

Run with custom configuration using environment variables:

```bash
PORT=8080 python app.py
HOST=127.0.0.1 PORT=3000 python app.py
```

## Running Tests

To run unit tests locally:

1. Install all dependencies:
    ```bash
    pip install -r requirements.txt
    pip install -r requirements-dev.txt
    ```
2. Run tests with pytest:
    ```bash
    pytest
    ```
Tests are located in the `tests/` directory. All endpoints and error cases are covered.

## API Endpoints

### GET /

Returns service metadata, system information, runtime details, request information, and available endpoints.

### GET /health

Health check endpoint used for monitoring and Kubernetes probes. Returns service status, timestamp, and uptime.

## Configuration

The application can be configured using environment variables:

| Variable | Description                     | Default |
| -------- | ------------------------------- | ------- |
| HOST     | Host address to bind the server | 0.0.0.0 |
| PORT     | Port number for the service     | 5000    |
| DEBUG    | Enable debug mode (true/false)  | false   |

## Docker

### Building the Image

Build the Docker image locally:

```bash
docker build -t devops-info-service:latest .
```

Build with custom tag:

```bash
docker build -t <your-username>/devops-info-service:1.0.0 .
```

### Running a Container

Run the container with default configuration:

```bash
docker run -p 5000:5000 devops-info-service:latest
```

Run with custom environment variables:

```bash
docker run -p 8080:5000 -e PORT=5000 -e DEBUG=true devops-info-service:latest
```

Run in background mode:

```bash
docker run -d -p 5000:5000 --name my-app devops-info-service:latest
```

### Accessing the Application

Once the container is running, access the endpoints:

```bash
# Service information
curl http://localhost:5000/

# Health check
curl http://localhost:5000/health
```

### Pulling from Docker Hub

Pull and run the published image:

```bash
docker pull <your-username>/devops-info-service:latest
docker run -p 5000:5000 <your-username>/devops-info-service:latest
```

### Container Details

- **Base Image:** python:3.13-slim
- **Runs as:** Non-root user (appuser)
- **Default Port:** 5000
- **Health Check:** Enabled with 30-second intervals

See [docs/LAB02.md](./docs/LAB02.md) for detailed Docker implementation documentation.

## Project Structure

```text
app_python/
├── app.py
├── requirements.txt
├── .gitignore
├── README.md
├── tests/
│   └── __init__.py
└── docs/
    ├── LAB01.md
    └── screenshots/
```

## Notes

* Virtual environment directory (`venv/`) is excluded from version control
* All dependencies are pinned for reproducibility
* The application follows PEP 8 and clean code principles
