# Lab 1 — DevOps Info Service Implementation Report

## Framework Selection

### Chosen Framework: FastAPI

I selected **FastAPI** as the web framework for this project. Here's the detailed comparison:

| Aspect | Flask | FastAPI | Django |
|--------|-------|---------|--------|
| **Learning Curve** | Easy | Moderate | Steep |
| **Performance** | Good | Excellent (async) | Good |
| **Setup Time** | Quick | Quick | Longer |
| **Auto Documentation** | Manual | Built-in | Manual |
| **Type Hints** | Optional | Required | Optional |
| **Async Support** | Limited | Native | Limited |
| **Dependencies** | Minimal | Minimal | Heavy |
| **Best For** | Learning | Production | Enterprise |

### Why FastAPI?

1. **Modern Python Standards**
   - Native async/await support for concurrent requests
   - Type hints for better code quality and IDE support
   - Automatic request validation with Pydantic

2. **Built-in Documentation**
   - Interactive Swagger UI at `/docs`
   - ReDoc at `/redoc`
   - No extra configuration needed

3. **Performance**
   - Significantly faster than Flask
   - Ideal for microservices and monitoring systems
   - Handles concurrent requests efficiently

4. **Production Ready**
   - Professional-grade framework
   - Used by major companies
   - Excellent error handling

5. **Future-Proof**
   - Will support scaling to distributed systems
   - Async-first design benefits future labs
   - Better for Kubernetes integration (Lab 9)

## Implementation Details

### Project Structure
```
app_python/
├── app.py                    # Main FastAPI application (100 lines)
├── requirements.txt          # Dependencies (pinned versions)
├── .gitignore               # Git ignore rules
├── README.md                # User documentation
├── tests/                   # Test directory
│   └── __init__.py
└── docs/                    # Lab documentation
    ├── LAB01.md            # This file
    └── screenshots/        # Evidence
```

### Key Components

#### 1. Application Setup
```python
app = FastAPI(
    title="DevOps Info Service",
    description="Service providing system and runtime information",
    version="1.0.0"
)
```

#### 2. System Information Collection
```python
def get_system_info():
    """Collect system information."""
    return {
        'hostname': socket.gethostname(),
        'platform': platform.system(),
        'platform_version': platform.release(),
        'architecture': platform.machine(),
        'cpu_count': os.cpu_count() or 1,
        'python_version': platform.python_version()
    }
```

#### 3. Uptime Calculation
```python
def get_uptime():
    """Calculate application uptime."""
    delta = datetime.now(timezone.utc) - START_TIME
    seconds = int(delta.total_seconds())
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    return {'seconds': seconds, 'human': f"{hours}h {minutes}m"}
```

#### 4. Main Endpoint `/`
Returns comprehensive JSON with:
- Service metadata
- System information
- Runtime metrics
- Request details
- Available endpoints

#### 5. Health Check `/health`
Lightweight endpoint for monitoring:
- HTTP 200 status
- Health status
- Uptime in seconds
- ISO timestamp

### Configuration Management

Environment variables with defaults:
```python
HOST = os.getenv('HOST', '0.0.0.0')
PORT = int(os.getenv('PORT', 8000))
DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'
```

Usage examples:
```bash
python app.py                    # Default: 0.0.0.0:8000
PORT=3000 python app.py          # Custom port
HOST=127.0.0.1 PORT=5000 python app.py  # Custom host and port
```

## Best Practices Applied

### 1. Clean Code Organization ✓
- **Docstrings:** Every function has clear documentation
- **Function Naming:** Descriptive names like `get_system_info()`, `get_uptime()`
- **Import Grouping:** Standard library, then third-party packages
- **PEP 8 Compliance:** Code formatted according to Python standards

**Example:**
```python
def get_system_info():
    """Collect system information."""
    return {
        'hostname': socket.gethostname(),
        'platform': platform.system(),
        # ...
    }
```

### 2. Error Handling ✓
- **404 Errors:** Custom not found handler
- **500 Errors:** General exception handler
- **Error Messages:** Clear, informative responses

**Implementation:**
```python
@app.exception_handler(404)
async def not_found_handler(request: Request, exc):
    return JSONResponse(
        status_code=404,
        content={"error": "Not Found", "message": "Endpoint does not exist"}
    )
```

### 3. Logging ✓
- **Configured Logging:** With timestamp and level
- **Strategic Logging:** Application startup and errors
- **Helpful Information:** Thread name, module name, and message

**Configuration:**
```python
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)
logger.info('Application starting...')
```

