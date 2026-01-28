# LAB01 - DevOps Info Service (Python / Flask)

## 1. Framework Selection
**Chosen framework:** Flask

**Why Flask:**
- Minimal setup and easy to understand for a first lab
- Clear request/response handling without extra abstractions)
- I tried Django, regretted it

**Comparison Table**
| Framework | Pros | Cons | Why Not Chosen |
|---|---|---|---|
| Flask | Lightweight, simple, widely used | Fewer built-in features | Selected due to simplicity |
| FastAPI | Async, auto-docs, type hints | Slightly more setup | Didn't try it, because of luck of time |
| Django | Full-featured, includes ORM | Heavy for small API | Too much for the first time|

## 2. Best Practices Applied
1. **Clean code organization** - helper functions for system, runtime, and request info
2. **Error handling** - custom 404 and 500 responses
3. **Logging** - structured logging with timestamp and level
4. **Configuration via environment variables** - HOST, PORT, DEBUG
5. **Pinned dependencies** - exact versions in `requirements.txt`

**Code examples (from `app.py`):**
```python
HOST = os.getenv('HOST', '0.0.0.0')
PORT = int(os.getenv('PORT', '5000'))
DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'
```

```python
@app.errorhandler(404)
def not_found(error):
    return jsonify({
        'error': 'Not Found',
        'message': 'Endpoint does not exist'
    }), 404
```

```python
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
```

## 3. API Documentation
### 3.1 `GET /`
**Description:** Returns service, system, runtime, request info, and endpoints.

**Example request:**
```bash
curl http://127.0.0.1:5000/
```

**Example response (truncated):**
```json
{
  "service": {
    "name": "devops-info-service",
    "version": "1.0.0",
    "description": "DevOps course info service",
    "framework": "Flask"
  }
}
```

### 3.2 `GET /health`
**Description:** Health check endpoint for monitoring.

**Example request:**
```bash
curl http://127.0.0.1:5000/health
```

**Example response:**
```json
{
  "status": "healthy",
  "timestamp": "2026-01-28T17:31:00.456Z",
  "uptime_seconds": 180
}
```

### 3.3 Swagger UI
**OpenAPI spec:**
```
GET /swagger.json
```

**Swagger UI:**
```
GET /docs
```
*it was easier to check app with swagger

## 4. Testing Evidence
Add screenshots to `docs/screenshots/` and embed them here.

- **Main endpoint:** `screenshots/01-main-endpoint.png`
- **Health check:** `screenshots/02-health-check.png`
- **Pretty-printed output:** `screenshots/03-formatted-output.png`

## 5. Challenges & Solutions
- **Timezone formatting:** Used UTC with ISO 8601 and `Z` suffix for consistency.
- **Client IP handling:** Added `X-Forwarded-For` fallback for proxy setups.

## 6. GitHub Community
Starring repositories helps to find useful tools and bookmaer them. Following developers improves collaboration by keeping you aware of classmates' and instructors' work, which supports learning and teamwork.
