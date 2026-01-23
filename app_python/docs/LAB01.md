# Lab 1 Submission: DevOps Info Service

## Framework Selection

### Choice: Flask

I selected **Flask** as the web framework for this project.

### Justification

Flask was chosen for the following reasons:

1. **Simplicity**: Flask's minimalistic design makes it ideal for beginners. It follows the "microframework" philosophy, providing only the essential components needed to build a web application.

2. **Lightweight**: Flask has minimal dependencies and a small footprint, making it perfect for a simple service.

3. **Production Ready**: Despite its simplicity, Flask is battle-tested and widely used in production environments. Many companies use Flask for microservices.

5. **Easy to Extend**: As the course progresses and we add features (Docker, CI/CD, monitoring), Flask's extensible architecture will accommodate these additions smoothly.

6. **Excellent Documentation**: Flask has comprehensive, beginner-friendly documentation that makes development straightforward.

### Framework Comparison

| Feature | Flask | FastAPI | Django |
|---------|-------|---------|--------|
| **Learning Curve** | Easy | Moderate | Steep |
| **Performance** | Good | Excellent (async) | Good |
| **Size** | Small | Small | Large |
| **Auto Documentation** | No | Yes (Swagger) | Yes (Admin) |
| **ORM Included** | No | No | Yes |
| **Flexibility** | High | High | Low (opinionated) |
| **Use Case** | Microservices, APIs | Modern APIs, async | Full web apps |
| **Best For** | Simple services | High-performance APIs | Complex web applications |

**Why not FastAPI?**
While FastAPI offers excellent performance and automatic API documentation, it introduces async/await concepts that may be unnecessary for this simple service. Flask's synchronous model is easier to understand for beginners.

**Why not Django?**
Django is overkill for this project. It includes an ORM, admin panel, and many features we don't need. Django's opinionated structure would add unnecessary complexity.

## Best Practices Applied

### 1. Clean Code Organization

**Practice**: Clear function names, proper imports, minimal comments, PEP 8 compliance.

**Implementation:**
```python
def get_uptime():
    """Calculate application uptime."""
    delta = datetime.now(timezone.utc) - START_TIME
    seconds = int(delta.total_seconds())
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    return {
        'seconds': seconds,
        'human': f"{hours} hour{'s' if hours != 1 else ''}, {minutes} minute{'s' if minutes != 1 else ''}"
    }
```

**Import Organization:**
- Standard library imports first
- Third-party imports second
- Local imports last
- Each group separated by a blank line

**Why it matters**: Clean code is easier to read, maintain, and debug. Following PEP 8 ensures consistency with the Python community.

### 2. Error Handling

**Practice**: Comprehensive error handlers for common HTTP errors.

**Implementation:**
```python
@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors."""
    return jsonify({
        'error': 'Not Found',
        'message': 'Endpoint does not exist'
    }), 404

@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors."""
    logger.error(f'Internal server error: {error}')
    return jsonify({
        'error': 'Internal Server Error',
        'message': 'An unexpected error occurred'
    }), 500
```

**Why it matters**: Proper error handling provides a better user experience and makes debugging easier. JSON error responses maintain API consistency.

### 3. Logging

**Practice**: Structured logging for application events and debugging.

**Implementation:**
```python
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

logger.info('Application starting...')
logger.info(f'Request: {request.method} {request.path} from {request.remote_addr}')
```

**Why it matters**: Logging is essential for production applications. It helps track application behavior, debug issues, and monitor performance. Structured logs can be easily parsed by log aggregation tools.

### 4. Configuration via Environment Variables

**Practice**: Externalize configuration to make the application flexible and deployment-ready.

**Implementation:**
```python
HOST = os.getenv('HOST', '0.0.0.0')
PORT = int(os.getenv('PORT', 5000))
DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'
```

**Why it matters**: Environment variables allow the same code to run in different environments (development, staging, production) without code changes. This is a fundamental DevOps practice.

### 5. Dependency Management

**Practice**: Pin exact versions in `requirements.txt` for reproducibility.

**Implementation:**
```txt
Flask==3.1.0
```

**Why it matters**: Pinned versions ensure that all developers and deployment environments use the same dependencies, preventing "works on my machine" issues.

### 6. Git Ignore

**Practice**: Proper `.gitignore` to exclude unnecessary files from version control.

**Implementation:**
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

**Why it matters**: Keeps the repository clean, prevents committing sensitive information, and reduces repository size.

## API Documentation

### Endpoint: `GET /`

