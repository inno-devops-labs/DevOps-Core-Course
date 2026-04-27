# DevOps Info Service

![Python CI](https://github.com/wkwtfigo/DevOps-Core-Course/actions/workflows/python-ci.yaml/badge.svg)

## Overview
The **DevOps Info Service** is a simple web service built with **FastAPI** that provides system information, including:
- Service metadata (name, version, description)
- System details (hostname, platform, CPU count, etc.)
- Runtime details (uptime, current time, timezone)
- A health check endpoint for monitoring the application's status

## Prerequisites
- **Python version:** 3.8 or higher
- **Dependencies:** See `requirements.txt` for the exact package versions.

## Installation
To set up the project locally, follow these steps:

1. **Create a virtual environment:**
    ```bash
    python -m venv venv
    ```

2. **Activate the virtual environment:**
    - On Windows:
      ```bash
      .\venv\Scripts\activate
      ```
    - On Mac/Linux:
      ```bash
      source venv/bin/activate
      ```

3. **Install dependencies:**
    for running the app:
    ```bash
    pip install -r requirements.txt
    ```
    for tests/lint:
    ```bash
    pip install -r requirements.txt -r requirements-dev.txt
    ```

## Running the Application
To run the app locally on the default host and port (`127.0.0.1:5000`):

```bash
python app.py
```

or with a custom port

```bash
$env:PORT="8080" python app.py   # PowerShell
export PORT=8080 && python app.py # bash (Linux/Mac)
```

## API Endpoints

<code>GET /</code>

Returns comprehensive information about the service, system, and runtime.

Example response:

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
    "python_version": "3.9.6"
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

<code>GET /health</code>

Returns a simple health status, useful for monitoring and Kubernetes probes.

Example response:

```json
{
  "status": "healthy",
  "timestamp": "2024-01-15T14:30:00.000Z",
  "uptime_seconds": 3600
}
```

## Configuration

The following environment variables can be configured to change the application behavior:

|Variable|	Description|	Default Value|
|------|---|----|
|HOST	|Host |IP address|	0.0.0.0|
|PORT	|Port number|	5000|
|DEBUG	|Enable/Disable |debug mode|	False|

## Testing

Install dev dependencies:
```bash
pip install -r requirements.txt -r requirements-dev.txt
```

Run unit tests:

```bash
pytest -q
```

## Docker

### Build locally
Pattern:
- Build an image from the Dockerfile in this directory:
  - `docker build -t <image_name>:<tag> .`

Notes:
- Local builds do not require Docker Hub naming. Example image name: `devops-info-service:lab02`.

### Run locally
Pattern:
- Run and publish the container port:
  - `docker run --rm --name <container_name> -p <host_port>:5000 <image_name>:<tag>`

Example:
- `docker run --rm --name devops-info -p 5000:5000 devops-info-service:lab02`

Optional environment overrides (if needed):
- `-e HOST=<host> -e DEBUG=<TRUE|FALSE>`

Note:
- The container is designed to listen on port **5000** by default. It is recommended to keep the internal port unchanged and only remap the host port using `-p`.

### Pull from Docker Hub
Pattern:
- Pull:
  - `docker pull <dockerhub_username>/<repo_name>:<tag>`
- Run:
  - `docker run --rm -p <host_port>:5000 <dockerhub_username>/<repo_name>:<tag>`
