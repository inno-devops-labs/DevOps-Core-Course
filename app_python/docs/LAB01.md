# lab 01 submission

## framework selection

### chosen framework: flask 3.1

i selected flask for this lab for the following reasons:

| criteria | flask | fastapi | django |
|----------|-------|---------|--------|
| complexity | low | medium | high |
| learning curve | gentle | moderate | steep |
| setup time | minutes | minutes | longer |
| json api support | built-in jsonify | native | requires drf |
| async support | optional | native | optional |

**decision rationale:**
- flask provides the simplest path to a working json api
- the built-in development server eliminates extra dependencies
- excellent documentation and community support
- matches the example code provided in lab instructions

## best practices applied

### 1 pep 8 compliance

organized imports in three groups: standard library, third-party, local

```python
import logging
import os
import platform

from flask import Flask, jsonify, request
```

### 2 error handling

implemented custom error handlers for 404 and 500 responses

```python
@app.errorhandler(404)
def not_found(error):
    return jsonify({
        'error': 'Not Found',
        'message': 'The requested endpoint does not exist'
    }), 404
```

### 3 logging configuration

configured structured logging with timestamps and log levels

```python
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
```

### 4 environment variables

made all configuration externally configurable

```python
HOST = os.getenv('HOST', '0.0.0.0')
PORT = int(os.getenv('PORT', 5000))
DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'
```

## api documentation

### main endpoint

**request:**
```bash
curl http://localhost:5000/
```

**response:**
```json
{
  "service": {
    "name": "devops-info-service",
    "version": "1.0.0",
    "description": "DevOps course info service",
    "framework": "Flask"
  },
  "system": {
    "hostname": "macbook",
    "platform": "Darwin",
    "platform_version": "Darwin-24.6.0-arm64",
    "architecture": "arm64",
    "cpu_count": 8,
    "python_version": "3.13.1"
  },
  "runtime": {
    "uptime_seconds": 120,
    "uptime_human": "0 hours, 2 minutes",
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
    {"path": "/", "method": "GET", "description": "Service information"},
    {"path": "/health", "method": "GET", "description": "Health check"}
  ]
}
```

### health endpoint

**request:**
```bash
curl http://localhost:5000/health
```

**response:**
```json
{
  "status": "healthy",
  "timestamp": "2026-01-27T14:30:00.000000+00:00",
  "uptime_seconds": 120
}
```

## testing evidence

![[fullscreen with two terminals: left running flask app on port 5173, right showing curl responses for main and health endpoints]](screenshots/python-implementation.png)

## challenges and solutions

### challenge 1: timezone handling

**problem:** datetime objects were being serialized without timezone information

**solution:** used `datetime.now(timezone.utc)` instead of `datetime.utcnow()` to ensure proper iso format with timezone

### challenge 2: uptime calculation accuracy

**problem:** needed consistent uptime across multiple endpoint calls

**solution:** stored `START_TIME` as a module-level constant at application startup and calculated delta on each request

## github community

starring repositories helps signal appreciation to maintainers and bookmark useful projects for future reference

following developers on github enables learning from their contributions and staying connected with the professional community
