# DevOps Info Service

## Overview
Service provides system and service information built with FastAPI.

### Prerequisites

- Python 3.10 or higher
- pip

####  Dependencies
- **FastAPI**
- **Pydantic**
- **ColorLog**
- **pydantic-settings**
- **Uvicorn**

## Installation
Run the following commands to set up the environment:
```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```
Run the following command to run the application using Python:
```bash
python app.py
# Or with custom config
PORT=8080 python app.py
```
Or by using Uvicorn:
```bash
uvicorn app:app --host 0.0.0.0 --port 5000
```

## ⚙️ Configuration 

| Variable              | Default value              | Description                |
|-----------------------|----------------------------|----------------------------|
| `SERVICE_TITLE`       | devops-info-service        | Service title              |
| `SERVICE_VERSION`     | 1.0.0                      | Version of the application |
| `SERVICE_DESCRIPTION` | DevOps course info service | Service description        |
| `SERVICE_FRAMEWORK`   | FastAPI                    | Service framework          |
| `HOST`                | 0.0.0.0                    | Service host               |
| `PORT`                | 5000                       | Server port                |


## 📡 API Эндпоинты

### 1. Root endpoint

**GET** `/`
Returns information about the service, system, uptime, and request.

```json
{
  "service": {
    "name": "devops-info-service",
    "version": "1.0.0",
    "description": "DevOps course info service",
    "framework": "FastAPI"
  },
  "system": {
    "hostname": "DESKTOP-1J70LO4",
    "platform": "Windows",
    "platform_version": "10.0.26100",
    "architecture": "AMD64",
    "cpu_count": 16,
    "python_version": "3.11.7"
  },
  "runtime": {
    "uptime_seconds": 10,
    "uptime_human": "0 hours, 0 minutes",
    "current_time": "2026-01-28T18:59:11.516321",
    "timezone": "RTZ 2 (зима)"
  },
  "request": {
    "client_ip": "127.0.0.1",
    "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36",
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

### 2. Health Check endpoint

**GET** `/health`
Health check endpoint to monitor service status.
```json
{
  "status": "healthy",
  "timestamp": "2026-01-28T18:59:28.764449",
  "uptime_seconds": 27
}
```
