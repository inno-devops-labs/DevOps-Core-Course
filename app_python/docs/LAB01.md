# Lab 1 — DevOps Info Service Implementation

**Student:** [Your Name]  
**Date:** January 28, 2026  
**Framework:** Flask 3.1.0

---

## Framework Selection

### Chosen Framework: Flask

I selected **Flask 3.1.0** as the web framework for this project.

### Justification

Flask is the ideal choice for this lab because:

1. **Lightweight & Simple:** Flask has minimal boilerplate code, making it perfect for learning and understanding web service fundamentals
2. **Flexibility:** Unlike Django, Flask doesn't enforce a specific project structure, allowing me to organize code as needed
3. **Industry Standard:** Widely used in production environments, especially for microservices
4. **Excellent Documentation:** Comprehensive guides and large community support
5. **Future-Ready:** Works well with Docker, Kubernetes, and other DevOps tools we'll use in later labs

### Framework Comparison

| Feature | Flask | FastAPI | Django |
|---------|-------|---------|--------|
| **Learning Curve** | Easy | Moderate | Steep |
| **Performance** | Good | Excellent (async) | Good |
| **Auto Documentation** | Manual | Automatic (OpenAPI) | Manual |
| **Built-in Features** | Minimal | Moderate | Extensive (ORM, Admin) |
| **Use Case** | Simple APIs, Microservices | Modern async APIs | Full web applications |
| **Setup Time** | Minutes | Minutes | Hours |

**Why not FastAPI?** While FastAPI offers better performance and automatic API documentation, Flask's simplicity is better for learning core concepts. I can always migrate to FastAPI in future labs if async operations become necessary.

**Why not Django?** Django is overpowered for this simple info service. Its built-in ORM, admin panel, and template engine would be unused, adding unnecessary complexity.

---

## Best Practices Applied

### 1. Clean Code Organization

**Practice:** Structured code with clear separation of concerns

```python
# Service metadata at module level
SERVICE_INFO = {
    'name': 'devops-info-service',
    'version': '1.0.0',
    'description': 'DevOps course info service',
    'framework': 'Flask'
}

# Helper functions for specific tasks
def get_system_info():
    """Collect system information."""
    return {...}

def get_uptime():
    """Calculate application uptime."""
    return {...}
```

**Why it matters:** Organized code is easier to test, debug, and maintain. Future labs will build on this structure.

### 2. Comprehensive Error Handling

**Practice:** Custom error handlers for common HTTP errors

```python
@app.errorhandler(404)
def not_found(error):
    return jsonify({
        'error': 'Not Found',
        'message': 'Endpoint does not exist'
    }), 404

@app.errorhandler(500)
def internal_error(error):
    logger.error(f'Internal error: {error}')
    return jsonify({
        'error': 'Internal Server Error',
        'message': 'An unexpected error occurred'
    }), 500
```

**Why it matters:** Graceful error handling prevents crashes and provides clear feedback to clients. This is essential for production services.

### 3. Structured Logging

**Practice:** Configured logging with appropriate levels and formatting

```python
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

logger.info(f'Starting DevOps Info Service...')
logger.debug(f'Request: {request.method} {request.path}')
```

**Why it matters:** Logs are crucial for debugging and monitoring in production. In Lab 7, we'll aggregate these logs using Promtail and Loki.

### 4. Environment-Based Configuration

**Practice:** Configurable via environment variables with sensible defaults

```python
HOST = os.getenv('HOST', '0.0.0.0')
PORT = int(os.getenv('PORT', 5000))
DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'
```

