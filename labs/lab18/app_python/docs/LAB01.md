## Framework Selection
I chose FastAPI because it is a modern standard, async and it is easy to use.

| Criteria    | FastAPI | Flask | Django |
|-------------|---------|-------|--------|
| Is standard | yes     | no    | yes    |
| Async       | yes     | no    | no     |
| Simple      | yes     | yes   | no     |

## Best Practices Applied
### Clean Code Organization
```python
# Grouped and ordered imports
import os
import socket
import platform
import logging
from datetime import datetime, timezone
from typing import Dict, Any

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
```
Importance: Proper import organization improves readability and avoids circular dependencies.

### Separation of Concerns
```python
def get_system_info() -> Dict[str, Any]:
    """Collect system information."""
    return {
        'hostname': socket.gethostname(),
        'platform': platform.system(),
        # ...
    }

def get_runtime_info() -> Dict[str, Any]:
    """Collect runtime information."""
    # ...
```

Importance: Each function has a single responsibility, making code easier to test, maintain, and reuse.


### Type Hints
```python
def get_uptime() -> Dict[str, Any]:
    """Calculate application uptime since start."""
    # ...
```
Importance: Improves code readability

### Environment-Based Configuration

```python
HOST = os.getenv('HOST', '0.0.0.0')
PORT = int(os.getenv('PORT', '5000'))
DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'
```

Importance: Allows configuration changes without code modifications

### Logging
```python
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)
```

Importance: Provides operational monitoring


### Error Handling
```python
@app.exception_handler(404)
async def not_found_handler(request: Request, exc):
    """Handle 404 Not Found errors."""
    return JSONResponse(
        status_code=404,
        content={
            "error": "Not Found",
            "message": f"Endpoint {request.url.path} does not exist",
            "timestamp": datetime.now().isoformat()
        }
    )
```
Importance: Provides clear error messages to users, prevents leakage of internal information


## API Documentation

### GET /

Request: curl -X GET "http://localhost:5000/" 

Response:
```json
{"service":{"name":"devops-info-service","version":"1.0.0","description":"DevOps course info service","framework":"FastAPI"},"system":{"hostname":"DESKTOP-2Q0E6TS","platform":"Windows","platform_version":"10.0.19045","architecture":"AMD64","cpu_count":8,"python_version":"3.11.5"},"runtime":{"uptime_seconds":163,"uptime_human":"0 hours, 2 minutes","current_time":"2026-01-25T10:46:35.373465","timezone":"UTC"},"request":{"client_ip":"127.0.0.1","user_agent":"PostmanRuntime/7.39.1","method":"GET","path":"/"},"endpoints":[{"path":"/","method":"GET","description":"Service information"},{"path":"/health","method":"GET","description":"Health check"}]}
```
### GET /health

Request: curl -X GET "http://localhost:5000/health"

Response:
```json
{"status":"healthy","timestamp":"2026-01-25T10:48:49.392040","uptime_seconds":297} 
```

## Testing Evidence

Terminal Output
```
2026-01-25 10:43:51,683 - __main__ - INFO - Starting Service on 0.0.0.0:5000
2026-01-25 10:44:19,388 - app - INFO - GET / requested from 127.0.0.1
2026-01-25 10:45:19,772 - app - INFO - GET / requested from 127.0.0.1
2026-01-25 10:45:32,977 - app - INFO - GET / requested from 127.0.0.1
2026-01-25 10:46:35,372 - app - INFO - GET / requested from 127.0.0.1
2026-01-25 10:48:02,640 - app - INFO - GET / requested from 127.0.0.1
```

## Challenges & Solutions
Challenge: Asynchronous Request Handling
Problem: Some Python functions (like socket.gethostname()) are blocking in async FastAPI context.

Solution: Used them in synchronous functions within async endpoints. For production with high load, asyncio.to_thread() could be implemented.


## GitHub Community
### Importance of Repository Stars

Quality Signal: Star count helps new users assess project reliability and activity.

Community Support: Stars are a form of appreciation and support for maintainers, showing their work is valuable to the community.

### Importance of Following Developers

Networking: I can see what projects other course participants are working on, creating opportunities for collaboration and knowledge sharing.

Learning by Example: Observing how experienced developers work teaches best practices, new tools, and problem-solving approaches.
