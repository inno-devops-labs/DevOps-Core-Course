# Lab 01 - DevOps Info Service: Python Implementation

## Framework Selection

### Chosen: FastAPI

**Decision Rationale:**
FastAPI was selected over Flask and Django for this project due to superior performance, modern Python features, and built-in documentation capabilities essential for a DevOps service.

### Comparison Table

| Feature | FastAPI | Flask | Django |
|---------|---------|-------|--------|
| Learning Curve | Moderate | Easy | Steep |
| Performance | Excellent (async) | Good | Good |
| Type Hints | Native | Optional | Limited |
| Auto-Docs | Built-in Swagger/OpenAPI | Via extensions | Via extensions |
| Async Support | Native | Limited | Emerging |
| Best For | APIs, services | Simple apps | Full-stack apps |
| Startup Time | Fast | Fast | Moderate |
| Memory Usage | Low | Low | Higher |

**Why FastAPI:**
1. **Native Async**: Built-in async/await for handling concurrent requests efficiently
2. **Type Safety**: Full type hints support enables IDE autocomplete and runtime validation
3. **Automatic Documentation**: Swagger UI and ReDoc auto-generated from code
4. **Performance**: Competitive with Go in benchmarks for JSON APIs
5. **DevOps-friendly**: Minimal dependencies, lightweight, production-ready

## Best Practices Applied

### 1. Clean Code Organization
**Implementation**: Code is organized into logical sections with clear separation of concerns.

```python
# Configuration at top
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", "5000"))

# Helper functions for data collection
def get_system_info() -> Dict[str, Any]:
    """Collect static system information."""

# Route handlers at bottom
@app.get("/")
async def index(request: Request):
    """Main endpoint returning comprehensive info."""
```

**Why Important**: Reduces cognitive load, improves maintainability, facilitates testing.

### 2. Type Hints
**Implementation**: All functions include type annotations for parameters and return values.

```python
def get_uptime() -> Dict[str, Any]:
    """Return uptime in seconds and human readable string."""
    # ...

def get_request_info(request: Request) -> Dict[str, Any]:
    """Extract request info (consider X-Forwarded-For)."""
```

**Why Important**: Enables IDE autocomplete, catches type errors before runtime, improves code clarity.

### 3. Error Handling
**Implementation**: Custom exception handler for HTTP errors with proper status codes.

```python
@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    logger.warning(f"HTTP exception: {exc.detail} ({exc.status_code})")
    return JSONResponse(status_code=exc.status_code, content={"error": exc.detail})
```

**Why Important**: Graceful error responses prevent crashes, provide debugging information, maintain API contract.

### 4. Structured Logging
**Implementation**: Configured logging with DEBUG/INFO levels and consistent format.

```python
logging.basicConfig(
    level=logging.DEBUG if DEBUG else logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("devops-info-service")
```

**Why Important**: Essential for debugging production issues, monitoring application health.

### 5. Environment Variables
**Implementation**: All configuration via env vars for different deployment environments.

```python
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", "5000"))
DEBUG = os.getenv("DEBUG", "False").lower() in ("1", "true", "yes")
```

**Why Important**: Allows same image/binary to run in development, staging, production.

### 6. ISO8601 Timestamp Formatting
**Implementation**: All timestamps use RFC3339 format with Z suffix for UTC.

```python
def _format_iso_z(dt: datetime) -> str:
    """Return ISO8601 with trailing Z for UTC times."""
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")
```

**Why Important**: Standard format ensures interoperability with monitoring systems, parsing libraries.

## API Documentation

### GET / - Service Information

**Request:**
```bash
curl http://localhost:3000/ | jq .
```

