# Lab 1 — DevOps Info Service (Python)

## Framework Selection
- **Choice:** Flask
- **Why:** Easiest to implement and support, has enough functionality for required software

### Comparison Table
| Option | Pros | Cons |
|-------|------|------|
| **Flask** | Simple, flexible, quick to implement | Less “built-in” structure |
| **FastAPI** | Async-ready, auto OpenAPI docs | Slightly more concepts upfront |
| **Django** | Full stack batteries included | Overkill for 2 endpoints |

## Best Practices Applied
- **Clean code organization:** standartized code style with meaningful names.
  This ensures other developers can understand what's happening right away.
- **Configuration via env vars:** `HOST`, `PORT`, `DEBUG`.  
  Env variables lets change programm behaviour without changing any code.
- **Logging:** basic logging
  Logs are critical for debugging in production; they show what requests were made and help trace issues after they happen.
- **Error handling:** `404` and `500` responses.  
  Errors wont cause programm to stop, crash, or cause any unexpected behaviour.
- **Reproducible deps:** pinned `Flask==3.1.0` in `requirements.txt`.  
  Using specific version in requirements.txt ensures the software works on different machines, and won't break due to version mismatches
## API Documentation
### `GET /`
Returns service metadata, system info, runtime info, request info, and endpoints list.
Example response:
```bash
{"endpoints":[{"description":"Service information","method":"GET","path":"/"},{"description":"Health check","method":"GET","path":"/health"}],"request":{"client_ip":"127.0.0.1","method":"GET","path":"/","user_agent":"Mozilla/5.0 (X11; Linux x86_64; rv:146.0) Gecko/20100101 Firefox/146.0"},"runtime":{"current_time":"2026-01-28T14:54:41.735Z","timezone":"UTC","uptime_human":"0 hours, 0 minutes","uptime_seconds":22},"service":{"description":"DevOps course info service","framework":"Flask","name":"devops-info-service","version":"1.0.0"},"system":{"architecture":"x86_64","cpu_count":8,"hostname":"host","platform":"Linux","platform_version":"Linux-6.17.13-hardened1-2-hardened-x86_64-with-glibc2.42","python_version":"3.14.2"}}```
```
### `GET /health`
Returns health status, UTC timestamp, and uptime seconds.
Example response:
```bash
{"status":"healthy","timestamp":"2026-01-28T14:54:24.458Z","uptime_seconds":4}```
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
All screenshots are located in `app_python/docs/screenshots/`

## Challenges & Solutions
No challenges were encountered during the implementation.

## GitHub Community
Starring repos helps to discover them, and add some "trust" to using software in them.  Following developers just notifies you about their activity.
