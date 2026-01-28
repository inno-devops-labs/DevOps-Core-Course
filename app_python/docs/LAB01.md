# Lab 1 — DevOps Info Service (Python)

## Framework Selection
- **Choice:** Flask
- **Why:** Lightweight, minimal boilerplate, easy routing for two endpoints, and widely used for small internal services.

### Comparison Table
| Option | Pros | Cons |
|-------|------|------|
| **Flask** | Simple, flexible, quick to implement | Less “built-in” structure |
| **FastAPI** | Async-ready, auto OpenAPI docs | Slightly more concepts upfront |
| **Django** | Full stack batteries included | Overkill for 2 endpoints |

## Best Practices Applied
- **Clean code organization:** helper functions for system/runtime/request info.  
  This keeps `app.py` readable and makes it easy to extend later (for example, adding more fields or endpoints without touching every route).
- **Configuration via env vars:** `HOST`, `PORT`, `DEBUG`.  
  This lets the same code run in different environments (local, Docker, Kubernetes) just by changing environment variables instead of editing source.
- **Logging:** basic logging configuration + request debug logs.  
  Logs are critical for debugging in production; they show what requests were made and help trace issues after they happen.
- **Error handling:** JSON `404` and `500` responses.  
  Consistent JSON errors make it easier for clients and monitoring tools to handle failures automatically.
- **Reproducible deps:** pinned `Flask==3.1.0` in `requirements.txt`.  
  Pinning versions avoids “works on my machine” issues by ensuring every environment installs the same library versions.

## API Documentation
### `GET /`
Returns service metadata, system info, runtime info, request info, and endpoints list.
Example response:
```bash
{"endpoints":[{"description":"Service information","method":"GET","path":"/"},{"description":"Health check","method":"GET","path":"/health"}],"request":{"client_ip":"127.0.0.1","method":"GET","path":"/","user_agent":"curl/8.5.0"},"runtime":{"current_time":"2026-01-28T09:36:55.695Z","timezone":"UTC","uptime_human":"0 hours, 0 minutes","uptime_seconds":8},"service":{"description":"DevOps course info service","framework":"Flask","name":"devops-info-service","version":"1.0.0"},"system":{"architecture":"x86_64","cpu_count":16,"hostname":"linh","platform":"Linux","platform_version":"Linux-6.14.0-37-generic-x86_64-with-glibc2.39","python_version":"3.12.3"}}
```

### `GET /health`
Returns health status, UTC timestamp, and uptime seconds.
Example response:
```bash
{"status":"healthy","timestamp":"2026-01-28T09:37:38.745Z","uptime_seconds":51}
```
## Testing Commands
```bash
cd app_python
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

python app.py
curl -s http://localhost:5000/ | jq .
curl -s http://localhost:5000/health | jq .
```

## Testing Evidence
Screenshots in `app_python/docs/screenshots/`:
- [python-health-endpoint](/app_python/docs/screenshots/python-health-endpoint.jpg)
- [python-main-endpoint](/app_python/docs/screenshots/python-main-endpoint.jpg)
- [python-raw-main-and-health-endpoints](/app_python/docs/screenshots/python-raw-main-and-health-endpoints.jpg)

## Challenges & Solutions
- Instructions are clear so there were not some big challenges or troubles.

## GitHub Community
Starring repos helps with discovery/bookmarking and signals support to maintainers. Following developers (instructors/classmates) improves collaboration and helps you learn from their activity over time.
