# 1. Framework selection.
## Choice
I have chose FastAPI because I have had an experience with it and have no experience with other frameworks.

## Comparison with Alternatives

| Criteria | FastAPI (chosen) | Flask | Django (DRF) |
|---------|-----------------|-------|--------------|
| Primary use | APIs / microservices | Lightweight web apps & APIs | Full-stack apps & large APIs |
| Performance model | ASGI (async-ready) | WSGI (sync by default) | WSGI/ASGI (heavier stack) |
| Built-in API docs | Yes (Swagger/OpenAPI) | No (manual/add-ons) | Yes (via DRF) |
| Validation / typing | Strong (type hints + Pydantic) | Manual or extensions | Strong (serializers) |
| Boilerplate | Low | Very low | Higher |
| Learning curve | Low–medium | Low | Medium–high |
| Best fit for this lab | Excellent | Good | Overkill |

---

# 2. Best Practices Applied
## Clean Code Organization

### 1) Clear Function Names
The code uses descriptive, intention-revealing function names that clearly communicate what each block returns:

```python
def get_service_info():
    """Get information about service."""
    ...

def get_system_info():
    """Get information about system."""
    ...

def get_runtime_info():
    """Get information about runtime."""
    ...

def get_request_info(request: Request):
    """Get information about request."""
    ...
```
**Why it matters**: Clear naming improves readability, reduces the need for extra comments, and makes the code easier to maintain and extend.

### 2) Proper imports grouping
Imports are organized by category (standard library first, then third-party libraries), which is the common Python convention:
```python
import logging
import os
import platform
import socket
from datetime import datetime, timezone

import uvicorn
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException
```
**Why it matters**: Grouped imports make dependencies easier to understand at a glance, help keep the file structured, and align with typical linting rules.

### 3) Comments only where needed
Instead of excessive inline comments, the code relies on clear names and short docstrings:
```python
"""
DevOps Info Service
Main application module
"""

def get_uptime():
    """Get uptime."""
    ...
```
**Why it matters**: Too many comments can become outdated. Minimal documentation plus clean naming keeps the codebase readable and accurate.

### 4) Follow PEP 8
The implementation follows common PEP 8 practices:
- consistent indentation and spacing,
- snake_case for variables and function names,
- configuration/constants placed near the top of the module (HOST, PORT, DEBUG),
- readable multi-line formatting for long calls:
```python
"""
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
```
**Why it matters**: PEP 8 improves consistency, supports teamwork, and makes the code compatible with linters/formatters such as `flake8`, `ruff`, and `black`.

## Error Handling
The service implements centralized error handling using FastAPI/Starlette exception handlers. This ensures that errors are returned in a consistent JSON format and that clients receive meaningful messages instead of raw stack traces.

### HTTP errors (e.g., 404 Not Found)
A dedicated handler processes HTTP-related exceptions and customizes the response for missing endpoints.

```python
from starlette.exceptions import HTTPException

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    if exc.status_code == 404:
        return JSONResponse(
            status_code=404,
            content={
                "error": "Not Found",
                "message": "Endpoint does not exist",
            },
        )

    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": "HTTP Error",
            "message": exc.detail if exc.detail else "Request failed",
        },
    )
```
**Why it matters**:
- Provides a clear and user-friendly message for invalid routes.
- Keeps error responses consistent across the API.
- Avoids exposing internal implementation details to the client.

### Unhandled exceptions (500 Internal Server Error)
A global handler catches any unexpected exceptions and returns a safe, standardized response.

```python
@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal Server Error",
            "message": "An unexpected error occurred",
        },
    )
```
**Why it matters**:
- Prevents server crashes from unhandled errors.
- Ensures clients always receive valid JSON (important for automation/scripts).
- Helps keep production behavior predictable while preserving the option to log the exception internally.

## 3. Logging
The service includes basic logging configuration to improve observability and simplify debugging. Logs are useful both during development (troubleshooting requests and behavior) and in production (monitoring, incident investigation).

### Logging setup
A global logging configuration is defined at startup with a consistent log format:
```python
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)
```
**Why it matters**:
- Provides timestamps and log levels for easier troubleshooting.
- A consistent format makes logs easier to parse in log aggregators (e.g., ELK, Loki).
- Centralized config avoids inconsistent logging across modules.

