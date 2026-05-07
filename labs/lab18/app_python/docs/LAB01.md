# Lab 01

## Framework Selection

I choosed `Flask ` because, how it was stated, it is lightweight and I have already worked with it in my project, so it will be easier to use it than study new tools (even if I think that study new tools is great, I want to practice with Flask more).

| Framework | Pros | Cons |
|----------|--------|-------------|
| **Flask** | Lightweight, already know from previous project | Not so good choice for complex projects |
| **FastAPI** | Modern, async, auto-documentation | Complex and requires learning it |
| **Django** | Full-featured, includes ORM | Too complex, requires a lot to learn |


## Best Practices Applied
### Clean Code Organization
Clear code is easier to maintain and read. It's especially important when working in teams, as it reduces time spent understanding code rather than working on it. Additionally, when returning to a project after some time, clean code helps you quickly understand what's happening.

**Implementation:**
```python
# Clear function names with descriptive docstrings
def get_system_info():
    """Collect system information."""
    return {
        'hostname': socket.gethostname(),
        'platform': platform.system(),
        'architecture': platform.machine(),
        'python_version': platform.python_version()
    }

# Proper imports grouping
import os
import socket
import platform
from datetime import datetime, timezone
from flask import Flask, jsonify, request
import logging

# Comments only where needed
"""
DevOps Info Service
Main application module
"""
import os
...

# Configuration - clearly separated section
HOST = os.getenv('HOST', '0.0.0.0')
...

# Following PEP 8 style guide
def get_uptime():
    delta = datetime.now() - start_time
    seconds = int(delta.total_seconds())
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    return {
        'seconds': seconds,
        'human': f"{hours} hours, {minutes} minutes"
    }
```


### Error Handling
Error handling is crucial because it helps ensure your service works correctly. Good error handling allows you to identify issues during testing and provides users with meaningful error messages.
``` python
@app.errorhandler(404)
def not_found(error):
    return jsonify({
        'error': 'Not Found',
        'message': 'Endpoint does not exist'
    }), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({
        'error': 'Internal Server Error',
        'message': 'An unexpected error occurred'
    }), 500
```

### Logging
Logging is a crucial part of development. It shows what's happening in the code: events, errors, and other important information. This helps identify hidden issues and confirms that everything is working as expected.
``` python
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

logger.info('Application starting...')
logger.debug(f'Request: {request.method} {request.path}')
```

### Dependencies 
t's good practice to collect all project dependencies in a dedicated file. This makes it easier to maintain the project and deploy it to different machines.
```
Flask==3.1.0
```

### Git Ignore
It's good practice to exclude unnecessary files from your repository to keep it clean and organized.
```
# Python
__pycache__/
*.py[cod]
venv/
*.log

# IDE
.vscode/
.idea/

# OS
.DS_Store
```

## API Documentation
### GET / - Service Information

**Description**: Returns comprehensive service and system information including service metadata, system details, runtime statistics, and request information.

**Request:**
```bash
curl http://localhost:5000/
```

**Response:**
```bash
{
  "service": {
    "name": "devops-info-service",
    "version": "1.0.0",
    "description": "DevOps course info service",
    "framework": "Flask"
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

### GET /health - Health Check
**Description:** Simple endpoint for service monitoring and health checks.

**Request:**
```bash
curl http://localhost:5000/health
```

**Response:**
```
{
  "status": "healthy",
  "timestamp": "2024-01-15T14:30:00.000Z",
  "uptime_seconds": 3600
}
```

### Testing
#### Screenshots
In the proper folder. You can find them there.
#### Terminal output

**Starting the application:**
```
2026-01-27 23:28:29,367 - __main__ - INFO - Application starting...
2026-01-27 23:28:29,367 - __main__ - INFO - Running on http://0.0.0.0:5000
2026-01-27 23:28:29,367 - __main__ - INFO - Debug mode: False
```

**Testing GET / endpoint:**
```bash
$curl http://localhost:5000/ | python3 -m json.tool
{
    "endpoints": [
        {
            "description": "Service information",
            "method": "GET",
            "path": "/"
        },
        {
            "description": "Health check",
            "method": "GET",
            "path": "/health"
        }
    ],
    "request": {
        "client_ip": "127.0.0.1",
        "method": "GET",
        "path": "/",
        "user_agent": "curl/7.81.0"
    },
    "runtime": {
        "current_time": "2026-01-27T20:35:29.676613Z",
        "timezone": "UTC",
        "uptime_human": "0 hours, 0 minutes",
        "uptime_seconds": 9
    },
    "service": {
        "description": "DevOps course info service",
        "framework": "Flask",
        "name": "devops-info-service",
        "version": "1.0.0"
    },
    "system": {
        "architecture": "x86_64",
        "cpu_count": 2,
        "hostname": "damir-VB",
        "platform": "Linux",
        "platform_version": "#89~22.04.2-Ubuntu SMP PREEMPT_DYNAMIC Wed Oct 29 10:45:25 UTC 2",
        "python_version": "3.10.12"
    }
}
```

**Testing GET /health endpoint:**
```bash
$curl http://localhost:5000/health | python3 -m json.tool
{
    "status": "healthy",
    "timestamp": "2026-01-27T20:37:22.664269Z",
    "uptime_seconds": 7
}
```

## Challenges & Solutions
For first week there were no significant challanges.

## GitHub Community
Starring repositories matters because it supports open-source projects by increasing their visibility and helping maintainers gauge community interest. Following developers helps build professional networks that foster collaboration, learning, and growth opportunities in team projects.