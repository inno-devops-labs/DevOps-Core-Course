
---

# Lab 1 — DevOps Info Service: FastAPI Implementation

## 1. Framework Selection

**Chosen Framework:** FastAPI

**Reason for choice:**
- Modern Python framework with native support for **asynchronous endpoints**.
- Automatically generates **interactive API documentation** (Swagger/OpenAPI).
- Lightweight and highly performant, suitable for microservices and DevOps tooling.

**Comparison with alternatives:**

| Framework | Pros | Cons |
|-----------|------|------|
| **FastAPI** | Async support, auto documentation, modern features | Smaller community than Django, newer framework |
| Flask | Lightweight, easy to learn | No async support out-of-the-box, manual documentation |
| Django | Full-featured, includes ORM, mature ecosystem | Heavyweight, more setup, more boilerplate code |

---

## 2. Best Practices Applied

**1. Logging**

```python
# Logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)
````

* Logs all incoming requests and errors.
* Helps **monitor application behavior** in production.

**2. Error Handling**

```python
@app.exception_handler(404)
async def not_found(request: Request, exc):
    return JSONResponse(
        status_code=404,
        content={
            "error": "Not Found",
            "message": "Endpoint does not exist"
        }
    )


@app.exception_handler(500)
async def internal_error(request: Request, exc):
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal Server Error",
            "message": "An unexpected error occurred"
        }
    )
```

* Provides **standardized responses** for 404 and 500 errors.
* Prevents server crashes and improves API reliability.

**3. Clean Code & PEP8**

* Clear function names and modular structure.
* Adherence to PEP8 ensures **readability and maintainability**.

**4. Configuration via Environment Variables**

```python
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", 5000))
DEBUG = os.getenv("DEBUG", "false").lower() == "true"
```

* Makes the app **flexible and deployable** on different environments.



## 3. API Documentation

**Endpoints:**

1. **`GET /`** — Returns service, system, runtime, and request information.

```bash
curl http://127.0.0.1:5000/
```

**Example JSON Response:**

```json
{
  "service": {
    "name": "devops-info-service",
    "version": "1.0.0",
    "description": "DevOps course info service",
    "framework": "FastAPI"
  },
  "system": {
    "hostname": "MacBook-Pro-George.local",
    "platform": "Darwin",
    "platform_version": "Darwin Kernel Version 25.2.0",
    "architecture": "arm64",
    "cpu_count": 8,
    "python_version": "3.10.7"
  },
  "runtime": {
    "uptime_seconds": 353,
    "uptime_human": "0 hours, 5 minutes",
    "current_time": "2026-01-28T17:39:15.751921+00:00",
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

2. **`GET /health`** — Returns service health and uptime.

```bash
curl http://127.0.0.1:5000/health
```

**Example JSON Response:**

```json
{
  "status": "healthy",
  "timestamp": "2026-01-28T17:39:15.751921+00:00",
  "uptime_seconds": 353
}
```



## 4. Testing Evidence

**Screenshots required:**

1. Main endpoint showing complete JSON → `01-Main-Endpoint-Json.png`
2. Health check response → `02-Health-Check-Response.png`
3. Pretty-printed JSON → `03-Formatted-output.png`

**Terminal Output:**

```bash
uvicorn app:app --reload --port 5000
curl http://127.0.0.1:5000/
curl http://127.0.0.1:5000/health
```



## 5. Challenges & Solutions

| Challenge                                                                                      | Solution                                                          |
| ---------------------------------------------------------------------------------------------- | ----------------------------------------------------------------- |
| First attempts to run FastAPI returned errors due to incorrect import and endpoint definitions | Fixed function decorators and imported `Request` properly         |
| JSON response formatting issues                                                                | Used Python dicts and UTC timestamps, verified output with `curl` |
| Dependency version conflicts                                                                   | Pinned FastAPI and Uvicorn versions in `requirements.txt`         |



## 6. GitHub Community

During the lab, I:

* Starred the course repository and simple-container-com/api repository
* Followed professor (@Cre-eD), TAs (@marat-biriushev, @pierrepicaud), and three classmates

**Why this matters:**

* **Stars**: help track popular projects, discover useful tools, and support open-source maintainers.
* **Following developers**: improves networking, allows learning from others’ code, and helps stay updated with new projects.