**Why it matters:** This follows the [12-Factor App](https://12factor.net/) methodology, making the app portable across environments (dev, staging, production).

### 5. PEP 8 Compliance

**Practice:** Following Python's official style guide

- 4-space indentation
- Descriptive variable names (`get_system_info()` not `gsi()`)
- Docstrings for all functions
- Blank lines to separate logical sections

**Why it matters:** Consistent style makes code readable for team collaboration and easier to maintain.

### 6. Dependency Pinning

**Practice:** Exact version specification in requirements.txt

```txt
Flask==3.1.0
Werkzeug==3.1.3
gunicorn==23.0.0
```

**Why it matters:** Prevents "works on my machine" issues by ensuring identical dependencies across all environments. Critical for reproducible builds in Lab 2.

### 7. Proper Gitignore

**Practice:** Exclude generated files, virtual environments, and sensitive data

```gitignore
__pycache__/
venv/
*.log
.env
```

**Why it matters:** Keeps the repository clean and prevents accidental commits of credentials or large binary files.

---

## API Documentation

### Endpoint: `GET /`

**Description:** Returns comprehensive service and system information

**Request Example:**
```bash
curl http://localhost:5000/
```

**Response Example:**
```json
{
  "service": {
    "name": "devops-info-service",
    "version": "1.0.0",
    "description": "DevOps course info service",
    "framework": "Flask"
  },
  "system": {
    "hostname": "DESKTOP-ABC123",
    "platform": "Windows",
    "platform_version": "10",
    "architecture": "AMD64",
    "cpu_count": 8,
    "python_version": "3.13.1"
  },
  "runtime": {
    "uptime_seconds": 245,
    "uptime_human": "0 hours, 4 minutes",
    "current_time": "2026-01-28T14:35:00.000000+00:00",
    "timezone": "UTC"
  },
  "request": {
    "client_ip": "127.0.0.1",
    "user_agent": "curl/8.0.1",
    "method": "GET",
    "path": "/"
  },
  "endpoints": [
    {"path": "/", "method": "GET", "description": "Service information"},
    {"path": "/health", "method": "GET", "description": "Health check"}
  ]
}
```

**Status Code:** `200 OK`

---

### Endpoint: `GET /health`

**Description:** Health check for monitoring and Kubernetes probes

**Request Example:**
```bash
curl http://localhost:5000/health
```

**Response Example:**
```json
{
  "status": "healthy",
  "timestamp": "2026-01-28T14:35:00.000000+00:00",
  "uptime_seconds": 245
}
```

**Status Code:** `200 OK`

---

## Testing Evidence

### Test 1: Main Endpoint

**Command:**
```bash
python app.py
curl http://localhost:5000/
```

**Result:** See screenshot `screenshots/01-main-endpoint.png`

The main endpoint successfully returns all required fields:
- ✅ Service metadata (name, version, description, framework)
- ✅ System info (hostname, platform, architecture, CPU count, Python version)
- ✅ Runtime info (uptime in seconds and human-readable format, current time, timezone)
- ✅ Request info (client IP, user agent, HTTP method, path)
- ✅ Available endpoints list

---

### Test 2: Health Check

**Command:**
```bash
curl http://localhost:5000/health
```

**Result:** See screenshot `screenshots/02-health-check.png`

The health endpoint returns:
- ✅ Status: "healthy"
- ✅ Timestamp in ISO format
- ✅ Uptime in seconds
- ✅ HTTP 200 status code

---

### Test 3: Formatted Output

**Command:**
```bash
curl http://localhost:5000/ | python -m json.tool
```

**Result:** See screenshot `screenshots/03-formatted-output.png`

JSON output is properly formatted and valid.

---

### Test 4: Environment Variable Configuration

**Commands:**
```powershell
# Test default port
python app.py

# Test custom port
$env:PORT=8080; python app.py

# Test custom host and port
$env:HOST="127.0.0.1"; $env:PORT=3000; python app.py
```

**Results:**
- ✅ Default configuration (0.0.0.0:5000) works
- ✅ Custom PORT environment variable changes the port
- ✅ Custom HOST environment variable changes the host
- ✅ Application logs show the configured values

---

## Challenges & Solutions

### Challenge 1: Virtual Environment Setup on Windows

**Problem:** PowerShell execution policy prevented activating the virtual environment.

**Error Message:**
```
cannot be loaded because running scripts is disabled on this system
```

**Solution:** 
Changed PowerShell execution policy for the current user:
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

**Lesson Learned:** Windows PowerShell has security policies that can affect development workflows. Understanding execution policies is important for DevOps work on Windows.

---

### Challenge 2: Uptime Calculation Precision

**Problem:** Initially used simple time subtraction which didn't account for proper formatting of hours and minutes.

**Initial Code:**
```python
# This gave incorrect formatting
uptime = str(datetime.now() - START_TIME)
```

**Solution:**
Created a dedicated function to calculate and format uptime properly:
```python
def get_uptime():
    delta = datetime.now(timezone.utc) - START_TIME
    seconds = int(delta.total_seconds())
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    return {
        'seconds': seconds,
        'human': f"{hours} hours, {minutes} minutes"
    }
```

**Lesson Learned:** Always handle time calculations explicitly rather than relying on default string representations. This ensures consistency across different platforms.

---

### Challenge 3: Timezone Awareness

**Problem:** Initial implementation used `datetime.now()` which creates timezone-naive datetimes.

**Solution:** 
Used `datetime.now(timezone.utc)` to create timezone-aware datetimes:
```python
START_TIME = datetime.now(timezone.utc)
'current_time': datetime.now(timezone.utc).isoformat()
```

**Lesson Learned:** In distributed systems (which we'll deploy in later labs), timezone awareness is critical. Always use UTC for server timestamps.

---

## GitHub Community

### Why Starring Repositories Matters

Starring repositories on GitHub serves as both a personal bookmarking system and a signal of appreciation to open-source maintainers. When we star a repository, we're not just saving it for later—we're contributing to its visibility and credibility in the open-source ecosystem. High star counts help projects attract more contributors, gain trust from potential users, and appear in trending lists. For developers, our starred repositories showcase our interests and the technologies we value, effectively curating a public portfolio of tools and practices we follow.

### How Following Developers Helps

Following developers on GitHub creates a professional network that extends beyond the classroom. By following classmates, we can observe their coding approaches, discover new techniques, and stay updated on their projects—fostering a collaborative learning environment even outside formal coursework. Following professors, TAs, and industry developers exposes us to best practices, emerging tools, and real-world problem-solving patterns. This ongoing exposure accelerates our growth as developers and helps us stay current with industry trends, ultimately building the kind of professional connections that are valuable throughout our careers.

### Actions Completed

- ✅ Starred the course repository
- ✅ Starred [simple-container-com/api](https://github.com/simple-container-com/api)
- ✅ Followed [@Cre-eD](https://github.com/Cre-eD) (Professor)
- ✅ Followed [@marat-biriushev](https://github.com/marat-biriushev) (TA)
- ✅ Followed [@pierrepicaud](https://github.com/pierrepicaud) (TA)
- ✅ Followed 3+ classmates

---

## Conclusion

This lab established a solid foundation for the DevOps course by creating a production-ready Python web service with proper structure, documentation, and best practices. The service is now ready for:

- **Lab 2:** Containerization with Docker
- **Lab 3:** CI/CD pipeline with unit tests
- **Future Labs:** Monitoring, Kubernetes deployment, and GitOps

**Key Takeaways:**
1. Framework selection should match project requirements and learning goals
2. Best practices (logging, error handling, configuration) are essential from day one
3. Proper documentation saves time and enables collaboration
4. Clean code structure makes future enhancements easier

---

## Appendix: Running the Application

### Quick Start

```bash
# Navigate to app directory
cd app_python

# Create virtual environment
python -m venv venv

# Activate virtual environment (Windows)
.\venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt

# Run application
python app.py

# Test endpoints
curl http://localhost:5000/
curl http://localhost:5000/health
```

### Files Created

- ✅ `app.py` - Main application (172 lines)
- ✅ `requirements.txt` - Dependencies
- ✅ `.gitignore` - Git ignore rules
- ✅ `README.md` - Application documentation
- ✅ `docs/LAB01.md` - This lab submission
- ✅ `tests/__init__.py` - Test module placeholder
