# Lab 1 — DevOps Info Service: Web Application Development

## Framework Selection

**Chosen Framework:** FastAPI  

**Reason for Selection:**  
I have daily experience working with FastAPI, which allows me to implement asynchronous endpoints easily, provides automatic API documentation (Swagger / ReDoc), and enforces modern Python type hints. This makes the development process faster, code more maintainable, and improves the API usability for consumers.

**Comparison Table with Alternatives:**

| Framework   | Pros                                                | Cons |
|-------------|-----------------------------------------------------|------|
| **FastAPI** | Async support, modern Python typing, automatic docs | Requires understanding of async for full benefits |
| Flask       | Lightweight, simple for beginners, many tutorials   | No built-in async, less strict type enforcement |
| Django      | Full-featured, ORM included, scalable               | Overkill for small APIs, steeper learning curve |

---

## Best Practices Applied

1. **Clean Code & Function Separation**
    ```python
    def get_system_info() -> dict[str, str | int | None]:
        ...
    ```
    Functions are modular, reusable, and easy to test. Each function has a single responsibility.

2. **Type Hints**
    ```python
    def get_runtime_info() -> dict[str, str | int | None]:
        ...
    ```
    Improves code readability, enables static analysis (mypy / Pylance), and reduces runtime bugs.

3. **Error Handling & Defaults**
    ```python
    "client_ip": request.client.host if request.client else "Unknown"
    ```
    Prevents runtime errors if optional attributes are missing. Provides safe fallback values.

4. **Environment Configuration**
    ```python
    HOST = os.getenv("HOST", "0.0.0.0")
    PORT = int(os.getenv("PORT", 5000))
    DEBUG = os.getenv("DEBUG", "False").lower() == "true"
    ```
    Allows running the service in different environments (development, production) without changing code.

---

## API Documentation

### 1. Main Endpoint — `GET /`

Returns comprehensive information about the service, system, runtime, request, and available endpoints.

**Example Response:**

```json
{
  "service": {
    "name": "Python Web Application",
    "version": "1.0",
    "description": "Simple production-ready Python web service with comprehensive system information",
    "framework": "FastAPI"
  },
  "system": {
    "hostname": "my-laptop",
    "platform": "Linux",
    "platform_version": "Ubuntu 24.04",
    "architecture": "x86_64",
    "cpu_count": 8,
    "python_version": "3.13.1"
  },
  "runtime": {
    "uptime_seconds": 3600,
    "uptime_human": "1 hour, 0 minutes",
    "current_time": "2026-01-25T14:30:00.000Z",
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

### 2. Health Check — `GET /health`

Returns the service health status and uptime.

**Example Response:**

```json
{
  "status": "healthy",
  "timestamp": "2026-01-25T14:30:00.000Z",
  "uptime_seconds": 3600
}
```

### Testing Commands

```bash
# Main endpoint
curl http://127.0.0.1:5000/

# Health check
curl http://127.0.0.1:5000/health
```

---

## Testing Evidence

* **Screenshots:** Place in `docs/screenshots/`

  * `01-main-endpoint.png` — output of `GET /`
  * `02-health-check.png` — output of `GET /health`
  * `03-formatted-output.png` — pretty-printed JSON in terminal

* **Terminal Output Example:**

```bash
% curl http://127.0.0.1:8080/ | jq   

  % Total    % Received % Xferd  Average Speed   Time    Time     Time  Current
                                 Dload  Upload   Total   Spent    Left  Speed
100   792  100   792    0     0   328k      0 --:--:-- --:--:-- --:--:--  386k
{
  "service": {
    "name": "Python Web Application",
    "version": "1.0",
    "description": "Simple production-ready Pythonweb service with comprehensive system information",
    "framework": "FastAPI"
  },
  "system": {
    "hostname": "gleb-mac.local",
    "platform": "Darwin",
    "platform_version": "Darwin Kernel Version 24.6.0: Wed Nov  5 21:34:00 PST 2025; root:xnu-11417.140.69.705.2~1/RELEASE_ARM64_T8132",
    "architecture": "arm64",
    "cpu_count": 10,
    "python_version": "3.14.0"
  },
  "runtime": {
    "uptime_seconds": 218,
    "uptime_human": "0 hours, 3 minutes",
    "current_time": "2026-01-25T19:33:45.771658",
    "timezone": "MSK"
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

---

## Challenges & Solutions

1. **Issue:** `request.client` could be `None`
   **Solution:** Added a safe fallback:

   ```python
   client_ip = request.client.host if request.client else "Unknown"
   ```

## GitHub Community

Starring repositories is important in open source because it helps you bookmark useful projects, shows appreciation to maintainers, and signals project popularity to the community. Following developers allows you to stay updated on their work, learn from their code, discover new projects, and build professional connections that support collaboration and career growth.
