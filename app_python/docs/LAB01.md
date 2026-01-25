# LAB01 — Python Web Application (DevOps Info Service)

## 1) Framework Selection

### Chosen framework: Flask
I chose **Flask** because it is a lightweight Python web framework that is quick to set up for small REST services and does not force a heavy project structure. 
For this lab (two endpoints + JSON responses + basic best practices) Flask keeps the implementation minimal and easy to explain.

### Comparison table
| Framework | Pros                                        | Cons                                                 | Fit for this lab            |
|-----------|---------------------------------------------|------------------------------------------------------|-----------------------------|
| Flask     | Lightweight, flexible, easy to learn        | Fewer built-in components than full-stack frameworks | Best match (simple service) |
| FastAPI   | Async-first, automatic OpenAPI docs         | More concepts (ASGI, Pydantic), more setup           | Good, but not required here |
| Django    | Full-featured framework, batteries included | Overkill for 2 endpoints                             | Too heavy for LAB01 scope   |

---

## 2) Best Practices Applied

### 2.1 Clean code organization (helpers + constants)
I separated logic into small functions (`get_system_info`, `get_uptime`, `get_request_info`) to keep routes readable and maintainable.

### 2.2 Environment-based configuration (12-factor style)
The service can be configured via environment variables to run in different environments without changing code.

```python
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", "5000"))
DEBUG = os.getenv("DEBUG", "false").lower() == "true"
```

### 2.3 Logging (visibility & debugging)
A structured logging format is configured at startup. Each request is logged via a before_request hook. 

```python
logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO").upper(),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("devops-info-service")

@app.before_request
def log_request():
    logger.info("%s %s from %s", request.method, request.path, request.remote_addr)
```

### 2.4 Error handling (JSON responses instead of HTML)
Custom handlers return JSON for 404 and 500, which is standard for API-style services.

```python
@app.errorhandler(404)
def not_found(_error):
    return jsonify({"error": "Not Found", "message": "Endpoint does not exist"}), 404

@app.errorhandler(500)
def internal_error(_error):
    logger.exception("Internal error")
    return jsonify({"error": "Internal Server Error", "message": "An unexpected error occurred"}), 500
```

### 2.5 Request data handling (headers, client IP)
Request metadata is taken from Flask’s request object (headers, path, method, remote address).

```python
def get_request_info() -> dict:
    forwarded_for = request.headers.get("X-Forwarded-For", "").split(",").strip()
    client_ip = forwarded_for or request.remote_addr
    user_agent = request.headers.get("User-Agent", "")
    return {
        "client_ip": client_ip,
        "user_agent": user_agent,
        "method": request.method,
        "path": request.path,
    }
```

## 3) API Documentation
### 3.1 Endpoints
- GET `/` — service + system + runtime + request information.
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
        "user_agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36"
      },
      "runtime": {
        "current_time": "2026-01-25T20:42:30.631Z",
        "timezone": "UTC",
        "uptime_human": "0 hours, 8 minutes",
        "uptime_seconds": 508
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
        "hostname": "Mac.ufanet.ru",
        "platform": "Darwin",
        "platform_version": "macOS-15.6.1-arm64-arm-64bit",
        "python_version": "3.12.10"
      }
    }
    ```
- GET `/health` — health status + timestamp + uptime.
    ```json
    {
      "status": "healthy",
      "timestamp": "2026-01-25T20:38:07.959Z",
      "uptime_seconds": 246
    }
    ```

### 3.2 Example requests
Run the app:
```bash
python3 app.py
# Custom config:
HOST=127.0.0.1 PORT=3000 DEBUG=true python app.py
```
Test endpoints:
```bash
curl -i http://127.0.0.1:5000/
curl -i http://127.0.0.1:5000/health
```
Pretty-print JSON:
```bash
curl -s http://127.0.0.1:5000/ | python3 -m json.tool
curl -s http://127.0.0.1:5000/health | python3 -m json.tool
```
## 4) Testing Evidence (Screenshots)
Screenshots are stored in docs/screenshots/:
- 01-main-endpoint.png — GET `/` full JSON response.
  ![](screenshots/01-main-endpoint.png)
- 02-health-check.png — GET `/health` response.
  ![](screenshots/02-health-check.png)
- 03-formatted-output.png — pretty-printed JSON output (python -m json.tool).
  ![](screenshots/03-formatted-output.png)

## 5) Challenges & Solutions
- OS version formatting: Different systems expose OS version differently, so I used a helper that tries `platform.freedesktop_os_release()` when available and falls back to `platform.platform()`.
- Client IP behind proxy: If the service is behind a reverse proxy, the real IP may be in `X-Forwarded-For`, so I check that header first, then fall back to `request.remote_addr`.

## 6) GitHub Community
Starring repositories helps with discovery/bookmarking and signals support to maintainers, which can increase a project’s visibility and contributions over time.

Following developers helps you stay aware of teammates’ work, learn from their activity, and collaborate more effectively in team projects.