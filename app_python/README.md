# devops info service

a python web service that provides detailed information about itself and its runtime environment

## overview

this service exposes two endpoints that return json data about the system, service metadata, and health status

## prerequisites

- python 3.11 or higher
- pip package manager

## installation

```bash
# create virtual environment
python -m venv venv

# activate virtual environment
source venv/bin/activate  # linux/macos
# or
venv\Scripts\activate  # windows

# install dependencies
pip install -r requirements.txt
```

## running the application

```bash
# default configuration (0.0.0.0:5000)
python app.py

# custom port
PORT=8080 python app.py

# custom host and port
HOST=127.0.0.1 PORT=3000 python app.py

# enable debug mode
DEBUG=true python app.py
```

## api endpoints

### get /

returns comprehensive service and system information

**response example:**

```json
{
  "service": {
    "name": "devops-info-service",
    "version": "1.0.0",
    "description": "DevOps course info service",
    "framework": "Flask"
  },
  "system": {
    "hostname": "my-laptop",
    "platform": "Darwin",
    "platform_version": "Darwin-24.6.0-arm64",
    "architecture": "arm64",
    "cpu_count": 8,
    "python_version": "3.13.1"
  },
  "runtime": {
    "uptime_seconds": 3600,
    "uptime_human": "1 hours, 0 minutes",
    "current_time": "2026-01-27T14:30:00.000000+00:00",
    "timezone": "UTC"
  },
  "request": {
    "client_ip": "127.0.0.1",
    "user_agent": "curl/8.1.2",
    "method": "GET",
    "path": "/"
  },
  "endpoints": [
    { "path": "/", "method": "GET", "description": "Service information" },
    { "path": "/health", "method": "GET", "description": "Health check" }
  ]
}
```

### get /health

returns service health status for monitoring

**response example:**

```json
{
  "status": "healthy",
  "timestamp": "2026-01-27T14:30:00.000000+00:00",
  "uptime_seconds": 3600
}
```

## configuration

| variable | default | description         |
| -------- | ------- | ------------------- |
| HOST     | 0.0.0.0 | server bind address |
| PORT     | 5000    | server port         |
| DEBUG    | false   | enable debug mode   |

## testing

```bash
# test main endpoint
curl http://localhost:5000/

# test health endpoint
curl http://localhost:5000/health

# pretty print json output
curl http://localhost:5000/ | python -m json.tool
```

## docker

### building the image

```bash
docker build -t devops-info-service .
```

### running the container

```bash
docker run -p 5173:5173 devops-info-service
```

### pulling from docker hub

```bash
docker pull mashfeii/devops-info-service:latest
docker run -p 5173:5173 mashfeii/devops-info-service:latest
```
