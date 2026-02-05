# devops info service

a web application providing detailed information about itself and its runtime environment. built with FastAPI as part of the devops course labs.

## overview

the devops info service is a monitoring foundation that reports system information and health status. this service will evolve throughout the course into a comprehensive monitoring tool with containerization, CI/CD, monitoring, and persistence capabilities.

## prerequisites

- python 3.11 or higher
- pip (python package manager)

## installation

1. create a virtual environment:
   ```bash
   python3 -m venv .venv
   ```

2. activate the virtual environment:

   ```bash
   source venv/bin/activate
   ```

3. install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## running the application

start the application with default configuration:

```bash
python app.py
```

or with custom configuration:

```bash
HOST=127.0.0.1 PORT=3000 DEBUG=True python app.py
```

the service will be available at `http://localhost:5000` (or the configured port).

## API endpoints

### `GET /`

returns comprehensive service and system information.

**example response:**
```json
{
  "service": {
    "name": "devops-info-service",
    "version": "1.0.0",
    "description": "DevOps course info service",
    "framework": "FastAPI"
  },
  "system": {
    "hostname": "s-razmakhov",
    "platform": "Darwin",
    "platform_version": "macOS-26.2-arm64-arm-64bit",
    "architecture": "arm64",
    "cpu_count": 12,
    "python_version": "3.9.6"
  },
  "runtime": {
    "uptime_seconds": 2,
    "uptime_human": "2 seconds",
    "current_time": "2026-01-28T20:07:01.956014+00:00",
    "timezone": "UTC"
  },
  "request": {
    "client_ip": "127.0.0.1",
    "user_agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36",
    "method": "GET",
    "path": "/"
  },
  "endpoints": [
    {
      "path": "/",
      "method": "GET",
      "description": "Service information"
    },
    {
      "path": "/health",
      "method": "GET",
      "description": "Health check"
    }
  ]
}
```

### `GET /health`

simple health check endpoint for monitoring and Kubernetes probes.

**example response:**
```json
{
  "status": "healthy",
  "timestamp": "2026-01-28T20:08:16.012061+00:00",
  "uptime_seconds": 76
}
```

## configuration

the application can be configured via environment variables:

| variable | default | description |
|----------|---------|-------------|
| `HOST` | `0.0.0.0` | host to bind the server to |
| `PORT` | `5000` | port to listen on |
| `DEBUG` | `False` | enable debug mode with auto-reload |

## docker

### building the image

build the docker image from the `app_python` directory:

```bash
docker build -t devops-info-service .
```

### running the container

run the container with port mapping:

```bash
docker run -d -p 5000:5000 devops-info-service
```

### pulling from docker hub

pull the image from docker hub:

```bash
docker pull onemoreslacker/devops-info-service:v0
```

run the pulled image:

```bash
docker run -d -p 5000:5000 onemoreslacker/devops-info-service:v0
```

## testing

```bash
# get main endpoint
curl http://localhost:5000/

# get health check
curl http://localhost:5000/health

# 404 not found
curl http://localhost:5000/devops
```
