# Lab 1 Submission: DevOps Info Service

## Framework Selection

### Choice: Flask 3.1.0

I selected **Flask** as the web framework for this project after evaluating the available options.

### Comparison Table

| Framework | Pros | Cons | Suitability |
|-----------|------|------|-------------|
| **Flask** ✓ | Lightweight, minimal boilerplate, easy to learn, flexible, large ecosystem | Fewer built-in features than Django, requires manual setup for some features | **High** - Perfect for a simple REST service |
| FastAPI | Modern, async support, automatic OpenAPI docs, type hints | Newer ecosystem, more complex for simple services | Medium - Good but overkill for this use case |
| Django | Full-featured, ORM included, admin panel, batteries included | Heavy, steep learning curve, overkill for simple APIs | Low - Too complex for this project |

### Why Flask?

1. **Simplicity**: Flask's minimal approach allows us to focus on the core functionality without unnecessary complexity
2. **Educational Value**: The framework's explicit nature makes it easier to understand what's happening under the hood
3. **Flexibility**: Easy to add middleware, error handlers, and custom behavior
4. **Industry Adoption**: Widely used in production for microservices and APIs
5. **Documentation**: Excellent documentation and large community support

For a simple REST API with two endpoints, Flask provides the right balance of simplicity and power.

---

## Best Practices Applied

### 1. Clean Code Organization

**Implementation:**
```python
def get_uptime():
    """Calculate application uptime."""
    delta = datetime.now(timezone.utc) - START_TIME
    seconds = int(delta.total_seconds())
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60

    human_parts = []
    if hours > 0:
        human_parts.append(f"{hours} hour{'s' if hours != 1 else ''}")
    if minutes > 0:
        human_parts.append(f"{minutes} minute{'s' if minutes != 1 else ''}")
    if seconds < 60:
        human_parts.append(f"{seconds} second{'s' if seconds != 1 else ''}")

    return {
        'seconds': seconds,
        'human': ', '.join(human_parts) if human_parts else '0 seconds'
    }
```

**Why It Matters:**
- Clear function name that describes what it does
- Proper docstring for documentation
- Single responsibility principle
- Returns structured data for easy JSON serialization

### 2. Error Handling

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

**Why It Matters:**
- Provides consistent JSON error responses
- Prevents stack traces from leaking to clients
- Logs server errors for debugging
- Follows REST API best practices

### 3. Structured Logging

**Implementation:**
```python
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

logger.info(f'Starting DevOps Info Service on {HOST}:{PORT}')
logger.info(f'Serving info request from {request.remote_addr}')
```

**Why It Matters:**
- Enables debugging and monitoring
- Provides audit trail of requests
- Helps diagnose production issues
- Structured format makes logs searchable

### 4. Environment Configuration

**Implementation:**
```python
HOST = os.getenv('HOST', '0.0.0.0')
PORT = int(os.getenv('PORT', 5000))
DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'
```

**Why It Matters:**
- **12-Factor App** compliance
- Same code works in dev/staging/prod
- No hardcoded configuration
- Easy deployment flexibility

### 5. Proper Dependency Management

**Implementation:**
```txt
Flask==3.1.0
Werkzeug==3.1.3
```

**Why It Matters:**
- Reproducible builds
- Prevents dependency conflicts
- Clear dependency documentation
- Security through pinned versions

---

## API Documentation

### Endpoint: GET /

**Description:** Returns comprehensive service and system information

**Request:**
```bash
curl http://localhost:5000/
```

**Response (200 OK):**
```json
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
    "user_agent": "curl/8.7.1"
  },
  "runtime": {
    "current_time": "2026-01-27T19:16:13.123098+00:00",
    "timezone": "UTC",
    "uptime_human": "8 seconds",
    "uptime_seconds": 8
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
    "hostname": "Mac",
    "platform": "Darwin",
    "platform_version": "Darwin Kernel Version 25.2.0: Tue Nov 18 21:08:48 PST 2025; root:xnu-12377.61.12~1/RELEASE_ARM64_T8132",
    "python_version": "3.13.1"
  }
}
```

### Endpoint: GET /health

**Description:** Simple health check for monitoring and Kubernetes probes

**Request:**
```bash
curl http://localhost:5000/health
```

**Response (200 OK):**
```json
{
  "status": "healthy",
  "timestamp": "2026-01-27T19:16:41.080927+00:00",
  "uptime_seconds": 35
}
```

### Error Responses

**404 Not Found:**
```json
{
  "error": "Not Found",
  "message": "Endpoint does not exist"
}
```

**500 Internal Server Error:**
```json
{
  "error": "Internal Server Error",
  "message": "An unexpected error occurred"
}
```

### Testing Commands

```bash
# Test main endpoint
curl http://localhost:5000/

# Test with pretty JSON
curl http://localhost:5000/ | jq

# Test health endpoint
curl http://localhost:5000/health

# Test with custom port
PORT=8080 python app.py
curl http://localhost:8080/

# Test from another machine
curl http://192.168.1.100:5000/

# Test with verbose output
curl -v http://localhost:5000/health

# Test error handling
curl http://localhost:5000/nonexistent
```

---

## Testing Evidence

### Main Endpoint Screenshot

