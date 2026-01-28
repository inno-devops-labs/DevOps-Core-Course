# lab 01 submission: devops info service

## framework selection (why FastAPI)


1. modern & async-first: built on Starlette with native async support, making it ideal for modern devops tools that may need concurrent operations.

2. automatic documentation: interactive API documentation at `/docs` (Swagger UI) and `/redoc` without additional configuration.

3. type safety: pydantic integration provides automatic data validation and clear API contracts.

4. performance: one of the fastest python web frameworks, which is important for monitoring tools that need to respond quickly.


## best practices applied

### 1. pydantic models for type safety

```python
class ServiceMetadata(BaseModel):
    name: str
    version: str
    description: str
    framework: str
```

**importance**: provides automatic validation, documentation generation, and IDE autocompletion. reduces runtime errors from malformed data.

### 2. structured logging

```python
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.exception_handler(404)
async def not_found_handler(request: Request, exc: Exception):
    logger.warning(f'not found: {request.method} {request.url.path}')
    # ...
```

**importance**: essential for production debugging and monitoring. structured logs help track issues in containerized environments where logs are the primary debugging tool.

### 3. custom error handlers

```python
@app.exception_handler(404)
async def not_found_handler(request: Request, exc: Exception):
    return {
        'error': 'not found',
        'message': 'endpoint does not exist',
        'path': request.url.path
    }
```

**importance**: consistent error responses make the API predictable and easier to integrate with monitoring systems.

### 4. startup/shutdown hooks

```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info(f'DevOps Info Service starting on {HOST}:{PORT}')
    logger.info(f'Python version: {platform.python_version()}')
    yield
    # Shutdown
    uptime = get_uptime()
    logger.info(f'DevOps Info Service shutting down (uptime: {uptime["human"]})')
```

**importance**: critical for graceful shutdown in containerized environments (Docker/Kubernetes) and proper resource cleanup.

## API documentation

### endpoints overview

| endpoint | method | description |
|----------|--------|-------------|
| `/` | GET | service and system information |
| `/health` | GET | health check |

### testing commands

**main endpoint:**
```bash
# basic request
curl http://localhost:5000/

# pretty-printed output
curl http://localhost:5000/ | jq
```

**health check:**
```bash
curl http://localhost:5000/health

# check HTTP status code
curl -s -o /dev/null -w '%{http_code}' http://localhost:5000/health
```

**custom port:**
```bash
PORT=8080 python app.py
curl http://localhost:8080/
```

### example response - main endpoint (`GET /`)

```json
{
  "service": {
    "name": "devops-info-service",
    "version": "1.0.0",
    "description": "DevOps course info service",
    "framework": "FastAPI"
  },
  "system": {
    "hostname": "s-razmakhov",
    "platform": "Darwin",
    "platform_version": "macOS-26.2-arm64-arm-64bit",
    "architecture": "arm64",
    "cpu_count": 12,
    "python_version": "3.9.6"
  },
  "runtime": {
    "uptime_seconds": 2,
    "uptime_human": "2 seconds",
    "current_time": "2026-01-28T20:07:01.956014+00:00",
    "timezone": "UTC"
  },
  "request": {
    "client_ip": "127.0.0.1",
    "user_agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36",
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

### example response - health check (`GET /health`)

```json
{
  "status": "healthy",
  "timestamp": "2026-01-28T20:08:16.012061+00:00",
  "uptime_seconds": 76
}
```

## testing evidence

### screenshots

*see screenshots in `docs/screenshots/`*

1. **`01-main-endpoint.png`** - main endpoint showing complete JSON response
2. **`02-health-check.png`** - health check response
3. **`03-formatted-output.png`** - pretty-printed JSON output using `jq`

### terminal output example

```bash
(venv) λ ~/bucket/courses/uni/devops-s26/app_python/ lab01* python3 app.py
INFO:     Started server process [83518]
INFO:     Waiting for application startup.
2026-01-28 23:26:40,735 - app - INFO - DevOps Info Service starting on 0.0.0.0:5000
2026-01-28 23:26:40,735 - app - INFO - Python version: 3.9.6
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:5000 (Press CTRL+C to quit)
INFO:     127.0.0.1:55234 - "GET /health HTTP/1.1" 200 OK
INFO:     127.0.0.1:55234 - "GET / HTTP/1.1" 200 OK
^CINFO:     Shutting down
INFO:     Waiting for application shutdown.
2026-01-28 23:26:49,635 - app - INFO - DevOps Info Service shutting down (uptime: 8 seconds)
INFO:     Application shutdown complete.
INFO:     Finished server process [83518]
```

## challenges & solutions


### challenge i: uptime human-readable format

**problem**: converting seconds to a readable format needed to handle various durations (seconds, minutes, hours) gracefully.

**solution**: dynamic formatting based on elapsed time:
```python
hours = seconds // 3600
minutes = (seconds % 3600) // 60
secs = seconds % 60

human_parts = []
if hours:
    human_parts.append(f"{hours} hour{'s' if hours != 1 else ''}")
# ... similar for minutes and seconds
```

### challenge ii: platform version string

**problem**: getting just the OS version information without the full platform string.

**solution**: used `platform.platform()` which provides comprehensive platform information including OS, version, and architecture in a single string.

## github community

### why starring repositories matters

starring repositories on github serves multiple important purposes in the open-source ecosystem:

1. discovery & bookmarking: stars help bookmark interesting projects for future reference. starred repositories appear on your github profile, making it easy to find them later and showing others what technologies you're interested in.

2. community signal: the star count indicates project popularity and community trust. high star counts help other developers discover quality tools and encourage maintainers by showing appreciation for their work.

3. professional development: a thoughtful collection of starred repositories demonstrates awareness of industry tools, best practices, and emerging technologies to potential employers.

### why following developers helps

following developers on github is valuable for several reasons:

1. learning & inspiration: seeing what others are working on, how they solve problems, and their code quality provides continuous learning opportunities.

2. networking & collaboration: building connections with classmates, professors, and industry professionals creates a supportive community for future projects and career opportunities.

3. staying current: following thought leaders and active contributors keeps you updated on trending projects, new tools, and best practices in your technology stack.
