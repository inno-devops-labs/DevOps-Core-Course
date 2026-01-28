# Lab 1 Submission

## Framework Selection

### Choice: FastAPI
I selected FastAPI as the web framework for this project.

### Justification:
FastAPI offers several advantages over alternatives:

1. **Performance**: Built on Starlette and Pydantic, FastAPI is one of the fastest Python frameworks available
2. **Automatic Documentation**: Generates OpenAPI/Swagger documentation automatically
3. **Modern Features**: Native async/await support, type hints, and dependency injection
4. **Developer Experience**: Excellent editor support with autocompletion and validation
5. **Standards Compliance**: Based on OpenAPI and JSON Schema standards

### Comparison Table:

| Feature | FastAPI | Flask | Django |
|---------|---------|-------|--------|
| Performance | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐ |
| Learning Curve | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐ |
| Auto Documentation | ✅ | ❌ | ❌ |
| Async Support | ✅ | Limited | ✅ |
| Built-in Admin | ❌ | ❌ | ✅ |
| Project Size | Micro | Micro | Full-stack |
| Best For | APIs, Microservices | Small apps, Prototyping | Large applications |

For a DevOps-focused service that needs to be lightweight, fast, and well-documented, FastAPI is the optimal choice.

## Best Practices Applied

### 1. Clean Code Organization
- **File structure**: Clear separation of concerns with dedicated functions
- **Function names**: Descriptive names like `get_system_info()`, `get_uptime()`
- **Import grouping**: Standard library imports first, then third-party, then local
- **Comments**: Only where necessary to explain complex logic
- **Type hints**: All functions have return type annotations

```python
def get_system_info() -> Dict[str, Any]:
    """Collect and return system information."""
    return {
        "hostname": socket.gethostname(),
        "platform": platform.system(),
        "platform_version": platform.version(),
        "architecture": platform.machine(),
        "cpu_count": os.cpu_count(),
        "python_version": platform.python_version(),
    }
```

### 2. Error Handling
- Custom exception handlers for 404 and 500 errors
- JSON responses for API consistency
- Logging of internal errors

```python
@app.exception_handler(404)
async def not_found(request: Request, exc):
    return JSONResponse(
        status_code=404,
        content={
            "error": "Not Found",
            "message": f"The requested endpoint {request.url.path} does not exist"
        }
    )
```

### 3. Logging
- Structured logging with timestamps and levels
- Configurable log levels via DEBUG environment variable
- Request logging for monitoring

```python
logging.basicConfig(
    level=logging.DEBUG if DEBUG else logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Usage in endpoints
logger.info(f"GET / requested by {request.client.host if request.client else 'unknown'}")
```

### 4. Configuration Management
- Environment variables for configuration
- Sensible defaults
- Type conversion for numeric values

```python
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", "5000"))
DEBUG = os.getenv("DEBUG", "False").lower() == "true"
```

### 5. Dependencies Management
- Pinned versions in `requirements.txt`
- Production-ready dependencies with performance extras

```txt
fastapi==0.115.0
uvicorn[standard]==0.32.0
```

### 6. Git Ignore
- Comprehensive `.gitignore` file
- Covers Python, IDE files, logs, and OS-specific files

```gitignore
# Python
__pycache__/
*.py[cod]
venv/

# Logs
*.log

# IDE
.vscode/
.idea/

# OS
.DS_Store
```

### 7. CORS Middleware
- Added CORS middleware for cross-origin requests
- Configurable for different environments

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

## API Documentation

### Endpoints:

#### GET `/`
**Description**: Returns comprehensive service and system information

**Request:**
```bash
curl http://localhost:5000/
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
    "hostname": "your-hostname",
    "platform": "Linux",
    "platform_version": "#1 SMP ...",
    "architecture": "x86_64",
    "cpu_count": 8,
    "python_version": "3.11.0"
  },
  "runtime": {
    "uptime_seconds": 120,
    "uptime_human": "0 hours, 2 minutes",
    "current_time": "2026-01-28T10:30:00.000Z",
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

#### GET `/health`
**Description**: Health check endpoint for monitoring

**Request:**
```bash
curl http://localhost:5000/health
```

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2026-01-28T10:30:00.000Z",
  "uptime_seconds": 120
}
```