### 4. Dependencies ✓
- **Pinned Versions:** Exact versions for reproducibility
- **Minimal:** Only FastAPI and Uvicorn needed
- **Production-Ready:** Stable, widely-used packages

**requirements.txt:**
```
fastapi==0.115.0
uvicorn[standard]==0.32.0
```

### 5. Git Configuration ✓
- **.gitignore:** Excludes Python artifacts, venv, IDE files
- **Reproducibility:** No unnecessary files in repo
- **Clean Repository:** Professional appearance

## API Documentation

### Endpoint: GET /

**Purpose:** Service and system information

**Request:**
```bash
curl http://localhost:8000/
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
    "hostname": "ramil-laptop",
    "platform": "Linux",
    "platform_version": "5.15.0-84-generic",
    "architecture": "x86_64",
    "cpu_count": 8,
    "python_version": "3.11.0"
  },
  "runtime": {
    "uptime_seconds": 1234,
    "uptime_human": "0 hour, 20 minutes",
    "current_time": "2026-01-27T15:45:30.123456Z",
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

### Endpoint: GET /health

**Purpose:** Health check for monitoring and Kubernetes probes

**Request:**
```bash
curl http://localhost:8000/health
```

**Response (200 OK):**
```json
{
  "status": "healthy",
  "timestamp": "2026-01-27T15:45:30.123456Z",
  "uptime_seconds": 1234
}
```

### Testing Commands

```bash
# Start the service
python app.py

# In another terminal:

# Test main endpoint
curl http://localhost:8000/

# Pretty print JSON
curl http://localhost:8000/ | jq .

# Test health endpoint
curl http://localhost:8000/health

# Test with verbose output
curl -v http://localhost:8000/

# Test with custom port
PORT=3000 python app.py
curl http://localhost:3000/

# Interactive documentation
# Open browser: http://localhost:8000/docs (Swagger UI)
```

## Testing Evidence

### Test 1: Main Endpoint Response
**Command:**
```bash
curl http://localhost:8000/ | jq .
```

**Expected Output:** Complete JSON with all required fields:
- ✓ Service metadata
- ✓ System information (hostname, platform, architecture, CPU, Python version)
- ✓ Runtime information (uptime, current time, timezone)
- ✓ Request details (client IP, user agent, method, path)
- ✓ Endpoints list

### Test 2: Health Check
**Command:**
```bash
curl http://localhost:8000/health | jq .
```

**Expected Output:**
```json
{
  "status": "healthy",
  "timestamp": "2026-01-27T15:45:30.123456Z",
  "uptime_seconds": 15
}
```

### Test 3: Configuration
**Commands:**
```bash
# Default port (8000)
python app.py

# Custom port
PORT=3000 python app.py
curl http://localhost:3000/

# Custom host (localhost only)
HOST=127.0.0.1 PORT=5000 python app.py
curl http://127.0.0.1:5000/
```

### Test 4: Error Handling
**Commands:**
```bash
# Test 404 error
curl http://localhost:8000/nonexistent

# Expected:
# {"error":"Not Found","message":"Endpoint does not exist","path":"/nonexistent"}
```

## Challenges & Solutions

### Challenge 1: Timezone Handling
**Problem:** Python datetime has timezone-aware and naive variants. ISO format timing needed UTC.

**Solution:** Used `timezone.utc` for timezone-aware datetime:
```python
datetime.now(timezone.utc).isoformat() + "Z"
```
This ensures consistency and proper ISO 8601 formatting.

### Challenge 2: Request Information in FastAPI
**Problem:** FastAPI's request object has different structure than Flask.

**Solution:** Used FastAPI's `Request` object with proper client detection:
```python
request.client.host  # Client IP
request.headers.get('user-agent')  # User agent
```


## GitHub Community

### Why Starring Repositories Matters

Starring repositories shows support for valuable projects and boosts their visibility. Following developers helps you learn from their work and stay current with industry trends.

## Conclusion

The DevOps Info Service is now fully implemented with:
- ✓ FastAPI web application
- ✓ Complete system information reporting
- ✓ Health check endpoint
- ✓ Professional code structure
- ✓ Comprehensive documentation
- ✓ Configuration via environment variables
- ✓ Error handling and logging

The service is ready for deployment and will serve as the foundation for containerization, CI/CD, monitoring, and orchestration in subsequent labs.

---

**Submission Status:** Ready for review

**Files Included:**
- [x] app.py (FastAPI application)
- [x] requirements.txt (dependencies)
- [x] .gitignore (git configuration)
- [x] README.md (user documentation)
- [x] docs/LAB01.md (this report)
- [x] tests/__init__.py (test structure)
- [x] Screenshots (saved to docs/screenshots/)

