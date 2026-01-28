# Lab 01 — DevOps Info Service: Implementation Documentation

## Framework Selection

### Chosen Framework: FastAPI 0.115

I chose **FastAPI** as the web framework for this project.

### Comparison with Alternatives

| Feature | Flask | FastAPI | Django |
|---------|-------|---------|--------|
| **Learning Curve** | Easy | Moderate | Steep |
| **Performance** | Good | Excellent | Good |
| **Auto Documentation** | Manual | Built-in (Swagger) | Manual |
| **Async Support** | Limited | Native | Limited |
| **Project Size** | Minimal | Small | Large |
| **Dependencies** | Few | Moderate | Many |
| **Best For** | Simple APIs | Modern APIs | Full apps |

### Why FastAPI?

1. **Modern & Async**: FastAPI is built on modern Python features (async/await, type hints), making it future-proof and efficient for I/O-bound operations.

2. **Automatic Documentation**: Built-in Swagger UI (`/docs`) and ReDoc (`/redoc`) provide interactive API documentation without any extra configuration.

3. **Type Safety**: Uses Pydantic for data validation and Python type hints, catching errors at development time rather than runtime.

4. **High Performance**: One of the fastest Python frameworks available, comparable to NodeJS and Go.

5. **Perfect for Microservices**: Lightweight and efficient, ideal for containerized microservices in upcoming labs.

6. **Industry Adoption**: Rapidly growing adoption in production environments, especially for APIs and microservices.

---

## Best Practices Applied

### 1. Clean Code Organization

```python
# Imports grouped by type: stdlib, third-party, local
import os
import socket
import platform
from datetime import datetime, timezone

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
```

**Why it matters**: Organized imports make code easier to read and maintain. PEP 8 recommends this grouping.

### 2. Configuration via Environment Variables

```python
HOST = os.getenv('HOST', '0.0.0.0')
PORT = int(os.getenv('PORT', 8000))
DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'
```

**Why it matters**: Follows the 12-Factor App methodology. Configuration can change between deployments without code changes.

### 3. Logging Implementation

```python
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

logger.info(f'Request: {request.method} {request.path}')
```

**Why it matters**: Proper logging is essential for debugging and monitoring in production. Structured logs help with log aggregation tools.

### 4. Error Handling

```python
@app.exception_handler(404)
async def not_found_handler(request: Request, exc):
    return JSONResponse(
        status_code=404,
        content={
            'error': 'Not Found',
            'message': 'Endpoint does not exist'
        }
    )
```

**Why it matters**: Consistent JSON error responses make API consumption predictable and debugging easier.

### 5. Modular Functions

```python
def get_system_info():
    """Collect system information."""
    return { ... }

def get_runtime_info():
    """Get runtime information."""
    return { ... }
```

**Why it matters**: Single-responsibility functions are easier to test, maintain, and reuse.

### 6. Documentation Strings

```python
def get_uptime():
    """Calculate application uptime."""
```

**Why it matters**: Docstrings improve code readability and can be used by documentation generators.

### 7. Constants for Static Data

```python
SERVICE_INFO = {
    'name': 'devops-info-service',
    'version': '1.0.0',
    ...
}
```

**Why it matters**: Constants defined at module level are easy to find and update.

---

## API Documentation

### Interactive Documentation

FastAPI provides automatic interactive API documentation:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### Main Endpoint: `GET /`

**Description**: Returns comprehensive service and system information.

**Request**:
```bash
curl -X GET http://localhost:8000/
```

**Response** (HTTP 200):
```json
{
  "service": {
    "name": "devops-info-service",
    "version": "1.0.0",
    "description": "DevOps course info service",
    "framework": "FastAPI"
  },
  "system": {
    "hostname": "DESKTOP-ABC123",
    "platform": "Windows",
    "platform_version": "Windows-10-10.0.22631-SP0",
    "architecture": "AMD64",
    "cpu_count": 8,
    "python_version": "3.13.1"
  },
  "runtime": {
    "uptime_seconds": 45,
    "uptime_human": "45 seconds",
    "current_time": "2026-01-28T10:30:00.123456+00:00",
    "timezone": "UTC"
  },
  "request": {
    "client_ip": "127.0.0.1",
    "user_agent": "curl/8.0.0",
    "method": "GET",
    "path": "/"
  },
  "endpoints": [
    {"path": "/", "method": "GET", "description": "Service information"},
    {"path": "/health", "method": "GET", "description": "Health check"}
  ]
}
```

