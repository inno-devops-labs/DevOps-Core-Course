# Lab 01 — DevOps Info Service

## Framework Selection

### Choice: Flask 3.1.0

Flask was selected as the web framework for this project.

**Rationale:** Flask is lightweight, has minimal setup requirements, and provides exactly what we need without unnecessary complexity. It's perfect for microservices and learning DevOps fundamentals.

### Framework Comparison

| Feature | Flask | FastAPI | Django |
|---------|-------|---------|--------|
| **Learning Curve** | Easy | Medium | Steep |
| **Performance** | Good | Excellent (async) | Good |
| **Auto-documentation** | No | Yes (OpenAPI) | No |
| **Batteries Included** | No | No | Yes (ORM, admin) |
| **Use Case** | Simple APIs | Modern async APIs | Full web apps |
| **Best For** | Learning, microservices | Production APIs | Complex projects |

**Conclusion:** Flask is ideal for this lab because it's simple, well-documented, and widely used in DevOps tooling.

## Best Practices Applied

### 1. Clean Code Organization

**Practice:** Structured imports, clear function names, proper docstrings.

**Example:**

```python
"""
DevOps Info Service
Main application module
"""
import os
import socket
import platform
from datetime import datetime, timezone
from flask import Flask, jsonify, request

def get_system_info():
    """Collect system information."""
    return {
        'hostname': socket.gethostname(),
        'platform': platform.system(),
        'architecture': platform.machine(),
        'python_version': platform.python_version()
    }
```

**Importance:** Clean code is easier to maintain, debug, and extend. Following PEP 8 standards ensures consistency across Python projects.

### 2. Error Handling

**Practice:** Custom error handlers for common HTTP errors.

**Example:**

```python
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

**Importance:** Proper error handling provides meaningful feedback to API clients and prevents application crashes from exposing sensitive information.

### 3. Structured Logging

**Practice:** Configured logging with appropriate levels and formatting.

**Example:**

```python
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

logger.info(f'Starting DevOps Info Service on {HOST}:{PORT}')
logger.debug(f'Request: {request.method} {request.path}')
```

**Importance:** Logging is essential for debugging, monitoring, and auditing in production environments. Proper log levels help filter important events.

### 4. Environment-Based Configuration

**Practice:** All configuration values are sourced from environment variables with sensible defaults.

**Example:**

```python
HOST = os.getenv('HOST', '0.0.0.0')
PORT = int(os.getenv('PORT', 8080))
DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'
```

**Importance:** Environment variables enable 12-factor app compliance, making the application portable across different environments without code changes.

### 5. Dependency Management

**Practice:** Pinned versions in `requirements.txt`.

```txt
Flask==3.1.0
Werkzeug==3.1.3
```

**Importance:** Version pinning ensures reproducible builds and prevents breaking changes from automatic updates.

### 6. Git Ignore Configuration

**Practice:** Comprehensive `.gitignore` to exclude generated files and sensitive data.

**Importance:** Keeps the repository clean and prevents accidental commits of credentials, cache files, or OS-specific artifacts.

## API Documentation

### Endpoint: `GET /`

**Description:** Returns comprehensive service and system information.

**Request:**

```bash
curl http://localhost:8080/
```

**Response (200 OK):**

```json
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
    "user_agent": "curl/8.7.1"
  },
  "runtime": {
    "current_time": "2026-01-27T10:12:24.616261+00:00",
    "timezone": "UTC",
    "uptime_human": "1 hour, 2 minutes",
    "uptime_seconds": 3765
  },
  "service": {
    "description": "DevOps course info service",
    "framework": "Flask",
    "name": "devops-info-service",
    "version": "1.0.0"
  },
  "system": {
    "architecture": "arm64",
    "cpu_count": 11,
    "hostname": "MacBook-Pro--Egor.local",
    "platform": "Darwin",
    "platform_version": "Darwin Kernel Version 25.2.0: Tue Nov 18 21:09:45 PST 2025; root:xnu-12377.61.12~1/RELEASE_ARM64_T6030",
    "python_version": "3.12.3"
  }
}
```

### Endpoint: `GET /health`

**Description:** Health check endpoint for monitoring.

**Request:**

```bash
curl http://localhost:8080/health
```

**Response (200 OK):**

```json
{
  "status": "healthy",
  "timestamp": "2026-01-27T10:15:11.908501+00:00",
  "uptime_seconds": 3932
}
```

## Testing Evidence

### Test Commands

```bash
# Start the service
python app.py

# Test main endpoint
curl http://localhost:8080/

# Test health check
curl http://localhost:8080/health

# Pretty-printed output
curl -s http://localhost:8080/ | python3 -m json.tool

# Custom port configuration
PORT=8080 python app.py
```

### Screenshots

The following screenshots demonstrate the working application:

1. **01-main-endpoint.png** - Main endpoint returning complete JSON with service, system, runtime, and request information
2. **02-health-check.png** - Health check endpoint returning status and uptime
3. **03-formatted-output.png** - Pretty-printed JSON output for better readability

## Challenges & Solutions

### Challenge 1: Environment Variable Configuration

**Problem:** Needed to ensure environment variables work correctly across different operating systems.

**Solution:** Used `os.getenv()` with sensible defaults and proper type conversion for PORT (int) and DEBUG (boolean).

### Challenge 2: Uptime Formatting

**Problem:** Raw uptime in seconds is not user-friendly for monitoring.

**Solution:** Implemented `get_uptime()` function that returns both raw seconds and human-readable format, handling singular/plural forms correctly.

## GitHub Community

### Repository Stars

**Why It Matters:** Starring repositories helps discover quality projects and shows appreciation to maintainers. It also signals to the community which tools are valuable and trustworthy.

### Following Developers

**Why It Matters:** Following developers enables continuous learning through observing their work, builds professional network for collaboration, and keeps you updated on industry trends and best practices.

## Implementation Summary

This lab successfully implemented a production-ready DevOps info service with:
- Two fully functional REST endpoints
- Comprehensive system introspection
- Environment-based configuration
- Proper error handling and logging
- Clean, maintainable code following Python best practices
- Complete documentation for users and developers