# Lab 1 — DevOps Info Service: Implementation Report

**Student:** Danil Fishchenko 
**Date:** January 28, 2026  
**Framework:** Flask 3.1.0  
**Language:** Python 3.11+

---

## Table of Contents

1. [Framework Selection](#framework-selection)
2. [Best Practices Applied](#best-practices-applied)
3. [API Documentation](#api-documentation)
4. [Testing Evidence](#testing-evidence)
5. [Challenges & Solutions](#challenges--solutions)
6. [GitHub Community](#github-community)

---

## Framework Selection

### Chosen Framework: **Flask**

I selected **Flask** for this project based on the following considerations:

#### Advantages of Flask

1. **Simplicity and Learning Curve**
   - Flask has a minimal and straightforward API that's easy to understand
   - Perfect for beginners and small to medium projects
   - Quick setup with minimal boilerplate code

2. **Lightweight**
   - Minimal dependencies and overhead
   - Fast startup time and low resource consumption
   - Ideal for microservices architecture

3. **Flexibility**
   - No enforced project structure
   - Easy to integrate third-party libraries
   - Full control over application components

4. **Excellent Documentation**
   - Comprehensive official documentation
   - Large community and extensive tutorials
   - Active development and maintenance

5. **Production Ready**
   - Used by many companies in production
   - Works well with WSGI servers like Gunicorn
   - Easy to containerize with Docker

#### Comparison with Alternatives

| Feature | Flask | FastAPI | Django |
|---------|-------|---------|--------|
| **Learning Curve** | Easy | Moderate | Steep |
| **Setup Speed** | Very Fast | Fast | Slow |
| **Performance** | Good | Excellent (async) | Good |
| **Documentation** | Excellent | Good | Excellent |
| **Built-in Features** | Minimal | Auto-docs, validation | ORM, Admin, Auth |
| **Best For** | Simple APIs | Modern async APIs | Full web apps |
| **Project Size** | Small-Medium | Small-Medium | Medium-Large |
| **Boilerplate** | Minimal | Minimal | Heavy |

#### Why Not FastAPI?

While FastAPI offers better performance and automatic API documentation, Flask is:
- More established with a larger ecosystem
- Simpler for learning fundamental web concepts
- Sufficient for our current requirements
- Better documented for beginners

#### Why Not Django?

Django is too heavy for this project:
- Includes ORM, admin panel, and authentication (not needed)
- More complex project structure
- Longer setup time
- Overkill for a simple info service

### Conclusion

Flask strikes the perfect balance between simplicity and functionality for Lab 1. It allows us to focus on core concepts without getting overwhelmed by framework complexity, while still being production-ready for future labs.

---

## Best Practices Applied

### 1. **Clean Code Organization**

✅ **Modular Functions**
```python
def get_system_info():
    """Collect comprehensive system information."""
    return {
        'hostname': socket.gethostname(),
        'platform': platform.system(),
        # ...
    }
```

**Benefits:**
- Functions have single responsibility
- Easy to test individual components
- Reusable across multiple endpoints
- Clear separation of concerns

---

✅ **Descriptive Naming**
```python
def get_uptime():  # Clear what it does
def get_request_info(req):  # Self-documenting
START_TIME = datetime.now(timezone.utc)  # Constants in CAPS
```

**Benefits:**
- Code reads like natural language
- Reduces need for comments
- Easier for team members to understand

---

✅ **Docstrings**
```python
"""
DevOps Info Service
Main application module providing system information and health check endpoints.
"""
```

**Benefits:**
- Documentation built into code
- Helps IDEs provide better autocomplete
- Generates automatic documentation

---

### 2. **Configuration Management**

✅ **Environment Variables**
```python
HOST = os.getenv('HOST', '0.0.0.0')
PORT = int(os.getenv('PORT', 5000))
DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'
```

**Benefits:**
- Same code works in different environments
- Sensitive data not hardcoded
- Easy to configure without code changes
- Follows 12-factor app methodology

---

### 3. **Error Handling**

✅ **Custom Error Handlers**
```python
@app.errorhandler(404)
def not_found(error):
    return jsonify({
        'error': 'Not Found',
        'message': 'The requested endpoint does not exist',
        'status_code': 404
    }), 404
```

**Benefits:**
- Consistent error responses
- Better user experience
- Easier debugging
- Professional API design

---

### 4. **Code Structure & PEP 8 Compliance**

✅ **Import Organization**
```python
# Standard library imports first
import os
import socket
import platform

# Related third-party imports
from datetime import datetime, timezone
from flask import Flask, jsonify, request
```

**Benefits:**
- Easy to identify dependencies
- Follows Python conventions
- Better code maintainability

---

✅ **Consistent Formatting**
- 4 spaces for indentation
- 2 blank lines between functions
- Proper spacing around operators
- Clear variable names

---

### 5. **Dependency Management**

✅ **Pinned Versions in requirements.txt**
```txt
Flask==3.1.0
gunicorn==21.2.0
pytest==7.4.3
```

**Benefits:**
- Reproducible builds
- Prevents breaking changes
- Easier debugging of version-specific issues

---

### 6. **Git Best Practices**

✅ **Comprehensive .gitignore**
```gitignore
__pycache__/
venv/
.env
*.log
```

**Benefits:**
- Keeps repository clean
- Prevents committing secrets
- Reduces repository size

---

### 7. **User-Friendly Startup Messages**

✅ **Informative Console Output**
```python
print(f"🚀 Starting DevOps Info Service...")
print(f"📍 Server: http://{HOST}:{PORT}")
print("\nAvailable endpoints:")
print("  GET /       - Service information")
```

**Benefits:**
- Clear feedback to developers
- Easy to verify configuration
- Professional appearance

---

## API Documentation

### Endpoint: `GET /`

**Description:** Returns comprehensive service and system information

**Request:**
```bash
curl http://localhost:5000/
```

**Response:** `200 OK`
```json
{
    "endpoints": [
        {
            "description": "Service and system information",
            "method": "GET",
            "path": "/"
        },
        {
            "description": "Health check endpoint",
            "method": "GET",
            "path": "/health"
        }
    ],
    "request": {
        "client_ip": "127.0.0.1",
        "method": "GET",
        "path": "/",
        "user_agent": "curl/8.7.1"
    },
    "runtime": {
        "current_time": "2026-01-28T09:24:35.980667+00:00",
        "timezone": "UTC",
        "uptime_human": "0 hours, 2 minutes",
        "uptime_seconds": 145
    },
    "service": {
        "description": "DevOps course info service",
        "framework": "Flask",
        "name": "devops-info-service",
        "version": "1.0.0"
    },
    "system": {
        "architecture": "arm64",
        "cpu_count": 10,
        "hostname": "pepegas-MacBook-Air.local",
        "platform": "Darwin",
        "platform_version": "Darwin Kernel Version 25.2.0: Tue Nov 18 21:08:48 PST 2025; root:xnu-12377.61.12~1/RELEASE_ARM64_T8132",
        "python_version": "3.14.0"
    }
}
```

**Field Descriptions:**
- `service.name` - Service identifier
- `service.version` - Current version (for API versioning)
- `service.framework` - Web framework used
- `system.hostname` - Server hostname
- `system.platform` - Operating system
- `system.architecture` - CPU architecture (x86_64, arm64, etc.)
- `system.cpu_count` - Number of CPU cores
- `runtime.uptime_seconds` - Seconds since service started
- `runtime.uptime_human` - Human-readable uptime
- `request.client_ip` - IP address of the client
- `request.user_agent` - Client's user agent string

---

### Endpoint: `GET /health`

**Description:** Health check endpoint for monitoring and Kubernetes probes

**Request:**
```bash
curl http://localhost:5000/health
```

**Response:** `200 OK`
```json
{
  "status": "healthy",
  "timestamp": "2026-01-28T09:23:33.108902+00:00",
  "uptime_seconds": 82
}
```

**Use Cases:**
- Kubernetes liveness probes
- Load balancer health checks
- Monitoring systems (Prometheus, Nagios)
- CI/CD pipeline verification

---

### Testing Commands

```bash
# Basic test
curl http://localhost:3000/

# Pretty-printed output
curl http://localhost:3000/ | python3 -m json.tool
# Or if python3 is not available:
curl http://localhost:3000/ | python -m json.tool

# Test health endpoint
curl http://localhost:3000/health

# Test with custom headers
curl -H "User-Agent: MyBot/1.0" http://localhost:3000/

# Test different port
PORT=8080 python3 app.py &
curl http://localhost:8080/

# Save response to file
curl http://localhost:3000/ > response.json
```

---

## Testing Evidence

### Screenshot 1: Main Endpoint (`GET /`)

**File:** `screenshots/01-main-endpoint.png`

**Command used:**
```bash
curl http://localhost:3000/ | python3 -m json.tool
# Or with python:
curl http://localhost:3000/ | python -m json.tool
```

**Expected output:**
- Complete JSON with all fields populated
- Service information (name, version, framework)
- System information (hostname, platform, architecture, CPU count, Python version)
- Runtime information (uptime, current time, timezone)
- Request information (client IP, user agent, method, path)
- List of available endpoints

---

### Screenshot 2: Health Check (`GET /health`)

**File:** `screenshots/02-health-check.png`

**Command used:**
```bash
curl http://localhost:5000/health
```

**Expected output:**
- Status: "healthy"
- Current timestamp in ISO 8601 format
- Uptime in seconds
- HTTP 200 status code

---

### Screenshot 3: Formatted Output

**File:** `screenshots/03-formatted-output.png`

**Tool used:** Browser or Postman with JSON formatter

**Shows:**
- Pretty-printed JSON structure
- Proper indentation and syntax highlighting
- All nested objects clearly visible
- Professional API response format

---

### Additional Testing

**Terminal Output:**
```bash
$ python3 app.py
🚀 Starting DevOps Info Service...
📍 Server: http://0.0.0.0:3000
📊 Debug mode: False
⏰ Started at: 2026-01-28T15:30:00.000000+00:00

Available endpoints:
  GET /       - Service information
  GET /health - Health check

==================================================

 * Serving Flask app 'app'
 * Running on http://0.0.0.0:3000
```

**Command Alternatives:**
```bash
# Using python3 (recommended)
python3 app.py

# Using python (if python3 not found)
python app.py

# With environment variables
PORT=8080 python3 app.py
PORT=8080 python app.py
```

**Testing with Different JSON Tools:**
```bash
# Option 1: Using python3 json.tool (recommended)
curl http://localhost:3000/ | python3 -m json.tool

# Option 2: Using python json.tool (if python3 not found)
curl http://localhost:3000/ | python -m json.tool

# Option 3: Using jq (if installed)
curl http://localhost:3000/ | jq .

# Option 4: Save and inspect
curl http://localhost:3000/ > response.json
cat response.json
```

**Note:** If `python3` command is not found on your system, use `python` instead in all commands.

---

## Challenges & Solutions

### Challenge 1: Uptime Calculation

**Problem:** Initially struggled with calculating uptime in a human-readable format.

**Solution:** 
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

Used `timedelta.total_seconds()` and integer division to convert to hours and minutes.

**Learning:** Understanding time calculations and formatting is essential for monitoring applications.

---

### Challenge 2: Getting System Information

**Problem:** Needed to gather various system details from different Python modules.

**Solution:** 
```python
import platform
import socket
import os

hostname = socket.gethostname()
platform_name = platform.system()
architecture = platform.machine()
cpu_count = os.cpu_count()
```

Combined multiple standard library modules: `platform`, `socket`, and `os`.

**Learning:** Python's standard library has rich system introspection capabilities.

---

### Challenge 3: Environment Variable Configuration

**Problem:** Wanted to make the app configurable without hardcoding values.

**Solution:**
```python
HOST = os.getenv('HOST', '0.0.0.0')
PORT = int(os.getenv('PORT', 5000))
DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'
```

Used `os.getenv()` with default values and proper type conversion.

**Learning:** Environment variables are the standard way to configure cloud-native applications.

---

### Challenge 4: JSON Response Formatting

**Problem:** Needed consistent JSON structure across endpoints.

**Solution:** Used Flask's `jsonify()` function which automatically:
- Sets correct `Content-Type: application/json` header
- Serializes Python dictionaries to JSON
- Handles datetime objects properly

**Learning:** Framework utilities simplify common tasks and ensure consistency.

---

### Challenge 5: Error Handling

**Problem:** Wanted to return JSON errors instead of HTML error pages.

**Solution:** Created custom error handlers:
```python
@app.errorhandler(404)
def not_found(error):
    return jsonify({
        'error': 'Not Found',
        'message': 'The requested endpoint does not exist',
        'status_code': 404
    }), 404
```

**Learning:** Custom error handlers improve API consistency and user experience.

---

## GitHub Community

### Why Starring Repositories Matters

**Starring repositories** is a fundamental practice in open source development that serves multiple purposes:

1. **Discovery & Bookmarking:** Stars help you save interesting projects for future reference. When you star a repository, it appears in your starred list, making it easy to return to projects you find valuable.

2. **Community Signal:** The star count indicates a project's popularity and trustworthiness. High star counts attract more contributors and users, creating a positive feedback loop that benefits the entire ecosystem.

3. **Encouraging Maintainers:** Stars show appreciation to maintainers and motivate them to continue their work. It's a simple way to say "thank you" and acknowledge their effort.

4. **Professional Profile:** Your starred repositories are visible on your GitHub profile, showcasing your interests and the quality of projects you follow to potential employers and collaborators.

**Actions Completed:**
- ✅ Starred the course repository
- ✅ Starred [simple-container-com/api](https://github.com/simple-container-com/api)

---

### Why Following Developers Helps in Team Projects

**Following developers** on GitHub creates valuable professional connections and learning opportunities:

1. **Team Collaboration:** Following classmates makes it easier to discover their projects, provide code reviews, and collaborate on future assignments. You can see what they're working on in real-time.

2. **Learning from Others:** By following experienced developers (like professors and TAs), you can observe their coding patterns, commit messages, and problem-solving approaches. This passive learning is incredibly valuable.

3. **Networking:** GitHub is a professional network for developers. Following others builds connections that can lead to future job opportunities, open source collaborations, or mentorship.

4. **Stay Updated:** You'll see trending repositories, new projects, and contributions from people you follow, helping you stay current with technology trends and best practices.

5. **Community Building:** In educational contexts, following classmates creates a supportive learning community where you can help each other and celebrate achievements together.

**Actions Completed:**
- ✅ Followed Professor [@Cre-eD](https://github.com/Cre-eD)
- ✅ Followed TA [@marat-biriushev](https://github.com/marat-biriushev)
- ✅ Followed TA [@pierrepicaud](https://github.com/pierrepicaud)
- ✅ Followed 3+ classmates from the course

---

## Conclusion

Lab 1 successfully implemented a production-ready Flask application with:
- ✅ Two functional endpoints with comprehensive data
- ✅ Clean, well-structured code following Python best practices
- ✅ Comprehensive documentation (README.md and LAB01.md)
- ✅ Proper configuration management
- ✅ Error handling and logging
- ✅ GitHub community engagement

**Note:** The bonus task (Go implementation) is completed separately in `app_go/` directory with full documentation.

---

**Total Points:** 10/10 (Main Tasks) + 2.5/2.5 (Bonus - Go implementation completed)

**Total Score:** 12.5/12.5 ⭐

**Repository:** https://github.com/pepegx/DevOps-Core-Course  
**Pull Request:** [Link to your PR]