### Health Check: `GET /health`

**Description**: Simple health endpoint for monitoring and container orchestration.

**Request**:
```bash
curl -X GET http://localhost:8000/health
```

**Response** (HTTP 200):
```json
{
  "status": "healthy",
  "timestamp": "2026-01-28T10:30:00.123456+00:00",
  "uptime_seconds": 45
}
```

### Error Response: 404 Not Found

**Request**:
```bash
curl -X GET http://localhost:8000/nonexistent
```

**Response** (HTTP 404):
```json
{
  "error": "Not Found",
  "message": "Endpoint does not exist",
  "path": "/nonexistent"
}
```

---

## Testing Evidence

### Testing Commands Used

```bash
# Start the application
python app.py

# Or using uvicorn directly
uvicorn app:app --host 0.0.0.0 --port 8000

# Test main endpoint
curl http://localhost:8000/

# Test health endpoint
curl http://localhost:8000/health

# Pretty print with jq (if available)
curl http://localhost:8000/ | jq .

# View interactive API docs
# Open browser to http://localhost:8000/docs

# Test with custom port
$env:PORT=3000; python app.py
curl http://localhost:3000/
```

### Screenshots

Screenshots are located in the `screenshots/` folder:
- `01-main-endpoint.png` - Main endpoint response
- `02-health-check.png` - Health check response
- `03-formatted-output.png` - Pretty-printed JSON output

---

## Challenges & Solutions

### Challenge 1: Cross-Platform Compatibility

**Problem**: The application needed to work on both Windows and Linux, but some system information methods behave differently.

**Solution**: Used Python's `platform` module which abstracts OS differences. The `platform.platform()` function returns appropriate information regardless of OS.

### Challenge 2: Environment Variables in PowerShell

**Problem**: Setting environment variables in PowerShell uses different syntax than Bash.

**Solution**: Documented both methods:
- Bash: `PORT=8080 python app.py`
- PowerShell: `$env:PORT=8080; python app.py`

### Challenge 3: Uptime Formatting

**Problem**: Converting seconds to human-readable format while handling edge cases (0 hours, 1 minute vs 2 minutes).

**Solution**: Built a flexible formatter that only includes non-zero units and handles singular/plural forms:

```python
parts = []
if hours > 0:
    parts.append(f"{hours} hour{'s' if hours != 1 else ''}")
```

### Challenge 4: UTC Timezone Handling

**Problem**: Ensuring consistent timezone handling across different system configurations.

**Solution**: Explicitly used `timezone.utc` from datetime module instead of relying on system timezone:

```python
from datetime import datetime, timezone
START_TIME = datetime.now(timezone.utc)
```

---

## GitHub Community

### Why Starring Repositories Matters

Starring repositories serves multiple purposes in the open-source ecosystem. It acts as a bookmark for projects you find useful, while also signaling appreciation to maintainers. High star counts help projects gain visibility in GitHub's recommendation system, attracting more contributors and users. For your profile, starred repos showcase your interests and awareness of quality tools in the industry.

### How Following Developers Helps

Following developers on GitHub creates a professional network that extends beyond the classroom. You can learn from experienced developers by observing their activity, discover new projects through their contributions, and build connections that may lead to collaboration opportunities. In team projects, following teammates makes it easier to track progress and coordinate work. This networking aspect of GitHub is increasingly valuable for career growth in the tech industry.

---

## Summary

This lab established the foundation for the DevOps Info Service using FastAPI. The implementation follows Python best practices including:

- ✅ Clean code organization
- ✅ Environment-based configuration
- ✅ Comprehensive logging
- ✅ Error handling
- ✅ Modular function design
- ✅ Complete documentation

The service is ready for containerization in Lab 2 and will continue to evolve throughout the course.