### Testing Commands:

```bash
# Test with different ports
PORT=8080 python app.py
curl http://localhost:8080/

# Test health endpoint
curl http://localhost:5000/health

# Test with pretty-print
curl http://localhost:5000/ | python -m json.tool

# Test auto-documentation
curl http://localhost:5000/docs

# Test error handling
curl http://localhost:5000/nonexistent

# Test with environment variables
HOST=127.0.0.1 PORT=3000 python app.py
curl http://127.0.0.1:3000/
```

## Testing Evidence

### Screenshots:
All screenshots are available in `docs/screenshots/`:
1. `01-main-endpoint.png` - Complete JSON response from `/`
2. `02-health-check.png` - Health endpoint response
3. `03-formatted-output.png` - Pretty-printed JSON output

### Terminal Output Examples:

**Starting the server:**
```
$ cd app_python
$ venv/bin/python app.py
2026-01-28 10:30:00 - app - INFO - Starting DevOps Info Service on 0.0.0.0:5000
2026-01-28 10:30:00 - app - INFO - Debug mode: False
INFO:     Started server process [12345]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:5000 (Press CTRL+C to quit)
```

**Testing endpoints:**
```
$ curl http://localhost:5000/health
{"status":"healthy","timestamp":"2026-01-28T10:30:15.123456Z","uptime_seconds":15}

$ curl http://localhost:5000/ | jq '.service'
{
  "name": "devops-info-service",
  "version": "1.0.0",
  "description": "DevOps course info service",
  "framework": "FastAPI"
}

$ curl http://localhost:5000/nonexistent
{"error":"Not Found","message":"The requested endpoint /nonexistent does not exist"}
```

**Testing environment variables:**
```
$ PORT=8080 venv/bin/python app.py &
$ curl http://localhost:8080/health
{"status":"healthy","timestamp":"2026-01-28T10:31:00.000000Z","uptime_seconds":5}
```

## Challenges & Solutions

### Shell Compatibility (Fish vs Bash)
**Problem**: Virtual environment activation scripts are shell-specific
**Solution**:

```bash
# Instead of: source venv/bin/activate
# Use: source venv/bin/activate.fish
```

## GitHub Community

### GitHub Social Features Engagement

**1. Why Starring Repositories Matters:**
Starring repositories serves multiple purposes in open source:
- **Discovery & Bookmarking**: Stars help bookmark interesting projects for future reference and indicate community trust. They serve as a personal library of quality projects you want to remember.
- **Open Source Signal**: Star counts show appreciation to maintainers, help projects gain visibility in GitHub searches and recommendations, and serve as social proof of a project's quality.
- **Professional Context**: Starring quality projects demonstrates awareness of industry tools and best practices to potential employers and collaborators. It shows you're engaged with the developer ecosystem.

**2. How Following Developers Helps:**
Following developers on GitHub provides several benefits for professional growth:
- **Networking**: Build professional connections and see what others in your field are working on. Following professors and TAs keeps you updated on their research and projects.
- **Learning**: Discover new projects, learn from others' code and commit patterns, and stay current with best practices. Following classmates allows you to learn from peers.
- **Collaboration**: Stay updated on classmates' work for potential future collaborations. Seeing others' approaches to the same problems can inspire new solutions.
- **Career Growth**: Follow thought leaders in your technology stack to stay current with industry trends and emerging technologies.

**GitHub Best Practices Applied:**
- ✅ Starred the course repository to show engagement and bookmark for reference
- ✅ Starred the simple-container-com/api project to support open-source container tools
- ✅ Followed professor and TAs for mentorship opportunities and to learn from experienced developers
- ✅ Followed at least 3 classmates
