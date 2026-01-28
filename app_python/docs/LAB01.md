# Lab 01 - DevOps Info Service Implementation

## Framework Selection

### Chosen Framework: Flask 3.1

**Rationale:**

Flask was selected for this project due to its simplicity, flexibility, and perfect fit for microservices. For a lightweight information service that doesn't require database ORM or complex middleware, Flask provides the optimal balance of features and overhead.

### Framework Comparison

| Feature | Flask | FastAPI | Django |
|---------|-------|---------|--------|
| **Learning Curve** | Low | Medium | High |
| **Performance** | Good | Excellent | Good |
| **Async Support** | Limited | Native | Limited |
| **Documentation** | Excellent | Excellent | Excellent |
| **Auto API Docs** | No | Yes | No |
| **ORM Included** | No | No | Yes |
| **Best For** | Simple APIs, Microservices | Modern async APIs | Full web apps |
| **Startup Time** | Fast | Fast | Slow |

**Decision Factors:**

1. **Project Requirements**: Simple REST endpoints with JSON responses - Flask excels at this
2. **Simplicity**: Minimal boilerplate, easy to understand and maintain
3. **Maturity**: Battle-tested framework with extensive community support
4. **Flexibility**: No enforced structure, easy to adapt as requirements evolve
5. **Dependencies**: Lightweight with minimal external dependencies

## Best Practices Applied

### 1. Clean Code Organization

**Module-level docstring** provides clear description of the file's purpose:
```python
"""
DevOps Info Service
Main application module
"""
```

**Function docstrings** document purpose and behavior:
```python
def get_system_info():
    """Collect system information."""
```

**Logical grouping** of imports and configuration:
- Standard library imports first
- Third-party imports (Flask) second
- Clear separation between configuration and logic

**Importance**: Clean code organization improves maintainability, makes onboarding easier, and reduces bugs through better readability.

### 2. Error Handling

Implemented custom error handlers for common HTTP errors:

```python
@app.errorhandler(404)
def not_found(error):
    return jsonify({
        'error': 'Not Found',
        'message': 'Endpoint does not exist'
    }), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({
        'error': 'Internal Server Error',
        'message': 'An unexpected error occurred'
    }), 500
```

**Importance**: Proper error handling provides consistent API responses, makes debugging easier, and improves user experience by returning meaningful error messages.

### 3. Logging

Configured structured logging with appropriate formatting:

```python
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)
```

**Importance**: Logging is critical for production monitoring, debugging issues, and understanding application behavior. Structured logs make it easier to parse and analyze in log aggregation systems.

### 4. Configuration via Environment Variables

Made the application configurable without code changes:

```python
HOST = os.getenv('HOST', '0.0.0.0')
PORT = int(os.getenv('PORT', 5000))
DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'
```

**Importance**: Following the 12-factor app methodology, configuration through environment variables enables running the same code in different environments (dev, staging, prod) without modification.

### 5. Dependency Management

Created `requirements.txt` with pinned versions:

```txt
Flask==3.1.0
Werkzeug==3.1.3
```

**Importance**: Pinning exact versions ensures reproducible builds, prevents unexpected breakages from dependency updates, and makes deployments more reliable.

## API Documentation

### Main Endpoint

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
    "hostname": "MacBook-Pro",
    "platform": "Darwin",
    "platform_version": "macOS-14.2-arm64",
    "architecture": "arm64",
    "cpu_count": 8,
    "python_version": "3.11.5"
  },
  "runtime": {
    "uptime_seconds": 120,
    "uptime_human": "0 hours, 2 minutes",
    "current_time": "2026-01-29T10:30:45.123456+00:00",
    "timezone": "UTC"
  },
  "request": {
    "client_ip": "127.0.0.1",
    "user_agent": "curl/8.1.2",
    "method": "GET",
    "path": "/"
  },
  "endpoints": [
    {"path": "/", "method": "GET", "description": "Service information"},
    {"path": "/health", "method": "GET", "description": "Health check"}
  ]
}
```

### Health Check Endpoint

**Request:**
```bash
curl http://localhost:5000/health
```

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2026-01-29T10:30:45.123456+00:00",
  "uptime_seconds": 120
}
```

### Testing Commands

```bash
# Test main endpoint
curl http://localhost:5000/

# Test health endpoint
curl http://localhost:5000/health

# Test with custom port
PORT=8080 python app.py
curl http://localhost:8080/

# Pretty print output
curl http://localhost:5000/ | python -m json.tool

# Test error handling
curl http://localhost:5000/nonexistent
```

## Testing Evidence

### Required Screenshots

1. **01-main-endpoint.png**: Main endpoint showing complete JSON response
2. **02-health-check.png**: Health check response
3. **03-formatted-output.png**: Pretty-printed output using jq or json.tool

**Note**: Screenshots should be placed in `app_python/docs/screenshots/` directory.

## Challenges & Solutions

### Challenge 1: Uptime Formatting

**Problem**: Needed to display uptime in both seconds (for programmatic use) and human-readable format.

**Solution**: Created a `get_uptime()` function that returns both formats, calculating hours and minutes from total seconds. Used conditional pluralization for better readability.

### Challenge 2: Environment Variable Type Conversion

**Problem**: Environment variables are strings, but PORT needs to be an integer and DEBUG needs to be boolean.

**Solution**: Used `int()` for PORT conversion and implemented string comparison for DEBUG flag with `.lower() == 'true'` to handle various input formats.

### Challenge 3: Timezone Handling

**Problem**: System time needed to be in UTC for consistency across different deployments.

**Solution**: Used `datetime.now(timezone.utc)` instead of `datetime.now()` to ensure all timestamps are UTC-based, making the service timezone-agnostic.

## GitHub Community

### Why Starring Repositories Matters

Starring repositories in open source serves multiple purposes: it bookmarks projects for future reference, signals appreciation to maintainers, and helps projects gain visibility. High star counts indicate community trust and can attract more contributors, creating a positive feedback loop that improves project quality.

### Professional Growth Through Following

Following developers on GitHub enables professional networking and continuous learning. You discover new projects through their activity, learn from their code patterns and commit history, and build connections that extend beyond the classroom. This practice helps you stay current with industry trends and can lead to collaboration opportunities.

### Actions Completed

- [x] Starred the course repository
- [x] Starred [simple-container-com/api](https://github.com/simple-container-com/api)
- [x] Followed Professor [@Cre-eD](https://github.com/Cre-eD)
- [x] Followed TA [@marat-biriushev](https://github.com/marat-biriushev)
- [x] Followed TA [@pierrepicaud](https://github.com/pierrepicaud)
- [x] Followed 3+ classmates

## Implementation Summary

The DevOps Info Service successfully implements all required functionality:
- Two working endpoints with comprehensive information
- Configurable via environment variables
- Clean, maintainable code following Python best practices
- Proper error handling and logging
- Production-ready structure suitable for containerization and deployment

The service provides a solid foundation for future labs where we'll add containerization, CI/CD pipelines, monitoring, and deployment automation.
