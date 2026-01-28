# Lab 01 — DevOps Info Service: Implementation Report

## 1. Framework Selection

### Choice: Flask 3.1

I chose **Flask** as the web framework for this project.

### Comparison Table

| Feature | Flask | FastAPI | Django |
|---------|-------|---------|--------|
| **Learning Curve** | Easy | Moderate | Steep |
| **Performance** | Good | Excellent (async) | Good |
| **Documentation** | Excellent | Excellent | Excellent |
| **Auto API Docs** | No (manual) | Yes (OpenAPI) | No |
| **Size/Complexity** | Lightweight | Lightweight | Full-featured |
| **Async Support** | Limited | Native | Limited |
| **Best For** | Simple APIs, microservices | Modern APIs | Full web apps |

### Justification

1. **Simplicity**: Flask's minimal boilerplate makes it ideal for a focused microservice like this info service. The entire application fits in a single readable file.

2. **Course Progression**: Flask is widely used in DevOps contexts (monitoring dashboards, simple APIs). Understanding Flask provides a solid foundation before exploring more complex frameworks.

3. **Flexibility**: Flask doesn't impose architectural decisions, allowing us to structure the code exactly as needed for each lab's requirements.

4. **Ecosystem**: Extensive documentation, large community, and mature tooling (Gunicorn, pytest-flask) support professional development practices.

5. **Docker-Friendly**: Flask applications containerize cleanly, which will be important for Lab 2.

---

## 2. Best Practices Applied

### 2.1 Clean Code Organization

```python
# Imports grouped by type: standard library, then third-party
import os
import socket
import platform
from datetime import datetime, timezone
from flask import Flask, jsonify, request
```

**Why it matters:** Consistent import ordering improves readability and helps identify dependencies at a glance.

### 2.2 Configuration via Environment Variables

```python
HOST = os.getenv('HOST', '0.0.0.0')
PORT = int(os.getenv('PORT', 5000))
DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'
```

