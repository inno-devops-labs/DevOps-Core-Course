# Lab 1 - DevOps Info Service

## Framework Selection

 **Choice** : Flask 3.1.0
 **Why** : Lightweight, synchronous, minimal dependencies. Perfect for simple 2-endpoint service matching lab examples.

**Comparison** :

| Framework           | Learning Curve | Async | Auto-docs | Lab Fit     |
| ------------------- | -------------- | ----- | --------- | ----------- |
| **Flask 3.1** | Low            | No    | Manual    | ✅ Selected |
| FastAPI 0.115       | Medium         | Yes   | Yes       | Overkill    |
| Django 5.0          | High           | No    | Yes       | Too heavy   |

## Best Practices Applied

### 1. Environment-driven Configuration

```
HOST = os.getenv('HOST', '0.0.0.0')
PORT = int(os.getenv('PORT', 5000))
DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'
```

**Importance** : Flexible deployment (Docker/K8s), 12-factor app principles.

### 2. Structured Logging

```
logger = logging.getLogger(name)
logger.info(f'Request: {request.method} {request.path}')
```

**Importance** : Production debugging, SRE monitoring.

### 3. JSON Error Handlers

```
@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Not Found'}), 404

```

**Importance** : API-friendly error responses.

### 4. PEP8 + Docstrings

```
def get_system_info():
    """Collect system information."""
```

**Importance** : Readability, maintainability.

## API Documentation

### GET / — Service Information

**Request**:

`curl http://localhost:5000/`

**Response** (200 OK):

```
{
  "service": {
    "description": "DevOps course info service",
    "framework": "Flask",
    "name": "devops-info-service",
    "version": "1.0.0"
  },
  {...}
}
```

### GET /health — Health Check

**Request** :

`curl http://localhost:5000/health`

**Response** (200 OK):

```
{
  "status": "healthy",
  "timestamp": "2026-01-28T18:47:00Z",
  "uptime_seconds": 120
}
```

### Testing Evidence

Screenshots are in docs/screenshots

**Terminal output:**

```
ko.zimin@macbook-D69TY4QGYD ~/D/o/d/D/app_python (labs/lab01)> PORT=8080 python app.py
2026-01-28 22:01:10,336 - main - INFO - Starting DevOps Info Service on 0.0.0.0:8080 (debug=False)Serving Flask app 'app'Debug mode: off
2026-01-28 22:01:10,530 - werkzeug - INFO - WARNING: This is a development server. Do not use it in a production deployment. Use a production WSGI server instead.Running on all addresses (0.0.0.0)Running on http://127.0.0.1:8080Running on http://10.240.23.216:8080
2026-01-28 22:01:10,530 - werkzeug - INFO - Press CTRL+C to quit
2026-01-28 22:01:16,917 - main - INFO - Request: GET / from 127.0.0.1
2026-01-28 22:01:16,917 - werkzeug - INFO - 127.0.0.1 - - [28/Jan/2026 22:01:16] "GET / HTTP/1.1" 200 -
```

### Challenges & Solutions

Choose the best framework as before I don't write in Python. And I really want to know the best framework for newcomers.

No more problems anymore.

### GitHub Community

Stars: Signal project quality, improve discoverability.
Following: Networking, learning from real code, staying current.
