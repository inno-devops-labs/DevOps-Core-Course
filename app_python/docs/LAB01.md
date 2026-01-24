# Lab 1 Submission - DevOps Info Service

## Framework Selection

### Chosen Framework: FastAPI

As a Java developer, I have limited Python web framework experience. I chose **FastAPI 0.115** because it was the framework I was familiar with from previous experience in Python development.

**Key advantages for this lab:**

- Type safety similar to Java's static typing via Pydantic models
- Automatic API documentation (similar to Swagger/OpenAPI in Spring Boot)
- Modern async/await support for future scalability
- Clean, structured code organization

### Comparison with Alternatives

| Feature | FastAPI | Flask | Django |
|---------|---------|-------|--------|
| Learning Curve | Medium | Easy | Hard |
| Type Safety | Yes (Pydantic) | No | No |
| Auto Documentation | Yes (Swagger/ReDoc) | No | Limited |
| Async Support | Native | Limited | Yes (3.1+) |
| Performance | Excellent | Good | Good |
| Use Case | APIs, Microservices | Simple Apps | Full Websites |

**Decision:** FastAPI provides familiar patterns for Java developers and excellent tooling for API development.

## Best Practices Applied

### 1. Type Hints & Data Models

**Importance:** Catch errors at development time, improve code readability, enable IDE autocompletion.

**Implementation:**

```python
from pydantic import BaseModel

class SystemInfo(BaseModel):
    hostname: str
    platform: str
    architecture: str
    cpu_count: int
    python_version: str
```

### 2. Configuration via Environment Variables

**Importance:** 12-factor app principle - separate configuration from code for flexible deployment.

**Implementation:**

```python
HOST = os.getenv('HOST', '0.0.0.0')
PORT = int(os.getenv('PORT', 8000))
DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'
```

### 3. Structured Logging

**Importance:** Essential for debugging and monitoring in production environments.

**Implementation:**

```python
logging.basicConfig(
    level=logging.DEBUG if DEBUG else logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)
logger.info(f"Request: {request.method} {request.url.path}")
```

### 4. Error Handling

**Importance:** Provide meaningful error messages and graceful failure.

**Implementation:**

```python
@app.exception_handler(404)
async def not_found_handler(request: Request, exc):
    return JSONResponse(
        status_code=404,
        content={"error": "Not Found", "message": "Endpoint does not exist"}
    )
```

### 5. Code Organization

**Importance:** Maintainability and readability for team collaboration.

**Implementation:**

- Separate helper functions for each concern
- Pydantic models for structured data
- Docstrings on all public functions
- Clear separation: configuration → models → routes

### 6. Dependency Management

**Importance:** Reproducible builds and version control.

**Implementation:**

```txt
fastapi==0.115.0
uvicorn[standard]==0.32.0
```

## API Documentation

### Main Endpoint: GET /

**Request:**

```bash
curl http://localhost:8000/
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
    "hostname": "MacNexonm",
    "platform": "Darwin",
    "platform_version": "Darwin Kernel Version...",
    "architecture": "arm64",
    "cpu_count": 8,
    "python_version": "3.11.0"
  },
  "runtime": {
    "uptime_seconds": 120,
    "uptime_human": "0 hours, 2 minutes",
    "current_time": "2026-01-24T17:00:00.000Z",
    "timezone": "UTC"
  },
  "request": {
    "client_ip": "127.0.0.1",
    "user_agent": "curl/8.7.1",
    "method": "GET",
    "path": "/"
  },
  "endpoints": [
    {"path": "/", "method": "GET", "description": "Service information"},
    {"path": "/health", "method": "GET", "description": "Health check"}
  ]
}
```

### Health Check: GET /health

**Request:**

```bash
curl http://localhost:8000/health
```

**Response:**

```json
{
  "status": "healthy",
  "timestamp": "2026-01-24T17:00:00.000Z",
  "uptime_seconds": 120
}
```

### Testing Commands

```bash
# Start application
python app.py

# Test main endpoint
curl http://localhost:8000/

# Test health check
curl http://localhost:8000/health

# Test with custom port
PORT=5000 python app.py
curl http://localhost:5000/

# Test with debug mode
DEBUG=true python app.py

# Interactive documentation
open http://localhost:8000/docs
```

## Testing Evidence

### Screenshots

**01-main-endpoint.png**
![Main Endpoint](screenshots/01-main-endpoint.png)
Shows complete JSON response from `GET /` endpoint with all required fields: service metadata, system information, runtime details, request information, and endpoints list.

**02-health-check.png**  
![Health Check](screenshots/02-health-check.png)
Shows `GET /health` endpoint returning healthy status with timestamp and uptime.

**03-formatted-output.png**
![Logs](screenshots/03-formatted-output.png)
Shows logs from the service in the terminal. Also, start commands and additional information can be found on the screenshot.

### Terminal Output

All endpoints tested successfully:

- Main endpoint returns complete system information
- Health check returns proper status
- Environment variable configuration works (PORT, HOST, DEBUG)
- Application starts without errors (only warns these can be ignored)
- Logging outputs requests correctly

## Challenges & Solutions

No significant challenges encountered during implementation. The application was straightforward to develop with FastAPI's clear documentation and intuitive API design.

## GitHub Community

**Why It Matters:**  
Starring repositories shows appreciation to maintainers and helps discover quality projects. Following developers enables learning from their work and builds professional connections for collaboration.
