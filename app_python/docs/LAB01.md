# Lab 01 - Python Implementation

DevOps Info Service - FastAPI implementation

## Overview

REST API service providing system information and health monitoring. Built with FastAPI for auto-documentation and async support.

## Framework Selection

**Chosen:** FastAPI 0.115

**Why FastAPI?**
- Auto-generated Swagger UI at `/docs`
- Modern async/await support
- Type validation with Pydantic
- Minimal boilerplate for simple APIs

**Why not Flask/Django?**
- Flask: No auto-docs, manual validation
- Django: Too heavy for a 2-endpoint service

## Best Practices Applied

### 1. Structured Logging
```python
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger.info(f'Request: {request.method} {request.url.path} from {request.client.host}')
```

### 2. Error Handling
```python
@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    logger.warning(f'HTTP {exc.status_code} error: {exc.detail}')
    return JSONResponse(status_code=exc.status_code, content={'error': exc.detail})
```

### 3. Environment Configuration
```python
HOST = os.getenv('HOST', '0.0.0.0')
PORT = int(os.getenv('PORT', 5000))
DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'
```

### 4. Code Organization
- Module docstrings
- Grouped imports (stdlib → third-party)
- Type hints for IDE support
- PEP 8 compliant

## API Documentation

### GET /

Returns comprehensive service, system, runtime, and request information.

```bash
curl http://localhost:5000/
```

### GET /health

Health check endpoint for monitoring.

```bash
curl http://localhost:5000/health
```

Response:
```json
{
  "status": "healthy",
  "timestamp": "2026-01-26T12:30:00.000000+00:00",
  "uptime_seconds": 120
}
```

### Interactive Documentation

FastAPI auto-generates Swagger UI:
```
http://localhost:5000/docs
```

## Running the Application

### Development
```bash
python app.py
PORT=8080 python app.py
```

### With uvicorn (hot reload)
```bash
uvicorn app:app --reload
uvicorn app:app --host 0.0.0.0 --port 8080
```

## Testing

### Basic curl
```bash
curl http://localhost:5000/
curl http://localhost:5000/health
```

### Pretty-print JSON
```bash
curl -s http://localhost:5000/ | python3 -m json.tool
curl -s http://localhost:5000/ | jq '.'
```

## Testing Evidence

Screenshots in `docs/screenshots/`:
- `01-main-endpoint.png` - GET / response
- `02-health-check.png` - GET /health response
- `03-formatted-output.png` - Swagger UI / pretty JSON