**Description**: Returns comprehensive service and system information.

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
    "framework": "Flask"
  },
  "system": {
    "hostname": "my-laptop",
    "platform": "Linux",
    "platform_version": "Linux-6.8.0-58-generic-x86_64-with-glibc2.39",
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

**Status Code**: `200 OK`

### Endpoint: `GET /health`

**Description**: Health check endpoint for monitoring and Kubernetes probes.

**Request:**
```bash
curl http://localhost:5000/health
```

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2024-01-15T14:30:00.000Z",
  "uptime_seconds": 3600
}
```

**Status Code**: `200 OK`

### Testing Commands

```bash
# Test main endpoint
curl http://localhost:5000/

# Test health endpoint
curl http://localhost:5000/health

# Pretty-print JSON (requires jq)
curl http://localhost:5000/ | jq

# Test with custom port
PORT=8080 python app.py
curl http://localhost:8080/

# Test error handling (404)
curl http://localhost:5000/nonexistent
```

## Testing Evidence

### Screenshots

Screenshots demonstrating the working endpoints are located in `docs/screenshots/`:
- `01-main-endpoint.png` - Main endpoint showing complete JSON response
- `02-health-check.png` - Health check endpoint response
- `03-formatted-output.png` - Pretty-printed JSON output using jq

### Terminal Output

```bash
$ python app.py
2026-01-07 14:30:00,123 - __main__ - INFO - Application starting...
2026-01-07 14:30:00,124 - __main__ - INFO - Starting server on 0.0.0.0:5000
 * Running on http://0.0.0.0:5000
Press CTRL+C to quit

$ curl http://localhost:5000/ | jq
{
  "endpoints": [
    {
      "description": "Service information",
      "method": "GET",
      "path": "/"
    },
    {
      "description": "Health check",
      "method": "GET",
      "path": "/health"
    }
  ],
  "request": {
    "client_ip": "127.0.0.1",
    "method": "GET",
    "path": "/",
    "user_agent": "curl/8.5.0"
  },
  "runtime": {
    "current_time": "2026-01-23T18:56:22.713364.000Z",
    "timezone": "UTC",
    "uptime_human": "0 hours, 0 minutes",
    "uptime_seconds": 45
  },
  "service": {
    "description": "DevOps course info service",
    "framework": "Flask",
    "name": "devops-info-service",
    "version": "1.0.0"
  },
  "system": {
    "architecture": "x86_64",
    "cpu_count": 12,
    "hostname": "j0cos-lenovo",
    "platform": "Linux",
    "platform_version": "Linux-6.8.0-58-generic-x86_64-with-glibc2.39",
    "python_version": "3.12.3"
  }
}



$ curl http://localhost:5000/health
{"status":"healthy","timestamp":"2026-01-07T14:30:00.000Z","uptime_seconds":123}
```

## Challenges & Solutions

### Uptime Calculation

**Problem**: Calculating human-readable uptime format (hours and minutes) from seconds.

**Solution**: Implemented a function that converts total seconds into hours and minutes, with proper pluralization:
```python
def get_uptime():
    delta = datetime.now(timezone.utc) - START_TIME
    seconds = int(delta.total_seconds())
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    return {
        'seconds': seconds,
        'human': f"{hours} hour{'s' if hours != 1 else ''}, {minutes} minute{'s' if minutes != 1 else ''}"
    }
```

### Client IP Detection

**Problem**: Getting the correct client IP, especially when behind proxies.

**Solution**: Implemented fallback logic to check both `request.remote_addr` and `X-Forwarded-For` header:
```python
'client_ip': request.remote_addr or request.environ.get('HTTP_X_FORWARDED_FOR', 'unknown')
```

## GitHub Community

### Why Starring Repositories Matters

Starring repositories in open source serves multiple important purposes. First, it acts as a bookmarking mechanism, allowing developers to save interesting projects for future reference. More importantly, stars provide valuable feedback to maintainers, showing appreciation for their work and encouraging continued development. High star counts also signal project quality and popularity to the community, helping other developers discover reliable tools and libraries. In a professional context, the repositories you star reflect your interests and awareness of industry best practices, which can be valuable for networking and career growth.

### How Following Developers Helps

Following developers on GitHub creates opportunities for learning and professional growth. By following professors, TAs, and classmates, you gain insights into their coding practices, project approaches, and problem-solving techniques. This visibility into others' work helps build a supportive learning community where you can discover new tools, techniques, and project ideas. In team projects, following teammates makes it easier to stay updated on their contributions and find collaborators for future work. Beyond the classroom, following experienced developers exposes you to industry trends, best practices, and real-world applications of technologies you're learning, accelerating your professional development.

