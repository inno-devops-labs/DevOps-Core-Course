# LAB01

---

## Example responses

GET `/` returns JSON similar to:

```json
{
  "service": {
    "name": "devops-info-service",
    "version": "1.0.0",
    "description": "DevOps course info service",
    "framework": "FastAPI"
  },
  "system": {
    "hostname": "my-host",
    "platform": "Linux",
    "platform_version": "Ubuntu 22.04",
    "architecture": "x86_64",
    "cpu_count": 4,
    "python_version": "3.11.3"
  },
  "runtime": {
    "uptime_seconds": 123,
    "uptime_human": "0 hours, 2 minutes",
    "current_time": "2026-01-07T14:30:00+00:00",
    "timezone": "UTC"
  },
  "request": {
    "client_ip": "127.0.0.1",
    "user_agent": "curl/7.81.0",
    "method": "GET",
    "path": "/"
  },
  "endpoints": [
    { "path": "/", "method": "GET", "description": "Service information" },
    { "path": "/health", "method": "GET", "description": "Health check" }
  ]
}
```

GET `/health` returns:

```json
{
  "status": "healthy",
  "timestamp": "2026-01-07T14:30:00+00:00",
  "uptime_seconds": 123
}
```

---

## Best-practices applied

- Non-root execution in Docker images
- Minimal and reproducible images
- JSON responses are deterministic and structured for automated monitoring and probes
- Health endpoint returns HTTP 200 when healthy and includes uptime and timestamp for observability
- Error handlers return JSON (FastAPI custom handlers and Go custom 404) to make behavior consistent for API clients
- Configuration via environment variables for easy orchestration

---
