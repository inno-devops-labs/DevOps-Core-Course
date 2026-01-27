# Lab 01 - DevOps Info Service

## 1. Framework Selection

### Chosen Framework: Flask 3.1.0

**Decision Rationale:**

I selected Flask as the web framework for this DevOps Info Service based on several key factors:

1. **Simplicity and Minimalism**
   - Flask follows the "micro-framework" philosophy - it provides just what you need
   - No unnecessary complexity for our use case (two simple endpoints)
   - Easy to understand and maintain

2. **Learning Curve**
   - Excellent for beginners and teaching purposes
   - Clear, straightforward syntax
   - Well-documented with extensive community resources

3. **Flexibility**
   - Doesn't impose strict project structure
   - Easy to add extensions as needed (future labs)
   - Perfect for microservices architecture

4. **Production-Ready**
   - Mature framework (since 2010)
   - Used by major companies (Pinterest, LinkedIn, Netflix)
   - Stable and well-tested

### Framework Comparison

| Feature | Flask | FastAPI | Django |
|---------|-------|---------|--------|
| **Complexity** | Low | Medium | High |
| **Learning Curve** | Easy | Medium | Steep |
| **Performance** | Good | Excellent (async) | Good |
| **Documentation** | Excellent | Excellent | Excellent |
| **Built-in Features** | Minimal | API-focused | Full-stack |
| **Async Support** | Limited | Native | Limited |
| **Best For** | Simple APIs, Prototypes | Modern APIs, High performance | Full applications, Admin panels |
| **Our Use Case** | Perfect | Good | Overkill |

### Why Not FastAPI or Django?

**FastAPI:**
- Excellent choice, but async features are unnecessary for our simple info service
- Auto-generated documentation is nice but not required
- Would be ideal for high-performance APIs with many concurrent requests

**Django:**
- Too heavyweight for our needs
- Includes ORM, admin panel, templating - features we don't need
- Better suited for full web applications with databases and user management

### Conclusion

Flask is the optimal choice for Lab 01 because it provides exactly what we need: a simple way to create REST endpoints with JSON responses, without unnecessary complexity. As we progress through the labs, Flask's extensibility will allow us to add features incrementally.

---

## 2. Best Practices Applied

### 2.1 Code Organization and Structure

**Practice: Modular Function Design**

```python
def get_system_info():
    """Collect comprehensive system information."""
    return {
        'hostname': socket.gethostname(),
        'platform': platform.system(),
        # ...
    }
```

**Why it matters:**
- Separates concerns: each function has one clear purpose
- Makes code testable (we can test `get_system_info()` independently)
- Easy to modify or extend without touching route handlers
- Improves code readability

### 2.2 Documentation

**Practice: Comprehensive Docstrings**

```python
def get_uptime():
    """Calculate application uptime since start."""
```

**Why it matters:**
- Self-documenting code reduces need for external documentation
- Helps IDEs provide better autocomplete and hints
- Essential for team collaboration
- Future you will thank present you

### 2.3 Error Handling

**Practice: Custom Error Handlers**

```python
@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors with JSON response."""
    return jsonify({
        'error': 'Not Found',
        'message': 'Endpoint does not exist',
        'path': request.path
    }), 404
```

**Why it matters:**
- Consistent error responses across the API
- Better debugging with contextual information
- Client applications can handle errors programmatically
- Professional API behavior

### 2.4 Logging

**Practice: Structured Logging**

```python
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

logger.info(f'Request: {request.method} {request.path} from {request.remote_addr}')
```

**Why it matters:**
- Essential for production debugging
- Helps track user behavior and system issues
- Different log levels allow filtering (INFO, DEBUG, WARNING, ERROR)
- Timestamps help with troubleshooting

### 2.5 Configuration Management

**Practice: Environment Variables**

```python
HOST = os.getenv('HOST', '0.0.0.0')
PORT = int(os.getenv('PORT', 5000))
DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'
```

**Why it matters:**
- Different configurations for dev/staging/production
- Security: sensitive data not hardcoded
- Easy deployment to different environments
- Follows 12-factor app methodology

### 2.6 PEP 8 Compliance

**Practice: Python Style Guide**

- 4-space indentation (not tabs)
- Maximum line length: 79 characters for code
- Clear naming conventions: `get_system_info()` not `getSysInfo()`
- Blank lines separate logical sections

**Why it matters:**
- Consistent code style across Python projects
- Easier collaboration with other developers
- Readable by anyone familiar with Python
- Professional standard

### 2.7 Dependency Management

**Practice: Pinned Versions in requirements.txt**

```txt
Flask==3.1.0
Werkzeug==3.1.3
requests==2.32.3
```

**Why it matters:**
- Reproducible builds: same code works everywhere
- Prevents breaking changes from automatic updates
- Easy to audit security vulnerabilities
- CI/CD systems can cache exact versions

---

## 3. API Documentation

### Endpoint: GET /

**Description:** Returns comprehensive service and system information

**Testing Command:**
```bash
curl http://localhost:5000/
```

