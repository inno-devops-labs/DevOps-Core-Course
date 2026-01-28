# Lab 01 — Python Web Application

## Framework Selection

**Chosen framework: Flask**

Flask was selected because it is lightweight and easy to build small apps such this

### Framework Comparison

| Framework | Advantages                    | Disadvantages                      | Use Case                     |
| --------- | ----------------------------- | ---------------------------------- | ---------------------------- |
| **Flask** | Simple, lightweight | No async, fewer built-ins | Small apps |
| **FastAPI**   | Async support, OpenAPI docs   | Harder than Flask    | High-performance APIs        |
| **Django**    | Full-featured, with ORM included   | Overkill for small apps        | Large web applications       |

---

## Best Practices Applied

### 1. Clean Code Organization

+ Clear function names (get_uptime(), get_system_info())
+ Comments only where needed
+ Imports grouped according to PEP 8

**Code example:**

```python   
@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": "Not Found", "message": "Endpoint does not exist"}), 404

```

Clean code improves readability, maintainability, and reduces the likelihood of bugs.

### 2. Logging

```python
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger.info('Application starting')
logger.info(f"Request: {request.method} {request.path} from {request.remote_addr}")
```

Tracks full app lifecycle and simplifies debug

### 3. Configuration via env variables
```python
HOST = os.getenv('HOST', '0.0.0.0')
PORT = int(os.getenv('PORT', 5000))
DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'
```

Makes app configurable without any code changes

### 4. Error Handling
```python
@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Not Found', 'message': 'Endpoint does not exist'}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal Server Error', 'message': 'An unexpected error occurred'}}
```

Prevents application from exposing sensitive data and tracebacks to end user

## API Documentation

### GET /

+ Returns service metadata, system information, runtime details, and request context

**Request example:**

```bash
curl http://localhost:5000/
```

**Response example (short):**

```json
{
  "service": {
    "name": "devops-info-service",
    "version": "1.0.0"
  },
  "system": {
    "hostname": "my-host",
    "platform": "Linux"
  },
  "request": {
    "client_ip": "127.0.0.1",
    "user_agent": "curl/7.80.0",
  }
}
```

### GET /health

+ Health check endpoint used for monitoring and probes

**Request example:**

```bash
curl http://localhost:5000/health
```

**Response example:**

```json
{
  "status": "healthy",
  "uptime_seconds": 3
}
```

Returns 200 if healthy

### Testing Commands

```bash
curl http://localhost:5000/
curl http://localhost:5000/health
curl http://localhost:5000/ | jq # Pretty print
```

## Testing Evidence

The following evidence demonstrates correct application behavior:

* Screenshot of `/` endpoint returning full JSON response
* Screenshot of `/health` endpoint returning healthy status
- [i] Note: all requests were made in Firefox browser and pretty-printed by default. If you make them with curl, please make sure you use `jq` for JSON processing

All screenshots are stored in the `docs/screenshots/` directory


## Challenges & Solutions

### Challenge: Timezone consistency

**Problem:** Clean JSON error responses

**Solution:** Implemented custom Flask error handlers returning clean JSON