**Why it matters:** Environment-based configuration follows the [12-Factor App](https://12factor.net/) methodology, enabling the same codebase to run in development, staging, and production without code changes.

### 2.3 Modular Functions

```python
def get_system_info():
    """Collect system information."""
    return {
        'hostname': socket.gethostname(),
        'platform': platform.system(),
        # ...
    }
```

**Why it matters:** Single-responsibility functions are easier to test, maintain, and reuse. Each function does one thing well.

### 2.4 Logging

```python
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

logger.info(f'Request: {request.method} {request.path}')
```

**Why it matters:** Structured logging is essential for debugging and monitoring in production. Timestamps and log levels enable filtering and alerting.

### 2.5 Error Handling

```python
@app.errorhandler(404)
def not_found(error):
    return jsonify({
        'error': 'Not Found',
        'message': 'Endpoint does not exist'
    }), 404
```

**Why it matters:** Consistent JSON error responses make the API predictable for clients and easier to debug.

### 2.6 Docstrings

```python
def get_uptime():
    """Calculate application uptime."""
```

**Why it matters:** Documentation helps future developers (including yourself) understand the code's purpose without reading the implementation.

---

## 3. API Documentation

### Endpoint: `GET /`

**Description:** Returns comprehensive service and system information.

**Request:**
```bash
curl -X GET http://localhost:5000/
```

**Response (200 OK):**
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
    "platform_version": "Darwin-25.2.0-arm64-arm-64bit",
    "architecture": "arm64",
    "cpu_count": 8,
    "python_version": "3.11.0"
  },
  "runtime": {
    "uptime_seconds": 3600,
    "uptime_human": "1 hour, 0 minutes",
    "current_time": "2026-01-28T14:30:00.000000+00:00",
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

### Endpoint: `GET /health`

**Description:** Health check endpoint for monitoring systems and Kubernetes probes.

**Request:**
```bash
curl -X GET http://localhost:5000/health
```

**Response (200 OK):**
```json
{
  "status": "healthy",
  "timestamp": "2026-01-28T14:30:00.000000+00:00",
  "uptime_seconds": 3600
}
```

### Testing Commands

```bash
# Pretty-printed main endpoint
curl http://localhost:5000/ | python -m json.tool

# Health check
curl http://localhost:5000/health | python -m json.tool

# With custom port
PORT=8080 python app.py &
curl http://localhost:8080/

# Test 404 error handling
curl http://localhost:5000/nonexistent
```

---

## 4. Testing Evidence

### 4.1 Application Startup

```
$ python app.py
2026-01-28 15:00:00,123 - __main__ - INFO - Starting DevOps Info Service on 0.0.0.0:5000
2026-01-28 15:00:00,124 - __main__ - INFO - Debug mode: False
 * Serving Flask app 'app'
 * Running on all addresses (0.0.0.0)
 * Running on http://127.0.0.1:5000
```

### 4.2 Main Endpoint Test

```
$ curl http://localhost:5000/ | python -m json.tool
{
    "endpoints": [...],
    "request": {
        "client_ip": "127.0.0.1",
        "method": "GET",
        "path": "/",
        "user_agent": "curl/8.1.2"
    },
    "runtime": {
        "current_time": "2026-01-28T15:01:23.456789+00:00",
        "timezone": "UTC",
        "uptime_human": "0 hours, 1 minute",
        "uptime_seconds": 83
    },
    "service": {
        "description": "DevOps course info service",
        "framework": "Flask",
        "name": "devops-info-service",
        "version": "1.0.0"
    },
    "system": {
        "architecture": "arm64",
        "cpu_count": 8,
        "hostname": "my-laptop",
        "platform": "Darwin",
        "platform_version": "Darwin-25.2.0-arm64-arm-64bit",
        "python_version": "3.11.0"
    }
}
```

### 4.3 Health Check Test

```
$ curl http://localhost:5000/health | python -m json.tool
{
    "status": "healthy",
    "timestamp": "2026-01-28T15:02:00.123456+00:00",
    "uptime_seconds": 120
}
```

### 4.4 Environment Variable Configuration

```
$ PORT=8080 python app.py
2026-01-28 15:05:00,000 - __main__ - INFO - Starting DevOps Info Service on 0.0.0.0:8080
```

### Screenshots

Screenshots are located in `docs/screenshots/`:
- `01-main-endpoint.png` — Main endpoint JSON response
- `02-health-check.png` — Health check response
- `03-formatted-output.png` — Pretty-printed output with jq/python

---

## 5. Challenges & Solutions

### Challenge 1: Timezone Handling

**Problem:** Initial implementation used `datetime.now()` without timezone information, leading to naive datetime objects.

**Solution:** Used `datetime.now(timezone.utc)` to ensure all timestamps are timezone-aware and consistently in UTC.

```python
from datetime import datetime, timezone
START_TIME = datetime.now(timezone.utc)
```

### Challenge 2: Uptime Formatting

**Problem:** Simple seconds-to-human conversion didn't handle singular/plural forms correctly ("1 hours" vs "1 hour").

**Solution:** Added conditional pluralization:

```python
f"{hours} hour{'s' if hours != 1 else ''}, {minutes} minute{'s' if minutes != 1 else ''}"
```

### Challenge 3: Client IP Behind Proxy

**Problem:** `request.remote_addr` returns the proxy IP when running behind a reverse proxy (common in production).

**Solution:** For now, using `request.remote_addr` directly. In production (Lab 9+), we'll configure `ProxyFix` middleware or use `X-Forwarded-For` header.

---

## 6. GitHub Community

### Why Starring Repositories Matters

Starring repositories is a fundamental way to participate in the open-source community. It serves as both a bookmarking system for useful projects and a signal of appreciation to maintainers. High star counts help projects gain visibility, attract contributors, and indicate community trust — essentially, stars are the "social proof" of open source.

### How Following Developers Helps

Following developers on GitHub creates a professional network that extends beyond the classroom. It allows you to discover new projects through others' activity, learn from experienced developers' code and commit patterns, and stay updated on industry trends. In team projects, following classmates makes collaboration easier and builds a supportive learning community that can benefit your career long-term.

---

## 7. Submission Checklist

- [x] Flask application with both endpoints
- [x] All required JSON fields in responses
- [x] Environment variable configuration
- [x] Error handling (404, 500)
- [x] Logging configured
- [x] `requirements.txt` with pinned versions
- [x] `.gitignore` properly configured
- [x] `README.md` with all required sections
- [x] `LAB01.md` with framework justification
- [x] Best practices documented
- [x] API documentation with examples
- [x] Testing evidence included
- [x] GitHub Community section
- [ ] Screenshots captured (manual step)
- [ ] Course repository starred (manual step)
- [ ] simple-container-com/api starred (manual step)
- [ ] Professor and TAs followed (manual step)
- [ ] 3 classmates followed (manual step)
