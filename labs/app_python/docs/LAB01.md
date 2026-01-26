# Lab 01 - DevOps Info Service Implementation

## Framework Selection

### Choice: FastAPI

I chose **FastAPI** as the web framework for this project.

### Comparison with Alternatives

| Feature | FastAPI | Flask | Django |
|---------|---------|-------|--------|
| Performance | High (async) | Moderate | Moderate |
| Learning Curve | Easy | Easy | Steeper |
| Auto Documentation | ✅ Built-in Swagger/ReDoc | ❌ Manual | ❌ Manual |
| Type Hints | ✅ Native support | ❌ Optional | ❌ Optional |
| Async Support | ✅ Native | ⚠️ Limited | ⚠️ Limited |
| Validation | ✅ Pydantic built-in | ❌ Manual | ⚠️ Forms only |
| Size | Lightweight | Lightweight | Heavy |
| Best For | APIs & Microservices | Simple apps | Full-stack web |

### Justification

1. **Modern & Production-Ready**: FastAPI is designed for modern Python (3.8+) with native async/await support, making it ideal for DevOps microservices.

2. **Automatic API Documentation**: Built-in Swagger UI and ReDoc means zero effort for API documentation - crucial for DevOps tooling.

3. **Type Safety**: Native Pydantic integration ensures request/response validation automatically.

4. **Performance**: One of the fastest Python frameworks, comparable to NodeJS and Go.

5. **Future-Proof**: Perfect for containerization (Lab 2) and Kubernetes (Lab 9) due to its lightweight async nature.

---

## Best Practices Applied

### 1. Clean Code Organization

```python
# Proper imports grouping (stdlib → third-party → local)
import os
import socket
import platform
import logging
from datetime import datetime, timezone

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
```

### 2. PEP 8 Compliance

- 4-space indentation
- Descriptive function names (`get_system_info`, `get_uptime`)
- Docstrings for all functions
- Line length under 100 characters
- Proper spacing around operators

### 3. Error Handling

```python
@app.exception_handler(404)
async def not_found_handler(request: Request, exc):
    return JSONResponse(
        status_code=404,
        content={'error': 'Not Found', 'message': 'Endpoint does not exist'}
    )

@app.exception_handler(500)
async def internal_error_handler(request: Request, exc):
    logger.error(f'Internal error: {exc}')
    return JSONResponse(
        status_code=500,
        content={'error': 'Internal Server Error', 'message': 'An unexpected error occurred'}
    )
```

### 4. Logging Configuration

```python
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

logger.info(f'Application starting on {HOST}:{PORT}')
logger.debug(f'Request: {request.method} {request.url.path}')
```

### 5. Configuration via Environment Variables

```python
HOST = os.getenv('HOST', '0.0.0.0')
PORT = int(os.getenv('PORT', 5000))
DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'
```

### 6. Dependency Pinning

```txt
fastapi==0.115.0
uvicorn[standard]==0.32.0
```

---

## API Documentation

### Main Endpoint: `GET /`

**Command:**
```bash
curl -s http://localhost:5000/ | jq .
```

**Response:**
```json
{
  "service": {
    "name": "devops-info-service",
    "version": "1.0.0",
    "description": "DevOps course info service",
    "framework": "FastAPI"
  },
  "system": {
    "hostname": "hostname",
    "platform": "Linux",
    "platform_version": "Linux-5.15.0-x86_64",
    "architecture": "x86_64",
    "cpu_count": 8,
    "python_version": "3.11.0"
  },
  "runtime": {
    "uptime_seconds": 120,
    "uptime_human": "0 hours, 2 minutes",
    "current_time": "2026-01-26T16:33:00.000Z",
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

### Health Endpoint: `GET /health`

**Command:**
```bash
curl -s http://localhost:5000/health | jq .
```

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2026-01-26T16:33:00.000Z",
  "uptime_seconds": 120
}
```

---

## Testing Evidence

The screenshots below demonstrate the working application:

### Screenshots

1. **Main Endpoint Response** - `screenshots/01-main-endpoint.png`
2. **Health Check Response** - `screenshots/02-health-check.png`
3. **Formatted Output** - `screenshots/03-formatted-output.png`

> **Note:** Screenshots should be captured after running the application and testing with curl.

**Terminal Test Commands:**
```bash
# Start the application
python app.py

# In another terminal - test main endpoint
curl http://localhost:5000/

# Test health endpoint
curl http://localhost:5000/health

# Pretty print with jq
curl -s http://localhost:5000/ | jq .
```

---

## Challenges & Solutions

### Challenge 1: Timezone Handling

**Problem:** Ensuring consistent UTC timestamps across responses.

**Solution:** Used `datetime.now(timezone.utc)` with explicit timezone and formatted ISO strings with 'Z' suffix:
```python
datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')
```

### Challenge 2: Human-Readable Uptime

**Problem:** Converting seconds to human-readable format.

**Solution:** Created a dedicated `get_uptime()` function with proper pluralization:
```python
f"{hours} hour{'s' if hours != 1 else ''}, {minutes} minute{'s' if minutes != 1 else ''}"
```

### Challenge 3: Platform Version

**Problem:** Getting detailed platform version info.

**Solution:** Used `platform.platform()` which provides comprehensive OS version information.

---

## GitHub Community

### Why Stars Matter

Starring repositories helps in several ways:
- **Bookmarking**: Stars let you save projects for future reference
- **Recognition**: High star counts show community trust and project quality
- **Visibility**: Stars help projects appear in GitHub recommendations and searches
- **Encouragement**: Stars motivate maintainers to continue development

### Why Following Matters

Following developers is important for:
- **Learning**: See what experienced developers work on and how they solve problems
- **Networking**: Build professional connections for future collaboration
- **Discovery**: Find new projects through your network's activity
- **Career Growth**: Stay updated on industry trends and tools

> I have starred the course repository and simple-container-com/api, followed the professor and TAs, and followed classmates on GitHub.