**Response (200 OK):**
```json
{
  "service": {
    "name": "devops-info-service",
    "version": "1.0.0",
    "description": "DevOps course info service",
    "framework": "FastAPI"
  },
  "system": {
    "hostname": "LAPTOP-LJVRUS9G",
    "platform": "Linux",
    "platform_version": "#1 SMP Fri Mar 29 23:14:13 UTC 2024",
    "architecture": "x86_64",
    "cpu_count": 20,
    "python_version": "3.10.12"
  },
  "runtime": {
    "uptime_seconds": 6,
    "uptime_human": "0 hours, 0 minutes",
    "current_time": "2026-01-24T17:07:43.217902Z",
    "timezone": "UTC"
  },
  "request": {
    "client_ip": "127.0.0.1",
    "user_agent": "curl/7.81.0",
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

### GET /health - Health Check

**Request:**
```bash
curl http://localhost:3000/health | jq .
```

**Response (200 OK):**
```json
{
  "status": "healthy",
  "timestamp": "2026-01-24T17:07:54.041701Z",
  "uptime_seconds": 17
}
```

## Testing Evidence

### Setup
```bash
cd app_python
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python app.py
```

### Test Commands

**Test 1: Main Endpoint**
```bash
curl http://localhost:5555/ | jq .
  % Total    % Received % Xferd  Average Speed   Time    Time     Time  Current
                                 Dload  Upload   Total   Spent    Left  Speed
100   667  100   667    0     0   476k      0 --:--:-- --:--:-- --:--:--  651k
{
  "service": {
    "name": "devops-info-service",
    "version": "1.0.0",
    "description": "DevOps course info service",
    "framework": "FastAPI"
  },
  "system": {
    "hostname": "LAPTOP-LJVRUS9G",
    "platform": "Linux",
    "platform_version": "#1 SMP Fri Mar 29 23:14:13 UTC 2024",
    "architecture": "x86_64",
    "cpu_count": 20,
    "python_version": "3.10.12"
  },
  "runtime": {
    "uptime_seconds": 14,
    "uptime_human": "0 hours, 0 minutes",
    "current_time": "2026-01-24T16:43:15.949608Z",
    "timezone": "UTC"
  },
  "request": {
    "client_ip": "127.0.0.1",
    "user_agent": "curl/7.81.0",
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
![Returns complete service information](screenshots/01-main-endpoint.png)

**Test 2: Health Check**
```bash
curl http://localhost:5555/health | jq .
  % Total    % Received % Xferd  Average Speed   Time    Time     Time  Current
                                 Dload  Upload   Total   Spent    Left  Speed
100    82  100    82    0     0  67880      0 --:--:-- --:--:-- --:--:-- 82000
{
  "status": "healthy",
  "timestamp": "2026-01-24T16:43:35.965829Z",
  "uptime_seconds": 34
}
```
![Returns complete service information](screenshots/02-health-check.png)


## Challenges & Solutions

### Challenge 1: X-Forwarded-For Header Handling
**Problem**: When running behind a reverse proxy (nginx, load balancer), `request.client.host` returns the proxy IP, not the client IP.

**Solution**: Check X-Forwarded-For header first (set by proxies), fall back to `request.client.host`:
```python
xff = request.headers.get("x-forwarded-for")
if xff:
    client_ip = xff.split(",")[0].strip()
else:
    client_ip = request.client.host if request.client else "unknown"
```

### Challenge 2: Platform Version Consistency
**Problem**: `platform.version()` and `platform.release()` return different strings on different systems.

**Solution**: Try `platform.version()` first (more detailed), fall back to `platform.release()` (always available):
```python
try:
    platform_version = platform.version()
except Exception:
    platform_version = platform.release()
```

### Challenge 3: Graceful Plural Handling
**Problem**: Uptime string should be "1 hour, 0 minutes" not "1 hours, 0 minutes".

**Solution**: Implement simple plural logic:
```python
human = f"{hours} hour{'s' if hours != 1 else ''}, {minutes} minute{'s' if minutes != 1 else ''}"
```

## GitHub Community

**Why Starring Repositories Matters:**
Stars serve as social currency in open source - they bookmark quality projects, signal appreciation to maintainers, and help other developers discover proven tools. A high star count indicates community trust and code quality.

**How Following Developers Helps:**
Following colleagues and mentors enables visibility into their work, facilitates collaboration, and builds a professional network. Seeing how experienced developers approach problems provides valuable learning opportunities.
