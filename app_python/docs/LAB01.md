# Lab 01 - DevOps Info Service (Python / FastAPI)

## 1. Framework Selection

Chosen framework: FastAPI 0.115.0.

FastAPI was selected because it keeps the service small while adding strong typing, built-in validation, and automatic API documentation at `/docs`. It is also a natural fit for modern DevOps services that may grow over time.

Comparison summary:

| Framework | Strengths | Trade-offs | Fit for Lab 01 |
| --- | --- | --- | --- |
| FastAPI | Type hints, validation, auto docs, async-ready | Requires ASGI server (Uvicorn) | Best balance of speed and future growth |
| Flask | Very simple and flexible | Less built-in structure and typing | Strong alternative for minimal APIs |
| Django | Full-featured framework with ORM and admin | Heavy for a two-endpoint service | Overkill for this lab |

## 2. Best Practices Applied

Key practices implemented in `app_python/app.py`:

1. Clear structure and small functions. Examples include `get_system_info()`, `get_runtime_info()`, and `get_request_info(request)`.
2. Configuration via environment variables. Variables: `HOST`, `PORT`, and `DEBUG`, with safer parsing handled by `_get_env_port()` and `_get_env_bool()`.
3. Logging for observability. Logging is configured once in `_configure_logging()`, and requests are logged through `@app.middleware("http")`.
4. JSON error handling. A custom 404 response is implemented via `@app.exception_handler(StarletteHTTPException)`, and a 500 handler is implemented via `@app.exception_handler(Exception)`.
5. Reproducible dependencies. `app_python/requirements.txt` pins `fastapi==0.115.0` and `uvicorn[standard]==0.32.0`.
6. Clean repository hygiene. `app_python/.gitignore` excludes environments, caches, logs, and IDE files.

Why this matters:
- Small focused functions are easier to test and reuse.
- Environment-based config is standard in DevOps workflows.
- Logging and consistent JSON errors improve debugging and monitoring.

## 3. API Documentation

### GET / - Service and System Information

Example request:

```bash
curl http://127.0.0.1:5000/
```

Example response (values depend on your machine):

```json
{
  "service": {
    "name": "devops-info-service",
    "version": "1.0.0",
    "description": "DevOps course info service",
    "framework": "FastAPI"
  },
  "system": {
    "hostname": "MY-PC",
    "platform": "Windows",
    "platform_version": "10.0.22631",
    "architecture": "AMD64",
    "cpu_count": 16,
    "python_version": "3.11.9"
  },
  "runtime": {
    "uptime_seconds": 12,
    "uptime_human": "0 minutes, 12 seconds",
    "current_time": "2026-01-27T10:10:00.000Z",
    "timezone": "Pacific Standard Time"
  },
  "request": {
    "client_ip": "127.0.0.1",
    "user_agent": "curl/8.0.0",
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

### GET /health - Health Check

Example request:

```bash
curl http://127.0.0.1:5000/health
```

Example response:

```json
{
  "status": "healthy",
  "timestamp": "2026-01-27T10:10:05.000Z",
  "uptime_seconds": 17
}
```

### Pretty-Printed Output

```bash
curl http://127.0.0.1:5000/ | python -m json.tool
```

## 4. Testing Evidence

Endpoints can be verified locally by running the app and calling both routes:

```bash
# From app_python/
uvicorn app:app --host 0.0.0.0 --port 5000

curl http://127.0.0.1:5000/
curl http://127.0.0.1:5000/health
curl http://127.0.0.1:5000/ | python -m json.tool
```

Alternative run command:

```bash
python app.py
```

Screenshots directory:
- `app_python/docs/screenshots/01-main-endpoint.png`
- `app_python/docs/screenshots/02-health-check.png`
- `app_python/docs/screenshots/03-formatted-output.png`

Note: placeholder PNG files were created in this environment. Replace them with real screenshots from your machine, browser, or terminal.

## 5. Challenges and Solutions

1. Robust environment parsing. Problem: `PORT` can be missing or invalid. Solution: `_get_env_port()` validates and falls back safely with a warning.
2. Consistent timestamps. Problem: mixed local vs UTC time formats. Solution: `_iso_utc_now()` always returns UTC with a `Z` suffix.
3. Friendly 404 responses in FastAPI. Problem: the default 404 is not in the requested lab format. Solution: a custom handler for `StarletteHTTPException` returns the required JSON for 404 while preserving default handling for other HTTP errors.

## 6. GitHub Community

Starring repositories helps with discovery, bookmarking, and signaling useful projects to others. Following developers (professor, TAs, and classmates) helps you learn from their activity and makes collaboration easier in team settings.

Actions like starring and following must be done directly in GitHub.