**Expected Response Structure:**
```json
{
  "service": {
    "name": "devops-info-service",
    "version": "1.0.0",
    "description": "DevOps course info service",
    "framework": "Flask"
  },
  "system": {
    "hostname": "MacBook-Pro.local",
    "platform": "Darwin",
    "platform_version": "Darwin Kernel Version 25.2.0",
    "architecture": "arm64",
    "cpu_count": 8,
    "python_version": "3.13.1"
  },
  "runtime": {
    "uptime_seconds": 45,
    "uptime_human": "45 seconds",
    "current_time": "2026-01-27T12:00:00.000000+00:00",
    "timezone": "UTC"
  },
  "request": {
    "client_ip": "127.0.0.1",
    "user_agent": "curl/8.7.1",
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

**Alternative Testing Command:**
```bash
# Pretty-print JSON
curl http://localhost:5000/ | python -m json.tool
```

### Endpoint: GET /health

**Description:** Health check endpoint for monitoring systems

**Testing Command:**
```bash
curl http://localhost:5000/health
```

**Expected Response:**
```json
{
  "status": "healthy",
  "timestamp": "2026-01-27T12:00:00.000000+00:00",
  "uptime_seconds": 45
}
```

**Use Cases:**
- Kubernetes liveness/readiness probes (Lab 9)
- Load balancer health checks
- Monitoring systems (Prometheus, Grafana)
- Uptime monitoring services

### Testing with Different Configurations

```bash
# Default configuration (port 5000)
python app.py

# Custom port
PORT=8080 python app.py
curl http://localhost:8080/

# Localhost only (more secure for development)
HOST=127.0.0.1 PORT=3000 python app.py
curl http://127.0.0.1:3000/

# Debug mode enabled
DEBUG=true python app.py
```

---

## 4. Testing Evidence

### Screenshots from app_python/docs/screenshots/

The following screenshots demonstrate the working application:

1. **01-main-endpoint.png**
   - Main endpoint (`GET /`) showing complete JSON response
   - All required fields present: service, system, runtime, request, endpoints
   - Response correctly formatted

2. **02-health-check.png**
   - Health check endpoint (`GET /health`)
   - Status: "healthy", timestamp, and uptime_seconds
   - HTTP 200 status code

3. **03-formatted-output.png**
   - Pretty-printed JSON output using `python -m json.tool`
   - Demonstrates readable formatting
   - All data fields visible

### Terminal Output Example

```
2026-01-27 12:17:36,245 - __main__ - INFO - Starting DevOps Info Service...
2026-01-27 12:17:36,245 - __main__ - INFO - Host: 0.0.0.0, Port: 8080, Debug: False
2026-01-27 12:17:36,245 - __main__ - INFO - Visit: http://0.0.0.0:8080/
 * Serving Flask app 'app'
 * Debug mode: off
2026-01-27 12:17:39,349 - werkzeug - INFO - WARNING: This is a development server. Do not use it in a production deployment. Use a production WSGI server instead.
 * Running on all addresses (0.0.0.0)
 * Running on http://127.0.0.1:8080
 * Running on http://10.8.1.8:8080
2026-01-27 12:17:39,349 - werkzeug - INFO - Press CTRL+C to quit
2026-01-27 12:18:44,688 - __main__ - INFO - Request: GET / from 127.0.0.1
2026-01-27 12:18:44,688 - werkzeug - INFO - 127.0.0.1 - - [27/Jan/2026 12:18:44] "GET / HTTP/1.1" 200 -
2026-01-27 12:19:27,266 - __main__ - INFO - Request: GET / from 127.0.0.1
2026-01-27 12:19:27,267 - werkzeug - INFO - 127.0.0.1 - - [27/Jan/2026 12:19:27] "GET / HTTP/1.1" 200 -
2026-01-27 12:19:27,281 - werkzeug - INFO - 127.0.0.1 - - [27/Jan/2026 12:19:27] "GET /health HTTP/1.1" 200 -
2026-01-27 12:19:54,814 - __main__ - INFO - Request: GET / from 127.0.0.1
```

---

## 5. Challenges & Solutions

### Challenge 1: Uptime Calculation

**Problem:**
Initially, uptime was calculated as total seconds only, which is hard to read (e.g., 7325 seconds).

**Solution:**
Implemented `get_uptime()` function that returns both:
- `uptime_seconds`: 7325 (for programmatic use)
- `uptime_human`: "2 hours, 2 minutes" (for human readability)

**Code:**
```python
def get_uptime():
    delta = datetime.now(timezone.utc) - START_TIME
    seconds = int(delta.total_seconds())
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    
    if hours > 0:
        human = f"{hours} hour{'s' if hours != 1 else ''}, {minutes} minute{'s' if minutes != 1 else ''}"
    elif minutes > 0:
        human = f"{minutes} minute{'s' if minutes != 1 else ''}"
    else:
        human = f"{seconds} second{'s' if seconds != 1 else ''}"
    
    return {'seconds': seconds, 'human': human}
```

### Challenge 2: Timezone Handling

**Problem:**
Python's `datetime.now()` returns timezone-naive datetime, which can cause confusion in distributed systems.

**Solution:**
Always use `datetime.now(timezone.utc)` to get timezone-aware UTC timestamps:

```python
current_time = datetime.now(timezone.utc).isoformat()
# Returns: "2026-01-27T12:00:00.000000+00:00"
```

**Why UTC:**
- Standard for server applications
- No daylight saving time confusion
- Easy to convert to local time on client side

### Challenge 3: Error Handling for System Info

**Problem:**
System calls like `socket.gethostname()` could fail in restricted environments.

**Solution:**
Wrapped system info collection in try-except:

```python
def get_system_info():
    try:
        return {
            'hostname': socket.gethostname(),
            # ...
        }
    except Exception as e:
        logger.error(f"Error getting system info: {e}")
        return {}
```

This ensures the service doesn't crash if a system call fails; it just returns empty system info.

---

## 6. GitHub Community

Starring repositories in open source helps bookmark useful projects while signaling appreciation to maintainers and increasing project visibility in the community. Following developers strengthens professional networks by enabling discovery of new projects, learning from others' coding practices, and building collaborative relationships for future team work.
