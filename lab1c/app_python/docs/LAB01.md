# LAB01 - DevOps Info Service (Python)

## Framework Selection
I chose **FastAPI** because I use this stack at my job, so it feels familiar and I can move faster. The auto-generated docs are also handy for quick checks.

| Framework | Pros | Cons | Decision |
| --- | --- | --- | --- |
| FastAPI | Fast, async-ready, automatic docs, type hints | Slightly more setup than Flask | Chosen (daily stack at work) |
| Flask | Very lightweight, easy to start | Manual docs, fewer built-ins | Not chosen |
| Django | Full-featured, includes ORM | Heavy for a small service | Not chosen |

## Best Practices Applied
**Clean structure and helpers**  
I kept the main endpoint small and pushed the system/runtime details into helper functions so it stays readable.

```python
def get_system_info() -> dict[str, str | int]:
    return {
        "hostname": socket.gethostname(),
        "platform": platform.system(),
        "platform_version": platform.release(),
        "architecture": platform.machine(),
        "cpu_count": os.cpu_count() or 0,
        "python_version": platform.python_version(),
    }
```

**Configuration through environment variables**  
The app can be configured without code changes:

```python
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", "5000"))
DEBUG = os.getenv("DEBUG", "False").lower() == "true"
```

**Logging**  
Requests and responses are logged through middleware so it is easy to trace incoming calls.

```python
@app.middleware("http")
async def log_requests(request: Request, call_next):
    logger.info("Request: %s %s", request.method, request.url.path)
    response = await call_next(request)
    logger.info("Response: %s %s -> %s", request.method, request.url.path, response.status_code)
    return response
```

**Error handling**  
There are explicit handlers for 404 and 500 to return errors.

```python
@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    if exc.status_code == 404:
        return JSONResponse(
            status_code=404,
            content={"error": "Not Found", "message": "Endpoint does not exist"},
        )
```

## API Documentation
### `GET /`
Returns service, system, runtime, and request details.

Example:
```json
{
  "service": {
    "name": "devops-info-service",
    "version": "1.0.0",
    "description": "DevOps course info service",
    "framework": "FastAPI"
  },
  "system": {
    "hostname": "my-machine",
    "platform": "Windows",
    "platform_version": "10",
    "architecture": "AMD64",
    "cpu_count": 12,
    "python_version": "3.11.7"
  },
  "runtime": {
    "uptime_seconds": 42,
    "uptime_human": "0 hours, 0 minutes",
    "current_time": "2026-01-27T10:15:00Z",
    "timezone": "UTC"
  },
  "request": {
    "client_ip": "127.0.0.1",
    "user_agent": "curl/8.5.0",
    "method": "GET",
    "path": "/"
  },
  "endpoints": [
    {"path": "/", "method": "GET", "description": "Service information"},
    {"path": "/health", "method": "GET", "description": "Health check"}
  ]
}
```

### `GET /health`
Returns a lightweight health response used for probes.

Example:
```json
{
  "status": "healthy",
  "timestamp": "2026-01-27T10:15:05Z",
  "uptime_seconds": 47
}
```

### Testing Commands
```bash
curl http://localhost:5000/
curl http://localhost:5000/health
```
Command outputs can be captured with same commands

## Challenges & Solutions
- **Uptime formatting:** I wanted something readable instead of raw seconds, so I added a small formatter that outputs hours and minutes.
- **Request metadata:** FastAPI's `Request` object has what I need, so I pulled `client_ip`, `user_agent`, and the path from there.

## GitHub Community
Stars are a quick way to show that a project is useful and to keep a personal list of tools I might revisit. Following developers keeps me in the loop on what people are building, which helps with collaboration and professional growth.