### Startup logging
The application logs an informational message when it starts:
```python
if __name__ == "__main__":
    logger.info("Application starting...")
    uvicorn.run("app:app", host=HOST, port=PORT, reload=True)
```
**Why it matters**:
- Confirms that the service started successfully.
- Helps identify restarts and uptime issues.

### Request logging (debug level)
Each endpoint logs basic request information (method and path):
```python
@app.get("/", status_code=status.HTTP_200_OK)
async def root(request: Request):
    logger.debug(f"Request: {request.method} {request.url.path}")
    ...
```
**Why it matters**:
- Helps trace API usage during development.
- Useful for debugging routing problems and unexpected client behavior.

## 4. Dependencies (requirements.txt)
The project keeps dependencies minimal and focused on what is required to run a FastAPI service in production.
### requirements.txt
```
fastapi>=0.110
uvicorn[standard]>=0.27
```
**Why it matters**:
- Faster builds & simpler setup: fewer packages mean faster installation and fewer moving parts.
- Lower risk of conflicts: minimal dependencies reduce version incompatibilities and “dependency hell”.
- Better security posture: fewer third-party libraries reduce the overall attack surface.
- More predictable deployments: only installing what the service truly needs improves reproducibility across environments (local, CI, Docker, VM).

## 5. Git Ignore (.gitignore)

A `.gitignore` file is used to prevent committing temporary, machine-specific, or sensitive files into the repository.

### Recommended `.gitignore`
```gitignore
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
**Why it matters**:
- Keeps the repository clean: avoids committing generated files (`__pycache__`, build outputs, logs).
- Improves portability: prevents OS- and IDE-specific files from polluting the project and causing noisy diffs.
- Protects secrets: ensures configuration files like `.env` (which may contain API keys or credentials) are not accidentally pushed.
- Reduces merge conflicts: fewer irrelevant files tracked by Git means fewer conflicts between contributors.

# 3. API Documentation
The service exposes two endpoints: the main information endpoint and a health check endpoint.
## Request/response examples
### GET `/` — Service and System Information
**Description:**  
Returns comprehensive metadata about the service, system, runtime, request details, and available endpoints.
**Request example:**
```bash
curl -i http://127.0.0.1:5000/
```
**Response example (200 OK):**
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
### GET /health — Health Check
**Description:**  
Returns a simple status response to confirm the service is running.**Request example:**
```bash
curl -i http://127.0.0.1:5000/health
```
**Response example (200 OK):**
```json
{
  "status": "healthy",
  "timestamp": "2024-01-15T14:30:00.000Z",
  "uptime_seconds": 3600
}
```
## Testing commands
### Basic tests
```bash
curl http://127.0.0.1:5000/
curl http://127.0.0.1:5000/health
```
### Test 404 handling (unknown endpoint)
```bash
curl -i http://127.0.0.1:5000/does-not-exist
```
Expected response (404):
```json
{
  "error": "Not Found",
  "message": "Endpoint does not exist"
}
```

# 4. Testing Evidence
Check screenshots.

# 5. Challenges & Solutions
I have no problems in this lab.

# GitHub Community
**Why Stars Matter:**

**Discovery & Bookmarking:**
- Stars help you bookmark interesting projects for later reference
- Star count indicates project popularity and community trust
- Starred repos appear in your GitHub profile, showing your interests

**Open Source Signal:**
- Stars encourage maintainers (shows appreciation)
- High star count attracts more contributors
- Helps projects gain visibility in GitHub search and recommendations

**Professional Context:**
- Shows you follow best practices and quality projects
- Indicates awareness of industry tools and trends

**Why Following Matters:**

**Networking:**
- See what other developers are working on
- Discover new projects through their activity
- Build professional connections beyond the classroom

**Learning:**
- Learn from others' code and commits
- See how experienced developers solve problems
- Get inspiration for your own projects

**Collaboration:**
- Stay updated on classmates' work
- Easier to find team members for future projects
- Build a supportive learning community

**Career Growth:**
- Follow thought leaders in your technology stack
- See trending projects in real-time
- Build visibility in the developer community