![Main Endpoint](screenshots/01-main-endpoint.png)

The main endpoint successfully returns all required information:
- Service metadata (name, version, description, framework)
- System information (hostname, platform, architecture, CPU, Python version)
- Runtime data (uptime in seconds and human format, current time, timezone)
- Request details (client IP, user agent, method, path)
- List of available endpoints

### Health Check Screenshot

![Health Check](screenshots/02-health-check.png)

The health endpoint returns the expected status with timestamp and uptime.

### Formatted Output Screenshot

![Formatted Output](screenshots/03-formatted-output.png)

Pretty-printed JSON output using `jq` for better readability.

---

## Challenges & Solutions

### Challenge 1: Cross-Platform Platform Detection

**Problem:** Different operating systems return platform information in different formats. For example, macOS returns "Darwin" as the platform name, while Linux returns "Linux".

**Solution:** Used Python's `platform` module which abstracts these differences:
```python
import platform

platform.system()      # Returns 'Linux', 'Darwin', 'Windows', etc.
platform.machine()     # Returns 'x86_64', 'arm64', etc.
platform.version()     # Returns detailed version info
```

This provides consistent behavior across platforms.

### Challenge 2: Human-Readable Uptime Format

**Problem:** Converting raw seconds into a human-readable format that handles singular/plural correctly and doesn't show unnecessary components.

**Solution:** Implemented smart formatting that only shows relevant time units:
```python
human_parts = []
if hours > 0:
    human_parts.append(f"{hours} hour{'s' if hours != 1 else ''}")
if minutes > 0:
    human_parts.append(f"{minutes} minute{'s' if minutes != 1 else ''}")
if seconds < 60:
    human_parts.append(f"{seconds} second{'s' if seconds != 1 else ''}")
```

This produces output like:
- "1 hour, 30 minutes" (not "1 hours, 30 minutes")
- "45 seconds" (for short uptimes)
- "2 hours, 15 minutes, 30 seconds" (for complete breakdown)

### Challenge 3: UTC Timestamp Formatting

**Problem:** Ensuring timestamps are in UTC and properly formatted in ISO 8601 format with 'Z' suffix for consistency.

**Solution:** Used `datetime.now(timezone.utc)` and explicit ISO formatting:
```python
from datetime import datetime, timezone

now = datetime.now(timezone.utc)
timestamp = now.isoformat()  # Produces '2026-01-27T12:00:00.000Z'
```

This ensures timestamps are timezone-aware and consistently formatted.

### Challenge 4: Client IP Detection

**Problem:** When running locally, `request.remote_addr` might return '::1' (IPv6 localhost) or '127.0.0.1' (IPv4 localhost).

**Solution:** Flask handles this automatically via `request.remote_addr`, which returns the appropriate IP. For production behind a proxy, we would need to check `X-Forwarded-For` headers, but for local development, the default behavior is sufficient.

### Challenge 5: Environment Variable Type Conversion

**Problem:** Environment variables are always strings, but PORT needs to be an integer and DEBUG needs to be a boolean.

**Solution:** Explicit type conversion:
```python
PORT = int(os.getenv('PORT', 5000))
DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'
```

This ensures proper types and handles case-insensitive boolean values.

---

## GitHub Community

### Why Starring Repositories Matters

Starring repositories on GitHub serves multiple important purposes in the open-source ecosystem:

**Discovery & Bookmarking:** Stars act as bookmarks for interesting projects, making it easy to find them later. The star count also signals project popularity and community trust, helping other developers identify quality tools.

**Open Source Signal:** starring encourages maintainers by showing appreciation for their work. High star counts help projects gain visibility in GitHub search results and recommendations, attracting more contributors and users.

**Professional Context:** Your starred repositories appear on your GitHub profile, showcasing your interests and awareness of industry-standard tools to potential employers and collaborators.

### Why Following Developers Helps

Following developers on GitHub is valuable for several reasons:

**Networking:** Following your professor, TAs, and classmates helps you stay connected with the development community. You can see what projects they're working on and discover new tools through their activity.

**Learning:** By following experienced developers, you can learn from their code, commits, and how they solve problems. This is especially valuable when learning new technologies or best practices.

**Collaboration:** Staying updated on classmates' work makes it easier to find team members for future projects and builds a supportive learning community beyond the classroom.

**Career Growth:** Following thought leaders in your technology stack helps you stay current with trending projects and industry developments, while building your visibility in the developer community.

### Actions Taken

For this lab, I have:
1. ⭐ Starred the course repository
2. ⭐ Starred the [simple-container-com/api](https://github.com/simple-container-com/api) project
3. 👤 Followed the professor and TAs:
   - [@Cre-eD](https://github.com/Cre-eD)
   - [@marat-biriushev](https://github.com/marat-biriushev)
   - [@pierrepicaud](https://github.com/pierrepicaud)
4. 👤 Followed at least 3 classmates from the course

---

## Conclusion

This lab provided a solid foundation in Python web development and REST API design. The implemented service follows production best practices including:

- Clean, modular code structure
- Comprehensive error handling
- Structured logging
- Environment-based configuration
- Complete documentation

The service is ready for the next phases of the course, including containerization with Docker, CI/CD with GitHub Actions, and deployment to Kubernetes.
